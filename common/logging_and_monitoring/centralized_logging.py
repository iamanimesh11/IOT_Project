import os
import logging
import json
import time
import requests
import sys
import re

# Loki URL
LOKI_URL = "http://loki:3100/loki/api/v1/push"

# Handle AIRFLOW_HOME override
AIRFLOW_HOME = os.getenv("AIRFLOW_HOME", "/opt/airflow")
if AIRFLOW_HOME != "/opt/airflow":
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    AIRFLOW_HOME = BASE_DIR

# Logging directory & file setup
SCRIPTS_PATH = os.path.join(AIRFLOW_HOME, "common", "logging_and_monitoring", "logs")
os.makedirs(SCRIPTS_PATH, exist_ok=True)  # ✅ Make sure the logs dir exists

script_logs_path = os.path.join(SCRIPTS_PATH, "loki_errors.log")
if not os.path.exists(script_logs_path):
    open(script_logs_path, 'a').close()  # ✅ Ensure the file exists

# Setup logger for internal logging (errors during Loki push etc.)
loki_logger = logging.getLogger("loki_logger")
loki_logger.setLevel(logging.ERROR)

formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

file_handler = logging.FileHandler(script_logs_path)
file_handler.setFormatter(formatter)
loki_logger.addHandler(file_handler)

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
loki_logger.addHandler(console_handler)

loki_unavailable = False


def extract_json_from_message(message):
    """
    Extracts a valid JSON object from a string if present, otherwise returns the original message.
    """
    match = re.search(r'- (?:INFO|WARNING|ERROR|DEBUG|CRITICAL) - (.*)', message)
    if match:
        return match.group(1).strip()
    else:
        return None


# Function to send logs to Loki
def send_log_to_loki(level, message, job_name, component_name,stage,service, max_retries=3):
    message_string = extract_json_from_message(message)

    global loki_unavailable  # Use a global flag
    # If Loki is already marked as unavailable, stop immediately
    if loki_unavailable:
        print(f"❌ Loki is down. Stopping script execution.")
        loki_logger.critical(f"❌ Loki is down. Stopping script execution.")
        return

    log_entry = {
        "streams": [
            {
                "stream": {
                    "level": level.upper(),

                    "job": job_name,
                    "component": component_name,
                    "service_name":service,
                    "stage":stage
                },

                "values": [[str(int(time.time() * 1e9)), json.dumps({
                    "level": level.upper(),
                    "message": message_string,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "stage": stage  # ✅ Now it is inside the JSON payload, Grafana will detect it

                })]]
            }
        ]
    }
    for attempt in range(max_retries):
        try:
            response = requests.post(
                LOKI_URL,
                headers={"Content-Type": "application/json"},
                data=json.dumps(log_entry),
                timeout=5  # Set timeout for better control
            )
            if response.status_code == 204:
                return
            # Log the failed attempt
            loki_logger.error(
                f"Failed to send log to Loki [{job_name}]. Attempt {attempt + 1}/{max_retries}: {response.text}")
        except requests.exceptions.RequestException as e:
            loki_logger.error(f"Loki connection error [{job_name}]. Attempt {attempt + 1}/{max_retries}: {e}")
            print("Loki connection error [{job_name}]. Attempt")
        time.sleep(4)
    loki_unavailable = True
    loki_logger.critical(f"🚨 All {max_retries} attempts to send logs to Loki failed. Disabling Loki logging.")


# Custom log handler to send logs to Loki
class LokiHandler(logging.Handler):
    def __init__(self, job_name="default_job", component_name="default_component",service_name="default_service"):
        super().__init__()
        self.job_name = job_name  # Store the job name dynamically
        self.component = component_name
        self.service=service_name

    def emit(self, record):
        stage = getattr(record, "stage", "unknown")  # Extract 'stage' from extra, default to 'unknown'
        log_entry = self.format(record)
        send_log_to_loki(record.levelname, log_entry, self.job_name, self.component,stage,self.service)


# Function to configure logging
def setup_logger(job="MyLogger", component="my_component",service="my_service", log_file=script_logs_path):
    logger_name = f"{job}.{component}"
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)  # Capture all log levels

    # os.makedirs(os.path.dirname(log_file), exist_ok=True)

    # Formatter
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    # Console Handler (Print to console)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # File Handler (Save to file)
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)

    # Loki Handler (Send to Loki)
    # Loki Handler (Send to Loki)
    loki_handler = LokiHandler(job_name=job, component_name=component,service_name=service)
    loki_handler.setFormatter(formatter)

    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.addHandler(loki_handler)

    return logger
