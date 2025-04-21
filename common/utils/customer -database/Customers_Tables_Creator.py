import psycopg2
import re
import logging
import time

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

from common.utils.Database_connection_Utils import connect_and_create_schemas

# Connect to DB
DB_CONNECTION = connect_and_create_schemas()
cur = DB_CONNECTION.cursor()
PROCESSED_TABLES = set()


def check_table_exists(cur, schema, table_name):
    """Checks if a table exists in the given schema."""
    if (schema, table_name) in PROCESSED_TABLES:
        return True
    cur.execute("""
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = %s
        AND table_name = %s
    """, (schema, table_name))
    exists = cur.fetchone() is not None
    if exists:
        PROCESSED_TABLES.add((schema, table_name))
    return exists


# Function to create a table dynamically if not exists
def create_customer_table(cur, connection, schema, table_name):
    """Creates a table for a specific device type and model."""
    create_query = f"""
        CREATE TABLE {schema}.{table_name} (
            customer_id SERIAL PRIMARY KEY,
            full_name VARCHAR(100),
            email VARCHAR(100),
            phone VARCHAR(50),
            address TEXT,
            device_id VARCHAR(255) REFERENCES registered_devices.{table_name}(device_id) UNIQUE,
            device_type VARCHAR(50) NOT NULL,
            model_name VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT now(),
            updated_at TIMESTAMP DEFAULT NOW(),
            is_active BOOLEAN DEFAULT TRUE  ,
            log_action VARCHAR(255) DEFAULT 'inserted'

        );
    """
    try:
        cur.execute(create_query)
        connection.commit()
        logging.info(f"✅ Created table: {schema}.{table_name}")
        return True
    except psycopg2.Error as e:
        connection.rollback()
        logging.error(f"Error creating table {schema}.{table_name}: {e}")
        return False


# store table names into different table
def upsert_customer_data(cur, connection, schema, table_name, customer_data):
    """Inserts or updates device data in the specific CUSTOMER  table IN customers schema."""
    sql = f"""
        INSERT INTO {schema}.{table_name} (full_name, email, phone, address, device_id,device_type,model_name,updated_at, log_action,is_active)
        VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), 'insert',TRUE)
        ON CONFLICT (device_id)
        DO UPDATE SET
            full_name = EXCLUDED.full_name,
            email = EXCLUDED.email,
            phone = EXCLUDED.phone,
            address = EXCLUDED.address,
            updated_at = NOW(),
            log_action = 'update',
            is_active = TRUE 
        WHERE {schema}.{table_name}.full_name IS DISTINCT FROM EXCLUDED.full_name
           OR {schema}.{table_name}.email IS DISTINCT FROM EXCLUDED.email
           OR {schema}.{table_name}.phone IS DISTINCT FROM EXCLUDED.phone
           OR {schema}.{table_name}.address IS DISTINCT FROM EXCLUDED.address
           OR {schema}.{table_name}.is_active IS DISTINCT FROM TRUE;

    """
    try:
        cur.execute(sql, (
            customer_data['full_name'],
            customer_data['email'],
            customer_data['phone'],
            customer_data['address'],
            customer_data['device_id'],
            customer_data['device_type'],
            customer_data['model_name']

        ))
        logging.info(f"🔄 UPSERTED customer data : {customer_data['device_id']} in {schema}.{table_name}")
        return True
    except psycopg2.Error as e:
        connection.rollback()
        logging.error(f"Error UPSERTING customer data {customer_data['device_id']} in {schema}.{table_name}: {e}")
        return False


def mark_missing_customers(cur, connection, schema, table_name, device_type, model_name):
    """Marks customers  as missing if not present in the customer_staging table."""
    sql = f"""
        UPDATE {schema}.{table_name}
        SET log_action = 'missing', updated_at = NOW(), is_active = FALSE
        WHERE NOT EXISTS (
            SELECT 1
            FROM customers.customer_staging staging
            WHERE staging.device_id = {schema}.{table_name}.device_id
            AND staging.device_type = %s
            AND staging.model_name = %s
        ) 
    """
    try:
        cur.execute(sql, (device_type, model_name))
        updated_count = cur.rowcount
        if updated_count > 0:
            logging.warning(f"🚨 Marked {updated_count} customers as missing in {schema}.{table_name}")
        return True
    except psycopg2.Error as e:
        connection.rollback()
        logging.error(f"Error marking missing customers in {schema}.{table_name}: {e}")
        return False


