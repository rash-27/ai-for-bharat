#!/bin/bash
cd /home/rash-27/projects/hackathon/ai-for-bharat

# Start backend
cd backend
source venv/bin/activate

echo "Starting seed_data.py in background..."
python seed_data.py > seed.log 2>&1 &

echo "Starting CDC worker..."
python cdc_worker.py > cdc.log 2>&1 &

echo "Starting Resolution Engine..."
python resolution_engine.py > res.log 2>&1 &

echo "Starting FastAPI server..."
uvicorn main:app --reload > api.log 2>&1 &

# Start frontend
cd ../frontend
echo "Starting React Frontend..."
npm run dev -- --host > frontend.log 2>&1 &

echo "All services started."
