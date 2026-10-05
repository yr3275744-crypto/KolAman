@echo off
rem Starts the alert simulator (same as: python simulator.py). Stop with Ctrl+C.
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel% equ 0 (
    py -3 simulator.py
) else (
    where python >nul 2>nul
    if errorlevel 1 (
        echo Python was not found. Install Python 3 from python.org and try again.
        pause
    ) else (
        python simulator.py
    )
)
