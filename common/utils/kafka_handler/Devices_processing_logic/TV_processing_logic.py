# --- Add necessary imports ---
import requests # For making HTTP requests to subscribers
import time     # For potential retries/backoff
import logging,requests,os
from typing import Dict, Any, List, Optional # Updated type hints
import redis
# Assume you have a module for database interactions
# import db_handler # e.g., db_handler.get_subscribers(device_id, device_type)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Database/Subscription Cache (Example - Simple Dictionary Cache) ---
# In a real app, use a more robust cache (e.g., Redis) or query DB directly
subscription_cache = {}
CACHE_TTL = 300 # Refresh cache every 5 minutes (adjust as needed)
last_cache_refresh = 0

# --- Redis Configuration ---
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
REDIS_DB = int(os.environ.get("REDIS_DB", 0))
SUBSCRIPTION_CACHE_TTL = int(os.environ.get("SUBSCRIPTION_CACHE_TTL", 300)) # Cache TTL in seconds (default 5 mins)


def get_subscribers_for_device(device_id: str, device_type: str) -> list:
    """
    Finds subscriber endpoints for a given device ID and type.
    Uses a simple time-based cache. Replace with actual DB query logic.
    """
    global last_cache_refresh, subscription_cache

    now = time.time()
    # Check if cache needs refresh
    if not subscription_cache or (now - last_cache_refresh > CACHE_TTL):
        logging.info("Refreshing subscription cache...")
        try:
            # --- Placeholder for actual DB query ---
            # all_subscriptions = db_handler.get_all_active_subscriptions()
            # Simulate fetching all subscriptions
            all_subscriptions = [
                {"service_endpoint": "http://service-a.example.com/events", "device_type": "tv", "device_id": "tv-livingroom-001"},
                {"service_endpoint": "http://service-b.example.com/notify", "device_type": "tv", "device_id": "tv-livingroom-001"},
                {"service_endpoint": "http://service-a.example.com/events", "device_type": "ac", "device_id": "ac-bedroom-005"},
                {"service_endpoint": "http://service-c.example.com/data", "device_type": "tv", "device_id": "tv-kitchen-002"},
            ]
            # --- End Placeholder ---

            # Rebuild cache grouped by (device_type, device_id)
            new_cache = {}
            for sub in all_subscriptions:
                key = (sub['device_type'], sub['device_id'])
                if key not in new_cache:
                    new_cache[key] = []
                new_cache[key].append(sub['service_endpoint'])

            subscription_cache = new_cache
            last_cache_refresh = now
            logging.info(f"Subscription cache refreshed. {len(subscription_cache)} device subscriptions loaded.")

        except Exception as db_error:
            logging.error(f"Failed to refresh subscription cache: {db_error}")
            # Decide: return empty list? raise error? use stale cache?
            # Using stale cache here, but log the error prominently.
            if not subscription_cache: # If cache was never populated, return empty
                 return []

    # Lookup in cache
    lookup_key = (device_type, device_id)
    return subscription_cache.get(lookup_key, []) # Return list of endpoints or empty list

def forward_to_subscriber(endpoint: str, payload: Dict[str, Any]):
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
        logging.error(f"Failed to forward message to {endpoint}: {e}")
        # Implement retry logic here if needed
        return False


def process_tv_data(payload: Dict[str, Any]):
    """Processes telemetry data specifically for TVs."""
    device_id = payload.get('deviceId', 'N/A')
    logging.info(f"Processing TV data for device: {device_id}")
    if "channel" in payload:
        logging.info(f"TV '{device_id}' changed to channel {payload['channel']}")
    # Example: Save to DB
    # db_handler.save_tv_telemetry(payload)
    print(f"--- Pretending to save TV data to DB: {payload} ---") # Placeholder
    
