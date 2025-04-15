@echo off
rem filepath: /mnt/c/Users/Mohammed/Desktop/Intake-CFD-Project/nx/run_windows.bat
rem This script runs the Intake CFD application directly in Windows

echo Intake CFD Optimization Suite - Windows Launcher
echo ================================================
echo.

rem Check if Python is installed
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Python not found! Please install Python from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

rem Get the directory where this script is located
set SCRIPT_DIR=%~dp0

echo Running from directory: %SCRIPT_DIR%
cd /d %SCRIPT_DIR%

echo Launching launcher script...
python run_direct.py
if %ERRORLEVEL% NEQ 0 (
    echo Failed to launch the application.
    echo Please check that Python and all dependencies are installed.
    pause
    exit /b 1
)

exit /b 0