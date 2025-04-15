#!/usr/bin/env python3

"""
WSL GUI Fix Utility
This script helps diagnose and fix common GUI issues when running in Windows Subsystem for Linux (WSL).
"""

import os
import sys
import subprocess
import platform

def check_wsl_environment():
    """Check if we're running in WSL and what environment variables are set"""
    is_wsl = False
    wsl_version = "unknown"
    
    if os.path.exists("/proc/version"):
        with open("/proc/version", "r") as f:
            version_info = f.read().lower()
            if "microsoft" in version_info:
                is_wsl = True
                wsl_version = "WSL1" if "lxss" in version_info.lower() else "WSL2"
    
    print(f"Running in WSL: {is_wsl}")
    if is_wsl:
        print(f"WSL Version: {wsl_version}")
    
    # Check important environment variables
    env_vars = ["DISPLAY", "WAYLAND_DISPLAY", "XDG_SESSION_TYPE", "LIBGL_ALWAYS_INDIRECT"]
    for var in env_vars:
        print(f"{var} = {os.environ.get(var, 'Not set')}")
    
    return is_wsl

def check_x_server():
    """Check if X server is accessible"""
    try:
        result = subprocess.run(['xset', 'q'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode == 0:
            print("X server is running and accessible.")
            return True
        else:
            print("X server is not accessible.")
            error_msg = result.stderr.decode('utf-8').strip()
            if error_msg:
                print(f"Error: {error_msg}")
            return False
    except FileNotFoundError:
        print("xset command not found. X11 utilities might not be installed.")
        return False
    except Exception as e:
        print(f"Error checking X server: {str(e)}")
        return False

def configure_wsl_display():
    """Configure DISPLAY variable for WSL"""
    if "DISPLAY" not in os.environ:
        # Try to determine Windows IP
        try:
            win_ip = subprocess.check_output(['/mnt/c/Windows/System32/ipconfig.exe'], 
                                           stderr=subprocess.STDOUT).decode('utf-8')
            
            # Look for WSL adapter
            for line in win_ip.split('\n'):
                if "WSL" in line and "IPv4" in line:
                    ip = line.split(":")[-1].strip()
                    print(f"Found WSL adapter IP: {ip}")
                    os.environ["DISPLAY"] = f"{ip}:0.0"
                    return True
            
            # Default option
            print("Setting default DISPLAY value")
            os.environ["DISPLAY"] = "127.0.0.1:0.0"
            return True
            
        except Exception as e:
            print(f"Error configuring DISPLAY: {str(e)}")
            
            # Fallback to typical defaults
            print("Using fallback DISPLAY value")
            os.environ["DISPLAY"] = "127.0.0.1:0.0"
            return True
    else:
        print(f"DISPLAY is already set to {os.environ['DISPLAY']}")
        return True

def fix_dbus_issues():
    """Fix common D-Bus issues in WSL"""
    if "DBUS_SESSION_BUS_ADDRESS" not in os.environ:
        print("Setting DBUS_SESSION_BUS_ADDRESS")
        os.environ["DBUS_SESSION_BUS_ADDRESS"] = "unix:path=/run/user/1000/bus"
    
    # Check if dbus is running
    try:
        result = subprocess.run(['dbus-launch', '--version'], 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE)
        if result.returncode == 0:
            print("dbus-launch is available")
        else:
            print("dbus-launch is not working correctly")
    except FileNotFoundError:
        print("dbus-launch not found. Consider installing dbus-x11 package.")
    except Exception as e:
        print(f"Error checking dbus: {str(e)}")

def create_wsl_launcher():
    """Create a launcher script for WSL environment"""
    launcher_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "launch_gui_wsl.sh")
    
    script_content = """#!/bin/bash
# WSL GUI launcher script - auto-generated

# Export display settings
export DISPLAY=127.0.0.1:0.0
export LIBGL_ALWAYS_INDIRECT=1

# Detect VcXsrv or X410
if ps -ef | grep -i "vcxsrv\|x410" | grep -v grep > /dev/null; then
    echo "X server detected. Good!"
else
    echo "WARNING: No X server detected. Please start VcXsrv, X410, or another X server on Windows."
    echo "For VcXsrv, make sure to run with options: -ac -multiwindow -clipboard -wgl"
    echo "Continuing anyway in case the detection failed..."
fi

# Set better font rendering
export GDK_DPI_SCALE=1.0
export QT_SCALE_FACTOR=1.0

# Launch the GUI
cd "$(dirname "$0")"
echo "Launching patched GUI..."
python patch.py
"""
    
    try:
        with open(launcher_file, 'w') as f:
            f.write(script_content)
        
        # Make it executable
        os.chmod(launcher_file, 0o755)
        print(f"Created WSL launcher at {launcher_file}")
        print("Run it with: ./launch_gui_wsl.sh")
        return True
    except Exception as e:
        print(f"Error creating launcher: {str(e)}")
        return False

def create_windows_launcher():
    """Create a Windows .bat launcher to help set up the environment"""
    launcher_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Launch_GUI.bat")
    
    script_content = """@echo off
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
        start "" "%PROGRAMFILES%\\VcXsrv\\vcxsrv.exe" -ac -multiwindow -clipboard -wgl
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
"""
    
    try:
        # Convert path to proper Windows path
        win_path = launcher_file.replace('/mnt/c/', 'C:\\').replace('/', '\\')
        
        # Write via direct Windows access if possible
        with open(launcher_file, 'w') as f:
            f.write(script_content)
        
        print(f"Created Windows launcher at {launcher_file}")
        return True
    except Exception as e:
        print(f"Error creating Windows launcher: {str(e)}")
        return False

def main():
    """Main function to run WSL GUI fixes"""
    print("Starting WSL GUI fix utility...")
    
    # Check WSL environment
    is_wsl = check_wsl_environment()
    
    if not is_wsl:
        print("Not running in WSL. This script is designed for WSL environments.")
        sys.exit(1)
    
    # Check X server
    x_server_working = check_x_server()
    
    # Configure display
    configure_wsl_display()
    
    # Fix D-Bus issues
    fix_dbus_issues()
    
    # Create launcher scripts
    create_wsl_launcher()
    create_windows_launcher()
    
    print("\nWSL GUI fixes applied!")
    print("\nTroubleshooting tips for WSL GUI issues:")
    print("1. Install and run VcXsrv or X410 on Windows")
    print("2. For VcXsrv, use these options: -ac -multiwindow -clipboard -wgl")
    print("3. Make sure Windows Firewall allows connections to your X server")
    print("4. Try using the created launcher scripts: Launch_GUI.bat or launch_gui_wsl.sh")
    print("5. If fonts look bad, try adjusting GDK_DPI_SCALE or QT_SCALE_FACTOR values")
    print("6. For persistent DISPLAY settings, add to your .bashrc: export DISPLAY=127.0.0.1:0.0")

if __name__ == "__main__":
    main()
