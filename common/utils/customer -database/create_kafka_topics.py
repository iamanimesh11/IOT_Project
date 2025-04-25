import configparser
import psycopg2
from kafka.admin import KafkaAdminClient, NewTopic
import logging


from common.utils.Database_connection_Utils import connect_and_create_schemas
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
CONFIG_PATH = r"C:\Users\Acer\PycharmProjects\IOT_Project\common\credentials\config.ini"

def load_config(config_path):
    config = configparser.ConfigParser()
    config.read(config_path)
    return config

def read_device_models_from_json(input_file="device_models.json"):
    """Reads device type and model name pairs from a JSON file."""
    try:
        with open(input_file, 'r') as f:
            loaded_data = json.load(f)
            device_models = [(device_type, model_name) for device_type, model_name in loaded_data.items()]
            return device_models
    except FileNotFoundError:
        logging.error(f"Error: '{input_file}' not found.")
        return []
    except json.JSONDecodeError:
        logging.error(f"Error: Could not decode JSON from '{input_file}'.")
        return []
    except IOError as e:
        logging.error(f"Error reading from '{input_file}': {e}")
        return []

def initialize_kafka_admin_client(config):
    """Initializes and returns a KafkaAdminClient."""
    kafka_config = config['kafka']
    try:
        admin = KafkaAdminClient(
            bootstrap_servers=kafka_config.get('bootstrap_servers'),
            client_id='topic_creator'
        )
        return admin
    except Exception as e:
        logging.error(f"Error initializing KafkaAdminClient: {e}")
        return None
        
def check_and_create_kafka_topics(admin, topics):
    """Checks for existing Kafka topics and creates the new ones if they don't exist."""
    if admin:
        existing_topics = admin.list_topics()
        new_topics = [NewTopic(name=topic, num_partitions=1, replication_factor=1)
                      for topic in topics if topic not in existing_topics]

        if new_topics:
            try:
                admin.create_topics(new_topics)
                logging.info(f"Created topics: {[t.name for t in new_topics]}")
            except Exception as e:
                logging.error(f"Error creating Kafka topics: {e}")
        else:
            logging.info("All required topics already exist.")


def process_device_models_from_json_and_kafka_topics():

    config = load_config(CONFIG_PATH)
    device_models = read_device_models_from_json()

    # --- Step 1: Read device models from JSON ---
    if not device_models:
        logging.info("No device models found in the JSON file. Exiting.")
        return

    # --- Step 2: Format topic names ---
    topics = [f"{device_type.lower()}_{model.lower()}" for device_type, model in device_models]


    # --- Kafka admin client ---
    admin = initialize_kafka_admin_client(config)
    if not admin:
        return

    # --- Step 3 & 4: Check and create new topics ---
    check_and_create_kafka_topics(admin, topics)

    # --- Cleanup ---
    if admin:
        try:
            admin.close()
        except Exception as e:
            logging.error(f"Error closing KafkaAdminClient: {e}")
