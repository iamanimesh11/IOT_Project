import streamlit as st
import pandas as pd
import time
# --- Data Flow Page ---
import requests
import json
from datetime import datetime
from requests.auth import HTTPBasicAuth
from PostgreSQL_streamlit_app import check_postgres_connection,load_data

def trigger_airflow_dag(lat, lng,run_id):
    url = "http://airflow-webserver:8080/api/v1/dags/kafka_road_producer_DAG/dagRuns"

    payload = {
        "conf": {
            "latitude": lat,
            "longitude": lng
        },
        "dag_run_id": run_id
    }

    response = requests.post(url, json=payload, auth=('animesh', 'animesh16'))  # if basic auth is enabled

    if response.status_code in [200, 201]:
        st.success("🚀 DAG triggered successfully with coordinates!")
    else:
        st.error(f"Failed to trigger DAG: {response.status_code}\n{response.text}")


def unpaused_dag_traffic():
    AIRFLOW_API = "http://airflow-webserver:8080/api/v1/dags/kafka_traffic_producer_DAG"
    USERNAME = "animesh"
    PASSWORD = "animesh16"  # use actual credentials

    # Set is_paused to False
    response = requests.patch(
        AIRFLOW_API,
        json={"is_paused": False},
        auth=HTTPBasicAuth(USERNAME, PASSWORD)
    )

    if response.status_code == 200:
         st.success("✅Traffic DAG unpaused successfully.")
    else:
         st.error("❌ Failed to unpause DAG:", response.text)


def schedule_traffic_Dag():
    url = "http://airflow-webserver:8080/api/v1/dags/kafka_traffic_producer_DAG/dagRuns"
    readable_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    run_id = f"Streamlit_trigger__{readable_time.replace(' ', '_').replace(':', '-')}"
    dag_id="kafka_traffic_producer_DAG"
    airflow_url="http://localhost:8080/"
    grafana_url = "http://localhost:3000"


    payload = {
        "dag_run_id": run_id
    }

    response = requests.post(url, json=payload, auth=('animesh', 'animesh16'))

    if response.status_code in [200, 201]:
        st.success(f"🚀 Traffic DAG scheduled successfully!")
        unpaused_dag_traffic()
        st.markdown("### DAG Trigger Info")
        st.info(f"Triggered DAG: `{dag_id}`")
        st.code(f"Run ID: {run_id}")
        st.markdown(
                    f"🔗 For DAG info, visit [Airflow UI]({airflow_url}) & for  real-time logs, check [Grafana Dashboard]({grafana_url})"
                )
    else:
        st.error(f"❌ Failed to trigger DAG: {response.status_code}\n{response.text}")

def unpaused_dag():
    AIRFLOW_API = "http://airflow-webserver:8080/api/v1/dags/kafka_road_producer_DAG"
    USERNAME = "animesh"
    PASSWORD = "animesh16"  # use actual credentials

    # Set is_paused to False
    response = requests.patch(
        AIRFLOW_API,
        json={"is_paused": False},
        auth=HTTPBasicAuth(USERNAME, PASSWORD)
    )

    if response.status_code == 200:
         st.success("✅ DAG unpaused successfully.")
    else:
         st.error("❌ Failed to unpause DAG:", response.text)



bool,engine=check_postgres_connection()
       
def is_valid_coordinate(coord_str, min_val, max_val):
    try:
        val = float(coord_str)
        return min_val <= val <= max_val
    except ValueError:
        return False

