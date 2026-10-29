#!/usr/bin/env bash
set -e

echo "===================================================="
echo "STARTING EVOLUTIONARY SOFTWARE DNA ENGINE"
echo "===================================================="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "Checking runtime environments..."
python --version || { echo "Python 3 is required."; exit 1; }
node --version || { echo "Node.js is required."; exit 1; }

echo "1. Installing backend dependencies..."
pip install -r "$ROOT_DIR/backend/requirements.txt" --quiet

echo "2. Installing frontend dependencies..."
cd "$ROOT_DIR/frontend"
npm install --quiet

echo "3. Initializing 5-Commit Mock Repository..."
cd "$ROOT_DIR"
python "$ROOT_DIR/backend/run.py" --gen-mock

echo "4. Starting Backend API Server (http://localhost:8000)..."
export PYTHONPATH="$ROOT_DIR/backend:$PYTHONPATH"
python "$ROOT_DIR/backend/run.py" --port 8000 &
BACKEND_PID=$!

echo "5. Starting Frontend Dev Server (http://localhost:5173)..."
cd "$ROOT_DIR/frontend"
npm run dev -- --host 0.0.0.0 &
FRONTEND_PID=$!

echo "===================================================="
echo "Software DNA Quality Engine is Live!"
echo "Backend:  http://localhost:8000"
echo "Docs:     http://localhost:8000/docs"
echo "Frontend: http://localhost:5173"
echo "===================================================="

trap "kill $BACKEND_PID $FRONTEND_PID" EXIT
wait
