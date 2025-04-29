import random
import time
import uuid
import json
from datetime import datetime
import paho.mqtt.client as mqtt

# MQTT Broker settings (local Docker container)
MQTT_BROKER = "localhost"
MQTT_PORT = 1883


with open(r"E:\IOT_Project\common\utils\test-mqtt\device_models.json") as f:
    devices=json.load(f)

with open(r"E:\IOT_Project\common\utils\test-mqtt\device_profiles.json") as f:
    profiles = json.load(f)

# Simulated device models and behaviors


# Function to generate telemetry
def generate_telemetry(device):
    device_type = device["device_type"]
    profile = profiles.get(device_type, {})

    status_options = profile.get("status", ["unknown"])
    error_options = profile.get("errors", [])
    error = random.choice(error_options) if random.random() < 0.1 else None


    payload = {
        "device_id": device["device_id"],
        "device_type":device["device_type"],
        "device_name": device["device_name"],
        "status": random.choice(status_options),
        "error_code": error,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    }

    return payload

# Connect to MQTT
client = mqtt.Client()
client.connect(MQTT_BROKER, MQTT_PORT, 60)

# Loop to simulate data sending
print("🚀 Starting device simulation...")
while True:
    device=random.choice(devices)
    topic=f"iot/telemetry/{device['device_type']}/{device['device_id']}"
    payload=json.dumps(generate_telemetry(device))
    client.publish(topic, payload)

    print(f"📡 Published to [{topic}]: {payload}")
    #time.sleep(random.uniform(1, 3))  # Send every 1–3 seconds
    time.sleep(60)  # Send every 1–3 seconds
