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
if exist venv rmdir /s /q venv
python -m venv venv
call venv\Scripts\activate
python -m pip install --upgrade pip setuptools wheel

echo Installing PyTorch (CUDA 12.1 Enabled)...
:: Windows'ta da varsayılan olarak GPU versiyonunu deniyoruz
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

pip install -r requirements.txt
python -m spacy download en_core_web_sm

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
echo start "Backend" cmd /k "cd backend ^& venv\Scripts\activate ^& uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
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
