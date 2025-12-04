@echo off
setlocal enabledelayedexpansion
color 0A
title AI Audiobook Studio - Quick Start

echo.
echo ========================================
echo AI Audiobook Studio - Quick Start
echo ========================================
echo.

REM Check setup
if not exist "backend\venv" (
    echo ERROR: Backend not setup!
    echo Please run: setup-all.cmd
    pause
    exit /b 1
)

if not exist "frontend\node_modules" (
    echo ERROR: Frontend not setup!
    echo Please run: setup-all.cmd
    pause
    exit /b 1
)

echo ✓ Backend ready
echo ✓ Frontend ready
echo.
echo.
echo Building frontend (npm run build)...
cd frontend
call npm run build
cd ..
echo.
echo Starting both servers...
echo.
echo NOTE: Two new windows will open
echo - Backend (Port 8000)
echo - Frontend (Port 5173)
echo.


REM Start Backend in new window
start "Backend - AI Audiobook Studio" cmd /k "cd /d %~dp0backend && venv\Scripts\activate && set TTS_HOME=%~dp0backend\storage\models && set COQUI_TOS_AGREED=1 && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

REM Start Frontend in new window
start "Frontend - AI Audiobook Studio" cmd /k "cd frontend && npm run dev"

REM Open browser
timeout /t 3 /nobreak
start http://localhost:5173

echo.
echo ✅ Both servers started!
echo.
echo Backend:  http://localhost:8000/docs
echo Frontend: http://localhost:5173
echo.
