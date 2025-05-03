import os
import sys
import psycopg2
import configparser
import logging
import requests
import json,time

# --- Configuration ---

# Assuming this script is run from its directory or the project root has paths set up
CONFIG_PATH = r"E:\IOT_Project\common\credentials\config.ini"
SERVICE_NAME_TO_SUBSCRIBE = "MyNewService"  # CHANGE THIS to the name of the service you want to subscribe
SUBSCRIPTION_API_BASE_URL = "http://localhost:8000" # Base URL of the 'POST subscribe Event.py' service

# --- Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Load Config ---
config = configparser.ConfigParser()
if not os.path.exists(CONFIG_PATH):
    logging.error(f"Config file not found at: {CONFIG_PATH}")
    sys.exit(1)
config.read(CONFIG_PATH)

# --- Database Config ---
try:
    db_config = config['database']
    db_host = db_config.get('host', 'localhost') # Default to localhost if not specified
    db_username = db_config['user']
    db_password = db_config['password']
    db_port = db_config.get('port', 5432) # Default PG port
    db_database_name = db_config['database']
except KeyError as e:
    logging.error(f"Missing database configuration key in {CONFIG_PATH}: {e}")
    sys.exit(1)

# --- Database Connection ---
def connect_db():
    """Connects to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            dbname=db_database_name,
            user=db_username,
            password=db_password,
            host=db_host,
            port=db_port
        )
        logging.info("Successfully connected to database.")
        return conn
    except psycopg2.Error as e:
        logging.error(f"Database connection failed: {e}")
        return None

# --- Fetch Service Details ---
def get_service_details(conn, service_name):
    """Fetches service_id and service_key for a given service name."""
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT service_id, service_key FROM subscriptions.services WHERE service_name = %s AND status = 'active'",
                (service_name,)
            )
            result = cur.fetchone()
            if result:
                logging.info(f"Found details for service '{service_name}'.")
                return {"service_id": str(result[0]), "service_key": result[1]} # Ensure service_id is string
            else:
                logging.error(f"Service '{service_name}' not found or not active in subscriptions.services table.")
                return None
    except psycopg2.Error as e:
        logging.error(f"Error fetching service details: {e}")
        return None

# --- Fetch Device IDs ---
def get_all_device_ids(conn):
    """Fetches all device_ids from the registered_devices.device_staging table."""
    device_ids = []
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT device_id FROM registered_devices.device_staging")
            results = cur.fetchall()
            device_ids = [row[0] for row in results]
            logging.info(f"Fetched {len(device_ids)} device IDs from device_staging.")
    except psycopg2.Error as e:
        logging.error(f"Error fetching device IDs: {e}")
    return device_ids

# --- Subscribe Function ---
def subscribe_device(device_id, service_info):
    """Sends a POST request to subscribe a device."""
    url = f"{SUBSCRIPTION_API_BASE_URL}/subscribe/{device_id}"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {service_info["service_key"]}'
    }
    payload = {
        "service_id": service_info["service_id"]
        # Add "expiry_hours": X here if you want non-default expiry
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        if response.status_code == 202 or response.status_code == 200: # 202 Accepted or 200 OK (if already subscribed)
            logging.info(f"Subscription request for device '{device_id}' successful (Status: {response.status_code}). Response: {response.text}")
        else:
            logging.warning(f"Subscription request for device '{device_id}' failed (Status: {response.status_code}). Response: {response.text}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending subscription request for device '{device_id}': {e}")

# --- Main Execution ---
if __name__ == "__main__":
    logging.info("--- Starting Bulk Subscription Script ---")
    db_conn = connect_db()
    if not db_conn:
        sys.exit(1)

    service_details = get_service_details(db_conn, SERVICE_NAME_TO_SUBSCRIBE)
    if not service_details:
        db_conn.close()
        sys.exit(1)

    all_devices = get_all_device_ids(db_conn)

    if not all_devices:
        logging.warning("No device IDs found in the database. Exiting.")
    else:
        logging.info(f"Attempting to subscribe service '{SERVICE_NAME_TO_SUBSCRIBE}' to {len(all_devices)} devices...")
        for dev_id in all_devices:
            
            subscribe_device(dev_id, service_details)
            time.sleep(300)

    db_conn.close()
    logging.info("--- Bulk Subscription Script Finished ---")