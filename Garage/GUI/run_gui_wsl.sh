#!/bin/bash
# filepath: /mnt/c/Users/Mohammed/Desktop/Intake-CFD-Project/nx/run_gui_wsl.sh

# This script provides an alternative way to run the GUI in WSL
# It uses a fallback to the Windows native Python with tkinter

echo "WSL GUI Helper - Running application with fallback options"
echo "=========================================================="

# Activate the virtual environment if it exists
if [ -f "./venv/bin/activate" ]; then
    source ./venv/bin/activate
fi

# Try different DISPLAY settings
echo "Attempting to run with various DISPLAY settings..."

# Try localhost display
export DISPLAY=localhost:0.0
export LIBGL_ALWAYS_INDIRECT=1
echo "Trying with DISPLAY=localhost:0.0"
python -c "import tkinter as tk; root=tk.Tk(); root.destroy()" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "Tkinter works with DISPLAY=localhost:0.0, running application..."
    python MDO.py
    exit 0
fi

# Try default display
export DISPLAY=:0
echo "Trying with DISPLAY=:0"
python -c "import tkinter as tk; root=tk.Tk(); root.destroy()" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "Tkinter works with DISPLAY=:0, running application..."
    python MDO.py
    exit 0
fi

# Try with WSL2 IP address
WINDOWS_IP=$(grep -m 1 nameserver /etc/resolv.conf | awk '{print $2}')
export DISPLAY="${WINDOWS_IP}:0"
echo "Trying with DISPLAY=${WINDOWS_IP}:0"
python -c "import tkinter as tk; root=tk.Tk(); root.destroy()" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "Tkinter works with DISPLAY=${WINDOWS_IP}:0, running application..."
    python MDO.py
    exit 0
fi

# All X11 attempts failed, try non-X11 GUI backends
echo "X11 display failed. Checking if matplotlib works with non-X11 backend..."
python -c "import matplotlib; matplotlib.use('Agg'); print('Matplotlib Agg backend works!')" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "Matplotlib can use non-GUI backend, but tkinter still requires X11."
fi

echo "All X11 attempts failed."
echo "Checking if we can run a headless version or Windows version..."

# Fallback to using Windows Python through powershell
echo "Attempting to run using Windows Python..."

# Create a temporary script to run in Windows Python
cat > ./run_gui_win.py << 'EOL'
import os
import sys
import subprocess
import tkinter as tk
from tkinter import messagebox, ttk

# Initialization...
root = tk.Tk()
root.title("WSL GUI Launcher")
root.geometry("600x400")
root.configure(background="#f0f0f0")

# Modern style
style = ttk.Style()
style.configure("TFrame", background="#f0f0f0")
style.configure("TLabel", background="#f0f0f0", font=("Segoe UI", 10))
style.configure("TButton", font=("Segoe UI", 10))

# Main frame
frame = ttk.Frame(root, padding="20")
frame.pack(fill=tk.BOTH, expand=True)

# Header with color
header_frame = tk.Frame(frame, bg="#2C3E50")
header_frame.pack(fill=tk.X, pady=(0, 20))
header = tk.Label(header_frame, text="Intake CFD Optimization Suite", 
                 font=("Segoe UI", 18, "bold"), fg="white", bg="#2C3E50", 
                 padx=20, pady=10)
header.pack()

# Status message
status_frame = ttk.Frame(frame)
status_frame.pack(fill=tk.X, pady=10)
status_label = ttk.Label(status_frame, text="Status:", font=("Segoe UI", 10, "bold"))
status_label.pack(side=tk.LEFT)
status = ttk.Label(status_frame, text="Initializing...", wraplength=500)
status.pack(side=tk.LEFT, padx=5)

# Progress section
progress_frame = ttk.Frame(frame)
progress_frame.pack(fill=tk.X, pady=10)
progress_label = ttk.Label(progress_frame, text="Progress:")
progress_label.pack(anchor="w")
progress = ttk.Progressbar(progress_frame, orient="horizontal", length=550, mode="indeterminate")
progress.pack(fill=tk.X, pady=5)
progress.start()

# Log section
log_frame = ttk.LabelFrame(frame, text="Log")
log_frame.pack(fill=tk.BOTH, expand=True, pady=10)
log = tk.Text(log_frame, height=8, width=70, font=("Consolas", 9))
log.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
log_scrollbar = ttk.Scrollbar(log, command=log.yview)
log.configure(yscrollcommand=log_scrollbar.set)
log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

def add_log(message):
    log.configure(state=tk.NORMAL)
    log.insert(tk.END, message + "\n")
    log.see(tk.END)
    log.configure(state=tk.DISABLED)

add_log("Initializing launcher...")

