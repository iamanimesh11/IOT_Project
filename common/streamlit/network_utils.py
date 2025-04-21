# network_utils.py
import socket
import streamlit as st

SERVICES = {
        "Kafka": {
                    "host": "localhost", 
                    "port": 9092
                    },
        "Zookeeper": {
                    "host": "localhost",
                    "port": 2181
                    },
        "Postgres": {
                    "host": "localhost", 
                    "port": 5432
                    },
        "Airflow Webserver": {
                    "host": "airflow-webserver",
                    "port": 8080
                    },
        "Streamlit": {
                    "host": "streamlit",
                    "port": 8501
                    },
        "Grafana": {
                    "host": "grafana",
                    "port": 3000
                    },
        "Loki": {
                    "host": "loki", 
                    "port": 3100
                },
    }

def check_connection(host, port, timeout=3):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception as e:
        return str(e)

def check_all_services():
        st.write("\n🧪 Checking Docker Service Connectivity:\n" + "-" * 45)
        for name, config in SERVICES.items():
            host, port = config["host"], config["port"]
            result = check_connection(host, port)
            status = "✅ UP" if result ==True  else "❌ DOWN"
            st.write(f"{name:<20} -> {host}:{port:<5} {status}")
        st.write("-" * 45 + "\n")
        st.write("hi")
        st.write("-" * 45 + "\n")

