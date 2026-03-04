![Status](https://img.shields.io/badge/Status-🚧_Updating_Regularly-yellow?style=for-the-badge)

# ⚡EventPulse :  A Scalable Real-Time IoT Streaming & Monitoring System

> 🛰️ An end-to-end real-time data engineering pipeline to simulate real-world IoT device events with scalable backend processing simulation, service subscriptions, and real-time event delivery to CRM  using modern data engineering tools.



---
**Remarks**:  
In real-world Data Engineering projects, deploying a full-scale production setup can be costly. Therefore, for the purpose of showcasing, the entire infrastructure in this project is built and demonstrated locally using Docker — ensuring it's fully reproducible without incurring any extra cost.

---



## 📚 Table of Contents

- [Key Features](#-key-features)
- [Tech Stack](#%EF%B8%8Ftech-stack)
- [Getting Started](#-getting-started)
- [Prerequisites](#-prerequisites)
- [Architecture](#architecture)
- [Setup Instructions](#setup-instructions)
- [Directory Structure](#directory-structure)
- [Configurations](#configurations)
- [Logging & Monitoring](#-logging--monitoring)
- [Future Scope](#-future-scope)
- [Author](#-author)


## 🔑 Key Features

- **🐳 Fully Dockerized Architecture**  
  Deploy the entire stack with a single `docker-compose up --build` — no manual setup.

- **⚙️ Real-Time IoT Event Simulation**  
  Continuously generates mock telemetry data from simulated IoT devices like Refrigerators, TVs, and Washing Machines..

- **⏰ Airflow-Based Workflow Orchestration**  
Airflow is integrated to schedule background tasks such as data validation, expired subscription cleanup, and periodic telemetry batch processing.
  
- **📡 Apache Kafka for High-Throughput Streaming**  
  Events are routed through Kafka, with device-type-specific consumer containers for modular and scalable processing.

- **🛠️ FastAPI Backend for Service Registration , Subscriptiong,webhook**  
    Enables external services to register and subscribe to specific device IDs for real-time event delivery.

- **📁 JSON, PostgreSQL, and Redis Integration**
   Combines persistent storage (PostgreSQL), structured configurations (JSON), and in-memory speed (Redis).

- **📝 Centralized Logging with Loki**  
  All logs from Python apps and services tasks are sent to Grafana Loki for monitoring and troubleshooting.

- **📊 Visual Monitoring with Grafana**  
Real-time visualization of system metrics, device errors, and subscription statuses using Grafana dashboards.

- **🔔 Notification System (Optional)**  
  Sends ETL job alerts (success/failure) via Discord webhooks.

- **🔐 Secure Credential & API Key Management**  
  Firebase securely stores API keys, secrets, and credentials — no hardcoding.

- **💾 Persistent PostgreSQL Storage**  
  Maintains structured data and ensures durability across restarts.

- **🧪 Mock CRM Integration**  
    Simulates CRM system behavior by receiving device alerts and acting on customer-device mappings.
  
- **👨‍💻 Plug-and-Play for Recruiters**  
  Instantly clonable and runnable — ideal for technical demos or code evaluations.

---
# 🛠️Tech Stack

| Component      | Tool / Service        | Logo                              |
|----------------|-----------------------|-----------------------------------|
| **Data Source** | Mock data generated via python | <img src="https://s3.dualstack.us-east-2.amazonaws.com/pythondotorg-assets/media/community/logos/python-logo-only.png" alt="Python" width="70"/>|
| **Scheduler**  | Apache Airflow         | <img src="https://icon.icepanel.io/Technology/svg/Apache-Airflow.svg" alt="Airflow" width="70"/> |
| **Streaming**  | Apache Kafka           | <img src="https://irisidea.com/wp-content/uploads/2024/04/kafka-implementation-experience--450x231.png" alt="Kafka" width="120"/> |
| **Messaging Protocol** | MQTT (Eclipse Mosquitto) | <img src="https://www.donskytech.com/wp-content/uploads/2023/02/Mqtt-hor.svg_.png" alt="MQTT" width="100"/> |
| **API Frameworks**     | FastAPI, Flask         | <img src="https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png" alt="FastAPI" width="90"/> <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/3/3c/Flask_logo.svg/768px-Flask_logo.svg.png" alt="Flask" width="50"/> |
| **Storage**    | PostgreSQL             | <img src="https://www.logo.wine/a/logo/PostgreSQL/PostgreSQL-Logo.wine.svg" alt="PostgreSQL" width="120"/> |
| **Logging**    | Grafana Loki           | <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/a/a1/Grafana_logo.svg/2005px-Grafana_logo.svg.png" alt="Grafana Loki" width="100"/> |
| **Memory Based Storage**    | Redis  | <img src="https://geelongwebdesign.com.au/wp-content/uploads/2025/04/redis-web-hosting-service-01.png" alt="Redis" width="100"/>|
| **UI framework**    | Streamlit           | <img src="https://streamlit.io/images/brand/streamlit-logo-primary-colormark-darktext.png" alt="Streamlit" width="180"/> |
| **Containerization**  | Docker, Docker Compose | <img src="https://cdn4.iconfinder.com/data/icons/logos-and-brands/512/97_Docker_logo_logos-1024.png" alt="Docker" width="100"/>|
| **Alerts and other**   | Discord               | <img src="https://pngimg.com/uploads/discord/discord_PNG3.png" alt="Discord" width="110"/>|
| **Language**   | Python                 | <img src="https://s3.dualstack.us-east-2.amazonaws.com/pythondotorg-assets/media/community/logos/python-logo-only.png" alt="Python" width="70"/>|

---

# Architecture

![Workflow](asset/workflow.gif)


# 🚀 Getting Started


## ✅ Prerequisites

Before running this project locally, make sure you have the following installed on your system:

- [Docker](https://www.docker.com/products/docker-desktop) & [Docker Compose](https://docs.docker.com/compose/)
- [Git](https://git-scm.com/downloads)
- A code editor like [VS Code](https://code.visualstudio.com/)
- Internet connection to access external APIs (TomTom, WeatherAPI, etc.)

💡 **Note:**  
Ensure that your system’s firewall or antivirus isn’t blocking Docker containers from making network requests.


# Setup Instructions


###  Clone the Repository

First, clone the repository to your local machine:

```bash
git clone https://github.com/iamanimesh11/IOT_Project.git

```
### Run in terminal

```bash
docker-compose up -d --build
```
## 📂Directory Structure

```bash
.
├── .dockerignore
├── .env
├── .gitattributes
├── .gitignore
├── device_models.json
├── docker-compose.yml
├── Dockerfile
├── project summary.txt
├── README.md
└── temp.py
├── idea
│   ├── .gitignore
│   ├── material_theme_project_new.xml
│   ├── misc.xml
│   ├── modules.xml
│   ├── project_IOT_LG.iml
│   └── vcs.xml
│   ├── inspectionProfiles
│   │   ├── profiles_settings.xml
│   │   └── Project_Default.xml
├── additionals
│   ├── backup.sqlc
│   ├── project_structure.json
│   ├── PROJECT_STRUCTURE.md
│   ├── project_structure_json_creator.py
│   └── text_Search.py
├── asset
│   └── workflow.gif
├── common
│   ├── __init__ copy.py
│   └── __init__.py
│   ├── credentials
│   │   ├── config.ini
│   │   └── red-button-442617-a9-89794f0a5b90.json
│   ├── logging_and_monitoring
│   │   ├── centralized_logging.py
│   │   └── firebase_db_api_utils.log
│   ├── logs
│   │   └── loki_errors.text
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
│   ├── test
│   │   ├── device_models.json
│   │   ├── readjson.py
│   │   ├── t.html
│   │   ├── temp.html
│   │   └── tojson.py
│   ├── utils
│   │   ├── config.ini
│   │   ├── Database_connection_Utils.py
│   │   ├── service_registration.py
│   │   └── __init__.py
│   │   ├── Subscription
│   │   │   ├── backend_subscription_consumer.py
│   │   │   ├── bulk_subscribe.py
│   │   │   ├── Database_connection_Utils.py
│   │   │   └── POST subscribe Event.py
│   │   ├── customer -database
│   │   │   ├── create_kafka_topics.py
│   │   │   ├── Customers_Tables_Creator.py
│   │   │   └── generate_customer_data.py
│   │   ├── get-devices
│   │   │   ├── dynamic_Devices_Tables_creator.py
│   │   │   ├── fastapi generates device data.py
│   │   │   ├── get-devices from fastapi.py
│   │   │   ├── staging_table_creation.py
│   │   │   └── __init__.py
│   │   ├── json_files
│   │   │   ├── device_models.json
│   │   │   └── device_profiles.json
│   │   ├── kafka_handler
│   │   │   ├── Dockerfile.kafka_controller
│   │   │   ├── kafka_consumer.py
│   │   │   ├── kafka_controller.py
│   │   │   ├── mock_crm.py
│   │   │   ├── requirements.txt
│   │   │   └── webhook_receiver.py
│   │   │   ├── Devices_processing_logic
│   │   │   │   └── refrigerator_processing_logic.py
│   │   │   ├── templates
│   │   │   │   └── crm_dashboard.html
│   │   ├── test-mqtt
│   │   │   ├── controller.py
│   │   │   ├── dockerfile
│   │   │   ├── dockerfile_consumer_and_controller
│   │   │   ├── generator.py
│   │   │   ├── mqtt_consumer.py
│   │   │   ├── requirements.txt
│   │   │   └── __init__.py
├── config
│   ├── db_initialize.sh
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
├── help notes
│   ├── airflow_usage
│   └── why mqtt and kafka both
├── json_files
│   └── device_models.json
├── mosquitto
│   ├── config
│   │   └── mosquitto.conf
│   ├── data
│   ├── log
├── pipelines
│   ├── airflow
│   │   ├── airflow.cfg
│   │   ├── airflow.db
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── webserver_config.py
│   │   ├── dags
│   │   │   └── DAG_Monitor_ETL_health.py
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
├── shared
│   ├── info_collected.flag
│   ├── start_logged.txt
│   ├── user_info.json
│   └── wait-for-flag.sh
```


### ▶️ Next Steps

Once the project is up and running, follow these steps:

1. 🌐 Open your browser and visit:  
   **[http://localhost:8501/](http://localhost:8501/)**  
   This will open the ETL helper streamlit app .

2. 📋 **Follow the ETL instructions** provided on the strreamlit app to Simulate ETL step by step.

3. 🐳 **Keep an eye on your containers:**  
   Use `docker ps` or Docker Desktop to monitor the status of all services.

---

✅ Everything running smoothly? You're all set to explore the project!







## Configurations 

### Access the Services
Once the containers are up and running, you can access the following services :

| Service           | URL                           | Username | Password |
|-------------------|-------------------------------|----------|----------|
| Streamlit App     | [http://localhost:8501](http://localhost:8501) | _N/A_     | _N/A_     |
| Airflow UI        | [http://localhost:8080](http://localhost:8080) | `animesh` | `animesh16` |
| Grafana Dashboard for logs | [http://localhost:3000](http://localhost:3000) | `admin`   | `animesh16` or `admin`   |

Postgrsql Database initialized at startup of Postgresql container with default configurations.

---


## 📊 Logging and Monitoring

To ensure visibility into the system's operations and health, this project integrates robust **logging** and **monitoring** mechanisms:

### 🔍 Logging with Grafana Loki

- All system logs, including data pipeline activities and API interactions, are streamed to **Grafana Loki**.
- Logs are labeled by component (e.g., `airflow`, `fastapi`, `kafka`, `mqtt`) for easy filtering.
- Structured logging (JSON format) is used where applicable to allow advanced querying in Grafana.

### 📈 Visualization with Grafana

- **Grafana** dashboards provide real-time visual insights into:
  - Task executions (success/failure counts)
  - Kafka message flow and throughput
  - API request/response times
  - Redis cache hit/miss ratio
  - MQTT connection status and message counts
- Dashboards are customizable to add alerts, thresholds, and trend analysis.

### 🚨 Alerting

- Alerts are configured in Grafana to notify via **Discord** for:
  - Task failures in Airflow
  - Abnormal data trends or system errors
  - Service downtime (e.g., Kafka broker or API unresponsive)

### 📝 Application Logs

- Python-based services (e.g., FastAPI, Flask) utilize the built-in `logging` module.
- Logs are forwarded to Loki using **Promtail**.
- Each log includes timestamps, severity level (INFO, WARNING, ERROR), and relevant context for debugging.

### 🔧 Tools Used

| Tool            | Purpose                   |
|-----------------|---------------------------|
| Grafana         | Dashboard and alerting    |
| Loki            | Centralized log storage   |
| Promtail        | Log shipping to Loki      |
| Discord Webhook | Real-time notifications   |

---


### Accessing Logs

1. Navigate to [http://localhost:3000](http://localhost:3000)
3. Use log query labels like `{job="airflow"}` or `{job="kafka-producer"}` to filter logs
4. Dashboard panels show service-wise activity, recent errors, and API request status

📷 **Please find sample images of dashboards and logs below**



> ✅ This setup ensures end-to-end visibility into your ETL pipeline operations.

## 🗃️ Data Stored

The following tables are created and managed by the system:

| Table Name                        | Purpose                                                                                                |
|-----------------------------------|--------------------------------------------------------------------------------------------------------|
| `registered_devices.device_staging` | Stores initial registration information for IoT devices before full provisioning or for staging data.  |
| `customers.customer_staging`        | Holds staging information for customers, linking them to their registered devices.                     |
| `registered_devices.auth_tokens`    | Manages authentication tokens issued to devices for secure communication.                              |
| `subscriptions.services`            | Defines the available services that devices can subscribe to, including their API keys and callbacks.  |
| `subscriptions.subscribed_devices`  | Tracks active subscriptions, linking devices to the services they are currently using.                 |
| `customers.error_events`            | Logs error events reported by devices,  used for CRM, support, and troubleshooting purposes.      |

---

## 🚀 Future Scope

This project serves as a strong foundation for simulating real-time IoT event-based ETL systems. Below are some future enhancements that can further elevate its capabilities:

### 🔁 1. **Real-Time Stream Processing**

* Integrate **Apache Flink** or **Spark Structured Streaming** to perform low-latency processing on telemetry data.
* Enable complex event detection like anomaly spotting, pattern recognition, or sliding-window aggregations.

### 🤖 2. **Predictive Maintenance with Machine Learning**

* Train and deploy ML models to **predict equipment failures** using historical telemetry.
* Schedule model training and inference using Airflow DAGs.
* Send early warnings to subscribed services or CRM systems.

### ☁️ 3. **Cloud Integration & Data Lake**

* Push data to cloud platforms like **AWS S3**, **Google Cloud Storage**, or **Azure Blob** for long-term storage.
* Store telemetry in **Parquet** format with partitioning for better query performance and future analytics.

### 📊 4. **Advanced Monitoring & Alerting**

* Extend Grafana dashboards to include:

  * Service health
  * Kafka consumer lag
  * Device-specific error trends
* Integrate **Prometheus alerts** to notify on failures, lags, or inactive devices.

### 📦 5. **CI/CD and DevOps**

* Automate Docker builds and deployments using **GitHub Actions** or **GitLab CI**.
* Ensure production-grade system reliability and faster iterations.

### 🧑‍💻 6. **Admin & CRM Dashboard**

* Build a **React/Next.js** based web interface to:

  * Visualize live device errors
  * Manage service subscriptions
  * View device-to-customer mappings

### 🔄 7. **Event Replay and Reprocessing**

* Build a Kafka replay module for testing and backfilling ML or ETL jobs.
* Useful for simulating new use cases on existing historical telemetry.

### 🔐 8. **Enhanced Security**

* Add authentication and authorization for:

  * Device data ingestion
  * Service registration and callbacks
* Use JWT tokens or OAuth2 for secure communications.

---

Remarks :
As we know in Data Engineering project,its impossible to bear cost of production and only way is to do everything locally for showcasing a project.


## 👤 Author

- **[Animesh Singh]**
- 💼 Aspiring Data Engineer | Big Data |Python | Postgresql/Databases| Kafka | Airflow | Docker 
```

----------------------------------------------------------------------------
