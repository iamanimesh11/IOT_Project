import os
import sys
import configparser
import logging
import datetime
import json
import redis
# from flask import Flask, request, jsonify # No longer needed
from kafka import KafkaProducer
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.security import HTTPBearer
import jwt as pyjwt # Import pyjwt for token verification

# --- Load Config ---
CONFIG_PATH = r"E:\IOT_Project\common\credentials\config.ini"
config = configparser.ConfigParser()
if not os.path.exists(CONFIG_PATH):
    logging.error(f"Config file not found at: {CONFIG_PATH}")
    sys.exit(1)
config.read(CONFIG_PATH)

# --- Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Kafka Config ---
kafka_config = config['kafka']
KAFKA_BOOTSTRAP_SERVERS = kafka_config.get('bootstrap_servers', 'localhost:9092')
SUBSCRIPTION_TOPIC = kafka_config.get('subscription_topic', 'subscription_requests')

security_config = config['security']
SECRET_KEY = security_config.get('jwt_secret_key', fallback='default-fallback-key-if-needed')

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

def verify_token(token: str):
    """Decodes the JWT token and returns the payload or None if invalid/expired."""
    if not token:
        return None
    try:
        # Decode the JWT token to verify signature and expiry
        payload = pyjwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        
        return payload  # Return the decoded payload (contains service_id, exp)
    except pyjwt.ExpiredSignatureError:
        logging.warning("Token verification failed: Expired signature")
        return None # Indicate failure due to expiry
    except pyjwt.InvalidTokenError as e:
        logging.warning(f"Token verification failed: Invalid token - {e}")
        return None # Indicate failure due to invalid token

def get_token_from_header(request: Request):
    """Extract token from the Authorization header."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    return auth_header.split(" ")[1]  # Extract the token from the 'Bearer <token>' header


@app.post("/subscribe/{device_id}", status_code=202) # Set default success status code if desired
async def handle_subscription(device_id: str, request: Request, token: str = Depends(get_token_from_header)):
    # Verify the token string directly
    token_data = verify_token(token)
    if not token_data:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    # Optionally check if the payload contains the expected service_id
    verified_service_id = token_data.get('service_id')
    if not verified_service_id:
         raise HTTPException(status_code=401, detail="Token payload missing service_id")
        # Token is valid, proceed with subscription logic
    data = await request.json()
    service_id = data.get("service_id")
    expiry_hours = int(data.get("expiry_hours", 24))

    if not service_id or not device_id:
        raise HTTPException(status_code=400, detail="Missing service_id or device_id")

    # Optional: Ensure the service_id in the token matches the one in the request body
    # if verified_service_id != service_id:
    #     logging.warning(f"Token service_id '{verified_service_id}' mismatch with request body service_id '{service_id}'")
    #     raise HTTPException(status_code=403, detail="Token does not match requested service_id")

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
        # Return dictionary directly for FastAPI
        return {
            "message": "Subscription request accepted",
            "device_id": device_id,
            "request_timestamp": now_utc.isoformat()
        }
    except Exception as e:
        logging.error(f"Kafka error: {e}")
        raise HTTPException(status_code=500, detail="Internal error")
    finally:
        producer.flush()
        producer.close()

# --- Run the FastAPI app ---
if __name__ == "__main__":
    import uvicorn
    # Run the server on host 0.0.0.0 (accessible externally) and port 8000 (or choose another)
    uvicorn.run(app, host="0.0.0.0", port=8000)
