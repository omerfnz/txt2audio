@echo off
set TTS_HOME=%CD%\backend\storage\models
set COQUI_TOS_AGREED=1
set TTS_USE_DEEPSPEED=False
start "Backend" cmd /k "cd backend ^& venv\Scripts\activate ^& set TTS_HOME=%~dp0backend\storage\models ^& set COQUI_TOS_AGREED=1 ^& set TTS_USE_DEEPSPEED=False ^& uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
start "Frontend" cmd /k "cd frontend ^& npm run dev"
echo App is starting...
echo Backend: http://localhost:8000
echo Frontend: http://localhost:5173
