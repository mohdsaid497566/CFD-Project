#!/bin/bash
# WSL Display Setup Script for Intake CFD GUI
# This script helps configure WSL for GUI applications

echo "===== WSL Display Setup Script ====="
echo "Setting up environment for GUI applications in WSL..."

# Check if running in WSL
if ! grep -q "Microsoft" /proc/version &>/dev/null && ! grep -q "microsoft" /proc/version &>/dev/null; then
    echo "Error: This script should only be run in WSL (Windows Subsystem for Linux)"
    exit 1
fi

# Determine WSL version
WSL_VERSION="1"
if grep -q "WSL2" /proc/version &>/dev/null; then
    WSL_VERSION="2"
fi
echo "Detected WSL version: $WSL_VERSION"

# Get Windows IP address (for WSL2)
if [ "$WSL_VERSION" = "2" ]; then
    WINDOWS_IP=$(ip route | grep default | awk '{print $3}')
    echo "Windows host IP: $WINDOWS_IP"
else
    WINDOWS_IP="localhost"
    echo "WSL1 detected, using localhost for X server connection"
fi

# Backup existing .bashrc
if [ -f ~/.bashrc ]; then
    cp ~/.bashrc ~/.bashrc.bak
    echo "Backed up existing .bashrc to ~/.bashrc.bak"
fi

# Add DISPLAY environment variable to .bashrc if not already there
if ! grep -q "DISPLAY=" ~/.bashrc; then
    if [ "$WSL_VERSION" = "2" ]; then
        echo -e "\n# X Server display configuration for WSL2" >> ~/.bashrc
        echo "export DISPLAY=$WINDOWS_IP:0.0" >> ~/.bashrc
    else
        echo -e "\n# X Server display configuration for WSL1" >> ~/.bashrc
        echo "export DISPLAY=:0" >> ~/.bashrc
    fi
    echo "Added DISPLAY environment variable to .bashrc"
else
    echo "DISPLAY variable already exists in .bashrc"
fi

# Set DISPLAY for current session
if [ "$WSL_VERSION" = "2" ]; then
    export DISPLAY=$WINDOWS_IP:0.0
else
    export DISPLAY=:0
fi
echo "Set DISPLAY=$DISPLAY for current session"

# Install required packages
echo -e "\nInstalling required X11 packages..."
sudo apt-get update
sudo apt-get install -y x11-apps libx11-dev libxext-dev libxrender-dev libxinerama-dev libxi-dev libxrandr-dev libxcursor-dev

# Create a simple test script
cat > ~/test_x11.sh << 'EOL'
#!/bin/bash
echo "Testing X11 connection..."
if command -v xeyes &>/dev/null; then
    echo "Running xeyes as a test (close the window to continue)"
    xeyes &
    sleep 3
    echo "If you see the xeyes application, X11 is working correctly."
else
    echo "xeyes not found, trying xclock instead..."
    if command -v xclock &>/dev/null; then
        echo "Running xclock as a test (close the window to continue)"
        xclock &
        sleep 3
    else
        echo "No X11 test applications found."
    fi
fi

echo -e "\nChecking X11 connection with xset..."
if xset q &>/dev/null; then
    echo "✅ X11 connection successful!"
else
    echo "❌ X11 connection failed!"
    echo "Make sure an X server (like VcXsrv or Xming) is running on Windows."
fi
EOL

chmod +x ~/test_x11.sh

# Create a launcher script
cat > ~/launch_cfd_gui.sh << 'EOL'
#!/bin/bash
# Launcher script for Intake CFD GUI

# Check if X server is reachable
if ! xset q &>/dev/null; then
    echo "ERROR: X server not reachable. Make sure an X server is running on Windows."
    echo "Install VcXsrv from: https://sourceforge.net/projects/vcxsrv/"
    echo "Then run it with 'Multiple Windows' mode and disable access control"
    exit 1
fi

# Navigate to the application directory
cd "$(dirname "$(realpath "$0")")/../Intake-CFD-Project/Garage"

# Run the application
echo "Launching Intake CFD GUI..."
python3 run_gui.py
EOL

chmod +x ~/launch_cfd_gui.sh

echo -e "\n===== Setup Complete ====="
echo "To test your X11 connection, run:"
echo "  ~/test_x11.sh"
echo ""
echo "To launch the Intake CFD GUI, run:"
echo "  ~/launch_cfd_gui.sh"
echo ""
echo "IMPORTANT: Make sure you have an X server (like VcXsrv) running on Windows!"
echo "Download VcXsrv from: https://sourceforge.net/projects/vcxsrv/"
