#!/usr/bin/env python3
"""
Direct launcher for Intake CFD Optimization Suite
This script launches the application directly in Windows bypassing WSL GUI issues
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import threading
import importlib.util
import time
import traceback

class DirectLauncher:
    def __init__(self, root):
        self.root = root
        self.logs = []
        self.process = None
        self.process_output = ""
        self.process_error = ""
        self.setup_ui()
        
    def setup_ui(self):
        self.root.title("Intake CFD Direct Launcher")
        self.root.geometry("800x600")
        
        # Create a modern style
        style = ttk.Style()
        style.configure("TFrame", background="#f0f0f0")
        style.configure("TButton", font=("Segoe UI", 10))
        style.configure("TLabel", background="#f0f0f0", font=("Segoe UI", 10))
        
        # Header
        header_frame = tk.Frame(self.root, bg="#2C3E50", padx=10, pady=10)
        header_frame.pack(fill=tk.X)
        
        header_label = tk.Label(header_frame, 
                             text="Intake CFD Optimization Suite", 
                             fg="white", bg="#2C3E50",
                             font=("Segoe UI", 16, "bold"))
        header_label.pack()
        
        # Main container
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Control panel
        control_frame = ttk.LabelFrame(main_frame, text="Launch Controls", padding=10)
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Mode selection
        mode_frame = ttk.Frame(control_frame)
        mode_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(mode_frame, text="Launch Mode:").pack(side=tk.LEFT, padx=5)
        
        self.mode_var = tk.StringVar(value="windows")
        ttk.Radiobutton(mode_frame, text="Windows", variable=self.mode_var, 
                      value="windows").pack(side=tk.LEFT, padx=15)
        ttk.Radiobutton(mode_frame, text="WSL (Advanced)", variable=self.mode_var, 
                      value="wsl").pack(side=tk.LEFT, padx=15)
        
        # Demo mode
        demo_frame = ttk.Frame(control_frame)
        demo_frame.pack(fill=tk.X, pady=5)
        
        self.demo_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(demo_frame, text="Demonstration Mode", 
                      variable=self.demo_var).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(demo_frame, text="(Uses mock data and skips external processes)").pack(side=tk.LEFT, padx=5)
        
        # Buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        launch_btn = ttk.Button(button_frame, text="Launch Application", 
                              command=self.launch_application)
        launch_btn.pack(side=tk.LEFT, padx=5)
        
        install_btn = ttk.Button(button_frame, text="Install Dependencies", 
                               command=self.install_dependencies)
        install_btn.pack(side=tk.LEFT, padx=5)
        
        # Log console
        log_frame = ttk.LabelFrame(main_frame, text="Console Output", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.console = scrolledtext.ScrolledText(log_frame, height=20, width=80, 
                                            bg="#212121", fg="#33FF33", 
                                            font=("Consolas", 10))
        self.console.pack(fill=tk.BOTH, expand=True)
        
        # Error details section
        error_frame = ttk.LabelFrame(main_frame, text="Error Details (if any)", padding=10)
        error_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.error_text = scrolledtext.ScrolledText(error_frame, height=6, width=80, 
                                            bg="#FFEEEE", fg="#990000", 
                                            font=("Consolas", 10))
        self.error_text.pack(fill=tk.X)
        
        # Advanced options section
        advanced_frame = ttk.LabelFrame(main_frame, text="Advanced Options", padding=10)
        advanced_frame.pack(fill=tk.X, padx=10, pady=10)
        
        python_frame = ttk.Frame(advanced_frame)
        python_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(python_frame, text="Python Executable:").grid(row=0, column=0, sticky='w')
        
        self.python_path = ttk.Entry(python_frame, width=50)
        self.python_path.grid(row=0, column=1, padx=5)
        self.python_path.insert(0, sys.executable)
        
        ttk.Button(python_frame, text="Browse", 
                 command=self.browse_python).grid(row=0, column=2)
        
        debug_frame = ttk.Frame(advanced_frame)
        debug_frame.pack(fill=tk.X, pady=5)
        
        self.debug_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(debug_frame, text="Run in Debug Mode (-v verbose imports)", 
                      variable=self.debug_var).pack(anchor='w')
        
        # Alternative launch buttons
        alt_frame = ttk.Frame(button_frame)
        alt_frame.pack(side=tk.TOP, fill=tk.X, pady=5)
        
        ttk.Button(alt_frame, text="Launch with GUI Diagnostics", 
                 command=self.launch_with_diagnostics).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(alt_frame, text="Launch WSL Helper", 
                 command=self.launch_wsl_helper).pack(side=tk.LEFT, padx=5)
        
        # Support materials
        support_frame = ttk.LabelFrame(main_frame, text="Troubleshooting", padding=10)
        support_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(support_frame, text="Check GUI Environment", 
                command=self.run_gui_diagnostics).pack(side=tk.LEFT, padx=5)
                
        ttk.Button(support_frame, text="Setup Environment", 
                command=self.setup_environment).pack(side=tk.LEFT, padx=5)
                
        ttk.Button(support_frame, text="View Error Log", 
                command=self.view_error_log).pack(side=tk.LEFT, padx=5)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.progress = ttk.Progressbar(status_frame, mode="indeterminate", length=400)
        self.progress.pack(side=tk.LEFT, padx=10, pady=5, fill=tk.X, expand=True)
        
        status_label = ttk.Label(status_frame, textvariable=self.status_var)
        status_label.pack(side=tk.RIGHT, padx=10, pady=5)
        
        # Initial log
        self.log("Intake CFD Direct Launcher initialized")
        self.log(f"System: {os.name}")
        self.log(f"Python: {sys.version}")
        
        # Check dependencies
        self.check_dependencies()
        
    def log(self, message):
        """Add a message to the log console"""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.logs.append(log_entry)
        
        # Add to UI console
        self.console.insert(tk.END, log_entry + "\n")
        self.console.see(tk.END)
        self.root.update_idletasks()
        
    def set_status(self, message, progress=False):
        """Update status bar"""
        self.status_var.set(message)
        if progress:
            self.progress.start()
        else:
            self.progress.stop()
        self.root.update_idletasks()
        
    def check_dependencies(self):
        """Check if required dependencies are installed"""
        self.log("Checking dependencies...")
        missing = []
        
        # Check core packages
        for package in ["numpy", "pandas", "matplotlib", "openmdao", "PIL", "scipy"]:
            try:
                importlib.import_module(package)
                self.log(f"✓ {package} is installed")
            except ImportError:
                self.log(f"✗ {package} is not installed")
                missing.append(package)
        
        # Report findings
        if missing:
            self.log(f"\nMissing dependencies: {', '.join(missing)}")
            self.log("Please click 'Install Dependencies' to install them")
            self.set_status("Dependencies missing")
        else:
            self.log("\nAll dependencies are installed")
            self.set_status("Ready")
            
    def install_dependencies(self):
        """Install required dependencies"""
        self.log("Installing dependencies...")
        self.set_status("Installing dependencies...", progress=True)
        
        # Create a thread to handle the installation
        def install_thread():
            try:
                # Basic dependencies
                dependencies = [
                    "numpy", "pandas", "matplotlib", "openmdao", "pillow", 
                    "scipy", "tk"
                ]
                
                # Install each dependency
                for dep in dependencies:
                    cmd = [sys.executable, "-m", "pip", "install", dep]
                    self.log(f"Running: {' '.join(cmd)}")
                    
                    proc = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True
                    )
                    
                    # Show output
                    for line in proc.stdout:
                        self.log(line.strip())
                        
                    proc.wait()
                    
                    if proc.returncode != 0:
                        self.log(f"Error installing {dep}")
                    else:
                        self.log(f"Successfully installed {dep}")
                
                self.log("All dependencies installed successfully")
                self.root.after(0, lambda: self.set_status("Dependencies installed", progress=False))
                
            except Exception as e:
                self.log(f"Error installing dependencies: {str(e)}")
                self.root.after(0, lambda: self.set_status("Installation failed", progress=False))
        
        # Start the installation thread
        threading.Thread(target=install_thread).start()
    
    def browse_python(self):
        """Browse for a Python executable"""
        from tkinter import filedialog
        filename = filedialog.askopenfilename(
            title="Select Python Executable",
            filetypes=[("Executable files", "*.exe"), ("All files", "*.*")]
        )
        if filename:
            self.python_path.delete(0, tk.END)
            self.python_path.insert(0, filename)
    
    def launch_with_diagnostics(self):
        """Launch with GUI diagnostics first"""
        self.log("Running GUI diagnostics before launch...")
        self.set_status("Running diagnostics...", progress=True)
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        diagnostics_script = os.path.join(script_dir, "gui_diagnostics.py")
        
        # Ensure the diagnostics script exists
        if not os.path.exists(diagnostics_script):
            with open(diagnostics_script, "w") as f:
                f.write("""#!/usr/bin/env python3