def input_coord():
    with st.form("coordinate_input_form"):
        col1, col2 = st.columns(2)
        with col1:
            lat = st.text_input("Enter Latitude", placeholder="e.g. 28.6139")
        with col2:
            lon = st.text_input("Enter Longitude", placeholder="e.g. 77.2090")

        submitted = st.form_submit_button("Start Road data DAG with Inputs")

    if submitted:
        if lat.strip() and lon.strip():
            if is_valid_coordinate(lat, -90, 90) and is_valid_coordinate(lon, -180, 180):
                st.success(f"✅ Coordinates received: ({lat}, {lon})")
                st.session_state.coordinates = (lat, lon)
                st.session_state.data_flow_step = 2
            else:
                st.error("⚠️ Invalid coordinate values. Latitude must be between -90 and 90, and longitude between -180 and 180.")
        else:
            st.error("❌ Please enter both latitude and longitude.")

    if "coordinates" in st.session_state:
        lat, lon = st.session_state.coordinates
        if st.button("▶️ Start Road Data DAG"):
            readable_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            run_id = f"Streamlit_trigger__{readable_time.replace(' ', '_').replace(':', '-')}"
            trigger_airflow_dag(lat, lon, run_id)
            unpaused_dag()
            st.session_state.dag_run_id = run_id
            
            
def reset_steps():
    for i in range(1, 7):
        st.session_state[f"step_{i}_done"] = False
        
