import paho.mqtt.client as mqtt
import json
import os
import logging
from kafka import KafkaProducer
from kafka.errors import KafkaError

# --- Basic Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# --- Configuration from Environment Variables ---
DEVICE_TYPE = os.environ.get("DEVICE_TYPE")
if not DEVICE_TYPE:
    logging.error("FATAL: DEVICE_TYPE environment variable not set.")
    raise ValueError("DEVICE_TYPE environment variable must be provided.")

MQTT_BROKER = os.environ.get("MQTT_BROKER", "localhost")
MQTT_PORT = 1883
MQTT_TOPIC = f"iot/telemetry/{DEVICE_TYPE}/#"  # Subscribe to all device topics for this type

KAFKA_BROKERS = os.environ.get("KAFKA_BROKERS", "localhost:9092") # Default Kafka broker if not set
KAFKA_TOPIC = f"iot_telemetry_{DEVICE_TYPE}" # Dynamic Kafka topic based on device type

# --- Kafka Producer Setup ---
producer = None
try:
    producer = KafkaProducer(bootstrap_servers=KAFKA_BROKERS.split(','), # Allow comma-separated list
                             value_serializer=lambda v: v) # Send raw bytes
    logging.info(f"Kafka Producer connected to brokers: {KAFKA_BROKERS}")
    logging.info(f"Messages will be sent to Kafka topic: {KAFKA_TOPIC}")
except KafkaError as e:
    logging.error(f"Failed to initialize Kafka Producer: {e}")
    # Depending on requirements, you might want to exit here or retry connection
    producer = None # Ensure producer is None if connection failed

# Called when client connects to broker
def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        logging.info(f"✅ Connected successfully to MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
        client.subscribe(MQTT_TOPIC)
        logging.info(f"🔍 Subscribed to MQTT topic '{MQTT_TOPIC}'")
    else:
        logging.error(f"⚠️ Failed to connect to MQTT Broker, reason code: {reason_code}")
        # You might want to handle specific reason codes here

# Called when a message is received
def on_message(client, userdata, msg):
    if not producer:
        logging.warning("Kafka producer not available. Skipping message forwarding.")
        return # Cannot forward if producer isn't working

    try:
        # Log reception (optional: decode for logging if needed, but send raw bytes)
        logging.info(f"📥 Received MQTT message from [{msg.topic}]. Forwarding to Kafka topic [{KAFKA_TOPIC}]...")
        # logging.debug(f"Payload (decoded for debug): {msg.payload.decode('utf-8', errors='ignore')}")

        # Send the raw message payload (bytes) to the specific Kafka topic
        future = producer.send(KAFKA_TOPIC, value=msg.payload)

        # Optional: Add callbacks for success/failure logging per message
        # future.add_callback(on_kafka_send_success, msg.topic)
        # future.add_errback(on_kafka_send_error, msg.topic)

    except Exception as e:
        logging.error(f"⚠️ Error processing message from topic {msg.topic} or sending to Kafka: {e}")

# Optional: Kafka send success callback
# def on_kafka_send_success(record_metadata, mqtt_topic):
#     logging.debug(f"Successfully sent message from MQTT topic {mqtt_topic} to Kafka topic {record_metadata.topic} partition {record_metadata.partition} offset {record_metadata.offset}")

# Optional: Kafka send error callback
# def on_kafka_send_error(excp, mqtt_topic):
#     logging.error(f"Error sending message from MQTT topic {mqtt_topic} to Kafka: {excp}")

# Set up client
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2) # Specify V2 callback API
client.on_connect = on_connect
client.on_message = on_message

# Connect and start loop
client.connect(MQTT_BROKER, MQTT_PORT, 60)

logging.info("🚀 Starting MQTT client loop...")
try:
    client.loop_forever()
except KeyboardInterrupt:
    logging.info("\n🔌 KeyboardInterrupt received. Disconnecting gracefully...")
except Exception as e:
    logging.error(f"❌ Unexpected error in main loop: {e}") # Log any other exceptions
finally:
    if producer:
        logging.info("Flushing Kafka messages...")
        producer.flush() # Ensure all buffered messages are sent
        producer.close()
        logging.info("Kafka producer closed.")
    client.disconnect()
    logging.info("👋 MQTT Client disconnected. Consumer stopped.")
