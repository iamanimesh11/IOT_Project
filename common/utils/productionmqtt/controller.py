# run_device_type_consumers.py

import json
import subprocess # Corrected typo

with open(r"E:\IOT_Project\common\utils\test-mqtt\device_models.json") as f:
    device_data = json.load(f)

for device_type, devices in device_data.items(): # Corrected variable name
    for device in devices:
        # Ensure only one container per device_type is created
        # If multiple devices exist for a type, only the first one will get a container
        container_name = f"mqtt_consumer_{device_type}"
        print(f"  Attempting to run container: {container_name} for device ID: {device['device_id']}") # DEBUG

        result = subprocess.run([
            "docker", "run", "-d",
            "--name", container_name,
            "--network", "host",  # For local MQTT broker access
            "-e", f"DEVICE_TYPE={device_type}",  # Pass the device type
            "-e", "MQTT_BROKER=localhost",
            "-e", "PYTHONUNBUFFERED=1", # Force unbuffered output
            "mqtt_consumer_image"   
        ], capture_output=True, text=True) # Capture output for better error checking

        if result.returncode == 0:
            print(f"  'docker run' command succeeded for {container_name}") # DEBUG
        else:
            print(f"  ⚠️ 'docker run' command FAILED for {container_name} with code {result.returncode}") # DEBUG
            print(f"  Error Output: {result.stderr}") # Print Docker's error message

        break # Exit the inner loop after processing the first device for this type
