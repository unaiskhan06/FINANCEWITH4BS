@echo off
cd /d "%~dp0"
REM Configuration is read from the .env file in this folder (see .env.example).
python backend\app.py
pause
