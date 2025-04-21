import time
import json
import logging
import requests
import random
import string

# Loki URL
LOKI_URL = "http://localhost:3100/loki/api/v1/push"

# Set up logging
logger = logging.getLogger("LokiLogger")
logger.setLevel(logging.DEBUG)

# Function to send logs to Loki
def send_log_to_loki(level, message):
    try :
        log_entry = {
            "streams": [
                {
                    "stream": {"job": "python_script"},
                    "values": [[str(int(time.time() * 1e9)), json.dumps({
                        "level": level.upper(),
                        "message": message,
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    })]]                    }
            ]
        }
        response = requests.post(
            LOKI_URL,
            headers={"Content-Type": "application/json"},
            data=json.dumps(log_entry)
        )

        if response.status_code == 204:
            print(f"✅ Log sent: {message}")
        else:
            print(f"❌ Failed to send log: {response.text}")

    except Exception as e:
        print(f"exception caught: {e}")

# Custom log handler to send logs to Loki
class LokiHandler(logging.Handler):
    def emit(self, record):
        log_entry = self.format(record)
        send_log_to_loki(record.levelname, log_entry)

# Add LokiHandler to the logger
loki_handler = LokiHandler()
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
loki_handler.setFormatter(formatter)
logger.addHandler(loki_handler)

# Logging Examples
logger.info("This is an INFO log")
logger.warning("This is a WARNING log")
logger.error("This is an ERROR log")

# Function to generate random string
def generate_random_string(length=10):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for i in range(length))

# Function to generate random data
def generate_random_data():
    data = {
        "user_id": random.randint(1, 100),
        "product_id": random.randint(1000, 2000),
        "amount": round(random.uniform(10.0, 100.0), 2),
        "status": random.choice(["success", "failure", "pending"]),
        "random_string": generate_random_string()
    }
    return json.dumps(data)

# Logging random data loop
try:
    while True:
        log_level = random.choice(["INFO", "WARNING", "ERROR"])
        random_data = generate_random_data()

        if log_level == "INFO":
            logger.info(random_data)
        elif log_level == "WARNING":
            logger.warning(random_data)
        elif log_level == "ERROR":
            logger.error(random_data)

        time.sleep(random.uniform(0.5, 2.0))  # Log every 0.5 to 2 seconds

except KeyboardInterrupt:
    print("Logging stopped.")