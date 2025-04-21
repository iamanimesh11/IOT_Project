import time
import os
import sys
import json
import string
import random


from kafka import KafkaProducer
from datetime import datetime
from kafka.admin import KafkaAdminClient,NewTopic
from oauthlib.common import generate_timestamp

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

from utils.api_utils import get_nearby_roads_with_coordinates

from modify_Topics import create_kafka_topic
from logging_and_monitoring.centralized_logging import setup_logger

producer_Script_logs_path=os.path.join(common_PATH, "Road_Producer.log")
logger = setup_logger("Road_Data_ETL", "producer_script", "kafka", producer_Script_logs_path)

admin_client=KafkaAdminClient(
            bootstrap_servers=['kafka:9092'],
            client_id="kafka_topic_manager"
        )

def producer(**kwargs):
    logger.info("Producer funtion called")
    conf = kwargs.get("dag_run").conf if "dag_run" in kwargs else {}

    lat = conf.get("latitude", 28.60507059568563)
    lng = conf.get("longitude", 77.44698311030206)
    logger.info(f"Coordinates in Producer passed: lat- {lat}, lng- {lng}")

    try:
        producer = KafkaProducer(
            bootstrap_servers='kafka:9092',
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        logger.info("Producer passed")


    except Exception as e:
        print(f"Error occurred:{e}")
        logger.error("Error occured : {e}")
        exit()
    road_list = []
    nearby_roads = get_nearby_roads_with_coordinates(lat, lng)
    print(len(nearby_roads))
   
    logger.info(len(nearby_roads))
    if nearby_roads:
        # Print results
        for road_name, coords in nearby_roads.items():
            # logging.info(f"Road_name: {road_name}, Start_coords : {coords['start']} , End_coords : {coords['end']}")
            road_list.append({
                "name": road_name,
                "start_lat": coords['start'][0],
                "start_lon": coords['start'][1],
                "end_lat": coords['end'][0],
                "end_lon": coords['end'][1],
            })
        timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        message = json.dumps(road_list).encode('utf-8')
        logger.info(message)

        try:
                f = producer.send('road-topic',value=road_list)
                # f=producer.send('chat-messages', key=user,value={'user': user, 'message': message,'timestamp':timestamp})
                f.get(timeout=10)
                logger.info("Message sent")
                time.sleep(3)

        except Exception as e:
                logger.fatal(f"failed to send message {e}")

        producer.close()


if __name__ == "__main__":
    try: 
        create_kafka_topic(admin_client,"road-topic",2,1)
        logger.info(f"topic road-topic created successfully")

    except Exception as e:
        logger.fatal(f"failed to create topic road-topic: {e}")

    producer()