def main():
        if not all(st.session_state.confirmed_steps):
            st.warning("🔒 Complete the system setup first to view the Data Flow.")
            st.stop()
        st.info(
            "Note: This step-by-step process is purely for user simulation. "
            "The ETL pipeline starts automatically once all Docker containers are running. "
            "So you can skip the simulation and jump straight into Airflow or Grafana to monitor logs, "
            "or query the database directly — either from this app or via the command line."
        )

        airflow_url="http://localhost:8080/"
        grafana_url = "http://localhost:3000"
        
        for i in range(1,8):
            st.session_state.setdefault(f"step_{i}_done", False)

        with st.expander("1️⃣ User Input - Coordinates", expanded=True):
            input_coord()
            if "dag_run_id" in st.session_state:
                dag_id = "kafka_road_producer_DAG"
                st.markdown("### DAG Trigger Info")
                st.info(f"Triggered DAG: `{dag_id}`")
                st.code(f"Run ID: {st.session_state.dag_run_id}")
                st.markdown(
                    f"🔗 For DAG info, visit [Airflow UI]({airflow_url}) & for  real-time logs, check [Grafana Dashboard]({grafana_url})"
                )
                if st.button("➡️ Next Step"):
                        st.session_state.step_1_done = True
                

        # # Phase 2: DAG Triggeringi
        if st.session_state.step_1_done:
            with st.expander("2️⃣ Airflow DAG Triggered"):
                st.markdown(
                                """
                                🛠 **Airflow is currently running the Kafka Producer script.**  
                                It performs the following steps:
                                
                                - ✅ Fetches **nearby roads** using the **Overpass API** with the coordinates:
                                    ```python
                                    nearby_roads = get_nearby_roads_with_coordinates(lat, lng)
                                    ```
                                - 🚀 Sends the road data to the Kafka topic: **`roads-topic`**
                                - 🧭 To view available Kafka topics, **navigate to the Kafka section** from the left-side navigation.

                                """
                            )
                if st.button("➡️ Next Step"):
                        st.session_state.step_2_done = True


        # Phase 3: Kafka Consumer → Nearby Roads
        if st.session_state.step_2_done:
            with st.expander("3️⃣ Kafka Consumer: Nearby Roads"):
                st.success("Kafka Consumer is processing messages containing nearby roads.")
                st.info("These roads are stored in the `roads` table within the PostgreSQL database.")
                st.markdown("""
                    📌 **Process:**
                    - Consumes messages from Kafka topic: `roads_topic`
                    - Uses Overpass API results received from the Kafka producer
                    - Stores road data into the `roads` table
                    
                    📄 **Sample of stored data is shown below**  
                """)
                road_data =load_data("roads_traffic","roads",engine)
                if road_data is not None and not road_data.empty:
                    st.dataframe(road_data)
                else:
                    st.warning("No road data received yet.")
                    
                st.markdown(""" 
                    🔍 For more, navigate to the **PostgreSQL** section and query the `road_data` table.""")
                if st.button("➡️ Next Step"):
                        st.session_state.step_3_done = True


        # # Phase 4: Road IDs → Kafka → Traffic Topic
        if st.session_state.step_3_done:
            with st.expander("4️⃣ Kafka Traffic Producer: send road data as a message "):
                st.info("Now it's time to schedule and trigger the Traffic DAG.")
                schedule_btn=st.button("Schedule Traffic Data DAG") 
                if schedule_btn:
                    schedule_traffic_Dag()
                if st.button("➡️ Next Step"):
                        st.session_state.step_4_done = True
       

        # Phase 5: Kafka Consumer → Nearby Roads
        if st.session_state.step_4_done:
            with st.expander("5️⃣  kafka Traffic and weather  Consumer: "):
                st.success("Now Kafka traffic Consumer is processing messages containing roads coordinates and other data .")
                st.info("📍 Successfully fetched road routes using the **TomTom Routing API**.")
                st.markdown(""" 📌 **Process:**

                    - 🔁 the **Traffic Producer DAG** fetches `road_id`s and sends them to the kafka `traffic_topic`.
                    - 🚦 The **Traffic Kafka Consumer** consumes each road ID, calls the **TomTom Route API**  of all major coordinates to:
                       - 📍 Collect **traffic data**  → stored in `traffic_data` table.
                       - 🌦️ Collect **weather data** → stored in `weather_data` table.

                    """)

                road_data =load_data("roads_traffic","traffic_data",engine)
                if road_data is not None and not road_data.empty:
                    st.markdown("### 🚦 Traffic Data from `traffic_data` Table")
                    st.dataframe(road_data)
                else:
                    st.markdown("### 🚦 Traffic Data from `traffic_data` Table")
                    st.warning("No road data received yet.")
                    
                road_data =load_data("roads_traffic","weather_data",engine)
                if road_data is not None and not road_data.empty:
                    st.markdown("###  🌦  🛣Traffic Data from `weather_data` Table")
                    st.dataframe(road_data)
                else:
                    st.markdown("###  🌦 🛣 Traffic Data from `weather_data` Table")
                    st.warning("No road data received yet.")
                    
                st.markdown(""" 
                    🔍 For more, navigate to the **PostgreSQL** section and query the `traffic_data` and `weather_data` table.
                """)
                if st.button("➡️ Next Step"):
                    st.session_state.step_5_done = True

            
        if st.session_state.step_5_done:
            with st.expander("6️⃣ Monitoring & Logs"):
                st.info("Centralized logging using Loki + Promtail + PostgreSQL + Airflow")
                if st.button("➡️ Next Step"):
                         st.session_state.step_6_done = True
  

    
        if st.session_state.step_6_done:
            st.markdown("""
                        Each step in the **ETL pipeline** is designed to generate **detailed logs**, enabling seamless monitoring and analysis. Whether it's **SQL query logs**, **API call logs**, **database operations**, or **exceptions**, **every action is recorded** to ensure transparency and traceability.

                        ---

                        🚨 **Service-based logs**, such as those from **Airflow** and **Kafka**, are also integrated into the system, providing a **holistic view** of the entire data flow.

                        🔍 All logs — including **warnings**, **info**, and **errors** — are collected and analyzed in real time, creating a **comprehensive, interactive Grafana dashboard**. This dashboard enables you to monitor:

                        - **File-based logs**
                        - **Database-based logs**
                        - **Action-specific logs** (e.g., SQL queries, API calls)
                        - **Service logs** (e.g., Airflow, Kafka)

                        💡 **Alerting** is an essential feature, triggering notifications for **critical events**, **errors**, or **performance issues**, helping the system stay proactive.

                        ---

                        👉 **[Visit the Grafana Dashboard](#)** to explore all logs and metrics. Log in using the provided credentials to access detailed insights into each step of the ETL pipeline.

                        """)

            st.markdown("""
                    ### 📸 **Dashboard Screenshot**

                    Here’s a preview of the **Grafana Dashboard**:

                    """)

            if st.button("➡️ Next Step"):
                    st.session_state.step_7_done = True

        # Button to trigger the display of the image
        if st.session_state.step_7_done:
            if st.button("Click to View Grafana Dashboard Sample"):
                # Display the image when the button is clicked
                with st.spinner("loading"): 
                    time.sleep(3)
                    st.image("images/Daasboard_1.png")
                
        st.button("🔄 Reset Steps", on_click=lambda: reset_steps())