import sys
import tkinter as tk
from tkinter import messagebox
import platform
import os

def check_display():
    print(f"DISPLAY variable: {os.environ.get('DISPLAY', 'Not set')}")
    return os.environ.get('DISPLAY') is not None

def check_tk():
    try:
        root = tk.Tk()
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        print(f"Screen dimensions: {screen_width}x{screen_height}")
        root.destroy()
        return True
    except Exception as e:
        print(f"Tk error: {e}")
        return False

def main():
    print("GUI Diagnostics Tool")
    print(f"Python version: {sys.version}")
    print(f"Platform: {platform.platform()}")
    
    display_ok = check_display()
    tk_ok = check_tk()
    
    if display_ok and tk_ok:
        print("GUI environment looks good!")
        return 0
    else:
        if not display_ok:
            print("DISPLAY variable not set correctly")
        if not tk_ok:
            print("Tkinter not working properly")
        return 1

if __name__ == "__main__":
    sys.exit(main())
""")
            self.log("Created GUI diagnostics script")
        
        # Run the diagnostics
        try:
            python_exe = self.python_path.get()
            process = subprocess.run(
                [python_exe, diagnostics_script],
                capture_output=True,
                text=True
            )
            
            self.log("Diagnostics output:")
            for line in process.stdout.splitlines():
                self.log(f"  {line}")
            
            if process.returncode == 0:
                self.log("Diagnostics passed! Launching application...")
                self.launch_application()
            else:
                self.log("Diagnostics failed. See error output.")
                self.error_text.delete(1.0, tk.END)
                self.error_text.insert(tk.END, process.stderr)
                self.set_status("Diagnostics failed", progress=False)
        except Exception as e:
            self.log(f"Error running diagnostics: {str(e)}")
            self.error_text.delete(1.0, tk.END)
            self.error_text.insert(tk.END, traceback.format_exc())
            self.set_status("Error", progress=False)
    
    def launch_wsl_helper(self):
        """Launch the WSL helper script"""
        self.log("Launching WSL GUI helper...")
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        helper_script = os.path.join(script_dir, "run_gui_wsl.sh")
        
        if os.path.exists(helper_script):
            try:
                # On Windows
                if os.name == 'nt':
                    process = subprocess.Popen(
                        ["wsl", "bash", helper_script],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True
                    )
                    
                    # Start a thread to monitor the output
                    def monitor_output():
                        for line in iter(process.stdout.readline, ""):
                            self.log(line.strip())
                        process.wait()
                        self.log(f"Helper exited with code: {process.returncode}")
                        
                    threading.Thread(target=monitor_output, daemon=True).start()
                else:
                    # In WSL
                    os.chmod(helper_script, 0o755)  # Ensure it's executable
                    subprocess.Popen(
                        ["bash", helper_script],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT
                    )
                    self.log("WSL helper launched in a separate window")
            except Exception as e:
                self.log(f"Error launching WSL helper: {str(e)}")
                self.error_text.delete(1.0, tk.END)
                self.error_text.insert(tk.END, traceback.format_exc())
        else:
            self.log(f"WSL helper script not found at: {helper_script}")
            self.log("Please make sure run_gui_wsl.sh exists")
    
    def run_gui_diagnostics(self):
        """Run GUI environment diagnostics"""
        self.log("Checking GUI environment...")
        
        # Create a detailed report
        report = []
        report.append(f"Python Version: {sys.version}")
        report.append(f"Platform: {sys.platform}")
        report.append(f"Operating System: {os.name}")
        
        # Check DISPLAY variable
        display = os.environ.get('DISPLAY', 'Not set')
        report.append(f"DISPLAY Environment Variable: {display}")
        
        # Check if WSL
        is_wsl = False
        if os.path.exists('/proc/version'):
            try:
                with open('/proc/version', 'r') as f:
                    if 'microsoft' in f.read().lower():
                        is_wsl = True
            except:
                pass
        report.append(f"Running in WSL: {'Yes' if is_wsl else 'No'}")
        
        # Check tkinter
        try:
            import tkinter as tk
            report.append(f"Tkinter Version: {tk.TkVersion}")
            
            # Try to create a root window
            try:
                root = tk.Tk()
                screen_width = root.winfo_screenwidth()
                screen_height = root.winfo_screenheight()
                report.append(f"Screen Dimensions: {screen_width}x{screen_height}")
                root.destroy()
                report.append("Tkinter GUI Creation: Success")
            except Exception as e:
                report.append(f"Tkinter GUI Creation: Failed - {str(e)}")
        except ImportError:
            report.append("Tkinter: Not installed or not working")
        
        # Check matplotlib
        try:
            import matplotlib
            report.append(f"Matplotlib Version: {matplotlib.__version__}")
            report.append(f"Matplotlib Backend: {matplotlib.get_backend()}")
        except ImportError:
            report.append("Matplotlib: Not installed")
        except Exception as e:
            report.append(f"Matplotlib Error: {str(e)}")
        
        # Check required packages
        for package in ["numpy", "pandas", "openmdao", "PIL", "scipy"]:
            try:
                module = importlib.import_module(package)
                if hasattr(module, '__version__'):
                    report.append(f"{package} Version: {module.__version__}")
                else:
                    report.append(f"{package}: Installed (version unknown)")
            except ImportError:
                report.append(f"{package}: Not installed")
            except Exception as e:
                report.append(f"{package} Error: {str(e)}")
        
        # Display the report
        self.error_text.delete(1.0, tk.END)
        self.error_text.insert(tk.END, "\n".join(report))
        
        for line in report:
            self.log(line)
            
        # Save the report
        try:
            with open("gui_diagnostics_report.txt", "w") as f:
                f.write("\n".join(report))
            self.log("Report saved to gui_diagnostics_report.txt")
        except:
            pass
            
        self.set_status("Diagnostics complete", progress=False)
    
    def setup_environment(self):
        """Run environment setup script"""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        setup_script = os.path.join(script_dir, "setup_environment.sh")
        
        if os.path.exists(setup_script):
            self.log("Running environment setup script...")
            self.set_status("Setting up environment...", progress=True)
            
            try:
                # Make sure script is executable
                os.chmod(setup_script, 0o755)
                
                if os.name == 'nt':  # Windows
                    process = subprocess.Popen(
                        ["wsl", "bash", setup_script],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True
                    )
                else:  # Linux/WSL
                    process = subprocess.Popen(
                        ["bash", setup_script],
                        stdout=subprocess.PIPE, 
                        stderr=subprocess.STDOUT,
                        text=True
                    )
                
                # Monitor output
                for line in iter(process.stdout.readline, ""):
                    self.log(line.strip())
                
                process.wait()
                self.log(f"Setup completed with code: {process.returncode}")
                self.set_status("Setup completed", progress=False)
            except Exception as e:
                self.log(f"Error during setup: {str(e)}")
                self.error_text.delete(1.0, tk.END)
                self.error_text.insert(tk.END, traceback.format_exc())
                self.set_status("Setup failed", progress=False)
        else:
            self.log(f"Setup script not found at: {setup_script}")
            self.set_status("Setup script not found", progress=False)
    
    def view_error_log(self):
        """View error log file"""
        log_files = ["error_log.txt", "command_log.txt"]
        combined_log = ""
        
        for log_file in log_files:
            if os.path.exists(log_file):
                try:
                    with open(log_file, "r") as f:
                        content = f.read()
                        combined_log += f"=== {log_file} ===\n{content}\n\n"
                except Exception as e:
                    combined_log += f"Error reading {log_file}: {str(e)}\n"
            else:
                combined_log += f"{log_file} does not exist\n\n"
        
        if not combined_log:
            combined_log = "No log files found."
        
        self.error_text.delete(1.0, tk.END)
        self.error_text.insert(tk.END, combined_log)
    
    def launch_application(self):
        """Launch the application based on selected mode"""
        mode = self.mode_var.get()
        demo = self.demo_var.get()
        
        self.log(f"Launching application in {mode} mode")
        self.log(f"Demo mode: {'enabled' if demo else 'disabled'}")
        self.set_status("Launching application...", progress=True)
        
        # Create mock files if in demo mode
        if demo:
            self.create_mock_files()
        
        # Get the script directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Launch thread
        def launch_thread():
            try:
                if mode == "windows":
                    # Direct mode - running directly in Windows Python
                    self.log("Launching application directly in Windows Python")
                    
                    # Set environment variables
                    env = os.environ.copy()
                    env["DEMO_MODE"] = "1" if demo else "0"
                    
                    # Get Python executable path
                    python_exe = self.python_path.get()
                    if not os.path.exists(python_exe):
                        self.log(f"Warning: Python executable not found at '{python_exe}', falling back to system Python")
                        python_exe = "python"  # Fallback to system default
                    
                    # In Windows mode, launch MDO.py directly with optional verbose mode
                    cmd = [python_exe]
                    if self.debug_var.get():
                        cmd.append("-v")  # Add verbose flag for debugging imports
                    cmd.append(os.path.join(script_dir, "MDO.py"))
                    
                    self.log(f"Running command: {' '.join(cmd)}")
                    
                    # Clear previous output
                    self.process_output = ""
                    self.process_error = ""
                    
                    self.process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        env=env
                    )
                    
                    # Use separate threads to monitor stdout and stderr
                    def monitor_stdout():
                        for line in iter(self.process.stdout.readline, ""):
                            self.log(line.strip())
                            self.process_output += line
                    
                    def monitor_stderr():
                        for line in iter(self.process.stderr.readline, ""):
                            self.log(f"ERROR: {line.strip()}")
                            self.process_error += line
                            # Show errors in the error text widget
                            self.root.after(0, lambda: self.error_text.insert(tk.END, line))
                    
                    stdout_thread = threading.Thread(target=monitor_stdout)
                    stderr_thread = threading.Thread(target=monitor_stderr)
                    stdout_thread.daemon = True
                    stderr_thread.daemon = True
                    stdout_thread.start()
                    stderr_thread.start()
                    
                    # Wait for the process to complete in this thread
                    self.process.wait()
                    
                    # Make sure threads complete
                    stdout_thread.join(timeout=2)
                    stderr_thread.join(timeout=2)
                    
                    # Check exit code
                    returncode = self.process.returncode
                    self.log(f"Application exited with code: {returncode}")
                    
                    if returncode != 0:
                        self.root.after(0, lambda: self.show_error_details(returncode))
                    else:
                        self.root.after(0, lambda: self.set_status("Application completed successfully", progress=False))
                    
                else:
                    # WSL mode
                    if self.is_wsl():
                        # We're already in WSL, so just run the script
                        self.log("Already in WSL, running MDO.py directly")
                        
                        # Set environment variables
                        env = os.environ.copy()
                        env["DEMO_MODE"] = "1" if demo else "0"
                        env["DISPLAY"] = ":0"
                        env["LIBGL_ALWAYS_INDIRECT"] = "1"
                        
                        cmd = [sys.executable, os.path.join(script_dir, "MDO.py")]
                        self.process = subprocess.Popen(
                            cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            text=True,
                            env=env
                        )
                        
                        # Monitor output
                        for line in iter(self.process.stdout.readline, ""):
                            self.log(line.strip())
                            
                        self.process.wait()
                        self.log(f"Application exited with code: {self.process.returncode}")
                    else:
                        # We're in Windows, need to run in WSL
                        self.log("Running in WSL mode from Windows")
                        self.log("This requires WSL to be installed with Python")
                        
                        # Try to run with wsl command
                        cmd = ["wsl", "cd", script_dir, "&&", 
                              "DISPLAY=:0", "LIBGL_ALWAYS_INDIRECT=1",
                              "python3", "MDO.py"]
                        
                        self.log(f"Running command: {' '.join(cmd)}")
                        self.process = subprocess.Popen(
                            cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            text=True
                        )
                        
                        # Monitor output
                        for line in iter(self.process.stdout.readline, ""):
                            self.log(line.strip())
                            
                        self.process.wait()
                        self.log(f"Application exited with code: {self.process.returncode}")
                        
                # Update status when done
                self.root.after(0, lambda: self.set_status("Execution completed", progress=False))
                
            except Exception as e:
                self.log(f"Error launching application: {str(e)}")
                self.root.after(0, lambda: self.set_status("Launch failed", progress=False))
                self.root.after(0, lambda: self.error_text.insert(tk.END, traceback.format_exc()))
        
        # Start the launch thread
        threading.Thread(target=launch_thread).start()
    
    def show_error_details(self, returncode):
        """Show detailed error information"""
        self.set_status(f"Application failed with code {returncode}", progress=False)
        
        error_details = f"Application exited with code: {returncode}\n\n"
        
        if self.process_error:
            error_details += "=== ERROR OUTPUT ===\n"
            error_details += self.process_error
            error_details += "\n\n"
        
        if "Traceback" in self.process_output:
            error_details += "=== TRACEBACK IN STDOUT ===\n"
            # Extract traceback from output
            lines = self.process_output.splitlines()
            in_traceback = False
            for line in lines:
                if line.strip().startswith("Traceback"):
                    in_traceback = True
                if in_traceback:
                    error_details += line + "\n"
        
        # Clear and update error text
        self.error_text.delete(1.0, tk.END)
        self.error_text.insert(tk.END, error_details)
        
        # Log the error to file
        try:
            with open("app_error_details.log", "w") as f:
                f.write(error_details)
            self.log("Error details saved to app_error_details.log")
        except:
            pass
        
        # Suggest possible solutions
        if "ModuleNotFoundError" in error_details:
            self.log("Suggestion: Missing dependency. Try clicking 'Install Dependencies'")
        elif "ImportError" in error_details:
            self.log("Suggestion: Import error. Try installing/reinstalling dependencies")
        elif "tkinter" in error_details.lower() or "_tkinter" in error_details.lower():
            self.log("Suggestion: Tkinter issue. Make sure tkinter is properly installed")
            if "DISPLAY" in error_details:
                self.log("Suggestion: DISPLAY environment variable issue detected. Try the WSL helper")
        elif "DISPLAY" in error_details:
            self.log("Suggestion: X11 display issue. Try launching the WSL Helper")
    
    def create_mock_files(self):
        """Create necessary mock files for demonstration mode"""
        self.log("Setting up demonstration mode...")
        
        try:
            # Create mock executables
            with open("gmsh_process", "w") as f:
                f.write("#!/bin/bash\necho 'Mock gmsh_process running...'\n")
            os.chmod("gmsh_process", 0o755)
            
            with open("cfd_solver", "w") as f:
                f.write("#!/bin/bash\necho 'Mock CFD solver running...'\n")
            os.chmod("cfd_solver", 0o755)
            
            with open("process_results", "w") as f:
                f.write("#!/bin/bash\necho 'Mock results processor running...'\n")
            os.chmod("process_results", 0o755)
            
            # Create mock result directories and files
            os.makedirs("cfd_results", exist_ok=True)
            
            with open("cfd_results/pressure.dat", "w") as f:
                f.write("0.123\n")
                
            self.log("Mock files created successfully")
        except Exception as e:
            self.log(f"Error creating mock files: {str(e)}")
    
    def is_wsl(self):
        """Check if running in WSL"""
        if os.name == 'posix':
            with open('/proc/version', 'r') as f:
                if 'microsoft' in f.read().lower():
                    return True
        return False

def main():
    root = tk.Tk()
    app = DirectLauncher(root)
    root.mainloop()

if __name__ == "__main__":
    main()
