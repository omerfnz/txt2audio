@echo off
setlocal enabledelayedexpansion
color 0A
title AI Audiobook Studio - Complete Setup

echo.
echo ========================================
echo AI Audiobook Studio - Complete Setup
echo ========================================
echo.

REM Check if already setup
if exist "backend\venv" (
    if exist "frontend\node_modules" (
        echo ✓ Already installed! Skipping setup...
        echo.
        goto :skip_setup
    )
)

REM Backend setup
echo.
echo ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
echo ░ BACKEND SETUP
echo ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
cd backend
call setup.cmd
if errorlevel 1 (
    echo ERROR: Backend setup failed
    pause
    exit /b 1
)
cd ..
echo.

REM Frontend setup
echo.
echo ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
echo ░ FRONTEND SETUP
echo ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
cd frontend
call setup.cmd
if errorlevel 1 (
    echo ERROR: Frontend setup failed
    pause
    exit /b 1
)
cd ..
echo.

REM Check espeak-ng
echo.
echo ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
echo ░ CHECKING DEPENDENCIES
echo ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
echo.
where espeak-ng >nul 2>&1
if errorlevel 1 (
    echo ⚠ espeak-ng not found in PATH
    echo Installing espeak-ng with winget...
    winget install eSpeak-NG.eSpeak-NG --silent --accept-source-agreements --accept-package-agreements
    if errorlevel 1 (
        echo.
        echo ⚠ Auto-install failed. Please install manually:
        echo   winget install eSpeak-NG.eSpeak-NG
        echo.
    ) else (
        echo ✓ espeak-ng installed successfully
    )
) else (
    echo ✓ espeak-ng found
)
echo.

:skip_setup

echo ========================================
echo ✅ COMPLETE SETUP FINISHED!
echo ========================================
echo.
echo NEXT STEPS:
echo.
echo 1. Backend (Terminal 1):
echo    cd backend
echo    venv\Scripts\activate
echo    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
echo.
echo 2. Frontend (Terminal 2):
echo    cd frontend
echo    npm run dev
echo.
echo 3. Open browser:
echo    http://localhost:5173
echo.
pause
