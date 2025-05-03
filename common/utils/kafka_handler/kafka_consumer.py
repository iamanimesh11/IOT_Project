import os
import json
import logging
from typing import Dict,Any

from kafka import KafkaConsumer
from kafka.errors import KafkaError

from Devices_processing_logic.refrigerator_processing_logic import get_subscribers_for_device
# --- Basic Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Configuration ---
DEVICE_TYPE = os.environ.get("DEVICE_TYPE")
if not DEVICE_TYPE:
    logging.error("FATAL: DEVICE_TYPE environment variable not set.")
    raise ValueError("DEVICE_TYPE environment variable must be provided.")

KAFKA_BROKERS = os.environ.get("KAFKA_BROKERS", "localhost:9092")
KAFKA_TOPIC = f"iot_telemetry_{DEVICE_TYPE}"

# --- Placeholder Processing Functions ---
# Replace these with imports of your actual logic later
def process_tv_data(payload: Dict[str, Any]):
    """Placeholder for processing TV data."""
    logging.info(f"Processing TV data (placeholder): {payload.get('device_id')}")
    # Add actual TV processing and DB logic here

def process_ac_data(payload: Dict[str, Any]):
    """Placeholder for processing AC data."""
    logging.info(f"Processing AC data (placeholder): {payload.get('device_id')}")
    # Add actual AC processing and DB logic here

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
        enable_auto_commit=True,          # Auto commit offsets
        group_id=f"{DEVICE_TYPE}_event_processor",  # Consumer group
        # Decode JSON, return None if decoding fails
        value_deserializer=lambda m: json.loads(m.decode('utf-8')) if m else None
    )
    logging.info(f"✅ Connected to Kafka brokers at: {KAFKA_BROKERS}")
    logging.info(f"📡 Listening to Kafka topic: {KAFKA_TOPIC}")
except KafkaError as ke:
    logging.error(f"❌ Kafka connection error: {ke}")
    raise
except Exception as e:
    logging.error(f"❌ Error connecting to Kafka: {e}")
    raise

# --- Message Loop ---
try:
    processing_function = PROCESSORS.get(DEVICE_TYPE, process_unknown_data)
    
    for message in consumer:
        try:
            payload = message.value
            if payload is None:
                logging.warning("skippin message due to deserialization error")
                continue
            
            logging.info(f"📨 Received message on {KAFKA_TOPIC}: {json.dumps(payload, indent=2)}")
            device_id=payload.get("device_id")
            message_device_type = payload.get("device_type")

            if not device_id or not message_device_type:
                logging.warning(f"Message missing 'device_id' or 'device_type'. Skipping. Payload: {payload}")
                
            else:
                
                subscribers=get_subscribers_for_device(device_id,device_type)
                try:
                    # --- Device-Specific Logic Starts Here ---
                    processing_function(payload)
                except Exception as processing_error:
                    logging.error(f"❌ Error processing message: {processing_error}. Payload: {payload}")
        
        except json.JSONDecodeError as json_err: # Catch errors if deserializer fails unexpectedly (though unlikely with lambda)
            logging.error(f"❌ JSON Decode Error processing message at offset {message.offset}: {json_err}")
        except KeyError as ke:
            logging.error(f"❌ Missing key in payload at offset {message.offset}: {ke}. Payload: {payload}")
        except Exception as processing_error:
            # Catch errors during specific message processing
            logging.error(f"❌ Error processing message at offset {message.offset}: {processing_error}. Payload: {payload}")
            # Decide if you want to continue or stop based on the error (e.g., raise to stop)


except KeyboardInterrupt:
    logging.info("🔌 Stopping Kafka consumer due to KeyboardInterrupt...")
except Exception as e:
    logging.error(f"❌ Kafka Error during consumption: {ke}")
finally:
    if 'consumer' in locals() and consumer:
        consumer.close()
    logging.info("👋 Kafka Consumer stopped.")
