import psycopg2
import io
import re
import logging
import time

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

from common.utils.Database_connection_Utils import connect_and_create_schemas

# Connect to DB
DB_CONNECTION = connect_and_create_schemas()
CURSOR = DB_CONNECTION.cursor()
PROCESSED_TABLES = set()


def check_table_exists(CURSOR, schema, table_name):
    """Checks if a table exists in the given schema."""
    if (schema, table_name) in PROCESSED_TABLES:
        return True
    CURSOR.execute("""
                   SELECT 1
                   FROM information_schema.tables
                   WHERE table_schema = %s
                     AND table_name = %s
                   """, (schema, table_name))
    exists = CURSOR.fetchone() is not None
    if exists:
        PROCESSED_TABLES.add((schema, table_name))
    return exists


# Function to create a table dynamically if not exists
def create_device_table(CURSOR, connection, schema, table_name):
    """Creates a table for a specific device type and model."""
    create_query = f"""
        CREATE TABLE {schema}.{table_name} (
            device_id VARCHAR(255) PRIMARY KEY,
            device_type VARCHAR(50) NOT NULL,
            model_name VARCHAR(255) NOT NULL,
            alias VARCHAR(255),
            reportable BOOLEAN DEFAULT TRUE,
            log_action VARCHAR(255) DEFAULT 'inserted',
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            is_active BOOLEAN DEFAULT TRUE  

        );
    """
    try:
        CURSOR.execute(create_query)
        connection.commit()
        logging.info(f"✅ Created table: {schema}.{table_name}")
        return True
    except psycopg2.Error as e:
        connection.rollback()
        logging.error(f"Error creating table {schema}.{table_name}: {e}")
        return False


# store table names into different table
def upsert_device_data(CURSOR, connection, schema, table_name, device_data):
    """Inserts or updates device data in the specific device table."""
    sql = f"""
        INSERT INTO {schema}.{table_name} (
            device_id, device_type, model_name, alias, reportable, updated_at, log_action,is_active)
            VALUES (%s, %s, %s, %s, %s, NOW(), 'insert',TRUE
        )
        ON CONFLICT (device_id)
        DO UPDATE SET
            alias = EXCLUDED.alias,
            reportable = EXCLUDED.reportable,
            updated_at = NOW(),
            log_action = 'update',
            is_active = TRUE
        WHERE {schema}.{table_name}.alias IS DISTINCT FROM EXCLUDED.alias
           OR {schema}.{table_name}.reportable IS DISTINCT FROM EXCLUDED.reportable
           OR {schema}.{table_name}.is_active IS DISTINCT FROM TRUE;
    """
    try:
        CURSOR.execute(sql, (
            device_data['device_id'],
            device_data['device_type'],
            device_data['model_name'],
            device_data['alias'],
            device_data['reportable']
        ))
        connection.commit()
        logging.info(f"🔄 UPSERTED device: {device_data['device_id']} in {schema}.{table_name}")
        return True
    except psycopg2.Error as e:
        connection.rollback()
        logging.error(f"Error UPSERTING device {device_data.get('device_id', 'N/A')} in {schema}.{table_name}: {e}")
        return False


def mark_missing_devices(CURSOR, connection, schema, table_name, device_type, model_name):
    """Marks devices as missing if not present in the staging table."""
    sql = f"""
            UPDATE {schema}.{table_name} target_table -- Added alias for clarity
            SET log_action = 'missing', updated_at = NOW(), is_active = FALSE
            WHERE target_table.is_active = TRUE -- Use this condition instead of log_action check
              AND NOT EXISTS (
                SELECT 1
                FROM registered_devices.device_staging staging -- Added alias for clarity
                WHERE staging.device_id = target_table.device_id
                AND staging.device_type = %s
                AND staging.model_name = %s
            );
            -- AND log_action != 'missing'; -- Removed this line
        """
    try:
        CURSOR.execute(sql, (device_type, model_name))
        updated_count = CURSOR.rowcount
        if updated_count > 0:
            logging.warning(f"🚨 Marked {updated_count} devices as missing in {schema}.{table_name}")
        return True
    except psycopg2.Error as e:
        connection.rollback()
        logging.error(f"Error marking missing devices in {schema}.{table_name}: {e}")
        return False

def Output_devices_to_json_file(device_model_dict):
    output_file = "device_models.json"
    try:
        with open(output_file, 'w') as f:
            json.dump(device_model_dict, f, indent=4)  # Use indent for pretty formatting
        logging.info(f"Device type and model names written to '{output_file}'")
    except IOError as e:
        logging.error(f"Error writing to '{output_file}': {e}")



