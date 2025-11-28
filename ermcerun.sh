#!/bin/bash
# Path: /erm-ce/ermcerun.sh

# THIS SH FILE IS TO RUN WITH SYSTEMCTL

# Exit if any command fails
set -e

# Change to project directory
cd /erm-ce

# Activate virtual environment
source venv/bin/activate

# Ensure logs directory exists
mkdir -p logs

# Run the Python app (in foreground for systemd)
echo "n" | python3 main.py >> logs/python.log 2>&1

