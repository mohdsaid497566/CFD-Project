@echo off
REM GUI launcher for WSL
echo Starting GUI environment for WSL...

REM Check if an X server is running
tasklist /FI "IMAGENAME eq vcxsrv.exe" 2>NUL | find /I /N "vcxsrv.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo X server is already running.
) else (
    echo No VcXsrv detected, checking for X410...
    tasklist /FI "IMAGENAME eq X410.exe" 2>NUL | find /I /N "X410.exe">NUL
    if "%ERRORLEVEL%"=="0" (
        echo X410 is running.
    ) else (
        echo No X server detected. Attempting to start VcXsrv...
        start "" "%PROGRAMFILES%\VcXsrv\vcxsrv.exe" -ac -multiwindow -clipboard -wgl
        if "%ERRORLEVEL%"=="9009" (
            echo VcXsrv not found. Please install VcXsrv or X410 from:
            echo VcXsrv: https://sourceforge.net/projects/vcxsrv/
            echo X410: https://x410.dev/ (Windows Store)
            echo.
            echo Continuing anyway, but the GUI may not appear...
        ) else (
            echo VcXsrv started successfully.
            timeout /t 2 /nobreak > NUL
        )
    )
)

echo.
echo Launching WSL GUI...
wsl -d Ubuntu bash -c "cd %~dp0 && ./launch_gui_wsl.sh"

echo.
echo If you don't see the GUI, try the following:
echo 1. Install VcXsrv from https://sourceforge.net/projects/vcxsrv/
echo 2. Run VcXsrv with these options: -ac -multiwindow -clipboard -wgl
echo 3. Try running the launcher again.
echo.

pause
