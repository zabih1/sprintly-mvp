@echo off
REM Windows batch script to start the FastAPI server
REM Supports large file uploads up to 2GB

echo Starting Sprintly MVP Backend Server...
echo Configuration: Max upload size = 2GB
echo.

cd /d "%~dp0"
python run_server.py

pause

