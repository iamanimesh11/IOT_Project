import json,os
# import subprocess # No longer needed
import sys,logging # For exiting on error
import docker # Import the Docker SDK
from docker.errors import APIError, NotFound # Import specific Docker errors
# --- Basic Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
    MQTT_BROKER_HOST = "localhost"
    KAFKA_BROKERS_HOST = "localhost:9092" # For local runs outside compose
    MQTT_PORT = 1883
else:
    logging.info("Detected environment inside Docker or AIRFLOW_HOME not set. Using relative path.")
    device_json_path= os.path.join("json_files","device_models.json") # Corrected path for Docker context
    device_profile_path= os.path.join("json_files","device_profiles.json")
    MQTT_BROKER_HOST = "mosquitto"
    KAFKA_BROKERS_HOST = "kafka:29092 " # Use the service name 'kafka' from docker-compose
    MQTT_PORT = 1883

logging.info(f"Using device models path: {device_json_path}")
logging.info(f"Using device profiles path: {device_profile_path}")
logging.info(f"Attempting to connect to MQTT Broker: {MQTT_BROKER_HOST}:{MQTT_PORT}")

# --- Configuratiomqtt_consumern ---
IMAGE_NAME = "iot_project-mqtt_consumer_container_creator" # Build this image first: docker build -t mqtt_consumer_image ./common/utils/test-mqtt
DOCKER_NETWORK = "iot_project_my_custom_network" # Default network name format: <project_directory>_<network_name>

# --- Load Device Data ---
try:
    with open(device_json_path) as f:
        device_data=json.load(f)
except FileNotFoundError:
    logging.error(f"❌ Error: Device models file not found at {device_json_path}")
    sys.exit(1)
except json.JSONDecodeError as e:
    logging.error(f"❌ Error: Failed to decode JSON from {device_json_path}: {e}")
    sys.exit(1)
except Exception as e:
    logging.error(f"❌ An unexpected error occurred while reading {device_json_path}: {e}")
    sys.exit(1)

# --- Initialize Docker Client ---
try:
    # Connect to Docker daemon via the mounted socket
    docker_client = docker.from_env()
    logging.info("✅ Successfully connected to Docker daemon.")
except Exception as e:
    logging.error(f"❌ Failed to connect to Docker daemon via socket. Is it mounted correctly? Error: {e}")
    sys.exit(1)
# --- Start Containers ---
logging.info(f"🚀 Starting MQTT Consumer containers for image '{IMAGE_NAME}'...")

processed_device_types = set() # Keep track of types already processed
for device_type, devices in device_data.items(): # device_data is a dictionary like {"tv": [...], "ac": [...]}
    if not devices or device_type in processed_device_types:
        continue # Skip if no devices for this type or already processed

    try:
        container_name = f"mqtt_consumer_{device_type}"
        logging.info(f"\nProcessing device type: {device_type} -> Container: {container_name}")

        # Remove existing container with the same name first
        logging.info(f"  Checking for and removing existing container '{container_name}'...")
        try:
            existing_container = docker_client.containers.get(container_name)
            existing_container.remove(force=True)
            logging.info(f"  Removed existing container '{container_name}'.")
        except NotFound:
            logging.info(f"  No existing container named '{container_name}' found.")
        except APIError as e:
            logging.error(f"  ⚠️ Docker API error removing container '{container_name}': {e}")
            continue # Skip to next device type if removal fails

        # Define environment variables for the new container
        environment_vars = {
            "DEVICE_TYPE": device_type,
            "MQTT_BROKER": MQTT_BROKER_HOST,
            "KAFKA_BROKERS": KAFKA_BROKERS_HOST,
            "PYTHONUNBUFFERED": "1"
        }

        # Run the new container using the SDK
        logging.info(f"  Starting container '{container_name}' with image '{IMAGE_NAME}'...")
        container = docker_client.containers.run(
            image=IMAGE_NAME,
            detach=True,
            name=container_name,
            network=DOCKER_NETWORK,
            environment=environment_vars,
            command=["python", "mqtt_consumer.py"] # <-- Add this line

        )

        logging.info(f"  ✅ Successfully started container '{container_name}' (ID: {container.short_id})")
        processed_device_types.add(device_type) # Mark this type as processed

    except APIError as e:
        logging.error(f"  ⚠️ Docker API Error starting container '{container_name}': {e}")
    except Exception as e:
        logging.error(f"  ❌ An unexpected error occurred while processing type {device_type}: {e}")
