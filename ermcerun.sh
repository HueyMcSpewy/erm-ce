#!/bin/bash
# Path: /erm-ce/ermcerun.sh

# Activate Python virtual environment
source /erm-ce/venv/bin/activate

# Make sure log directory exists
mkdir -p /erm-ce/logs

# Run Python script in background with logging
echo "n" | python3 /erm-ce/main.py >> /erm-ce/logs/python.log 2>&1 &

# Go to Vite website directory and run dev server with logging
cd /erm-ce-website
npm run dev >> /erm-ce/logs/vite.log 2>&1

