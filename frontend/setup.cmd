@echo off
setlocal enabledelayedexpansion
color 0A
title AI Audiobook Studio - Frontend Setup

echo ========================================
echo AI Audiobook Studio - Frontend Setup
echo ========================================
echo.

REM Adım 1: Node.js kontrol
echo [1/3] Checking Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js not found!
    echo Please install Node.js from: https://nodejs.org/
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('node --version') do set NODE_VERSION=%%i
echo ✓ Node.js !NODE_VERSION! found
echo.

REM Adım 2: npm paketleri kontrol
echo [2/3] Checking npm packages...
if exist node_modules (
    echo ✓ npm packages already installed
) else (
    echo Installing npm packages...
    call npm install --silent
    if errorlevel 1 (
        echo ERROR: Failed to install packages
        pause
        exit /b 1
    )
)
echo.

REM Adım 3: build testi (hata olsa da devam et)
echo [3/3] Testing build...
call npm run build >nul 2>&1
if errorlevel 1 (
    echo ⚠ Build had issues, but frontend can still run with: npm run dev
) else (
    echo ✓ Build successful
)
echo.

echo ========================================
echo ✅ Frontend setup completed!
echo ========================================
echo.
echo To start the frontend:
echo   npm run dev
echo.
echo Frontend will run on: http://localhost:5173
echo.
pause
