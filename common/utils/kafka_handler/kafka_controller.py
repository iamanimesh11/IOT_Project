import json,os
import sys,logging
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
    KAFKA_BROKERS_HOST = "localhost:9092" # For local runs outside compose
else:
    logging.info("Detected environment inside Docker or AIRFLOW_HOME not set. Using relative path.")
    device_json_path= os.path.join("json_files","device_models.json") # Corrected path for Docker context
    KAFKA_BROKERS_HOST = "kafka:9092" # Use the service name 'kafka' from docker-compose

logging.info(f"Using device models path: {device_json_path}")
logging.info(f"Kafka brokers for consumer containers: {KAFKA_BROKERS_HOST}")

# --- Configuration ---
KAFKA_CONSUMER_IMAGE_NAME = "iot_project-kafka_consumer_container_creator" # Name of the image built by Dockerfile.kafka_consumer
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

# --- Start Kafka Consumer Containers ---
logging.info(f"🚀 Starting Kafka Consumer containers for image '{KAFKA_CONSUMER_IMAGE_NAME}'...")

processed_device_types = set() # Keep track of types already processed
for device_type, devices in device_data.items(): # device_data is a dictionary like {"tv": [...], "ac": [...]}
    if not devices or device_type in processed_device_types:
        continue # Skip if no devices for this type or already processed

    try:
        container_name = f"kafka_consumer_{device_type}"
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
            "KAFKA_BROKERS": KAFKA_BROKERS_HOST,
            "PYTHONUNBUFFERED": "1"
            # Add DB connection strings or other processing-related env vars here later
        }

        # Run the new container using the SDK
        logging.info(f"  Starting container '{container_name}' with image '{KAFKA_CONSUMER_IMAGE_NAME}'...")
        container = docker_client.containers.run(
            image=KAFKA_CONSUMER_IMAGE_NAME,
            detach=True,
            name=container_name,
            network=DOCKER_NETWORK,
            environment=environment_vars,
            command=["python", "kafka_consumer.py"] # Explicitly run the consumer script
        )

        logging.info(f"  ✅ Successfully started container '{container_name}' (ID: {container.short_id})")
        processed_device_types.add(device_type) # Mark this type as processed

    except APIError as e:
        logging.error(f"  ⚠️ Docker API Error starting container '{container_name}': {e}")
    except Exception as e:
        logging.error(f"  ❌ An unexpected error occurred while processing type {device_type}: {e}")

logging.info("\n✅ Kafka Controller finished launching consumer containers.")