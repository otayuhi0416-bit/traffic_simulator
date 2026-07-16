@echo off
title SUMO Junction Patch Editor Launcher
echo =================================================================
echo  SUMO Junction Patch Editor - Starting Launcher...
echo =================================================================
echo.

cd /d "%~dp0"

:: Flask のインストールチェック
python -c "import flask" 2>nul
if %errorlevel% neq 0 (
    echo [INFO] Flask is not installed. Installing flask...
    pip install flask
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install Flask. Please check python/pip configuration.
        pause
        exit /b 1
    )
)

:: sumolib のインストールチェック
python -c "import sumolib" 2>nul
if %errorlevel% neq 0 (
    echo [INFO] sumolib is not installed. Installing sumolib...
    pip install sumolib
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install sumolib.
        pause
        exit /b 1
    )
)

echo [INFO] Starting Web Server on http://localhost:5000...
start http://localhost:5000
python app.py
pause
