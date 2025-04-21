import time
import json
from kafka import KafkaConsumer
import os 
import sys


AIRFLOW_HOME = os.getenv("AIRFLOW_HOME", "/opt/airflow")
if AIRFLOW_HOME != "/opt/airflow":
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    AIRFLOW_HOME = BASE_DIR
    print(BASE_DIR)

SCRIPTS_PATH = os.path.join(AIRFLOW_HOME, "scripts") 
sys.path.append(SCRIPTS_PATH)
common_PATH = os.path.join(AIRFLOW_HOME, "common") 
sys.path.append(common_PATH)
common_PATH = os.path.join(AIRFLOW_HOME, "common","logging_and_monitoring","logs") 
sys.path.append(common_PATH)


from logging_and_monitoring.centralized_logging import setup_logger

from utils.db_utils import bulk_insert_into_road_Table
from utils.Database_connection_Utils import connect_Database
consumer_Script_logs_path=os.path.join(common_PATH, "kafka_consumer.log")

consumer_Script_logger = setup_logger("database_logging", "consumer_script", "kafka", consumer_Script_logs_path)

# Set `earliest = True` if  want to read old messages
earliest = True
def consumer1():
    try: 
        consumer = KafkaConsumer(
            "road-topic",  
            bootstrap_servers='kafka:9092',
            auto_offset_reset="earliest", #if earliest else "latest",
            value_deserializer=lambda v: json.loads(v.decode('utf-8')),
            enable_auto_commit=True,  # Enable auto-commit
        )
        
        consumer_Script_logger.info("Connected tooo Kafka. Listening for messages...")
        conn= connect_Database()
        consumer_Script_logger.info(f"conn: {conn}")
    
        if conn is None:
            consumer_Script_logger.critical("Failed to establish database connection.", extra={"stage": "start"})
            exit()
        messages = []
        while True:  
            for message in consumer:
                consumer_Script_logger.info(f"Received message: {message.value}")
                consumer_Script_logger.info(f"type of messages :{type(message)}")
                msg = message.value  # Extract the JSON object

                if isinstance(msg, list):  # If message is a list, extend instead of append
                    messages.extend(msg)
                else:
                    messages.append(msg)
                
                if len(messages) > 10:
                    messages.pop(0)
                consumer_Script_logger.info("insertion begins...")  # Log before inserting
                bulk_insert_into_road_Table(messages, conn)  # Perform insertion
                consumer_Script_logger.info("insertion completed...")  # Log after insertion
                    
    except Exception as e:
        consumer_Script_logger.error(f"Exception occurred: {str(e)}")
        consumer.close()


# Run consumer forever
if __name__ == "__main__":
        consumer1()
       
