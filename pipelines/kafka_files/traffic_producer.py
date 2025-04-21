import time
import os
import sys
import logging
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
    
    
SCRIPTS_PATH = os.path.join(AIRFLOW_HOME, "scripts")
sys.path.append(SCRIPTS_PATH)
common_PATH = os.path.join(AIRFLOW_HOME, "common") 
sys.path.append(common_PATH)
common_PATH = os.path.join(AIRFLOW_HOME, "common","logging_and_monitoring","logs") 
sys.path.append(common_PATH)

from utils.Database_connection_Utils import connect_Database
from utils.db_utils import get_road_id
from modify_Topics import create_kafka_topic
from logging_and_monitoring.centralized_logging import setup_logger



producer_Script_logs_path=os.path.join(common_PATH, "Traffic_Producer.log")
logger = setup_logger("Traffic_Data_ETL", "producer_script", "kafka", producer_Script_logs_path)


admin_client=KafkaAdminClient(
            bootstrap_servers=['kafka:9092'],
            client_id="kafka_topic_manager"
        )

def traffic_producer():
    logger.info("Producer function called")
    try:
        producer = KafkaProducer(
            bootstrap_servers='kafka:9092',
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        logger.info("traffic Producer passed")

    except Exception as e:
        print(f"Error occurred:{e}")
        logger.error("Error occured : {e}")
        exit()

    
    logger.info("Connected too Kafka. Listening for messages...")
    conn= connect_Database()
    logger.info(f"conn: {conn}")
    
    if conn is None:
         logger.critical("Failed to establish database connection.", extra={"stage": "start"})
         exit()
   
    road_Data = get_road_id(conn)
    if not road_Data:
        logger.warning("No roads found in get_road_id(), exiting main()", extra={"stage": "start"})
        return
        
        
    for road  in road_Data:
        timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        #message = json.dumps(road[0]).encode('utf-8')
        message= {"road_id":road[0]}
        logger.info(f"message: {message}")

        try:
                f = producer.send('traffic-topic',value=message)
                # f=producer.send('chat-messages', key=user,value={'user': user, 'message': message,'timestamp':timestamp})
                f.get(timeout=10)
                logger.info("Message sent")
                time.sleep(3)

        except Exception as e:
                logger.fatal(f"failed to send message {e}")
        break
                    
     
    producer.close()


if __name__ == "__main__":
        status=create_kafka_topic(admin_client,"traffic-topic",2,1)
        logger.info(status)
        traffic_producer()
