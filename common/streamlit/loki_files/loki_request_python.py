import requests
import time
import json
import pandas as pd
loki_address = "http://localhost:3100"  # Replace with your Loki address
query = '{job="python_script"}'


LOKI_QUERY_URL = "http://localhost:3100/loki/api/v1/query_range"

def fetch_logs(selected_job):
    if not selected_job:
        return pd.DataFrame()

    query = f'{{job="{selected_job}"}}'
    params = {
        "query": query,
        "limit": 500,
        "direction": "backward",
        "step": "10s",
    }

    try:
        response = requests.get(LOKI_QUERY_URL, params=params)
        data = response.json()
        print(data)
        logs = []

        # Parse logs
        for stream in data.get("data", {}).get("result", []):
            for entry in stream.get("values", []):
                log_id = entry[0]  # Timestamp or log ID
                log_message = entry[1]  # Log message (JSON string)

                try:
                    log_data = json.loads(log_message)  # Parse the outer JSON
                    if selected_job =="python_script":

                        # Extract the 'message' field and parse the nested JSON inside it
                        message_part = log_data["message"].split(" - ")[-1]  # Get JSON string
                        nested_data = json.loads(message_part)  # Parse it
                        # Store extracted values
                        logs.append({
                            "log_id": log_id,
                            "Level": log_data.get("level", "UNKNOWN"),
                            "User ID": nested_data.get("user_id", "N/A"),
                            "Product ID": nested_data.get("product_id", "N/A"),
                            "Amount": nested_data.get("amount", "N/A"),
                            "Status": nested_data.get("status", "N/A"),
                            "Random String": nested_data.get("random_string", "N/A"),
                        })
                    elif selected_job== "database_connection_logger":
                        parts =log_data.get("message", "N/A").split(" - ")
                        print(parts)
                        timestamp = parts[0].strip()
                        log_level = parts[1].strip()
                        error_message = parts[2].strip()
                        logs.append({
                            "log_id": log_id,
                            "timestamp":timestamp,
                            "log_level":log_level,
                            "error_message":error_message
                        })
                    else:
                        logs.append({
                            "log_id":log_id,
                            "Raw Log":log_message
                        })

                except json.JSONDecodeError:
                    print(f"Failed to parse log message: {log_message}")

        return pd.DataFrame(logs)

    except requests.exceptions.RequestException as e:
        print(f"Error fetching logs: {e}")  # ✅ Use print instead of Streamlit
        return pd.DataFrame()


# Function to fetch all job IDs from Loki
def fetch_job_ids():
    LOKI_LABELS_URL = "http://localhost:3100/loki/api/v1/label/job/values"

    try:
        response = requests.get(LOKI_LABELS_URL)
        data = response.json().get("data",[])
        return data

    except requests.exceptions.RequestException as e:
        print(f"Error fetching job IDs: {e}")  # ✅ Print instead of using Streamlit
        return []


print(fetch_logs("database_connection_logger"))