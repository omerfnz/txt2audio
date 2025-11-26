@echo off
echo ============================================
echo AI Audiobook Studio - System Check
echo ============================================
echo.

REM Python Version
echo [1/6] Checking Python...
python --version
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python not found!
    pause
    exit /b 1
)

REM Virtual Environment
echo.
echo [2/6] Checking Virtual Environment...
if exist "backend\venv\Scripts\python.exe" (
    echo OK: Virtual environment exists
) else (
    echo ERROR: Virtual environment not found!
    echo Run: setup-all.cmd
    pause
    exit /b 1
)

REM Node.js
echo.
echo [3/6] Checking Node.js...
node --version
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Node.js not found!
    pause
    exit /b 1
)

REM espeak-ng
echo.
echo [4/6] Checking espeak-ng...
where espeak-ng
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: espeak-ng not in PATH
    echo Install with: winget install eSpeak-NG.eSpeak-NG
) else (
    echo OK: espeak-ng found
)

REM PyTorch CUDA
echo.
echo [5/6] Checking PyTorch CUDA...
backend\venv\Scripts\python -c "import torch; print('CUDA Available:', torch.cuda.is_available()); print('Device:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')"

REM TTS Version
echo.
echo [6/6] Checking Coqui TTS...
backend\venv\Scripts\python -c "from TTS import __version__; print('TTS Version:', __version__)"

echo.
echo ============================================
echo System check complete!
echo ============================================
pause
