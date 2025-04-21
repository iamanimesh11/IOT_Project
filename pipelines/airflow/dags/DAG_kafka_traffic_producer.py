import sys
import os
import logging

AIRFLOW_HOME = os.getenv("AIRFLOW_HOME", "/opt/airflow")

if AIRFLOW_HOME != "/opt/airflow":
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    AIRFLOW_HOME = BASE_DIR
    logging.info("below base_Dir")
    logging.info(BASE_DIR)


SCRIPTS_PATH = os.path.join(AIRFLOW_HOME, "common")
sys.path.append(SCRIPTS_PATH)
SCRIPTS_PATH = os.path.join(AIRFLOW_HOME, "scripts")
sys.path.append(SCRIPTS_PATH)
SCRIPTS_PATH = os.path.join(AIRFLOW_HOME, "kafka_files")
sys.path.append(SCRIPTS_PATH)

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
from kafka.admin import KafkaAdminClient,NewTopic
from traffic_producer import traffic_producer
from utils.Database_connection_Utils import connect_Database
from utils.db_utils import get_road_id
from modify_Topics import create_kafka_topic
from logging_and_monitoring.centralized_logging import setup_logger

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2024, 3, 15),
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
}

admin_client=KafkaAdminClient(
            bootstrap_servers=['kafka:9092'],
            client_id="kafka_topic_manager"
        )

with DAG(
        dag_id="kafka_traffic_producer_DAG",
        default_args=default_args,
        description="DAG to run kafka traffic producer script",
        tags=["kafka", "producer", "traffic"],
        #schedule_interval='*/5 * * * *',  # Every 5 minutes
        schedule_interval='*/1 * * * *', 
        catchup=False,  # Prevents backfilling past runs
) as dag:
 
    create_topic_task  = PythonOperator(
        task_id="create_traffic_topic",
        python_callable=create_kafka_topic,
        op_args=[admin_client,"traffic_topic",2,1],  

    )

    send_road_task = PythonOperator(
        task_id="send_road_data",
        python_callable= traffic_producer,
    )

    create_topic_task >> send_road_task
