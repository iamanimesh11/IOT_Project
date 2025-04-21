from faker import Faker
import random
import psycopg2
import time
from common.utils.Database_connection_Utils import connect_and_create_schemas

fake = Faker()
db_connection = connect_and_create_schemas()
cur = db_connection.cursor()
start_time= time.time()
DEVICE_ID_FETCH_CHUNK_SIZE = 1000
CUSTOMER_INSERT_BATCH_SIZE = 1000

def generate_customer_data(device_ids):
    """Generates customer data for a list of device IDs."""
    customer_batch = []
    for device_id in device_ids:
        customer_batch.append((
            fake.name(),
            fake.email(),
            fake.phone_number(),
            fake.address().replace('\n', ', '),
            device_id
        ))
    return customer_batch

def insert_customer_batch(cursor, connection, customer_data):
    """Inserts a batch of customer data into the database."""
    try:
        cursor.executemany("""
            INSERT INTO customer_staging.customer_staging
            (full_name, email, phone, address, device_id)
            VALUES (%s, %s, %s, %s, %s)
        """, customer_data)
        connection.commit()
        print(f"✅ Inserted {len(customer_data)} customers.")
    except psycopg2.Error as e:
        connection.rollback()
        print(f"❌ Error inserting batch of {len(customer_data)} customers: {e}")

total_devices_processed = 0
offset = 0

while True:
    # Step 1: Fetch a chunk of existing device IDs
    cur.execute("""
        SELECT device_id
        FROM customer_staging.device_Staging
        ORDER BY device_id  
        LIMIT %s
        OFFSET %s
    """, (DEVICE_ID_FETCH_CHUNK_SIZE, offset))
    device_id_chunk = [row[0] for row in cur.fetchall()]

    if not device_id_chunk:
        break  # No more device IDs to process

    num_devices_in_chunk = len(device_id_chunk)
    print(f"Fetched {num_devices_in_chunk} device IDs (offset: {offset}).")

    # Step 2: Generate customer data for the fetched device IDs
    customer_data_chunk = generate_customer_data(device_id_chunk)

    # Step 3: Insert the generated customer data
    if customer_data_chunk:
        insert_customer_batch(cur, db_connection, customer_data_chunk)

    total_devices_processed += num_devices_in_chunk
    offset += DEVICE_ID_FETCH_CHUNK_SIZE

print(f"✅ Finished processing {total_devices_processed} devices and associated customers.")

if cur:
    cur.close()
if db_connection:
    db_connection.close()

end_time = time.time()
print(f"Total time taken: {end_time - start_time} seconds")