import random
import time
import uuid
import json,os
from datetime import datetime
import logging # Import logging
import socket  # Import socket for handling socket errors

import paho.mqtt.client as mqtt
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# MQTT Broker settings (local Docker container)


def get_root_Directory_path(n):
    path=os.path.abspath(__file__)
    for _ in range(n+1):
        path=os.path.dirname(path)
    return path

Directory = os.getenv("AIRFLOW_HOME", "inside_docker")  # Default to Airflow's path

if Directory != "inside_docker":
    root_dir_path=get_root_Directory_path(3)
    logging.info(f"Detected environment outside Docker (AIRFLOW_HOME='{Directory}'). Calculating root path.")
    device_json_path= os.path.join(root_dir_path, "common", "utils","json_files","device_models.json")
    device_profile_path= os.path.join(root_dir_path, "common", "utils","json_files","devices_profiles.json")
    MQTT_BROKER = "localhost"
    MQTT_PORT = 1883
else:
    logging.info("Detected environment inside Docker or AIRFLOW_HOME not set. Using relative path.")
    device_json_path= os.path.join("json_files","device_models.json") # Corrected path for Docker context
    device_profile_path= os.path.join("json_files","device_profiles.json")
    MQTT_BROKER = "mosquitto"
    MQTT_PORT = 1883

logging.info(f"Using device models path: {device_json_path}")
logging.info(f"Using device profiles path: {device_profile_path}")
logging.info(f"Attempting to connect to MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")

# --- Load Device Data with Error Handling ---
try:
    with open(device_json_path) as f:
        device_data = json.load(f)
    logging.info(f"Successfully loaded device models from {device_json_path}")
except FileNotFoundError:
    logging.error(f"FATAL: Device models file not found at {device_json_path}")
    exit(1) # Exit if essential file is missing
except json.JSONDecodeError as e:
    logging.error(f"FATAL: Failed to decode JSON from {device_json_path}: {e}")
    exit(1)
    
try:
    with open(device_profile_path) as f:
        profiles = json.load(f)
    logging.info(f"Successfully loaded device profiles from {device_profile_path}")
except FileNotFoundError:
    logging.error(f"FATAL: Device profiles file not found at {device_profile_path}")
    exit(1)
except json.JSONDecodeError as e:
    logging.error(f"FATAL: Failed to decode JSON from {device_profile_path}: {e}")
    exit(1)   
    
    
# Create a flat list of all devices, adding the device_type to each device object
all_devices = []
for device_type, devices_list in device_data.items():
    for device in devices_list:
        all_devices.append({**device, "device_type": device_type}) # Add device_type key


# Simulated device models and behaviors


# Function to generate telemetry
def generate_telemetry(device):
    device_type = device["device_type"]
    profile = profiles.get(device_type, {})

    status_options = profile.get("status", ["unknown"])
    error_options = profile.get("errors", [])
    error = random.choice(error_options) if random.random() < 0.1 else None


    payload = {
        "device_id": device["device_id"],
        "device_type":device["device_type"],
        "model_name": device["model_name"],
        "status": random.choice(status_options),
        "error_code": error,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    }

    return payload

# Connect to MQTT
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2) # Fix DeprecationWarning
try:
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start() # Start background thread for handling reconnects etc.
    logging.info(f"✅ Successfully connected to MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
except socket.gaierror as e:
    logging.error(f"❌ MQTT Connection Error: Could not resolve hostname '{MQTT_BROKER}'. Check network or service name. Error: {e}")
    exit(1)
except ConnectionRefusedError as e:
     logging.error(f"❌ MQTT Connection Error: Connection refused by broker at {MQTT_BROKER}:{MQTT_PORT}. Is it running? Error: {e}")
     exit(1)
except Exception as e:
    logging.error(f"❌ Failed to connect to MQTT Broker ({MQTT_BROKER}:{MQTT_PORT}): {e}")
    exit(1) # Exit if cannot connect
    
# Loop to simulate data sending
logging.info("🚀 Starting device simulation...")
try:
    while True:
        device=random.choice(all_devices) # Select from the flat list
        topic=f"iot/telemetry/{device['device_type']}/{device['device_id']}"
        payload=json.dumps(generate_telemetry(device))
        client.publish(topic, payload)

        logging.info(f"📡 Published to [{topic}]: {payload}")
        #time.sleep(random.uniform(1, 3))  # Send every 1–3 seconds
        time.sleep(60)  # Send every 1–3 seconds
except KeyboardInterrupt:
    logging.info("\n🔌 Simulation stopped by user.")
finally:
    logging.info("Disconnecting MQTT client...")
    client.loop_stop() # Stop the background thread
    client.disconnect()
+    logging.info("👋 MQTT Client disconnected.")
