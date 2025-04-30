# run_device_type_consumers.py

import json
import subprocess

with open("device_types.json") as f:
    device_types = json.load(f)["device_types"]

for device in device_types:
    container_name = f"mqtt_consumer_{device}"
    subprocess.run([
        "docker", "run", "-d",
        "--name", container_name,
        "--network", "host",  # So it can access MQTT broker locally
        "-e", f"DEVICE_TYPE={device}",
        "-e", "MQTT_BROKER=localhost",
        "mqtt_consumer_image"  # name of image you build from Dockerfile
    ])
    
    
    
#expects json format
#{
#     "device_types": [
#         "temperature_sensor",
#         "humidity_sensor",
#         "motion_detector"
#     ]
# }