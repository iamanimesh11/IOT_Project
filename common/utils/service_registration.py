import os
import sys
import logging
import datetime
import json
import redis
import uuid
import jwt
from flask import Flask, request, jsonify
import psycopg2,configparser

# --- Load Confiiig  ---
CONFIG_PATH = r"C:\Users\Acer\PycharmProjects\IOT_Project\common\credentials\config.ini"
config = configparser.ConfigParser()
if not os.path.exists(CONFIG_PATH):
    logging.error(f"Config file not found at: {CONFIG_PATH}")
    sys.exit(1)
config.read(CONFIG_PATH)

# --- Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

from Database_connection_Utils import connect_to_db
conn = connect_to_db()




# --- Redis ---

# --- Flask App ---
app = Flask(__name__)

# Secret key for JWT token generation (ensure it's kept secret and secure)
SECRET_KEY = 'your-secret-key'


# --- PostgreSQL Connection ---

    
def generate_service_id():
    """Generate a unique service_id."""
    return str(uuid.uuid4())

def generate_service_key(service_id):
    """Generate a service_key (JWT token) for the service."""
    payload = {
        'service_id': service_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)  # Token expires in 24 hours
    }
    service_key = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    # Store the service_key in Redis for quick validation (with TTL of 24 hours)
    r.set(service_id, service_key, ex=86400)  # 86400 seconds = 24 hours
    return service_key

def verify_service_key(service_key):
    """Verify the service_key from the Authorization header."""
    try:
        payload = jwt.decode(service_key, SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

@app.route("/register", methods=["POST"])
def register():
    # Generate a unique service_id
    data = request.get_json()
    service_name = data.get("service_name")

    if not service_name:
        return jsonify({"error": "Missing service_name"}), 400

    try:
        cur = conn.cursor()

        # Check if the service already exists
        cur.execute("SELECT service_id FROM subscriptions.services WHERE service_name = %s", (service_name,))
        existing = cur.fetchone()

        if existing:
            return jsonify({"message": "Service already registered", "service_id": existing[0]}), 200

       
        service_id = generate_service_id()
        service_key = generate_service_key(service_id)

        # Store in database
        cursor.execute("""
                INSERT INTO subscriptions.services (service_id, service_name, service_key, callback_url)
                VALUES (%s, %s, %s, %s)
            """, (service_id, service_name, service_key, callback_url))
        conn.commit()

        logging.info(f"Service registered with service_id: {service_id}")
        
        return jsonify({
                "message": "Registration successful",
                "service_id": service_id,
                "service_key": service_key
            }), 201
        
    except Exception as e:
        logging.error(f"Registration failed: {e}")
        return jsonify({"error": "Internal server error"}), 500
    finally:
        if conn:
            conn.close()



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
