import os
import sys
import logging
import datetime
import json
import redis
import uuid
import jwt as pyjwt
from flask import Flask, request, jsonify,current_app

import psycopg2,configparser
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

redis_client = redis.Redis(host='localhost', port=6379, db=0)


from Database_connection_Utils import connect_to_db


# --- Redis ---

# --- Flask App ---
app = Flask(__name__)

# Secret key for JWT token generation (ensure it's kept secret and secure)
SECRET_KEY = 'your-secret-key'
#app.extensions['redis'] = redis_client #store the raw client.  FlaskRedis does this.


def get_redis():
    """Gets the redis client from the current app."""
    if 'redis' not in current_app.extensions:
        raise RuntimeError("Redis is not initialized. Did you forget to call init_app(app)?")
    return current_app.extensions['redis']
    
def generate_service_id():
    """Generate a unique service_id."""
    return str(uuid.uuid4())

def generate_service_key(service_id):
    """Generate a service_key (JWT token) for the service."""
    utc_now = datetime.datetime.now(datetime.timezone.utc)
    payload = {
        'service_id': service_id,
        'exp': utc_now + datetime.timedelta(hours=24)  # Token expires in 24 hours
    }
    try:
        service_key = pyjwt.encode(payload, SECRET_KEY, algorithm='HS256')
    except Exception as e:
        logging.error(f"Error encoding JWT: {e}")
        return None # IMPORTANT:  Handle the error!

    # Store the service_key in Redis for quick validation (with TTL of 24 hours)
    redis_client.set(service_id, service_key, ex=86400)  # 86400 seconds = 24 hours
    return service_key

def verify_service_key(service_key):
    try:
        payload = pyjwt.decode(service_key, SECRET_KEY, algorithms=['HS256'])
        service_id = payload['service_id']
        stored_token = redis_client.connection.get(f"service:{service_id}")
        if stored_token is None or stored_token.decode() != service_key:
            return None
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
    callback_url = data.get("callback_url")  # Get callback URL

    if not service_name:
        return jsonify({"error": "Missing service_name"}), 400
    if not callback_url:
        return jsonify({"error": "Missing callback_url"}), 400 #add this
    conn = None # Initialize conn

    try:
        conn = connect_to_db()
        cur = conn.cursor()

        # Check if the service already exists
        cur.execute("SELECT service_id FROM subscriptions.services WHERE service_name = %s", (service_name,))
        existing = cur.fetchone()

        if existing:
            return jsonify({"message": "Service already registered", "service_id": existing[0]}), 200

       
        service_id = generate_service_id()
        service_key = generate_service_key(service_id)

        # Store in database
        cur.execute("""
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
