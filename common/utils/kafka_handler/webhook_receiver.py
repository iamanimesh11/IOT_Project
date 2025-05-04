import logging
from fastapi import FastAPI, Request, HTTPException
from typing import Dict, Any
import uvicorn

# --- Basic Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- FastAPI App ---
app = FastAPI()

@app.post("/notify")
async def receive_notification(request: Request):
    """
    Receives POST requests with JSON data and logs the payload.
    This endpoint simulates a service receiving a callback notification.
    """
    logging.info("--- Received Callback Notification ---")
    try:
        payload: Dict[str, Any] = await request.json()
        logging.info(f"Callback URL '/notify' received payload: {payload}")
        # --- Add your service-specific logic here ---
        # Example: Update a dashboard, trigger an alert, store data, etc.
        # print(f"Processing notification for device: {payload.get('device_id')}")
        # --------------------------------------------
        return {"status": "Notification received successfully"}
    except Exception as e:
        logging.error(f"Error processing notification payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON payload or processing error")

if __name__ == "__main__":
    logging.info("Starting Callback Receiver Service...")
    # Run on port 8001 to avoid conflict with the subscription service (port 8000)
    uvicorn.run(app, host="0.0.0.0", port=8001)