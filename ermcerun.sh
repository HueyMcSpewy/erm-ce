#!/bin/bash
# Path: /erm-ce/ermcerun.sh

# Exit if any command fails
set -e

# Ensure virtual environment exists
if [ ! -f /erm-ce/venv/bin/activate ]; then
    cd /erm-ce/
    python3 -m venv venv
fi

# Ensure MongoDB container is running
if ! docker ps --filter "name=mongo" --filter "status=running" | grep -q mongodb; then
    echo "MongoDB container is not running. Please start it first."
    exit 1
fi

# Activate virtual environment
source /erm-ce/venv/bin/activate

# Ensure logs directory exists
mkdir -p /erm-ce/logs

# Run the Python app (in foreground for systemd)
echo "n" | python3 /erm-ce/main.py >> /erm-ce/logs/python.log 2>&1
