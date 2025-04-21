import psycopg2
import io
import re
import logging
import json
import time

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

from Database_connection_Utils import connect_and_create_schemas

# Connect to DB
DB_CONNECTION = connect_and_create_schemas()
CURSOR = DB_CONNECTION.cursor()
PROCESSED_TABLES = set()

# Function to check if a table exists for device type and model
checked_tables = set()


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
        INSERT INTO {schema}.{table_name} (device_id, device_type, model_name, alias, reportable, updated_at, log_action)
        VALUES (%s, %s, %s, %s, %s, NOW(), 'insert')
        ON CONFLICT (device_id)
        DO UPDATE SET
            alias = EXCLUDED.alias,
            reportable = EXCLUDED.reportable,
            updated_at = NOW(),
            log_action = 'update'
        WHERE {schema}.{table_name}.alias IS DISTINCT FROM EXCLUDED.alias
           OR {schema}.{table_name}.reportable IS DISTINCT FROM EXCLUDED.reportable
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
        logging.error(f"Error UPSERTING device {device_data['device_id']} in {schema}.{table_name}: {e}")
        return False


def mark_missing_devices(CURSOR, connection, schema, table_name, device_type, model_name):
    """Marks devices as missing if not present in the staging table."""
    sql = f"""
        UPDATE {schema}.{table_name}
        SET log_action = 'missing', updated_at = NOW(), is_active = FALSE
        WHERE NOT EXISTS (
            SELECT 1
            FROM registered_devices.device_staging
            WHERE device_staging.device_id = {schema}.{table_name}.device_id
            AND device_staging.device_type = %s
            AND device_staging.model_name = %s
        ) AND log_action != 'missing';
    """
    try:
        CURSOR.execute(sql, (device_type, model_name))
        connection.commit()
        updated_count = CURSOR.rowcount
        if updated_count > 0:
            logging.warning(f"🚨 Marked {updated_count} devices as missing in {schema}.{table_name}")
        return True
    except psycopg2.Error as e:
        connection.rollback()
        logging.error(f"Error marking missing devices in {schema}.{table_name}: {e}")
        return False


if __name__ == "__main__":
    start_time = time.time()

    # 1. Fetch unique device type and model combinations from staging
    CURSOR.execute("""
        SELECT DISTINCT device_type, model_name
        FROM registered_devices.device_staging;
    """)
    unique_devices = CURSOR.fetchall()
    logging.info(f"Found {len(unique_devices)} unique device type/model combinations in staging.")
    for device_type, model_name in unique_devices:
        print(f"{device_type}: {model_name}")
    print(f"length of uniue devices: {len(unique_devices)}")
    print("sleeping")
    # 2. Process each unique device type and model
    for device_type, model_name in unique_devices:
        table_name = f"{device_type.lower().replace('device_', '')}_model_{model_name.lower()}"
        table_name = re.sub(r'\W+', '_', table_name).strip('_')

        # 3. Create the table if it doesn't exist
        if not check_table_exists(CURSOR, 'registered_devices', table_name):
            create_device_table(CURSOR, DB_CONNECTION, 'registered_devices', table_name)

        # 4. Fetch data for the current device type and model from staging
        CURSOR.execute("""
            SELECT device_id, device_type, model_name, alias, reportable
            FROM registered_devices.device_staging
            WHERE device_type = %s AND model_name = %s;
        """, (device_type, model_name))
        devices_to_sync = CURSOR.fetchall()

        # 5. UPSERT each device
        for row in devices_to_sync:
            device_data = {
                'device_id': row[0],
                'device_type': row[1],
                'model_name': row[2],
                'alias': row[3],
                'reportable': row[4]
            }
            upsert_device_data(CURSOR, DB_CONNECTION, 'registered_devices', table_name, device_data)

        # 6. Mark missing devices for this table
        mark_missing_devices(CURSOR, DB_CONNECTION, 'registered_devices', table_name, device_type, model_name)

    # 7. Handle tables for device types/models no longer in staging
    CURSOR.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'registered_devices'
        AND table_name LIKE '%_model_%';
    """)
    existing_device_tables = [row[0] for row in CURSOR.fetchall()]

    CURSOR.execute("""
        SELECT DISTINCT LOWER(REPLACE(REPLACE(device_type, 'device_', ''), ' ', '_')) || '_model_' || LOWER(REPLACE(model_name, ' ', '_'))
        FROM registered_devices.device_staging;
    """)
    current_device_table_names = set(row[0] for row in CURSOR.fetchall())

    for table in existing_device_tables:
        if table not in current_device_table_names:
            # Extract device_type and model_name (best effort based on naming convention)
            match = re.match(r"(.+)_model_(.+)", table)
            if match:
                device_type_part = match.group(1).replace('_', ' ').lower()
                model_name_part = match.group(2).replace('_', ' ').lower()
                mark_missing_devices(CURSOR, DB_CONNECTION, 'registered_devices', table, device_type_part, model_name_part)
            else:
                logging.warning(f"Could not reliably extract device info from table name: {table} for marking missing devices.")

    logging.info("✅ All devices processed successfully!")

    # Cleanup (optional)
    # CURSOR.execute("TRUNCATE TABLE registered_devices.device_staging;")
    # DB_CONNECTION.commit()
    # logging.info("🧹 Cleaned up staging table")

    CURSOR.close()
    DB_CONNECTION.close()

    end_time = time.time()
    logging.info(f"Total time taken: {end_time - start_time} seconds")
