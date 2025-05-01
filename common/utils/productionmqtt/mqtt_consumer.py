print("--- MQTT Consumer Script Started ---") # Add this line

import paho.mqtt.client as mqtt
import json
import os

device_type=os.environ.get("DEVICE_TYPE","na")
if  device_type=="na":
    print("issue")
    raise ValueError("device type not prodvided in enviornemnet variable")

    
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = f"iot/telemetry/{device_type}/#"  # Subscribe to all device topics for this type

# Called when client connects to broker
def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print("✅ Connected successfully!")
    else:
        print(f"⚠️ Failed to connect, reason code: {reason_code}")
        # You might want to handle specific reason codes here
    client.subscribe(MQTT_TOPIC)
    print(f"🔍 Subscribed to topic '{MQTT_TOPIC}'")
    
# Called when a message is received
def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        print(f"📥 Message from [{msg.topic}]: {json.dumps(payload, indent=2)}")
    except Exception as e:
        print("⚠️ Error decoding message:", e)

# Set up client
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2) # Specify V2 callback API
client.on_connect = on_connect
client.on_message = on_message

# Connect and start loop
client.connect(MQTT_BROKER, MQTT_PORT, 60)

print("🚀 Entering main loop...")
try:
    client.loop_forever()
except KeyboardInterrupt:
    print("\n🔌 Disconnecting gracefully...")
except Exception as e:
    print(f"❌ Unexpected error in main loop: {e}") # Log any other exceptions
finally:
    client.disconnect()
    print("👋 MQTT Consumer stopped.")
