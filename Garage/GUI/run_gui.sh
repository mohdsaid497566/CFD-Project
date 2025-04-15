#!/bin/bash
# filepath: /mnt/c/Users/Mohammed/Desktop/Intake-CFD-Project/nx/run_gui.sh

# This script helps run GUI applications in WSL with proper X11 configuration

# Activate the virtual environment if it exists
if [ -f "./venv/bin/activate" ]; then
    source ./venv/bin/activate
fi

# Try to detect if we're in WSL
IS_WSL=false
if grep -q Microsoft /proc/version || grep -q microsoft /proc/version; then
    IS_WSL=true
    echo "WSL detected - configuring display for X11"
    
    # Try to get the Windows host IP address
    WINDOWS_IP=$(grep -m 1 nameserver /etc/resolv.conf | awk '{print $2}')
    
    if [ -n "$WINDOWS_IP" ]; then
        echo "Setting DISPLAY to Windows host at $WINDOWS_IP:0"
        export DISPLAY="$WINDOWS_IP:0"
    else
        echo "Setting DISPLAY to default :0"
        export DISPLAY=:0
    fi
    
    # Check if we need to disable access control
    export LIBGL_ALWAYS_INDIRECT=1
    echo "Set LIBGL_ALWAYS_INDIRECT=1"
fi

# Run the diagnostics script to check GUI setup
echo "Running GUI diagnostics..."
python gui_diagnostics.py

echo -e "\n=== Attempting to start the application ===\n"

# Try to run the application
python MDO.py

# Store exit code
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo -e "\n=== Application exited with error code: $EXIT_CODE ==="
    echo "Starting trouble shooting..."
    
    # If it failed, try to suggest fixes
    if [ "$IS_WSL" = true ]; then
        echo -e "\nPossible WSL GUI issues:"
        echo "1. Make sure you have an X Server running on Windows"
        echo "   - Popular options: VcXsrv, Xming, X410"
        echo "   - When using VcXsrv, ensure 'Disable access control' is checked"
        echo ""
        echo "2. Try these alternative DISPLAY settings:"
        echo "   export DISPLAY=:0"
        echo "   export DISPLAY=127.0.0.1:0"
        echo "   export DISPLAY=\$(grep -m 1 nameserver /etc/resolv.conf | awk '{print \$2}'):0"
        echo ""
        echo "3. Install needed X11 libraries:"
        echo "   sudo apt-get update"
        echo "   sudo apt-get install -y libx11-dev libxext-dev libxrender-dev libxinerama-dev \\"
        echo "        libxi-dev libxrandr-dev libxcursor-dev libxtst-dev libxft-dev \\"
        echo "        libgl1-mesa-dev libglu1-mesa-dev"
    fi
    
    echo -e "\nInstall debug version of tkinter:"
    echo "sudo apt-get install python3-tk-dbg"
    echo ""
    echo "Try running with Python verbose mode:"
    echo "python -v MDO.py"
fi