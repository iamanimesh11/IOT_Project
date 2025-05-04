import json
import logging
import psycopg2
import redis
from kafka import KafkaConsumer
from datetime import datetime, timedelta
from dateutil import parser # For parsing ISO timestamp string

# --- Load Config ---
import configparser
import os
# Use the correct path for your config file
CONFIG_PATH = r"E:\IOT_Project\common\credentials\config.ini"
config = configparser.ConfigParser()
if not os.path.exists(CONFIG_PATH):
    logging.error(f"Config file not found at: {CONFIG_PATH}")
    exit(1)
config.read(CONFIG_PATH)

# --- Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Kafka Config ---
# Access the 'kafka' section directly
kafka_config = config['kafka']
KAFKA_BOOTSTRAP_SERVERS = kafka_config.get('bootstrap_servers', 'localhost:9092')
SUBSCRIPTION_TOPIC = kafka_config.get('subscription_topic', 'subscription_requests')

# --- Redis Config ---
# Consider making Redis host/port configurable too
r = redis.Redis(host='localhost', port=6379, db=0)

# --- PostgreSQL Config ---
# Load DB config from the config file
db_config_section = config['database']
db_config = {
    'host': db_config_section.get('host', 'localhost'),
    'database': db_config_section.get('database'),
    'user': db_config_section.get('user'),
    'password': db_config_section.get('password'),
    'port': db_config_section.get('port', 5432)
}


# --- PostgreSQL Connection ---
def get_db_connection():
    try:
        conn = psycopg2.connect(**db_config)
        return conn
    except Exception as e:
        logging.error(f"Error connecting to PostgreSQL ({db_config.get('host')}): {e}")
        return None


# --- Kafka Consumer ---
def get_kafka_consumer():
    try:
        consumer = KafkaConsumer(
            SUBSCRIPTION_TOPIC,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            group_id="subscription_processor_group", # Use a descriptive group ID
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )
        logging.info("Kafka consumer connected.")
        return consumer
    except Exception as e:
        logging.error(f"Kafka consumer connection failed: {e}")
        return None


# --- Process Subscription Event ---
def process_subscription_event(event):
    service_id = event.get("service_id")
    device_id = event.get("device_id")
    expiry_hours = int(event.get("expiry_hours", 24))
    timestamp_str = event.get("timestamp") # Timestamp from the event (when request was received)

    try:
        subscribed_at_dt = parser.isoparse(timestamp_str) if timestamp_str else datetime.now(datetime.timezone.utc)
    except ValueError:
        logging.warning(f"Could not parse timestamp string '{timestamp_str}', using current time.")
        subscribed_at_dt = datetime.now(datetime.timezone.utc)

    if not service_id or not device_id:
        logging.error("Missing service_id or device_id in event.")
        return

    redis_key = f"sub:{service_id}:{device_id}"

    # Check Redis for existing subscription
    if r.exists(redis_key):
        logging.info(f"Device {device_id} subscription for service {service_id} already exists in Redis cache. Skipping DB insert.")
        return  # Skip if already subscribed in Redis

    # Store in Redis
    expires_at_dt = subscribed_at_dt + timedelta(hours=expiry_hours)
    subscription_data = {
        "service_id": service_id,
        "device_id": device_id,
        "subscribed_at": subscribed_at_dt.isoformat(),
        "expires_at": expires_at_dt.isoformat()
    }

    r.set(redis_key, json.dumps(subscription_data), ex=int(expiry_hours * 3600))  # Expiry in seconds

    # Store in PostgreSQL
    conn = get_db_connection()
    if not conn:
        logging.error("Failed to connect to PostgreSQL.")
        return

    cursor = None # Initialize cursor
    try:
        cursor = conn.cursor()
        # Insert into the correct table with correct columns
        cursor.execute("""
            INSERT INTO subscriptions.subscribed_devices
                (service_id, device_id, subscribed_at, expires_at, subscription_status)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING; -- Optional: Decide how to handle conflicts if needed
            """, (service_id, device_id, subscribed_at_dt, expires_at_dt, 'active')) # Use datetime objects
        conn.commit()
        logging.info(f"Device {device_id} subscription for service {service_id} added to PostgreSQL.")
    except Exception as e:
        logging.error(f"Error inserting subscription into PostgreSQL: {e}")
        conn.rollback() # Rollback on error
    finally:
        if cursor: cursor.close()
        conn.close()


# --- Main Consumer Loop ---
def start_consumer():
    consumer = get_kafka_consumer()
    if not consumer:
        logging.error("Kafka consumer failed to start.")
        return

    for message in consumer:
        event = message.value
        logging.info(f"Received subscription event: {event}")
        process_subscription_event(event)


if __name__ == "__main__":
    start_consumer()