if __name__ == "__main__":
    start_time = time.time()

    # 1. Fetch unique device type and model combinations from staging
    cur.execute("""
        SELECT DISTINCT device_id,device_type, model_name
        FROM customers.customer_staging;
    """)

    unique_devices = cur.fetchall()
    logging.info(f"Found {len(unique_devices)} unique device type/model combinations in staging.")
    # for device_id,device_type, model_name in unique_devices:
    #     print(f"{device_type}: {model_name}")
    # print(f"length of unique devices: {len(unique_devices)}")
    # 2. Process each unique device type and model
    current_staging_table_names = set()
    for device_id,device_type, model_name in unique_devices:
        table_name = f"{device_type.lower().replace('device_', '')}_model_{model_name.lower()}"
        table_name = re.sub(r'\W+', '_', table_name).strip('_')
        current_staging_table_names.add(table_name) # Track expected tables

        # 3. Create the table if it doesn't exist
        if not check_table_exists(cur, 'customers', table_name):
            # Pass DB_CONNECTION here
            if not create_customer_table(cur, DB_CONNECTION, 'customers', table_name):
                logging.error(f"Failed to create table {table_name}, skipping...")
                continue  # Skip this type/model if table creation fails

        # 4. Fetch data for the current device type and model from staging
        cur.execute("""
            SELECT customer_id,full_name,email,phone,address,device_id, device_type, model_name
            FROM customers.customer_staging
            WHERE device_type = %s AND model_name = %s;
        """, (device_type, model_name))
        customers_to_sync = cur.fetchall()
        logging.debug(f"Found {len(customers_to_sync)} customer records for {device_type}/{model_name} in staging.")
        # 5. UPSERT each device
        upsert_success_count = 0
        for row in customers_to_sync:
            customer_data = {
                'customer_id': row[0],
                'full_name': row[1],
                'email': row[2],
                'phone': row[3],
                'address': row[4],
                'device_id': row[5],
                'device_type': row[6],
                'model_name': row[7]

            }
            # Call the UPSERT function
            if upsert_customer_data(cur, DB_CONNECTION, 'customers', table_name, customer_data):
                upsert_success_count += 1
        DB_CONNECTION.commit()
        logging.info(f"Committed UPSERTs for {upsert_success_count}/{len(customers_to_sync)} customers into customers.{table_name}")
        # 6. Mark missing customers for this table
        mark_missing_customers(cur, DB_CONNECTION, 'customers', table_name, device_type, model_name)
        DB_CONNECTION.commit()  # <-- ADD THIS LINE
    # 7. Handle tables for device types/models no longer in staging
    logging.info("Checking for customer tables with no corresponding staging data...")
    cur.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'customers'
        AND table_name LIKE '%_model_%';
    """)
    existing_customer_tables = [row[0] for row in cur.fetchall()]

    # cur.execute("""
    #     SELECT DISTINCT LOWER(REPLACE(REPLACE(device_type, 'device_', ''), ' ', '_')) || '_model_' || LOWER(REPLACE(model_name, ' ', '_'))
    #     FROM customers.customer_staging;
    # """)
    # current_device_table_names = set(row[0] for row in cur.fetchall())
    tables_to_mark_fully_missing = existing_customer_tables - current_staging_table_names
    logging.info(f"Customer tables potentially containing only missing customers: {tables_to_mark_fully_missing}") # Added logging
    for table in tables_to_mark_fully_missing:
        # This logic is simpler and better than trying to parse the name
        logging.warning(f"Marking all active customers in customers.{table} as missing (type/model no longer in staging).")
        sql_mark_all = f"""
                 UPDATE customers.{table}
                 SET log_action = 'missing_type_model', updated_at = NOW(), is_active = FALSE
                 WHERE is_active = TRUE; -- Use is_active condition
             """
        try:
            cur.execute(sql_mark_all)
            # GOOD: Commit after updating this table.
            DB_CONNECTION.commit()
        except psycopg2.Error as e:
            DB_CONNECTION.rollback()
            logging.error(f"Error marking all missing in customers.{table}: {e}")

    logging.info("✅ Customer table processing complete!") # Updated log message
    # Cleanup (optional)
    # cur.execute("TRUNCATE TABLE customers.customer_staging;")
    # DB_CONNECTION.commit()
    # logging.info("🧹 Cleaned up staging table")
    cur.close()
    DB_CONNECTION.close()
    end_time = time.time()
    logging.info(f"Total time taken: {end_time - start_time} seconds")
