#!/bin/bash
# filepath: /mnt/c/Users/Mohammed/Desktop/Intake-CFD-Project/nx/fix_wsl_gui.sh

# This script provides a complete solution for running GUI applications in WSL2
# by configuring the X server properly and handling firewall exceptions

echo "===== WSL GUI Fixer ====="
echo "This tool will set up your WSL environment to run GUI applications properly"
echo ""

# Detect WSL version
if grep -q "microsoft" /proc/version; then
    echo "WSL detected"
    WSL_VERSION=$(wsl.exe -l -v | grep -v "NAME" | grep -v "\-\-" | awk '{print $3}' | tr -d '\r\n')
    echo "WSL Version: $WSL_VERSION"
else
    echo "This script is intended to run on Windows Subsystem for Linux (WSL)"
    exit 1
fi

# Function to get Windows IP
get_windows_ip() {
    # Get Windows host IP address (most reliable method)
    WINDOWS_IP=$(grep -m 1 nameserver /etc/resolv.conf | awk '{print $2}')
    echo "Detected Windows host IP: $WINDOWS_IP"
    return 0
}

# Function to check if X server is running
check_xserver() {
    # Test if X server is accessible with the current DISPLAY setting
    echo "Testing X server connection with DISPLAY=$DISPLAY"
    if xset q &>/dev/null; then
        echo "✅ X server is running and accessible"
        return 0
    else
        echo "❌ X server is not accessible"
        return 1
    fi
}

