import paho.mqtt.client as mqtt
import json

MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "iot/#"  # Subscribe to all device topics

# Called when client connects to broker
def on_connect(client, userdata, flags, rc):
    print("✅ Connected with result code " + str(rc))
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
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

# Connect and start loop
client.connect(MQTT_BROKER, MQTT_PORT, 60)
print("🚀 Listening for incoming device messages...\n")
client.loop_forever()
