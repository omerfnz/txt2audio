@echo off
setlocal enabledelayedexpansion

echo ========================================
echo AI Audiobook Studio - Otomatik Kurulum (Windows)
echo ========================================
echo.

:: 1) Sistem bagimliliklari (uyari)
for %%B in (espeak-ng ffmpeg) do (
    where %%B >nul 2>&1
    if errorlevel 1 (
        echo [WARN] %%B bulunamadi. Lutfen winget/choco/brew ile kurun ve PATH'e ekleyin.
    ) else (
        echo [OK] %%B bulundu.
    )
)
echo.

:: 2) Backend kurulumu
echo [2/5] Backend kurulumu...
cd backend
if defined CONDA_PREFIX (
    echo Conda aktif: %CONDA_PREFIX%
) else (
    if not exist "venv\Scripts\activate.bat" (
        echo Venv olusturuluyor...
        python -m venv venv
    )
    echo Venv aktif ediliyor...
    call venv\Scripts\activate
)

echo Pip guncelleniyor...
python -m pip install --upgrade pip setuptools wheel

echo Gerekli paketler yukleniyor...
pip install -r requirements.txt

echo Spacy modeli indiriliyor...
python -m spacy download en_core_web_sm

echo Opsiyonel duzeltmeler...
pip uninstall -y torchcodec >nul 2>&1
pip install ffmpeg-python

if exist "storage\models" (
    echo [INFO] Models klasoru mevcut (XTTS ilk calistirmada indirir veya mevcutsa kullanir).
) else (
    echo [INFO] Models klasoru olusturulacak/ilk calistirmada dolacak.
)

cd ..
echo [OK] Backend tamam.
echo.

:: 3) Frontend kurulumu
echo [3/5] Frontend kurulumu...
cd frontend
call npm install
call npm run build
cd ..
echo [OK] Frontend tamam.
echo.

:: 4) run.cmd olustur
echo [4/5] run.cmd olusturuluyor...
(
echo @echo off
echo setlocal enabledelayedexpansion
echo set ROOT=%%~dp0
echo set BACKEND=%%ROOT%%backend
echo set FRONTEND=%%ROOT%%frontend
echo set VENV=%%BACKEND%%\venv
echo if defined CONDA_PREFIX ^(
echo ^  echo Using conda: %%CONDA_PREFIX%%
echo ^) else ^
echo ^( if exist "%%VENV%%\Scripts\activate.bat" ^( call "%%VENV%%\Scripts\activate.bat" ^&^& echo Using venv: %%VENV%% ^) ^)
echo set TTS_HOME=%%BACKEND%%\storage\models
echo set COQUI_TOS_AGREED=1
echo set TTS_USE_DEEPSPEED=False
echo start "backend" cmd /k "cd /d %%BACKEND%% ^& set TTS_HOME=%%TTS_HOME%% ^& set COQUI_TOS_AGREED=1 ^& set TTS_USE_DEEPSPEED=False ^& uvicorn app.main:app --host 0.0.0.0 --port 8000"
echo start "frontend" cmd /k "cd /d %%FRONTEND%% ^& npm run dev -- --host --port 5173"
echo echo Backend:  http://localhost:8000
echo echo Frontend: http://localhost:5173
) > run.cmd
echo [OK] run.cmd olusturuldu.
echo.

:: 5) Bilgi
echo ========================================
echo Kurulum tamam. Calistirmak icin:
echo   run.cmd
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:5173
echo ========================================
pause
@echo off
setlocal

echo ========================================
echo AI Audiobook Studio - Unified Setup (Windows)
echo ========================================
echo.

:: 1. Check system dependencies
echo [1/4] Checking system dependencies...

:: Check espeak-ng
echo Checking espeak-ng...
where espeak-ng >nul 2>nul
if %errorlevel% neq 0 (
    echo [WARNING] espeak-ng not found in PATH!
    echo Please install: winget install eSpeak-NG.eSpeak-NG
    echo Or download from: https://github.com/espeak-ng/espeak-ng/releases
    echo Add it to your PATH environment variable.
) else (
    echo [OK] espeak-ng found.
)
echo.

:: Check ffmpeg
echo Checking ffmpeg...
where ffmpeg >nul 2>nul
if %errorlevel% neq 0 (
    echo [WARNING] ffmpeg not found in PATH!
    echo ffmpeg is required for audio merging. Please install:
    echo   winget install Gyan.FFmpeg
    echo Or download from: https://ffmpeg.org/download.html
    echo Add it to your PATH environment variable.
    echo.
    echo [WARNING] Audio merging will fail without ffmpeg!
) else (
    echo [OK] ffmpeg found.
)
echo.

:: 2. Backend Setup
echo [2/4] Setting up Backend...
cd backend
if not exist venv (
    echo Creating Python virtual environment...
    python -m venv venv
) else (
    echo Virtual environment already exists, using existing...
)
call venv\Scripts\activate
python -m pip install --upgrade pip setuptools wheel

REM Check if PyTorch is already installed
python -c "import torch; print('PyTorch already installed')" >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing PyTorch with CUDA 12.1...
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
) else (
    echo PyTorch already installed, skipping...
)

REM Check if requirements are installed
python -c "import fastapi; import sqlalchemy; print('Requirements check')" >nul 2>&1
if errorlevel 1 (
    echo Installing requirements...
    pip install -r requirements.txt
) else (
    echo Requirements already installed, checking for updates...
    pip install -r requirements.txt --upgrade --quiet
)

REM Check if Spacy model is installed
python -c "import spacy; spacy.load('en_core_web_sm'); print('Spacy model ready')" >nul 2>&1
if errorlevel 1 (
    echo Downloading Spacy model...
    python -m spacy download en_core_web_sm
) else (
    echo Spacy model already installed...
)

:: Model Check
if exist "storage\models" (
    echo [INFO] Models directory exists.
) else (
    echo [INFO] Models will be downloaded on first run.
)

cd ..
echo [OK] Backend setup complete.
echo.

:: 3. Frontend Setup
echo [3/4] Setting up Frontend...
cd frontend
call npm install
call npm run build
cd ..
echo [OK] Frontend setup complete.
echo.

:: 4. Create Start Script
echo [4/4] Creating start script...
(
echo @echo off
echo set TTS_HOME=%%CD%%\backend\storage\models
echo set COQUI_TOS_AGREED=1
echo set TTS_USE_DEEPSPEED=False
echo start "Backend" cmd /k "cd backend ^& venv\Scripts\activate ^& set TTS_HOME=%%~dp0backend\storage\models ^& set COQUI_TOS_AGREED=1 ^& set TTS_USE_DEEPSPEED=False ^& uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo start "Frontend" cmd /k "cd frontend ^& npm run dev"
echo echo App is starting...
echo echo Backend: http://localhost:8000
echo echo Frontend: http://localhost:5173
) > start_app.cmd

echo ========================================
echo [SUCCESS] Setup Completed!
echo To start the application, run: start_app.cmd
echo ========================================
pause
