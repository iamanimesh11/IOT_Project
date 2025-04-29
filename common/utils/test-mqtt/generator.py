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
def generate_telemetry(device):
    device_type = device["device_type"]
    status_options = ["idle", "running", "paused"]
    error_chance = random.random()
    error =None
    
    
    if error_chance < 0.1 and device_type in error_codes:
        error = random.choice(error_codes[device_type])

    payload = {
        "device_id": device["device_id"],
        "device_type":device["device_type"],
        "device_name": device["device_name"],
        "status": random.choice(status_options),
        "error_code": error,
        "timestamp": time.time()
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
    payload=json.dump(generate_telemetry(device))
    client.publish(topic, payload)

    print(f"📡 Published to [{topic}]: {payload}")
    #time.sleep(random.uniform(1, 3))  # Send every 1–3 seconds
    time.sleep(60)  # Send every 1–3 seconds
