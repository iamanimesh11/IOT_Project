import psycopg2
import io
import re
import logging
import json
import time
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

start_time = time.time()
from Database_connection_Utils import connect_and_create_schemas

db_connection = connect_and_create_schemas()
cur = db_connection.cursor()

staging_table_name = "device_staging"
checked_staging_table = False


# Function to check if a table exists for device type and model

def check_staging_table_exists():
    global checked_staging_table
    if checked_staging_table:
        return True
    cur.execute("""
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = 'registered_devices'
        AND table_name = %s
    """, (staging_table_name,))
    exists = cur.fetchone() is not None
    if exists:
        checked_staging_table = True
    return exists


# Function to create a table dynamically if not exists
def create_staging_table():
    create_query = f"""
            CREATE TABLE IF NOT EXISTS registered_devices.{staging_table_name} (
                device_id VARCHAR(255) PRIMARY KEY,
                device_type VARCHAR(50) NOT NULL,
                model_name VARCHAR(255) NOT NULL,
                alias VARCHAR(255),
                reportable BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT now()
            );
        """
    cur.execute(create_query)
    db_connection.commit()
    print(f"✅ Created table: {staging_table_name}")


cur.execute("SET search_path TO registered_devices;")
db_connection.commit()
logging.info("Set search_path to Registered_Devices")


def dump_device_data_to_staging(devices_data):
    """
    Dumps the provided list of device data into the registered_devices.device_staging table.
    """
    print(f"Dumping data: {devices_data}")
    cur = db_connection.cursor()

    inserted_count = 0
    batch_size = 500
    csv_data = io.StringIO()

    try:
        # Set the search path to 'iot_lg'
        cur.execute('SHOW search_path;')
        search_path = cur.fetchone()
        #logging.info(f"Current search_path before dump: {search_path}")

        # Check and create the staging table if it doesn't exist
        if not check_staging_table_exists():
            create_staging_table()
        else:
            print(f"✅ Table {staging_table_name} already exists!")

        for device in devices_data:
            device_id = device['deviceId']
            device_type = device['deviceInfo']['deviceType']
            model_name = device['deviceInfo']['modelName']
            alias = device['deviceInfo']['alias']
            reportable = device['deviceInfo']['reportable']

            csv_data.write(f"{device_id},{device_type},{model_name},{alias},{reportable}\n")
            inserted_count += 1

            if inserted_count >= batch_size:
                logging.debug(f"Batch size reached, inserting batch of {batch_size} records.")
                csv_data.seek(0)
                try:
                    cur.copy_from(csv_data, f"{staging_table_name}", sep=',', columns=(
                        'device_id', 'device_type', 'model_name', 'alias', 'reportable'))
                    db_connection.commit()
                    logging.info(f"Batch of {batch_size} records inserted into {staging_table_name}.")
                except Exception as e:
                    logging.error(f"Error inserting batch: {e}")
                    db_connection.rollback()
                csv_data = io.StringIO()
                inserted_count = 0

        # Insert any remaining records
        if inserted_count > 0:
            logging.debug(f"Inserting remaining {inserted_count} records.")
            csv_data.seek(0)
            try:
                cur.copy_from(csv_data, f"{staging_table_name}", sep=',', columns=(
                    'device_id', 'device_type', 'model_name', 'alias', 'reportable'))
                db_connection.commit()
                logging.info(f"Remaining {inserted_count} records inserted into {staging_table_name}.")
            except Exception as e:
                logging.error(f"Error inserting remaining records: {e}")
                db_connection.rollback()

    except Exception as e:
        logging.error(f"An error occurred during the dumping process: {e}")
        if db_connection:
            db_connection.rollback()
