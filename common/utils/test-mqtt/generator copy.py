import random
import time
import uuid
import json
from datetime import datetime
import paho.mqtt.client as mqtt

# MQTT Broker settings (local Docker container)
MQTT_BROKER = "localhost"
MQTT_PORT = 1883

with open("devices.json") as f:
    devices=json.load(f)
    
with open("error_codes.json") as f:
    error_codes = json.load(f)

# Simulated device models and behaviors


# Function to generate telemetry
def generate_telemetry():
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

    topic = f"iot/telemetry/{device_type}/{device_id}"
    return topic, json.dumps(payload)

# Connect to MQTT
client = mqtt.Client()
client.connect(MQTT_BROKER, MQTT_PORT, 60)

# Loop to simulate data sending
print("🚀 Starting device simulation...")
while True:
    device=random.choice(devices)
    topic=f"iot/telemetry/{device['device_type']}/{device['device_id']}"
    payload=json.dump(generate_telemetry(device))
    client.publish(topic, payload)

    print(f"📡 Published to [{topic}]: {message}")
    #time.sleep(random.uniform(1, 3))  # Send every 1–3 seconds
    time.sleep(60)  # Send every 1–3 seconds
