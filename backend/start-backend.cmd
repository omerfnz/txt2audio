@echo off
title AI Audiobook Studio - Backend
color 0A

echo Activating venv...
call venv\Scripts\activate.bat

echo.
echo Starting Backend Server...
echo.
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

pause
