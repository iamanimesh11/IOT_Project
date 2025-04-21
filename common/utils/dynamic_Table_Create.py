import psycopg2
import io
import re
import logging
import json
import time

start_time = time.time()
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

from Database_connection_Utils import connect_and_create_schemas


# Connect to DB
db_connection = connect_and_create_schemas()
cur = db_connection.cursor()

log_printed = False

# Function to check if a table exists for device type and model
checked_tables = set()

def check_table_exists(table_name):
    if table_name in checked_tables:
        return True
    cur.execute("""
        SELECT 1
        FROM information_schema.tables 
        WHERE table_schema = 'registered_devices' 
        AND table_name = %s
    """, (table_name,))
    exists = cur.fetchone() is not None
    if exists:
        checked_tables.add(table_name)
    return exists


# Function to create a table dynamically if not exists
def create_table(table_name):
    create_query = f"""
        CREATE TABLE registered_devices.{table_name} (
            device_id VARCHAR(255) PRIMARY KEY,
            device_type VARCHAR(50) NOT NULL,
            model_name VARCHAR(255) NOT NULL,
            alias VARCHAR(255),
            reportable BOOLEAN DEFAULT TRUE,
            log_action VARCHAR(255) DEFAULT 'inserted',
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
        );
    """
    cur.execute(create_query)
    db_connection.commit()
    print(f"✅ Created table: {table_name}")


# store table names into different table

def create_table_all_table_name(table_name):
    create_query = f"""
    CREATE TABLE IF NOT EXISTS registered_devices.{table_name} (
       device_type TEXT DEFAULT NULL,
       model_name TEXT DEFAULT NULL,
       PRIMARY KEY (device_type, model_name)  
       );
    """
    try:
        cur.execute(create_query)
        db_connection.commit()
        logging.info(f"Table created in registered_devices schema : {table_name}.")
    except Exception as e:
        logging.error(f"Table creation error :{table_name} , exception message: {e}")


create_table_all_table_name("all_table_names")


def insert_all_tables_names(table_name):
    query = f"""
     INSERT INTO registered_devices.{table_name} (device_type, model_name)
    SELECT DISTINCT device_type, model_name FROM registered_devices.device_staging
    ON CONFLICT (device_type, model_name) DO NOTHING
    RETURNING *;
    """
    try:
        cur.execute(query)
        db_connection.commit()
        inserted_Rows = cur.fetchall()

        logging.info(f"Inserted total {len(inserted_Rows)} records in table {table_name}")
        logging.info(f"Inserted rows are: {inserted_Rows}")

    except Exception as e:
        logging.error(f"Insertion failed in table {table_name} , exception is : {e}")


insert_all_tables_names("all_table_names")



cur.execute("""
    SELECT  device_type, model_name FROM registered_devices.all_table_names;
""")

unique_devices = cur.fetchall()

for device_type, model_name in unique_devices:
    print(f"{device_type}: {model_name}")
print(f"length of uniue devices: {len(unique_devices)}")
print("sleeping")
time.sleep(3000)

if not unique_devices:
    # Query to get all table names in the 'registered_devices' schema
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'registered_devices'
          AND table_type = 'BASE TABLE';
    """)

    # Fetch all the table names
    existing_tables = cur.fetchall()

    print("Device staging is empty. Marking all devices as missing.")

    for table_name in existing_tables:  # assuming you have the list of all table names already
        table_name = table_name[0]
        if table_name == 'device_staging':
            print("Table name doesn't match expected format.")
            continue
        split_parts = table_name.split('_model_')
        print(len(split_parts))

        # Check if the table name is in the expected format
        if len(split_parts) == 2:
            device_type = split_parts[0]
            model_name = split_parts[1]

            # Optional: If you want to clean the device_type (e.g., remove 'device_' prefix)
            device_type = device_type.replace('device_', '')

            # Print the extracted device_type and model_name
            print(f"Device Type: {device_type}")
            print(f"Model Name: {model_name}")

        print(f"🚨 Marking missing devices as inactive for table: {table_name}")
        cur.execute(f"""
               UPDATE registered_devices.{table_name}
               SET log_action = 'missing', updated_at = NOW(), is_active = FALSE
               WHERE NOT EXISTS (
                   SELECT 1
                   FROM registered_devices.device_staging
                   WHERE device_staging.device_id = registered_devices.{table_name}.device_id
                   AND device_staging.device_type = %s
                   AND device_staging.model_name = %s
               );
           """, (device_type, model_name))
        db_connection.commit()
else:
    for device_type, model_name in unique_devices:
        print(f"{device_type}:{model_name}")
        table_name = f"{device_type.lower().replace('device_', '')}_model_{model_name.lower()}"
        table_name = re.sub(r'\W+', '_', table_name)  # Replace non-word characters with '_'
        table_name = table_name.strip('_')

        # Check if table exists for device type and model name
        table_Exist = check_table_exists(table_name)
        if table_Exist:
            print(f"Table {table_name}  already exists!")
            if not log_printed:
                log_printed = True

        if not table_Exist:
            print(f"Table {table_name} doesn't  exists ,creating!")
            create_table(table_name)

        print(f"🔄 Performing UPSERT for table: {table_name}")

        sql = f"""
            WITH upserted AS (
                INSERT INTO registered_devices.{table_name} (device_id, device_type, model_name, alias, reportable, updated_at, log_action)
                SELECT device_id, device_type, model_name, alias, reportable, NOW(), 'insert'
                FROM registered_devices.device_staging
                WHERE device_type = %s AND model_name = %s
                ON CONFLICT (device_id)
                DO UPDATE 
                SET alias = EXCLUDED.alias, 
                    reportable = EXCLUDED.reportable, 
                    updated_at = NOW(),
                    log_action = 'update'
                    WHERE registered_devices.{table_name}.alias IS DISTINCT FROM EXCLUDED.alias
                    OR registered_devices.{table_name}.reportable IS DISTINCT FROM EXCLUDED.reportable
                RETURNING device_id, log_action
            )
            SELECT * FROM upserted;
        """
        cur.execute(sql, (device_type, model_name))

        updated_rows = cur.fetchall()  # Fetch the results
        for row in updated_rows:
            print(row)  # Log or process as needed

        db_connection.commit()

        print(f"🚨 Marking missing devices as inactive for table: {table_name}")
        cur.execute(f"""
               UPDATE registered_devices.{table_name}
               SET log_action = 'missing', updated_at = NOW(),is_active=FALSE
                WHERE NOT EXISTS (
                SELECT 1
                FROM registered_devices.device_staging
                WHERE device_staging.device_id = registered_devices.{table_name}.device_id
                AND device_staging.device_type = %s
                AND device_staging.model_name = %s
            );
           """, (device_type, model_name))
        db_connection.commit()

print("✅ All devices processed successfully!")

# # Cleanup: Truncate the staging table
# cur.execute("TRUNCATE TABLE registered_devices.device_staging;")
# db_connection.commit()
# print("🧹 Cleaned up staging table")

# Close DB connection
cur.close()
db_connection.close()

# Function to insert device data into its corresponding table
# Now process the devices one by one
