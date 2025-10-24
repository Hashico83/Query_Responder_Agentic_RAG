@echo off
REM Query Responder RAG App - Startup Script for Windows
REM This script starts both the backend and frontend applications

echo 🚀 Starting Query Responder RAG App...

REM Start Backend
echo 📡 Starting Flask backend...
cd backend
python -m venv venv
call venv\Scripts\activate.bat
pip install -r requirements.txt >nul 2>&1
start /B python app.py
cd ..

REM Wait a moment for backend to start
timeout /t 3 /nobreak >nul

REM Start Frontend
echo 🎨 Starting React frontend...
cd frontend
start /B npm run dev
cd ..

echo ✅ Both applications are starting...
echo 📱 Frontend will be available at: http://localhost:5173
echo 🔧 Backend will be available at: http://localhost:5001
echo 🛑 Press Ctrl+C to stop both applications

pause 