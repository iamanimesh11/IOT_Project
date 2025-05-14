# 🚦 Real-Time  ETL of Road Traffic & Weather Monitoring.

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
- [Screenshots](#screenshots)
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
| **Storage**    | PostgreSQL             | <img src="https://www.logo.wine/a/logo/PostgreSQL/PostgreSQL-Logo.wine.svg" alt="PostgreSQL" width="120"/> |
| **Logging**    | Grafana Loki           | <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/a/a1/Grafana_logo.svg/2005px-Grafana_logo.svg.png" alt="Grafana Loki" width="100"/> |
| **UI framework**    | Streamlit           | <img src="https://streamlit.io/images/brand/streamlit-logo-primary-colormark-darktext.png" alt="Streamlit" width="180"/> |
| **Containerization**  | Docker, Docker Compose | <img src="https://cdn4.iconfinder.com/data/icons/logos-and-brands/512/97_Docker_logo_logos-1024.png" alt="Docker" width="100"/>|
| **API & Credentials**   | Firebase               | <img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTxQktpK3Jy3GkxXutGPzl8R3OBCNMxfFWP5A&s" alt="Firebase" width="130"/>|
| **Alerts and other**   | Discord               | <img src="https://pngimg.com/uploads/discord/discord_PNG3.png" alt="Discord" width="110"/>|
| **Language**   | Python                 | <img src="https://s3.dualstack.us-east-2.amazonaws.com/pythondotorg-assets/media/community/logos/python-logo-only.png" alt="Python" width="70"/>|

---

# Architecture

![Workflow](asset/workflow.gif)


# 🚀 Getting Started

## ⚠️ IMPORTANT

<p align="left">
  <img src="https://img.freepik.com/free-vector/www-concept-illustration_114360-2143.jpg?t=st=1744565213~exp=1744568813~hmac=cc0420ee0ca016a8962950768146a9a73c652ef7e93dfd0f6be86f2c3eca7cb6&w=826" alt="API Status" width="200"/>
</p>

> Before cloning and running this project, **please ensure that the API is up and running.**

🔗 **[Visit Project App](https://realtimeetlroadtrafficweather.vercel.app/#)**  
Make sure the API is **not down** before proceeding.

💡 Once the API is confirmed to be **live and functional**, you can go ahead and clone the repo, and run the project locally. 
Just follow the steps below 👇


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
git clone https://github.com/animesh11singh/project_real_time_trafic_monitoring.git
cd project_real_time_trafic_monitoring
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


## 📊 Logging & Monitoring


This project implements a **centralized logging and monitoring system** using **Grafana Loki**, ensuring transparency, debuggability, and maintainability across all services.

### Key Highlights

- **Structured Logging**  
  All Python scripts across Kafka producers/consumers, Airflow DAGs, and data pipelines generate structured logs with timestamp, service name, event type, and status.

- **Centralized Collection with Grafana Loki**  
  Logs from all services are collected and pushed to Loki using `Promtail`. These logs are accessible in real-time via **Grafana dashboards**.

- **Dockerized Monitoring Stack**  
  - `Grafana` for visualization  
  - `Loki` for log storage  
  - `Promtail` for log shipping  
  These services are configured in `docker-compose.yml` with persistent volume storage.

- **Real-Time Debugging**  
  Logs include all critical operations such as:
  - API calls (Overpass, TomTom, WeatherAPI)  
  - Kafka message flow  
  - Database operations (insert/update/failure)  
  - Retry attempts and error messages  

- **Failover & Local Storage**  
  In case of Grafana/Loki downtime, logs are safely written to local files and retried later to avoid data loss.

- **Security & Hygiene**  
  - API keys and sensitive values are **excluded from log outputs**  
  - Logs are rotated and archived periodically (based on configuration)

### Accessing Logs

1. Navigate to [http://localhost:3000](http://localhost:3000)
3. Use log query labels like `{job="airflow"}` or `{job="kafka-producer"}` to filter logs
4. Dashboard panels show service-wise activity, recent errors, and API request status

📷 **Please find sample images of dashboards and logs below**



> ✅ This setup ensures end-to-end visibility into your ETL pipeline operations.

## 🗃️ Data Stored

| Table Name       | Description                      |
|------------------|----------------------------------|
| roads_traffic     | Road metadata from Overpass API |
| traffic_flow_data | Real-time traffic speed data    |
| weather_conditions| Weather data per coordinate     |

---


## 📊 Future Scope

- **Advanced Analytics & ML Integration:**  
  Implement predictive models for traffic congestion, accident risk zones, or weather-based route recommendations.

- **Real-Time Alert System:**  
  Notify users of traffic anomalies or severe weather via email, SMS, or push notifications.

- **Interactive Dashboard:**  
  Integrate tools like Streamlit or Dash for live data visualization and insights.

- **Scalability Enhancements:**  
  Deploy to cloud platforms (AWS, GCP, or Azure) using Kubernetes and CI/CD pipelines for production readiness.

- **API Gateway & Access Layer:**  
  Build secure REST APIs for external systems to query real-time traffic insights.

- **Data Lake Integration:**  
  Archive historical traffic and weather data to a data lake for long-term analysis and trend forecasting.
---

Remarks :
As we know in Data Engineering project,its impossible to bear cost of production and only way is to do everything locally for showcasing a project.


## 👤 Author

- **[Animesh Singh]**
- 💼 Aspiring Data Engineer | Big Data |Python | Postgresql/Databases| Kafka | Airflow | Docker 
```

----------------------------------------------------------------------------
