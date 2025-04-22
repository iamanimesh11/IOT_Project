import os
import sys
import psycopg2
import configparser
import logging
import datetime
from flask import Flask, request, jsonify  # Import Flask components

# --- Configuration and Setup (Keep your existing config loading) ---
# Determine the correct base directory dynamically (similar to your setup script)
# AIRFLOW_HOME = os.getenv("AIRFLOW_HOME", "/opt/airflow")
# if AIRFLOW_HOME != "/opt/airflow":
#     BASE_DIR = os.path.abspath(os.path.join(AIRFLOW_HOME, ".."))
#     AIRFLOW_HOME = BASE_DIR
# CONFIG_PATH = os.path.join(AIRFLOW_HOME, "common", "credentials", "config.ini")
# --- Simplified config path for this example ---
CONFIG_PATH = r"C:\Users\Acer\PycharmProjects\IOT_Project\common\credentials\config.ini"  # Adjust as needed

# Load the config file
config = configparser.ConfigParser()
if not os.path.exists(CONFIG_PATH):
    logging.error(f"Config file not found at: {CONFIG_PATH}")
    sys.exit(1)  # Exit if config is missing
config.read(CONFIG_PATH)

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Database connection details (Keep your existing DB config loading) ---
try:
    db_config = config['database']
    db_host = db_config['host']
    db_username = db_config['user']
    db_password = db_config['password']
    db_port = db_config['port']
    db_database_name = db_config['database']
except KeyError as e:
    logging.error(f"Missing database configuration key: {e}")
    sys.exit(1)

# Subscription duration (Example: 1 hour) - Can be configured later
SUBSCRIPTION_DURATION_SECONDS = 3600


# --- Database Connection Function (Keep your get_db_connection function) ---
def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    conn = None
    try:
        conn = psycopg2.connect(
            dbname=db_database_name,
            user=db_username,
            password=db_password,
            host=db_host,  # Use configured host
            port=db_port
        )
        logging.debug("Database connection successful.")
        return conn
    except psycopg2.Error as e:
        logging.error(f"Error connecting to database: {e}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error during DB connection: {e}")
        return None


# --- Flask Application ---
app = Flask(__name__)  # Create the Flask app instance


# --- Define the POST route ---
@app.route('/event/<string:device_id>', methods=['POST'])
def handle_subscription(device_id):
    """
    Handles POST requests to subscribe or renew a device's subscription.
    (Backend logic will be added here later)
    """
    logging.info(f"Received POST request for device_id: {device_id}")

    # --- Placeholder for backend logic ---
    # We will add database interaction here in the next steps.
    # For now, just return a simple success message.

    # Example: Calculate timestamps (we'll use these later)
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    expires_at_utc = now_utc + datetime.timedelta(seconds=SUBSCRIPTION_DURATION_SECONDS)

    # --- Placeholder Response ---
    response_data = {
        "message": "Subscription request received (backend processing pending)",
        "device_id": device_id,
        "received_at": now_utc.isoformat(),
        "calculated_expiry": expires_at_utc.isoformat()  # For info only right now
    }
    return jsonify(response_data), 202  # 202 Accepted: Request received, processing not complete


# --- Main execution (for running the Flask app) ---
if __name__ == '__main__':
    # Run the app (use debug=True only for development)
    # Listen on 0.0.0.0 to be accessible from other machines on the network
    app.run(host='0.0.0.0', port=5001, debug=True)
import os
import sys
import psycopg2
import configparser
import logging
import datetime
import json  # Needed for serializing the message
from flask import Flask, request, jsonify
from kafka import KafkaProducer  # Import KafkaProducer

# --- Configuration and Setup (Keep your existing config loading) ---
# ... (rest of your config loading code) ...
CONFIG_PATH = r"C:\Users\Acer\PycharmProjects\IOT_Project\common\credentials\config.ini"  # Adjust as needed
config = configparser.ConfigParser()
if not os.path.exists(CONFIG_PATH):
    logging.error(f"Config file not found at: {CONFIG_PATH}")
    sys.exit(1)
config.read(CONFIG_PATH)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Database connection details (Keep your existing DB config loading) ---
# ... (db config loading) ...

