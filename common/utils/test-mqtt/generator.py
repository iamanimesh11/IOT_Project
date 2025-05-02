import random
import time
import uuid
import json,os
from datetime import datetime
import paho.mqtt.client as mqtt

# MQTT Broker settings (local Docker container)
MQTT_BROKER = "localhost"
MQTT_PORT = 1883

def get_root_Directory_path(n):
    path=os.path.abspath(__file__)
    for _ in range(n+1):
        path=os.path.dirname(path)
    return path
root_dir_path=get_root_Directory_path(3)
device_json_path= os.path.join(root_dir_path, "common", "utils","test-mqtt","device_models.json")
device_profiles_path=os.path.join(root_dir_path, "common", "utils","test-mqtt","device_profiles.json")

with open(device_json_path) as f:
    device_data = json.load(f)

# Create a flat list of all devices, adding the device_type to each device object
all_devices = []
for device_type, devices_list in device_data.items():
    for device in devices_list:
        all_devices.append({**device, "device_type": device_type}) # Add device_type key
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
        "model_name": device["model_name"],
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
    device=random.choice(all_devices) # Select from the flat list
    topic=f"iot/telemetry/{device['device_type']}/{device['device_id']}"
    payload=json.dumps(generate_telemetry(device))
    client.publish(topic, payload)

    print(f"📡 Published to [{topic}]: {payload}")
    #time.sleep(random.uniform(1, 3))  # Send every 1–3 seconds
    time.sleep(5)  # Send every 1–3 seconds
