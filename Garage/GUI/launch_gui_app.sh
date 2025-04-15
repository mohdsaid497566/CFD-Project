#!/bin/bash
# Launch GUI application with proper X server configuration

# Set verbose debugging
set -x

echo "========================================"
echo "Enhanced WSL GUI Application Launcher"
echo "========================================"

# Function to check if a command exists
command_exists() {
    command -v "$1" &> /dev/null
}

# Function to check if X server is accessible
check_xserver() {
    echo "Testing X server connection with DISPLAY=$DISPLAY"
    if xset q &>/dev/null; then
        echo "✓ X server connection successful!"
        return 0
    else
        echo "✗ X server connection failed"
        return 1
    fi
}

# Get path to VcXsrv on Windows
get_vcxsrv_path() {
    local paths=(
        "/mnt/c/Program Files/VcXsrv/vcxsrv.exe"
        "/mnt/c/Program Files (x86)/VcXsrv/vcxsrv.exe"
    )
    
    for path in "${paths[@]}"; do
        if [ -f "$path" ]; then
            echo "$path"
            return 0
        fi
    done
    
    echo ""
    return 1
}

# Start VcXsrv if not already running
start_vcxsrv() {
    echo "Starting VcXsrv X server..."
    
    # Get Windows username
    WIN_USER=$(powershell.exe -Command '$env:UserName' | tr -d '\r\n')
    echo "Windows username: $WIN_USER"
    
    # Check if vcxsrv is running
    if powershell.exe -Command "Get-Process vcxsrv -ErrorAction SilentlyContinue" | grep -q vcxsrv; then
        echo "VcXsrv is already running"
    else
        # Get path to VcXsrv
        VCXSRV_PATH=$(get_vcxsrv_path)
        if [ -z "$VCXSRV_PATH" ]; then
            echo "VcXsrv not found. Please install it from https://sourceforge.net/projects/vcxsrv/"
            powershell.exe -Command "Start-Process 'https://sourceforge.net/projects/vcxsrv/'"
            return 1
        fi
        
        # Create config directory if it doesn't exist
        CONFIG_DIR="/mnt/c/Users/$WIN_USER/AppData/Roaming/Xlaunch"
        mkdir -p "$CONFIG_DIR" 2>/dev/null
        
        # Create a minimal XLaunch config file
        CONFIG_PATH="$CONFIG_DIR/wsl_config.xlaunch"
        cat > "$CONFIG_PATH" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<XLaunch
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
        
        # Start VcXsrv using PowerShell
        VCXSRV_WIN_PATH=$(wslpath -w "$VCXSRV_PATH")
        CONFIG_WIN_PATH=$(wslpath -w "$CONFIG_PATH")
        
        echo "Starting VcXsrv from $VCXSRV_WIN_PATH with config $CONFIG_WIN_PATH"
        powershell.exe -Command "Start-Process '$VCXSRV_WIN_PATH' -ArgumentList '-run', '$CONFIG_WIN_PATH' -NoNewWindow"
        
        # Give it a moment to start
        sleep 3
    fi
}

# Configure Windows Firewall for X11
configure_firewall() {
    echo "Checking Windows Firewall configuration..."
    
    # Create PowerShell script to check and update firewall rules
    cat > check_firewall.ps1 << 'EOF'
$ErrorActionPreference = "Stop"

# Check if the rule exists
$ruleName = "WSL2 X11 Forwarding"
$rule = Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue

if ($rule -eq $null) {
    Write-Host "Creating firewall rule for X11..."
    try {
        New-NetFirewallRule -DisplayName $ruleName -Direction Inbound -Action Allow -Protocol TCP -LocalPort 6000-6010 -Description "Allows X11 forwarding from WSL2"
        Write-Host "Firewall rule created successfully"
    } catch {
        Write-Host "Failed to create firewall rule. Run this script as administrator."
    }
} else {
    Write-Host "X11 firewall rule already exists"
}
EOF
    
    # Run the PowerShell script
    powershell.exe -ExecutionPolicy Bypass -File check_firewall.ps1
    
    # Clean up
    rm -f check_firewall.ps1
}

