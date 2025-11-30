@echo off
title AI Audiobook Studio - Backend
color 0A

echo Activating venv...
call venv\Scripts\activate.bat

REM Set TTS environment variables
set TTS_HOME=%CD%\storage\models
set COQUI_TOS_AGREED=1

echo.
echo Starting Backend Server...
echo TTS_HOME: %TTS_HOME%
echo.
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

pause
