from kafka import KafkaConsumer
import os
import json
import logging
from typing import Dict,Any
# --- Basic Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
from Devices_processing_logic.TV_processing_logic import get_subscribers_for_device
from kafka import KafkaConsumer

# --- Configuration ---
DEVICE_TYPE = os.environ.get("DEVICE_TYPE")
if not DEVICE_TYPE:
    logging.error("FATAL: DEVICE_TYPE environment variable not set.")
    raise ValueError("DEVICE_TYPE environment variable must be provided.")

KAFKA_BROKERS = os.environ.get("KAFKA_BROKERS", "localhost:9092")
KAFKA_TOPIC = f"iot_telemetry_{DEVICE_TYPE}"



    
def process_unknown_data(payload: Dict[str, Any]):
    """Handles data for unexpected device types if needed."""
    logging.warning(f"Received data for unhandled device type '{DEVICE_TYPE}': {payload}")

# --- Map device types to functions ---
# This dictionary allows easy extension for new device types
PROCESSORS = {
    "tv": process_tv_data,
    "ac": process_ac_data,
    # Add other device types here
}

# --- Kafka Consumer Setup ---
try:
    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BROKERS.split(','),
        auto_offset_reset='earliest',     # or 'latest'
        enable_auto_commit=True,
        group_id=f"{DEVICE_TYPE}_event_processor",  # Consumer group
        value_deserializer=lambda m: json.loads(m.decode('utf-8'))  # Decode JSON
    )
    logging.info(f"✅ Connected to Kafka brokers at: {KAFKA_BROKERS}")
    logging.info(f"📡 Listening to Kafka topic: {KAFKA_TOPIC}")
except Exception as e:
    logging.error(f"❌ Error connecting to Kafka: {e}")
    raise

# --- Message Loop ---
try:
    processing_function = PROCESSORS.get(DEVICE_TYPE, process_unknown_data)
    
    for message in consumer:
        payload = message.value
        if payload is None:
            logging.warning("skippin message due to deserialization error")
            continue
        
        logging.info(f"📨 Received message on {KAFKA_TOPIC}: {json.dumps(payload, indent=2)}")
        device_id=payload.get("device_id")
        
        if not device_id:
            logging.warning(f"Message missing 'deviceId'. Cannot check subscriptions. Payload: {payload}")
            
        else:
            try:
                subscribers=get_subscribers_for_device(device_id,device_type)
        device_type=payload.get("device_type")
        try:
            # --- Device-Specific Logic Starts Here ---
            processing_function(payload)
            # --- Device-Specific Logic Ends Here ---
        except Exception as processing_error:
            # Catch errors during specific message processing
            logging.error(f"❌ Error processing message: {processing_error}. Payload: {payload}")
            # Decide if you want to continue or stop based on the error


except KeyboardInterrupt:
    logging.info("🔌 Stopping Kafka consumer...")
except Exception as e:
    logging.error(f"❌ Unexpected error: {e}")
finally:
    consumer.close()
    logging.info("👋 Kafka Consumer stopped.")