# Create PowerShell script to configure Windows firewall
create_firewall_script() {
    cat > setup_firewall.ps1 << 'EOL'
# Windows PowerShell script to allow X11 connections through Windows Firewall
$ErrorActionPreference = "Stop"

Write-Host "Setting up Windows Firewall for X11 forwarding..."

try {
    # Check if the rule already exists
    $existingRule = Get-NetFirewallRule -DisplayName "WSL2 X11 Forwarding" -ErrorAction SilentlyContinue
    
    if ($existingRule -eq $null) {
        # Create a new inbound rule to allow X11 traffic
        New-NetFirewallRule -DisplayName "WSL2 X11 Forwarding" `
                           -Direction Inbound `
                           -Action Allow `
                           -Protocol TCP `
                           -LocalPort 6000-6010 `
                           -Program "%ProgramW6432%\VcXsrv\vcxsrv.exe" `
                           -Description "Allows X11 forwarding from WSL2 to VcXsrv"
        
        Write-Host "✅ Firewall rule created successfully"
    }
    else {
        Write-Host "✅ Firewall rule already exists"
    }
    
    # Create a new rule for any X server
    $anyXServerRule = Get-NetFirewallRule -DisplayName "X11 Server" -ErrorAction SilentlyContinue
    
    if ($anyXServerRule -eq $null) {
        New-NetFirewallRule -DisplayName "X11 Server" `
                           -Direction Inbound `
                           -Action Allow `
                           -Protocol TCP `
                           -LocalPort 6000-6010 `
                           -Description "Allows any X11 server to receive connections"
        
        Write-Host "✅ Generic X11 server firewall rule created successfully"
    }
    
    Write-Host "Firewall configuration complete!"
    
} catch {
    Write-Host "❌ Error configuring firewall: $_"
    exit 1
}
EOL
    echo "Created PowerShell script for firewall configuration"
}

# Function to setup XServer
setup_xserver() {
    echo "Setting up X server configuration..."
    
    # Create permanent configuration for DISPLAY
    BASHRC_PATH="$HOME/.bashrc"
    
    # Check if we've already added our config to .bashrc
    if grep -q "# WSL GUI CONFIGURATION" "$BASHRC_PATH"; then
        echo "WSL GUI configuration already exists in $BASHRC_PATH"
        # Update it
        sed -i '/# WSL GUI CONFIGURATION START/,/# WSL GUI CONFIGURATION END/d' "$BASHRC_PATH"
    fi
    
    # Add configuration to .bashrc
    cat >> "$BASHRC_PATH" << EOL

# WSL GUI CONFIGURATION START - Added by fix_wsl_gui.sh
# Set up X11 forwarding for GUI applications
export DISPLAY=:0
export LIBGL_ALWAYS_INDIRECT=1
if [ -z "\$DISPLAY" ] || ! xset q &>/dev/null; then
    # Try different DISPLAY settings if the default isn't working
    export DISPLAY=\$(grep -m 1 nameserver /etc/resolv.conf | awk '{print \$2}'):0
    if ! xset q &>/dev/null; then
        export DISPLAY=localhost:0.0
    fi
fi
# WSL GUI CONFIGURATION END

EOL

    echo "✅ Updated $BASHRC_PATH with GUI configuration"
    
    # Create XServer startup script
    cat > "$HOME/start_xserver.sh" << 'EOL'
#!/bin/bash
# Start X server and GUI applications from WSL

# This script helps start the X server on Windows and prepare the environment for GUI apps

# Check if we're on WSL
if ! grep -q "microsoft" /proc/version; then
    echo "This script is intended for WSL only."
    exit 1
fi

# Get Windows username
WINDOWS_USER=$(cmd.exe /c echo %USERNAME% 2>/dev/null | tr -d '\r')
echo "Windows user: $WINDOWS_USER"

# Check if VcXsrv is installed
VCXSRV_PATH="/mnt/c/Program Files/VcXsrv/vcxsrv.exe"
VCXSRV_PATH_X86="/mnt/c/Program Files (x86)/VcXsrv/vcxsrv.exe"

if [ -f "$VCXSRV_PATH" ]; then
    echo "Found VcXsrv at $VCXSRV_PATH"
    FOUND_VCXSRV=true
elif [ -f "$VCXSRV_PATH_X86" ]; then
    echo "Found VcXsrv at $VCXSRV_PATH_X86"
    VCXSRV_PATH="$VCXSRV_PATH_X86"
    FOUND_VCXSRV=true
else
    echo "VcXsrv not found in common locations."
    FOUND_VCXSRV=false
fi

# Start VcXsrv if found
if [ "$FOUND_VCXSRV" = true ]; then
    echo "Launching VcXsrv..."
    
    # Create config file
    CONFIG_PATH="/mnt/c/Users/$WINDOWS_USER/AppData/Roaming/Xlaunch/wsl_config.xlaunch"
    mkdir -p "$(dirname "$CONFIG_PATH")" 2>/dev/null
    
    cat > "$CONFIG_PATH" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<XLaunch
    xmlns="http://www.straightrunning.com/XmingNotes"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.straightrunning.com/XmingNotes XLaunch.xsd"
    WindowMode="MultiWindow"
    ClientMode="NoClient"
    Display="0"
    Clipboard="true"
    ExtraParams="-ac"
    LocalClient="false"
    RemoteClient="false"
    NoAccessControl="true"
    XDMCPTerminate="false"
/>
EOF
    
    # Close any existing VcXsrv instances
    powershell.exe -Command "Stop-Process -Name vcxsrv -ErrorAction SilentlyContinue"
    
    # Start VcXsrv with our config
    powershell.exe -Command "Start-Process '$VCXSRV_PATH' -ArgumentList '-run', '$CONFIG_PATH'"
    
    echo "VcXsrv started with no access control (allows WSL connections)"
else
    echo "Please install VcXsrv from: https://sourceforge.net/projects/vcxsrv/"
    powershell.exe -Command "Start-Process 'https://sourceforge.net/projects/vcxsrv/'"
    exit 1
fi

# Set DISPLAY to Windows host IP
export DISPLAY=:0
export LIBGL_ALWAYS_INDIRECT=1
echo "Set DISPLAY=$DISPLAY"

# Wait a moment for X server to start
sleep 2

# Check if X server is accessible
if xset q &>/dev/null; then
    echo "✅ X server connection successful!"
else
    WINDOWS_IP=$(grep -m 1 nameserver /etc/resolv.conf | awk '{print $2}')
    echo "❌ X server not accessible. Trying with Windows IP..."
    export DISPLAY=$WINDOWS_IP:0
    
    if xset q &>/dev/null; then
        echo "✅ X server connection successful with DISPLAY=$DISPLAY"
    else
        echo "❌ X server still not accessible. Please ensure:"
        echo "  1. VcXsrv is running with 'Disable access control' checked"
        echo "  2. Windows firewall allows connections to VcXsrv"
        exit 1
    fi
fi

# Run the application if provided as an argument
if [ -n "$1" ]; then
    echo "Launching application: $1"
    "$@"
fi

echo "Environment is ready for GUI applications"
echo "You can run GUI apps now! The X server is running."
EOL

    chmod +x "$HOME/start_xserver.sh"
    echo "✅ Created X server startup script at $HOME/start_xserver.sh"
    
    # Configure firewall by running PowerShell script
    echo "Configuring Windows Firewall for X11 forwarding (requires admin rights)..."
    create_firewall_script
    powershell.exe -ExecutionPolicy Bypass -Command "Start-Process powershell -Verb RunAs -ArgumentList '-ExecutionPolicy Bypass -File $(wslpath -w $(pwd))/setup_firewall.ps1'"
    
    echo "✅ Configuration complete!"
}

# Main script execution
echo "Configuring environment for GUI applications..."
get_windows_ip

# Create a script to launch our application with GUI
cat > ./launch_gui_app.sh << 'EOL'
#!/bin/bash
# Launch GUI application with proper X server configuration

# Check if X server is running and accessible
xset q &>/dev/null
if [ $? -ne 0 ]; then
    echo "X server not accessible. Starting X server setup..."
    
    # Check if start_xserver.sh exists and run it
    if [ -f "$HOME/start_xserver.sh" ]; then
        bash "$HOME/start_xserver.sh"
    else
        echo "Startx script not found. Please run fix_wsl_gui.sh first."
        exit 1
    fi
fi

# Add execution permission for modified script
chmod +x MDO.py

# Run the application
echo "Starting the application..."
python MDO.py
EOL

chmod +x ./launch_gui_app.sh

# Set up XServer configuration
setup_xserver

echo ""
echo "============================"
echo "Setup completed successfully!"
echo "============================"
echo ""
echo "To run the GUI application:"
echo "1. Install VcXsrv on Windows if not already installed"
echo "2. Run ./launch_gui_app.sh"
echo ""
echo "Would you like to run the application now? (y/n)"
read -r answer
if [[ "$answer" =~ ^[Yy]$ ]]; then
    ./launch_gui_app.sh
else
    echo "You can run the application later with ./launch_gui_app.sh"
fi

# Clean up
rm -f setup_firewall.ps1