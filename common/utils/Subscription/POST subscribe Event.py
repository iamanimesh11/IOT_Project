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
# --- FastAPI App ---
app = FastAPI()

# Authentication Header for FastAPI
security = HTTPBearer()


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

def get_token_from_header(request: Request):
    """Extract token from the Authorization header."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    return auth_header.split(" ")[1]  # Extract the token from the 'Bearer <token>' header


@app.post("/subscribe/{device_id}")
async def handle_subscription(device_id: str, request: Request, token: str = Depends(get_token_from_header)):
    # Extract token from the Authorization header
    token_data = verify_token(token.credentials)
    if not token_data:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

        # Token is valid, proceed with subscription logic
    data = await request.json()
    service_id = data.get("service_id")
    expiry_hours = int(data.get("expiry_hours", 24))

    if not service_id or not device_id:
        raise HTTPException(status_code=400, detail="Missing service_id or device_id")

    redis_key = f"sub:{service_id}:{device_id}"

    # Check Redis for existing subscription
    if r.exists(redis_key):
        return {"message": "Already subscribed"}

    now_utc = datetime.datetime.now(datetime.timezone.utc)

    event = {
        "service_id": service_id,
        "device_id": device_id,
        "timestamp": now_utc.isoformat(),
        "expiry_hours": expiry_hours
    }

    producer = get_kafka_producer()
    if not producer:
        raise HTTPException(status_code=503, detail="Kafka unavailable")

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
        raise HTTPException(status_code=500, detail="Internal error")
    finally:
        producer.flush()
        producer.close()

