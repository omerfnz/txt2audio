@echo off
setlocal enabledelayedexpansion
set ROOT=%~dp0
set BACKEND=%ROOT%backend
set FRONTEND=%ROOT%frontend
set VENV=%BACKEND%\venv

rem Kullanılacak Python ortamı
if defined CONDA_PREFIX (
  echo Using conda: %CONDA_PREFIX%
) else (
  if exist "%VENV%\Scripts\activate.bat" (
    call "%VENV%\Scripts\activate.bat"
    echo Using venv: %VENV%
  ) else (
    echo No conda/venv detected; using system Python.
  )
)

set TTS_HOME=%BACKEND%\storage\models
set COQUI_TOS_AGREED=1
set TTS_USE_DEEPSPEED=False

echo Starting backend on 0.0.0.0:8000 ...
start "backend" cmd /k "cd /d %BACKEND% && set TTS_HOME=%TTS_HOME% && set COQUI_TOS_AGREED=1 && set TTS_USE_DEEPSPEED=False && uvicorn app.main:app --host 0.0.0.0 --port 8000"

echo Starting frontend on 0.0.0.0:5173 ...
start "frontend" cmd /k "cd /d %FRONTEND% && npm run dev -- --host --port 5173"

echo Backend:  http://localhost:8000
echo Frontend: http://localhost:5173
