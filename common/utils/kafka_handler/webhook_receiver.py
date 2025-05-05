import logging
from fastapi import FastAPI, Request, HTTPException
from typing import Dict, Any
import httpx  # Using httpx for async requests
import os
import uvicorn

# --- Basic Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Configuration ---
MOCK_CRM_URL = os.environ.get("MOCK_CRM_URL", "http://localhost:8002/log_event")
HTTP_CLIENT_TIMEOUT = 10 # Timeout for calling the CRM

# --- FastAPI App ---
app = FastAPI()

@app.post("/notify")
async def receive_notification(request: Request):
    """
    Receives POST requests with JSON data and logs the payload.
    This endpoint simulates a service receiving a callback notification.
    It then forwards the payload to the Mock CRM.
    """
    logging.info("--- Received Callback Notification ---")
    try:
        # Log raw body first for debugging
        raw_body = await request.body()
        logging.debug(f"Raw request body: {raw_body}") # Check terminal logs for this output
        payload: Dict[str, Any] = await request.json()
        # If parsing succeeds, log the parsed payload
        logging.info(f"Callback URL '/notify' received payload: {payload}")

        # --- Forward directly to Mock CRM ---
        async with httpx.AsyncClient(timeout=HTTP_CLIENT_TIMEOUT) as client:
            try:
                response = await client.post(MOCK_CRM_URL, json=payload)
                response.raise_for_status() # Check for HTTP errors
                logging.info(f"Successfully forwarded to Mock CRM (Status: {response.status_code}) - CRM Response: {response.json()}")
            except httpx.RequestError as e:
                logging.error(f"Failed to forward payload to Mock CRM ({type(e).__name__}): {e}")
                # Optionally raise an HTTPException here if forwarding failure is critical

        return {"status": "Notification received successfully"}
    except Exception as e:
        logging.error(f"Error processing notification payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON payload or processing error")

if __name__ == "__main__":
    logging.info("Starting Callback Receiver Service...")
    # Run on port 8001 to avoid conflict with the subscription service (port 8000)
    uvicorn.run(app, host="0.0.0.0", port=8001)