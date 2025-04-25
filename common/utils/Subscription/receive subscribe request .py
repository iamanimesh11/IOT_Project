import os,sys,json,logging
import configparser
import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Header, Depends
from kafka import KafkaProducer

CONFIG_PATH = r"C:\Users\Acer\PycharmProjects\IOT_Project\common\credentials\config.ini"
config = configparser.ConfigParser()

if not os.path.exists(CONFIG_PATH):
    logging.error(f"config file not found: {CONFIG_PATH}")
    sys.exist(1)
config.read(CONFIG_PATH)

logging.basicConfig(level=logging.INFO,format="%(asctime)s- %(levelname)- %(message)s")

## --kafka config --

try:
    kafka_config=config['kakfa']
    KAFKA_BOOTSTRAP_SERVERS=kafka_config.get('bootstrap_servers','localhost:9092')
    SUBSCRIPTION_TOPIC =kafka_config.get('subscription_topic','subscription_requests')
except KeyError:
    logging.warning(f"kafka config section not found,using defualts")
    KAFKA_BOOTSTRAP_SERVERS = kafka_config.get('bootstrap_servers', 'localhost:9092')
    SUBSCRIPTION_TOPIC = kafka_config.get('subscription_topic', 'subscription_requests')

SUBSCRIPTON_DURATION_SECONDS=3600



@asynccontextmanager
async def lifespan(app:FastAPI):
    try:
        app.state.producer=KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        logging.info("✅ Kafka producer initialized.")

    except Exception as e:
        logging.error("f kafka init failed")
        app.state.producer = None

    yield  # Run the app

    if app.state.producer:
        app.state.producer.flush()
        app.state.producer.close()
        logging.info("🔻 Kafka producer closed.")


app = FastAPI(lifespan=lifespan)

# ---------- AUTH DEPENDENCY ----------
def verify_token(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Missing or invalid Authorization header")

    token = auth_header.split(" ")[1]

    with DB_CONN.cursor() as cur:
        cur.execute("""
            SELECT device_id, expires_at, is_active FROM registered_devices.auth_tokens
            WHERE token = %s
        """, (token,))
        result = cur.fetchone()

        if not result:
            raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Token not found")

        device_id_db, expires_at, is_active = result
        if not is_active or datetime.datetime.utcnow() > expires_at.replace(tzinfo=None):
            raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Token expired or inactive")

        return device_id_db


# ---------- MODELS ----------
class TokenRequest(BaseModel):
    device_id: str
@app.post("/generate-token")
def generate_token(req: TokenRequest):
    token = os.urandom(24).hex()
    issued_at = datetime.datetime.utcnow()
    expires_at = issued_at + datetime.timedelta(hours=1)

    with DB_CONN.cursor() as cur:
        cur.execute("""
            INSERT INTO registered_devices.auth_tokens (token, device_id, issued_at, expires_at, is_active)
            VALUES (%s, %s, %s, %s, TRUE)
        """, (token, req.device_id, issued_at, expires_at))
        DB_CONN.commit()

    return {"token": token, "device_id": req.device_id, "expires_at": expires_at.isoformat()}

@app.post("/event/{device_id}")
def handle_subscription(device_id: str, request: Request, device_id_db: str = Depends(verify_token)):
    if device_id != device_id_db:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Token does not match device_id")

    now_utc = datetime.datetime.now(datetime.timezone.utc)

    subscription_event = {
        "device_id": device_id,
        "event_type": "subscribe",
        "requested_at_iso": now_utc.isoformat(),
        "requested_at_unix": now_utc.timestamp(),
        "subscription_duration_seconds": SUBSCRIPTION_DURATION_SECONDS
    }

    try:
        request.app.state.producer.send(SUBSCRIPTION_TOPIC, value=subscription_event, key=device_id.encode('utf-8'))
        logging.info(f"Published subscription event for {device_id}")
        return JSONResponse(
            status_code=202,
            content={"message": "Subscription request accepted", "device_id": device_id}
        )
    except Exception as e:
        logging.error(f"Kafka error: {e}")
        raise HTTPException(status_code=500, detail="Failed to send to event stream")
