from faker import Faker
import psycopg2
import time,os,sys
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from common.utils.Database_connection_Utils import connect_and_create_schemas
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

fake = Faker()
db_connection = connect_and_create_schemas()
if not db_connection:
    logging.critical("Failed to connect to the database. Exiting.")
    exit()
cur = db_connection.cursor()
start_time= time.time()
DEVICE_ID_FETCH_CHUNK_SIZE = 1000
CUSTOMER_INSERT_BATCH_SIZE = 1000

def generate_customer_data(device_info_list):
    """Generates customer data for a list of device IDs."""
    customer_batch = []
    for device_id ,device_type,model_name in device_info_list:
        customer_batch.append((
            fake.name(),
            fake.email(),
            fake.phone_number(),
            fake.address().replace('\n', ', '),
            device_id,
            device_type,  # Include device_type
            model_name  # Include model_name
        ))
    return customer_batch


def insert_customer_batch(cursor, connection, customer_data):
    """Inserts a batch of customer data into the database."""
    if not customer_data:  # Avoid empty inserts
        logging.warning("Attempted to insert an empty customer batch.")
        return
    try:
        sql = """
                    INSERT INTO customers.customer_staging
                    (full_name, email, phone, address, device_id, device_type, model_name)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)         
                    ON CONFLICT (device_id)
                    DO UPDATE SET
                        full_name = EXCLUDED.full_name,
                        email = EXCLUDED.email,
                        phone = EXCLUDED.phone,
                        address = EXCLUDED.address,
                        device_type = EXCLUDED.device_type,
                        model_name = EXCLUDED.model_name;
                """
        cursor.executemany(sql, customer_data)
        logging.info(f"Processed upsert for {len(customer_data)} customer staging records.")
        return True
    except psycopg2.Error as e:
        connection.rollback()
        logging.error(f"❌ Error inserting batch of {len(customer_data)} customers: {e}")
        return False

total_devices_processed = 0
total_customers_inserted = 0
offset = 0
try: # Wrap main logic in try...finally for cleanup
    while True:
        # Step 1: Fetch a chunk of existing device IDs
        cur.execute("""
            SELECT device_id,device_type,model_name
            FROM registered_devices.device_Staging
            ORDER BY device_id  
            LIMIT %s
            OFFSET %s
        """, (DEVICE_ID_FETCH_CHUNK_SIZE, offset))
        device_info_chunk = cur.fetchall()

        if not device_info_chunk:
            logging.info("No more device IDs to process.")
            break  # No more device IDs to process


        num_devices_in_chunk = len(device_info_chunk)
        logging.info(f"Fetched {num_devices_in_chunk} device info records (offset: {offset}).")


        # Step 2: Generate customer data for the fetched device IDs
        customer_data_chunk = generate_customer_data(device_info_chunk)
        print(f"length: {len(customer_data_chunk)}")
        # Step 3: Insert the generated customer data
        if customer_data_chunk:
            if insert_customer_batch(cur, db_connection, customer_data_chunk):
                total_customers_inserted += len(customer_data_chunk)
                logging.info(f"{len(customer_data_chunk)} Inserted succesfull")

        total_devices_processed += num_devices_in_chunk
        offset += DEVICE_ID_FETCH_CHUNK_SIZE

    logging.info("Committing all inserted customer data...")
    db_connection.commit()

except psycopg2.Error as db_err:
    logging.error(f"Database error during processing: {db_err}")
    if db_connection:
        db_connection.rollback() # Rollback any pending transaction
except Exception as e:
    logging.error(f"An unexpected error occurred: {e}")
    if db_connection:
        db_connection.rollback()
finally:
    # Clean up
    if cur:
        cur.close()
        logging.info("Database cursor closed.")
    if db_connection:
        db_connection.close()
        logging.info("Database connection closed.")

    end_time = time.time()
    logging.info(f"✅ Finished processing {total_devices_processed} devices.")
    logging.info(f"Total customers prepared/inserted: {total_customers_inserted}")
    logging.info(f"Total time taken: {end_time - start_time:.2f} seconds")