if __name__ == "__main__":
    start_time = time.time()

    # 1. Fetch unique device type and model combinations from staging
    CURSOR.execute("""
                   SELECT DISTINCT device_type, model_name
                   FROM registered_devices.device_staging;
                   """)
    unique_type_models = CURSOR.fetchall()
    device_model_dict = {device_type: model for device_type, model in unique_type_models}

    Output_devices_to_json_file(device_model_dict)

    logging.info(f"Found {len(unique_type_models)} unique device type/model combinations in staging.")
    current_staging_table_names = set()
    # 2. Process each unique device type and model
    for device_type, model_name in unique_type_models:
        table_name = f"{device_type.lower().replace('device_', '')}_model_{model_name.lower()}"
        table_name = re.sub(r'\W+', '_', table_name).strip('_')
        current_staging_table_names.add(table_name)  # Track expected tables

        # 3. Create the table if it doesn't exist
        if not check_table_exists(CURSOR, 'registered_devices', table_name):
            # Pass DB_CONNECTION here
            if not create_device_table(CURSOR, DB_CONNECTION, 'registered_devices', table_name):
                logging.error(f"Failed to create table {table_name}, skipping...")
                continue  # Skip this type/model if table creation fails

        # 4. Fetch data for the current device type and model from staging
        CURSOR.execute("""
                       SELECT device_id, device_type, model_name, alias, reportable
                       FROM registered_devices.device_staging
                       WHERE device_type = %s
                         AND model_name = %s;
                       """, (device_type, model_name))
        devices_to_sync = CURSOR.fetchall()
        upsert_success_count = 0  # Track success
        # 5. UPSERT each device
        for row in devices_to_sync:
            device_data = {
                'device_id': row[0],
                'device_type': row[1],
                'model_name': row[2],
                'alias': row[3],
                'reportable': row[4]
            }

            # Call the UPSERT function (needs correction for is_active and commit)
            if upsert_device_data(CURSOR, DB_CONNECTION, 'registered_devices', table_name, device_data):
                upsert_success_count += 1
        DB_CONNECTION.commit()  # <-- ADD COMMIT HERE
        logging.info(f"Committed UPSERTs for {upsert_success_count}/{len(devices_to_sync)} devices into {table_name}")
        # 6. Mark missing devices for this table
        mark_missing_devices(CURSOR, DB_CONNECTION, 'registered_devices', table_name, device_type, model_name)
        DB_CONNECTION.commit()  # <-- ADD COMMIT HERE

    # 7. Handle tables for device types/models no longer in staging
    logging.info("Checking for device tables with no corresponding staging data...")  # Added logging
    CURSOR.execute("""
                   SELECT table_name
                   FROM information_schema.tables
                   WHERE table_schema = 'registered_devices'
                     AND table_name LIKE '%_model_%';
                   """)
    existing_device_tables = [row[0] for row in CURSOR.fetchall()]

    tables_to_mark_fully_missing = set(existing_device_tables) - current_staging_table_names
    logging.info(
        f"Device tables potentially containing only missing devices: {len(tables_to_mark_fully_missing)}")  # Added logging
    for table in tables_to_mark_fully_missing:
        logging.warning(
            f"Marking all active devices in registered_devices.{table} as missing (type/model no longer in staging).")  # Extract device_type and model_name (best effort based on naming convention)
        sql_mark_all = f"""
                     UPDATE registered_devices.{table}
                     SET log_action = 'missing_type_model', updated_at = NOW(), is_active = FALSE
                     WHERE is_active = TRUE; -- Use is_active condition
                 """
        try:
            CURSOR.execute(sql_mark_all)
            DB_CONNECTION.commit()  # Good: Commit after updating this table.
        except psycopg2.Error as e:
            DB_CONNECTION.rollback()
            logging.error(f"Error marking all missing in registered_devices.{table}: {e}")

    logging.info("✅ All devices processed successfully!")

    # Cleanup (optional)
    # CURSOR.execute("TRUNCATE TABLE registered_devices.device_staging;")
    # DB_CONNECTION.commit()
    # logging.info("🧹 Cleaned up staging table")

    CURSOR.close()
    DB_CONNECTION.close()

    end_time = time.time()
    logging.info(f"Total time taken: {end_time - start_time} seconds")
