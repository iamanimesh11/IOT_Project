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

from utils.kafka_modify_Topics_utils import create_kafka_topic
from road_producer import producer
from utils.Database_connection_Utils import connect_Database
from logging_and_monitoring.centralized_logging import setup_logger

# DAG default arguments
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2024, 4, 12),
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
}

admin_client=KafkaAdminClient(
            bootstrap_servers=['kafka:9092'],
            client_id="kafka_topic_manager"
        )

with DAG(
        dag_id="kafka_road_producer_DAG",
        default_args=default_args,
        description="DAG to run kafka road producer script",
        tags=["kafka", "producer", "roads"],
        schedule_interval='*/5 * * * *',  # Every 5 minutes
        catchup=False,  # Prevents backfilling past runs
) as dag:
 
    create_topic_task  = PythonOperator(
        task_id="create_road_topic",
        python_callable=create_kafka_topic,
        op_args=[admin_client,"roads_topic",2,1],  # List of positional args
        provide_context=True  # This is needed to access kwargs


    )

    fetch_road_task = PythonOperator(
        task_id="fetch_road_data",
        python_callable= producer,
        provide_context=True 

    )

    create_topic_task >> fetch_road_task