# --- Kafka Configuration ---
try:
    kafka_config = config['kafka']
    KAFKA_BOOTSTRAP_SERVERS = kafka_config.get('bootstrap_servers', 'localhost:9092')  # Default if not in config
    SUBSCRIPTION_TOPIC = kafka_config.get('subscription_topic', 'subscription_requests')  # Default if not in config
except KeyError:
    logging.warning("Kafka configuration section not found in config. Using defaults.")
    KAFKA_BOOTSTRAP_SERVERS = 'localhost:9092'
    SUBSCRIPTION_TOPIC = 'subscription_requests'

# Subscription duration (Example: 1 hour)
SUBSCRIPTION_DURATION_SECONDS = 3600


# --- Kafka Producer Setup ---
# It's generally better to initialize the producer once rather than per request
# For simplicity here, we'll create it within the request context,
# but consider a more robust initialization for production.
def get_kafka_producer():
    try:
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')  # Serialize message to JSON bytes
        )
        logging.info(f"Kafka producer connected to {KAFKA_BOOTSTRAP_SERVERS}")
        return producer
    except Exception as e:
        logging.error(f"Failed to connect Kafka producer: {e}")
        return None


# --- Database Connection Function (We won't use it directly in the endpoint anymore) ---
# def get_db_connection():
#     ... (keep the function definition if needed elsewhere, but the endpoint won't call it)

# --- Flask Application ---
app = Flask(__name__)


# --- Define the POST route ---
@app.route('/event/<string:device_id>', methods=['POST'])
def handle_subscription(device_id):
    """
    Handles POST requests by publishing a subscription event to Kafka.
    """
    logging.info(f"Received POST request for device_id: {device_id}")

    producer = None  # Initialize producer variable
    try:
        # 1. Calculate Timestamps
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        # We don't calculate expires_at here anymore, the consumer will do that.

        # 2. Prepare Kafka Message
        subscription_event = {
            "device_id": device_id,
            "event_type": "subscribe",  # Or "renew" - could add logic later
            "requested_at_iso": now_utc.isoformat(),
            "requested_at_unix": now_utc.timestamp(),  # Unix timestamp can be useful
            "subscription_duration_seconds": SUBSCRIPTION_DURATION_SECONDS
            # Add any other relevant info from the request if needed
        }

        # 3. Get Kafka Producer
        producer = get_kafka_producer()
        if not producer:
            # Error already logged by get_kafka_producer
            return jsonify({"error": "Failed to connect to event stream backend"}), 503  # Service Unavailable

        # 4. Publish to Kafka
        future = producer.send(SUBSCRIPTION_TOPIC, value=subscription_event, key=device_id.encode('utf-8'))  # Use device_id as key for partitioning
        # Optional: Wait for send confirmation (adds latency, but ensures message is sent)
        # try:
        #     record_metadata = future.get(timeout=10)
        #     logging.info(f"Message sent to Kafka topic {record_metadata.topic} partition {record_metadata.partition} offset {record_metadata.offset}")
        # except Exception as e:
        #     logging.error(f"Error waiting for Kafka send confirmation: {e}")
        #     # Decide how to handle: maybe retry, maybe return error
        #     return jsonify({"error": "Failed to reliably send event to backend"}), 500

        logging.info(f"Published event for {device_id} to Kafka topic {SUBSCRIPTION_TOPIC}")

        # 5. Return Accepted Response
        response_data = {
            "message": "Subscription request accepted for processing",
            "device_id": device_id,
            "request_timestamp": now_utc.isoformat()
        }
        # 202 Accepted is appropriate here, as processing is asynchronous
        return jsonify(response_data), 202

    except Exception as e:
        # General error handling
        logging.error(f"Unexpected error processing request for {device_id}: {e}")
        return jsonify({"error": "An internal error occurred"}), 500

    finally:
        # Ensure producer is closed/flushed if created
        if producer:
            producer.flush()  # Ensure all buffered messages are sent
            producer.close()
            logging.debug("Kafka producer flushed and closed.")


# --- Main execution (for running the Flask app) ---
if __name__ == '__main__':
    # Remember to use Gunicorn/uWSGI for production
    app.run(host='0.0.0.0', port=5001, debug=True)  # Use debug=False in production
