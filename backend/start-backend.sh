#!/bin/bash

echo "Activating venv..."
source venv/bin/activate

echo ""
echo "Starting Backend Server..."
echo ""
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
