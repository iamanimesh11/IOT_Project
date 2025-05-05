import logging,os
from fastapi import FastAPI, Request, HTTPException
import uvicorn
from fastapi.responses import HTMLResponse # Keep for potential direct HTML responses if needed elsewhere
from fastapi.templating import Jinja2Templates # Import Jinja2Templates
import psycopg2.extras # Import the extras module for DictCursor
from fastapi.responses import RedirectResponse # Import RedirectResponse
from typing import Dict, Any, List, Optional # Import Optional for query param

# Initialize Jinja2Templates with the directory containing your HTML templates

# --- Determine the absolute path to the templates directory ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(SCRIPT_DIR, "templates")

templates = Jinja2Templates(directory=TEMPLATE_DIR)
from typing import Dict, Any, List # Import List for type hinting
import sys
import psycopg2
# --- Basic Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# --- Add project root to sys.path for DB utility import ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from common.utils.Database_connection_Utils import connect_to_db

# --- In-Memory CRM State (using a lock for basic thread safety) ---
def insert_into_db(payload):
        device_id = payload.get("device_id")
        device_type = payload.get("device_type")
        error_code = payload.get("error_code")
        event_timestamp = payload.get("timestamp") # Assuming 'timestamp' field exists
        # Determine request state based on error code
        # --- Log to Database ---
        # Only log if device_id is present (or adjust logic as needed)
        if device_id:
            conn = None
            owner_name = "N/A"
            owner_contact = "N/A"
            try:
                conn = connect_to_db()
                if conn:
                    with conn.cursor() as cur:
                        # 1. Get Owner Details (only if needed, e.g., for pending state)
                        owner_query = """
                                SELECT c.full_name, c.email
                                FROM  customers.customer_staging c 
                                WHERE c.device_id = %s;
                            """
                        cur.execute(owner_query, (device_id,))
                        owner_result = cur.fetchone()
                        logging.info(f"Owner query result: {owner_result}")
                        if owner_result:
                                owner_name, owner_contact = owner_result

                        # 2. Insert into CRM event log table including the state
                        # Ensure the schema name 'crm' is correct here
                        insert_query = """
                            INSERT INTO customers.error_events
                                (device_id, device_type, error_code, event_timestamp, owner_name, owner_contact, request_state)
                            VALUES (%s, %s, %s, %s, %s, %s, %s);
                        """
                        cur.execute(insert_query, (device_id, device_type, error_code, event_timestamp, owner_name, owner_contact, "pending"))
                        conn.commit()
                        logging.info(f"Logged event for device {device_id} with state  to CRM database.")
            except (Exception, psycopg2.Error) as db_error:
                logging.error(f"CRM Database Error logging event for device {device_id}: {db_error}")
                if conn: conn.rollback() # Rollback on error
            finally:
                if conn: conn.close()
        
        return {"status": "Event logged in CRM successfully"}

# --- FastAPI App ---
app = FastAPI()
# --- Basic HTML UI ---
def _fetch_dashboard_data(state_filter: Optional[str] = None) -> (Dict[str, int], List[Dict[str, Any]]):
    """
    Fetches counters and recent error events from the database. (Synchronous)

    Args:
        state_filter: Optional string to filter events by request_state ('pending' or 'solved').
    """
    # Removed payload processing and insertion from GET endpoint
    # Read the current state safely
    counters = {
            "total_requests": 0,
            "pending_requests": 0,
            "solved_requests": 0
        }
    error_events: List[Dict[str, Any]] = [] # Initialize as empty list
    conn = None
    try:    
        conn = connect_to_db()
        if conn:
                with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur: # Use DictCursor
                    # Fetch counts (using correct schema 'crm')
                    cur.execute("SELECT COUNT(*) FROM customers.error_events")
                    counters["total_requests"] = cur.fetchone()[0]
                    cur.execute("SELECT COUNT(*) FROM customers.error_events WHERE request_state = 'pending'")
                    counters["pending_requests"] = cur.fetchone()[0]
                    cur.execute("SELECT COUNT(*) FROM customers.error_events WHERE request_state = 'solved'")
                    counters["solved_requests"] = cur.fetchone()[0]
                    
                    # Build query for recent events with optional filtering
                    query_params = []
                    events_query = """
                        SELECT event_id, received_timestamp, device_id, device_type, error_code, request_state, owner_name, owner_contact
                        FROM customers.error_events
                    """
                    if state_filter in ('pending', 'solved'):
                        events_query += " WHERE request_state = %s"
                        query_params.append(state_filter)

                    events_query += " ORDER BY received_timestamp DESC LIMIT 20"
                    cur.execute(events_query, query_params)
                    error_events = [dict(row) for row in cur.fetchall()]
                    logging.info(f"Fetched {len(error_events)} recent error events from the database.")
        else:
             logging.warning("UI: Database connection failed.")
    except (Exception, psycopg2.Error) as e:
            logging.error(f"Error fetching data for UI: {e}")
    finally:
        if conn:
            conn.close()
    return counters, error_events
    
