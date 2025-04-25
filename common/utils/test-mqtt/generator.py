import random
import time
import uuid
import json
from datetime import datetime
import paho.mqtt.client as mqtt

# MQTT Broker settings (local Docker container)
MQTT_BROKER = "localhost"
MQTT_PORT = 1883

# Simulated device models and behaviors
DEVICE_MODELS = {
    "washing_machine": {
        "models": ["WM1001", "WM2000", "WMProX"],
        "statuses": ["idle", "running", "paused", "completed"],
        "errors": ["E01", "E02", None]
    },
    "tv": {
        "models": ["TVUltraHD", "TVSmartX", "TVBasic"],
        "statuses": ["off", "on", "standby"],
        "errors": ["E10", None]
    }
}

# Function to generate telemetry
def generate_telemetry():
    device_type = random.choice(list(DEVICE_MODELS.keys()))
    model_data = DEVICE_MODELS[device_type]
    device_id = str(uuid.uuid4())[:8]
    model = random.choice(model_data["models"])
    status = random.choices(model_data["statuses"], weights=[0.3, 0.4, 0.2, 0.1] if device_type == "washing_machine" else [0.3, 0.5, 0.2])[0]
    error_code = random.choices(model_data["errors"], weights=[0.03 if e else 0.94 for e in model_data["errors"]])[0]

    payload = {
        "device_id": device_id,
        "device_type": device_type,
        "model": model,
        "status": status,
        "error_code": error_code,
        "timestamp": datetime.utcnow().isoformat()
    }

    topic = f"iot/{device_type}/{device_id}"
    return topic, json.dumps(payload)

# Connect to MQTT
client = mqtt.Client()
client.connect(MQTT_BROKER, MQTT_PORT, 60)

# Loop to simulate data sending
print("🚀 Starting device simulation...")
while True:
    topic, message = generate_telemetry()
    client.publish(topic, message)
    print(f"📡 Published to [{topic}]: {message}")
    #time.sleep(random.uniform(1, 3))  # Send every 1–3 seconds
    time.sleep(60)  # Send every 1–3 seconds
