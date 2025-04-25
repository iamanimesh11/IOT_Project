import json
import logging
import psycopg2
import redis
from kafka import KafkaConsumer
from datetime import datetime, timedelta

# --- Load Config ---
import configparser
import os

CONFIG_PATH = r"C:\Users\Acer\PycharmProjects\IOT_Project\common\credentials\config.ini"
config = configparser.ConfigParser()
if not os.path.exists(CONFIG_PATH):
    logging.error(f"Config file not found at: {CONFIG_PATH}")
    exit(1)
config.read(CONFIG_PATH)

# --- Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Kafka Config ---
kafka_config = config.get('kafka', {})
KAFKA_BOOTSTRAP_SERVERS = kafka_config.get('bootstrap_servers', 'localhost:9092')
SUBSCRIPTION_TOPIC = kafka_config.get('subscription_topic', 'subscription_requests')

# --- Redis Config ---
r = redis.Redis(host='localhost', port=6379, db=0)

# --- PostgreSQL Config ---
db_config = {
    'host': 'localhost',
    'database': 'your_database',
    'user': 'your_user',
    'password': 'your_password'
}


# --- PostgreSQL Connection ---
def get_db_connection():
    try:
        conn = psycopg2.connect(**db_config)
        return conn
    except Exception as e:
        logging.error(f"Error connecting to PostgreSQL: {e}")
        return None


# --- Kafka Consumer ---
def get_kafka_consumer():
    try:
        consumer = KafkaConsumer(
            SUBSCRIPTION_TOPIC,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            group_id="subscription_group",
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
    timestamp = event.get("timestamp")

    if not service_id or not device_id:
        logging.error("Missing service_id or device_id in event.")
        return

    redis_key = f"sub:{service_id}:{device_id}"

    # Check Redis for existing subscription
    if r.exists(redis_key):
        logging.info(f"Device {device_id} is already subscribed.")
        return  # Skip if already subscribed in Redis

    # Store in Redis
    expiry_time = datetime.utcnow() + timedelta(hours=expiry_hours)
    subscription_data = {
        "service_id": service_id,
        "device_id": device_id,
        "timestamp": timestamp,
        "expiry_time": expiry_time.isoformat()
    }

    r.set(redis_key, json.dumps(subscription_data), ex=expiry_hours * 3600)  # Expiry in seconds

    # Store in PostgreSQL
    conn = get_db_connection()
    if not conn:
        logging.error("Failed to connect to PostgreSQL.")
        return

    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO subscription (service_id, device_id, timestamp, expiry_time)
            VALUES (%s, %s, %s, %s)
            """, (service_id, device_id, timestamp, expiry_time))
        conn.commit()
        logging.info(f"Device {device_id} subscription added to PostgreSQL.")
    except Exception as e:
        logging.error(f"Error inserting subscription into PostgreSQL: {e}")
    finally:
        cursor.close()
        conn.close()


# --- Main Consumer Loop ---
def start_consumer():
    consumer = get_kafka_consumer()
    if not consumer:
        logging.error("Kafka consumer failed to start.")
        return

    for message in consumer:
        event = message.value
        logging.info(f"Received event: {event}")
        process_subscription_event(event)


if __name__ == "__main__":
    start_consumer()