# Try different DISPLAY settings
try_display_settings() {
    echo "Trying different DISPLAY settings..."
    
    # Try with Windows IP
    WINDOWS_IP=$(grep -m 1 nameserver /etc/resolv.conf | awk '{print $2}')
    export DISPLAY="${WINDOWS_IP}:0.0"
    export LIBGL_ALWAYS_INDIRECT=1
    echo "Trying with DISPLAY=${DISPLAY}"
    if check_xserver; then
        return 0
    fi
    
    # Try with localhost
    export DISPLAY=localhost:0.0
    echo "Trying with DISPLAY=${DISPLAY}"
    if check_xserver; then
        return 0
    fi
    
    # Try with default display
    export DISPLAY=:0
    echo "Trying with DISPLAY=${DISPLAY}"
    if check_xserver; then
        return 0
    fi
    
    # Try with 127.0.0.1
    export DISPLAY=127.0.0.1:0.0
    echo "Trying with DISPLAY=${DISPLAY}"
    if check_xserver; then
        return 0
    fi
    
    return 1
}

# Check necessary packages
check_packages() {
    echo "Checking required packages..."
    
    local missing_packages=()
    
    # Check for tkinter
    if ! python -c "import tkinter" &>/dev/null; then
        missing_packages+=("python3-tk")
    fi
    
    # Check for X11 utilities
    if ! command_exists xset; then
        missing_packages+=("x11-apps")
    fi
    
    # If we're missing packages, ask to install them
    if [ ${#missing_packages[@]} -gt 0 ]; then
        echo "Missing packages: ${missing_packages[*]}"
        echo "These packages are required for GUI applications"
        
        read -p "Do you want to install them? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            sudo apt-get update
            sudo apt-get install -y "${missing_packages[@]}"
            
            echo "Packages installed successfully"
            return 0
        else
            echo "Packages not installed. GUI application may not function correctly."
            return 1
        fi
    else
        echo "All required packages are installed"
        return 0
    fi
}

# Create a Windows fallback script
create_windows_fallback() {
    echo "Creating Windows Python fallback script..."
    
    cat > run_in_windows.py << 'EOF'
import os
import sys
import subprocess
import tkinter as tk
from tkinter import messagebox

# Create a simple status window
root = tk.Tk()
root.title("WSL GUI Fallback")
root.geometry("600x400")

status_text = tk.Text(root, wrap=tk.WORD)
status_text.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)

def add_status(msg):
    status_text.insert(tk.END, msg + "\n")
    status_text.see(tk.END)
    root.update()

add_status("WSL GUI Fallback Launcher")
add_status("======================")
add_status("This script helps run GUI applications when the WSL X server approach fails.")
add_status("")

# Try to get the WSL directory
wsl_dir = os.getcwd()
if len(sys.argv) > 1:
    wsl_dir = sys.argv[1]
add_status(f"WSL directory: {wsl_dir}")

# Try to get the WSL distribution name
wsl_distro = "Ubuntu"
if len(sys.argv) > 2:
    wsl_distro = sys.argv[2]
add_status(f"WSL distribution: {wsl_distro}")

# Check for Python in WSL
add_status("Checking Python in WSL...")
try:
    result = subprocess.run(
        ["wsl", "-d", wsl_distro, "-e", "python", "--version"],
        capture_output=True, text=True
    )
    add_status(f"WSL Python version: {result.stdout.strip()}")
except Exception as e:
    add_status(f"Error checking WSL Python: {str(e)}")

# Check if X server is running
add_status("Starting VcXsrv X server...")
try:
    # Check if VcXsrv is running
    vcxsrv_running = False
    try:
        result = subprocess.run(["tasklist", "/FI", "IMAGENAME eq vcxsrv.exe"], 
                               capture_output=True, text=True)
        if "vcxsrv.exe" in result.stdout:
            add_status("VcXsrv is already running")
            vcxsrv_running = True
    except:
        pass
    
    # Try to start VcXsrv if not running
    if not vcxsrv_running:
        # Look for VcXsrv in common locations
        vcxsrv_paths = [
            os.path.expandvars("%ProgramFiles%\\VcXsrv\\vcxsrv.exe"),
            os.path.expandvars("%ProgramFiles(x86)%\\VcXsrv\\vcxsrv.exe"),
            "C:\\Program Files\\VcXsrv\\vcxsrv.exe",
            "C:\\Program Files (x86)\\VcXsrv\\vcxsrv.exe"
        ]
        
        vcxsrv_path = None
        for path in vcxsrv_paths:
            if os.path.exists(path):
                vcxsrv_path = path
                break
        
        if vcxsrv_path:
            add_status(f"Found VcXsrv at: {vcxsrv_path}")
            
            # Create config file directory
            config_dir = os.path.join(os.environ["APPDATA"], "Xlaunch")
            os.makedirs(config_dir, exist_ok=True)
            
            # Create config file
            config_file = os.path.join(config_dir, "config.xlaunch")
            with open(config_file, "w") as f:
                f.write('''<?xml version="1.0" encoding="UTF-8"?>
<XLaunch WindowMode="MultiWindow" ClientMode="NoClient" Display="0" LocalClient="False" RemoteClient="False" NoAccessControl="True" XDMCPTerminate="False" />''')
            
            # Start VcXsrv
            add_status("Starting VcXsrv...")
            subprocess.Popen([vcxsrv_path, "-run", config_file])
            add_status("VcXsrv started")
            
            # Wait a moment for it to start
            import time
            time.sleep(2)
        else:
            add_status("VcXsrv not found. Please install it.")
            if messagebox.askyesno("VcXsrv Missing", "VcXsrv is required but not found. Would you like to download it now?"):
                import webbrowser
                webbrowser.open("https://sourceforge.net/projects/vcxsrv/")
except Exception as e:
    add_status(f"Error starting VcXsrv: {str(e)}")

# Try running the GUI application
add_status("\nAttempting to run the application...")

# Get local IP address for WSL
import socket
host_ip = socket.gethostbyname(socket.gethostname())
add_status(f"Host IP: {host_ip}")

# Construct the command to run
cmd = f'''
cd {wsl_dir} && 
export DISPLAY="{host_ip}:0" &&
export LIBGL_ALWAYS_INDIRECT=1 &&
python MDO.py
'''
add_status(f"Running command: {cmd}")

# Run the command
try:
    process = subprocess.Popen(
        ["wsl", "-d", wsl_distro, "-e", "bash", "-c", cmd],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Show a simple progress indicator
    import threading
    
    def monitor_process():
        while process.poll() is None:
            add_status("Application running...")
            # Display some stdout if available
            stdout = process.stdout.readline().decode('utf-8', errors='replace').strip()
            if stdout:
                add_status(f"Output: {stdout}")
            import time
            time.sleep(1)
            
        # Process has finished
        returncode = process.returncode
        stdout, stderr = process.communicate()
        stdout = stdout.decode('utf-8', errors='replace')
        stderr = stderr.decode('utf-8', errors='replace')
        
        add_status(f"\nApplication exited with code: {returncode}")
        if stdout:
            add_status("\nOutput:")
            add_status(stdout)
        
        if stderr:
            add_status("\nErrors:")
            add_status(stderr)
    
    thread = threading.Thread(target=monitor_process)
    thread.daemon = True
    thread.start()
    
except Exception as e:
    add_status(f"Error running application: {str(e)}")

# Add buttons
button_frame = tk.Frame(root)
button_frame.pack(pady=20)

def open_vcxsrv_download():
    import webbrowser
    webbrowser.open("https://sourceforge.net/projects/vcxsrv/")

tk.Button(button_frame, text="Download VcXsrv", command=open_vcxsrv_download).pack(side=tk.LEFT, padx=10)
tk.Button(button_frame, text="Close", command=root.quit).pack(side=tk.LEFT, padx=10)

root.mainloop()
EOF

    echo "Windows fallback script created"
}

# Run application with Windows Python as a fallback
run_with_windows_python() {
    echo "Attempting to run with Windows Python as fallback..."
    
    # Create the fallback script
    create_windows_fallback
    
    # Get the Windows path to this directory
    WSL_DIR="$(pwd)"
    WIN_PATH="$(wslpath -w "$WSL_DIR")"
    
    # Get the WSL distro name
    WSL_DISTRO="$(wsl.exe -l -q | head -1 | tr -d '\r')"
    
    echo "WSL directory: $WSL_DIR"
    echo "Windows path: $WIN_PATH"
    echo "WSL distribution: $WSL_DISTRO"
    
    # Run the Python script in Windows
    echo "Launching Windows Python to run the application..."
    powershell.exe -Command "cd '$WIN_PATH'; python run_in_windows.py '$WIN_PATH' '$WSL_DISTRO'"
    
    # Clean up
    rm -f run_in_windows.py
}

# Main script

# 1. Check for required packages
check_packages

# 2. Start VcXsrv if needed
start_vcxsrv

# 3. Configure firewall
configure_firewall

# 4. Try different display settings
if try_display_settings; then
    echo "X server connection established. Launching application..."
    
    # 5. Run the application
    python -vv MDO.py
    
    # Check if the application exited successfully
    if [ $? -eq 0 ]; then
        echo "Application exited successfully!"
        exit 0
    else
        echo "Application exited with an error. See above for details."
        echo "Attempting to run with Windows Python as fallback..."
        run_with_windows_python
    fi
else
    echo "Failed to connect to the X server after trying multiple settings."
    echo "Attempting to run with Windows Python as fallback..."
    run_with_windows_python
fi
