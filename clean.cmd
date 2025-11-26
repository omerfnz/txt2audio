@echo off
setlocal enabledelayedexpansion
color 0C
title AI Audiobook Studio - Clean

echo.
echo ========================================
echo AI Audiobook Studio - Clean All
echo ========================================
echo.
echo WARNING: This will delete all cached packages!
echo.
set /p confirm="Continue? (Y/N): "
if /i not "%confirm%"=="Y" exit /b 1

echo.
echo Cleaning backend...
if exist "backend\venv" (
    rmdir /s /q backend\venv
    echo ✓ Backend venv deleted
)
if exist "backend\.pytest_cache" rmdir /s /q backend\.pytest_cache
if exist "backend\__pycache__" rmdir /s /q backend\__pycache__

echo.
echo Cleaning frontend...
if exist "frontend\node_modules" (
    rmdir /s /q frontend\node_modules
    echo ✓ Frontend node_modules deleted
)
if exist "frontend\dist" rmdir /s /q frontend\dist
if exist "frontend\.vite" rmdir /s /q frontend\.vite

echo.
echo ✅ Clean completed!
echo.
echo To reinstall, run: setup-all.cmd
echo.
pause
