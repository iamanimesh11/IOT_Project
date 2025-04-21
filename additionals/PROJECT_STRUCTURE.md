.
├── .dockerignore
├── .env
├── .gitattributes
├── .gitignore
├── docker-compose.yml
├── Dockerfile
└── README.md
├── additionals
│   ├── backup.sqlc
│   ├── project_structure.json
│   ├── PROJECT_STRUCTURE.md
│   ├── project_structure_json_creator.py
│   └── text_Search.py
├── common
│   └── __init__.py
│   ├── common
│   │   ├── logging_and_monitoring
│   │   │   ├── logs
│   │   │   │   └── loki_errors.text
│   ├── credentials
│   │   ├── config.ini
│   │   ├── firebase_cred.json
│   │   └── red-button-442617-a9-89794f0a5b90.json
│   ├── logging_and_monitoring
│   │   ├── centralized_logging.py
│   │   └── firebase_db_api_utils.log
│   │   ├── logs
│   │   │   ├── api_utils.log
│   │   │   ├── database_connection.log
│   │   │   ├── db_utils.log
│   │   │   ├── firebase_db_api_utils.log
│   │   │   ├── kafka_consumer.log
│   │   │   ├── loki_errors.text
│   │   │   ├── road_data_main.log
│   │   │   ├── Road_Producer.log
│   │   │   ├── Traffic_consumer.log
│   │   │   └── Traffic_Producer.log
│   ├── streamlit
│   │   ├── database_logger dashboard-7-4.json
│   │   ├── Dockerfile
│   │   ├── Docker_container_Status.py
│   │   ├── Docker_running_containers_HTTP_Streamlit.py
│   │   ├── ETL_walkthrough_Streamlit.py
│   │   ├── kafka_manager_Streamlit.py
│   │   ├── lokii_streamlit.py
│   │   ├── main_Streamlit.py
│   │   ├── network_utils.py
│   │   ├── PostgreSQL_streamlit_app.py
│   │   ├── project_flow.py
│   │   └── requirements.txt
│   │   ├── images
│   │   │   ├── Daasboard_1.png
│   │   │   ├── Grafana_guide_1.png
│   │   │   ├── Grafana_guide_2.png
│   │   │   └── Grafana_guide_3.png
│   │   ├── loki_files
│   │   │   ├── log_sent _to_loki.py
│   │   │   └── loki_request_python.py
│   ├── utils
│   │   ├── api_utils.py
│   │   ├── config_loader.py.py
│   │   ├── Database_connection_Utils.py
│   │   ├── db_utils.py
│   │   ├── extract_Data_from_link_using_DIFFBOT.py
│   │   ├── firebase_db_api_track_util.py
│   │   ├── genai_text_Extracter.py
│   │   ├── kafka_modify_Topics_utils.py
│   │   └── trafficHelper_utils.py
├── config
│   ├── init-db.sql
│   ├── loki-config.yml
│   ├── loki.json
│   ├── promtail-config.yml
│   └── wait-for-flag.sh
├── grafana
│   ├── provisioning
│   │   ├── dashboards
│   │   │   ├── Airflow Log Analytics.json
│   │   │   ├── dashboard.yml
│   │   │   └── ETL dashboard.json
├── pipelines
│   ├── airflow
│   │   ├── airflow.cfg
│   │   ├── airflow.db
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── webserver_config.py
│   │   ├── dags
│   │   │   ├── DAG_kafka_road_producer.py
│   │   │   ├── DAG_kafka_traffic_producer.py
│   │   │   └── DAG_Monitor_ETL_health.py
│   │   ├── plugins
│   ├── kafka_files
│   │   ├── Dockerfile
│   │   ├── Dockerfile_consumer_traffic
│   │   ├── modify_Topics.py
│   │   ├── requirements_traffic.txt
│   │   ├── road_consumer.py
│   │   ├── road_producer.py
│   │   ├── traffic_consumer.py
│   │   ├── traffic_producer.py
│   │   └── __init__.py
│   ├── scripts
├── shared
│   └── wait-for-flag.sh