#!/bin/sh

FLAG_PATH="/shared/info_collected.flag"
TIMEOUT=300 # Total timeout in seconds
SLEEP_INTERVAL=2
WAITED=0

echo "⏳ Waiting for user input in Streamlit (timeout: ${TIMEOUT}s)..."

while [ ! -f "$FLAG_PATH" ]; do
  sleep $SLEEP_INTERVAL
  WAITED=$((WAITED + SLEEP_INTERVAL))

  if [ $WAITED -ge $TIMEOUT ]; then
    echo "❌ Timeout reached: No Input found in ${TIMEOUT}s"
    exit 1
  fi
done

echo "✅ Flag detected! Proceeding..."