# --- Basic HTML UI Endpoint ---
@app.get("/", response_class=HTMLResponse, name="get_crm_dashboard") # Explicitly set the route name
async def get_crm_dashboard(request: Request, state: Optional[str] = None):
    """
    Serves a simple HTML page displaying the current CRM state by fetching data.
    Optionally filters events based on the 'state' query parameter.
    """
    # Validate state filter
    valid_states = ['pending', 'solved', 'all']
    current_filter = state if state in valid_states else 'all'

    # Fetch data using the helper function, passing the filter
    counters, error_events = _fetch_dashboard_data(state_filter=current_filter if current_filter != 'all' else None) # Call renamed sync function

    # Render the template
    try:
        return templates.TemplateResponse("crm_dashboard.html", {
            "request": request,
            "counters": counters,
            "error_events": error_events,
            "current_filter": current_filter
        })
    except Exception as e:
        logging.error(f"Error rendering template 'crm_dashboard.html': {e}")
        raise HTTPException(status_code=500, detail="Error rendering dashboard page.")

    
# --- Endpoint to Mark an Event as Solved ---
@app.post("/solve_event/{event_id}")
async def solve_event(event_id: int):
    """
    Updates the request_state of a specific event to 'solved'.
    """
    logging.info(f"Received request to mark event {event_id} as solved.")
    conn = None
    try:
        conn = connect_to_db()
        if conn:
            with conn.cursor() as cur:
                update_query = "UPDATE customers.error_events SET request_state = 'solved' WHERE event_id = %s AND request_state = 'pending';"
                cur.execute(update_query, (event_id,))
                conn.commit()
                if cur.rowcount > 0:
                    logging.info(f"Successfully marked event {event_id} as solved.")
                else:
                    logging.warning(f"Event {event_id} not found or already solved.")
        else:
            logging.error(f"Failed to connect to DB to solve event {event_id}.")
            raise HTTPException(status_code=500, detail="Database connection failed")
    except (Exception, psycopg2.Error) as db_error:
        logging.error(f"Database error updating event {event_id}: {db_error}")
        if conn: conn.rollback()
        raise HTTPException(status_code=500, detail="Database update failed")
    finally:
        if conn: conn.close()

    # Redirect back to the dashboard after processing
    return RedirectResponse(url="/", status_code=303) # Use 303 See Other for POST-redirect
    
    
        
@app.post("/log_event")
async def log_event_in_crm(request: Request):
    """
    Receives event data from the webhook receiver and updates CRM counters.
    """
    logging.info("--- Mock CRM Received Event ---")
    try:
        payload: Dict[str, Any] = await request.json()
        logging.info(f"CRM received payload: {payload}")

        # Call the insertion logic here
        return insert_into_db(payload)
    except Exception as e:
        logging.error(f"Error processing event in CRM: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error processing event: {e}") # Use 500 for internal errors

if __name__ == "__main__":
    logging.info("Starting Mock CRM Service...")
    # Run on a different port, e.g., 8002
    uvicorn.run(app, host="0.0.0.0", port=8002)