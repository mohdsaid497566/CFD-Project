@echo off
REM filepath: /mnt/c/Users/Mohammed/Desktop/Intake-CFD-Project/nx/run_with_bypass.bat
REM This is a Windows batch script that launches MDO.py directly with Python
REM bypassing all WSL display issues

echo Intake CFD Optimization Suite - Direct Launcher
echo ==============================================
echo.

REM Get the directory of the batch file
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

REM First try python command
echo Checking for Python...
python --version >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo Python found, attempting to launch application...
    
    REM Create a simple environment
    set DEMO_MODE=1
    
    REM Run the application with verbose flag to see import issues
    python -v "%SCRIPT_DIR%\MDO.py" > python_output.log 2>&1
    if %ERRORLEVEL% NEQ 0 (
        echo Application failed with error code %ERRORLEVEL%
        echo See python_output.log for details
        echo.
        echo Launching diagnostic tool instead...
        python "%SCRIPT_DIR%\run_direct.py"
    ) else (
        echo Application ran successfully
    )
) else (
    echo Python not found in PATH
    echo Attempting to find Python in default locations...
    
    REM Try common Python installation paths
    if exist "C:\Python310\python.exe" (
        echo Found Python at C:\Python310\python.exe
        "C:\Python310\python.exe" "%SCRIPT_DIR%\MDO.py" > python_output.log 2>&1
    ) else if exist "C:\Program Files\Python310\python.exe" (
        echo Found Python at C:\Program Files\Python310\python.exe
        "C:\Program Files\Python310\python.exe" "%SCRIPT_DIR%\MDO.py" > python_output.log 2>&1
    ) else (
        echo Python not found in common locations
        echo Please install Python from https://www.python.org/downloads/
        echo or launch the diagnostic tool directly
        
        REM Try to run the diagnostic tool with system python anyway
        python "%SCRIPT_DIR%\run_direct.py"
    )
)

echo.
echo If the application did not start correctly, try:
echo 1. Check python_output.log for error messages
echo 2. Run run_direct.py directly with Python
echo 3. Install required dependencies with: pip install -r requirements.txt
echo.
echo Press any key to exit...
pause >nul