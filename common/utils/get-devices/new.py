import os
import sys
import psycopg2
import configparser
import logging
import datetime
import json
import redis
from flask import Flask, request, jsonify
from kafka import KafkaProducer

# --- Load Config ---
CONFIG_PATH = r"C:\Users\Acer\PycharmProjects\IOT_Project\common\credentials\config.ini"
config = configparser.ConfigParser()
if not os.path.exists(CONFIG_PATH):
    logging.error(f"Config file not found at: {CONFIG_PATH}")
    sys.exit(1)
config.read(CONFIG_PATH)

# --- Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Kafka Config ---
kafka_config = config.get('kafka', {})
KAFKA_BOOTSTRAP_SERVERS = kafka_config.get('bootstrap_servers', 'localhost:9092')
SUBSCRIPTION_TOPIC = kafka_config.get('subscription_topic', 'subscription_requests')

# --- Redis ---
r = redis.Redis(host='localhost', port=6379, db=0)

# --- Kafka Producer ---
def get_kafka_producer():
    try:
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        logging.info("Kafka producer connected.")
        return producer
    except Exception as e:
        logging.error(f"Kafka producer connection failed: {e}")
        return None

# --- Flask App ---
app = Flask(__name__)

def verify_token(token):
    """Check if the token is valid and exists in Redis."""
    if not token:
        return None
    # Check Redis for the token
    cached_token_data = r.get(token)
    if cached_token_data:
        return json.loads(cached_token_data)  # return device ID from cached data
    else:
        try:
            # Decode the JWT token to verify it
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            return payload  # Return the decoded data if token is valid
        except jwt.ExpiredSignatureError:
            return {"error": "Token has expired"}
        except jwt.InvalidTokenError:
            return {"error": "Invalid token"}

@app.route("/subscribe/<string:device_id>", methods=["POST"])
def handle_subscription(device_id):
    # Extract token from the Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"error": "Missing or invalid Authorization header"}), 401

    token = auth_header.split(" ")[1]  # Extract the token from the 'Bearer <token>' header
    token_data = verify_token(token)
    if not token_data:
        return jsonify({"error": "Invalid or expired token"}), 401

    # Token is valid, proceed with subscription logic
    data = request.json
    service_id = data.get("service_id")
    expiry_hours = int(data.get("expiry_hours", 24))

    if not service_id or not device_id:
        return jsonify({"error": "Missing service_id or device_id"}), 400

    redis_key = f"sub:{service_id}:{device_id}"

    # Check Redis for existing subscription
    if r.exists(redis_key):
        return jsonify({"message": "Already subscribed"}), 200

    now_utc = datetime.datetime.now(datetime.timezone.utc)

    event = {
        "service_id": service_id,
        "device_id": device_id,
        "timestamp": now_utc.isoformat(),
        "expiry_hours": expiry_hours
    }

    producer = get_kafka_producer()
    if not producer:
        return jsonify({"error": "Kafka unavailable"}), 503

    try:
        producer.send(SUBSCRIPTION_TOPIC, value=event, key=device_id.encode('utf-8'))
        logging.info(f"Published event for {device_id}")
        return jsonify({
            "message": "Subscription request accepted",
            "device_id": device_id,
            "request_timestamp": now_utc.isoformat()
        }), 202
    except Exception as e:
        logging.error(f"Kafka error: {e}")
        return jsonify({"error": "Internal error"}), 500
    finally:
        producer.flush()
        producer.close()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