# Function to launch the app
def launch_app():
    try:
        # Get the WSL directory from command line if provided
        wsl_dir = os.getcwd()
        if len(sys.argv) > 1:
            wsl_dir = sys.argv[1]
        add_log(f"WSL directory: {wsl_dir}")
        
        # Get the distribution name from command line if provided
        wsl_distro = "Ubuntu" # Default
        if len(sys.argv) > 2:
            wsl_distro = sys.argv[2]
        add_log(f"WSL distribution: {wsl_distro}")
        
        status.config(text="Installing/configuring VcXsrv X server...")
        
        # Check if VcXsrv is installed
        import winreg
        vcxsrv_installed = False
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\VcXsrv_is1") as key:
                vcxsrv_path = winreg.QueryValueEx(key, "InstallLocation")[0]
                status.config(text=f"Found VcXsrv at {vcxsrv_path}")
                add_log(f"VcXsrv found at: {vcxsrv_path}")
                vcxsrv_installed = True
        except:
            add_log("VcXsrv registry key not found")
            
            # Try another common registry location
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\VcXsrv_is1") as key:
                    vcxsrv_path = winreg.QueryValueEx(key, "InstallLocation")[0]
                    status.config(text=f"Found VcXsrv at {vcxsrv_path}")
                    add_log(f"VcXsrv found at: {vcxsrv_path}")
                    vcxsrv_installed = True
            except:
                add_log("VcXsrv not found in WOW6432Node registry")
        
        # Try common paths
        if not vcxsrv_installed:
            common_paths = [
                "C:\\Program Files\\VcXsrv\\",
                "C:\\Program Files (x86)\\VcXsrv\\",
                os.path.expandvars("%PROGRAMFILES%\\VcXsrv\\"),
                os.path.expandvars("%PROGRAMFILES(X86)%\\VcXsrv\\"),
            ]
            
            for path in common_paths:
                if os.path.exists(os.path.join(path, "vcxsrv.exe")):
                    vcxsrv_path = path
                    status.config(text=f"Found VcXsrv at {vcxsrv_path}")
                    add_log(f"VcXsrv found at: {vcxsrv_path}")
                    vcxsrv_installed = True
                    break
        
        if not vcxsrv_installed:
            status.config(text="VcXsrv not found. Please download and install VcXsrv")
            add_log("VcXsrv not found. Opening download page...")
            
            # Add install button
            install_frame = ttk.Frame(frame)
            install_frame.pack(pady=10)
            
            def open_download():
                import webbrowser
                webbrowser.open("https://sourceforge.net/projects/vcxsrv/")
                add_log("Download page opened in browser")
            
            install_btn = ttk.Button(install_frame, text="Download VcXsrv", command=open_download)
            install_btn.pack()
            
            # Continue without VcXsrv
            status.config(text="VcXsrv not installed. Will try to run app without X server.")
            vcxsrv_path = None
        
        # If VcXsrv is available, start it
        if vcxsrv_installed:
            status.config(text="Starting VcXsrv X server...")
            add_log("Starting VcXsrv X server...")
            
            # Start XLaunch with a config that disables access control
            try:
                config_dir = os.path.join(os.environ["APPDATA"], "Xlaunch")
                os.makedirs(config_dir, exist_ok=True)
                config_file = os.path.join(config_dir, "config.xlaunch")
                
                # Create a minimal XLaunch config file
                with open(config_file, "w") as f:
                    f.write('''<?xml version="1.0" encoding="UTF-8"?>
<XLaunch xmlns="http://www.straightrunning.com/XmingNotes" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.straightrunning.com/XmingNotes XLaunch.xsd" WindowMode="MultiWindow" ClientMode="NoClient" Display="0" LocalClient="False" RemoteClient="False" NoAccessControl="True" XDMCPTerminate="False" ClipboardPrimary="True"/>''')
                
                # Start XLaunch
                vcxsrv_exe = os.path.join(vcxsrv_path, "vcxsrv.exe")
                add_log(f"Starting VcXsrv: {vcxsrv_exe}")
                subprocess.Popen([vcxsrv_exe, "-run", config_file])
                status.config(text="VcXsrv X server started")
                add_log("VcXsrv started successfully")
                
                # Give X server a moment to start
                import time
                time.sleep(2)
                
            except Exception as e:
                add_log(f"Error starting XLaunch: {str(e)}")
                status.config(text=f"Error starting XLaunch: {str(e)}")
        
        # Set up environment and run the application
        status.config(text="Setting up environment in WSL...")
        add_log("Setting up environment in WSL")
        
        # Get Windows IP address for WSL
        import socket
        windows_ip = socket.gethostbyname(socket.gethostname())
        status.config(text=f"Windows IP for WSL connection: {windows_ip}")
        add_log(f"Windows IP: {windows_ip}")
        
        # Prepare WSL command with multiple DISPLAY attempts
        wsl_command = f"""
cd {wsl_dir} && \\
{{
    # Try with Windows IP
    export DISPLAY={windows_ip}:0 && \\
    export LIBGL_ALWAYS_INDIRECT=1 && \\
    python -c "import tkinter as tk; root=tk.Tk(); root.destroy()" 2>/dev/null && \\
    python MDO.py && \\
    exit 0;
    
    # Try with localhost
    export DISPLAY=localhost:0.0 && \\
    export LIBGL_ALWAYS_INDIRECT=1 && \\
    python -c "import tkinter as tk; root=tk.Tk(); root.destroy()" 2>/dev/null && \\
    python MDO.py && \\
    exit 0;
    
    # Try with :0
    export DISPLAY=:0 && \\
    export LIBGL_ALWAYS_INDIRECT=1 && \\
    python -c "import tkinter as tk; root=tk.Tk(); root.destroy()" 2>/dev/null && \\
    python MDO.py && \\
    exit 0;
    
    # Create a headless fallback version
    echo "All X server attempts failed. Unable to display GUI." && \\
    exit 1;
}}
"""
        
        # Run the command in WSL
        status.config(text="Starting application in WSL...")
        add_log("Starting application in WSL...")
        add_log(f"Executing WSL command: {wsl_command.strip()}")
        
        # Use wsl.exe to run the command
        process = subprocess.Popen(["wsl", "-d", wsl_distro, "-e", "bash", "-c", wsl_command],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        status.config(text="Application started in WSL environment")
        add_log("Application process started")
        progress.stop()
        launch_btn.config(text="Application Running", state="disabled")
        
        # Monitor the process
        def check_process():
            if process.poll() is not None:
                returncode = process.poll()
                stdout, stderr = process.communicate()
                stdout_text = stdout.decode('utf-8', errors='replace')
                stderr_text = stderr.decode('utf-8', errors='replace')
                
                if returncode == 0:
                    status.config(text="Application has exited normally")
                    add_log("Application has exited normally")
                    add_log(stdout_text)
                else:
                    status.config(text=f"Application exited with code {returncode}")
                    add_log(f"Application exited with code {returncode}")
                    add_log("STDOUT: " + stdout_text)
                    add_log("STDERR: " + stderr_text)
                    
                    # Show error dialog
                    messagebox.showerror("Application Error", 
                                       f"The application failed to run properly.\n\n"
                                       f"Error code: {returncode}\n\n"
                                       f"Error: {stderr_text[:200]}...")
                    
                launch_btn.config(text="Launch Application", state="normal")
            else:
                root.after(1000, check_process)
        
        root.after(1000, check_process)
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        status.config(text=f"Error: {str(e)}")
        add_log(f"Error: {str(e)}")
        add_log(error_details)
        progress.stop()
        launch_btn.config(text="Launch Application", state="normal")

# Button section
btn_frame = ttk.Frame(frame)
btn_frame.pack(pady=10)

launch_btn = ttk.Button(btn_frame, text="Launch Application", command=launch_app)
launch_btn.pack(side=tk.LEFT, padx=5)

close_btn = ttk.Button(btn_frame, text="Close", command=root.destroy)
close_btn.pack(side=tk.LEFT, padx=5)

# Alternative options
alt_frame = ttk.LabelFrame(frame, text="Alternative Options")
alt_frame.pack(fill=tk.X, pady=10)

def open_webpage():
    import webbrowser
    webbrowser.open("https://learn.microsoft.com/en-us/windows/wsl/tutorials/gui-apps")
    add_log("Opened WSL GUI apps documentation")

help_btn = ttk.Button(alt_frame, text="WSL GUI Apps Documentation", command=open_webpage)
help_btn.pack(pady=5)

# Automatically launch after a short delay
root.after(1000, launch_app)

# Run the main loop
root.mainloop()
EOL

# Get current directory in Windows path format
WSL_DIR=$(pwd)
WINDOWS_PATH=$(wslpath -w "$WSL_DIR")

echo "WSL directory: $WSL_DIR"
echo "Windows path: $WINDOWS_PATH"

# Get the WSL distribution name
WSL_DISTRO=$(wsl.exe -l -q | head -1 | tr -d '\r')
echo "WSL distribution: $WSL_DISTRO"

# Run the Python script using Windows Python
echo "Launching Windows helper to start X server and run application..."
powershell.exe -Command "cd '$WINDOWS_PATH'; python run_gui_win.py '$WINDOWS_PATH' '$WSL_DISTRO'"

# Clean up the temporary script
rm -f ./run_gui_win.py