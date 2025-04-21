#!/bin/sh
set -e

PGHOST="postgres"
PGPORT="5432"
PGUSER="$POSTGRES_USER"
PGPASSWORD="$POSTGRES_PASSWORD"
DEFAULT_DATABASE="postgres"
TARGET_DATABASE="IOT_Project"

echo "Waiting for PostgreSQL to be ready..."
until pg_isready -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$DEFAULT_DATABASE"; do
  sleep 1
done
echo "PostgreSQL is ready."

# Check if the IOT_Project database exists
echo "Checking if database $TARGET_DATABASE exists..."
if PGPASSWORD="$PGPASSWORD" psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -lqt | cut -d\| -f1 | grep -wiq "$TARGET_DATABASE"; then
  echo "Database $TARGET_DATABASE already exists. Skipping creation."
else
  echo "Database $TARGET_DATABASE does not exist. Creating it..."
  PGPASSWORD="$PGPASSWORD" psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$DEFAULT_DATABASE" -c "CREATE DATABASE $TARGET_DATABASE;"
  echo "Database $TARGET_DATABASE created."
fi
