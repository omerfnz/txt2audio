@echo off
setlocal enabledelayedexpansion
color 0A
title AI Audiobook Studio - Backend Setup

echo ========================================
echo AI Audiobook Studio - Backend Setup
echo ========================================
echo.

REM Adım 1: venv kontrol - yoksa oluştur
echo [1/7] Checking Python virtual environment...
if exist venv (
    echo ✓ venv already exists
    echo.
) else (
    echo Creating Python virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create venv
        pause
        exit /b 1
    )
    echo ✓ venv created
    echo.
)

REM Adım 2: venv aktifleştir
echo [2/7] Activating venv...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate venv
    pause
    exit /b 1
)
echo ✓ venv activated
echo.

REM Adım 3: pip güncelle
echo [3/7] Upgrading pip...
python -m pip install --upgrade pip setuptools wheel >nul 2>&1
if errorlevel 1 (
    echo WARNING: pip upgrade had issues, continuing...
)
echo ✓ pip upgraded
echo.

REM Adım 4: PyTorch kontrol
echo [4/7] Checking PyTorch...
python -c "import torch; print('✓ PyTorch already installed')" >nul 2>&1
if errorlevel 1 (
    echo Installing PyTorch...
    python install_pytorch.py
    if errorlevel 1 (
        echo Trying manual GPU installation...
        pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121 --no-cache-dir
    )
) else (
    echo ✓ PyTorch already installed
)
echo.

REM Adım 5: requirements kontrol
echo [5/7] Checking requirements...
python -c "import fastapi; import sqlalchemy; import f5_tts; print('✓ Requirements already installed')" >nul 2>&1
if errorlevel 1 (
    echo Installing requirements...
    pip install -r requirements.txt --quiet
    if errorlevel 1 (
        echo ERROR: Failed to install requirements
        pause
        exit /b 1
    )
) else (
    echo ✓ Requirements already installed
)
echo.

REM Adım 6: Spacy model kontrol
echo [6/7] Checking Spacy model...
python -c "import spacy; spacy.load('en_core_web_sm'); print('✓ Spacy model ready')" >nul 2>&1
if errorlevel 1 (
    echo Downloading Spacy model...
    python -m spacy download en_core_web_sm
)
echo.

REM Adım 7: espeak-ng kontrol
echo [7/8] Checking espeak-ng...
where espeak-ng >nul 2>&1
if errorlevel 1 (
    echo WARNING: espeak-ng not found!
    echo Please install: winget install eSpeak-NG.eSpeak-NG
    echo Or download from: http://espeak.sourceforge.net/
) else (
    echo ✓ espeak-ng found
)
echo.

REM Adım 8: ffmpeg kontrol
echo [8/8] Checking ffmpeg...
where ffmpeg >nul 2>&1
if errorlevel 1 (
    echo WARNING: ffmpeg not found!
    echo ffmpeg is required for audio merging. Please install:
    echo   winget install Gyan.FFmpeg
    echo Or download from: https://ffmpeg.org/download.html
    echo.
    echo WARNING: Audio merging will fail without ffmpeg!
) else (
    echo ✓ ffmpeg found
)
echo.

echo ========================================
echo ✅ Backend setup completed!
echo ========================================
echo.
echo To start the backend:
echo   venv\Scripts\activate
echo   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
echo.
pause
