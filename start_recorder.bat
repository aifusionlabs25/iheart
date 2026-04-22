@echo off
REM ==============================================
REM iHeart Recorder — Start Script
REM ==============================================
REM Set your credentials as environment variables before running,
REM or create a .env file (see .env.example).
REM ==============================================

cd /d "%~dp0"
echo Batch script started at %TIME% > batch_run_new.log

REM Load credentials from environment (set these before running)
REM   set IHEART_USERNAME=your_email@domain.com
REM   set IHEART_PASSWORD=yourpassword

REM Execute the GUI with auto-schedule
python iheart_gui.py --auto-schedule >> batch_run_new.log 2>&1

echo Batch script finished at %TIME% >> batch_run_new.log