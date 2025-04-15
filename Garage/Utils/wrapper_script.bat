@echo off
REM Wrapper Script for NX Commands Using run_journal.exe

REM --- Configuration ---
SET SCRIPT_DIR=C:\Users\Mohammed\Desktop\Intake-CFD-Project\nx
SET UGRAF_EXEC=C:\Program Files\Siemens\NX2406\NXBIN\run_journal.exe
SET SCRIPT_1=%SCRIPT_DIR%\nx_express2.py
SET SCRIPT_2=%SCRIPT_DIR%\nx_export.py
SET PART_FILE=%SCRIPT_DIR%\INTAKE3D.prt

REM --- Validate Files ---
echo Debug: Validating required files...
IF NOT EXIST "%UGRAF_EXEC%" (
    echo ERROR: run_journal.exe not found: %UGRAF_EXEC%
    exit /b 1
)
echo Debug: run_journal.exe found: %UGRAF_EXEC%

IF NOT EXIST "%SCRIPT_1%" (
    echo ERROR: Journal script not found: %SCRIPT_1%
    exit /b 1
)
echo Debug: Journal script 1 found: %SCRIPT_1%

IF NOT EXIST "%SCRIPT_2%" (
    echo ERROR: Journal script not found: %SCRIPT_2%
    exit /b 1
)
echo Debug: Journal script 2 found: %SCRIPT_2%

IF NOT EXIST "%PART_FILE%" (
    echo ERROR: Part file not found: %PART_FILE%
    exit /b 1
)
echo Debug: Part file found: %PART_FILE%

REM --- Execution ---
REM Run the first journal script
echo Debug: Running first journal script: %UGRAF_EXEC% -nx -journal "%SCRIPT_1%" -args "%PART_FILE%"
"%UGRAF_EXEC%" -nx -journal "%SCRIPT_1%" -args "%PART_FILE%" > "%SCRIPT_DIR%\nx_command_1.log" 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo ERROR: SCRIPT_1 execution failed with error code %ERRORLEVEL%
    echo Check log: %SCRIPT_DIR%\nx_command_1.log
    exit /b %ERRORLEVEL%
)
echo Debug: First journal script executed successfully.

REM Run the second journal script
echo Debug: Running second journal script: %UGRAF_EXEC% -nx -journal "%SCRIPT_2%" -args "%PART_FILE%"
"%UGRAF_EXEC%" -nx -journal "%SCRIPT_2%" -args "%PART_FILE%" > "%SCRIPT_DIR%\nx_command_2.log" 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo ERROR: SCRIPT_2 execution failed with error code %ERRORLEVEL%
    echo Check log: %SCRIPT_DIR%\nx_command_2.log
    exit /b %ERRORLEVEL%
)
echo Debug: Second journal script executed successfully.

echo Debug: All NX commands completed successfully.
exit /b 0
