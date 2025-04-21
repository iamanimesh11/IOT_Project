import sys
import os
import logging
import psycopg2

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
        
def check_etl_health():
    logging.info("Starting ETL health check...")
    
    conn = psycopg2.connect(
        host="postgres",
        port="5432",
        database="de_personal",
        user="postgres",
        password="animesh11"
    )
    cur = conn.cursor()

    tables = {
        'roads': 'created_at',
        'traffic_data': 'recorded_at'
    }

    for table, time_col in tables.items():
        cur.execute(f"SELECT MAX({time_col}) FROM roads_traffic.{table};")
        latest_time = cur.fetchone()[0]

        cur.execute(f"SELECT COUNT(*) FROM roads_traffic.{table};")
        row_count = cur.fetchone()[0]

        logging.info(f"{table} | Latest: {latest_time} | Rows: {row_count}")

        if latest_time is None or (datetime.now() - latest_time) > timedelta(minutes=20):
            logging.warning(f"{table} data might be stale!")

    cur.close()
    conn.close()
# Define DAG
with DAG(
        dag_id="monitor_etl_health_dag",
        default_args=default_args,
        description="DAG to monitor ETL health ",
        tags=["kafka", "producer", "Health"],
        schedule_interval='*/5 * * * *',  # Every 5 minutes
        catchup=False,  
) as dag:
 
    monitor_task = PythonOperator(
        task_id='check_etl_status',
        python_callable=check_etl_health
    )


    monitor_task