# --- Add necessary imports ---
import requests # For making HTTP requests to subscribers
import time     # For potential retries/backoff
import logging,requests,os
from typing import Dict, Any, List, Optional # Updated type hints
import redis
import psycopg2
import json
import sys
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Add project root to sys.path for imports ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# --- Import your actual DB connection utility ---
from common.utils.Database_connection_Utils import connect_to_db # Assuming connect_to_db is defined there


# --- Redis Configuration ---
# Consider loading these from config.ini or environment variables consistently
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
REDIS_DB = int(os.environ.get("REDIS_DB", 0))
SUBSCRIPTION_CACHE_TTL = int(os.environ.get("SUBSCRIPTION_CACHE_TTL", 300)) # Cache TTL in seconds (default 5 mins)
inside_docker = os.environ.get("inside_docker", "False").lower() == "true"
# --- Initialize Redis Client ---
try:
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)
    redis_client.ping() # Check connection
    logging.info(f"Connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
except redis.exceptions.ConnectionError as e:
    logging.error(f"Failed to connect to Redis: {e}")
    redis_client = None # Set to None if connection fails


def get_subscribers_for_device(device_id: str) -> List[str]:
    device_id="7dd73c3d-4f60-44a8-ae8d-80683cb8c760" # Hardcoded for testing
    """
    Finds active subscriber callback URLs for a given device ID.
    Uses Redis for caching database query results.
    """
    cache_key = f"device_subs:{device_id}"
    subscribers = []

    # 1. Check Redis cache first
    if redis_client:
        try:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                subscribers = json.loads(cached_data)
                logging.debug(f"Cache hit for device {device_id}. Found {len(subscribers)} subscribers.")
                return subscribers
        except redis.exceptions.RedisError as e:
            logging.warning(f"Redis cache read error for key {cache_key}: {e}")
        except json.JSONDecodeError as e:
            logging.warning(f"Error decoding cached JSON for key {cache_key}: {e}")

    # 2. If not in cache or Redis error, query the database
    logging.debug(f"Cache miss for device {device_id}. Querying database.")
    conn = None
    try:
        conn = connect_to_db() # Use the imported function
        if not conn:
            logging.error(f"Failed to connect to DB to get subscribers for device {device_id}")
            return [] # Return empty list on connection failure

        with conn.cursor() as cur:
            # Join subscribed_devices with services to get the callback_url
            query = """
                SELECT srv.callback_url
                FROM subscriptions.subscribed_devices sd
                JOIN subscriptions.services srv ON sd.service_id = srv.service_id
                WHERE sd.device_id = %s
                  AND sd.subscription_status = 'active' -- Only notify active subscriptions
                  AND srv.status = 'active';          -- Only notify active services
            """
            cur.execute(query, (device_id,))
            results = cur.fetchall()
            subscribers = [row[0] for row in results if row[0]] # Extract non-null callback URLs
            logging.info(f"Database query found {len(subscribers)} active subscribers for device {device_id}")

            # 3. Store result in Redis Cache
            if redis_client:
                try:
                    redis_client.set(cache_key, json.dumps(subscribers), ex=SUBSCRIPTION_CACHE_TTL)
                    logging.debug(f"Stored query result for device {device_id} in Redis cache.")
                except redis.exceptions.RedisError as e:
                    logging.warning(f"Redis cache write error for key {cache_key}: {e}")

    except (Exception, psycopg2.Error) as db_error:
        logging.error(f"Error querying subscribers for device {device_id}: {db_error}")
        # Return empty list on query error
        return []
    finally:
        if conn:
            conn.close()

    return subscribers

def forward_to_subscriber(endpoint: str, payload: Dict[str, Any]):
    if inside_docker:
        endpoint = endpoint.replace("localhost", "host.docker.internal")
    """Sends the payload to a subscriber endpoint via HTTP POST."""
    try:
        # Consider adding headers like Content-Type and potentially authentication tokens
        headers = {'Content-Type': 'application/json'}
        # You might need API keys or other auth depending on subscriber requirements
        # headers['Authorization'] = f'Bearer {YOUR_SUBSCRIBER_API_KEY}'

        response = requests.post(endpoint, json=payload, headers=headers, timeout=10) # 10 second timeout
        response.raise_for_status() # Raises HTTPError for bad responses (4xx or 5xx)
        logging.info(f"Successfully forwarded message to {endpoint} (Status: {response.status_code})")
        return True
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to forward message to {endpoint} ({type(e).__name__}): {e}")
        # Implement retry logic here if needed
        return False


def process_refrigerator_data(payload: Dict[str, Any]):
    """Processes telemetry data specifically for Refrigerators."""
    device_id = payload.get('device_id', 'N/A') # Correct key based on generator
    logging.info(f"Processing Refrigerator data for device: {device_id}")

    # --- Add specific refrigerator processing logic here ---
    # Example: Check temperature thresholds, door status, etc.
    # if payload.get('temperature') > 5:
    #     logging.warning(f"Refrigerator {device_id} temperature is high: {payload.get('temperature')}°C")
    print(f"--- Pretending to save Refrigerator data to DB: {payload} ---") # Placeholder
