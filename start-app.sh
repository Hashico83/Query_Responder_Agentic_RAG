#!/bin/bash

# Query Responder RAG App - Startup Script
# This script starts both the backend and frontend applications

echo "🚀 Starting Query Responder RAG App..."

# Function to cleanup background processes on exit
cleanup() {
    echo "🛑 Stopping all processes..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Start Backend
echo "📡 Starting Flask backend..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt > /dev/null 2>&1
python3 app.py &
BACKEND_PID=$!
cd ..

# Wait a moment for backend to start
sleep 3

# Start Frontend
echo "🎨 Starting React frontend..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo "✅ Both applications are starting..."
echo "📱 Frontend will be available at: http://localhost:5173"
echo "🔧 Backend will be available at: http://localhost:5001"
echo "🛑 Press Ctrl+C to stop both applications"

# Wait for both processes
wait 