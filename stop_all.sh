#!/bin/bash
echo "Stopping all Darpan components..."

echo "Stopping seed_data.py..."
pkill -f "python seed_data.py" || echo "Not running."

echo "Stopping CDC worker..."
pkill -f "python cdc_worker.py" || echo "Not running."

echo "Stopping Resolution Engine..."
pkill -f "python resolution_engine.py" || echo "Not running."

echo "Stopping FastAPI server..."
pkill -f "uvicorn main:app" || echo "Not running."

echo "Stopping React Frontend..."
pkill -f "vite --host" || echo "Not running."
pkill -f "npm run dev" || echo "Not running."

echo "All components stopped."
