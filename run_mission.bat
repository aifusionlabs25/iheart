@echo off
REM ==============================================
REM iHeart Recorder — Direct Mission Runner
REM ==============================================
REM Usage: run_mission.bat [duration_seconds] [device_index]
REM Defaults: 4 hours (14400s), auto-detect device
REM ==============================================

cd /d "%~dp0"

echo ================================================== >> mission.log
echo Mission Started at %DATE% %TIME% >> mission.log
echo ================================================== >> mission.log

REM Execute the mission (uses defaults if no args provided)
python run_mission.py --duration 14400 >> mission.log 2>&1

echo ================================================== >> mission.log
echo Mission Finished at %DATE% %TIME% >> mission.log
echo ================================================== >> mission.log
