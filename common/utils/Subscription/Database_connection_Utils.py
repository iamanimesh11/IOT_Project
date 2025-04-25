import os
import sys
import psycopg2
import configparser
import logging

# Determine the correct base directory dynamically
AIRFLOW_HOME = os.getenv("AIRFLOW_HOME", "/opt/airflow")  # Default to Airflow's path
if AIRFLOW_HOME != "/opt/airflow":
    BASE_DIR = os.path.abspath(os.path.join(AIRFLOW_HOME, ".."))  # Go one level up from /opt/airflow
    print("BASE_DIR:", BASE_DIR)  # ✅ Debugging: Print to verify inside container
    AIRFLOW_HOME = BASE_DIR
    logging.info("below base_Dir")
    logging.info(BASE_DIR)
    
COMMON_PATH = os.path.join(AIRFLOW_HOME, "common", "logging_and_monitoring")
sys.path.append(COMMON_PATH)

common_PATH = os.path.join(AIRFLOW_HOME, "common","logging_and_monitoring","logs") 
sys.path.append(common_PATH)


# from centralized_logging import setup_logger



import os

current_path = os.getcwd()
parent_directory = os.path.dirname(current_path)  # Get the parent directory)
print(parent_directory)
one_level_up = os.path.abspath(os.path.join(parent_directory,"credentials","config.ini"))
print(one_level_up)
# Load the config file
config = configparser.ConfigParser()
config.read(r"C:\Users\Acer\PycharmProjects\IOT_Project\common\credentials\config.ini")

import psycopg2
import configparser


db_config = config['database']
host = db_config['host']
username = db_config['user']
password = db_config['password']
port = db_config['port']
database_name = db_config['database']


def connect_to_db():
    """Connects to the PostgreSQL database and returns the connection object."""
    conn = None
    try:
        conn = psycopg2.connect(
            dbname=database_name,
            user=username,
            password=password,
            host="localhost",
            port=port
        )
        conn.autocommit = True
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        if result[0] != 1:
            print("Warning: Test query failed.")
        print("Successfully connected to PostgreSQL database.")
        return conn
    except psycopg2.Error as e:
        print(f"Database connection failed: {e}")
        if conn:
            conn.close()
        return None


def create_schema(cursor, conn, dbname, schema_name):
    try:
        cursor.execute(f"CREATE SCHEMA {schema_name};")
        print(f"Schema {schema_name} created in {dbname}.")
    except psycopg2.errors.DuplicateSchema:
        print(f"Schema {schema_name} already exists in {dbname}.")
    except Exception as e:
        print(f"Failed to create schema {schema_name} in {dbname}: {e}")
        conn.rollback()  # Rollback so the transaction is usable again


def create_table(cursor,conn,schema_name,table_name,create_query):
    try:
        cursor.execute(create_query)
        print(f"Table {table_name} created in {schema_name}.")
    except psycopg2.errors.DuplicateSchema:
        print(f"Table {table_name} already exists in {schema_name}.")
    except Exception as e:
        print(f"Failed to create table {table_name} in {schema_name}: {e}")
        conn.rollback()  # Rollback so the transaction is usable again


def connect_and_create_schemas():
    conn = None
    try:
        conn = psycopg2.connect(
            dbname=database_name,
            user=username,
            password=password,
            host="localhost",
            port=port
        )
        conn.autocommit = True

        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        if result[0] != 1:
            print("Warning: Test query failed.")
        print("Successfully connected to PostgreSQL database.")

        create_schema(cursor, conn, database_name, "registered_devices")
        create_schema(cursor, conn, database_name, "customers")
        create_schema(cursor, conn, database_name, "subscriptions")

        create_query = f"""
                   CREATE TABLE IF NOT EXISTS registered_devices.device_staging (
                       device_id VARCHAR(255) PRIMARY KEY,
                       device_type VARCHAR(50) NOT NULL,
                       model_name VARCHAR(255) NOT NULL,
                       alias VARCHAR(255),
                       reportable BOOLEAN DEFAULT TRUE,
                       created_at TIMESTAMP DEFAULT now()
                   );
               """
        create_table(cursor,conn,"registered_devices","device_staging",create_query)
        create_query = f"""
                           CREATE TABLE IF NOT EXISTS customers.customer_staging (
                               customer_id SERIAL PRIMARY KEY,
                                full_name VARCHAR(100),
                                email VARCHAR(100),
                                phone VARCHAR(50),
                                address TEXT,
                                device_id VARCHAR(255) REFERENCES registered_devices.device_staging(device_id) UNIQUE,
                                device_type VARCHAR(50) NOT NULL,
                                model_name VARCHAR(255) NOT NULL,
                                created_at TIMESTAMP DEFAULT now()
                                
                           );
                       """
        create_table(cursor, conn, "customers", "customer_staging", create_query)
        create_query = f"""
                                 CREATE TABLE subscriptions.subscribed_devices (
                                    id SERIAL PRIMARY KEY,
                                    device_id VARCHAR(255) NOT NULL,
                                    subscribed_at TIMESTAMP DEFAULT NOW(),
                                    expires_at TIMESTAMP NOT NULL,
                                    subscription_status VARCHAR(20) DEFAULT 'active' -- or 'expired', 'failed'
                                  );
                              """
        create_table(cursor, conn, "subscriptions", "subscribed_devices", create_query)
        create_query = f"""
                              CREATE TABLE registered_devices.auth_tokens (
                                    token TEXT PRIMARY KEY,
                                    device_id TEXT NOT NULL,
                                    issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                    expires_at TIMESTAMP NOT NULL,
                                    is_active BOOLEAN DEFAULT TRUE
                              );

                    """
        create_table(cursor, conn, "registered_devices", "auth_tokens", create_query)
        create_query = f"""
                                    CREATE TABLE subscriptions.services (
                                        service_id UUID PRIMARY KEY ,
                                        service_name VARCHAR(100) NOT NULL UNIQUE,
                                        service_key TEXT NOT NULL,
                                        callback_url TEXT NOT NULL,
                                        status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'paused', 'disabled')),
                                        registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                                    );
                               """
        create_table(cursor, conn, "subscriptions", "services", create_query)
        # CREATE INDEX idx_subscriptions_expiry ON subscriptions(expires_at);
        # CREATE INDEX idx_subscriptions_service_device ON subscriptions (service_id, device_id);


        conn.commit()  # Commit the schema creation
        print("Schema&tables creation complete.")
        return conn
    except psycopg2.Error as e:
        print(f"Database operation failed: {e}")
        if conn:
            conn.rollback()  # Rollback any pending changes
        return False

if __name__ == "__main__":
    connect_and_create_schemas()