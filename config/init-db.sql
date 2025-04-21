-- Switch to the default database (usually 'postgres') if not already connected.
\c postgres;
\echo 'Attempting to create database IOT_Project...'
CREATE DATABASE IOT_Project;
\echo 'Database IOT_Project created successfully.'

-- Connect to the IOT_Project database
\c IOT_Project;
\echo 'Connected to database IOT_Project.'

-- Create the Registered_Devices schema
\echo 'Attempting to create schema Registered_Devices...'
CREATE SCHEMA Registered_Devices;
\echo 'Schema Registered_Devices created successfully.'

-- Create the subscribed_devices schema
\echo 'Attempting to create schema subscribed_devices...'
CREATE SCHEMA subscribed_devices;
\echo 'Schema subscribed_devices created successfully.'

-- You can add more initialization scripts here, like creating tables, users, etc.