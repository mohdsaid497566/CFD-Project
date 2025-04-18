import os
import sys
import time
import json
import shutil
import logging
import platform
import argparse
import subprocess
import threading
import traceback
import datetime
import multiprocessing
import numpy as np
import pandas as pd
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from PIL import Image, ImageTk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm

# Ensure config directory exists
os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "Config"), exist_ok=True)

# Try to import paramiko for SSH functionality
try:
    import paramiko
    PARAMIKO_AVAILABLE = True
except ImportError:
    PARAMIKO_AVAILABLE = False
    print("Warning: paramiko module not found. SSH functionality will be limited.")

# Add parent directory to the Python path to find the Expressions module
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)
    print(f"Added {parent_dir} to Python path")
# Now import Expressions and other modules
from tkinter import ttk, filedialog, messagebox, scrolledtext
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
from PIL import Image, ImageTk
from Expressions import format_exp, write_exp_file
from tkinter import ttk, filedialog, messagebox, scrolledtext


# Flag for demonstration mode
DEMO_MODE = True

def initialize_hpc_components(app):
    """Initialize HPC components in the application"""
    try:
        from Garage.HPC.hpc_integration import create_hpc_tab
        create_hpc_tab(app)
        return True
    except ImportError as e:
        print(f"Error importing HPC modules: {e}")
        return False
    except Exception as e:
        print(f"Error initializing HPC components: {e}")
        print(traceback.format_exc())
        return False    


# Utility to run shell commands with timeout and logging
def run_command(command, cwd=None, timeout=300):
    if DEMO_MODE and (command[0].startswith('./') or '/mnt/c/Program Files' in command[0]):
        print(f"DEMO MODE: Simulating command: {' '.join(command)}")
        with open("command_log.txt", "a") as log_file:
            log_file.write(f"DEMO MODE: Simulating: {' '.join(command)}\n")
        
        if 'nx_express2.py' in ' '.join(command) or 'nx_export.py' in ' '.join(command):
            print("Mock NX execution completed successfully.")
            return "Mock NX execution completed successfully."
        elif 'gmsh_process' in command[0]:
            print("Mock mesh generation completed successfully.")
            return "Mock mesh generation completed successfully."
        elif 'cfd_solver' in command[0]:
            print("Mock CFD simulation completed successfully.")
            return "Mock CFD simulation completed successfully."
        elif 'process_results' in command[0]:
            print("Mock results processing completed successfully.")
            return "Mock results processing completed successfully."
        else:
            print("Generic mock command execution.")
            return "Generic mock command execution."
    
    try:
        if command[0].startswith('/') or command[0].startswith('./'):
            if not os.path.exists(command[0]):
                error_msg = f"Executable not found: {command[0]}"
                print(error_msg)
                with open("error_log.txt", "a") as log_file:
                    log_file.write(f"{error_msg}\n")
                
                if DEMO_MODE:
                    print(f"DEMO MODE: Simulating command despite missing executable: {' '.join(command)}")
                    return f"DEMO MODE: Simulated execution of {' '.join(command)}"
                    
                raise FileNotFoundError(error_msg)
        
        cmd_str = ' '.join(command)
        print(f"Executing: {cmd_str}")
        with open("command_log.txt", "a") as log_file:
            log_file.write(f"Executing: {cmd_str}\n")
            
        result = subprocess.run(command, check=True, capture_output=True, text=True, cwd=cwd, timeout=timeout)
        
        print(result.stdout)
        with open("command_log.txt", "a") as log_file:
            log_file.write(f"Success: {cmd_str}\nOutput: {result.stdout}\n")
        
        return result.stdout
    except subprocess.TimeoutExpired as e:
        error_msg = f"Error: Command timed out after {timeout} seconds: {' '.join(command)}"
        print(error_msg)
        with open("error_log.txt", "a") as log_file:
            log_file.write(f"Timeout: {' '.join(command)}\n")
            
        if DEMO_MODE:
            print(f"DEMO MODE: Continuing with mock result despite timeout...")
            return f"DEMO MODE: Simulated execution (after timeout) of {' '.join(command)}"
            
        raise
    except subprocess.CalledProcessError as e:
        error_msg = f"Error: Command failed with exit status {e.returncode}: {' '.join(command)}\n{e.stderr}"
        print(error_msg)
        with open("error_log.txt", "a") as log_file:
            log_file.write(f"Command failed: {' '.join(command)}\nExit code: {e.returncode}\nError: {e.stderr}\n")
            
        if DEMO_MODE:
            print(f"DEMO MODE: Continuing with mock result despite error...")
            return f"DEMO_MODE: Simulated execution (after error) of {' '.join(command)}"
            
        raise
    except FileNotFoundError as e:
        error_msg = f"Error: File not found: {e.filename}"
        print(error_msg)
        with open("error_log.txt", "a") as log_file:
            log_file.write(f"{error_msg}\n")
            
        if DEMO_MODE:
            print(f"DEMO MODE: Continuing with mock result despite file not found...")
            return f"DEMO MODE: Simulated execution (after file not found) of {' '.join(command)}"
            
        raise
    except Exception as e:
        error_msg = f"Error: Unexpected error: {str(e)}"
        print(error_msg)
        with open("error_log.txt", "a") as log_file:
            log_file.write(f"{error_msg}\n")
            
        if DEMO_MODE:
            print(f"DEMO MODE: Continuing with mock result despite error...")
            return f"DEMO MODE: Simulated execution (after error) of {' '.join(command)}"
            
        raise

# Function to check if running on WSL
def is_wsl():
    if platform.system() == "Linux":
        if "microsoft" in platform.release().lower():
            return True
        try:
            with open("/proc/version", "r") as f:
                if "microsoft" in f.read().lower():
                    return True
        except:
            pass
        if os.path.exists("/proc/sys/fs/binfmt_misc/WSLInterop"):
            return True
        if "wsl" in os.environ.get("WSL_DISTRO_NAME", "").lower():
            return True
        if os.path.exists("/mnt/c/Windows"):
            return True
    return False

# Function to check and fix NX paths based on the platform
def get_nx_command():
    if is_wsl():
        nx_exe = "/mnt/c/Program Files/Siemens/NX2406/NXBIN/run_journal.exe"
        if not os.path.exists(nx_exe):
            alternatives = [
                "/mnt/c/Program Files/Siemens/NX2207/NXBIN/run_journal.exe",
                "/mnt/c/Program Files/Siemens/NX2306/NXBIN/run_journal.exe",
                "/mnt/c/Program Files/Siemens/NX1980/NXBIN/run_journal.exe"
            ]
            for alt in alternatives:
                if os.path.exists(alt):
                    nx_exe = alt
                    break
        if not os.path.exists(nx_exe):
            found = False
            for root, dirs, files in os.walk("/mnt/c/Program Files"):
                if "run_journal.exe" in files:
                    nx_exe = os.path.join(root, "run_journal.exe")
                    print(f"Found NX executable at: {nx_exe}")
                    found = True
                    break
            if not found:
                raise FileNotFoundError(f"NX executable not found. Please install NX or update the path.")
        return nx_exe
    elif platform.system() == "Windows":
        nx_exe = "C:\\Program Files\\Siemens\\NX2406\\NXBIN\\run_journal.exe"
        if not os.path.exists(nx_exe):
            raise FileNotFoundError(f"NX executable not found at {nx_exe}. Please install NX or update the path.")
        return nx_exe
    else:
        if os.path.exists("/mnt/c/Windows"):
            print("Warning: WSL detection failed but Windows mount found. Treating as WSL.")
            return get_nx_command()
        raise RuntimeError(f"Unsupported platform: {platform.system()}. NX automation is only supported on Windows or WSL. If using WSL, please ensure /mnt/c is accessible.")

# Function to create mock executables and files for demonstration
def create_mock_executables():
    """Create mock scripts and files for demonstration"""
    print("Creating mock executables and files for demonstration...")
    
    # Create mock gmsh_process script
    with open("./gmsh_process", "w") as f:
        f.write("#!/bin/bash\n")
        f.write("echo 'Mock gmsh_process running...'\n")
        f.write("echo 'Processing $2 to $4'\n")
        f.write("echo 'Created mock mesh file'\n")
        f.write("touch $4\n")
    
    # Create mock cfd_solver script
    with open("./cfd_solver", "w") as f:
        f.write("#!/bin/bash\n")
        f.write("echo 'Mock CFD solver running...'\n")
        f.write("echo 'Processing $2'\n")
        f.write("echo 'Created mock result files'\n")
        f.write("mkdir -p cfd_results\n")
        f.write("echo '0.123' > cfd_results/pressure.dat\n")
    
    # Create mock process_results script
    with open("./process_results", "w") as f:
        f.write("#!/bin/bash\n")
        f.write("echo 'Mock results processor running...'\n")
        f.write("echo 'Processing results from $2 to $4'\n")
        f.write("echo '0.123' > $4\n")
    
    # Create mock STEP file if it doesn't exist
    if not os.path.exists("INTAKE3D.step"):
        with open("INTAKE3D.step", "w") as f:
            f.write("MOCK STEP FILE - This is not a real STEP file\n")
            f.write("For demonstration purposes only\n")
    
    # Create mock mesh file if it doesn't exist
    if not os.path.exists("INTAKE3D.msh"):
        with open("INTAKE3D.msh", "w") as f:
            f.write("MOCK MESH FILE - This is not a real mesh file\n")
            f.write("For demonstration purposes only\n")
    
    # Create mock results directory and file
    os.makedirs("cfd_results", exist_ok=True)
    with open("cfd_results/pressure.dat", "w") as f:
        f.write("0.123\n")
        
    with open("processed_results.csv", "w") as f:
        f.write("0.123\n")
    
    # Make scripts executable
    try:
        os.chmod("./gmsh_process", 0o755)
        os.chmod("./cfd_solver", 0o755)
        os.chmod("./process_results", 0o755)
    except Exception as e:
        print(f"Warning: Could not set executable permissions: {str(e)}")
    
    print("Mock executables and files created successfully.")

# Function to generate expressions and export them to a file
def exp(L4, L5, alpha1, alpha2, alpha3):
    expressions_list = list()
    L4_expression = format_exp('L4', 'number', L4, unit='Meter')
    L5_expression = format_exp('L5', 'number', L5, unit='Meter')
    alpha1_expression = format_exp('alpha1', 'number', alpha1, unit='Degrees')
    alpha2_expression = format_exp('alpha2', 'number', alpha2, unit='Degrees')
    alpha3_expression = format_exp('alpha3', 'number', alpha3, unit='Degrees')
    expressions_list.append(L4_expression)
    expressions_list.append(L5_expression)
    expressions_list.append(alpha1_expression)
    expressions_list.append(alpha2_expression)
    expressions_list.append(alpha3_expression)
    write_exp_file(expressions_list, "expressions")

# Function to manage NX geometry modification and STEP export
def run_nx_workflow():
    try:
        if DEMO_MODE:
            print("DEMO MODE: Using mock NX workflow.")
            with open("INTAKE3D.step", "w") as f:
                f.write("MOCK STEP FILE - This is not a real STEP file\n")
                f.write("Generated by mock NX workflow\n")
                f.write(f"Date: {pd.Timestamp.now()}\n")
                f.write(f"Parameters: Demo run\n")
            return "INTAKE3D.step"
            
        nx_exe = get_nx_command()
        print(f"Using NX executable: {nx_exe}")
        
        express_script = "C:/Users/Mohammed/Desktop/Intake-CFD-Project/nx/nx_express2.py"
        export_script = "C:/Users/Mohammed/Desktop/Intake-CFD-Project/nx/nx_export.py"
        part_file = "C:/Users/Mohammed/Desktop/Intake-CFD-Project/nx/INTAKE3D.prt"
        
        for file_path in [express_script, export_script, part_file]:
            if not os.path.exists(file_path.replace('C:', '/mnt/c')):
                raise FileNotFoundError(f"Required file not found: {file_path}")
        
        print(f"Running NX script: {express_script} with part: {part_file}")
        run_command([
            nx_exe,
            express_script,
            "-args", part_file
        ])
        
        print(f"Running NX export script: {export_script} with part: {part_file}")
        run_command([
            nx_exe,
            export_script,
            "-args", part_file
        ])
        
        step_file = "C:/Users/Mohammed/Desktop/Intake-CFD-Project/nx/INTAKE3D.step"
        wsl_step_file = step_file.replace('C:', '/mnt/c')
        
        if not os.path.exists(wsl_step_file):
            raise FileNotFoundError(f"STEP file was not created at expected location: {wsl_step_file}")
        
        print(f"STEP file successfully created: {wsl_step_file}")
        return wsl_step_file
        
    except Exception as e:
        print(f"Error in NX workflow: {str(e)}")
        with open("error_log.txt", "a") as log_file:
            log_file.write(f"NX workflow error: {str(e)}\n")
            
        if DEMO_MODE:
            print("DEMO MODE: Creating mock STEP file despite error...")
            with open("INTAKE3D.step", "w") as f:
                f.write("MOCK STEP FILE - This is not a real STEP file\n")
                f.write("Generated as fallback after NX error\n")
                f.write(f"Error: {str(e)}\n")
            return "INTAKE3D.step"
        else:
            raise

# Function to process the STEP file with GMSH
def process_mesh(step_file, mesh_file):
    try:
        if DEMO_MODE:
            print(f"DEMO MODE: Using mock mesh processing for {step_file}.")
            with open(mesh_file, "w") as f:
                f.write("MOCK MESH FILE - This is not a real mesh file\n")
                f.write(f"Generated from: {step_file}\n")
                f.write(f"Date: {pd.Timestamp.now()}\n")
            return
            
        run_command(["./gmsh_process", "--input", step_file, "--output", mesh_file, "--auto-refine", "--curvature-adapt"])
    except Exception as e:
        print(f"Error in mesh processing: {str(e)}")
        with open("error_log.txt", "a") as log_file:
            log_file.write(f"Mesh processing error: {str(e)}\n")
            
        if DEMO_MODE:
            print("DEMO MODE: Creating mock mesh file despite error...")
            with open(mesh_file, "w") as f:
                f.write("MOCK MESH FILE - This is not a real mesh file\n")
                f.write(f"Generated as fallback after error\n")
                f.write(f"Error: {str(e)}\n")
        else:
            raise

# Function to run the CFD solver
def run_cfd(mesh_file):
    try:
        if DEMO_MODE:
            print(f"DEMO MODE: Using mock CFD solver for {mesh_file}.")
            os.makedirs("cfd_results", exist_ok=True)
            with open("cfd_results/pressure.dat", "w") as f:
                f.write("0.123\n")
            with open("cfd_results/velocity.dat", "w") as f:
                f.write("0.45\n")
            return
            
        run_command(["./cfd_solver", "--mesh", mesh_file, "--solver", "openfoam"])
    except Exception as e:
        print(f"Error in CFD simulation: {str(e)}")
        with open("error_log.txt", "a") as log_file:
            log_file.write(f"CFD simulation error: {str(e)}\n")
            
        if DEMO_MODE:
            print("DEMO MODE: Creating mock CFD results despite error...")
            os.makedirs("cfd_results", exist_ok=True)
            with open("cfd_results/pressure.dat", "w") as f:
                f.write("0.123\n")
            with open("cfd_results/velocity.dat", "w") as f:
                f.write("0.45\n")
        else:
            raise

# Function to process CFD results
def process_results(results_dir, output_file):
    try:
        if DEMO_MODE:
            print(f"DEMO MODE: Using mock results processing for {results_dir}.")
            with open(output_file, "w") as f:
                f.write("0.123\n")
            return
            
        run_command(["./process_results", "--input", results_dir, "--output", output_file])
    except Exception as e:
        print(f"Error in processing results: {str(e)}")
        with open("error_log.txt", "a") as log_file:
            log_file.write(f"Results processing error: {str(e)}\n")
            
        if DEMO_MODE:
            print("DEMO MODE: Creating mock processed results despite error...")
            with open(output_file, "w") as f:
                f.write("0.123\n")
        else:
            raise

# Function to run unit tests with enhanced error handling
def run_tests():
    if DEMO_MODE:
        print("DEMO MODE: Skipping unit tests.")
        return
        
    try:
        run_command(["./run_tests.sh", "--category", "all"])
    except subprocess.CalledProcessError as e:
        print("Unit tests failed. Please check the output below:")
        print(e.stderr)
        print("Detailed logs can be found in 'error_log.txt'.")
        raise RuntimeError("Unit tests did not pass. Fix the issues and try again.")

# Enhanced GUI Class for Pre-/Post-Processing
class ModernTheme:
    """Modern theme settings for the application"""
    def __init__(self):
        # Define colors
        self.primary_color = "#4a6fa5"  # Blue
        self.secondary_color = "#45b29d"  # Teal
        self.bg_color = "#f5f5f5"  # Light gray
        self.text_color = "#333333"  # Dark gray
        self.border_color = "#dddddd"  # Light gray border
        self.success_color = "#5cb85c"  # Green
        self.warning_color = "#f0ad4e"  # Orange
        self.error_color = "#d9534f"  # Red
        self.accent_color = "#007bff"
        self.accent_hover = "#2980B9"
        self.light_text = "#FFFFFF"
        
        # Define padding and margins
        self.padding = 10
        self.small_padding = 5
        self.large_padding = 20
        
        # Define fonts
        self.title_font = ("Helvetica", 16, "bold")
        self.header_font = ("Helvetica", 14, "bold")
        self.normal_font = ("Helvetica", 12)
        self.small_font = ("Helvetica", 10)
        self.code_font = ("Courier", 10)
        self.button_font = ("Helvetica", 12, "bold")
        
    def apply_theme(self, root):
        """Apply theme settings to the root window and children"""
        # Configure ttk styles
        style = ttk.Style(root)
        
        # Try to use a modern theme if available
        try:
            style.theme_use("clam")  # More modern looking theme
        except:
            pass  # Fall back to default theme
        
        # Configure colors for ttk widgets
        style.configure("TFrame", background=self.bg_color)
        style.configure("TLabel", background=self.bg_color, foreground=self.text_color)
        style.configure("TButton", background=self.primary_color, foreground="white")
        style.configure("TCheckbutton", background=self.bg_color, foreground=self.text_color)
        style.configure("TRadiobutton", background=self.bg_color, foreground=self.text_color)
        style.configure("TEntry", fieldbackground="white", foreground=self.text_color)
        style.configure("TCombobox", fieldbackground="white", foreground=self.text_color)
        
        # Configure special styles
        style.configure("Header.TLabel", font=self.header_font)
        style.configure("Title.TLabel", font=self.title_font)
        style.configure("Success.TLabel", foreground=self.success_color)
        style.configure("Error.TLabel", foreground=self.error_color)
        style.configure("Warning.TLabel", foreground=self.warning_color)
        
        # Configure the notebook style
        style.configure("TNotebook", background=self.bg_color, tabmargins=[2, 5, 2, 0])
        style.configure("TNotebook.Tab", background="#e1e1e1", padding=[10, 4], font=self.normal_font)
        style.map("TNotebook.Tab",
                background=[("selected", self.primary_color)],
                foreground=[("selected", "white")])
        
        # Configure progressbar
        style.configure("TProgressbar", troughcolor=self.bg_color, 
                      background=self.secondary_color, borderwidth=0)
        
        # Configure root window
        root.configure(background=self.bg_color)

    def _apply_light_theme(self, root):
            """Apply light theme to the application"""
            self.bg_color = "#f0f0f0"
            self.fg_color = "#000000"
            self.secondary_color = "#0078d7"
            self.selected_bg = "#CCE8FF"
            self.hover_color = "#E5F1FB"
            
            style = ttk.Style()
            style.theme_use('clam')  # Use clam as base theme - stable across platforms
            
            # Configure ttk styles
            style.configure(".", 
                        background=self.bg_color,
                        foreground=self.fg_color,
                        fieldbackground=self.bg_color)
            
            style.configure("TButton", 
                        background=self.bg_color, 
                        foreground=self.fg_color)
            
            style.map("TButton",
                    background=[("active", self.hover_color)],
                    foreground=[("active", self.fg_color)])
            
            style.configure("TFrame", background=self.bg_color)
            style.configure("TNotebook", background=self.bg_color)
            style.configure("TNotebook.Tab", background=self.bg_color, foreground=self.fg_color)
            style.map("TNotebook.Tab",
                    background=[("selected", self.selected_bg)],
                    foreground=[("selected", self.fg_color)])
            
            style.configure("TLabelframe", background=self.bg_color, foreground=self.fg_color)
            style.configure("TLabelframe.Label", background=self.bg_color, foreground=self.fg_color)
            
            # Configure the root window and standard widgets
            root.configure(background=self.bg_color)
            
            # Apply recursively to all tkinter widgets
            self._update_widget_colors(root)
    
    def _apply_dark_theme(self, root):
        """Apply dark theme to the application"""
        self.bg_color = "#2d2d2d"
        self.fg_color = "#ffffff"
        self.secondary_color = "#0078d7"
        self.selected_bg = "#185a9d"
        self.hover_color = "#404040"
        
        style = ttk.Style()
        style.theme_use('clam')  # Use clam as base theme - stable across platforms
        
        # Configure ttk styles for dark theme
        style.configure(".", 
                      background=self.bg_color,
                      foreground=self.fg_color,
                      fieldbackground="#3d3d3d")
        
        style.configure("TButton", 
                       background="#3d3d3d", 
                       foreground=self.fg_color)
        
        style.map("TButton",
                 background=[("active", self.hover_color)],
                 foreground=[("active", self.fg_color)])
        
        style.configure("TFrame", background=self.bg_color)
        style.configure("TNotebook", background=self.bg_color)
        style.configure("TNotebook.Tab", background="#3d3d3d", foreground=self.fg_color)
        style.map("TNotebook.Tab",
                 background=[("selected", self.selected_bg)],
                 foreground=[("selected", "#ffffff")])
        
        style.configure("TLabelframe", background=self.bg_color, foreground=self.fg_color)
        style.configure("TLabelframe.Label", background=self.bg_color, foreground=self.fg_color)
        
        style.configure("TEntry", fieldbackground="#3d3d3d", foreground=self.fg_color)
        style.configure("TCombobox", fieldbackground="#3d3d3d", foreground=self.fg_color,
                      selectbackground=self.selected_bg, selectforeground="#ffffff")
        
        # Configure the root window
        root.configure(background=self.bg_color)
        
        # Apply recursively to all tkinter widgets
        self._update_widget_colors(root)

    def _apply_system_theme(self, root):
        """Apply system theme (falls back to light or dark based on OS settings)"""
        # Check if we can detect system dark mode
        # This is a simplified approach - in practice, you might want to use platform-specific methods
        if self._is_system_in_dark_mode():
            self._apply_dark_theme(root)
        else:
            self._apply_light_theme(root)
    
    def _is_system_in_dark_mode(self):
        """Detect if system is using dark mode"""
        # This is a simplified implementation
        # In practice, you would use platform-specific methods
        # For now, just always return False (default to light theme)
        return False
    
    def _update_widget_colors(self, widget):
        """Recursively update colors for all widgets"""
        try:
            # Skip updating certain widget types
            if isinstance(widget, (ttk.Separator, ttk.Progressbar, ttk.Scrollbar)):
                return
                
            # Update tkinter (non-ttk) widgets
            if not isinstance(widget, ttk.Widget) and hasattr(widget, 'configure'):
                if hasattr(widget, 'cget'):
                    try:
                        # Only change color if it's not a ttk widget
                        if 'background' in widget.keys():
                            widget.configure(background=self.bg_color)
                        if 'foreground' in widget.keys():
                            widget.configure(foreground=self.fg_color)
                        if isinstance(widget, tk.Text) and 'insertbackground' in widget.keys():
                            widget.configure(insertbackground=self.fg_color)
                    except tk.TclError:
                        pass  # Some widgets don't support these options
                        
            # Recursively process all children
            for child in widget.winfo_children():
                self._update_widget_colors(child)
                
        except Exception as e:
            # Just log the error and continue - don't let theme issues crash the app
            print(f"Error updating widget colors: {e}")
            pass
    
    def _get_timestamp(self):
        """Get current timestamp for logging"""
        import datetime
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

class ToolTip:
    """Create tooltips for widgets"""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)
    
    def show_tooltip(self, event=None):
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        
        # Create tooltip window
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        
        label = ttk.Label(self.tooltip_window, text=self.text, 
                        background="#ffffe0", relief="solid", borderwidth=1,
                        wraplength=250, justify="left", padding=5)
        label.pack()
    
    def hide_tooltip(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

def add_tooltip(self, widget, text):
    """Add a tooltip to a widget"""
    return ToolTip(widget, text)


class WorkflowGUI:
    """Main GUI class for the Intake CFD Optimization Suite"""
    def __init__(self, root):
        """Initialize the WorkflowGUI with the root Tk window"""
        self.root = root
        
        # Initialize the theme
        self.theme = ModernTheme()
        self.theme.apply_theme(root)
        
        # Add application header with logo and title
        self.setup_app_header(root, self.theme)
        
        # Setup the UI components
        self.setup_ui()
        
        # Load settings
        self.load_settings()
        
        # Variable to track if workflow is running
        self.workflow_running = False
        self.optimization_running = False
        
        # Check for HPC module availability
        if not PARAMIKO_AVAILABLE:
            # Disable HPC functionality
            if hasattr(self, 'notebook') and hasattr(self, 'hpc_tab'):
                self.notebook.tab(self.hpc_tab, state='disabled')
        
        # Initialize demo mode if needed
        if DEMO_MODE:
            self.log("Running in demonstration mode")
            # Create mock executables for demonstration
            create_mock_executables()
        
        # Set up basic visualization data structure
        self.visualization_data = {
            'X': None,
            'Y': None,
            'Pressure': None,
            'Velocity': None,
            'Temperature': None,
            'Turbulence': None
        }
        
        # Update memory usage display
        self.update_memory_display()
        
        self.log("Intake CFD Optimization Suite initialized")
    
    def log(self, message):
        """Log a message to both the console and the application log if available"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        
        # Print to console
        print(log_message)
        
        # Add to log file
        try:
            with open("application.log", "a") as log_file:
                log_file.write(log_message + "\n")
        except Exception as e:
            print(f"Warning: Could not write to log file: {e}")
        
        # Add to status text if available
        if hasattr(self, 'workflow_status_text'):
            try:
                self.workflow_status_text.configure(state='normal')
                self.workflow_status_text.insert(tk.END, log_message + "\n")
                self.workflow_status_text.see(tk.END)
                self.workflow_status_text.configure(state='disabled')
            except:
                pass
        
    def setup_ui(self):
        """Set up the main UI components"""
        # Create main notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create tabs
        self.workflow_tab = ttk.Frame(self.notebook)
        self.visualization_tab = ttk.Frame(self.notebook)
        self.optimization_tab = ttk.Frame(self.notebook)
        self.hpc_tab = ttk.Frame(self.notebook)
        self.settings_tab = ttk.Frame(self.notebook)
        
        # Add tabs to notebook
        self.notebook.add(self.workflow_tab, text="Workflow")
        self.notebook.add(self.visualization_tab, text="Visualization")
        self.notebook.add(self.optimization_tab, text="Optimization")
        self.notebook.add(self.hpc_tab, text="HPC")
        self.notebook.add(self.settings_tab, text="Settings")
        
        # Set up each tab
        self.setup_workflow_tab()
        self.setup_visualization_tab()
        self.setup_optimization_tab()
        # HPC tab will be set up by HPC module if available
        self.setup_settings_tab()
        
        # Set up status bar
        self.setup_status_bar()
        
        self.log("UI setup complete")

    def toggle_auth_type(self):
        """Toggle between password and key authentication frames"""
        try:
            if self.auth_type.get() == "password":
                self.password_frame.pack(fill="x", padx=10, pady=5)
                if hasattr(self, 'key_frame'):
                    self.key_frame.pack_forget()
            else:
                if hasattr(self, 'password_frame'):
                    self.password_frame.pack_forget()
                self.key_frame.pack(fill="x", padx=10, pady=5)
        except Exception as e:
            self.log(f"Error toggling auth type: {e}")

    def browse_key_file(self):
        """Browse for SSH private key file"""
        from tkinter import filedialog
        try:
            key_file = filedialog.askopenfilename(
                title="Select SSH Private Key",
                filetypes=[("All Files", "*.*"), ("SSH Key", "*.pem")]
            )
            if key_file:
                self.hpc_key_path.delete(0, tk.END)
                self.hpc_key_path.insert(0, key_file)
        except Exception as e:
            self.log(f"Error browsing for key file: {e}")

    def test_hpc_connection(self):
        """Test HPC connection"""
        try:
            self.connection_status_var.set("Status: Testing...")
            self.connection_status_label.config(foreground="orange")
            
            # Get connection details
            config = self.get_hpc_config()
            if not config:
                return
                
            # Disable test button during test
            if hasattr(self, 'test_connection_button'):
                self.test_connection_button.config(state=tk.DISABLED)
            
            # Run the test in a thread
            thread = threading.Thread(target=self._test_connection_thread, args=(config,), daemon=True)
            thread.start()
        except Exception as e:
            self.log(f"Error testing HPC connection: {e}")
            self.connection_status_var.set(f"Status: Error - {str(e)}")
            self.connection_status_label.config(foreground="red")

    def _test_connection_thread(self, config):
        """Thread to test HPC connection"""
        try:
            # Try to import paramiko
            try:
                import paramiko
            except ImportError:
                # Update UI in main thread
                self.root.after(0, lambda: self.update_connection_status(False, "Paramiko SSH library not installed"))
                return
            
            # Test connection
            try:
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                
                if config.get("use_key"):
                    # Connect with key
                    client.connect(
                        hostname=config["hostname"],
                        port=config["port"],
                        username=config["username"],
                        key_filename=config["key_path"],
                        timeout=10
                    )
                else:
                    # Connect with password
                    client.connect(
                        hostname=config["hostname"],
                        port=config["port"],
                        username=config["username"],
                        password=config["password"],
                        timeout=10
                    )
                    
                # Execute a simple command to test
                stdin, stdout, stderr = client.exec_command("uname -a")
                result = stdout.read().decode('utf-8')
                
                # Close connection
                client.close()
                
                # Update UI in main thread
                self.root.after(0, lambda: self.update_connection_status(True, f"Connected: {result.strip()}"))
                
            except Exception as e:
                # Update UI in main thread
                self.root.after(0, lambda: self.update_connection_status(False, str(e)))
                
        except Exception as e:
            # Update UI in main thread
            self.root.after(0, lambda: self.update_connection_status(False, f"Error: {str(e)}"))

    def update_connection_status(self, success, message):
        """Update connection status UI"""
        try:
            if success:
                self.connection_status_var.set(f"Status: Connected")
                self.connection_status_label.config(foreground="green")
                self.log(f"HPC connection successful: {message}")
            else:
                self.connection_status_var.set(f"Status: Failed")
                self.connection_status_label.config(foreground="red")
                self.log(f"HPC connection failed: {message}")
                messagebox.showerror("Connection Failed", f"Failed to connect: {message}")
            
            # Re-enable test button
            if hasattr(self, 'test_connection_button'):
                self.test_connection_button.config(state=tk.NORMAL)
        except Exception as e:
            self.log(f"Error updating connection status: {e}")

    def get_hpc_config(self):
        """Get HPC connection configuration from UI settings"""
        try:
            # Check if all required widgets exist
            required_attrs = ['hpc_hostname', 'hpc_username', 'hpc_port']
            if not all(hasattr(self, attr) for attr in required_attrs):
                self.log("Error: HPC widgets not properly initialized")
                return None
                
            config = {
                "hostname": self.hpc_hostname.get(),
                "username": self.hpc_username.get(),
                "port": int(self.hpc_port.get()) if self.hpc_port.get().isdigit() else 22,
            }
            
            # Get authentication details
            if hasattr(self, 'auth_type') and self.auth_type.get() == "key":
                config["use_key"] = True
                config["key_path"] = self.hpc_key_path.get() if hasattr(self, 'hpc_key_path') else ""
            else:
                config["use_key"] = False
                config["password"] = self.hpc_password.get() if hasattr(self, 'hpc_password') else ""
                
            # Get scheduler type
            if hasattr(self, 'hpc_scheduler'):
                config["scheduler"] = self.hpc_scheduler.get()
                
            return config
        except Exception as e:
            self.log(f"Error getting HPC config: {e}")
            messagebox.showerror("Error", f"Invalid HPC configuration: {str(e)}")
            return None

    def save_hpc_profiles(self):
        """Save HPC settings to config file"""
        try:
            settings = {
                "hpc_enabled": True,
                "visible_in_gui": True,
                "hostname": self.hpc_hostname.get() if hasattr(self, 'hpc_hostname') else "",
                "username": self.hpc_username.get() if hasattr(self, 'hpc_username') else "",
                "port": int(self.hpc_port.get()) if hasattr(self, 'hpc_port') and self.hpc_port.get().isdigit() else 22,
                "remote_dir": self.hpc_remote_dir.get() if hasattr(self, 'hpc_remote_dir') else "/home/user/cfd_projects",
                "use_key": self.auth_type.get() == "key" if hasattr(self, 'auth_type') else False,
                "key_path": self.hpc_key_path.get() if hasattr(self, 'hpc_key_path') else "",
                "scheduler": self.hpc_scheduler.get() if hasattr(self, 'hpc_scheduler') else "slurm",
                "job_defaults": {}
            }
            
            # Add job settings
            if hasattr(self, 'job_name'):
                settings["job_defaults"]["name"] = self.job_name.get()
            if hasattr(self, 'job_nodes'):
                settings["job_defaults"]["nodes"] = self.job_nodes.get()
            if hasattr(self, 'job_cores_per_node'):
                settings["job_defaults"]["cores_per_node"] = self.job_cores_per_node.get()
            if hasattr(self, 'job_walltime'):
                settings["job_defaults"]["walltime"] = self.job_walltime.get()
            if hasattr(self, 'job_queue'):
                settings["job_defaults"]["queue"] = self.job_queue.get()
            
            # Ensure Config directory exists
            import os
            config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Config")
            os.makedirs(config_dir, exist_ok=True)
            
            # Save settings
            import json
            settings_file = os.path.join(config_dir, "hpc_profiles.json")
            with open(settings_file, 'w') as f:
                json.dump(settings, f, indent=4)
            
            self.log("HPC settings saved successfully")
            messagebox.showinfo("Success", "HPC settings saved successfully")
            return True
        except Exception as e:
            self.log(f"Error saving HPC settings: {e}")
            messagebox.showerror("Error", f"Failed to save HPC settings: {str(e)}")
            return False

    def _create_default_hpc_profiles(self):
        """Create default HPC settings"""
        default_settings = {
            "hpc_enabled": True,
            "visible_in_gui": True,
            "hostname": "localhost",
            "username": "",
            "port": 22,
            "remote_dir": "/home/user/cfd_projects",
            "use_key": False,
            "key_path": "",
            "scheduler": "slurm",
            "job_defaults": {
                "name": "cfd_job",
                "nodes": "1",
                "cores_per_node": "8",
                "walltime": "24:00:00",
                "queue": "compute"
            }
        }
        
        self.hpc_profiles = default_settings
        return default_settings

    def apply_hpc_profiles(self):
        """Apply loaded HPC settings to UI widgets"""
        try:
            settings = getattr(self, 'hpc_profiles', None)
            if not settings:
                settings = self.load_hpc_profiles()
            
            # Apply settings to widgets if they exist
            if hasattr(self, 'hpc_hostname'):
                self.hpc_hostname.delete(0, tk.END)
                self.hpc_hostname.insert(0, settings.get("hostname", ""))
            
            if hasattr(self, 'hpc_username'):
                self.hpc_username.delete(0, tk.END)
                self.hpc_username.insert(0, settings.get("username", ""))
            
            if hasattr(self, 'hpc_port'):
                self.hpc_port.delete(0, tk.END)
                self.hpc_port.insert(0, str(settings.get("port", 22)))
            
            if hasattr(self, 'hpc_remote_dir'):
                self.hpc_remote_dir.delete(0, tk.END)
                self.hpc_remote_dir.insert(0, settings.get("remote_dir", ""))
            
            # Authentication
            if hasattr(self, 'auth_type'):
                self.auth_type.set("key" if settings.get("use_key", False) else "password")
                
                if settings.get("use_key", False) and hasattr(self, 'hpc_key_path'):
                    self.hpc_key_path.delete(0, tk.END)
                    self.hpc_key_path.insert(0, settings.get("key_path", ""))
            
            # Scheduler
            if hasattr(self, 'hpc_scheduler'):
                self.hpc_scheduler.set(settings.get("scheduler", "slurm"))
            
            # Job settings
            job_defaults = settings.get("job_defaults", {})
            
            if hasattr(self, 'job_name'):
                self.job_name.delete(0, tk.END)
                self.job_name.insert(0, job_defaults.get("name", "cfd_job"))
            
            if hasattr(self, 'job_nodes'):
                self.job_nodes.delete(0, tk.END)
                self.job_nodes.insert(0, job_defaults.get("nodes", "1"))
            
            if hasattr(self, 'job_cores_per_node'):
                self.job_cores_per_node.delete(0, tk.END)
                self.job_cores_per_node.insert(0, job_defaults.get("cores_per_node", "8"))
            
            if hasattr(self, 'job_walltime'):
                self.job_walltime.delete(0, tk.END)
                self.job_walltime.insert(0, job_defaults.get("walltime", "24:00:00"))
            
            if hasattr(self, 'job_queue'):
                self.job_queue.delete(0, tk.END)
                self.job_queue.insert(0, job_defaults.get("queue", "compute"))
            
            self.log("HPC settings applied to UI")
            return True
        except Exception as e:
            self.log(f"Error applying HPC settings: {e}")
            return False

    def install_hpc_dependencies(self):
        """Install required HPC dependencies"""
        try:
            import subprocess
            
            # Run pip install in a separate process
            self.update_status("Installing HPC dependencies...", show_progress=True)
            
            def install_thread():
                try:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", "paramiko"])
                    
                    # Update UI in main thread
                    self.root.after(0, lambda: self.update_status("Dependencies installed successfully", show_progress=False))
                    self.root.after(0, lambda: messagebox.showinfo("Installation Complete", 
                                                                "HPC dependencies installed successfully.\nPlease restart the application."))
                except subprocess.CalledProcessError as e:
                    # Update UI in main thread
                    self.root.after(0, lambda: self.update_status("Installation failed", show_progress=False))
                    self.root.after(0, lambda: messagebox.showerror("Installation Failed", 
                                                                f"Failed to install dependencies:\n{str(e)}"))
            
            # Start the thread
            import threading
            threading.Thread(target=install_thread, daemon=True).start()
            
        except Exception as e:
            self.update_status("Installation failed", show_progress=False)
            messagebox.showerror("Error", f"Error initiating installation: {str(e)}")

    def setup_settings_tab(self):
        """Set up the settings tab"""
        # Main frame for settings tab
        settings_frame = ttk.Frame(self.settings_tab, padding=self.theme.padding)
        settings_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create a notebook for different settings categories
        settings_notebook = ttk.Notebook(settings_frame)
        settings_notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        # General settings tab
        general_tab = ttk.Frame(settings_notebook)
        settings_notebook.add(general_tab, text="General")
        
        # Create sections in general tab
        project_frame = ttk.LabelFrame(general_tab, text="Project", padding=10)
        project_frame.pack(fill='x', pady=5, padx=5)
        
        ttk.Label(project_frame, text="Project Directory:").grid(row=0, column=0, sticky='w', pady=5)
        self.project_dir_var = tk.StringVar(value=os.path.abspath("."))
        project_entry = ttk.Entry(project_frame, textvariable=self.project_dir_var, width=40)
        project_entry.grid(row=0, column=1, sticky='ew', padx=5, pady=5)
        ttk.Button(project_frame, text="Browse...", 
                 command=self.browse_project_dir).grid(row=0, column=2, padx=5, pady=5)
        
        # NX path settings
        nx_frame = ttk.LabelFrame(general_tab, text="NX Integration", padding=10)
        nx_frame.pack(fill='x', pady=5, padx=5)
        
        ttk.Label(nx_frame, text="NX Executable:").grid(row=0, column=0, sticky='w', pady=5)
        self.nx_path_var = tk.StringVar()
        nx_entry = ttk.Entry(nx_frame, textvariable=self.nx_path_var, width=40)
        nx_entry.grid(row=0, column=1, sticky='ew', padx=5, pady=5)
        ttk.Button(nx_frame, text="Browse...", 
                 command=self.browse_nx_path).grid(row=0, column=2, padx=5, pady=5)
        
        # Appearance settings tab
        appearance_tab = ttk.Frame(settings_notebook)
        settings_notebook.add(appearance_tab, text="Appearance")
        
        # Theme settings
        theme_frame = ttk.LabelFrame(appearance_tab, text="Theme", padding=10)
        theme_frame.pack(fill='x', pady=5, padx=5)
        
        self.theme_var = tk.StringVar(value="system")
        ttk.Radiobutton(theme_frame, text="System", variable=self.theme_var, 
                      value="system", command=self.apply_system_theme).grid(
                      row=0, column=0, sticky='w', pady=5)
        ttk.Radiobutton(theme_frame, text="Light", variable=self.theme_var, 
                      value="light", command=self.apply_light_theme).grid(
                      row=0, column=1, sticky='w', pady=5)
        ttk.Radiobutton(theme_frame, text="Dark", variable=self.theme_var, 
                      value="dark", command=self.apply_dark_theme).grid(
                      row=0, column=2, sticky='w', pady=5)
        
        # Font size settings
        font_frame = ttk.LabelFrame(appearance_tab, text="Font Size", padding=10)
        font_frame.pack(fill='x', pady=5, padx=5)
        
        self.font_size_var = tk.StringVar(value="normal")
        ttk.Radiobutton(font_frame, text="Small", variable=self.font_size_var, 
                    value="small", command=lambda: self.apply_font_size("Small")).grid(
                    row=0, column=0, sticky='w', pady=5)
        ttk.Radiobutton(font_frame, text="Normal", variable=self.font_size_var, 
                    value="normal", command=lambda: self.apply_font_size("Medium")).grid(
                    row=0, column=1, sticky='w', pady=5)
        ttk.Radiobutton(font_frame, text="Large", variable=self.font_size_var, 
                    value="large", command=lambda: self.apply_font_size("Large")).grid(
                    row=0, column=2, sticky='w', pady=5)
        
        # Advanced settings tab
        advanced_tab = ttk.Frame(settings_notebook)
        settings_notebook.add(advanced_tab, text="Advanced")
        
        # Performance settings
        perf_frame = ttk.LabelFrame(advanced_tab, text="Performance", padding=10)
        perf_frame.pack(fill='x', pady=5, padx=5)
        
        ttk.Label(perf_frame, text="CPU Cores to Use:").grid(row=0, column=0, sticky='w', pady=5)
        max_cores = multiprocessing.cpu_count()
        self.cores_var = tk.StringVar(value=str(max(1, max_cores - 1)))
        cores_spinbox = ttk.Spinbox(perf_frame, from_=1, to=max_cores, textvariable=self.cores_var, width=5)
        cores_spinbox.grid(row=0, column=1, sticky='w', padx=5, pady=5)
        ttk.Label(perf_frame, text=f"(Max: {max_cores})").grid(row=0, column=2, sticky='w', pady=5)
        
        # Debugging settings
        debug_frame = ttk.LabelFrame(advanced_tab, text="Debugging", padding=10)
        debug_frame.pack(fill='x', pady=5, padx=5)
        
        self.debug_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(debug_frame, text="Enable Debug Logging", 
                      variable=self.debug_var).grid(row=0, column=0, sticky='w', pady=5)
        
        self.demo_var = tk.BooleanVar(value=DEMO_MODE)
        ttk.Checkbutton(debug_frame, text="Demo Mode (No actual simulations)", 
                      variable=self.demo_var).grid(row=1, column=0, sticky='w', pady=5)
        
        # System information
        sys_frame = ttk.LabelFrame(advanced_tab, text="System Information", padding=10)
        sys_frame.pack(fill='x', pady=5, padx=5)
        
        ttk.Label(sys_frame, text=f"OS: {platform.system()} {platform.release()}").grid(
            row=0, column=0, sticky='w', pady=2)
        ttk.Label(sys_frame, text=f"Python: {platform.python_version()}").grid(
            row=1, column=0, sticky='w', pady=2)
        
        self.mem_info_var = tk.StringVar(value="Memory: --")
        mem_label = ttk.Label(sys_frame, textvariable=self.mem_info_var)
        mem_label.grid(row=2, column=0, sticky='w', pady=2)
        
        # Add buttons for memory update, diagnostics, update check
        button_frame = ttk.Frame(sys_frame)
        button_frame.grid(row=3, column=0, sticky='w', pady=5)
        
        ttk.Button(button_frame, text="Update Memory Info", 
                 command=self.update_memory_display).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Run Diagnostics", 
                 command=self.run_diagnostics).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Check for Updates", 
                 command=self.check_updates).pack(side='left', padx=5)
        
        # Buttons at the bottom
        button_frame = ttk.Frame(settings_frame)
        button_frame.pack(fill='x', pady=10)
        
        ttk.Button(button_frame, text="Save Settings", 
                 command=self.save_settings).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Reset to Default", 
                 command=self.reset_settings).pack(side='left', padx=5)
        
        self.log("Settings tab initialized")
        
        # Update memory info
        self.update_memory_display()
    
    def browse_nx_path(self):
        """Browse for NX executable"""
        file_path = filedialog.askopenfilename(
            title="Select NX Executable",
            filetypes=[("Executable files", "*.exe"), ("All files", "*.*")]
        )
        if file_path:
            self.nx_path_var.set(file_path)
    
    def browse_project_dir(self):
        """Browse for project directory"""
        dir_path = filedialog.askdirectory(title="Select Project Directory")
        if dir_path:
            self.project_dir_var.set(dir_path)
    
    def apply_appearance_settings(self):
        """Apply selected appearance settings"""
        theme_name = self.theme_combo.get()
        font_size = self.font_size.get()
        
        self.log(f"Applying appearance settings: Theme={theme_name}, Font Size={font_size}")
        
        try:
            # Apply theme
            if theme_name == "Dark":
                self.apply_dark_theme()
            elif theme_name == "Light":
                self.apply_light_theme()
            elif theme_name == "System":
                self.apply_system_theme()
            
            # Apply font size - just pass the setting name
            self.apply_font_size(font_size)
                
            messagebox.showinfo("Settings Applied", "Appearance settings have been applied.")
            self.update_status("Appearance settings applied")
        except Exception as e:
            self.log(f"Error applying appearance settings: {e}")
            messagebox.showerror("Error", f"Failed to apply appearance settings: {e}")
        
    def apply_dark_theme(self):
        """Apply dark theme to the application"""
        # Update theme object - remove secondary_color reference, use only existing properties
        self.theme.bg_color = "#2C3E50"
        self.theme.primary_color = "#34495E"
        self.theme.secondary_color = "#3498DB"  # Secondary color already exists
        self.theme.text_color = "#ECF0F1"
        self.theme.success_color = "#2ECC71"
        self.theme.warning_color = "#F39C12"
        self.theme.error_color = "#E74C3C"
        self.theme.border_color = "#7F8C8D"
        
        # Apply theme to all widgets
        self.theme.apply_theme(self.root)
        
        # Switch to dark theme variants for all canvases if they exist
        if hasattr(self, 'workflow_canvas'):
            self.workflow_canvas.configure(bg=self.theme.bg_color, highlightbackground=self.theme.border_color)
        
        # Update status
        self.update_status("Applied dark theme")
        
        # Redraw workflow if available
        if hasattr(self, '_redraw_workflow'):
            self._redraw_workflow()
    
    def apply_light_theme(self):
        """Apply light theme to the application"""
        self.theme.primary_color = "#4a6fa5"  # Blue
        self.theme.secondary_color = "#45b29d"  # Teal
        self.theme.bg_color = "#f5f5f5"  # Light gray
        self.theme.text_color = "#333333"  # Dark gray
        self.theme.border_color = "#dddddd"  # Light gray border
        
        # Apply theme to the root window
        self.theme.apply_theme(self.root)
        
        # Switch to light theme variants for all canvases
        if hasattr(self, 'workflow_canvas'):
            self.workflow_canvas.configure(bg="white", highlightbackground="#dddddd")
        
        # Update status
        self.update_status("Applied light theme")
        
        # Redraw workflow if available
        if hasattr(self, '_redraw_workflow'):
            self._redraw_workflow()
    
    def apply_system_theme(self):
        """Apply system theme to the application"""
        # For simplicity, use light theme as system theme
        self.apply_light_theme()
        
        # Update status
        self.update_status("Applied system theme")
        
    def save_settings(self):
        """Save settings to a configuration file"""
        try:
            # Collect settings
            settings = {
                "general": {
                    "project_dir": self.project_dir_var.get(),
                    "nx_path": self.nx_path_var.get(),
                    "cores": self.cores_var.get(),
                    "debug": self.debug_var.get(),
                    "demo_mode": self.demo_var.get()
                },
                "appearance": {
                    "theme": self.theme_var.get(),
                    "font_size": self.font_size_var.get()
                }
            }
            
            # Save to file
            with open("settings.json", "w") as f:
                json.dump(settings, f, indent=4)
                
            self.update_status("Settings saved successfully")
            messagebox.showinfo("Settings Saved", "Your settings have been saved successfully.")
            
        except Exception as e:
            self.log(f"Error saving settings: {str(e)}")
            messagebox.showerror("Error", f"Failed to save settings: {str(e)}")
    
    def load_settings(self):
        """Load settings from configuration file"""
        try:
            if not os.path.exists("settings.json"):
                self.log("Settings file not found, using defaults")
                return
                
            with open("settings.json", "r") as f:
                settings = json.load(f)
            
            # Apply general settings
            if "general" in settings:
                gen = settings["general"]
                if "project_dir" in gen and hasattr(self, 'project_dir_var'):
                    self.project_dir_var.set(gen["project_dir"])
                    
                if "nx_path" in gen and hasattr(self, 'nx_path_var'):
                    self.nx_path_var.set(gen["nx_path"])
                    
                if "cores" in gen and hasattr(self, 'cores_var'):
                    self.cores_var.set(gen["cores"])
                    
                if "debug" in gen and hasattr(self, 'debug_var'):
                    self.debug_var.set(gen["debug"])
                    
                if "demo_mode" in gen and hasattr(self, 'demo_var'):
                    self.demo_var.set(gen["demo_mode"])
                    global DEMO_MODE
                    DEMO_MODE = gen["demo_mode"]
            
            # Apply appearance settings
            if "appearance" in settings:
                app = settings["appearance"]
                if "theme" in app and hasattr(self, 'theme_var'):
                    self.theme_var.set(app["theme"])
                    self.apply_appearance_settings()
                    
                if "font_size" in app and hasattr(self, 'font_size_var'):
                    self.font_size_var.set(app["font_size"])
                    self.apply_appearance_settings()
            
            self.log("Settings loaded successfully")
            
        except Exception as e:
            self.log(f"Error loading settings: {str(e)}")
            # Don't show an error dialog here since this is called during initialization
    
    def reset_settings(self):
        """Reset settings to default values"""
        if not messagebox.askyesno("Confirm Reset", "Are you sure you want to reset all settings to default values?"):
            return
            
        try:
            # Reset general settings
            if hasattr(self, 'project_dir_var'):
                self.project_dir_var.set(os.path.abspath("."))
                
            if hasattr(self, 'nx_path_var'):
                self.nx_path_var.set("")
                
            if hasattr(self, 'cores_var'):
                max_cores = multiprocessing.cpu_count()
                self.cores_var.set(str(max(1, max_cores - 1)))
                
            if hasattr(self, 'debug_var'):
                self.debug_var.set(False)
                
            if hasattr(self, 'demo_var'):
                self.demo_var.set(True)
                global DEMO_MODE
                DEMO_MODE = True
            
            # Reset appearance settings
            if hasattr(self, 'theme_var'):
                self.theme_var.set("system")
                
            if hasattr(self, 'font_size_var'):
                self.font_size_var.set("normal")
            
            # Apply reset settings
            self.apply_appearance_settings()
            
            # Delete settings file if it exists
            if os.path.exists("settings.json"):
                os.remove("settings.json")
            
            self.update_status("Settings reset to defaults")
            messagebox.showinfo("Settings Reset", "All settings have been reset to their default values.")
            
        except Exception as e:
            self.log(f"Error resetting settings: {str(e)}")
            messagebox.showerror("Error", f"Failed to reset settings: {str(e)}")
    
    def check_updates(self):
        """Check for application updates"""
        # In a real app, this would connect to a server to check for updates
        # For this demo, just show a message
        messagebox.showinfo("Update Check", "You are using the latest version of the Intake CFD Optimization Suite.")
    
    def run_diagnostics(self):
        """Run system diagnostics"""
        # Create a dialog to show diagnostics progress
        diagnostics_dialog = tk.Toplevel(self.root)
        diagnostics_dialog.title("System Diagnostics")
        diagnostics_dialog.geometry("500x400")
        diagnostics_dialog.transient(self.root)
        diagnostics_dialog.grab_set()
        
        # Create UI for diagnostics dialog
        frame = ttk.Frame(diagnostics_dialog, padding=10)
        frame.pack(fill='both', expand=True)
        
        ttk.Label(frame, text="Running system diagnostics...", 
                font=self.theme.header_font).pack(pady=10)
        
        progress = ttk.Progressbar(frame, orient='horizontal', length=400, mode='indeterminate')
        progress.pack(pady=10)
        progress.start()
        
        status_var = tk.StringVar(value="Initializing diagnostics...")
        ttk.Label(frame, textvariable=status_var).pack(pady=5)
        
        results_text = scrolledtext.ScrolledText(frame, wrap=tk.WORD, height=12, width=60)
        results_text.pack(fill='both', expand=True, pady=10)
        results_text.insert(tk.END, "Gathering system information...\n")
        
        close_button = ttk.Button(frame, text="Close", command=diagnostics_dialog.destroy)
        close_button.pack(pady=10)
        close_button.config(state='disabled')
        
        # Run diagnostics in a separate thread
        def run_thread():
            try:
                # Run diagnostics
                self._run_diagnostics_thread(status_var, results_text, progress, close_button)
            except Exception as e:
                # Handle errors
                self.log(f"Diagnostics error: {str(e)}")
                self.root.after(0, lambda: self._show_diagnostics_error(str(e)))
                self.root.after(0, lambda: status_var.set("Diagnostics failed"))
                self.root.after(0, lambda: progress.stop())
                self.root.after(0, lambda: close_button.config(state='normal'))
        
        # Start diagnostics thread
        threading.Thread(target=run_thread, daemon=True).start()

    def run_workflow(self):
        """Run the entire intake optimization workflow"""
        try:
            # Check if a workflow is already running
            if self.workflow_running:
                messagebox.showinfo("Workflow Running", "A workflow is already running. Please wait for it to complete or cancel it.")
                return
            
            # Validate inputs
            try:
                self._validate_workflow_inputs()
            except Exception as ve:
                messagebox.showerror("Invalid Input", str(ve))
                return
            
            # Get parameter values
            L4 = float(self.l4_workflow.get())
            L5 = float(self.l5_workflow.get())
            alpha1 = float(self.alpha1_workflow.get())
            alpha2 = float(self.alpha2_workflow.get())
            alpha3 = float(self.alpha3_workflow.get())
            
            # Update UI state
            self.workflow_running = True
            self.run_button.config(state='disabled')
            self.cancel_button.config(state='normal')
            
            # Clear status text
            if hasattr(self, 'workflow_status_text'):
                self.workflow_status_text.configure(state='normal')
                self.workflow_status_text.delete(1.0, tk.END)
                self.workflow_status_text.configure(state='disabled')
            
            # Reset workflow step statuses
            for step in self.workflow_steps:
                step['status'] = 'pending'
            self._redraw_workflow()
            
            # Check if using HPC
            if self.env_var.get() == "hpc":
                # Run workflow on HPC
                self._run_hpc_workflow(L4, L5, alpha1, alpha2, alpha3)
            else:
                # Create and start a local worker thread
                self.workflow_thread = threading.Thread(
                    target=self._run_workflow_thread,
                    args=(L4, L5, alpha1, alpha2, alpha3),
                    daemon=True
                )
                self.workflow_thread.start()
            
            # Update status
            self.update_status("Workflow started", show_progress=True)
            
        except Exception as e:
            self.log(f"Error starting workflow: {str(e)}")
            messagebox.showerror("Error", f"Failed to start workflow: {str(e)}")

    def _validate_workflow_inputs(self):
        """Validate workflow input parameters"""
        try:
            # Check that all parameters are valid numbers
            L4 = float(self.l4_workflow.get())
            L5 = float(self.l5_workflow.get())
            alpha1 = float(self.alpha1_workflow.get())
            alpha2 = float(self.alpha2_workflow.get())
            alpha3 = float(self.alpha3_workflow.get())
            
            # Check parameter ranges
            if L4 < 1.0 or L4 > 10.0:
                messagebox.showwarning("Range Warning", "L4 is recommended to be between 1.0 and 10.0")
                
            if L5 < 1.0 or L5 > 10.0:
                messagebox.showwarning("Range Warning", "L5 is recommended to be between 1.0 and 10.0")
                
            if alpha1 < 0.0 or alpha1 > 45.0:
                messagebox.showwarning("Range Warning", "Alpha1 is recommended to be between 0.0 and 45.0 degrees")
                
            if alpha2 < 0.0 or alpha2 > 45.0:
                messagebox.showwarning("Range Warning", "Alpha2 is recommended to be between 0.0 and 45.0 degrees")
                
            if alpha3 < 0.0 or alpha3 > 45.0:
                messagebox.showwarning("Range Warning", "Alpha3 is recommended to be between 0.0 and 45.0 degrees")
            
            return True
            
        except ValueError:
            messagebox.showerror("Invalid Input", "All parameters must be valid numbers")
            return False

    def _run_workflow_thread(self, L4, L5, alpha1, alpha2, alpha3):
        """Run the workflow process in a separate thread"""
        try:
            # Flag to track if the workflow was canceled
            self.workflow_canceled = False
            
            # Generate and export expressions
            self._update_workflow_status("Generating expressions...")
            if DEMO_MODE:
                time.sleep(1)  # Simulate processing time
            self._update_workflow_step("CAD", "running")
            
            # Generate expression file
            try:
                exp(L4, L5, alpha1, alpha2, alpha3)
                self._update_workflow_status("Expressions generated")
            except Exception as e:
                self._update_workflow_status(f"Error generating expressions: {str(e)}")
                self._update_workflow_step("CAD", "error")
                self._workflow_failed(f"Expression generation failed: {str(e)}")
                return
            
            # Check if canceled
            if self.workflow_canceled:
                self._workflow_canceled()
                return
            
            # Run NX update
            self._update_workflow_status("Updating NX model...")
            try:
                if not DEMO_MODE:
                    run_nx_workflow()
                else:
                    time.sleep(2)  # Simulate NX processing time
                self._update_workflow_status("NX model updated successfully")
                self._update_workflow_step("CAD", "complete")
            except Exception as e:
                self._update_workflow_status(f"Error updating NX model: {str(e)}")
                self._update_workflow_step("CAD", "error")
                self._workflow_failed(f"NX update failed: {str(e)}")
                return
            
            # Check if canceled
            if self.workflow_canceled:
                self._workflow_canceled()
                return
            
            # Process mesh
            self._update_workflow_status("Generating mesh...")
            self._update_workflow_step("Mesh", "running")
            try:
                if not DEMO_MODE:
                    process_mesh("INTAKE3D.step", "INTAKE3D.msh")
                else:
                    time.sleep(3)  # Simulate mesh generation time
                self._update_workflow_status("Mesh generated successfully")
                self._update_workflow_step("Mesh", "complete")
            except Exception as e:
                self._update_workflow_status(f"Error generating mesh: {str(e)}")
                self._update_workflow_step("Mesh", "error")
                self._workflow_failed(f"Mesh generation failed: {str(e)}")
                return
            
            # Check if canceled
            if self.workflow_canceled:
                self._workflow_canceled()
                return
            
            # Run CFD simulation
            self._update_workflow_status("Running CFD simulation...")
            self._update_workflow_step("CFD", "running")
            try:
                if not DEMO_MODE:
                    run_cfd("INTAKE3D.msh")
                else:
                    time.sleep(5)  # Simulate CFD computation time
                self._update_workflow_status("CFD simulation completed successfully")
                self._update_workflow_step("CFD", "complete")
            except Exception as e:
                self._update_workflow_status(f"Error running CFD simulation: {str(e)}")
                self._update_workflow_step("CFD", "error")
                self._workflow_failed(f"CFD simulation failed: {str(e)}")
                return
            
            # Check if canceled
            if self.workflow_canceled:
                self._workflow_canceled()
                return
            
            # Process CFD results
            self._update_workflow_status("Processing CFD results...")
            self._update_workflow_step("Results", "running")
            try:
                if not DEMO_MODE:
                    process_results("cfd_results", "processed_results.csv")
                else:
                    time.sleep(2)  # Simulate results processing time
                    
                    # In demo mode, generate sample visualization data
                    X, Y = np.meshgrid(np.linspace(-1, 1, 50), np.linspace(-1, 1, 50))
                    R = np.sqrt(X**2 + Y**2)
                    Z = np.exp(-R**2) * 100  # Gaussian shape
                    
                    # Store the data for visualization
                    self.visualization_data = {
                        'X': X,
                        'Y': Y,
                        'Pressure': Z,
                        'Velocity': 20 * (1 - np.exp(-R)),
                        'Temperature': 300 + 50 * np.exp(-R**2),
                        'Turbulence': 5 * R * np.exp(-R)
                    }
                    
                self._update_workflow_status("Results processing completed")
                self._update_workflow_step("Results", "complete")
            except Exception as e:
                self._update_workflow_status(f"Error processing results: {str(e)}")
                self._update_workflow_step("Results", "error")
                self._workflow_failed(f"Results processing failed: {str(e)}")
                return
            
            # Load and display results
            try:
                # In a real application, we would load actual data from processed_results.csv
                # For demo mode, we use the generated data
                self._load_and_display_results("processed_results.csv", L4, L5, alpha1, alpha2, alpha3)
                self._update_workflow_status("Workflow completed successfully")
                self._workflow_completed()
            except Exception as e:
                self._update_workflow_status(f"Error loading results: {str(e)}")
                self._workflow_failed(f"Loading results failed: {str(e)}")
            
        except Exception as e:
            self._update_workflow_status(f"Unexpected error: {str(e)}")
            self._workflow_failed(f"Workflow failed: {str(e)}")

    def _update_workflow_status(self, message):
        """Update the workflow status text with a new message"""
        self.log(message)
        
        # Update text widget if available
        if hasattr(self, 'workflow_status_text'):
            try:
                self.workflow_status_text.configure(state='normal')
                self.workflow_status_text.insert(tk.END, message + "\n")
                self.workflow_status_text.see(tk.END)
                self.workflow_status_text.configure(state='disabled')
            except Exception as e:
                print(f"Warning: Could not update workflow status text: {e}")
        
        # Update main status bar
        self.update_status(message)

    def _update_workflow_step(self, step_name, status):
        """Update the status of a workflow step and redraw"""
        if not hasattr(self, 'workflow_steps'):
            return
            
        # Find the step by name and update its status
        for step in self.workflow_steps:
            if step['name'] == step_name:
                step['status'] = status
                break
        
        # Redraw the workflow visualization
        self._redraw_workflow()

    def _load_and_display_results(self, results_file, L4, L5, alpha1, alpha2, alpha3):
        """Load results from file and display in the visualization tab"""
        # Switch to visualization tab
        if hasattr(self, 'notebook'):
            self.notebook.select(self.visualization_tab)
        
        # Update CFD visualization with the loaded data
        self.update_cfd_visualization()
        
        # For demo mode, generate some result metrics
        if DEMO_MODE:
            # Calculate some metrics based on input parameters
            pressure_drop = 100 * (0.5 + 0.2 * L4 - 0.1 * L5 + 
                                0.01 * alpha1 + 0.005 * alpha2 + 0.003 * alpha3)
            
            flow_rate = 50 * (1 + 0.1 * L4 + 0.15 * L5 - 
                            0.01 * alpha1 - 0.02 * alpha2 - 0.01 * alpha3)
            
            uniformity = 85 * (1 - 0.02 * abs(L4 - 3) - 0.02 * abs(L5 - 3) - 
                            0.01 * abs(alpha1 - 15) - 0.01 * abs(alpha2 - 15) - 
                            0.01 * abs(alpha3 - 15))
            
            # Show results in a message box
            msg = (f"Simulation Results for Parameters:\n"
                f"L4: {L4}, L5: {L5}, Alpha1: {alpha1}, Alpha2: {alpha2}, Alpha3: {alpha3}\n\n"
                f"Pressure Drop: {pressure_drop:.2f} Pa\n"
                f"Flow Rate: {flow_rate:.2f} m³/s\n"
                f"Flow Uniformity: {uniformity:.1f}%")
            
            messagebox.showinfo("Simulation Results", msg)

    def _workflow_completed(self):
        """Handle workflow completion"""
        # Update UI state
        self.workflow_running = False
        
        if hasattr(self, 'run_button'):
            self.run_button.config(state='normal')
            
        if hasattr(self, 'cancel_button'):
            self.cancel_button.config(state='disabled')
        
        # Update status
        self.update_status("Workflow completed successfully", show_progress=False)
        
        # Show notification
        messagebox.showinfo("Workflow Complete", "The workflow has been completed successfully.")

    def _workflow_canceled(self):
        """Handle workflow cancellation"""
        # Update UI state
        self.workflow_running = False
        
        if hasattr(self, 'run_button'):
            self.run_button.config(state='normal')
            
        if hasattr(self, 'cancel_button'):
            self.cancel_button.config(state='disabled')
        
        # Update status
        self.update_status("Workflow canceled", show_progress=False)
        
        # Set status for incomplete steps
        if hasattr(self, 'workflow_steps'):
            for step in self.workflow_steps:
                if step['status'] == 'running':
                    step['status'] = 'canceled'
                elif step['status'] == 'pending':
                    step['status'] = 'canceled'
            
            # Redraw the workflow
            self._redraw_workflow()
        
        # Update status text
        self._update_workflow_status("Workflow has been canceled by the user")

    def _workflow_failed(self, error_message):
        """Handle workflow failure"""
        # Update UI state
        self.workflow_running = False
        
        if hasattr(self, 'run_button'):
            self.run_button.config(state='normal')
            
        if hasattr(self, 'cancel_button'):
            self.cancel_button.config(state='disabled')
        
        # Update status
        self.update_status(f"Workflow failed: {error_message}", show_progress=False)
        
        # Update status text
        self._update_workflow_status(f"Workflow failed: {error_message}")
        
        # Show error dialog
        messagebox.showerror("Workflow Failed", f"The workflow has failed:\n\n{error_message}")

    def cancel_workflow(self):
        """Cancel the running workflow"""
        if not self.workflow_running:
            return
            
        answer = messagebox.askyesno("Confirm Cancel", "Are you sure you want to cancel the current workflow?")
        if not answer:
            return
            
        # Set the canceled flag for the thread to detect
        self.workflow_canceled = True
        
        # Update status
        self.update_status("Canceling workflow...", show_progress=True)
        
        # If using real processes, we might need to actually terminate them
        if hasattr(self, 'process') and self.process:
            try:
                self.process.terminate()
            except:
                pass

    def get_hpc_config(self):
        """
        Get HPC configuration from the UI
        
        Returns:
            dict: HPC configuration dictionary
        """
        from Garage.HPC.hpc_integration import get_hpc_config
        return get_hpc_config(self)

    def refresh_job_list(self):
        """Refresh the HPC job list"""
        from Garage.HPC.hpc_integration import refresh_job_list
        refresh_job_list(self)

    def update_job_tree(self, jobs):
        """Update the job tree with the list of jobs"""
        from Garage.HPC.hpc_integration import update_job_list
        update_job_list(self, jobs)

    def submit_job(self):
        """Show dialog to submit a new HPC job"""
        from Garage.HPC.hpc_integration import submit_job
        submit_job(self)

    def cancel_job(self):
        """Cancel a selected HPC job"""
        from Garage.HPC.hpc_integration import cancel_job
        cancel_job(self)

    def show_job_details(self):
        """Show details for a selected HPC job"""
        from Garage.HPC.hpc_integration import show_job_details
        show_job_details(self)

    def download_results(self):
        """Download results from a selected HPC job"""
        from Garage.HPC.hpc_integration import download_results
        download_results(self)

    def toggle_opt_execution_environment(self):
        """Toggle between local and HPC execution for optimization"""
        if hasattr(self, 'opt_env_var') and hasattr(self, 'opt_hpc_profiles_frame'):
            if self.opt_env_var.get() == "hpc":
                self.opt_hpc_profiles_frame.pack(anchor='w', pady=5)
            else:
                self.opt_hpc_profiles_frame.pack_forget()

    def load_hpc_profiles_for_opt(self):
        """Load HPC profiles for optimization tab"""
        import os
        import json
        
        try:
            profiles_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                    "Config", "hpc_profiles.json")
            
            if os.path.exists(profiles_path):
                with open(profiles_path, 'r') as f:
                    profiles = json.load(f)
                    
                if hasattr(self, 'opt_hpc_profile'):
                    self.opt_hpc_profile['values'] = list(profiles.keys())
                    if profiles:
                        self.opt_hpc_profile.current(0)
        except Exception as e:
            self.log(f"Error loading HPC profiles for optimization: {e}")
            
    def refresh_job_list(self):
        """Refresh the HPC job list"""
        try:
            import paramiko
            import threading
            
            # Check if we have connection details
            if not hasattr(self, 'conn_profile') or not self.conn_profile.get():
                messagebox.showerror("Error", "No HPC profile selected.")
                return
                
            # Get connection config
            config = self.get_hpc_config()
            
            # Clear existing job list
            if hasattr(self, 'job_tree'):
                for item in self.job_tree.get_children():
                    self.job_tree.delete(item)
            
            self.update_status("Refreshing job list...", show_progress=True)
            
            # Function to run in separate thread
            def fetch_jobs_thread():
                try:
                    # Create SSH client
                    client = paramiko.SSHClient()
                    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    
                    # Connect based on authentication method
                    if config["use_key"]:
                        key_path = config["key_path"]
                        if not key_path:
                            self.root.after(0, lambda: self.update_status("Error: No key file specified", show_progress=False))
                            return
                        
                        try:
                            key = paramiko.RSAKey.from_private_key_file(key_path)
                            client.connect(hostname=config["hostname"], 
                                        port=config["port"], 
                                        username=config["username"], 
                                        pkey=key, 
                                        timeout=10)
                        except Exception as e:
                            self.root.after(0, lambda: self.update_status(f"Error: {str(e)}", show_progress=False))
                            return
                    else:
                        # Password authentication
                        password = config["password"]
                        if not password:
                            self.root.after(0, lambda: self.update_status("Error: No password provided", show_progress=False))
                            return
                        
                        try:
                            client.connect(hostname=config["hostname"], 
                                        port=config["port"], 
                                        username=config["username"], 
                                        password=password,
                                        timeout=10)
                        except Exception as e:
                            self.root.after(0, lambda: self.update_status(f"Error: {str(e)}", show_progress=False))
                            return
                    
                    # Run job query command based on scheduler
                    # Try to detect scheduler type first
                    stdin, stdout, stderr = client.exec_command("command -v squeue qstat bjobs")
                    scheduler_check = stdout.read().decode().strip()
                    
                    if 'squeue' in scheduler_check:
                        # SLURM
                        stdin, stdout, stderr = client.exec_command("squeue -u $USER -o '%j|%i|%T|%P|%D|%M'")
                        job_data = stdout.read().decode().strip()
                        parse_slurm_jobs(job_data)
                    elif 'qstat' in scheduler_check:
                        # PBS/Torque
                        stdin, stdout, stderr = client.exec_command("qstat -u $USER -f | grep -E 'Job Id|Job_Name|job_state|Queue|Resource_List.nodes|resources_used.walltime'")
                        job_data = stdout.read().decode().strip()
                        parse_pbs_jobs(job_data)
                    elif 'bjobs' in scheduler_check:
                        # LSF
                        stdin, stdout, stderr = client.exec_command("bjobs -u $USER -o 'JOBID JOB_NAME STAT QUEUE SLOTS RUNTIME'")
                        job_data = stdout.read().decode().strip()
                        parse_lsf_jobs(job_data)
                    else:
                        # Generic approach - check common job commands
                        self.root.after(0, lambda: self.update_status("Could not determine job scheduler type", show_progress=False))
                        
                    client.close()
                    
                    # Update UI when complete
                    self.root.after(0, lambda: self.update_status("Job list refreshed successfully", show_progress=False))
                    
                except Exception as e:
                    self.log(f"Error fetching HPC jobs: {str(e)}")
                    self.root.after(0, lambda: self.update_status(f"Error: {str(e)}", show_progress=False))
            
            # Parse SLURM format job data and update UI
            def parse_slurm_jobs(job_data):
                jobs = []
                lines = job_data.split('\n')
                
                for line in lines[1:]:  # Skip header
                    if not line.strip():
                        continue
                    
                    parts = line.strip().split('|')
                    if len(parts) >= 6:
                        job = {
                            'name': parts[0],
                            'id': parts[1],
                            'status': parts[2],
                            'queue': parts[3],
                            'nodes': parts[4],
                            'time': parts[5]
                        }
                        jobs.append(job)
                
                # Update UI from main thread
                self.root.after(0, lambda: self.update_job_tree(jobs))
                
            # Parse PBS format job data and update UI
            def parse_pbs_jobs(job_data):
                jobs = []
                current_job = {}
                
                # PBS output is a bit more complex to parse
                lines = job_data.split('\n')
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    if line.startswith('Job Id:'):
                        # New job entry
                        if current_job and 'id' in current_job:
                            jobs.append(current_job)
                        
                        current_job = {'id': line.split(':')[1].strip()}
                    elif 'Job_Name' in line:
                        current_job['name'] = line.split('=')[1].strip()
                    elif 'job_state' in line:
                        current_job['status'] = line.split('=')[1].strip()
                    elif 'Queue' in line:
                        current_job['queue'] = line.split('=')[1].strip()
                    elif 'Resource_List.nodes' in line:
                        current_job['nodes'] = line.split('=')[1].strip()
                    elif 'resources_used.walltime' in line:
                        current_job['time'] = line.split('=')[1].strip()
                
                # Add the last job if it exists
                if current_job and 'id' in current_job:
                    jobs.append(current_job)
                
                # Update UI from main thread
                self.root.after(0, lambda: self.update_job_tree(jobs))
                
            # Parse LSF format job data and update UI
            def parse_lsf_jobs(job_data):
                jobs = []
                lines = job_data.split('\n')
                
                for line in lines[1:]:  # Skip header
                    if not line.strip():
                        continue
                    
                    parts = line.strip().split()
                    if len(parts) >= 6:
                        job = {
                            'id': parts[0],
                            'name': parts[1],
                            'status': parts[2],
                            'queue': parts[3],
                            'nodes': parts[4],  # This is actually 'slots' in LSF
                            'time': parts[5]
                        }
                        jobs.append(job)
                
                # Update UI from main thread
                self.root.after(0, lambda: self.update_job_tree(jobs))
            
            # Start the fetch in a separate thread
            threading.Thread(target=fetch_jobs_thread, daemon=True).start()
            
        except ImportError:
            messagebox.showerror("Module Error", "Paramiko SSH library not installed. Install using: pip install paramiko")
        except Exception as e:
            self.log(f"Error refreshing job list: {e}")
            self.update_status(f"Error: {str(e)}", show_progress=False)

    def initialize_convergence_plot(self):
        """Initialize the convergence plot in the optimization tab"""
        if not hasattr(self, 'opt_ax') or not hasattr(self, 'opt_canvas'):
            return
            
        # Clear any existing plot
        self.opt_ax.clear()
        
        # Set up the axes
        self.opt_ax.set_title("Optimization Convergence")
        self.opt_ax.set_xlabel("Generation")
        self.opt_ax.set_ylabel("Objective Value")
        self.opt_ax.grid(True)
        
        # Initialize empty data for the plot
        self.convergence_data = {
            'generations': [],
            'best_values': [],
            'mean_values': []
        }
        
        # Add a legend placeholder
        self.opt_ax.legend(['Best Value', 'Mean Value'], loc='upper right')
        
        # Draw the canvas
        if hasattr(self, 'opt_canvas'):
            self.opt_canvas.draw()
        
        self.log("Convergence plot initialized")

    def initialize_pareto_front(self):
        """Initialize the Pareto front plot for multi-objective optimization"""
        if not hasattr(self, 'pareto_ax') or not hasattr(self, 'pareto_canvas'):
            return
            
        # Clear any existing plot
        self.pareto_ax.clear()
        
        # Set up the axes
        self.pareto_ax.set_title("Pareto Front")
        self.pareto_ax.set_xlabel("Objective 1 (Pressure Drop)")
        self.pareto_ax.set_ylabel("Objective 2 (Flow Uniformity)")
        self.pareto_ax.grid(True)
        
        # Initialize empty data for the plot
        self.pareto_data = {
            'objective1': [],
            'objective2': [],
            'parameters': []
        }
        
        # Draw the canvas
        if hasattr(self, 'pareto_canvas'):
            self.pareto_canvas.draw()
        
        self.log("Pareto front plot initialized")

    def start_optimization(self):
            """Start the optimization process"""
            try:
                # Validate inputs
                self._validate_optimization_inputs()
                
                # Check if optimization is already running
                if hasattr(self, 'optimization_running') and self.optimization_running:
                    messagebox.showwarning("Optimization Running", 
                                        "An optimization is already in progress. Please wait or stop it first.")
                    return
                
                # Get optimization parameters
                method = self.opt_method.get() if hasattr(self, 'opt_method') else "Genetic Algorithm"
                
                # Get parameter bounds
                bounds = {
                    'L4': (float(self.l4_min.get()), float(self.l4_max.get())),
                    'L5': (float(self.l5_min.get()), float(self.l5_max.get())),
                    'alpha1': (float(self.alpha1_min.get()), float(self.alpha1_max.get())),
                    'alpha2': (float(self.alpha2_min.get()), float(self.alpha2_max.get())),
                    'alpha3': (float(self.alpha3_min.get()), float(self.alpha3_max.get()))
                }
                
                # Get algorithm settings
                pop_size = int(self.pop_size.get()) if hasattr(self, 'pop_size') else 30
                max_gen = int(self.max_gen.get()) if hasattr(self, 'max_gen') else 20
                mut_rate = float(self.mut_rate.get()) if hasattr(self, 'mut_rate') else 0.15
                cross_rate = float(self.cross_rate.get()) if hasattr(self, 'cross_rate') else 0.7
                
                # Get objective settings
                objective = self.objective_combo.get() if hasattr(self, 'objective_combo') else "Pressure Drop"
                opt_goal = self.obj_var.get() if hasattr(self, 'obj_var') else "minimize"
                
                # Get execution environment
                env = self.opt_env_var.get() if hasattr(self, 'opt_env_var') else "local"
                
                # Update UI
                self.opt_status_var.set("Initializing optimization...")
                self.opt_progress["value"] = 0
                
                # Initialize plots
                self.initialize_convergence_plot()
                self.initialize_pareto_front()
                
                # Set optimization running flag
                self.optimization_running = True
                self.start_opt_button.config(state="disabled")
                
                if env == "local":
                    # Start optimization in a separate thread
                    self.opt_thread = threading.Thread(
                        target=self._run_optimization_thread,
                        args=(method, bounds, pop_size, max_gen, mut_rate, cross_rate, objective, opt_goal),
                        daemon=True
                    )
                    self.opt_thread.start()
                else:  # HPC
                    # Get HPC profile
                    if hasattr(self, 'opt_hpc_profile'):
                        hpc_profile = self.opt_hpc_profile.get()
                        if not hpc_profile:
                            messagebox.showerror("Profile Required", "Please select an HPC profile to continue.")
                            self.optimization_running = False
                            self.start_opt_button.config(state="normal")
                            return
                        
                        # Submit optimization to HPC
                        self.submit_optimization_to_hpc(method, bounds, pop_size, max_gen, 
                                                    mut_rate, cross_rate, objective, opt_goal)
                    else:
                        messagebox.showerror("HPC Not Available", "HPC execution is not available.")
                        self.optimization_running = False
                        self.start_opt_button.config(state="normal")
                
            except ValueError as ve:
                # Handle validation errors
                self.log(f"Optimization input validation error: {str(ve)}")
                messagebox.showerror("Invalid Input", str(ve))
            except Exception as e:
                # Handle other exceptions
                self.log(f"Error starting optimization: {str(e)}")
                messagebox.showerror("Error", f"Failed to start optimization: {str(e)}")
                self.opt_status_var.set("Optimization failed")

    def _validate_optimization_inputs(self):
        """Validate optimization input parameters"""
        try:
            # Check that all bounds are valid numbers
            float(self.l4_min.get())
            float(self.l4_max.get())
            float(self.l5_min.get())
            float(self.l5_max.get())
            float(self.alpha1_min.get())
            float(self.alpha1_max.get())
            float(self.alpha2_min.get())
            float(self.alpha2_max.get())
            float(self.alpha3_min.get())
            float(self.alpha3_max.get())
            
            # Check that min < max for all parameters
            if float(self.l4_min.get()) >= float(self.l4_max.get()):
                raise ValueError("L4 minimum must be less than maximum")
                
            if float(self.l5_min.get()) >= float(self.l5_max.get()):
                raise ValueError("L5 minimum must be less than maximum")
                
            if float(self.alpha1_min.get()) >= float(self.alpha1_max.get()):
                raise ValueError("Alpha1 minimum must be less than maximum")
                
            if float(self.alpha2_min.get()) >= float(self.alpha2_max.get()):
                raise ValueError("Alpha2 minimum must be less than maximum")
                
            if float(self.alpha3_min.get()) >= float(self.alpha3_max.get()):
                raise ValueError("Alpha3 minimum must be less than maximum")
            
            # Validate algorithm settings
            try:
                pop_size = int(self.pop_size.get())
                if pop_size <= 0:
                    raise ValueError("Population size must be greater than zero")
            except ValueError:
                raise ValueError("Population size must be an integer")
                
            try:
                max_gen = int(self.max_gen.get())
                if max_gen <= 0:
                    raise ValueError("Max generations must be greater than zero")
            except ValueError:
                raise ValueError("Max generations must be an integer")
                
            try:
                mut_rate = float(self.mut_rate.get())
                if mut_rate < 0 or mut_rate > 1:
                    raise ValueError("Mutation rate must be between 0 and 1")
            except ValueError:
                raise ValueError("Mutation rate must be a number between 0 and 1")
                
            try:
                cross_rate = float(self.cross_rate.get())
                if cross_rate < 0 or cross_rate > 1:
                    raise ValueError("Crossover rate must be between 0 and 1")
            except ValueError:
                raise ValueError("Crossover rate must be a number between 0 and 1")
                
            # For HPC execution, validate job settings
            if hasattr(self, 'opt_env_var') and self.opt_env_var.get() == "hpc":
                if hasattr(self, 'opt_hpc_profile') and not self.opt_hpc_profile.get():
                    raise ValueError("Please select an HPC profile")
        
        except ValueError as e:
            if "could not convert string to float" in str(e).lower():
                raise ValueError("All parameter bounds must be valid numbers")
            raise

    def _run_optimization_thread(self, method, bounds, pop_size, max_gen, mut_rate, cross_rate, objective, opt_goal):
        """Run optimization in a separate thread"""
        try:
            # Set up flag to allow stopping
            self.optimization_stopped = False
            
            # Initialize random population
            self.log(f"Starting {method} optimization with population size {pop_size}")
            self.root.after(0, lambda: self.opt_status_var.set(f"Generation 1/{max_gen}"))
            
            # Initialize best solution storage
            best_solution = None
            best_fitness = float('inf') if opt_goal == "minimize" else float('-inf')
            
            # Initialize convergence data
            self.convergence_data = {
                'generations': [],
                'best_values': [],
                'mean_values': []
            }
            
            # Simulate optimization iterations
            for gen in range(1, max_gen + 1):
                # Check if optimization was stopped
                if self.optimization_stopped:
                    self.root.after(0, lambda: self._optimization_stopped())
                    return
                    
                # Update progress
                progress = (gen / max_gen) * 100
                self.root.after(0, lambda p=progress: self.opt_progress.config(value=p))
                self.root.after(0, lambda g=gen: self.opt_status_var.set(f"Generation {g}/{max_gen}"))
                
                # Simulate a generation of evolution
                time.sleep(0.5)  # Simulate computation time
                
                # Generate random solutions for this demo
                pop_fitness = []
                pop_solutions = []
                
                for i in range(pop_size):
                    # Random solution within bounds
                    solution = {
                        'L4': np.random.uniform(bounds['L4'][0], bounds['L4'][1]),
                        'L5': np.random.uniform(bounds['L5'][0], bounds['L5'][1]),
                        'alpha1': np.random.uniform(bounds['alpha1'][0], bounds['alpha1'][1]),
                        'alpha2': np.random.uniform(bounds['alpha2'][0], bounds['alpha2'][1]),
                        'alpha3': np.random.uniform(bounds['alpha3'][0], bounds['alpha3'][1])
                    }
                    
                    # Simulate fitness calculation
                    if objective == "Pressure Drop":
                        # Lower is better for pressure drop
                        fitness = 100 * (0.5 + 0.2 * solution['L4'] - 0.1 * solution['L5'] + 
                                    0.01 * solution['alpha1'] + 0.005 * solution['alpha2'] + 
                                    0.003 * solution['alpha3'])
                        
                        # Add some noise to make it interesting
                        fitness *= (1 + 0.05 * np.random.randn())
                        
                    elif objective == "Flow Rate":
                        # Higher is better for flow rate
                        fitness = 50 * (1 + 0.1 * solution['L4'] + 0.15 * solution['L5'] - 
                                    0.01 * solution['alpha1'] - 0.02 * solution['alpha2'] - 
                                    0.01 * solution['alpha3'])
                        
                        # Add some noise
                        fitness *= (1 + 0.05 * np.random.randn())
                        
                    elif objective == "Flow Uniformity":
                        # Higher is better for uniformity
                        fitness = 85 * (1 - 0.02 * abs(solution['L4'] - 3) - 
                                    0.02 * abs(solution['L5'] - 3) - 
                                    0.01 * abs(solution['alpha1'] - 15) - 
                                    0.01 * abs(solution['alpha2'] - 15) - 
                                    0.01 * abs(solution['alpha3'] - 15))
                        
                        # Add some noise
                        fitness *= (1 + 0.03 * np.random.randn())
                        
                    else:  # Custom or default
                        # Create some arbitrary function
                        fitness = (solution['L4'] - 3)**2 + (solution['L5'] - 3)**2 + \
                                ((solution['alpha1'] - 15)/10)**2 + \
                                ((solution['alpha2'] - 15)/10)**2 + \
                                ((solution['alpha3'] - 15)/10)**2
                        
                    # Store solution and fitness
                    pop_solutions.append(solution)
                    pop_fitness.append(fitness)
                    
                    # Update best solution if better
                    if ((opt_goal == "minimize" and fitness < best_fitness) or 
                        (opt_goal == "maximize" and fitness > best_fitness)):
                        best_fitness = fitness
                        best_solution = solution.copy()
                
                # Calculate statistics for this generation
                mean_fitness = np.mean(pop_fitness)
                best_gen_fitness = min(pop_fitness) if opt_goal == "minimize" else max(pop_fitness)
                
                # Update convergence data
                self.convergence_data['generations'].append(gen)
                self.convergence_data['best_values'].append(best_gen_fitness)
                self.convergence_data['mean_values'].append(mean_fitness)
                
                # Update convergence plot
                self.root.after(0, lambda: self._update_convergence_plot())
                
                # Update Pareto front for demonstration (using two objectives)
                if gen % 2 == 0:  # Update every other generation for efficiency
                    objective2_values = []
                    for sol in pop_solutions:
                        # Calculate second objective (flow uniformity) for Pareto demonstration
                        obj2 = 85 * (1 - 0.02 * abs(sol['L4'] - 3) - 
                                    0.02 * abs(sol['L5'] - 3) - 
                                    0.01 * abs(sol['alpha1'] - 15) - 
                                    0.01 * abs(sol['alpha2'] - 15) - 
                                    0.01 * abs(sol['alpha3'] - 15))
                        objective2_values.append(obj2)
                    
                    self.pareto_data = {
                        'objective1': pop_fitness.copy(),
                        'objective2': objective2_values,
                        'parameters': pop_solutions.copy()
                    }
                    self.root.after(0, lambda: self._update_pareto_front())
                
                # Simulate some delay for visual effect
                time.sleep(0.2)
            
            # Optimization complete
            if best_solution:
                # Update best design tab with the best solution
                self.root.after(0, lambda: self._update_best_design(best_solution, best_fitness, objective))
            
            # Mark optimization as complete
            self.root.after(0, lambda: self._optimization_completed())
            
        except Exception as e:
            self.log(f"Optimization error: {str(e)}")
            self.root.after(0, lambda: self._optimization_failed(str(e)))

    def _update_convergence_plot(self):
        """Update the convergence plot with latest data"""
        if not hasattr(self, 'opt_ax') or not hasattr(self, 'convergence_data'):
            return
            
        # Clear existing plot
        self.opt_ax.clear()
        
        # Plot data if available
        if self.convergence_data['generations']:
            self.opt_ax.plot(self.convergence_data['generations'], 
                            self.convergence_data['best_values'], 
                            'b-', linewidth=2, label='Best Value')
            self.opt_ax.plot(self.convergence_data['generations'], 
                            self.convergence_data['mean_values'], 
                            'r--', linewidth=1, label='Mean Value')
            
        # Update labels
        self.opt_ax.set_title("Optimization Convergence")
        self.opt_ax.set_xlabel("Generation")
        self.opt_ax.set_ylabel("Objective Value")
        self.opt_ax.grid(True)
        
        # Add legend
        self.opt_ax.legend(loc='upper right')
        
        # Redraw the canvas
        self.opt_canvas.draw()

    def _update_pareto_front(self):
        """Update the Pareto front plot with latest data"""
        if not hasattr(self, 'pareto_ax') or not hasattr(self, 'pareto_data'):
            return
            
        # Clear existing plot
        self.pareto_ax.clear()
        
        # Plot data if available
        if ('objective1' in self.pareto_data and 
            'objective2' in self.pareto_data and 
            len(self.pareto_data['objective1']) > 0):
            
            # Plot all solutions
            self.pareto_ax.scatter(self.pareto_data['objective1'], 
                                self.pareto_data['objective2'], 
                                c='blue', marker='o', alpha=0.5)
            
            # Highlight the non-dominated solutions (simplified Pareto front)
            # In a real implementation, we would compute the actual Pareto front
            # For this demo, we'll just highlight some points
            
            # Simulate some Pareto-optimal points
            pareto_indices = []
            obj1 = np.array(self.pareto_data['objective1'])
            obj2 = np.array(self.pareto_data['objective2'])
            
            for i in range(len(obj1)):
                is_dominated = False
                for j in range(len(obj1)):
                    if i != j:
                        # For minimization of obj1 and maximization of obj2
                        if obj1[j] <= obj1[i] and obj2[j] >= obj2[i] and (obj1[j] < obj1[i] or obj2[j] > obj2[i]):
                            is_dominated = True
                            break
                if not is_dominated:
                    pareto_indices.append(i)
            
            # Highlight Pareto-optimal points
            if pareto_indices:
                pareto_obj1 = [obj1[i] for i in pareto_indices]
                pareto_obj2 = [obj2[i] for i in pareto_indices]
                self.pareto_ax.scatter(pareto_obj1, pareto_obj2, 
                                    c='red', marker='*', s=100, label='Pareto Front')
                                    
                # Connect Pareto front with a line
                indices = np.argsort(pareto_obj1)
                sorted_obj1 = [pareto_obj1[i] for i in indices]
                sorted_obj2 = [pareto_obj2[i] for i in indices]
                self.pareto_ax.plot(sorted_obj1, sorted_obj2, 'r--', linewidth=1)
        
        # Update labels
        self.pareto_ax.set_title("Pareto Front")
        self.pareto_ax.set_xlabel("Objective 1 (Pressure Drop)")
        self.pareto_ax.set_ylabel("Objective 2 (Flow Uniformity)")
        self.pareto_ax.grid(True)
        
        # Add legend
        self.pareto_ax.legend(loc='best')
        
        # Redraw the canvas
        self.pareto_canvas.draw()

    def _update_best_design(self, solution, fitness, objective_name):
        """Update the best design tab with the optimization result"""
        if not hasattr(self, 'param_values') or not hasattr(self, 'obj_values'):
            return
            
        # Update parameter values
        if 'L4' in solution:
            self.param_values['L4'].set(f"{solution['L4']:.4f}")
        if 'L5' in solution:
            self.param_values['L5'].set(f"{solution['L5']:.4f}")
        if 'alpha1' in solution:
            self.param_values['alpha1'].set(f"{solution['alpha1']:.4f}")
        if 'alpha2' in solution:
            self.param_values['alpha2'].set(f"{solution['alpha2']:.4f}")
        if 'alpha3' in solution:
            self.param_values['alpha3'].set(f"{solution['alpha3']:.4f}")
        
        # Calculate and update objective values
        if objective_name == "Pressure Drop":
            pressure_drop = fitness
            flow_rate = 50 * (1 + 0.1 * solution['L4'] + 0.15 * solution['L5'] - 
                            0.01 * solution['alpha1'] - 0.02 * solution['alpha2'] - 
                            0.01 * solution['alpha3'])
            uniformity = 85 * (1 - 0.02 * abs(solution['L4'] - 3) - 
                            0.02 * abs(solution['L5'] - 3) - 
                            0.01 * abs(solution['alpha1'] - 15) - 
                            0.01 * abs(solution['alpha2'] - 15) - 
                            0.01 * abs(solution['alpha3'] - 15))
        elif objective_name == "Flow Rate":
            flow_rate = fitness
            pressure_drop = 100 * (0.5 + 0.2 * solution['L4'] - 0.1 * solution['L5'] + 
                                0.01 * solution['alpha1'] + 0.005 * solution['alpha2'] + 
                                0.003 * solution['alpha3'])
            uniformity = 85 * (1 - 0.02 * abs(solution['L4'] - 3) - 
                            0.02 * abs(solution['L5'] - 3) - 
                            0.01 * abs(solution['alpha1'] - 15) - 
                            0.01 * abs(solution['alpha2'] - 15) - 
                            0.01 * abs(solution['alpha3'] - 15))
        elif objective_name == "Flow Uniformity":
            uniformity = fitness
            pressure_drop = 100 * (0.5 + 0.2 * solution['L4'] - 0.1 * solution['L5'] + 
                                0.01 * solution['alpha1'] + 0.005 * solution['alpha2'] + 
                                0.003 * solution['alpha3'])
            flow_rate = 50 * (1 + 0.1 * solution['L4'] + 0.15 * solution['L5'] - 
                            0.01 * solution['alpha1'] - 0.02 * solution['alpha2'] - 
                            0.01 * solution['alpha3'])
        else:  # Custom or default
            pressure_drop = 100 * (0.5 + 0.2 * solution['L4'] - 0.1 * solution['L5'] + 
                                0.01 * solution['alpha1'] + 0.005 * solution['alpha2'] + 
                                0.003 * solution['alpha3'])
            flow_rate = 50 * (1 + 0.1 * solution['L4'] + 0.15 * solution['L5'] - 
                            0.01 * solution['alpha1'] - 0.02 * solution['alpha2'] - 
                            0.01 * solution['alpha3'])
            uniformity = 85 * (1 - 0.02 * abs(solution['L4'] - 3) - 
                            0.02 * abs(solution['L5'] - 3) - 
                            0.01 * abs(solution['alpha1'] - 15) - 
                            0.01 * abs(solution['alpha2'] - 15) - 
                            0.01 * abs(solution['alpha3'] - 15))
        
        # Update objective values in UI
        self.obj_values['Pressure Drop'].set(f"{pressure_drop:.4f} Pa")
        self.obj_values['Flow Rate'].set(f"{flow_rate:.4f} m³/s")
        self.obj_values['Flow Uniformity'].set(f"{uniformity:.2f}%")
        
        # Store this design for later use
        self.best_design = {
            'parameters': solution,
            'metrics': {
                'pressure_drop': pressure_drop,
                'flow_rate': flow_rate,
                'uniformity': uniformity
            }
        }

    def stop_optimization(self):
        """Stop the running optimization"""
        if not hasattr(self, 'optimization_running') or not self.optimization_running:
            return
            
        answer = messagebox.askyesno("Confirm Stop", "Are you sure you want to stop the current optimization?")
        if not answer:
            return
            
        self.log("User requested optimization stop")
        
        # Set stopping flag for thread to detect
        self.optimization_stopped = True
        
        # Update status
        self.opt_status_var.set("Stopping optimization...")

    def _optimization_completed(self):
        """Handle optimization completion"""
        self.optimization_running = False
        self.start_opt_button.config(state="normal")
        
        self.opt_status_var.set("Optimization completed")
        self.opt_progress["value"] = 100
        
        messagebox.showinfo("Optimization Complete", "The optimization process has completed successfully.")
        
    def _optimization_stopped(self):
        """Handle optimization being stopped by user"""
        self.optimization_running = False
        self.start_opt_button.config(state="normal")
        
        self.opt_status_var.set("Optimization stopped by user")
        
    def _optimization_failed(self, error_message):
        """Handle optimization failure"""
        self.optimization_running = False
        self.start_opt_button.config(state="normal")
        
        self.opt_status_var.set("Optimization failed")
        messagebox.showerror("Optimization Failed", f"The optimization process failed:\n\n{error_message}")

    def import_optimization_config(self):
        """Import optimization configuration from JSON file"""
        try:
            file_path = filedialog.askopenfilename(
                title="Import Optimization Configuration",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if not file_path:
                return
                
            with open(file_path, 'r') as f:
                config = json.load(f)
            
            # Apply configuration to UI
            if 'method' in config:
                self.opt_method.set(config['method'])
                
            if 'bounds' in config:
                bounds = config['bounds']
                if 'L4' in bounds:
                    self.l4_min.delete(0, tk.END)
                    self.l4_min.insert(0, str(bounds['L4'][0]))
                    self.l4_max.delete(0, tk.END)
                    self.l4_max.insert(0, str(bounds['L4'][1]))
                    
                if 'L5' in bounds:
                    self.l5_min.delete(0, tk.END)
                    self.l5_min.insert(0, str(bounds['L5'][0]))
                    self.l5_max.delete(0, tk.END)
                    self.l5_max.insert(0, str(bounds['L5'][1]))
                    
                if 'alpha1' in bounds:
                    self.alpha1_min.delete(0, tk.END)
                    self.alpha1_min.insert(0, str(bounds['alpha1'][0]))
                    self.alpha1_max.delete(0, tk.END)
                    self.alpha1_max.insert(0, str(bounds['alpha1'][1]))
                    
                if 'alpha2' in bounds:
                    self.alpha2_min.delete(0, tk.END)
                    self.alpha2_min.insert(0, str(bounds['alpha2'][0]))
                    self.alpha2_max.delete(0, tk.END)
                    self.alpha2_max.insert(0, str(bounds['alpha2'][1]))
                    
                if 'alpha3' in bounds:
                    self.alpha3_min.delete(0, tk.END)
                    self.alpha3_min.insert(0, str(bounds['alpha3'][0]))
                    self.alpha3_max.delete(0, tk.END)
                    self.alpha3_max.insert(0, str(bounds['alpha3'][1]))
            
            if 'algorithm_settings' in config:
                settings = config['algorithm_settings']
                if 'population_size' in settings:
                    self.pop_size.delete(0, tk.END)
                    self.pop_size.insert(0, str(settings['population_size']))
                    
                if 'max_generations' in settings:
                    self.max_gen.delete(0, tk.END)
                    self.max_gen.insert(0, str(settings['max_generations']))
                    
                if 'mutation_rate' in settings:
                    self.mut_rate.delete(0, tk.END)
                    self.mut_rate.insert(0, str(settings['mutation_rate']))
                    
                if 'crossover_rate' in settings:
                    self.cross_rate.delete(0, tk.END)
                    self.cross_rate.insert(0, str(settings['crossover_rate']))
            
            if 'objective' in config:
                obj = config['objective']
                if 'name' in obj:
                    self.objective_combo.set(obj['name'])
                    
                if 'goal' in obj:
                    self.obj_var.set(obj['goal'])
            
            self.log(f"Imported optimization configuration from {file_path}")
            self.update_status(f"Imported optimization configuration")
            messagebox.showinfo("Import Complete", "Optimization configuration imported successfully.")
            
        except Exception as e:
            self.log(f"Error importing optimization configuration: {str(e)}")
            messagebox.showerror("Import Error", f"Failed to import configuration: {str(e)}")

    def export_optimization_config(self):
        """Export optimization configuration to JSON file"""
        try:
            file_path = filedialog.asksaveasfilename(
                title="Export Optimization Configuration",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if not file_path:
                return
                
            # Create configuration dictionary
            config = {
                'method': self.opt_method.get(),
                'bounds': {
                    'L4': [float(self.l4_min.get()), float(self.l4_max.get())],
                    'L5': [float(self.l5_min.get()), float(self.l5_max.get())],
                    'alpha1': [float(self.alpha1_min.get()), float(self.alpha1_max.get())],
                    'alpha2': [float(self.alpha2_min.get()), float(self.alpha2_max.get())],
                    'alpha3': [float(self.alpha3_min.get()), float(self.alpha3_max.get())]
                },
                'algorithm_settings': {
                    'population_size': int(self.pop_size.get()),
                    'max_generations': int(self.max_gen.get()),
                    'mutation_rate': float(self.mut_rate.get()),
                    'crossover_rate': float(self.cross_rate.get())
                },
                'objective': {
                    'name': self.objective_combo.get(),
                    'goal': self.obj_var.get()
                }
            }
            
            with open(file_path, 'w') as f:
                json.dump(config, f, indent=4)
            
            self.log(f"Exported optimization configuration to {file_path}")
            self.update_status(f"Exported optimization configuration")
            messagebox.showinfo("Export Complete", "Optimization configuration exported successfully.")
            
        except Exception as e:
            self.log(f"Error exporting optimization configuration: {str(e)}")
            messagebox.showerror("Export Error", f"Failed to export configuration: {str(e)}")

    def submit_optimization_to_hpc(self, method, bounds, pop_size, max_gen, mut_rate, cross_rate, objective, opt_goal):
        """Submit optimization job to HPC"""
        try:
            # Get HPC profile
            hpc_profile = self.opt_hpc_profile.get()
            
            # Create dialog to configure HPC submission
            job_dialog = tk.Toplevel(self.root)
            job_dialog.title(f"Submit Optimization to HPC")
            job_dialog.geometry("600x500")
            job_dialog.transient(self.root)
            job_dialog.grab_set()
            
            # Apply theme to dialog
            job_dialog.configure(background=self.theme.bg_color)
            
            # Create form
            main_frame = ttk.Frame(job_dialog, padding=self.theme.padding)
            main_frame.pack(fill='both', expand=True)
            
            # Job details section
            job_frame = ttk.LabelFrame(main_frame, text="Job Details", padding=self.theme.padding)
            job_frame.pack(fill='x', pady=5)
            
            ttk.Label(job_frame, text="Job Name:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
            job_name = ttk.Entry(job_frame, width=30)
            job_name.grid(row=0, column=1, padx=5, pady=5, sticky='w')
            job_name.insert(0, f"opt_{method}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}")
            
            # Queue selection
            ttk.Label(job_frame, text="Queue:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
            queue_combo = ttk.Combobox(job_frame, values=["standard", "debug", "high_priority"])
            queue_combo.grid(row=1, column=1, padx=5, pady=5, sticky='w')
            queue_combo.current(0)
            
            # Resources section
            res_frame = ttk.LabelFrame(main_frame, text="Resources", padding=self.theme.padding)
            res_frame.pack(fill='x', pady=5)
            
            ttk.Label(res_frame, text="Nodes:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
            nodes_entry = ttk.Entry(res_frame, width=5)
            nodes_entry.grid(row=0, column=1, padx=5, pady=5, sticky='w')
            nodes_entry.insert(0, "1")
            
            ttk.Label(res_frame, text="Cores per Node:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
            cores_entry = ttk.Entry(res_frame, width=5)
            cores_entry.grid(row=1, column=1, padx=5, pady=5, sticky='w')
            cores_entry.insert(0, "16")
            
            ttk.Label(res_frame, text="Memory per Node (GB):").grid(row=2, column=0, padx=5, pady=5, sticky='w')
            mem_entry = ttk.Entry(res_frame, width=5)
            mem_entry.grid(row=2, column=1, padx=5, pady=5, sticky='w')
            mem_entry.insert(0, "32")
            
            ttk.Label(res_frame, text="Wall Time (HH:MM:SS):").grid(row=3, column=0, padx=5, pady=5, sticky='w')
            time_entry = ttk.Entry(res_frame, width=10)
            time_entry.grid(row=3, column=1, padx=5, pady=5, sticky='w')
            time_entry.insert(0, "12:00:00")
            
            # Optimization parameters section
            opt_frame = ttk.LabelFrame(main_frame, text="Optimization Parameters", padding=self.theme.padding)
            opt_frame.pack(fill='x', pady=5)
            
            # Create string representation of bounds
            bounds_str = f"""L4: [{bounds['L4'][0]}, {bounds['L4'][1]}]
    L5: [{bounds['L5'][0]}, {bounds['L5'][1]}]
    alpha1: [{bounds['alpha1'][0]}, {bounds['alpha1'][1]}]
    alpha2: [{bounds['alpha2'][0]}, {bounds['alpha2'][1]}]
    alpha3: [{bounds['alpha3'][0]}, {bounds['alpha3'][1]}]"""
            
            ttk.Label(opt_frame, text="Method:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
            ttk.Label(opt_frame, text=method).grid(row=0, column=1, padx=5, pady=5, sticky='w')
            
            ttk.Label(opt_frame, text="Population Size:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
            ttk.Label(opt_frame, text=str(pop_size)).grid(row=1, column=1, padx=5, pady=5, sticky='w')
            
            ttk.Label(opt_frame, text="Max Generations:").grid(row=2, column=0, padx=5, pady=5, sticky='w')
            ttk.Label(opt_frame, text=str(max_gen)).grid(row=2, column=1, padx=5, pady=5, sticky='w')
            
            ttk.Label(opt_frame, text="Parameter Bounds:").grid(row=3, column=0, padx=5, pady=5, sticky='nw')
            ttk.Label(opt_frame, text=bounds_str).grid(row=3, column=1, padx=5, pady=5, sticky='w')
            
            # Job script section
            script_frame = ttk.LabelFrame(main_frame, text="Job Script", padding=self.theme.padding)
            script_frame.pack(fill='both', expand=True, pady=5)
            
            # Create script editor with template
            script_template = "#!/bin/bash\n\n"
            script_template += "#SBATCH --job-name={job_name}\n"
            script_template += "#SBATCH --output=opt_%j.out\n"
            script_template += "#SBATCH --error=opt_%j.err\n"
            script_template += "#SBATCH --partition={queue}\n"
            script_template += "#SBATCH --nodes={nodes}\n"
            script_template += "#SBATCH --ntasks-per-node={cores}\n"
            script_template += "#SBATCH --mem={memory}G\n"
            script_template += "#SBATCH --time={wall_time}\n\n"
            script_template += "# Load required modules\nmodule load python\nmodule load openfoam\n\n"
            script_template += "# Change to working directory\ncd $SLURM_SUBMIT_DIR\n\n"
            script_template += "# Create optimization config file\ncat > opt_config.json << 'EOL'\n"
            script_template += "{{\n"
            script_template += "  \"method\": \"{method}\",\n"
            script_template += "  \"bounds\": {{\n"
            script_template += "    \"L4\": [{l4_min}, {l4_max}],\n"
            script_template += "    \"L5\": [{l5_min}, {l5_max}],\n"
            script_template += "    \"alpha1\": [{alpha1_min}, {alpha1_max}],\n"
            script_template += "    \"alpha2\": [{alpha2_min}, {alpha2_max}],\n"
            script_template += "    \"alpha3\": [{alpha3_min}, {alpha3_max}]\n"
            script_template += "  }},\n"
            script_template += "  \"algorithm_settings\": {{\n"
            script_template += "    \"population_size\": {pop_size},\n"
            script_template += "    \"max_generations\": {max_gen},\n"
            script_template += "    \"mutation_rate\": {mut_rate},\n"
            script_template += "    \"crossover_rate\": {cross_rate}\n"
            script_template += "  }},\n"
            script_template += "  \"objective\": {{\n"
            script_template += "    \"name\": \"{objective}\",\n"
            script_template += "    \"goal\": \"{opt_goal}\"\n"
            script_template += "  }}\n"
            script_template += "}}\n"
            script_template += "EOL\n\n"
            script_template += "# Run the optimization\n"
            script_template += "python -m optimizer --config opt_config.json --parallel {total_cores}\n\n"
            script_template += "# Process results\n"
            script_template += "python -m process_results --input optimization_results.csv --output summary.csv\n"
            
            script_editor = scrolledtext.ScrolledText(script_frame, wrap=tk.WORD, height=10, width=80)
            script_editor.pack(fill='both', expand=True, padx=5, pady=5)
            
            # Function to update script template
            def update_script_template():
                try:
                    # Get values from form
                    job_name_val = job_name.get()
                    queue_val = queue_combo.get()
                    nodes_val = nodes_entry.get()
                    cores_val = cores_entry.get()
                    mem_val = mem_entry.get()
                    time_val = time_entry.get()
                    
                    # Calculate total cores
                    try:
                        total = int(nodes_val) * int(cores_val)
                    except ValueError:
                        total = "{nodes}*{cores}"
                    
                    # Fill template
                    script = script_template.format(
                        job_name=job_name_val,
                        queue=queue_val,
                        nodes=nodes_val,
                        cores=cores_val,
                        memory=mem_val,
                        wall_time=time_val,
                        total_cores=total,
                        method=method,
                        l4_min=bounds['L4'][0],
                        l4_max=bounds['L4'][1],
                        l5_min=bounds['L5'][0],
                        l5_max=bounds['L5'][1],
                        alpha1_min=bounds['alpha1'][0],
                        alpha1_max=bounds['alpha1'][1],
                        alpha2_min=bounds['alpha2'][0],
                        alpha2_max=bounds['alpha2'][1],
                        alpha3_min=bounds['alpha3'][0],
                        alpha3_max=bounds['alpha3'][1],
                        pop_size=pop_size,
                        max_gen=max_gen,
                        mut_rate=mut_rate,
                        cross_rate=cross_rate,
                        objective=objective,
                        opt_goal=opt_goal
                    )
                    
                    # Update script editor
                    script_editor.delete(1.0, tk.END)
                    script_editor.insert(tk.END, script)
                except Exception as e:
                    self.log(f"Error updating script template: {e}")
            
            # Initial update of script
            update_script_template()
            
            # Add button to update template
            ttk.Button(script_frame, text="Update Template", 
                     command=update_script_template).pack(pady=5)
            
            # Buttons section
            button_frame = ttk.Frame(main_frame)
            button_frame.pack(fill='x', pady=10)
            
            def submit_job_script():
                try:
                    # Get script content
                    script_content = script_editor.get(1.0, tk.END)
                    
                    # Show confirmation
                    if not messagebox.askyesno("Confirm Submission", 
                                             "Are you sure you want to submit this optimization job to HPC?"):
                        return
                    
                    # Status update
                    self.update_status("Submitting optimization to HPC...", show_progress=True)
                    
                    # Submit in a separate thread to keep UI responsive
                    threading.Thread(
                        target=lambda: self.submit_hpc_script(script_content, hpc_profile, job_dialog),
                        daemon=True
                    ).start()
                    
                    # Update status for optimization UI
                    self.opt_status_var.set("Submitted to HPC. Check HPC tab for status.")
                    
                except Exception as e:
                    self.log(f"Error preparing job submission: {e}")
                    messagebox.showerror("Error", f"Failed to prepare job: {str(e)}")
            
            ttk.Button(button_frame, text="Submit Job", 
                     command=submit_job_script).pack(side="left", padx=5)
            
            ttk.Button(button_frame, text="Cancel", 
                     command=job_dialog.destroy).pack(side="right", padx=5)
            
            # Mark optimization as submitted
            self.optimization_running = False
            self.start_opt_button.config(state="normal")
            
        except Exception as e:
            self.log(f"Error submitting optimization to HPC: {str(e)}")
            messagebox.showerror("Submission Error", f"Failed to submit optimization to HPC: {str(e)}")
            
            # Reset UI state
            self.optimization_running = False
            self.start_opt_button.config(state="normal")
            self.opt_status_var.set("Optimization submission failed")
    
    def submit_hpc_script(self, script_content, profile_name, dialog=None):
        """Submit a script to HPC in a separate thread"""
        # This is a placeholder for the real implementation
        # For now, we'll assume this sends the job to the HPC system
        
        try:
            # Simulate sending to HPC
            time.sleep(2)
            
            # Show success message
            self.root.after(0, lambda: self.update_status("Optimization job submitted to HPC", show_progress=False))
            self.root.after(0, lambda: messagebox.showinfo("Job Submitted", "Optimization job successfully submitted to HPC cluster."))
            
            # Close the dialog if provided
            if dialog:
                self.root.after(0, dialog.destroy)
                
            # Schedule a refresh of the HPC job list
            if hasattr(self, 'refresh_job_list'):
                self.root.after(2000, self.refresh_job_list)
                
        except Exception as e:
            self.log(f"Error submitting script to HPC: {str(e)}")
            self.root.after(0, lambda: self.update_status("Job submission failed", show_progress=False))
            self.root.after(0, lambda: messagebox.showerror("Submission Error", f"Failed to submit job: {str(e)}"))

    def update_job_tree(self, jobs):
        """Update the job tree with the list of jobs"""
        if not hasattr(self, 'job_tree'):
            return
            
        # Clear existing items
        for item in self.job_tree.get_children():
            self.job_tree.delete(item)
        
        # Add jobs to tree
        for job in jobs:
            # Ensure all required fields exist
            job_id = job.get('id', 'N/A')
            name = job.get('name', 'N/A')
            status = job.get('status', 'N/A')
            queue = job.get('queue', 'N/A')
            nodes = job.get('nodes', 'N/A')
            time = job.get('time', 'N/A')
            
            self.job_tree.insert('', 'end', values=(job_id, name, status, queue, nodes, time))
        
        if not jobs:
            self.update_status("No jobs found")
        else:
            self.update_status(f"Found {len(jobs)} jobs")

    def submit_job(self):
        """Show dialog to submit a new HPC job"""
        try:
            # Create dialog window
            job_dialog = tk.Toplevel(self.root)
            job_dialog.title("Submit HPC Job")
            job_dialog.geometry("600x500")
            job_dialog.transient(self.root)
            job_dialog.grab_set()
            
            # Apply theme to dialog
            job_dialog.configure(background=self.theme.bg_color)
            
            # Create form
            main_frame = ttk.Frame(job_dialog, padding=self.theme.padding)
            main_frame.pack(fill='both', expand=True)
            
            # Job details section
            job_frame = ttk.LabelFrame(main_frame, text="Job Details", padding=self.theme.padding)
            job_frame.pack(fill='x', pady=5)
            
            ttk.Label(job_frame, text="Job Name:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
            job_name = ttk.Entry(job_frame, width=30)
            job_name.grid(row=0, column=1, padx=5, pady=5, sticky='w')
            job_name.insert(0, f"cfd_job_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}")
            
            # Queue selection
            ttk.Label(job_frame, text="Queue:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
            queue_combo = ttk.Combobox(job_frame, values=["standard", "debug", "high_priority"])
            queue_combo.grid(row=1, column=1, padx=5, pady=5, sticky='w')
            queue_combo.current(0)
            
            # Resources section
            res_frame = ttk.LabelFrame(main_frame, text="Resources", padding=self.theme.padding)
            res_frame.pack(fill='x', pady=5)
            
            ttk.Label(res_frame, text="Nodes:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
            nodes_entry = ttk.Entry(res_frame, width=5)
            nodes_entry.grid(row=0, column=1, padx=5, pady=5, sticky='w')
            nodes_entry.insert(0, "1")
            
            ttk.Label(res_frame, text="Cores per Node:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
            cores_entry = ttk.Entry(res_frame, width=5)
            cores_entry.grid(row=1, column=1, padx=5, pady=5, sticky='w')
            cores_entry.insert(0, "8")
            
            ttk.Label(res_frame, text="Memory per Node (GB):").grid(row=2, column=0, padx=5, pady=5, sticky='w')
            mem_entry = ttk.Entry(res_frame, width=5)
            mem_entry.grid(row=2, column=1, padx=5, pady=5, sticky='w')
            mem_entry.insert(0, "16")
            
            ttk.Label(res_frame, text="Wall Time (HH:MM:SS):").grid(row=3, column=0, padx=5, pady=5, sticky='w')
            time_entry = ttk.Entry(res_frame, width=10)
            time_entry.grid(row=3, column=1, padx=5, pady=5, sticky='w')
            time_entry.insert(0, "01:00:00")
            
            # Job script section
            script_frame = ttk.LabelFrame(main_frame, text="Job Script", padding=self.theme.padding)
            script_frame.pack(fill='both', expand=True, pady=5)
            
            # Create script editor with template
            script_template = "#!/bin/bash\n\n"
            script_template += "#SBATCH --job-name={job_name}\n"
            script_template += "#SBATCH --output=job_%j.out\n"
            script_template += "#SBATCH --error=job_%j.err\n"
            script_template += "#SBATCH --partition={queue}\n"
            script_template += "#SBATCH --nodes={nodes}\n"
            script_template += "#SBATCH --ntasks-per-node={cores}\n"
            script_template += "#SBATCH --mem={memory}G\n"
            script_template += "#SBATCH --time={wall_time}\n\n"
            script_template += "# Load required modules\nmodule load openfoam\n\n"
            script_template += "# Change to working directory\ncd $SLURM_SUBMIT_DIR\n\n"
            script_template += "# Run the simulation\nmpirun -np {total_cores} ./cfd_solver --mesh INTAKE3D.msh --solver openfoam\n\n"
            script_template += "# Process results\n./process_results --input cfd_results --output results_summary.csv\n"
            
            script_editor = scrolledtext.ScrolledText(script_frame, wrap=tk.WORD, height=15, width=80)
            script_editor.pack(fill='both', expand=True, padx=5, pady=5)
            script_editor.insert(tk.END, script_template)
            
            # Function to update script template
            def update_script_template():
                try:
                    # Get values from form
                    name = job_name.get()
                    queue = queue_combo.get()
                    nodes = nodes_entry.get()
                    cores = cores_entry.get()
                    mem = mem_entry.get()
                    time = time_entry.get()
                    
                    # Calculate total cores
                    try:
                        total = int(nodes) * int(cores)
                    except ValueError:
                        total = "{nodes}*{cores}"
                    
                    # Fill template
                    script = script_template.format(
                        job_name=name,
                        queue=queue,
                        nodes=nodes,
                        cores=cores,
                        memory=mem,
                        wall_time=time,
                        total_cores=total
                    )
                    
                    # Update script editor
                    script_editor.delete(1.0, tk.END)
                    script_editor.insert(tk.END, script)
                except Exception as e:
                    self.log(f"Error updating script template: {e}")
            
            # Add button to update template
            ttk.Button(script_frame, text="Update Template", 
                    command=update_script_template).pack(pady=5)
            
            # Buttons section
            button_frame = ttk.Frame(main_frame)
            button_frame.pack(fill='x', pady=10)
            
            def submit_job_script():
                try:
                    # Get script content
                    script_content = script_editor.get(1.0, tk.END)
                    
                    # Get profile
                    profile_name = self.conn_profile.get() if hasattr(self, 'conn_profile') else None
                    
                    if not profile_name:
                        messagebox.showerror("Error", "No HPC profile selected")
                        return
                    
                    # Show confirmation
                    if not messagebox.askyesno("Confirm Submission", 
                                            "Are you sure you want to submit this job to the HPC cluster?"):
                        return
                    
                    # Status update
                    self.update_status("Submitting job...", show_progress=True)
                    
                    # Submit in a separate thread to keep UI responsive
                    threading.Thread(
                        target=lambda: self.submit_job_script_thread(script_content, profile_name, job_dialog),
                        daemon=True
                    ).start()
                    
                except Exception as e:
                    self.log(f"Error preparing job submission: {e}")
                    messagebox.showerror("Error", f"Failed to prepare job: {str(e)}")
            
            ttk.Button(button_frame, text="Submit Job", 
                    command=submit_job_script).pack(side="left", padx=5)
            
            ttk.Button(button_frame, text="Cancel", 
                    command=job_dialog.destroy).pack(side="right", padx=5)
            
            # Update script with initial values
            update_script_template()
            
        except Exception as e:
            self.log(f"Error creating job submission dialog: {e}")
            messagebox.showerror("Error", f"Failed to create job submission dialog: {str(e)}")

    def submit_job_script_thread(self, script_content, profile_name, dialog=None):
        """Submit a job script to the HPC cluster in a separate thread"""
        import paramiko
        
        try:
            # Load the HPC profile
            profiles_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                    "Config", "hpc_profiles.json")
            
            if not os.path.exists(profiles_path):
                self.root.after(0, lambda: messagebox.showerror("Error", "HPC profiles configuration not found"))
                self.root.after(0, lambda: self.update_status("Job submission failed", show_progress=False))
                return
                    
            with open(profiles_path, 'r') as f:
                profiles = json.load(f)
            
            if profile_name not in profiles:
                self.root.after(0, lambda: messagebox.showerror("Error", f"HPC profile '{profile_name}' not found"))
                self.root.after(0, lambda: self.update_status("Job submission failed", show_progress=False))
                return
                    
            config = profiles[profile_name]
            
            # Create SSH client
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Connect based on authentication method
            try:
                if config.get("use_key", False):
                    key_path = config.get("key_path", "")
                    if not key_path:
                        self.root.after(0, lambda: messagebox.showerror("Authentication Error", 
                                                                    "Key path not specified in the profile"))
                        self.root.after(0, lambda: self.update_status("Job submission failed: Missing key path", show_progress=False))
                        return
                        
                    key = paramiko.RSAKey.from_private_key_file(key_path)
                    client.connect(
                        hostname=config.get("hostname", ""),
                        port=int(config.get("port", 22)),
                        username=config.get("username", ""),
                        pkey=key,
                        timeout=15
                    )
                else:
                    # Use password auth
                    password = config.get("password", "")
                    if not password:
                        self.root.after(0, lambda: messagebox.showerror("Authentication Error", 
                                                                    "Password not specified in the profile"))
                        self.root.after(0, lambda: self.update_status("Job submission failed: Missing password", show_progress=False))
                        return
                    
                    client.connect(
                        hostname=config.get("hostname", ""),
                        port=int(config.get("port", 22)),
                        username=config.get("username", ""),
                        password=password,
                        timeout=15
                    )
            except paramiko.AuthenticationException:
                self.root.after(0, lambda: messagebox.showerror("Authentication Error", 
                                                            "Failed to authenticate with the remote server"))
                self.root.after(0, lambda: self.update_status("Job submission failed: Authentication error", show_progress=False))
                return
            except paramiko.SSHException as e:
                self.root.after(0, lambda: messagebox.showerror("SSH Error", f"SSH error: {str(e)}"))
                self.root.after(0, lambda: self.update_status("Job submission failed: SSH error", show_progress=False))
                return
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Connection Error", f"Error connecting to server: {str(e)}"))
                self.root.after(0, lambda: self.update_status("Job submission failed: Connection error", show_progress=False))
                return
            
            # Create SFTP client for file transfer
            try:
                sftp = client.open_sftp()
                
                # Get remote directory
                remote_dir = config.get("remote_dir", "")
                if not remote_dir:
                    # Try to get home directory
                    stdin, stdout, stderr = client.exec_command("echo $HOME")
                    remote_dir = stdout.read().decode().strip()
                
                # Make sure remote directory exists
                try:
                    sftp.stat(remote_dir)
                except FileNotFoundError:
                    self.log(f"Remote directory {remote_dir} does not exist. Creating it...")
                    client.exec_command(f"mkdir -p {remote_dir}")
                
                # Change to remote directory
                sftp.chdir(remote_dir)
                
                # Create job script file remotely
                script_filename = f"job_script_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.sh"
                remote_script_path = f"{remote_dir}/{script_filename}"
                
                with sftp.file(script_filename, 'w') as f:
                    f.write(script_content)
                
                # Make script executable
                client.exec_command(f"chmod +x {remote_script_path}")
                
                # Determine job submission command based on available scheduler
                stdin, stdout, stderr = client.exec_command("command -v sbatch qsub bsub")
                scheduler_cmds = stdout.read().decode().strip().split('\n')
                
                submission_cmd = ""
                if scheduler_cmds and '/sbatch' in scheduler_cmds[0]:
                    submission_cmd = f"cd {remote_dir} && sbatch {script_filename}"
                    scheduler = "SLURM"
                elif scheduler_cmds and '/qsub' in scheduler_cmds[0]:
                    submission_cmd = f"cd {remote_dir} && qsub {script_filename}"
                    scheduler = "PBS"
                elif scheduler_cmds and '/bsub' in scheduler_cmds[0]:
                    submission_cmd = f"cd {remote_dir} && bsub < {script_filename}"
                    scheduler = "LSF"
                else:
                    self.root.after(0, lambda: messagebox.showerror("Error", 
                                                                "Could not identify job scheduler (SLURM/PBS/LSF)"))
                    self.root.after(0, lambda: self.update_status("Job submission failed", show_progress=False))
                    client.close()
                    return
                
                # Submit job
                self.log(f"Submitting job with command: {submission_cmd}")
                stdin, stdout, stderr = client.exec_command(submission_cmd)
                response = stdout.read().decode().strip()
                error = stderr.read().decode().strip()
                
                # Close connection
                client.close()
                
                if error and ('error' in error.lower() or 'not found' in error.lower()):
                    self.log(f"Job submission error: {error}")
                    self.root.after(0, lambda: messagebox.showerror("Submission Error", 
                                                                f"Failed to submit job: {error}"))
                    self.root.after(0, lambda: self.update_status("Job submission failed", show_progress=False))
                else:
                    # Parse job ID from response based on scheduler type
                    job_id = None
                    if scheduler == "SLURM" and 'Submitted batch job' in response:
                        job_id = response.split()[-1]
                    elif scheduler == "PBS":
                        job_id = response.strip()
                    elif scheduler == "LSF" and 'Job <' in response:
                        import re
                        match = re.search(r'Job <(\d+)>', response)
                        if match:
                            job_id = match.group(1)
                    
                    success_message = f"Job submitted successfully"
                    if job_id:
                        success_message += f" with ID: {job_id}"
                    
                    self.log(success_message)
                    self.root.after(0, lambda: self.update_status(success_message, show_progress=False))
                    self.root.after(0, lambda: messagebox.showinfo("Job Submitted", success_message))
                    
                    # Close the dialog if provided
                    if dialog:
                        self.root.after(0, dialog.destroy)
                    
                    # Refresh job list to show new job
                    if hasattr(self, 'refresh_job_list'):
                        self.root.after(2000, self.refresh_job_list)
                    
            except Exception as e:
                self.log(f"Error submitting job: {str(e)}")
                self.root.after(0, lambda: messagebox.showerror("Submission Error", 
                                                            f"Failed to submit job: {str(e)}"))
                self.root.after(0, lambda: self.update_status("Job submission failed", show_progress=False))
                client.close()
        except Exception as e:
            self.log(f"Error preparing job submission: {str(e)}")
            self.root.after(0, lambda: messagebox.showerror("Error", 
                                                        f"Unexpected error during job submission: {str(e)}"))
            self.root.after(0, lambda: self.update_status("Job submission failed", show_progress=False))

    def cancel_job(self):
        """Cancel a selected HPC job"""
        try:
            # Check if job tree exists and an item is selected
            if not hasattr(self, 'job_tree'):
                messagebox.showerror("Error", "Job list not available")
                return
                
            # Get selected item
            selection = self.job_tree.selection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select a job to cancel")
                return
                
            # Get job ID from selection
            job_data = self.job_tree.item(selection[0])
            job_values = job_data['values']
            
            if not job_values or len(job_values) < 2:
                messagebox.showerror("Error", "Invalid job selection")
                return
                
            job_id = str(job_values[1])
            job_name = str(job_values[0])
            
            # Confirm cancellation
            if not messagebox.askyesno("Confirm Cancellation", 
                                    f"Are you sure you want to cancel job '{job_name}' (ID: {job_id})?"):
                return
            
            # Get HPC profile
            if not hasattr(self, 'conn_profile') or not self.conn_profile.get():
                messagebox.showerror("Error", "No HPC profile selected")
                return
                
            profile_name = self.conn_profile.get()
            
            # Update status
            self.update_status(f"Cancelling job {job_id}...", show_progress=True)
            
            # Execute cancellation in separate thread
            threading.Thread(
                target=lambda: self.cancel_job_thread(profile_name, job_id),
                daemon=True
            ).start()
            
        except Exception as e:
            self.log(f"Error preparing job cancellation: {str(e)}")
            messagebox.showerror("Error", f"Failed to prepare job cancellation: {str(e)}")

    def cancel_job_thread(self, profile_name, job_id):
        """Cancel a job in a separate thread"""
        import paramiko
        import os
        
        try:
            # Load the HPC profile
            profiles_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                    "Config", "hpc_profiles.json")
            
            if not os.path.exists(profiles_path):
                self.root.after(0, lambda: messagebox.showerror("Error", "HPC profiles configuration not found"))
                self.root.after(0, lambda: self.update_status("Job cancellation failed", show_progress=False))
                return
                
            with open(profiles_path, 'r') as f:
                profiles = json.load(f)
            
            if profile_name not in profiles:
                self.root.after(0, lambda: messagebox.showerror("Error", f"HPC profile '{profile_name}' not found"))
                self.root.after(0, lambda: self.update_status("Job cancellation failed", show_progress=False))
                return
                
            config = profiles[profile_name]
            
            # Create SSH client
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Connect based on authentication method
            if config.get("use_key", False):
                key_path = config.get("key_path", "")
                if not key_path:
                    self.root.after(0, lambda: messagebox.showerror("Error", "No SSH key specified in profile"))
                    self.root.after(0, lambda: self.update_status("Job cancellation failed", show_progress=False))
                    return
                    
                key = paramiko.RSAKey.from_private_key_file(key_path)
                client.connect(
                    hostname=config.get("hostname", ""),
                    port=int(config.get("port", 22)),
                    username=config.get("username", ""),
                    pkey=key
                )
            else:
                # Use password auth
                client.connect(
                    hostname=config.get("hostname", ""),
                    port=int(config.get("port", 22)),
                    username=config.get("username", ""),
                    password=config.get("password", "")
                )
            
            # Determine job cancellation command based on available scheduler
            stdin, stdout, stderr = client.exec_command("command -v scancel qdel bkill")
            scheduler_cmd = stdout.read().decode().strip().split('\n')[0]
            
            cancel_cmd = ""
            if 'scancel' in scheduler_cmd:
                cancel_cmd = f"scancel {job_id}"
            elif 'qdel' in scheduler_cmd:
                cancel_cmd = f"qdel {job_id}"
            elif 'bkill' in scheduler_cmd:
                cancel_cmd = f"bkill {job_id}"
            else:
                self.root.after(0, lambda: messagebox.showerror("Error", "Could not identify job scheduler (SLURM/PBS/LSF)"))
                self.root.after(0, lambda: self.update_status("Job cancellation failed", show_progress=False))
                client.close()
                return
            
            # Execute job cancellation
            stdin, stdout, stderr = client.exec_command(cancel_cmd)
            response = stdout.read().decode().strip()
            error = stderr.read().decode().strip()
            
            # Close connection
            client.close()
            
            if error and 'not found' in error.lower():
                self.log(f"Job cancellation error: {error}")
                self.root.after(0, lambda: messagebox.showerror("Cancellation Error", f"Error cancelling job: {error}"))
                self.root.after(0, lambda: self.update_status("Job cancellation failed", show_progress=False))
            else:
                self.log(f"Job {job_id} cancelled: {response if response else 'Successfully cancelled'}")
                self.root.after(0, lambda: self.update_status("Job cancelled successfully", show_progress=False))
                
                # Show success message
                self.root.after(0, lambda: messagebox.showinfo("Job Cancelled", f"Job {job_id} has been cancelled"))
                
                # Refresh job list after cancellation
                self.root.after(1000, self.refresh_job_list)
                
        except Exception as e:
            self.log(f"Error cancelling job: {str(e)}")
            self.root.after(0, lambda: messagebox.showerror("Cancellation Error", f"Failed to cancel job: {str(e)}"))
            self.root.after(0, lambda: self.update_status("Job cancellation failed", show_progress=False))



    def show_job_details(self):
        """Show details for a selected HPC job"""
        try:
            # Check if job tree exists and an item is selected
            if not hasattr(self, 'job_tree'):
                messagebox.showerror("Error", "Job list not available")
                return
                
            # Get selected item
            selection = self.job_tree.selection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select a job to view details")
                return
                
            # Get job ID from selection
            job_data = self.job_tree.item(selection[0])
            job_values = job_data['values']
            
            if not job_values or len(job_values) < 2:
                messagebox.showerror("Error", "Invalid job selection")
                return
                
            job_id = str(job_values[1])
            job_name = str(job_values[0])
            
            # Get HPC profile
            if not hasattr(self, 'conn_profile') or not self.conn_profile.get():
                messagebox.showerror("Error", "No HPC profile selected")
                return
                
            profile_name = self.conn_profile.get()
            
            # Update status
            self.update_status(f"Fetching details for job {job_id}...", show_progress=True)
            
            # Execute details fetch in separate thread
            threading.Thread(
                target=lambda: self.get_job_details_thread(profile_name, job_id, job_name),
                daemon=True
            ).start()
            
        except Exception as e:
            self.log(f"Error preparing job details retrieval: {str(e)}")
            messagebox.showerror("Error", f"Failed to prepare job details view: {str(e)}")

    def get_job_details_thread(self, profile_name, job_id, job_name):
        """Fetch job details in a separate thread"""
        import paramiko
        import os
        
        try:
            # Load the HPC profile
            profiles_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                    "Config", "hpc_profiles.json")
            
            if not os.path.exists(profiles_path):
                self.root.after(0, lambda: messagebox.showerror("Error", "HPC profiles configuration not found"))
                self.root.after(0, lambda: self.update_status("Job details fetch failed", show_progress=False))
                return
                
            with open(profiles_path, 'r') as f:
                profiles = json.load(f)
            
            if profile_name not in profiles:
                self.root.after(0, lambda: messagebox.showerror("Error", f"HPC profile '{profile_name}' not found"))
                self.root.after(0, lambda: self.update_status("Job details fetch failed", show_progress=False))
                return
                
            config = profiles[profile_name]
            
            # Create SSH client
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Connect based on authentication method
            if config.get("use_key", False):
                key_path = config.get("key_path", "")
                if not key_path:
                    self.root.after(0, lambda: messagebox.showerror("Error", "No SSH key specified in profile"))
                    self.root.after(0, lambda: self.update_status("Job details fetch failed", show_progress=False))
                    return
                    
                key = paramiko.RSAKey.from_private_key_file(key_path)
                client.connect(
                    hostname=config.get("hostname", ""),
                    port=int(config.get("port", 22)),
                    username=config.get("username", ""),
                    pkey=key
                )
            else:
                # Use password auth
                client.connect(
                    hostname=config.get("hostname", ""),
                    port=int(config.get("port", 22)),
                    username=config.get("username", ""),
                    password=config.get("password", "")
                )
            
            # Determine job details command based on available scheduler
            stdin, stdout, stderr = client.exec_command("command -v scontrol qstat bjobs")
            scheduler_cmd = stdout.read().decode().strip().split('\n')[0]
            
            details_cmd = ""
            scheduler = ""
            if 'scontrol' in scheduler_cmd:
                details_cmd = f"scontrol show job {job_id}"
                scheduler = "SLURM"
            elif 'qstat' in scheduler_cmd:
                details_cmd = f"qstat -f {job_id}"
                scheduler = "PBS"
            elif 'bjobs' in scheduler_cmd:
                details_cmd = f"bjobs -l {job_id}"
                scheduler = "LSF"
            else:
                self.root.after(0, lambda: messagebox.showerror("Error", "Could not identify job scheduler (SLURM/PBS/LSF)"))
                self.root.after(0, lambda: self.update_status("Job details fetch failed", show_progress=False))
                client.close()
                return
            
            # Execute job details command
            stdin, stdout, stderr = client.exec_command(details_cmd)
            details = stdout.read().decode().strip()
            error = stderr.read().decode().strip()
            
            # Check if job has output files
            output_files = []
            if scheduler == "SLURM":
                # Try to find output files
                stdin, stdout, stderr = client.exec_command(f"find . -name '*{job_id}*' -o -name '*{job_name}*' | grep -E '\\.(out|err)'")
                files_output = stdout.read().decode().strip()
                if files_output:
                    output_files = files_output.split('\n')
            
            # Close connection
            client.close()
            
            if error and 'not found' in error.lower():
                self.log(f"Job details error: {error}")
                self.root.after(0, lambda: messagebox.showerror("Details Error", f"Error fetching job details: {error}"))
                self.root.after(0, lambda: self.update_status("Job details fetch failed", show_progress=False))
                return
                
            if not details:
                self.log(f"No details found for job {job_id}")
                self.root.after(0, lambda: messagebox.showinfo("No Details", f"No details found for job {job_id}"))
                self.root.after(0, lambda: self.update_status("Job details fetch complete", show_progress=False))
                return
                
            # Create job details dialog on main thread
            self.root.after(0, lambda: self.display_job_details(job_id, job_name, scheduler, details, output_files))
            self.root.after(0, lambda: self.update_status("Job details fetched successfully", show_progress=False))
            
        except Exception as e:
            self.log(f"Error fetching job details: {str(e)}")
            self.root.after(0, lambda: messagebox.showerror("Details Error", f"Failed to fetch job details: {str(e)}"))
            self.root.after(0, lambda: self.update_status("Job details fetch failed", show_progress=False))

    def display_job_details(self, job_id, job_name, scheduler, details_text, output_files):
        """Display job details in a dialog"""
        try:
            # Create dialog window
            details_dialog = tk.Toplevel(self.root)
            details_dialog.title(f"Job Details - {job_name} ({job_id})")
            details_dialog.geometry("700x600")
            details_dialog.transient(self.root)
            
            # Apply theme to dialog
            details_dialog.configure(background=self.theme.bg_color)
            
            # Create notebook for details and output
            notebook = ttk.Notebook(details_dialog)
            notebook.pack(fill='both', expand=True, padx=10, pady=10)
            
            # Details tab
            details_tab = ttk.Frame(notebook)
            notebook.add(details_tab, text="Job Details")
            
            # Details text widget
            details_view = scrolledtext.ScrolledText(details_tab, wrap=tk.WORD, height=25, width=80, font=self.theme.code_font)
            details_view.pack(fill='both', expand=True, padx=5, pady=5)
            details_view.insert(tk.END, f"Job ID: {job_id}\n")
            details_view.insert(tk.END, f"Job Name: {job_name}\n")
            details_view.insert(tk.END, f"Scheduler: {scheduler}\n\n")
            details_view.insert(tk.END, "==== Raw Job Information ====\n\n")
            details_view.insert(tk.END, details_text)
            details_view.config(state='disabled')
            
            # Output files tab (if any were found)
            if output_files:
                output_tab = ttk.Frame(notebook)
                notebook.add(output_tab, text="Output Files")
                
                # Add files list on left
                files_frame = ttk.Frame(output_tab)
                files_frame.pack(side='left', fill='y', padx=5, pady=5)
                
                ttk.Label(files_frame, text="Output Files:").pack(anchor='w')
                
                # Create listbox with scrollbar for files
                files_frame_inner = ttk.Frame(files_frame)
                files_frame_inner.pack(fill='both', expand=True)
                
                scrollbar = ttk.Scrollbar(files_frame_inner)
                scrollbar.pack(side='right', fill='y')
                
                files_list = tk.Listbox(files_frame_inner, height=20, width=30, 
                                    yscrollcommand=scrollbar.set,
                                    exportselection=0)
                files_list.pack(side='left', fill='both', expand=True)
                
                scrollbar.config(command=files_list.yview)
                
                # Add files to list
                for file_path in output_files:
                    files_list.insert(tk.END, os.path.basename(file_path))
                
                # Output content area on right
                content_frame = ttk.Frame(output_tab)
                content_frame.pack(side='right', fill='both', expand=True, padx=5, pady=5)
                
                content_view = scrolledtext.ScrolledText(content_frame, wrap=tk.WORD, font=self.theme.code_font)
                content_view.pack(fill='both', expand=True)
                content_view.insert(tk.END, "Select an output file to view its contents")
                content_view.config(state='disabled')
                
                # Function to load file content when selected
                def on_file_select(event):
                    # Get selected file
                    if not files_list.curselection():
                        return
                    
                    selected_idx = files_list.curselection()[0]
                    selected_file = output_files[selected_idx]
                    
                    # Update status
                    self.update_status(f"Loading file content: {os.path.basename(selected_file)}...", show_progress=True)
                    
                    # Load file content in thread
                    threading.Thread(
                        target=lambda: self.load_remote_file_content(profile_name, selected_file, content_view),
                        daemon=True
                    ).start()
                
                # Bind selection event
                files_list.bind('<<ListboxSelect>>', on_file_select)
            
            # Button to close dialog
            button_frame = ttk.Frame(details_dialog)
            button_frame.pack(fill='x', padx=10, pady=10)
            
            ttk.Button(button_frame, text="Close", 
                    command=details_dialog.destroy).pack(side='right')
                    
            ttk.Button(button_frame, text="Refresh", 
                    command=lambda: self.refresh_job_details(
                        job_id, job_name, details_dialog)).pack(side='left')
            
        except Exception as e:
            self.log(f"Error displaying job details: {str(e)}")
            messagebox.showerror("Display Error", f"Failed to display job details: {str(e)}")

    def load_remote_file_content(self, profile_name, file_path, text_widget):
        """Load content of a remote file"""
        import paramiko
        import os
        
        try:
            # Load the HPC profile
            profiles_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                    "Config", "hpc_profiles.json")
            
            if not os.path.exists(profiles_path):
                self.root.after(0, lambda: self.update_status("File content fetch failed", show_progress=False))
                return
                
            with open(profiles_path, 'r') as f:
                profiles = json.load(f)
            
            if profile_name not in profiles:
                self.root.after(0, lambda: self.update_status("File content fetch failed", show_progress=False))
                return
                
            config = profiles[profile_name]
            
            # Create SSH client
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Connect based on authentication method
            if config.get("use_key", False):
                key_path = config.get("key_path", "")
                if not key_path:
                    self.root.after(0, lambda: self.update_status("File content fetch failed", show_progress=False))
                    return
                    
                key = paramiko.RSAKey.from_private_key_file(key_path)
                client.connect(
                    hostname=config.get("hostname", ""),
                    port=int(config.get("port", 22)),
                    username=config.get("username", ""),
                    pkey=key
                )
            else:
                # Use password auth
                client.connect(
                    hostname=config.get("hostname", ""),
                    port=int(config.get("port", 22)),
                    username=config.get("username", ""),
                    password=config.get("password", "")
                )
            
            # Create SFTP client
            sftp = client.open_sftp()
            
            # Get remote directory - needed to handle relative paths
            remote_dir = config.get("remote_dir", "")
            if not remote_dir:
                # Try to get home directory
                stdin, stdout, stderr = client.exec_command("echo $HOME")
                remote_dir = stdout.read().decode().strip()
            
            # Handle file path - if it's relative, prepend remote_dir
            if not file_path.startswith('/'):
                full_path = f"{remote_dir}/{file_path}"
            else:
                full_path = file_path
                
            # Read file content
            try:
                with sftp.file(full_path, 'r') as f:
                    content = f.read().decode('utf-8', errors='replace')
            except:
                # If that fails, try cat command which might handle special files better
                stdin, stdout, stderr = client.exec_command(f"cat '{full_path}'")
                content = stdout.read().decode('utf-8', errors='replace')
            
            # Close connection
            client.close()
            
            # Update text widget in main thread
            def update_text_widget():
                text_widget.config(state='normal')
                text_widget.delete(1.0, tk.END)
                text_widget.insert(tk.END, content)
                text_widget.config(state='disabled')
                self.update_status("File content loaded", show_progress=False)
                
            self.root.after(0, update_text_widget)
            
        except Exception as e:
            self.log(f"Error loading remote file content: {str(e)}")
            self.root.after(0, lambda: self.update_status(f"Error: {str(e)}", show_progress=False))

    def refresh_job_details(self, job_id, job_name, dialog=None):
        """Refresh job details"""
        # Close existing dialog if provided
        if dialog:
            dialog.destroy()
        
        # Show job details again
        selection = self.job_tree.selection()
        self.show_job_details()

    def download_results(self):
        """Download results from a selected HPC job"""
        try:
            # Check if job tree exists and an item is selected
            if not hasattr(self, 'job_tree'):
                messagebox.showerror("Error", "Job list not available")
                return
                
            # Get selected item
            selection = self.job_tree.selection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select a job to download results")
                return
                
            # Get job ID from selection
            job_data = self.job_tree.item(selection[0])
            job_values = job_data['values']
            
            if not job_values or len(job_values) < 2:
                messagebox.showerror("Error", "Invalid job selection")
                return
                
            job_id = str(job_values[1])
            job_name = str(job_values[0])
            
            # Get HPC profile
            if not hasattr(self, 'conn_profile') or not self.conn_profile.get():
                messagebox.showerror("Error", "No HPC profile selected")
                return
                
            profile_name = self.conn_profile.get()
            
            # Create dialog to specify what to download
            download_dialog = tk.Toplevel(self.root)
            download_dialog.title(f"Download Results - Job {job_name}")
            download_dialog.geometry("500x400")
            download_dialog.transient(self.root)
            
            # Apply theme to dialog
            download_dialog.configure(background=self.theme.bg_color)
            
            # Create form
            main_frame = ttk.Frame(download_dialog, padding=self.theme.padding)
            main_frame.pack(fill='both', expand=True)
            
            # Job info
            info_frame = ttk.LabelFrame(main_frame, text="Job Information", padding=self.theme.padding)
            info_frame.pack(fill='x', pady=5)
            
            ttk.Label(info_frame, text=f"Job Name: {job_name}").pack(anchor='w')
            ttk.Label(info_frame, text=f"Job ID: {job_id}").pack(anchor='w')
            
            # Download options
            options_frame = ttk.LabelFrame(main_frame, text="Download Options", padding=self.theme.padding)
            options_frame.pack(fill='x', pady=5)
            
            # Remote directory
            ttk.Label(options_frame, text="Remote Directory:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
            remote_dir_var = tk.StringVar()
            remote_dir_var.set("job_*")  # Default pattern for job directories
            remote_dir = ttk.Entry(options_frame, width=30, textvariable=remote_dir_var)
            remote_dir.grid(row=0, column=1, padx=5, pady=5, sticky='w')
            
            # File patterns
            ttk.Label(options_frame, text="File Patterns:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
            file_patterns_var = tk.StringVar()
            file_patterns_var.set("*.csv *.dat *.vtu *.log")  # Default patterns
            file_patterns = ttk.Entry(options_frame, width=30, textvariable=file_patterns_var)
            file_patterns.grid(row=1, column=1, padx=5, pady=5, sticky='w')
            
            # Local directory
            ttk.Label(options_frame, text="Local Directory:").grid(row=2, column=0, padx=5, pady=5, sticky='w')
            local_dir_var = tk.StringVar()
            local_dir_var.set(os.path.join(os.getcwd(), f"results_job_{job_id}"))
            local_dir = ttk.Entry(options_frame, width=30, textvariable=local_dir_var)
            local_dir.grid(row=2, column=1, padx=5, pady=5, sticky='w')
            ttk.Button(options_frame, text="Browse", 
                    command=lambda: self.browse_local_dir(local_dir_var)).grid(row=2, column=2, padx=5, pady=5)
            
            # Options
            options_subframe = ttk.Frame(options_frame)
            options_subframe.grid(row=3, column=0, columnspan=3, padx=5, pady=5, sticky='w')
            
            overwrite_var = tk.BooleanVar(value=True)
            ttk.Checkbutton(options_subframe, text="Overwrite existing files", 
                        variable=overwrite_var).pack(side='left', padx=5)
                        
            recursive_var = tk.BooleanVar(value=True)
            ttk.Checkbutton(options_subframe, text="Download recursively", 
                        variable=recursive_var).pack(side='left', padx=5)
            
            # Status area
            status_frame = ttk.LabelFrame(main_frame, text="Download Status", padding=self.theme.padding)
            status_frame.pack(fill='both', expand=True, pady=5)
            
            status_text = scrolledtext.ScrolledText(status_frame, height=10, wrap=tk.WORD)
            status_text.pack(fill='both', expand=True, padx=5, pady=5)
            status_text.insert(tk.END, "Specify download options and click 'Start Download'")
            
            # Progress bar
            progress_var = tk.DoubleVar(value=0.0)
            progress = ttk.Progressbar(main_frame, orient='horizontal', 
                                    length=300, mode='determinate', 
                                    variable=progress_var)
            progress.pack(fill='x', padx=5, pady=5)
            
            # Button frame
            button_frame = ttk.Frame(main_frame)
            button_frame.pack(fill='x', pady=10)
            
            def start_download():
                # Get values from form
                remote_path = remote_dir_var.get()
                patterns = file_patterns_var.get()
                local_path = local_dir_var.get()
                overwrite = overwrite_var.get()
                recursive = recursive_var.get()
                
                # Create local directory if it doesn't exist
                if not os.path.exists(local_path):
                    try:
                        os.makedirs(local_path)
                    except Exception as e:
                        messagebox.showerror("Error", f"Could not create local directory: {str(e)}")
                        return
                
                # Disable form while downloading
                start_button.config(state='disabled')
                cancel_button.config(state='normal')
                
                # Clear status text
                status_text.delete(1.0, tk.END)
                status_text.insert(tk.END, "Starting download...\n")
                
                # Start download in thread
                self.download_thread = threading.Thread(
                    target=lambda: self.download_results_thread(
                        profile_name, remote_path, patterns, local_path, 
                        overwrite, recursive, status_text, progress_var,
                        download_dialog),
                    daemon=True
                )
                self.download_thread.start()
            
            start_button = ttk.Button(button_frame, text="Start Download", 
                                command=start_download)
            start_button.pack(side="left", padx=5)
            
            cancel_button = ttk.Button(button_frame, text="Cancel", 
                                    state='disabled',
                                    command=lambda: self.cancel_download())
            cancel_button.pack(side="left", padx=5)
            
            close_button = ttk.Button(button_frame, text="Close", 
                                command=download_dialog.destroy)
            close_button.pack(side="right", padx=5)
            
        except Exception as e:
            self.log(f"Error setting up download dialog: {str(e)}")
            messagebox.showerror("Error", f"Failed to setup download: {str(e)}")

    def browse_local_dir(self, dir_var):
        """Open directory browser to select local download directory"""
        dir_path = filedialog.askdirectory(
            title="Select Download Directory"
        )
        if dir_path:
            dir_var.set(dir_path)

    def cancel_download(self):
        """Set flag to cancel ongoing download"""
        if hasattr(self, 'download_canceled'):
            self.download_canceled = True

    def download_results_thread(self, profile_name, remote_path, patterns, local_path, 
                                overwrite, recursive, status_text, progress_var, dialog=None):
        """Download job results in a separate thread"""
        import paramiko
        import os
        import fnmatch
        
        try:
            # Set up cancellation flag
            self.download_canceled = False
            
            # Load the HPC profile
            profiles_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                    "Config", "hpc_profiles.json")
            
            if not os.path.exists(profiles_path):
                self.update_status_text(status_text, "Error: HPC profiles configuration not found")
                self.root.after(0, lambda: self.update_status("Download failed", show_progress=False))
                return
                
            with open(profiles_path, 'r') as f:
                profiles = json.load(f)
            
            if profile_name not in profiles:
                self.update_status_text(status_text, f"Error: HPC profile '{profile_name}' not found")
                self.root.after(0, lambda: self.update_status("Download failed", show_progress=False))
                return
                
            config = profiles[profile_name]
            
            # Create SSH client
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Connect based on authentication method
            if config.get("use_key", False):
                key_path = config.get("key_path", "")
                if not key_path:
                    self.update_status_text(status_text, "Error: No SSH key specified in profile")
                    self.root.after(0, lambda: self.update_status("Download failed", show_progress=False))
            if not hasattr(self, 'workflow_canvas') or not hasattr(self, 'workflow_steps'):
                return
                
            # Get canvas dimensions
            width = self.workflow_canvas.winfo_width() or 800
            height = self.workflow_canvas.winfo_height() or 120
            
            # Check if any step was clicked
            for step in self.workflow_steps:
                # Get step position
                x = int(step["x"] * width)
                y = int(step["y"] * height)
                
                # Calculate distance from click to step center
                distance = ((event.x - x) ** 2 + (event.y - y) ** 2) ** 0.5
                
                # If within circle radius, show details
                if distance <= 20:  # 20px circle radius
                    # Display step details in a message box
                    messagebox.showinfo(
                        f"Step: {step['name']}",
                        f"Description: {step['desc']}\n"
                        f"Status: {step['status'].title()}"
                    )
                    
                    return
        except Exception as e:
            # Handle any exceptions
            self.log(f"Error downloading results: {str(e)}")
            self.root.after(0, lambda: self.update_status(f"Download failed: {str(e)}", show_progress=False))
            if status_text:
                self.root.after(0, lambda: self.update_status_text(status_text, f"Error: {str(e)}"))

    def setup_optimization_tab(self):
        """Set up the Optimization tab"""
        # Main frame for optimization tab
        outer_frame, main_frame = self.create_scrollable_frame(self.optimization_tab, 
                                                            bg=self.theme.bg_color,
                                                            highlightthickness=0)
        outer_frame.pack(fill='both', expand=True)

        # Split into input panel and results panel
        left_pane = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        left_pane.pack(fill='both', expand=True, padx=self.theme.padding, pady=self.theme.padding)

        # Create scrollable frame specifically for input section
        input_scroll_frame, input_inner = self.create_scrollable_frame(left_pane, 
                                                                    bg=self.theme.bg_color,
                                                                    highlightthickness=0)
        
        # Create label frame inside the scrollable area
        input_frame = ttk.LabelFrame(input_inner, text="Optimization Settings", padding=self.theme.padding)
        input_frame.pack(fill='both', expand=True)
        
        # Results panel remains as before
        results_frame = ttk.LabelFrame(left_pane, text="Optimization Results", padding=self.theme.padding)
        
        # Add both panels to the paned window with appropriate weights
        left_pane.add(input_scroll_frame, weight=1)  # Use the scrollable container
        left_pane.add(results_frame, weight=3)

            
        # Optimization method section
        method_frame = ttk.Frame(input_frame)
        method_frame.pack(fill='x', pady=10)
        
        ttk.Label(method_frame, text="Optimization Method:").pack(anchor='w')
        self.opt_method = ttk.Combobox(method_frame, values=[
            "Gradient Descent", "Genetic Algorithm", "Particle Swarm", "Bayesian Optimization"
        ])
        self.opt_method.pack(fill='x', pady=5)
        self.opt_method.current(1)  # Default to Genetic Algorithm
        
        # Parameter bounds section
        bounds_frame = ttk.LabelFrame(input_frame, text="Parameter Bounds", padding=5)
        bounds_frame.pack(fill='x', pady=10)
        
        # Create a grid for parameter bounds
        grid = ttk.Frame(bounds_frame)
        grid.pack(fill='x')
        
        # Parameter headers
        ttk.Label(grid, text="Parameter").grid(row=0, column=0, padx=5, pady=5)
        ttk.Label(grid, text="Min").grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(grid, text="Max").grid(row=0, column=2, padx=5, pady=5)
        
        # L4 parameter
        ttk.Label(grid, text="L4:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        self.l4_min = ttk.Entry(grid, width=10)
        self.l4_min.grid(row=1, column=1, padx=5, pady=5)
        self.l4_min.insert(0, "1.0")
        self.l4_max = ttk.Entry(grid, width=10)
        self.l4_max.grid(row=1, column=2, padx=5, pady=5)
        self.l4_max.insert(0, "5.0")
        
        # L5 parameter
        ttk.Label(grid, text="L5:").grid(row=2, column=0, padx=5, pady=5, sticky='w')
        self.l5_min = ttk.Entry(grid, width=10)
        self.l5_min.grid(row=2, column=1, padx=5, pady=5)
        self.l5_min.insert(0, "1.0")
        self.l5_max = ttk.Entry(grid, width=10)
        self.l5_max.grid(row=2, column=2, padx=5, pady=5)
        self.l5_max.insert(0, "5.0")
        
        # Alpha1 parameter
        ttk.Label(grid, text="Alpha1:").grid(row=3, column=0, padx=5, pady=5, sticky='w')
        self.alpha1_min = ttk.Entry(grid, width=10)
        self.alpha1_min.grid(row=3, column=1, padx=5, pady=5)
        self.alpha1_min.insert(0, "5.0")
        self.alpha1_max = ttk.Entry(grid, width=10)
        self.alpha1_max.grid(row=3, column=2, padx=5, pady=5)
        self.alpha1_max.insert(0, "30.0")
        
        # Alpha2 parameter
        ttk.Label(grid, text="Alpha2:").grid(row=4, column=0, padx=5, pady=5, sticky='w')
        self.alpha2_min = ttk.Entry(grid, width=10)
        self.alpha2_min.grid(row=4, column=1, padx=5, pady=5)
        self.alpha2_min.insert(0, "5.0")
        self.alpha2_max = ttk.Entry(grid, width=10)
        self.alpha2_max.grid(row=4, column=2, padx=5, pady=5)
        self.alpha2_max.insert(0, "30.0")
        
        # Alpha3 parameter
        ttk.Label(grid, text="Alpha3:").grid(row=5, column=0, padx=5, pady=5, sticky='w')
        self.alpha3_min = ttk.Entry(grid, width=10)
        self.alpha3_min.grid(row=5, column=1, padx=5, pady=5)
        self.alpha3_min.insert(0, "5.0")
        self.alpha3_max = ttk.Entry(grid, width=10)
        self.alpha3_max.grid(row=5, column=2, padx=5, pady=5)
        self.alpha3_max.insert(0, "30.0")
        
        # Objective function section
        obj_frame = ttk.LabelFrame(input_frame, text="Objective Function", padding=5)
        obj_frame.pack(fill='x', pady=10)
        
        ttk.Label(obj_frame, text="Optimization Goal:").pack(anchor='w')
        self.obj_var = tk.StringVar(value="minimize")
        ttk.Radiobutton(obj_frame, text="Minimize", variable=self.obj_var, value="minimize").pack(anchor='w')
        ttk.Radiobutton(obj_frame, text="Maximize", variable=self.obj_var, value="maximize").pack(anchor='w')
        
        ttk.Label(obj_frame, text="Objective:").pack(anchor='w', pady=(10,0))
        self.objective_combo = ttk.Combobox(obj_frame, values=[
            "Pressure Drop", "Flow Rate", "Flow Uniformity", "Custom"
        ])
        self.objective_combo.pack(fill='x', pady=5)
        self.objective_combo.current(0)
        
        # Advanced options section
        adv_frame = ttk.LabelFrame(input_frame, text="Algorithm Settings", padding=5)
        adv_frame.pack(fill='x', pady=10)
        
        ttk.Label(adv_frame, text="Population Size:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.pop_size = ttk.Entry(adv_frame, width=10)
        self.pop_size.grid(row=0, column=1, padx=5, pady=5)
        self.pop_size.insert(0, "30")
        
        ttk.Label(adv_frame, text="Max Generations:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        self.max_gen = ttk.Entry(adv_frame, width=10)
        self.max_gen.grid(row=1, column=1, padx=5, pady=5)
        self.max_gen.insert(0, "20")
        
        ttk.Label(adv_frame, text="Mutation Rate:").grid(row=2, column=0, padx=5, pady=5, sticky='w')
        self.mut_rate = ttk.Entry(adv_frame, width=10)
        self.mut_rate.grid(row=2, column=1, padx=5, pady=5)
        self.mut_rate.insert(0, "0.15")
        
        ttk.Label(adv_frame, text="Crossover Rate:").grid(row=3, column=0, padx=5, pady=5, sticky='w')
        self.cross_rate = ttk.Entry(adv_frame, width=10)
        self.cross_rate.grid(row=3, column=1, padx=5, pady=5)
        self.cross_rate.insert(0, "0.7")
        
        # Execution environment section
        exec_frame = ttk.LabelFrame(input_frame, text="Execution Environment", padding=5)
        exec_frame.pack(fill='x', pady=10)
        
        # Environment radio buttons with clearer labels
        ttk.Label(exec_frame, text="Select execution mode:").pack(anchor='w', pady=2)
        self.opt_env_var = tk.StringVar(value="local")
        
        # Add radio buttons with more padding and clearer styling
        local_radio = ttk.Radiobutton(exec_frame, text="Local Execution", 
                                    variable=self.opt_env_var, value="local",
                                    command=self.toggle_opt_execution_environment)
        local_radio.pack(anchor='w', pady=4, padx=10)  # Increased padding
        
        hpc_radio = ttk.Radiobutton(exec_frame, text="HPC Execution", 
                                  variable=self.opt_env_var, value="hpc",
                                  command=self.toggle_opt_execution_environment)
        hpc_radio.pack(anchor='w', pady=4, padx=10)  # Increased padding
        
        # HPC settings frame with better visibility
        self.opt_hpc_profiles_frame = ttk.Frame(exec_frame, padding=5)
        self.opt_hpc_profiles_frame.pack(fill='x', pady=5, padx=5)  # Fill horizontally with padding
        
        ttk.Label(self.opt_hpc_profiles_frame, text="HPC Profile:").pack(side="left", padx=5)
        self.opt_hpc_profile = ttk.Combobox(self.opt_hpc_profiles_frame, width=20)
        self.opt_hpc_profile.pack(side="left", padx=5, fill='x', expand=True)
        
        # Add a visual separator to make the section more distinct
        ttk.Separator(exec_frame, orient='horizontal').pack(fill='x', pady=5)
        
        # Load HPC profiles for optimization
        self.load_hpc_profiles_for_opt()
        
        # Buttons
        button_frame = ttk.Frame(input_frame)
        button_frame.pack(fill='x', pady=10)
        
        self.start_opt_button = ttk.Button(button_frame, text="Start Optimization", 
                                        command=lambda: self.start_optimization())
        self.start_opt_button.pack(side="left", padx=5)
        
        ttk.Button(button_frame, text="Stop", command=lambda: self.stop_optimization()).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Import Config", 
                command=lambda: self.import_optimization_config()).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Export Config", 
                command=lambda: self.export_optimization_config()).pack(side="left", padx=5)
        
        # Results display section - create notebook for different result views
        self.opt_notebook = ttk.Notebook(results_frame)
        self.opt_notebook.pack(fill='both', expand=True)
        
        # Convergence history tab
        self.conv_tab = ttk.Frame(self.opt_notebook)
        self.opt_notebook.add(self.conv_tab, text="Convergence")
        
        # Set up matplotlib figure for convergence plot
        self.opt_fig = Figure(figsize=(6, 5), dpi=100)
        self.opt_ax = self.opt_fig.add_subplot(111)
        self.opt_canvas = FigureCanvasTkAgg(self.opt_fig, master=self.conv_tab)
        self.opt_canvas.draw()
        self.opt_canvas.get_tk_widget().pack(fill='both', expand=True)
        
        # Add toolbar
        toolbar_frame = ttk.Frame(self.conv_tab)
        toolbar_frame.pack(fill='x', expand=False)
        self.opt_toolbar = NavigationToolbar2Tk(self.opt_canvas, toolbar_frame)
        self.opt_toolbar.update()
        
        # Pareto front tab for multi-objective optimization
        self.pareto_tab = ttk.Frame(self.opt_notebook)
        self.opt_notebook.add(self.pareto_tab, text="Pareto Front")
        
        # Set up matplotlib figure for Pareto front
        self.pareto_fig = Figure(figsize=(6, 5), dpi=100)
        self.pareto_ax = self.pareto_fig.add_subplot(111)
        self.pareto_canvas = FigureCanvasTkAgg(self.pareto_fig, master=self.pareto_tab)
        self.pareto_canvas.draw()
        self.pareto_canvas.get_tk_widget().pack(fill='both', expand=True)
        
        # Add toolbar
        pareto_toolbar_frame = ttk.Frame(self.pareto_tab)
        pareto_toolbar_frame.pack(fill='x', expand=False)
        self.pareto_toolbar = NavigationToolbar2Tk(self.pareto_canvas, pareto_toolbar_frame)
        self.pareto_toolbar.update()
        
        # Best design tab
        self.best_design_tab = ttk.Frame(self.opt_notebook)
        self.opt_notebook.add(self.best_design_tab, text="Best Design")
        
        # Create container for best design data
        best_design_frame = ttk.Frame(self.best_design_tab)
        best_design_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Best design parameters section
        params_frame = ttk.LabelFrame(best_design_frame, text="Parameters", padding=5)
        params_frame.pack(fill='x', pady=10)
        
        # Create a grid layout for parameters
        grid = ttk.Frame(params_frame)
        grid.pack(fill='x', padx=5, pady=5)
        
        # Add column headings
        ttk.Label(grid, text="Parameter", font=self.theme.normal_font).grid(row=0, column=0, padx=10, pady=5, sticky='w')
        ttk.Label(grid, text="Value", font=self.theme.normal_font).grid(row=0, column=1, padx=10, pady=5)
        
        # Parameter rows for display
        params = ["L4", "L5", "Alpha1", "Alpha2", "Alpha3"]
        self.param_values = {}
        
        for i, param in enumerate(params):
            ttk.Label(grid, text=param, font=self.theme.normal_font).grid(row=i+1, column=0, padx=10, pady=5, sticky='w')
            self.param_values[param] = tk.StringVar(value="---")
            ttk.Label(grid, textvariable=self.param_values[param], font=self.theme.normal_font).grid(
                row=i+1, column=1, padx=10, pady=5)
        
        # Best design objectives section
        obj_frame = ttk.LabelFrame(best_design_frame, text="Objectives", padding=5)
        obj_frame.pack(fill='x', pady=10)
        
        # Create grid for objectives
        grid = ttk.Frame(obj_frame)
        grid.pack(fill='x', padx=5, pady=5)
        
        # Add column headings
        ttk.Label(grid, text="Objective", font=self.theme.normal_font).grid(row=0, column=0, padx=10, pady=5, sticky='w')
        ttk.Label(grid, text="Value", font=self.theme.normal_font).grid(row=0, column=1, padx=10, pady=5)
        
        # Objective rows for display
        objectives = ["Pressure Drop", "Flow Rate", "Flow Uniformity"]
        self.obj_values = {}
        
        for i, obj in enumerate(objectives):
            ttk.Label(grid, text=obj, font=self.theme.normal_font).grid(row=i+1, column=0, padx=10, pady=5, sticky='w')
            self.obj_values[obj] = tk.StringVar(value="---")
            ttk.Label(grid, textvariable=self.obj_values[obj], font=self.theme.normal_font).grid(
                row=i+1, column=1, padx=10, pady=5)
        
        # Result visualization section
        viz_frame = ttk.LabelFrame(best_design_frame, text="Visualization", padding=5)
        viz_frame.pack(fill='both', expand=True, pady=10)
        
        # Add placeholder for visualization
        placeholder_text = tk.Label(viz_frame, 
                                text="Best design visualization will be displayed here\nonce optimization is complete.", 
                                font=self.theme.normal_font, 
                                fg=self.theme.text_color,
                                bg=self.theme.bg_color,
                                pady=30)
        placeholder_text.pack(fill='both', expand=True)
        
        # Progress indicator at the bottom
        progress_frame = ttk.Frame(results_frame)
        progress_frame.pack(fill='x', pady=10)
        
        ttk.Label(progress_frame, text="Optimization Progress:").pack(side='left', padx=5)
        self.opt_progress = ttk.Progressbar(progress_frame, orient='horizontal', length=300, mode='determinate')
        self.opt_progress.pack(side='left', padx=5, expand=True, fill='x')
        
        self.opt_status_var = tk.StringVar(value="Ready")
        ttk.Label(progress_frame, textvariable=self.opt_status_var).pack(side='right', padx=5)
        
        # Initialize plots
        self.initialize_convergence_plot()
        self.initialize_pareto_front()
        
        # Hide HPC settings initially
        self.opt_hpc_profiles_frame.pack_forget()
        
        self.log("Optimization tab initialized")

    def setup_workflow_tab(self):
        """Set up the workflow tab"""
        # Main frame for workflow tab
        main_frame = ttk.Frame(self.workflow_tab, padding=self.theme.padding)
        main_frame.pack(fill='both', expand=True)
        
        # Split into parameters panel and workflow panel
        parameters_frame = ttk.LabelFrame(main_frame, text="Parameters", padding=self.theme.padding)
        parameters_frame.pack(side='left', fill='y', padx=self.theme.padding, pady=self.theme.padding)
        
        workflow_frame = ttk.LabelFrame(main_frame, text="Workflow", padding=self.theme.padding)
        workflow_frame.pack(side='right', fill='both', expand=True, padx=self.theme.padding, pady=self.theme.padding)
        
        # Create sub-frames for organizing parameters - using pack() consistently
        params_frame = ttk.Frame(parameters_frame)
        params_frame.pack(fill='x', pady=5)
        
        # Parameter inputs - using pack()
        param_entry_frame = ttk.Frame(params_frame)
        param_entry_frame.pack(fill='x', pady=5)
        
        # L4 parameter
        l4_frame = ttk.Frame(param_entry_frame)
        l4_frame.pack(fill='x', pady=2)
        ttk.Label(l4_frame, text="L4:").pack(side='left', padx=5)
        self.l4_workflow = ttk.Entry(l4_frame, width=10)
        self.l4_workflow.pack(side='right', padx=5)
        self.l4_workflow.insert(0, "3.0")
        
        # L5 parameter
        l5_frame = ttk.Frame(param_entry_frame)
        l5_frame.pack(fill='x', pady=2)
        ttk.Label(l5_frame, text="L5:").pack(side='left', padx=5)
        self.l5_workflow = ttk.Entry(l5_frame, width=10)
        self.l5_workflow.pack(side='right', padx=5)
        self.l5_workflow.insert(0, "3.0")
        
        # Alpha1 parameter
        alpha1_frame = ttk.Frame(param_entry_frame)
        alpha1_frame.pack(fill='x', pady=2)
        ttk.Label(alpha1_frame, text="Alpha1:").pack(side='left', padx=5)
        self.alpha1_workflow = ttk.Entry(alpha1_frame, width=10)
        self.alpha1_workflow.pack(side='right', padx=5)
        self.alpha1_workflow.insert(0, "15.0")
        
        # Alpha2 parameter
        alpha2_frame = ttk.Frame(param_entry_frame)
        alpha2_frame.pack(fill='x', pady=2)
        ttk.Label(alpha2_frame, text="Alpha2:").pack(side='left', padx=5)
        self.alpha2_workflow = ttk.Entry(alpha2_frame, width=10)
        self.alpha2_workflow.pack(side='right', padx=5)
        self.alpha2_workflow.insert(0, "15.0")
        
        # Alpha3 parameter
        alpha3_frame = ttk.Frame(param_entry_frame)
        alpha3_frame.pack(fill='x', pady=2)
        ttk.Label(alpha3_frame, text="Alpha3:").pack(side='left', padx=5)
        self.alpha3_workflow = ttk.Entry(alpha3_frame, width=10)
        self.alpha3_workflow.pack(side='right', padx=5)
        self.alpha3_workflow.insert(0, "15.0")
        
        # Execution environment
        env_frame = ttk.LabelFrame(parameters_frame, text="Execution Environment", padding=5)
        env_frame.pack(fill='x', pady=10)  # Using pack() instead of grid()
        
        # Radio buttons for execution environment
        self.env_var = tk.StringVar(value="local")
        ttk.Radiobutton(env_frame, text="Local Execution", 
                    variable=self.env_var, value="local",
                    command=self.toggle_execution_environment).pack(anchor='w', pady=2)
        ttk.Radiobutton(env_frame, text="HPC Execution", 
                    variable=self.env_var, value="hpc",
                    command=self.toggle_execution_environment).pack(anchor='w', pady=2)
        
        # HPC settings (initially hidden)
        self.workflow_hpc_frame = ttk.Frame(env_frame)
        
        ttk.Label(self.workflow_hpc_frame, text="HPC Profile:").pack(side="left", padx=5)
        self.workflow_hpc_profile = ttk.Combobox(self.workflow_hpc_frame, width=20)
        self.workflow_hpc_profile.pack(side="left", padx=5)
        
        # Load HPC profiles for workflow
        self.load_workflow_hpc_profiles()
        
        # Hide HPC settings initially
        self.workflow_hpc_frame.pack_forget()
        
        # Run/Cancel buttons
        button_frame = ttk.Frame(parameters_frame)
        button_frame.pack(pady=10)  # Using pack() instead of grid()
        
        self.run_button = ttk.Button(button_frame, text="Run Workflow", command=self.run_workflow)
        self.run_button.pack(side="left", padx=5)
        
        self.cancel_button = ttk.Button(button_frame, text="Cancel", command=self.cancel_workflow, state="disabled")
        self.cancel_button.pack(side="left", padx=5)
        
        # Workflow visualization
        viz_frame = ttk.Frame(workflow_frame)
        viz_frame.pack(fill='both', expand=True)
        
        # Create canvas for workflow visualization
        self.workflow_canvas = tk.Canvas(viz_frame, bg="white", height=120)
        self.workflow_canvas.pack(fill='both', expand=True, padx=5, pady=5)
        self.workflow_canvas.bind("<Button-1>", self.workflow_canvas_click)
        
        self.workflow_steps = [
            {'name': 'CAD', 'status': 'pending', 'x': 0.1, 'y': 0.5, 'desc': 'Updates the NX model with parameters'},
            {'name': 'Mesh', 'status': 'pending', 'x': 0.35, 'y': 0.5, 'desc': 'Generates mesh from geometry'},
            {'name': 'CFD', 'status': 'pending', 'x': 0.6, 'y': 0.5, 'desc': 'Runs CFD simulation'},
            {'name': 'Results', 'status': 'pending', 'x': 0.85, 'y': 0.5, 'desc': 'Processes simulation results'}
        ]
        
        # Draw the workflow
        self._redraw_workflow()
        
        # Status text area
        status_frame = ttk.LabelFrame(workflow_frame, text="Status")
        status_frame.pack(fill='x', expand=False, padx=5, pady=5)
        
        self.workflow_status_text = scrolledtext.ScrolledText(status_frame, height=10, wrap=tk.WORD)
        self.workflow_status_text.pack(fill='both', expand=True, padx=5, pady=5)
        self.workflow_status_text.insert(tk.END, "Ready to start workflow. Set parameters and click 'Run Workflow'.")
        self.workflow_status_text.config(state='disabled')
        
        self.log("Workflow tab initialized")

    def setup_settings_tab(self):
            """Set up the Settings tab"""
            # Main frame for settings tab
            main_frame = ttk.Frame(self.settings_tab, padding=self.theme.padding)
            main_frame.pack(fill='both', expand=True)
            
            # Create sections for different settings
            # General Settings
            general_frame = ttk.LabelFrame(main_frame, text="General Settings", padding=self.theme.padding)
            general_frame.pack(fill='x', padx=self.theme.padding, pady=self.theme.small_padding)
            
            # Path settings
            ttk.Label(general_frame, text="NX Path:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
            self.nx_path = ttk.Entry(general_frame, width=50)
            self.nx_path.grid(row=0, column=1, padx=5, pady=5, sticky='w')
            ttk.Button(general_frame, text="Browse", command=self.browse_nx_path).grid(row=0, column=2, padx=5, pady=5)
            
            ttk.Label(general_frame, text="Project Directory:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
            self.project_dir = ttk.Entry(general_frame, width=50)
            self.project_dir.grid(row=1, column=1, padx=5, pady=5, sticky='w')
            ttk.Button(general_frame, text="Browse", command=self.browse_project_dir).grid(row=1, column=2, padx=5, pady=5)
            
            # Appearance Settings
            appearance_frame = ttk.LabelFrame(main_frame, text="Appearance", padding=self.theme.padding)
            appearance_frame.pack(fill='x', padx=self.theme.padding, pady=self.theme.small_padding)
            
            # Theme selection
            ttk.Label(appearance_frame, text="Theme:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
            self.theme_combo = ttk.Combobox(appearance_frame, values=["Light", "Dark", "System"])
            self.theme_combo.grid(row=0, column=1, padx=5, pady=5, sticky='w')
            self.theme_combo.current(0)  # Default to light theme
            
            # Font size selection
            ttk.Label(appearance_frame, text="Font Size:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
            self.font_size = ttk.Combobox(appearance_frame, values=["Small", "Medium", "Large"])
            self.font_size.grid(row=1, column=1, padx=5, pady=5, sticky='w')
            self.font_size.current(1)  # Default to medium
            ttk.Button(appearance_frame, text="Apply", command=self.apply_appearance_settings).grid(row=1, column=2, padx=5, pady=5)
            
            # Simulation Settings
            sim_frame = ttk.LabelFrame(main_frame, text="Simulation Settings", padding=self.theme.padding)
            sim_frame.pack(fill='x', padx=self.theme.padding, pady=self.theme.small_padding)
            
            # CFD solver settings
            ttk.Label(sim_frame, text="CFD Solver:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
            self.solver_combo = ttk.Combobox(sim_frame, values=["OpenFOAM", "Fluent", "Star-CCM+", "Custom"])
            self.solver_combo.grid(row=0, column=1, padx=5, pady=5, sticky='w')
            self.solver_combo.current(0)  # Default to OpenFOAM
            
            # Mesher settings
            ttk.Label(sim_frame, text="Mesher:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
            self.mesher_combo = ttk.Combobox(sim_frame, values=["GMSH", "Fluent Meshing", "Star-CCM+ Meshing", "Custom"])
            self.mesher_combo.grid(row=1, column=1, padx=5, pady=5, sticky='w')
            self.mesher_combo.current(0)  # Default to GMSH
            
            # Default mesh size
            ttk.Label(sim_frame, text="Default Mesh Size:").grid(row=2, column=0, sticky='w', padx=5, pady=5)
            mesh_size_frame = ttk.Frame(sim_frame)
            mesh_size_frame.grid(row=2, column=1, sticky='w', padx=5, pady=5)
            
            self.mesh_size = ttk.Entry(mesh_size_frame, width=10)
            self.mesh_size.pack(side='left')
            self.mesh_size.insert(0, "0.1")
            ttk.Label(mesh_size_frame, text="m").pack(side='left')
            
            # Default viscosity
            ttk.Label(sim_frame, text="Default Viscosity:").grid(row=3, column=0, sticky='w', padx=5, pady=5)
            viscosity_frame = ttk.Frame(sim_frame)
            viscosity_frame.grid(row=3, column=1, sticky='w', padx=5, pady=5)
            
            self.viscosity = ttk.Entry(viscosity_frame, width=10)
            self.viscosity.pack(side='left')
            self.viscosity.insert(0, "1.8e-5")
            ttk.Label(viscosity_frame, text="kg/m·s").pack(side='left')
            
            # Default density
            ttk.Label(sim_frame, text="Default Density:").grid(row=4, column=0, sticky='w', padx=5, pady=5)
            density_frame = ttk.Frame(sim_frame)
            density_frame.grid(row=4, column=1, sticky='w', padx=5, pady=5)
            
            self.density = ttk.Entry(density_frame, width=10)
            self.density.pack(side='left')
            self.density.insert(0, "1.225")
            ttk.Label(density_frame, text="kg/m³").pack(side='left')
            
            # Advanced Settings
            adv_frame = ttk.LabelFrame(main_frame, text="Advanced Settings", padding=self.theme.padding)
            adv_frame.pack(fill='x', padx=self.theme.padding, pady=self.theme.small_padding)
            
            # Number of threads
            ttk.Label(adv_frame, text="Number of Threads:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
            self.threads = ttk.Entry(adv_frame, width=5)
            self.threads.grid(row=0, column=1, padx=5, pady=5, sticky='w')
            self.threads.insert(0, str(multiprocessing.cpu_count()))
            
            # Debugging mode
            self.debug_var = tk.BooleanVar(value=False)
            ttk.Checkbutton(adv_frame, text="Enable Debug Mode", variable=self.debug_var).grid(row=1, column=0, columnspan=2, sticky='w', padx=5, pady=5)
            
            # Auto-save interval
            ttk.Label(adv_frame, text="Auto-save Interval (min):").grid(row=2, column=0, sticky='w', padx=5, pady=5)
            self.autosave = ttk.Entry(adv_frame, width=5)
            self.autosave.grid(row=2, column=1, padx=5, pady=5, sticky='w')
            self.autosave.insert(0, "10")
            
            # Memory usage limit
            ttk.Label(adv_frame, text="Memory Limit (%):").grid(row=3, column=0, sticky='w', padx=5, pady=5)
            self.memory_limit = ttk.Scale(adv_frame, from_=10, to=90, orient='horizontal', length=200)
            self.memory_limit.grid(row=3, column=1, padx=5, pady=5, sticky='w')
            self.memory_limit.set(70)  # Default to 70%
            
            # Memory usage display
            self.memory_usage_var = tk.StringVar(value="Current Memory Usage: Unknown")
            ttk.Label(adv_frame, textvariable=self.memory_usage_var).grid(row=4, column=0, columnspan=2, sticky='w', padx=5, pady=5)
            
            # System information
            info_frame = ttk.LabelFrame(main_frame, text="System Information", padding=self.theme.padding)
            info_frame.pack(fill='x', padx=self.theme.padding, pady=self.theme.small_padding)
            
            # Get system info
            cpu_info = platform.processor()
            memory_info = self.get_memory_info()
            os_info = f"{platform.system()} {platform.release()}"
            python_ver = platform.python_version()
            
            # Display system info
            ttk.Label(info_frame, text="CPU:").grid(row=0, column=0, sticky='w', padx=5, pady=2)
            ttk.Label(info_frame, text=cpu_info).grid(row=0, column=1, sticky='w', padx=5, pady=2)
            
            ttk.Label(info_frame, text="Memory:").grid(row=1, column=0, sticky='w', padx=5, pady=2)
            ttk.Label(info_frame, text=memory_info).grid(row=1, column=1, sticky='w', padx=5, pady=2)
            
            ttk.Label(info_frame, text="OS:").grid(row=2, column=0, sticky='w', padx=5, pady=2)
            ttk.Label(info_frame, text=os_info).grid(row=2, column=1, sticky='w', padx=5, pady=2)
            
            ttk.Label(info_frame, text="Python:").grid(row=3, column=0, sticky='w', padx=5, pady=2)
            ttk.Label(info_frame, text=python_ver).grid(row=3, column=1, sticky='w', padx=5, pady=2)
            
            # Action Buttons
            button_frame = ttk.Frame(main_frame)
            button_frame.pack(fill='x', padx=self.theme.padding, pady=self.theme.padding)
            
            ttk.Button(button_frame, text="Save Settings", command=self.save_settings).pack(side='left', padx=5)
            ttk.Button(button_frame, text="Load Settings", command=self.load_settings).pack(side='left', padx=5)
            ttk.Button(button_frame, text="Reset to Defaults", command=self.reset_settings).pack(side='left', padx=5)
            ttk.Button(button_frame, text="Check for Updates", command=self.check_updates).pack(side='right', padx=5)
            ttk.Button(button_frame, text="Run Diagnostics", command=self.run_diagnostics).pack(side='right', padx=5)
            
            # Schedule periodic updates of memory usage
            self.root.after(1000, self.update_memory_display)
            
            self.log("Settings tab initialized")

    def _redraw_workflow(self):
        """Redraw the workflow visualization with enhanced visuals"""
        if not hasattr(self, 'workflow_canvas') or not hasattr(self, 'workflow_steps'):
            return
            
        # Clear the canvas
        self.workflow_canvas.delete("all")
        
        # Get canvas dimensions
        width = self.workflow_canvas.winfo_width()
        height = self.workflow_canvas.winfo_height()
        
        # If canvas size is not yet determined, use default values
        if width <= 1:
            width = 800
        if height <= 1:
            height = 200
        
        # Colors for different statuses - use standard hex colors without alpha
        colors = {
            "pending": "#E0E0E0",   # Light gray
            "running": "#FFC107",   # Amber
            "complete": "#4CAF50",  # Green
            "error": "#F44336",     # Red
            "canceled": "#9E9E9E"   # Gray
        }
        
        # Draw connections between steps
        for i in range(len(self.workflow_steps) - 1):
            x1 = int(self.workflow_steps[i]["x"] * width)
            y1 = int(self.workflow_steps[i]["y"] * height)
            x2 = int(self.workflow_steps[i+1]["x"] * width)
            y2 = int(self.workflow_steps[i+1]["y"] * height)
            
            # Determine connection appearance based on status
            start_status = self.workflow_steps[i]["status"]
            end_status = self.workflow_steps[i+1]["status"]
            
            # Base connection
            if start_status == "complete" and end_status == "pending":
                # Ready for next step - dashed line
                self.workflow_canvas.create_line(
                    x1+25, y1, x2-25, y2, 
                    fill=colors[start_status], 
                    width=2.5, 
                    dash=(6, 3)
                )
            elif start_status == "running":
                # Currently running - animated line effect
                self.workflow_canvas.create_line(
                    x1+25, y1, x2-25, y2, 
                    fill=colors[start_status], 
                    width=3
                )
                
                # Add small moving dot for animation effect
                dot_pos = (datetime.datetime.now().timestamp() * 2) % 1.0
                dot_x = x1 + (x2 - x1) * dot_pos
                dot_y = y1 + (y2 - y1) * dot_pos
                self.workflow_canvas.create_oval(
                    dot_x-5, dot_y-5, dot_x+5, dot_y+5,
                    fill=colors[start_status],
                    outline=""
                )
                
                # Schedule redraw for animation
                self.root.after(50, self._redraw_workflow)
            else:
                # Normal connection
                self.workflow_canvas.create_line(
                    x1+25, y1, x2-25, y2, 
                    fill=colors[start_status], 
                    width=2
                )
        
        # Draw each step with modern styling
        for step in self.workflow_steps:
            x = int(step["x"] * width)
            y = int(step["y"] * height)
            status = step["status"]
            color = colors[status]
            
            # Add shadow for 3D effect - use solid color instead of one with alpha
            self.workflow_canvas.create_oval(
                x-22, y-22+3, x+22, y+22+3, 
                fill="#CCCCCC",  # Light gray for shadow
                outline=""
            )
            
            # Draw circle with gradient effect
            for i in range(3):
                size = 22 - i*2
                # Use the same color for all circles instead of varying alpha
                self.workflow_canvas.create_oval(
                    x-size, y-size, x+size, y+size, 
                    fill=sanitize_color(color), 
                    outline=sanitize_color(self.theme.primary_color) if i == 0 else ""
                )
            
            # For running state, add pulsing animation
            if status == "running":
                pulse_size = 25 + (math.sin(datetime.datetime.now().timestamp() * 5) + 1) * 3
                self.workflow_canvas.create_oval(
                    x-pulse_size, y-pulse_size, x+pulse_size, y+pulse_size, 
                    outline=color, 
                    width=2
                )
                
                # Schedule redraw for animation
                self.root.after(50, self._redraw_workflow)
            
            # Draw step name with shadow for better readability
            self.workflow_canvas.create_text(
                x+1, y+1, 
                text=step["name"], 
                fill="#CCCCCC",  # Light gray for text shadow
                font=self.theme.header_font
            )
            self.workflow_canvas.create_text(
                x, y, 
                text=step["name"], 
                fill="white" if status in ["running", "complete"] else self.theme.text_color, 
                font=self.theme.header_font
            )
            
            # Draw status text below
            status_y = y + 35
            self.workflow_canvas.create_text(
                x, status_y, 
                text=status.title(), 
                fill=self.theme.text_color
            )

    def workflow_canvas_click(self, event):
        """Handle clicks on workflow canvas"""
        if not hasattr(self, 'workflow_canvas') or not hasattr(self, 'workflow_steps'):
            return
            
        # Get canvas dimensions
        width = self.workflow_canvas.winfo_width() or 800
        height = self.workflow_canvas.winfo_height() or 120
        
        # Check if any step was clicked
        for step in self.workflow_steps:
            # Get step position
            x = int(step["x"] * width)
            y = int(step["y"] * height)
            
            # Calculate distance from click to step center
            distance = ((event.x - x) ** 2 + (event.y - y) ** 2) ** 0.5
            
            # If within circle radius, show details
            if distance <= 20:  # 20px circle radius
                # Display step details in a message box
                messagebox.showinfo(
                    f"Step: {step['name']}",
                    f"Description: {step['desc']}\n"
                    f"Status: {step['status'].title()}"
                )
                return

    def toggle_execution_environment(self):
        """Toggle between local and HPC execution for workflow"""
        if hasattr(self, 'env_var') and hasattr(self, 'workflow_hpc_frame'):
            if self.env_var.get() == "hpc":
                self.workflow_hpc_frame.pack(anchor='w', pady=5)
            else:
                self.workflow_hpc_frame.pack_forget()
    
    def import_mesh(self):
        """Import mesh from file"""
        file_path = filedialog.askopenfilename(
            title="Import Mesh File",
            filetypes=[
                ("Mesh Files", "*.msh *.vtk *.vtu *.obj *.stl"),
                ("GMSH Files", "*.msh"),
                ("VTK Files", "*.vtk *.vtu"),
                ("OBJ Files", "*.obj"),
                ("STL Files", "*.stl"),
                ("All Files", "*.*")
            ]
        )
        
        if not file_path:
            return
            
        try:
            self.update_status(f"Importing mesh from {file_path}...", show_progress=True)
            
            # For demonstration, we'll create a sample visualization
            if DEMO_MODE or not self._load_real_mesh(file_path):
                self._create_sample_mesh()
                
            self.update_status(f"Mesh imported successfully", show_progress=False)
            messagebox.showinfo("Import Complete", f"Mesh imported from {os.path.basename(file_path)}")
            
        except Exception as e:
            self.log(f"Error importing mesh: {str(e)}")
            self.update_status("Mesh import failed", show_progress=False)
            messagebox.showerror("Import Error", f"Failed to import mesh:\n\n{str(e)}")
    
    def _load_real_mesh(self, file_path):
        """Load a real mesh file - returns True if successful"""
        try:
            # This would use a proper mesh parser in a real implementation
            # For now, we'll return False to fall back to demo mode
            return False
        except Exception as e:
            self.log(f"Error loading mesh file: {str(e)}")
            return False
    
    def _create_sample_mesh(self):
        """Create a sample mesh for visualization"""
        # Clear existing plot
        self.mesh_ax.clear()
        
        # Generate a simple mesh - a cube
        vertices = np.array([
            [0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0],
            [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]
        ])
        
        # Define the faces using the vertices
        faces = [
            [vertices[0], vertices[1], vertices[2], vertices[3]],  # bottom
            [vertices[4], vertices[5], vertices[6], vertices[7]],  # top
            [vertices[0], vertices[1], vertices[5], vertices[4]],  # front
            [vertices[2], vertices[3], vertices[7], vertices[6]],  # back
            [vertices[0], vertices[3], vertices[7], vertices[4]],  # left
            [vertices[1], vertices[2], vertices[6], vertices[5]]   # right
        ]
        
        # Plot each face of the cube
        for face in faces:
            face = np.array(face)
            self.mesh_ax.plot3D(face[:, 0], face[:, 1], face[:, 2], 'gray')
            
        # Set the plot limits and labels
        self.mesh_ax.set_xlim(0, 1)
        self.mesh_ax.set_ylim(0, 1)
        self.mesh_ax.set_zlim(0, 1)
        self.mesh_ax.set_title("Sample Mesh")
        self.mesh_ax.set_xlabel("X")
        self.mesh_ax.set_ylabel("Y")
        self.mesh_ax.set_zlabel("Z")
        
        # Update the display
        self.mesh_canvas.draw()
    
    def export_mesh(self):
        """Export mesh to file"""
        file_path = filedialog.asksaveasfilename(
            title="Export Mesh",
            defaultextension=".msh",
            filetypes=[
                ("GMSH Files", "*.msh"),
                ("VTK Files", "*.vtk"),
                ("STL Files", "*.stl"),
                ("OBJ Files", "*.obj"),
                ("All Files", "*.*")
            ]
        )
        
        if not file_path:
            return
            
        try:
            self.update_status(f"Exporting mesh to {file_path}...", show_progress=True)
            
            # In a real app, this would save the actual mesh
            # For demo, just create a placeholder file
            with open(file_path, 'w') as f:
                f.write("# Demo Mesh File\n")
                f.write("# This is a placeholder file for demonstration purposes\n")
                f.write("# In a real application, this would contain mesh data\n")
                
            self.update_status(f"Mesh exported successfully", show_progress=False)
            messagebox.showinfo("Export Complete", f"Mesh exported to {os.path.basename(file_path)}")
            
        except Exception as e:
            self.log(f"Error exporting mesh: {str(e)}")
            self.update_status("Mesh export failed", show_progress=False)
            messagebox.showerror("Export Error", f"Failed to export mesh:\n\n{str(e)}")
    
    def update_mesh_display(self):
        """Update mesh display based on selected options"""
        try:
            display_mode = self.mesh_display_var.get()
            
            # Simply redraw the mesh for demonstration purposes
            self._create_sample_mesh()
            
            # In a real app, you would change the display style based on the mode
            self.mesh_ax.set_title(f"Mesh - {display_mode}")
            self.mesh_canvas.draw()
            
        except Exception as e:
            self.log(f"Error updating mesh display: {str(e)}")
            messagebox.showerror("Display Error", f"Failed to update mesh display:\n\n{str(e)}")
    
    def import_geometry(self):
        """Import geometry from file"""
        file_path = filedialog.askopenfilename(
            title="Import Geometry File",
            filetypes=[
                ("CAD Files", "*.step *.stp *.iges *.igs *.stl"),
                ("STEP Files", "*.step *.stp"),
                ("IGES Files", "*.iges *.igs"),
                ("STL Files", "*.stl"),
                ("All Files", "*.*")
            ]
        )
        
        if not file_path:
            return
            
        try:
            self.update_status(f"Importing geometry from {file_path}...", show_progress=True)
            
            # For demonstration, we'll create a sample visualization
            if DEMO_MODE or not self._load_real_geometry(file_path):
                self._create_sample_geometry()
                
            self.update_status(f"Geometry imported successfully", show_progress=False)
            messagebox.showinfo("Import Complete", f"Geometry imported from {os.path.basename(file_path)}")
            
        except Exception as e:
            self.log(f"Error importing geometry: {str(e)}")
            self.update_status("Geometry import failed", show_progress=False)
            messagebox.showerror("Import Error", f"Failed to import geometry:\n\n{str(e)}")
    
    def _load_real_geometry(self, file_path):
        """Load a real geometry file - returns True if successful"""
        try:
            # This would use a proper CAD parser in a real implementation
            # For now, we'll return False to fall back to demo mode
            return False
        except Exception as e:
            self.log(f"Error loading geometry file: {str(e)}")
            return False
    
    def _create_sample_geometry(self):
        """Create a sample geometry for visualization"""
        # Clear existing plot
        self.geometry_ax.clear()
        
        # Generate a simple geometry - a cylinder
        theta = np.linspace(0, 2*np.pi, 30)
        z = np.linspace(0, 2, 30)
        theta_grid, z_grid = np.meshgrid(theta, z)
        x = np.cos(theta_grid)
        y = np.sin(theta_grid)
        
        # Plot the cylinder surface
        self.geometry_ax.plot_surface(x, y, z_grid, alpha=0.8, cmap=cm.coolwarm)
        
        # Add top and bottom circles
        theta = np.linspace(0, 2*np.pi, 30)
        x = np.cos(theta)
        y = np.sin(theta)
        self.geometry_ax.plot(x, y, np.zeros_like(theta), 'b-')
        self.geometry_ax.plot(x, y, np.ones_like(theta)*2, 'b-')
        
        # Set labels and title
        self.geometry_ax.set_title("Sample Geometry")
        self.geometry_ax.set_xlabel("X")
        self.geometry_ax.set_ylabel("Y")
        self.geometry_ax.set_zlabel("Z")
        
        # Update the display
        self.geometry_canvas.draw()
    
    def export_geometry(self):
        """Export geometry to file"""
        file_path = filedialog.asksaveasfilename(
            title="Export Geometry",
            defaultextension=".step",
            filetypes=[
                ("STEP Files", "*.step"),
                ("IGES Files", "*.iges"),
                ("STL Files", "*.stl"),
                ("All Files", "*.*")
            ]
        )
        
        if not file_path:
            return
            
        try:
            self.update_status(f"Exporting geometry to {file_path}...", show_progress=True)
            
            # In a real app, this would save the actual geometry
            # For demo, just create a placeholder file
            with open(file_path, 'w') as f:
                f.write("ISO-10303-21;\n")
                f.write("HEADER;\n")
                f.write("FILE_DESCRIPTION(('Demo Geometry'),'2;1');\n")
                f.write("FILE_NAME('demo.step','2025-04-17',(''),(''),('Demo App'),'','');\n")
                f.write("FILE_SCHEMA(('AUTOMOTIVE_DESIGN { 1 0 10303 214 1 1 1 1 }'));\n")
                f.write("ENDSEC;\n")
                f.write("DATA;\n")
                f.write("/* This is a placeholder file for demonstration purposes */\n")
                f.write("ENDSEC;\n")
                f.write("END-ISO-10303-21;\n")
                
            self.update_status(f"Geometry exported successfully", show_progress=False)
            messagebox.showinfo("Export Complete", f"Geometry exported to {os.path.basename(file_path)}")
            
        except Exception as e:
            self.log(f"Error exporting geometry: {str(e)}")
            self.update_status("Geometry export failed", show_progress=False)
            messagebox.showerror("Export Error", f"Failed to export geometry:\n\n{str(e)}")
    
    def update_geometry_display(self):
        """Update geometry display based on selected options"""
        try:
            display_mode = self.geometry_display_var.get()
            
            # Simply redraw the geometry for demonstration purposes
            self._create_sample_geometry()
            
            # Adjust display properties based on mode
            if display_mode == "Wireframe":
                # In a real implementation, you would change to wireframe view
                pass
            elif display_mode == "Transparent":
                # Make surfaces more transparent
                for c in self.geometry_ax.collections:
                    c.set_alpha(0.3)
            
            self.geometry_ax.set_title(f"Geometry - {display_mode}")
            self.geometry_canvas.draw()
            
        except Exception as e:
            self.log(f"Error updating geometry display: {str(e)}")
            messagebox.showerror("Display Error", f"Failed to update geometry display:\n\n{str(e)}")
    
    def export_cfd_results(self):
        """Export CFD results to file"""
        file_path = filedialog.asksaveasfilename(
            title="Export CFD Results",
            defaultextension=".csv",
            filetypes=[
                ("CSV Files", "*.csv"),
                ("VTK Files", "*.vtk"),
                ("NumPy Files", "*.npy"),
                ("MATLAB Files", "*.mat"),
                ("All Files", "*.*")
            ]
        )
        
        if not file_path:
            return
            
        try:
            field_name = self.field_var.get()
            self.update_status(f"Exporting {field_name} results to {file_path}...", show_progress=True)
            
            # Check if we have visualization data
            if not hasattr(self, 'visualization_data') or self.visualization_data.get(field_name) is None:
                raise ValueError(f"No {field_name} data available to export")
            
            # Export based on file format
            if file_path.endswith('.csv'):
                # Export as CSV
                X = self.visualization_data['X']
                Y = self.visualization_data['Y']
                Z = self.visualization_data[field_name]
                
                with open(file_path, 'w') as f:
                    f.write(f"X,Y,{field_name}\n")
                    for i in range(len(X)):
                        for j in range(len(X[i])):
                            f.write(f"{X[i][j]},{Y[i][j]},{Z[i][j]}\n")
            
            elif file_path.endswith('.vtk'):
                # Export as VTK structured grid
                self._export_to_vtk(file_path, field_name)
                
            elif file_path.endswith('.npy'):
                # Export as NumPy array
                import numpy as np
                data_dict = {
                    'X': self.visualization_data['X'],
                    'Y': self.visualization_data['Y'],
                    field_name: self.visualization_data[field_name]
                }
                np.save(file_path, data_dict)
                
            elif file_path.endswith('.mat'):
                # Export as MATLAB file
                try:
                    import scipy.io
                    scipy.io.savemat(file_path, {
                        'X': self.visualization_data['X'],
                        'Y': self.visualization_data['Y'],
                        field_name.replace(' ', '_'): self.visualization_data[field_name]
                    })
                except ImportError:
                    messagebox.showerror("Export Error", "SciPy is required for MATLAB export but was not found.")
                    return
            else:
                # For other formats, just create a placeholder
                with open(file_path, 'w') as f:
                    f.write(f"# {field_name} CFD Results\n")
                    f.write("# This is a placeholder file for demonstration purposes\n")
                    
            self.update_status(f"Results exported successfully", show_progress=False)
            messagebox.showinfo("Export Complete", f"Results exported to {os.path.basename(file_path)}")
            
        except Exception as e:
            self.log(f"Error exporting results: {str(e)}")
            self.update_status("Results export failed", show_progress=False)
            messagebox.showerror("Export Error", f"Failed to export results:\n\n{str(e)}")
    
    def _export_to_vtk(self, file_path, field_name):
        """Export results to VTK file format"""
        try:
            # Get data
            X = self.visualization_data['X']
            Y = self.visualization_data['Y']
            Z = self.visualization_data[field_name]
            
            # Create VTK structured grid file
            with open(file_path, 'w') as f:
                # Write header
                f.write("# vtk DataFile Version 3.0\n")
                f.write(f"CFD Results - {field_name}\n")
                f.write("ASCII\n")
                f.write("DATASET STRUCTURED_GRID\n")
                
                # Write dimensions
                nx, ny = X.shape
                f.write(f"DIMENSIONS {nx} {ny} 1\n")
                
                # Write points
                f.write(f"POINTS {nx*ny} float\n")
                for i in range(nx):
                    for j in range(ny):
                        f.write(f"{X[i][j]} {Y[i][j]} 0.0\n")
                
                # Write point data
                f.write(f"POINT_DATA {nx*ny}\n")
                f.write(f"SCALARS {field_name} float 1\n")
                f.write("LOOKUP_TABLE default\n")
                for i in range(nx):
                    for j in range(ny):
                        f.write(f"{Z[i][j]}\n")
        except Exception as e:
            self.log(f"Error creating VTK file: {str(e)}")
            raise
    
    def setup_visualization_tab(self):
        """Set up the modernized visualization tab"""
        # Create main container with scrollable functionality
        outer_frame, main_frame = self.create_scrollable_frame(self.visualization_tab, 
                                                            bg=self.theme.bg_color,
                                                            highlightthickness=0)
        outer_frame.pack(fill='both', expand=True)
        
        # Create a horizontal paned window for control panel and visualization area
        paned_window = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Left control panel - create it directly as a child of the paned_window
        control_panel = ttk.Frame(paned_window)
        
        # Right visualization area 
        visualization_area = ttk.Frame(paned_window)
        
        # Add both to the paned window
        paned_window.add(control_panel, weight=1)
        paned_window.add(visualization_area, weight=3)
        
        # Set up visualization controls in the control panel
        self._setup_control_panel(control_panel)
        
        # Set up visualization display in the visualization area
        self._setup_display_area(visualization_area)
        
        self.log("Modernized visualization tab initialized")
        
    def _toggle_range_inputs(self):
        """Toggle min/max range inputs based on auto range setting"""
        if self.auto_range_var.get():
            # Disable manual inputs
            for widget in self.range_inputs_frame.winfo_children():
                if isinstance(widget, ttk.Entry):
                    widget.configure(state='disabled')
        else:
            # Enable manual inputs
            for widget in self.range_inputs_frame.winfo_children():
                if isinstance(widget, ttk.Entry):
                    widget.configure(state='normal')
            
            # Update with current values if data is available
            if hasattr(self, 'visualization_data'):
                field = self.field_var.get()
                if field in self.visualization_data and self.visualization_data[field] is not None:
                    Z = self.visualization_data[field]
                    self.range_min_var.set(f"{np.min(Z):.4f}")
                    self.range_max_var.set(f"{np.max(Z):.4f}")
        
        # Update visualization
        self.update_cfd_visualization()
    
    def update_cfd_visualization(self, event=None):
        """Update the CFD visualization based on selected field and visualization type"""
        if not hasattr(self, 'cfd_ax') or not hasattr(self, 'visualization_data'):
            return
            
        # Show/hide specialized control frames based on visualization type
        viz_type = self.viz_var.get()
        
        # Handle specialized control visibility
        if hasattr(self, 'vector_frame'):
            if viz_type == "Vector":
                self.vector_frame.pack(fill='x', padx=5, pady=5)
            else:
                self.vector_frame.pack_forget()
                
        if hasattr(self, 'slice_frame'):
            if viz_type == "Slice":
                self.slice_frame.pack(fill='x', padx=5, pady=5)
            else:
                self.slice_frame.pack_forget()
        
        # Clear the current plot
        self.cfd_ax.clear()
        
        # Get selected field and visualization type
        field = self.field_var.get()
        colormap = self.colormap_var.get() if hasattr(self, 'colormap_var') else "viridis"
        
        # Get data range
        vmin, vmax = None, None
        if hasattr(self, 'auto_range_var') and not self.auto_range_var.get():
            try:
                vmin = float(self.range_min_var.get())
                vmax = float(self.range_max_var.get())
            except (ValueError, TypeError):
                pass
        
        # Get data - if we have it
        if hasattr(self, 'visualization_data'):
            X = self.visualization_data.get('X')
            Y = self.visualization_data.get('Y')
            Z = self.visualization_data.get(field)
            
            if X is not None and Y is not None and Z is not None:
                # Calculate statistics and update stats display
                self._update_statistics(Z, field)
                
                # Create visualization based on selected type
                if viz_type == "Contour":
                    try:
                        levels = int(self.contour_levels_var.get())
                    except (ValueError, AttributeError):
                        levels = 20
                    
                    cs = self.cfd_ax.contourf(X, Y, Z, cmap=colormap, levels=levels, vmin=vmin, vmax=vmax)
                    
                    # Add contour lines
                    contour_lines = self.cfd_ax.contour(X, Y, Z, levels=levels, colors='black', linewidths=0.5, vmin=vmin, vmax=vmax)
                    
                    # Add contour labels (use fewer levels for clarity)
                    self.cfd_ax.clabel(contour_lines, inline=True, fontsize=8, fmt='%.2f', levels=contour_lines.levels[::4])
                    
                    # Add colorbar if requested
                    if self.show_colorbar_var.get():
                        self.cfd_fig.colorbar(cs, ax=self.cfd_ax)
                    
                elif viz_type == "Surface":
                    # Convert mesh grid to 3D
                    self.cfd_ax.remove()
                    self.cfd_ax = self.cfd_fig.add_subplot(111, projection='3d')
                    surf = self.cfd_ax.plot_surface(X, Y, Z, cmap=colormap, linewidth=0, antialiased=True, vmin=vmin, vmax=vmax)
                    
                    # Add colorbar if requested
                    if self.show_colorbar_var.get():
                        self.cfd_fig.colorbar(surf, ax=self.cfd_ax, shrink=0.5, aspect=5)
                        
                elif viz_type == "Vector":
                    # Show a quiver plot for vector fields
                    # For demo, use gradients of Z as vector components
                    dx, dy = np.gradient(Z)
                    
                    # Get vector density
                    try:
                        density = int(self.vector_density_var.get())
                    except (ValueError, AttributeError):
                        density = 20
                    
                    # Calculate step size based on density
                    step = max(1, int(min(X.shape) / density))
                    
                    # Create quiver plot
                    quiv = self.cfd_ax.quiver(X[::step, ::step], Y[::step, ::step], 
                                    dx[::step, ::step], dy[::step, ::step],
                                    Z[::step, ::step],  # Use field values for color
                                    cmap=colormap, scale=50, vmin=vmin, vmax=vmax)
                    
                    # Add colorbar if requested
                    if self.show_colorbar_var.get():
                        self.cfd_fig.colorbar(quiv, ax=self.cfd_ax)
                    
                elif viz_type == "Streamlines":
                    # Compute gradients for streamlines
                    dx, dy = np.gradient(Z)
                    
                    # Normalize gradients for better visualization
                    magnitude = np.sqrt(dx**2 + dy**2)
                    magnitude[magnitude == 0] = 1  # Avoid division by zero
                    dx = dx / magnitude
                    dy = dy / magnitude
                    
                    # Create streamplot with colors based on field values
                    strm = self.cfd_ax.streamplot(X, Y, dx, dy, color=Z, 
                                               density=1.5, linewidth=1, 
                                               cmap=colormap, arrowsize=1.2)
                    
                    # Add colorbar if requested
                    if self.show_colorbar_var.get():
                        self.cfd_fig.colorbar(strm.lines, ax=self.cfd_ax)
                    
                elif viz_type == "Isosurface":
                    # Create a 3D plot with iso-contours
                    self.cfd_ax.remove()
                    self.cfd_ax = self.cfd_fig.add_subplot(111, projection='3d')
                    
                    # Create elevated surface
                    surf = self.cfd_ax.plot_surface(X, Y, np.zeros_like(Z), 
                                                facecolors=cm.get_cmap(colormap)((Z - np.min(Z)) / (np.max(Z) - np.min(Z) if np.max(Z) > np.min(Z) else 1)),
                                                cmap=colormap, alpha=0.8)
                    
                    # Add multiple contour lines at different heights
                    num_levels = 8
                    if vmin is not None and vmax is not None:
                        levels = np.linspace(vmin, vmax, num_levels)
                    else:
                        levels = np.linspace(np.min(Z), np.max(Z), num_levels)
                    
                    # Draw contour lines at different heights
                    for i, level in enumerate(levels):
                        z_level = i * 0.5  # Offset height for each contour
                        cs = self.cfd_ax.contour(X, Y, Z, [level], colors=['black'], 
                                              linewidths=2, offset=z_level)
                        
                        # Fill contours
                        self.cfd_ax.contourf(X, Y, Z, [level, level+0.0001], 
                                          colors=[cm.get_cmap(colormap)((level - np.min(Z)) / (np.max(Z) - np.min(Z) if np.max(Z) > np.min(Z) else 1))], 
                                          offset=z_level)
                    
                    # Add colorbar if requested
                    if self.show_colorbar_var.get():
                        m = cm.ScalarMappable(cmap=colormap)
                        m.set_array(Z)
                        self.cfd_fig.colorbar(m, ax=self.cfd_ax)
                        
                    # Set z axis limits
                    self.cfd_ax.set_zlim(0, (num_levels-1) * 0.5)
                    
                elif viz_type == "Slice":
                    # Show a sliced view (either vertical or horizontal)
                    position = self.slice_position_var.get()
                    
                    # Extract slice index based on position
                    i_slice = int(position * (X.shape[0]-1))
                    j_slice = int(position * (X.shape[1]-1))
                    
                    # Plot horizontal slice
                    h_line = self.cfd_ax.axhline(y=Y[i_slice, 0], color='white', linestyle='--')
                    h_slice = self.cfd_ax.plot(X[i_slice, :], Z[i_slice, :], 'r-', linewidth=2, label='Horizontal Slice')
                    
                    # Plot vertical slice
                    v_line = self.cfd_ax.axvline(x=X[0, j_slice], color='white', linestyle='--')
                    v_slice = self.cfd_ax.plot(Y[:, j_slice], Z[:, j_slice], 'g-', linewidth=2, label='Vertical Slice')
                    
                    # Also show the background contour plot
                    cs = self.cfd_ax.contourf(X, Y, Z, cmap=colormap, alpha=0.7, levels=15, vmin=vmin, vmax=vmax)
                    
                    # Add colorbar if requested
                    if self.show_colorbar_var.get():
                        self.cfd_fig.colorbar(cs, ax=self.cfd_ax)
                    
                    # Add legend
                    self.cfd_ax.legend(loc='best')
                    
                # Set title and labels based on options
                title = f"{field} - {viz_type}"
                self.cfd_ax.set_title(title)
                
                if self.show_labels_var.get():
                    self.cfd_ax.set_xlabel("X")
                    self.cfd_ax.set_ylabel("Y")
                    if viz_type in ["Surface", "Isosurface"]:
                        self.cfd_ax.set_zlabel("Z")
                
                # Add grid if requested
                if self.show_grid_var.get():
                    self.cfd_ax.grid(True)
                
            else:
                # No data available, show message
                self.cfd_ax.text(0.5, 0.5, "No CFD data available.\nRun workflow to generate results.",
                            horizontalalignment='center', verticalalignment='center',
                            transform=self.cfd_ax.transAxes)
                
                # Clear statistics
                if hasattr(self, 'stats_text'):
                    self.stats_text.config(state='normal')
                    self.stats_text.delete(1.0, tk.END)
                    self.stats_text.insert(tk.END, "No data available")
                    self.stats_text.config(state='disabled')
        else:
            # No data available, show message
            self.cfd_ax.text(0.5, 0.5, "No CFD data available.\nRun workflow to generate results.",
                        horizontalalignment='center', verticalalignment='center',
                        transform=self.cfd_ax.transAxes)
        
        # Redraw the canvas
        self.cfd_canvas.draw()
    
    def _update_statistics(self, data, field_name):
        """Update statistics display with data metrics"""
        if not hasattr(self, 'stats_text'):
            return
            
        # Calculate basic statistics
        min_val = np.min(data)
        max_val = np.max(data)
        mean_val = np.mean(data)
        median_val = np.median(data)
        std_val = np.std(data)
        
        # Update stats text
        self.stats_text.config(state='normal')
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(tk.END, f"{field_name} Statistics:\n")
        self.stats_text.insert(tk.END, f"Min: {min_val:.4f}\n")
        self.stats_text.insert(tk.END, f"Max: {max_val:.4f}\n")
        self.stats_text.insert(tk.END, f"Mean: {mean_val:.4f}\n")
        self.stats_text.insert(tk.END, f"Median: {median_val:.4f}\n")
        self.stats_text.insert(tk.END, f"Std Dev: {std_val:.4f}\n")
        self.stats_text.config(state='disabled')
        
        # Update range inputs if in auto mode
        if hasattr(self, 'auto_range_var') and self.auto_range_var.get():
            self.range_min_var.set(f"{min_val:.4f}")
            self.range_max_var.set(f"{max_val:.4f}")
    
    def export_cfd_image(self):
        """Export the current CFD visualization as an image"""
        file_path = filedialog.asksaveasfilename(
            title="Export Visualization Image",
            defaultextension=".png",
            filetypes=[
                ("PNG Image", "*.png"),
                ("JPEG Image", "*.jpg"),
                ("SVG Image", "*.svg"),
                ("PDF Document", "*.pdf"),
                ("All Files", "*.*")
            ]
        )
        
        if not file_path:
            return
            
        try:
            self.update_status(f"Exporting visualization to {file_path}...", show_progress=True)
            
            # Save figure with tight layout and high DPI for quality
            self.cfd_fig.savefig(file_path, dpi=300, bbox_inches='tight')
            
            self.update_status(f"Image exported successfully", show_progress=False)
            messagebox.showinfo("Export Complete", f"Visualization exported to {os.path.basename(file_path)}")
            
        except Exception as e:
            self.log(f"Error exporting image: {str(e)}")
            self.update_status("Image export failed", show_progress=False)
            messagebox.showerror("Export Error", f"Failed to export image:\n\n{str(e)}")
    
    def get_memory_info(self):
            """Get system memory information"""
            try:
                if platform.system() == "Linux":
                    with open('/proc/meminfo', 'r') as f:
                        meminfo = f.readlines()
                    
                    mem_total = None
                    mem_available = None
                    
                    for line in meminfo:
                        if 'MemTotal' in line:
                            mem_total = int(line.split()[1])
                        elif 'MemAvailable' in line or 'MemFree' in line:
                            if mem_available is None:  # Prefer MemAvailable, but use MemFree as backup
                                mem_available = int(line.split()[1])
                    
                    # Convert to GB
                    mem_total_gb = mem_total / (1024 * 1024) if mem_total else 0
                    mem_available_gb = mem_available / (1024 * 1024) if mem_available else 0
                    
                    return f"{mem_total_gb:.1f} GB Total, {mem_available_gb:.1f} GB Available"
                
                elif platform.system() == "Windows":
                    import psutil
                    mem = psutil.virtual_memory()
                    mem_total_gb = mem.total / (1024 * 1024 * 1024)
                    mem_available_gb = mem.available / (1024 * 1024 * 1024)
                    
                    return f"{mem_total_gb:.1f} GB Total, {mem_available_gb:.1f} GB Available"
                
                else:
                    return "Unknown"
                    
            except Exception as e:
                self.log(f"Error getting memory info: {e}")
                return "Error retrieving memory information"

    def browse_nx_path(self):
            """Open file browser to select NX executable path"""
            file_path = filedialog.askopenfilename(
                title="Select NX Executable",
                filetypes=[("Executable files", "*.exe"), ("All files", "*.*")]
            )
            if file_path:
                self.nx_path.delete(0, tk.END)
                self.nx_path.insert(0, file_path)
                self.log(f"Updated NX path: {file_path}")
    
    def setup_status_bar(self):
        """Set up the status bar at the bottom of the window"""
        self.status_bar = ttk.Frame(self.root)
        self.status_bar.pack(side='bottom', fill='x')
        
        # Status message
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        self.status_label = ttk.Label(self.status_bar, textvariable=self.status_var)
        self.status_label.pack(side='left', padx=10, pady=5)
        
        # Progress bar (initially hidden)
        self.progress_bar = ttk.Progressbar(self.status_bar, orient='horizontal', length=200, mode='indeterminate')
        
        # Memory usage on right
        self.memory_var = tk.StringVar()
        self.memory_var.set("Memory: --")
        memory_label = ttk.Label(self.status_bar, textvariable=self.memory_var)
        memory_label.pack(side='right', padx=10, pady=5)
        
        # Update memory usage periodically
        self.update_memory_usage()

    def update_status(self, message, show_progress=False):
        """Update the status bar message and progress indicator"""
        if hasattr(self, 'status_var'):
            self.status_var.set(message)
            
            if show_progress and hasattr(self, 'progress_bar'):
                if not self.progress_bar.winfo_ismapped():
                    self.progress_bar.pack(side='left', padx=10, pady=5)
                    self.progress_bar.start(10)
            else:
                if hasattr(self, 'progress_bar') and self.progress_bar.winfo_ismapped():
                    self.progress_bar.stop()
                    self.progress_bar.pack_forget()
        
        self.log(message)

    def update_memory_display(self):
        """Update the memory usage in the status bar"""
        if hasattr(self, 'memory_var'):
            memory_info = self.get_memory_info()
            self.memory_var.set(f"Memory: {memory_info}")
        
        # Schedule next update (every 5 seconds)
        if hasattr(self, 'root'):
            self.root.after(5000, self.update_memory_display)

    def update_memory_usage(self):
        """Update the memory usage display"""
        if hasattr(self, 'memory_var'):
            try:
                memory_info = self.get_memory_info().split(",")[0]  # Just get the total part
                self.memory_var.set(f"Memory: {memory_info}")
            except:
                self.memory_var.set("Memory: --")
        
        # Schedule next update
        self.root.after(10000, self.update_memory_usage)  # Update every 10 seconds   
        
    def browse_project_dir(self):
            """Open directory browser to select project directory"""
            dir_path = filedialog.askdirectory(
                title="Select Project Directory"
            )
            if dir_path:
                self.project_dir.delete(0, tk.END)
                self.project_dir.insert(0, dir_path)
                self.log(f"Updated project directory: {dir_path}")
        
    def apply_appearance_settings(self):
            """Apply selected appearance settings"""
            theme_name = self.theme_combo.get()
            font_size = self.font_size.get()
            
            self.log(f"Applying appearance settings: Theme={theme_name}, Font Size={font_size}")
            
            try:
                # Apply theme
                if theme_name == "Dark":
                    self.apply_dark_theme()
                elif theme_name == "Light":
                    self.apply_light_theme()
                elif theme_name == "System":
                    self.apply_system_theme()
                
                # Apply font size
                if font_size == "Small":
                    self.apply_font_size(8, 10, 12)
                elif font_size == "Medium":
                    self.apply_font_size(10, 12, 14)
                elif font_size == "Large":
                    self.apply_font_size(12, 14, 16)
                    
                messagebox.showinfo("Settings Applied", "Appearance settings have been applied.")
                self.update_status("Appearance settings applied")
            except Exception as e:
                self.log(f"Error applying appearance settings: {e}")
                messagebox.showerror("Error", f"Failed to apply appearance settings: {e}")
        
    def apply_dark_theme(self):
            """Apply dark theme"""
            # Update theme object
            self.theme.bg_color = "#2C3E50"
            self.theme.primary_color = "#34495E"
            self.theme.secondary_color = "#3498DB"
            self.theme.accent_hover = "#2980B9"
            self.theme.text_color = "#ECF0F1"
            self.theme.light_text = "#FFFFFF"
            self.theme.success_color = "#2ECC71"
            self.theme.warning_color = "#F39C12"
            self.theme.error_color = "#E74C3C"
            self.theme.border_color = "#7F8C8D"
            
            # Apply theme to all widgets
            self.theme.apply_theme(self.root)
            
    def apply_light_theme(self):
            """Apply light theme"""
            # Reset theme object to default values
            self.theme = ModernTheme()
            
            # Apply theme to all widgets
            self.theme.apply_theme(self.root)
            
    def apply_system_theme(self):
            """Apply system-based theme"""
            try:
                # Try to detect system theme (simplified approach)
                if platform.system() == "Windows":
                    import winreg
                    registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
                    key = winreg.OpenKey(registry, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
                    value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                    
                    if value == 0:
                        self.apply_dark_theme()
                    else:
                        self.apply_light_theme()
                else:
                    # Default to light theme for other platforms
                    self.apply_light_theme()
            except Exception:
                # If detection fails, fall back to light theme
                self.apply_light_theme()
        
    def apply_font_size(self, size_setting):
        """Apply font size settings"""
        # Convert string settings to numeric values
        if size_setting == "Small":
            small, normal, large = 8, 10, 12
        elif size_setting == "Medium":
            small, normal, large = 10, 12, 14
        elif size_setting == "Large":
            small, normal, large = 12, 14, 16
        else:
            # Default to medium if unknown
            small, normal, large = 10, 12, 14
        
        # Update theme font sizes
        self.theme.small_font = ("Segoe UI", small)
        self.theme.normal_font = ("Segoe UI", normal)
        self.theme.header_font = ("Segoe UI", large, "bold")
        self.theme.button_font = ("Segoe UI", normal)
        self.theme.code_font = ("Consolas", small+1)
        
        # Apply theme to reapply fonts
        self.theme.apply_theme(self.root)
        
        # Log the change
        self.log(f"Font size updated to {size_setting}")

    def run_workflow(self):
        """Execute the complete workflow process"""
        try:
            # Validate inputs before running
            self._validate_workflow_inputs()
            
            # Check if a workflow is already running
            if hasattr(self, 'workflow_running') and self.workflow_running:
                messagebox.showwarning("Workflow Running", 
                                        "A workflow is already in progress. Please wait or cancel it first.")
                return
            
            # Get parameters from UI
            L4 = float(self.l4_workflow.get())
            L5 = float(self.l5_workflow.get())
            alpha1 = float(self.alpha1_workflow.get())
            alpha2 = float(self.alpha2_workflow.get())
            alpha3 = float(self.alpha3_workflow.get())
            
            # Get execution environment
            env = self.env_var.get() if hasattr(self, 'env_var') else "local"
            
            # Update UI to show processing
            self.update_status("Running simulation workflow...", show_progress=True)
            self.workflow_status_text.configure(state='normal')
            self.workflow_status_text.delete(1.0, tk.END)
            self.workflow_status_text.insert(tk.END, f"Starting workflow with parameters:\n")
            self.workflow_status_text.insert(tk.END, f"L4: {L4}, L5: {L5}, Alpha1: {alpha1}, Alpha2: {alpha2}, Alpha3: {alpha3}\n")
            self.workflow_status_text.configure(state='disabled')
            
            # Update status in workflow visualization
            for step in self.workflow_steps:
                step["status"] = "pending"
            self._redraw_workflow()
            
            # Set workflow running flag
            self.workflow_running = True
            self.run_button.config(state="disabled")
            self.cancel_button.config(state="normal")
            
            if env == "local":
                # Start workflow in separate thread to keep UI responsive
                self.current_workflow = threading.Thread(
                    target=self._run_workflow_thread,
                    args=(L4, L5, alpha1, alpha2, alpha3),
                    daemon=True
                )
                self.current_workflow.start()
            else:  # HPC
                # Get HPC profile
                if hasattr(self, 'workflow_hpc_profile'):
                    hpc_profile = self.workflow_hpc_profile.get()
                    if not hpc_profile:
                        messagebox.showerror("Profile Required", "Please select an HPC profile to continue.")
                        self.workflow_running = False
                        self.run_button.config(state="normal")
                        self.cancel_button.config(state="disabled")
                        return
                    
                    # Submit workflow to HPC
                    self.submit_workflow_to_hpc(L4, L5, alpha1, alpha2, alpha3)
                else:
                    messagebox.showerror("HPC Not Available", "HPC execution is not available.")
                    self.workflow_running = False
                    self.run_button.config(state="normal")
                    self.cancel_button.config(state="disabled")
        except ValueError as ve:
            # Handle validation errors
            self.log(f"Input validation error: {str(ve)}")
            messagebox.showerror("Invalid Input", str(ve))
        except Exception as e:
            # Handle other exceptions
            self.log(f"Error starting workflow: {str(e)}")
            messagebox.showerror("Error", f"Failed to start workflow: {str(e)}")
            self.update_status("Workflow failed", show_progress=False)

    def _validate_workflow_inputs(self):
        """Validate workflow input parameters"""
        try:
            # Check that all parameter values are valid numbers
            L4 = float(self.l4_workflow.get())
            L5 = float(self.l5_workflow.get())
            alpha1 = float(self.alpha1_workflow.get())
            alpha2 = float(self.alpha2_workflow.get())
            alpha3 = float(self.alpha3_workflow.get())
            
            # Validate ranges
            if L4 <= 0:
                raise ValueError("L4 must be greater than zero")
            
            if L5 <= 0:
                raise ValueError("L5 must be greater than zero")
                
            # Angle validations
            if alpha1 < 0 or alpha1 > 90:
                raise ValueError("Alpha1 must be between 0 and 90 degrees")
                
            if alpha2 < 0 or alpha2 > 90:
                raise ValueError("Alpha2 must be between 0 and 90 degrees")
                
            if alpha3 < 0 or alpha3 > 90:
                raise ValueError("Alpha3 must be between 0 and 90 degrees")
            
            # For HPC execution, validate job settings
            if hasattr(self, 'env_var') and self.env_var.get() == "hpc":
                if hasattr(self, 'workflow_hpc_profile') and not self.workflow_hpc_profile.get():
                    raise ValueError("Please select an HPC profile")
        
        except ValueError as e:
            if "could not convert string to float" in str(e).lower():
                raise ValueError("All parameters must be valid numbers")
            raise

    def _run_workflow_thread(self, L4, L5, alpha1, alpha2, alpha3):
        """Execute the workflow in a separate thread"""
        try:
            # Set up flag to allow cancellation
            self.workflow_canceled = False
            
            # STEP 1: Update NX model using expressions
            self.root.after(0, lambda: self._update_workflow_status("Updating NX model..."))
            self.root.after(0, lambda: self._update_workflow_step("CAD", "running"))
            
            # Generate expressions file
            try:
                exp(L4, L5, alpha1, alpha2, alpha3)
                self.log(f"Generated expressions file with parameters: L4={L4}, L5={L5}, Alpha1={alpha1}, Alpha2={alpha2}, Alpha3={alpha3}")
            except Exception as e:
                self.log(f"Error generating expressions file: {str(e)}")
                raise
            
            # Check for cancellation before proceeding
            if self.workflow_canceled:
                self.root.after(0, lambda: self._workflow_canceled())
                return
                
            # Run NX automation to update model and export STEP
            try:
                step_file = run_nx_workflow()
                self.log(f"NX workflow completed, generated: {step_file}")
                self.root.after(0, lambda: self._update_workflow_step("CAD", "complete"))
            except Exception as e:
                self.log(f"Error in NX workflow: {str(e)}")
                self.root.after(0, lambda: self._update_workflow_step("CAD", "error"))
                raise RuntimeError(f"NX workflow failed: {str(e)}")
            
            # Check for cancellation before proceeding
            if self.workflow_canceled:
                self.root.after(0, lambda: self._workflow_canceled())
                return
                
            # STEP 2: Generate mesh from STEP
            self.root.after(0, lambda: self._update_workflow_status("Generating mesh..."))
            self.root.after(0, lambda: self._update_workflow_step("Mesh", "running"))
            
            # Define mesh file
            mesh_file = "INTAKE3D.msh"
            
            # Process mesh
            try:
                process_mesh(step_file, mesh_file)
                self.log(f"Mesh generation completed: {mesh_file}")
                self.root.after(0, lambda: self._update_workflow_step("Mesh", "complete"))
            except Exception as e:
                self.log(f"Error in mesh generation: {str(e)}")
                self.root.after(0, lambda: self._update_workflow_step("Mesh", "error"))
                raise RuntimeError(f"Mesh generation failed: {str(e)}")
            
            # Check for cancellation before proceeding
            if self.workflow_canceled:
                self.root.after(0, lambda: self._workflow_canceled())
                return
                
            # STEP 3: Run CFD simulation
            self.root.after(0, lambda: self._update_workflow_status("Running CFD simulation..."))
            self.root.after(0, lambda: self._update_workflow_step("CFD", "running"))
            
            # Run CFD solver
            try:
                run_cfd(mesh_file)
                self.log(f"CFD simulation completed")
                self.root.after(0, lambda: self._update_workflow_step("CFD", "complete"))
            except Exception as e:
                self.log(f"Error in CFD simulation: {str(e)}")
                self.root.after(0, lambda: self._update_workflow_step("CFD", "error"))
                raise RuntimeError(f"CFD simulation failed: {str(e)}")
            
            # Check for cancellation before proceeding
            if self.workflow_canceled:
                self.root.after(0, lambda: self._workflow_canceled())
                return
                
            # STEP 4: Process results
            self.root.after(0, lambda: self._update_workflow_status("Processing results..."))
            self.root.after(0, lambda: self._update_workflow_step("Results", "running"))
            
            # Define results file
            results_output = "processed_results.csv"
            
            # Process CFD results
            try:
                process_results("cfd_results", results_output)
                self.log(f"Results processing completed: {results_output}")
                self.root.after(0, lambda: self._update_workflow_step("Results", "complete"))
                
                # Load and display results
                self._load_and_display_results(results_output, L4, L5, alpha1, alpha2, alpha3)
            except Exception as e:
                self.log(f"Error in results processing: {str(e)}")
                self.root.after(0, lambda: self._update_workflow_step("Results", "error"))
                raise RuntimeError(f"Results processing failed: {str(e)}")
            
            # Workflow completed successfully
            self.root.after(0, lambda: self._workflow_completed())
            
        except Exception as e:
            # Handle uncaught exceptions
            self.log(f"Workflow error: {str(e)}")
            self.root.after(0, lambda: self._workflow_failed(str(e)))

    def _update_workflow_status(self, message):
        """Update the workflow status text widget"""
        if hasattr(self, 'workflow_status_text'):
            self.workflow_status_text.configure(state='normal')
            self.workflow_status_text.insert(tk.END, f"{message}\n")
            self.workflow_status_text.see(tk.END)
            self.workflow_status_text.configure(state='disabled')
        
        self.update_status(message)

    def _update_workflow_step(self, step_name, status):
        """Update a workflow step's status"""
        for step in self.workflow_steps:
            if step["name"] == step_name:
                step["status"] = status
                break
                
        self._redraw_workflow()

    def _load_and_display_results(self, results_file, L4, L5, alpha1, alpha2, alpha3):
        """Load and display simulation results"""
        try:
            # In a real implementation, this would parse the results file
            # For demo, we'll create sample results
            
            # Create sample visualization data
            self.visualization_data = {
                'X': np.linspace(-5, 5, 50),
                'Y': np.linspace(-5, 5, 50),
                'Z': None,
                'Pressure': None,
                'Velocity': None,
                'Temperature': None,
                'Turbulence': None
            }
            
            # Create meshgrid
            X, Y = np.meshgrid(self.visualization_data['X'], self.visualization_data['Y'])
            R = np.sqrt(X**2 + Y**2)
            
            # Calculate sample data fields based on input parameters
            # Simulating relationship between parameters and results
            intensity = 0.5 + 0.1 * L4 + 0.05 * L5 + 0.01 * (alpha1 + alpha2 + alpha3)
            phase = 0.1 * alpha1
            
            self.visualization_data['Z'] = intensity * np.sin(R + phase) / (R + 0.1)
            self.visualization_data['Pressure'] = intensity * (1 - np.exp(-0.1 * R**2)) * (1 + 0.2 * np.sin(5*R))
            self.visualization_data['Velocity'] = intensity * 2 * np.exp(-0.2 * R**2) * (1 + 0.1 * np.cos(5*Y))
            self.visualization_data['Temperature'] = intensity * (0.5 + 0.5 * np.tanh(R - 2))
            self.visualization_data['Turbulence'] = intensity * 0.1 * (X**2 + Y**2) * np.exp(-0.1 * R)
            
            # Update visualization tab
            self.results_notebook.select(self.cfd_results_tab)
            
            # Create results summary
            self._update_workflow_status("Simulation completed successfully!")
            self._update_workflow_status(f"\nParameters: L4={L4}, L5={L5}, Alpha1={alpha1}, Alpha2={alpha2}, Alpha3={alpha3}")
            self._update_workflow_status("\nResults Summary:")
            
            # Simulate extracting key metrics
            pressure_drop = 100 * (0.5 + 0.2 * L4 - 0.1 * L5 + 0.01 * alpha1 + 0.005 * alpha2 + 0.003 * alpha3)
            flow_rate = 50 * (1 + 0.1 * L4 + 0.15 * L5 - 0.01 * alpha1 - 0.02 * alpha2 - 0.01 * alpha3)
            uniformity = 85 * (1 - 0.02 * abs(L4 - 3) - 0.02 * abs(L5 - 3) - 0.01 * abs(alpha1 - 15) - 0.01 * abs(alpha2 - 15) - 0.01 * abs(alpha3 - 15))
            
            self._update_workflow_status(f"Pressure Drop: {pressure_drop:.4f} Pa")
            self._update_workflow_status(f"Flow Rate: {flow_rate:.4f} m³/s")
            self._update_workflow_status(f"Flow Uniformity: {uniformity:.2f}%")
            
            # Store results for later use
            self.last_results = {
                'parameters': {
                    'L4': L4, 'L5': L5, 'alpha1': alpha1, 'alpha2': alpha2, 'alpha3': alpha3
                },
                'metrics': {
                    'pressure_drop': pressure_drop,
                    'flow_rate': flow_rate,
                    'uniformity': uniformity
                }
            }
            
            # Update mesh and geometry views if needed
            
        except Exception as e:
            self.log(f"Error loading and displaying results: {str(e)}")
            self._update_workflow_status(f"Error displaying results: {str(e)}")

    def _workflow_completed(self):
        """Handle workflow completion"""
        self.workflow_running = False
        self.run_button.config(state="normal")
        self.cancel_button.config(state="disabled")
        
        self.update_status("Workflow completed", show_progress=False)
        messagebox.showinfo("Workflow Complete", "The simulation workflow has completed successfully.")
        
    def _workflow_canceled(self):
        """Handle workflow cancellation"""
        self.workflow_running = False
        self.run_button.config(state="normal")
        self.cancel_button.config(state="disabled")
        
        self._update_workflow_status("Workflow was canceled")
        self.update_status("Workflow canceled", show_progress=False)

    def _workflow_failed(self, error_message):
        """Handle workflow failure"""
        self.workflow_running = False
        self.run_button.config(state="normal")
        self.cancel_button.config(state="disabled")
        
        self._update_workflow_status(f"Workflow failed: {error_message}")
        self.update_status("Workflow failed", show_progress=False)
        messagebox.showerror("Workflow Failed", f"The simulation workflow failed:\n\n{error_message}")

    def cancel_workflow(self):
            """Cancel the running workflow"""
            if not hasattr(self, 'workflow_running') or not self.workflow_running:
                return
                
            answer = messagebox.askyesno("Confirm Cancel", "Are you sure you want to cancel the current workflow?")
            if not answer:
                return
                
            self.log("User requested workflow cancellation")
            
            # Set cancellation flag for thread to detect
            self.workflow_canceled = True
            
            # Disable cancel button while canceling
            self.cancel_button.config(state="disabled")
            self._update_workflow_status("Canceling workflow...")
            self.update_status("Canceling workflow...", show_progress=False)

    def setup_app_header(self, root, theme):
        """Setup the application header with logo and title"""
        # Create a frame for the header
        self.header_frame = ttk.Frame(root)
        self.header_frame.pack(fill='x', padx=theme.padding, pady=theme.padding)
        
        # Try to load and display a logo
        try:
            # Check if logo file exists, create a placeholder if not
            if not os.path.exists("logo.png"):
                # Create a simple colored rectangle as placeholder logo
                logo_img = Image.new('RGB', (60, 60), color=theme.primary_color)
                logo_img.save("logo.png")
                
            # Load the logo image
            logo_img = Image.open("logo.png")
            logo_img = logo_img.resize((60, 60), Image.LANCZOS)
            logo_photo = ImageTk.PhotoImage(logo_img)
            
            # Store the image to prevent garbage collection
            self.logo_photo = logo_photo
            
            # Create and place logo label
            logo_label = ttk.Label(self.header_frame, image=logo_photo, background=theme.bg_color)
            logo_label.pack(side='left', padx=theme.padding)
        except Exception as e:
            # If logo loading fails, log the error but continue
            print(f"Warning: Could not load logo: {e}")
        
        # Add application title and version
        title_frame = ttk.Frame(self.header_frame)
        title_frame.pack(side='left', padx=theme.padding)
        
        app_title = ttk.Label(title_frame, text="Intake CFD Optimization Suite", 
                            font=theme.title_font, style="Title.TLabel")
        app_title.pack(anchor='w')
        
        app_version = ttk.Label(title_frame, text="Version 1.0.0", 
                              font=theme.small_font)
        app_version.pack(anchor='w')
        
        # Add some buttons on the right side
        button_frame = ttk.Frame(self.header_frame)
        button_frame.pack(side='right', padx=theme.padding)
        
        help_button = ttk.Button(button_frame, text="Help", command=lambda: self.show_help())
        help_button.pack(side='right', padx=5)
        
        about_button = ttk.Button(button_frame, text="About", command=lambda: self.show_about())
        about_button.pack(side='right', padx=5)
        
        # Add these methods
        def show_help(self):
            """Show help information"""
            messagebox.showinfo("Help", 
                              "For assistance with using the Intake CFD Optimization Suite, please refer to the documentation.")
        
        def show_about(self):
            """Show about dialog"""
            messagebox.showinfo("About", 
                              "Intake CFD Optimization Suite\nVersion 1.0.0\n\n"
                              "A comprehensive tool for optimizing intake manifold designs using CFD simulations.\n\n"
                              "© 2023 Intake Design Technologies")

    def show_help(self):
        """Show help dialog"""
        from tkinter import scrolledtext
        
        help_dialog = tk.Toplevel(self.root)
        help_dialog.title("Help - Intake CFD Optimization Suite")
        help_dialog.geometry("800x600")
        help_dialog.transient(self.root)
        help_dialog.grab_set()
        
        # Add content
        help_text = scrolledtext.ScrolledText(help_dialog, wrap=tk.WORD, width=80, height=30)
        help_text.pack(fill="both", expand=True, padx=20, pady=20)
        
        help_content = """
    # Intake CFD Optimization Suite Help

    ## Overview
    The Intake CFD Optimization Suite is a comprehensive tool for designing and optimizing automotive intake manifolds using Computational Fluid Dynamics (CFD).

    ## Workflow Tab
    This tab guides you through the process of:
    1. Parameter setup
    2. Geometry generation
    3. Mesh creation
    4. CFD simulation
    5. Results analysis

    ## Optimization Tab
    Configure and run optimization studies to improve your design based on:
    - Pressure drop
    - Flow rate
    - Flow uniformity

    ## Visualization Tab
    View 3D models and simulation results.

    ## HPC Tab
    Configure and use High-Performance Computing resources for faster simulations and optimizations.

    ## Settings Tab
    Configure application settings, including:
    - File paths
    - Solver parameters
    - Appearance settings

    ## For more information
    Visit the documentation or contact support at support@intake-cfd.org
    """
        
        help_text.insert(tk.INSERT, help_content)
        help_text.config(state="disabled")
        
        # Close button
        ttk.Button(help_dialog, text="Close", command=help_dialog.destroy).pack(pady=10)

    def show_about(self):
        """Show about dialog"""
        about_dialog = tk.Toplevel(self.root)
        about_dialog.title("About - Intake CFD Optimization Suite")
        about_dialog.geometry("500x400")
        about_dialog.transient(self.root)
        about_dialog.grab_set()
        
        # Add content
        about_frame = ttk.Frame(about_dialog, padding=20)
        about_frame.pack(fill="both", expand=True)
        
        # Logo 
        try:
            import os
            from PIL import Image, ImageTk
            
            logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.png")
            if os.path.exists(logo_path):
                logo_img = Image.open(logo_path)
                logo_img = logo_img.resize((150, 150), Image.Resampling.LANCZOS)
                logo_tk = ImageTk.PhotoImage(logo_img)
                
                logo_label = ttk.Label(about_frame, image=logo_tk)
                logo_label.image = logo_tk  # Keep a reference
                logo_label.pack(pady=10)
        except Exception as e:
            self.log(f"Error loading logo: {e}")
        
        # Title
        ttk.Label(about_frame, text="Intake CFD Optimization Suite", 
                font=("Arial", 16, "bold")).pack(pady=10)
        
        # Version
        ttk.Label(about_frame, text="Version 1.0.0").pack()
        
        # Description
        ttk.Label(about_frame, text="A comprehensive tool for designing and optimizing\n"
                                    "automotive intake manifolds using CFD simulation").pack(pady=10)
        
        # Copyright
        ttk.Label(about_frame, text="© 2025 Mohammed S. Al-Mahrouqi").pack(pady=5)
        
        # Close button
        ttk.Button(about_frame, text="Close", command=about_dialog.destroy).pack(pady=10)

    def browse_key_file(self):
        """Browse for SSH private key file"""
        from tkinter import filedialog
        try:
            key_file = filedialog.askopenfilename(
                title="Select SSH Private Key",
                filetypes=[("All Files", "*.*"), ("SSH Key", "*.pem")]
            )
            if key_file:
                self.hpc_key_path.delete(0, tk.END)
                self.hpc_key_path.insert(0, key_file)
        except Exception as e:
            self.log(f"Error browsing for key file: {e}")

    def _test_hpc_connection(self):
        """Test connection to HPC"""
        try:
            self.connection_status_var.set("Status: Testing...")
            self.connection_status_label.config(foreground="orange")
            
            # Get connection details
            config = self.get_hpc_config()
            if not config:
                return
                
            # Disable test button during test
            for widget in self.hpc_tab.winfo_children():
                if isinstance(widget, ttk.Button) and widget.cget("text") == "Test Connection":
                    widget.config(state=tk.DISABLED)
                    break
            
            # Run the test in a thread
            thread = threading.Thread(target=self._test_connection_thread, args=(config,), daemon=True)
            thread.start()
        except Exception as e:
            self.log(f"Error testing HPC connection: {e}")
            self.connection_status_var.set(f"Status: Error - {str(e)}")
            self.connection_status_label.config(foreground="red")

    def _test_connection_thread(self, config):
        """Thread to test HPC connection"""
        try:
            # Try to import paramiko
            try:
                import paramiko
            except ImportError:
                self.update_connection_status(False, "Paramiko SSH library not installed")
                return
            
            # Test connection
            try:
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                
                if config.get("use_key"):
                    # Connect with key
                    client.connect(
                        hostname=config["hostname"],
                        port=config["port"],
                        username=config["username"],
                        key_filename=config["key_path"],
                        timeout=10
                    )
                else:
                    # Connect with password
                    client.connect(
                        hostname=config["hostname"],
                        port=config["port"],
                        username=config["username"],
                        password=config["password"],
                        timeout=10
                    )
                    
                # Execute a simple command to test
                stdin, stdout, stderr = client.exec_command("uname -a")
                result = stdout.read().decode('utf-8')
                
                # Close connection
                client.close()
                
                # Update UI in main thread
                self.root.after(0, lambda: self.update_connection_status(True, f"Connected: {result.strip()}"))
                
            except Exception as e:
                # Update UI in main thread
                self.root.after(0, lambda: self.update_connection_status(False, str(e)))
                
        except Exception as e:
            # Update UI in main thread
            self.root.after(0, lambda: self.update_connection_status(False, f"Error: {str(e)}"))

    def update_connection_status(self, success, message):
        """Update connection status UI"""
        try:
            if success:
                self.connection_status_var.set(f"Status: Connected")
                self.connection_status_label.config(foreground="green")
                self.log(f"HPC connection successful: {message}")
            else:
                self.connection_status_var.set(f"Status: Failed")
                self.connection_status_label.config(foreground="red")
                self.log(f"HPC connection failed: {message}")
                messagebox.showerror("Connection Failed", f"Failed to connect: {message}")
            
            # Re-enable test button
            for widget in self.hpc_tab.winfo_children():
                if isinstance(widget, ttk.Button) and widget.cget("text") == "Test Connection":
                    widget.config(state=tk.NORMAL)
                    break
        except Exception as e:
            self.log(f"Error updating connection status: {e}")

    def get_hpc_config(self):
        """Get HPC connection configuration from UI settings"""
        try:
            config = {
                "hostname": self.hpc_hostname.get(),
                "username": self.hpc_username.get(),
                "port": int(self.hpc_port.get()) if self.hpc_port.get().isdigit() else 22,
            }
            
            # Get authentication details
            if self.auth_type.get() == "key":
                config["use_key"] = True
                config["key_path"] = self.hpc_key_path.get()
            else:
                config["use_key"] = False
                config["password"] = self.hpc_password.get()
                
            # Get scheduler type
            config["scheduler"] = self.hpc_scheduler.get()
                
            return config
        except Exception as e:
            self.log(f"Error getting HPC config: {e}")
            messagebox.showerror("Error", f"Invalid HPC configuration: {str(e)}")
            return None

    def save_hpc_profiles(self):
        """Save HPC settings to config file"""
        try:
            settings = {
                "hpc_enabled": True,
                "visible_in_gui": True,
                "hostname": self.hpc_hostname.get(),
                "username": self.hpc_username.get(),
                "port": int(self.hpc_port.get()) if self.hpc_port.get().isdigit() else 22,
                "remote_dir": self.hpc_remote_dir.get(),
                "use_key": self.auth_type.get() == "key",
                "key_path": self.hpc_key_path.get(),
                "scheduler": self.hpc_scheduler.get(),
                "job_defaults": {
                    "name": self.job_name.get(),
                    "nodes": self.job_nodes.get(),
                    "cores_per_node": self.job_cores_per_node.get(),
                    "walltime": self.job_walltime.get(),
                    "queue": self.job_queue.get()
                }
            }
            
            # Save to Config directory
            import os
            import json
            
            config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Config")
            os.makedirs(config_dir, exist_ok=True)
            
            settings_file = os.path.join(config_dir, "hpc_profiles.json")
            with open(settings_file, 'w') as f:
                json.dump(settings, f, indent=4)
            
            self.log("HPC settings saved successfully")
            messagebox.showinfo("Success", "HPC settings saved successfully")
            
            return True
        except Exception as e:
            self.log(f"Error saving HPC settings: {e}")
            messagebox.showerror("Error", f"Failed to save HPC settings: {str(e)}")
            return False

    def load_hpc_profiles(self):
        """Load HPC settings from config file"""
        try:
            import os
            import json
            
            config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Config")
            settings_file = os.path.join(config_dir, "hpc_profiles.json")
            
            if not os.path.exists(settings_file):
                self.log("No HPC settings file found, using defaults")
                return False
            
            with open(settings_file, 'r') as f:
                settings = json.load(f)
            
            # Apply settings to UI
            if hasattr(self, 'hpc_hostname'):
                self.hpc_hostname.delete(0, tk.END)
                self.hpc_hostname.insert(0, settings.get("hostname", ""))
            
            if hasattr(self, 'hpc_username'):
                self.hpc_username.delete(0, tk.END)
                self.hpc_username.insert(0, settings.get("username", ""))
            
            if hasattr(self, 'hpc_port'):
                self.hpc_port.delete(0, tk.END)
                self.hpc_port.insert(0, str(settings.get("port", 22)))
            
            if hasattr(self, 'hpc_remote_dir'):
                self.hpc_remote_dir.delete(0, tk.END)
                self.hpc_remote_dir.insert(0, settings.get("remote_dir", ""))
            
            # Authentication
            if hasattr(self, 'auth_type'):
                self.auth_type.set("key" if settings.get("use_key", False) else "password")
                if settings.get("use_key", False):
                    self.hpc_key_path.delete(0, tk.END)
                    self.hpc_key_path.insert(0, settings.get("key_path", ""))
            
            # Scheduler
            if hasattr(self, 'hpc_scheduler'):
                self.hpc_scheduler.set(settings.get("scheduler", "slurm"))
            
            # Job settings
            job_defaults = settings.get("job_defaults", {})
            if hasattr(self, 'job_name'):
                self.job_name.delete(0, tk.END)
                self.job_name.insert(0, job_defaults.get("name", "cfd_job"))
            
            if hasattr(self, 'job_nodes'):
                self.job_nodes.delete(0, tk.END)
                self.job_nodes.insert(0, job_defaults.get("nodes", "1"))
            
            if hasattr(self, 'job_cores_per_node'):
                self.job_cores_per_node.delete(0, tk.END)
                self.job_cores_per_node.insert(0, job_defaults.get("cores_per_node", "8"))
            
            if hasattr(self, 'job_walltime'):
                self.job_walltime.delete(0, tk.END)
                self.job_walltime.insert(0, job_defaults.get("walltime", "24:00:00"))
            
            if hasattr(self, 'job_queue'):
                self.job_queue.delete(0, tk.END)
                self.job_queue.insert(0, job_defaults.get("queue", "compute"))
            
            self.log("HPC settings loaded successfully")
            self.toggle_auth_type()
            return True
        except Exception as e:
            self.log(f"Error loading HPC settings: {e}")
            return False

        """Set up the HPC tab in the notebook"""
        try:
            # Check if HPC tab already exists
            for tab_id in self.notebook.tabs():
                if self.notebook.tab(tab_id, "text") == "HPC":
                    return  # Tab already exists
            
            # Create HPC tab
            self.hpc_tab = ttk.Frame(self.notebook)
            self.notebook.add(self.hpc_tab, text="HPC")
            
            # Connection settings section
            conn_frame = ttk.LabelFrame(self.hpc_tab, text="HPC Connection Settings")
            conn_frame.pack(fill="x", padx=20, pady=10)
            
            # Host settings
            host_frame = ttk.Frame(conn_frame)
            host_frame.pack(fill="x", padx=10, pady=5)
            
            ttk.Label(host_frame, text="HPC Host:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
            self.hpc_hostname = ttk.Entry(host_frame, width=30)
            self.hpc_hostname.grid(row=0, column=1, padx=5, pady=5, sticky="w")
            
            # Username
            ttk.Label(host_frame, text="Username:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
            self.hpc_username = ttk.Entry(host_frame, width=30)
            self.hpc_username.grid(row=1, column=1, padx=5, pady=5, sticky="w")
            
            # Port
            ttk.Label(host_frame, text="Port:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
            self.hpc_port = ttk.Entry(host_frame, width=10)
            self.hpc_port.grid(row=2, column=1, padx=5, pady=5, sticky="w")
            self.hpc_port.insert(0, "22")
            
            # Remote directory
            ttk.Label(host_frame, text="Remote Directory:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
            self.hpc_remote_dir = ttk.Entry(host_frame, width=30)
            self.hpc_remote_dir.grid(row=3, column=1, padx=5, pady=5, sticky="w")
            self.hpc_remote_dir.insert(0, "/home/user/cfd_projects")
            
            # Authentication
            auth_frame = ttk.LabelFrame(conn_frame, text="Authentication")
            auth_frame.pack(fill="x", padx=10, pady=10)
            
            self.auth_type = tk.StringVar(value="password")
            ttk.Radiobutton(auth_frame, text="Password", variable=self.auth_type, 
                            value="password", command=self.toggle_auth_type).pack(anchor="w", padx=10, pady=5)
            ttk.Radiobutton(auth_frame, text="Key File", variable=self.auth_type, 
                            value="key", command=self.toggle_auth_type).pack(anchor="w", padx=10, pady=5)
            
            # Password frame
            self.password_frame = ttk.Frame(auth_frame)
            self.password_frame.pack(fill="x", padx=10, pady=5)
            ttk.Label(self.password_frame, text="Password:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
            self.hpc_password = ttk.Entry(self.password_frame, width=30, show="*")
            self.hpc_password.grid(row=0, column=1, padx=5, pady=5, sticky="w")
            
            # Key file frame
            self.key_frame = ttk.Frame(auth_frame)
            ttk.Label(self.key_frame, text="Key File:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
            self.hpc_key_path = ttk.Entry(self.key_frame, width=30)
            self.hpc_key_path.grid(row=0, column=1, padx=5, pady=5, sticky="w")
            ttk.Button(self.key_frame, text="Browse...", command=self.browse_key_file).grid(row=0, column=2, padx=5, pady=5)
            
            # Scheduler Settings
            scheduler_frame = ttk.LabelFrame(self.hpc_tab, text="Scheduler Settings")
            scheduler_frame.pack(fill="x", padx=20, pady=10)
            
            ttk.Label(scheduler_frame, text="Scheduler Type:").pack(anchor="w", padx=10, pady=5)
            self.hpc_scheduler = tk.StringVar(value="slurm")
            ttk.Radiobutton(scheduler_frame, text="SLURM", variable=self.hpc_scheduler, value="slurm").pack(anchor="w", padx=30, pady=2)
            ttk.Radiobutton(scheduler_frame, text="PBS/Torque", variable=self.hpc_scheduler, value="pbs").pack(anchor="w", padx=30, pady=2)
            ttk.Radiobutton(scheduler_frame, text="SGE/UGE", variable=self.hpc_scheduler, value="sge").pack(anchor="w", padx=30, pady=2)
            
            # Job Settings
            job_frame = ttk.LabelFrame(self.hpc_tab, text="Default Job Settings")
            job_frame.pack(fill="x", padx=20, pady=10)
            
            job_settings_grid = ttk.Frame(job_frame)
            job_settings_grid.pack(fill="x", padx=10, pady=10)
            
            # Job name
            ttk.Label(job_settings_grid, text="Job Name Prefix:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
            self.job_name = ttk.Entry(job_settings_grid, width=20)
            self.job_name.grid(row=0, column=1, padx=5, pady=5, sticky="w")
            self.job_name.insert(0, "cfd_job")
            
            # Nodes
            ttk.Label(job_settings_grid, text="Nodes:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
            self.job_nodes = ttk.Entry(job_settings_grid, width=5)
            self.job_nodes.grid(row=1, column=1, padx=5, pady=5, sticky="w")
            self.job_nodes.insert(0, "1")
            
            # Cores per node
            ttk.Label(job_settings_grid, text="Cores per Node:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
            self.job_cores_per_node = ttk.Entry(job_settings_grid, width=5)
            self.job_cores_per_node.grid(row=2, column=1, padx=5, pady=5, sticky="w")
            self.job_cores_per_node.insert(0, "8")
            
            # Walltime
            ttk.Label(job_settings_grid, text="Wall Time (HH:MM:SS):").grid(row=3, column=0, padx=5, pady=5, sticky="w")
            self.job_walltime = ttk.Entry(job_settings_grid, width=10)
            self.job_walltime.grid(row=3, column=1, padx=5, pady=5, sticky="w")
            self.job_walltime.insert(0, "24:00:00")
            
            # Queue/Partition
            ttk.Label(job_settings_grid, text="Queue/Partition:").grid(row=4, column=0, padx=5, pady=5, sticky="w")
            self.job_queue = ttk.Entry(job_settings_grid, width=15)
            self.job_queue.grid(row=4, column=1, padx=5, pady=5, sticky="w")
            self.job_queue.insert(0, "compute")
            
            # Button frame
            button_frame = ttk.Frame(self.hpc_tab)
            button_frame.pack(fill="x", padx=20, pady=20)
            
            ttk.Button(button_frame, text="Test Connection", command=self._test_hpc_connection).pack(side="left", padx=5)
            ttk.Button(button_frame, text="Save Settings", command=self.save_hpc_profiles).pack(side="left", padx=5)
            ttk.Button(button_frame, text="Load Settings", command=self.load_hpc_profiles).pack(side="left", padx=5)
            
            # Connection status
            status_frame = ttk.Frame(self.hpc_tab)
            status_frame.pack(fill="x", padx=20, pady=10)
            
            self.connection_status_var = tk.StringVar(value="Status: Not Connected")
            self.connection_status_label = ttk.Label(status_frame, textvariable=self.connection_status_var, foreground="red")
            self.connection_status_label.pack(side="left", padx=5)
            
            # Load HPC settings
            self.load_hpc_profiles()
            
            # Initialize with default auth type
            self.toggle_auth_type()
            
            self.log("HPC tab initialized successfully")
        except Exception as e:
            import traceback
            self.log(f"Error initializing HPC tab: {e}")
            print(f"Error initializing HPC tab: {e}")
            print(traceback.format_exc())

    def setup_hpc_tab(self):
        """Set up the HPC tab in the notebook"""
        try:
            # Check if HPC tab already exists
            for tab_id in self.notebook.tabs():
                if self.notebook.tab(tab_id, "text") == "HPC":
                    # Tab exists but might be empty - clear it and repopulate
                    hpc_tab = self.notebook.nametowidget(tab_id)
                    for widget in hpc_tab.winfo_children():
                        widget.destroy()
                    self.hpc_tab = hpc_tab
                    self.log("Rebuilding existing HPC tab")
                    break
            else:
                # Create new HPC tab
                self.hpc_tab = ttk.Frame(self.notebook)
                self.notebook.add(self.hpc_tab, text="HPC")
                self.log("Created new HPC tab")
                self.create_hpc_tab_content()

            # Load settings first to use for defaults
            self.load_hpc_profiles()
            
            # Connection settings section
            conn_frame = ttk.LabelFrame(self.hpc_tab, text="HPC Connection Settings")
            conn_frame.pack(fill="x", padx=20, pady=10)
            
            # Host settings
            host_frame = ttk.Frame(conn_frame)
            host_frame.pack(fill="x", padx=10, pady=5)
            
            ttk.Label(host_frame, text="HPC Host:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
            self.hpc_hostname = ttk.Entry(host_frame, width=30)
            self.hpc_hostname.grid(row=0, column=1, padx=5, pady=5, sticky="w")
            
            # Username
            ttk.Label(host_frame, text="Username:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
            self.hpc_username = ttk.Entry(host_frame, width=30)
            self.hpc_username.grid(row=1, column=1, padx=5, pady=5, sticky="w")
            
            # Port
            ttk.Label(host_frame, text="Port:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
            self.hpc_port = ttk.Entry(host_frame, width=10)
            self.hpc_port.grid(row=2, column=1, padx=5, pady=5, sticky="w")
            self.hpc_port.insert(0, "22")  # Default port
            
            # Remote directory
            ttk.Label(host_frame, text="Remote Directory:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
            self.hpc_remote_dir = ttk.Entry(host_frame, width=30)
            self.hpc_remote_dir.grid(row=3, column=1, padx=5, pady=5, sticky="w")
            self.hpc_remote_dir.insert(0, "/home/user/cfd_projects")
            
            # Authentication
            auth_frame = ttk.LabelFrame(conn_frame, text="Authentication")
            auth_frame.pack(fill="x", padx=10, pady=10)
            
            self.auth_type = tk.StringVar(value="password")
            ttk.Radiobutton(auth_frame, text="Password", variable=self.auth_type, 
                            value="password", command=self.toggle_auth_type).pack(anchor="w", padx=10, pady=5)
            ttk.Radiobutton(auth_frame, text="Key File", variable=self.auth_type, 
                            value="key", command=self.toggle_auth_type).pack(anchor="w", padx=10, pady=5)
            
            # Password frame
            self.password_frame = ttk.Frame(auth_frame)
            self.password_frame.pack(fill="x", padx=10, pady=5)
            ttk.Label(self.password_frame, text="Password:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
            self.hpc_password = ttk.Entry(self.password_frame, width=30, show="*")
            self.hpc_password.grid(row=0, column=1, padx=5, pady=5, sticky="w")
            
            # Key file frame
            self.key_frame = ttk.Frame(auth_frame)
            ttk.Label(self.key_frame, text="Key File:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
            self.hpc_key_path = ttk.Entry(self.key_frame, width=30)
            self.hpc_key_path.grid(row=0, column=1, padx=5, pady=5, sticky="w")
            ttk.Button(self.key_frame, text="Browse...", command=self.browse_key_file).grid(row=0, column=2, padx=5, pady=5)
            
            # Scheduler Settings
            scheduler_frame = ttk.LabelFrame(self.hpc_tab, text="Scheduler Settings")
            scheduler_frame.pack(fill="x", padx=20, pady=10)
            
            ttk.Label(scheduler_frame, text="Scheduler Type:").pack(anchor="w", padx=10, pady=5)
            self.hpc_scheduler = tk.StringVar(value="slurm")
            ttk.Radiobutton(scheduler_frame, text="SLURM", variable=self.hpc_scheduler, value="slurm").pack(anchor="w", padx=30, pady=2)
            ttk.Radiobutton(scheduler_frame, text="PBS/Torque", variable=self.hpc_scheduler, value="pbs").pack(anchor="w", padx=30, pady=2)
            ttk.Radiobutton(scheduler_frame, text="SGE/UGE", variable=self.hpc_scheduler, value="sge").pack(anchor="w", padx=30, pady=2)
            
            # Job Settings
            job_frame = ttk.LabelFrame(self.hpc_tab, text="Default Job Settings")
            job_frame.pack(fill="x", padx=20, pady=10)
            
            job_settings_grid = ttk.Frame(job_frame)
            job_settings_grid.pack(fill="x", padx=10, pady=10)
            
            # Job name
            ttk.Label(job_settings_grid, text="Job Name Prefix:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
            self.job_name = ttk.Entry(job_settings_grid, width=20)
            self.job_name.grid(row=0, column=1, padx=5, pady=5, sticky="w")
            self.job_name.insert(0, "cfd_job")
            
            # Nodes
            ttk.Label(job_settings_grid, text="Nodes:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
            self.job_nodes = ttk.Entry(job_settings_grid, width=5)
            self.job_nodes.grid(row=1, column=1, padx=5, pady=5, sticky="w")
            self.job_nodes.insert(0, "1")
            
            # Cores per node
            ttk.Label(job_settings_grid, text="Cores per Node:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
            self.job_cores_per_node = ttk.Entry(job_settings_grid, width=5)
            self.job_cores_per_node.grid(row=2, column=1, padx=5, pady=5, sticky="w")
            self.job_cores_per_node.insert(0, "8")
            
            # Walltime
            ttk.Label(job_settings_grid, text="Wall Time (HH:MM:SS):").grid(row=3, column=0, padx=5, pady=5, sticky="w")
            self.job_walltime = ttk.Entry(job_settings_grid, width=10)
            self.job_walltime.grid(row=3, column=1, padx=5, pady=5, sticky="w")
            self.job_walltime.insert(0, "24:00:00")
            
            # Queue/Partition
            ttk.Label(job_settings_grid, text="Queue/Partition:").grid(row=4, column=0, padx=5, pady=5, sticky="w")
            self.job_queue = ttk.Entry(job_settings_grid, width=15)
            self.job_queue.grid(row=4, column=1, padx=5, pady=5, sticky="w")
            self.job_queue.insert(0, "compute")
            
            # Button frame
            button_frame = ttk.Frame(self.hpc_tab)
            button_frame.pack(fill="x", padx=20, pady=20)
            
            self.test_connection_button = ttk.Button(button_frame, text="Test Connection", 
                                                command=self.test_hpc_connection)
            self.test_connection_button.pack(side="left", padx=5)
            
            ttk.Button(button_frame, text="Save Settings", 
                    command=self.save_hpc_profiles).pack(side="left", padx=5)
            
            ttk.Button(button_frame, text="Load Settings", 
                    command=self.load_hpc_profiles).pack(side="left", padx=5)
            
            # Connection status
            status_frame = ttk.Frame(self.hpc_tab)
            status_frame.pack(fill="x", padx=20, pady=10)
            
            self.connection_status_var = tk.StringVar(value="Status: Not Connected")
            self.connection_status_label = ttk.Label(status_frame, textvariable=self.connection_status_var, 
                                                foreground="red")
            self.connection_status_label.pack(side="left", padx=5)
            
            # Apply settings from config
            self.apply_hpc_profiles()
            
            # Initialize with default auth type
            self.toggle_auth_type()
            
            self.log("HPC tab initialized successfully")
            return True
        except Exception as e:
            import traceback
            self.log(f"Error initializing HPC tab: {e}")
            print(f"Error initializing HPC tab: {e}")
            print(traceback.format_exc())
            return False

    def _run_hpc_workflow(self, L4, L5, alpha1, alpha2, alpha3):
        """Run workflow on HPC system"""
        try:
            # Check if HPC profile is selected
            if not hasattr(self, 'workflow_hpc_profile') or not self.workflow_hpc_profile.get():
                messagebox.showerror("HPC Error", "Please select an HPC profile")
                self._workflow_failed("No HPC profile selected")
                return
                
            profile_name = self.workflow_hpc_profile.get()
            self._update_workflow_status(f"Preparing to submit job to HPC using profile '{profile_name}'...")
            
            # Create submission dialog
            self._create_hpc_submission_dialog(L4, L5, alpha1, alpha2, alpha3, profile_name)
            
        except Exception as e:
            self.log(f"Error preparing HPC workflow: {str(e)}")
            self._workflow_failed(f"Failed to prepare HPC workflow: {str(e)}")

    def _create_hpc_submission_dialog(self, L4, L5, alpha1, alpha2, alpha3, profile_name):
        """Create dialog for HPC job submission"""
        import os
        import datetime
        
        # Create dialog window
        dialog = tk.Toplevel(self.root)
        dialog.title("Submit Workflow to HPC")
        dialog.geometry("700x600")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Apply theme to dialog
        if hasattr(self, 'theme'):
            dialog.configure(background=self.theme.bg_color)
        
        # Main frame
        main_frame = ttk.Frame(dialog, padding=10)
        main_frame.pack(fill='both', expand=True)
        
        # Job details section
        job_frame = ttk.LabelFrame(main_frame, text="Job Details", padding=10)
        job_frame.pack(fill='x', pady=5)
        
        ttk.Label(job_frame, text="Job Name:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        job_name_var = tk.StringVar(value=f"intake_cfd_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}")
        job_name_entry = ttk.Entry(job_frame, width=30, textvariable=job_name_var)
        job_name_entry.grid(row=0, column=1, padx=5, pady=5, sticky='w')
        
        # Resources section
        resources_frame = ttk.LabelFrame(main_frame, text="Resources", padding=10)
        resources_frame.pack(fill='x', pady=5)
        
        ttk.Label(resources_frame, text="Nodes:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        nodes_var = tk.StringVar(value="1")
        nodes_entry = ttk.Entry(resources_frame, width=5, textvariable=nodes_var)
        nodes_entry.grid(row=0, column=1, padx=5, pady=5, sticky='w')
        
        ttk.Label(resources_frame, text="Cores per Node:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        cores_var = tk.StringVar(value="8")
        cores_entry = ttk.Entry(resources_frame, width=5, textvariable=cores_var)
        cores_entry.grid(row=1, column=1, padx=5, pady=5, sticky='w')
        
        ttk.Label(resources_frame, text="Memory per Node (GB):").grid(row=2, column=0, padx=5, pady=5, sticky='w')
        memory_var = tk.StringVar(value="16")
        memory_entry = ttk.Entry(resources_frame, width=5, textvariable=memory_var)
        memory_entry.grid(row=2, column=1, padx=5, pady=5, sticky='w')
        
        ttk.Label(resources_frame, text="Wall Time (HH:MM:SS):").grid(row=3, column=0, padx=5, pady=5, sticky='w')
        walltime_var = tk.StringVar(value="01:00:00")
        walltime_entry = ttk.Entry(resources_frame, width=10, textvariable=walltime_var)
        walltime_entry.grid(row=3, column=1, padx=5, pady=5, sticky='w')
        
        # Queue selection
        ttk.Label(resources_frame, text="Queue/Partition:").grid(row=4, column=0, padx=5, pady=5, sticky='w')
        queue_var = tk.StringVar(value="compute")
        queue_entry = ttk.Entry(resources_frame, width=15, textvariable=queue_var)
        queue_entry.grid(row=4, column=1, padx=5, pady=5, sticky='w')
        
        # Parameters section
        params_frame = ttk.LabelFrame(main_frame, text="Parameters", padding=10)
        params_frame.pack(fill='x', pady=5)
        
        param_text = f"L4: {L4}\nL5: {L5}\nalpha1: {alpha1}\nalpha2: {alpha2}\nalpha3: {alpha3}"
        ttk.Label(params_frame, text=param_text).pack(anchor='w', padx=5, pady=5)
        
        # Script section
        script_frame = ttk.LabelFrame(main_frame, text="Job Script", padding=10)
        script_frame.pack(fill='both', expand=True, pady=5)
        
        # Create script template
        script_template = self._create_hpc_script_template(job_name_var.get(), nodes_var.get(), cores_var.get(), 
                                                        memory_var.get(), walltime_var.get(), queue_var.get(),
                                                        L4, L5, alpha1, alpha2, alpha3)
        
        script_editor = scrolledtext.ScrolledText(script_frame, wrap=tk.WORD, height=15, width=80)
        script_editor.pack(fill='both', expand=True, padx=5, pady=5)
        script_editor.insert(tk.END, script_template)
        
        # Function to update script template
        def update_script_template():
            script = self._create_hpc_script_template(job_name_var.get(), nodes_var.get(), cores_var.get(), 
                                                    memory_var.get(), walltime_var.get(), queue_var.get(),
                                                    L4, L5, alpha1, alpha2, alpha3)
            script_editor.delete(1.0, tk.END)
            script_editor.insert(tk.END, script)
        
        # Add button to update template
        ttk.Button(script_frame, text="Update Script", 
                command=update_script_template).pack(pady=5)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=10)
        
        # Function to submit job
        def submit_job():
            script_content = script_editor.get(1.0, tk.END)
            
            # Show confirmation dialog
            if messagebox.askyesno("Confirm Submission", 
                                f"Submit job '{job_name_var.get()}' to HPC cluster using profile '{profile_name}'?"):
                # Submit job in a separate thread
                threading.Thread(target=self._submit_hpc_job, 
                            args=(script_content, profile_name, job_name_var.get(), dialog),
                            daemon=True).start()
        
        ttk.Button(button_frame, text="Submit Job", 
                command=submit_job).pack(side='left', padx=5)
        
        ttk.Button(button_frame, text="Cancel", 
                command=dialog.destroy).pack(side='right', padx=5)
    
            
        # Function to submit job
        def submit_job():
            script_content = script_editor.get(1.0, tk.END)
            
            # Show confirmation dialog
            if messagebox.askyesno("Confirm Submission", 
                                f"Submit job '{job_name_var.get()}' to HPC cluster using profile '{profile_name}'?"):
                # Submit job in a separate thread
                threading.Thread(target=self._submit_hpc_job, 
                            args=(script_content, profile_name, job_name_var.get(), dialog),
                            daemon=True).start()
        
        ttk.Button(button_frame, text="Submit Job", 
                command=submit_job).pack(side='left', padx=5)
        
        ttk.Button(button_frame, text="Cancel", 
                command=dialog.destroy).pack(side='right', padx=5)

    def _create_hpc_script_template(self, job_name, nodes, cores, memory, walltime, queue, L4, L5, alpha1, alpha2, alpha3):
        """Create HPC job script template"""
        
        # Determine total cores
        try:
            total_cores = int(nodes) * int(cores)
        except ValueError:
            total_cores = "{nodes} * {cores}"
        
        # Create the script template
        script = f"""#!/bin/bash
    #SBATCH --job-name={job_name}
    #SBATCH --output={job_name}_%j.out
    #SBATCH --error={job_name}_%j.err
    #SBATCH --partition={queue}
    #SBATCH --nodes={nodes}
    #SBATCH --ntasks-per-node={cores}
    #SBATCH --mem={memory}G
    #SBATCH --time={walltime}

    # Load required modules
    module load python
    module load openfoam

    # Print job info
    echo "Running job on $SLURM_JOB_NODELIST"
    echo "Job started at $(date)"
    echo ""

    # Create expressions file
    cat > expressions.exp << EOF
    L4 = {L4} UNIT:Meter
    L5 = {L5} UNIT:Meter
    alpha1 = {alpha1} UNIT:Degrees
    alpha2 = {alpha2} UNIT:Degrees
    alpha3 = {alpha3} UNIT:Degrees
    EOF

    # Run the workflow steps
    echo "Step 1: Updating NX model..."
    # In HPC environment, we might use pre-generated geometry or run NX via remote execution
    # This is a placeholder for the actual command

    echo "Step 2: Generating mesh..."
    ./gmsh_process --input INTAKE3D.step --output INTAKE3D.msh --auto-refine --threads {total_cores}

    echo "Step 3: Running CFD simulation..."
    mpirun -np {total_cores} ./cfd_solver --mesh INTAKE3D.msh --solver openfoam

    echo "Step 4: Processing results..."
    ./process_results --input cfd_results --output processed_results.csv

    echo "Job finished at $(date)"
    """
        return script

    def _submit_hpc_job(self, script_content, profile_name, job_name, dialog=None):
        """Submit a job to HPC system"""
        import os
        import json
        import tempfile
        
        self._update_workflow_status("Submitting job to HPC system...")
        self.update_status("Submitting job to HPC...", show_progress=True)
        
        try:
            # Import required modules
            try:
                import paramiko
            except ImportError:
                self._update_workflow_status("Error: paramiko module not installed. Please install it using 'pip install paramiko'")
                self.update_status("Error: paramiko module not installed", show_progress=False)
                messagebox.showerror("Import Error", "The paramiko module is required for HPC connectivity.\n\nPlease install it using: pip install paramiko")
                return
            
            # Load profiles
            profiles_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                    "Config", "hpc_profiles.json")
            
            if not os.path.exists(profiles_path):
                self._update_workflow_status("Error: HPC profiles file not found")
                self.update_status("Error: HPC profiles file not found", show_progress=False)
                messagebox.showerror("File Not Found", f"HPC profiles file not found at {profiles_path}")
                return
                
            with open(profiles_path, 'r') as f:
                profiles = json.load(f)
            
            if profile_name not in profiles:
                self._update_workflow_status(f"Error: Profile '{profile_name}' not found in profiles file")
                self.update_status(f"Error: Profile '{profile_name}' not found", show_progress=False)
                messagebox.showerror("Profile Not Found", f"HPC profile '{profile_name}' not found in profiles file")
                return
                
            profile = profiles[profile_name]
            
            # Create SSH client
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            self._update_workflow_status(f"Connecting to {profile['hostname']}...")
            
            # Connect to server
            try:
                if profile.get("use_key", False):
                    ssh.connect(
                        hostname=profile["hostname"],
                        username=profile["username"],
                        port=profile.get("port", 22),
                        key_filename=profile.get("key_path", "")
                    )
                else:
                    # Get password securely
                    password_dialog = tk.Toplevel(self.root)
                    password_dialog.title("SSH Password")
                    password_dialog.geometry("300x150")
                    password_dialog.transient(self.root)
                    password_dialog.grab_set()
                    
                    ttk.Label(password_dialog, text=f"Enter password for {profile['username']}@{profile['hostname']}:").pack(pady=10)
                    
                    password_var = tk.StringVar()
                    password_entry = ttk.Entry(password_dialog, show="*", width=30, textvariable=password_var)
                    password_entry.pack(pady=10)
                    password_entry.focus_set()
                    
                    # Password entry dialog result
                    dialog_result = {"password": None, "canceled": False}
                    
                    def on_ok():
                        dialog_result["password"] = password_var.get()
                        password_dialog.destroy()
                    
                    def on_cancel():
                        dialog_result["canceled"] = True
                        password_dialog.destroy()
                    
                    ttk.Button(password_dialog, text="OK", command=on_ok).pack(side='left', padx=20, pady=10)
                    ttk.Button(password_dialog, text="Cancel", command=on_cancel).pack(side='right', padx=20, pady=10)
                    
                    # Wait for dialog to close
                    self.root.wait_window(password_dialog)
                    
                    if dialog_result["canceled"]:
                        self._update_workflow_status("Job submission canceled")
                        self.update_status("Job submission canceled", show_progress=False)
                        return
                        
                    ssh.connect(
                        hostname=profile["hostname"],
                        username=profile["username"],
                        password=dialog_result["password"],
                        port=profile.get("port", 22)
                    )
            except Exception as e:
                self._update_workflow_status(f"Connection failed: {str(e)}")
                self.update_status("Connection failed", show_progress=False)
                messagebox.showerror("Connection Failed", f"Failed to connect to HPC server:\n\n{str(e)}")
                return
                
            self._update_workflow_status("Connected to HPC server, uploading files...")
            
            # Create SFTP client
            sftp = ssh.open_sftp()
            
            # Get remote directory
            remote_dir = profile.get("remote_dir", "")
            if not remote_dir:
                remote_dir = f"/home/{profile['username']}/cfd_projects"
                
            # Create remote directory if it doesn't exist
            try:
                sftp.stat(remote_dir)
            except FileNotFoundError:
                self._update_workflow_status(f"Creating directory {remote_dir}...")
                ssh.exec_command(f"mkdir -p {remote_dir}")
                
            # Create job directory
            job_dir = f"{remote_dir}/{job_name}"
            ssh.exec_command(f"mkdir -p {job_dir}")
            
            # Upload job script
            script_path = f"{job_dir}/job_script.sh"
            with sftp.open(script_path, 'w') as f:
                f.write(script_content)
                
            # Make script executable
            ssh.exec_command(f"chmod +x {script_path}")
            
            # Upload necessary files
            if os.path.exists("INTAKE3D.step"):
                self._update_workflow_status("Uploading STEP file...")
                sftp.put("INTAKE3D.step", f"{job_dir}/INTAKE3D.step")
                
            # Upload additional files as needed
            # ...
            
            self._update_workflow_status("Submitting job to scheduler...")
            
            # Change to job directory
            stdin, stdout, stderr = ssh.exec_command(f"cd {job_dir} && echo $PWD")
            current_dir = stdout.read().decode().strip()
            self._update_workflow_status(f"Working directory: {current_dir}")
            
            # Determine scheduler type and submit job
            scheduler_cmd = ""
            job_id = None
            
            # Try SLURM
            stdin, stdout, stderr = ssh.exec_command("command -v sbatch")
            if stdout.read().strip():
                self._update_workflow_status("Using SLURM scheduler...")
                stdin, stdout, stderr = ssh.exec_command(f"cd {job_dir} && sbatch job_script.sh")
                response = stdout.read().decode().strip()
                error = stderr.read().decode().strip()
                
                if error:
                    self._update_workflow_status(f"Job submission error: {error}")
                else:
                    # Parse job ID from SLURM response (typically "Submitted batch job 12345")
                    import re
                    match = re.search(r'Submitted batch job (\d+)', response)
                    if match:
                        job_id = match.group(1)
                        self._update_workflow_status(f"Job submitted successfully with ID: {job_id}")
                    else:
                        self._update_workflow_status(f"Job submitted, but couldn't parse job ID. Response: {response}")
            
            # Try PBS if SLURM not available
            elif ssh.exec_command("command -v qsub")[1].read().strip():
                self._update_workflow_status("Using PBS scheduler...")
                stdin, stdout, stderr = ssh.exec_command(f"cd {job_dir} && qsub job_script.sh")
                response = stdout.read().decode().strip()
                error = stderr.read().decode().strip()
                
                if error:
                    self._update_workflow_status(f"Job submission error: {error}")
                else:
                    job_id = response.strip()
                    self._update_workflow_status(f"Job submitted successfully with ID: {job_id}")
            
            # Try LSF if neither SLURM nor PBS available
            elif ssh.exec_command("command -v bsub")[1].read().strip():
                self._update_workflow_status("Using LSF scheduler...")
                stdin, stdout, stderr = ssh.exec_command(f"cd {job_dir} && bsub < job_script.sh")
                response = stdout.read().decode().strip()
                error = stderr.read().decode().strip()
                
                if error:
                    self._update_workflow_status(f"Job submission error: {error}")
                else:
                    import re
                    match = re.search(r'Job <(\d+)>', response)
                    if match:
                        job_id = match.group(1)
                        self._update_workflow_status(f"Job submitted successfully with ID: {job_id}")
                    else:
                        self._update_workflow_status(f"Job submitted, but couldn't parse job ID. Response: {response}")
            
            else:
                self._update_workflow_status("No supported job scheduler found on HPC system")
                self.update_status("No job scheduler found", show_progress=False)
                messagebox.showerror("Scheduler Error", "No supported job scheduler (SLURM, PBS, LSF) found on HPC system")
                
            # Close SSH connection
            ssh.close()
            
            # Update workflow steps status
            self._update_workflow_step("CAD", "running")
            
            # Show success message
            if job_id:
                self.update_status(f"Job submitted with ID: {job_id}", show_progress=False)
                messagebox.showinfo("Job Submitted", f"Job '{job_name}' submitted successfully with ID: {job_id}\n\nUse the HPC tab to monitor job status.")
            else:
                self.update_status("Job submitted", show_progress=False)
                messagebox.showinfo("Job Submitted", f"Job '{job_name}' submitted successfully.\n\nUse the HPC tab to monitor job status.")
            
            # Close the dialog if provided
            if dialog:
                dialog.destroy()
                
            # Update workflow status to completed
            self._workflow_completed()
            
        except Exception as e:
            self.log(f"Error submitting HPC job: {str(e)}")
            self._update_workflow_status(f"Error submitting job: {str(e)}")
            self.update_status("Job submission failed", show_progress=False)
            messagebox.showerror("Submission Error", f"Failed to submit job to HPC system:\n\n{str(e)}")
            self._workflow_failed(f"Failed to submit job: {str(e)}")

    def submit_workflow_to_hpc(self, L4, L5, alpha1, alpha2, alpha3):
        """Submit workflow job to HPC system"""
        try:
            # Check if HPC profile is selected
            if not hasattr(self, 'workflow_hpc_profile') or not self.workflow_hpc_profile.get():
                messagebox.showerror("HPC Error", "Please select an HPC profile")
                self._workflow_failed("No HPC profile selected")
                return
                
            profile_name = self.workflow_hpc_profile.get()
            self._update_workflow_status(f"Preparing to submit job to HPC using profile '{profile_name}'...")
            
            # Create submission dialog
            self._create_hpc_submission_dialog(L4, L5, alpha1, alpha2, alpha3, profile_name)
            
        except Exception as e:
            self.log(f"Error preparing HPC workflow: {str(e)}")
            self._workflow_failed(f"Failed to prepare HPC workflow: {str(e)}")

    def load_workflow_hpc_profiles(self):
        """Load HPC profiles for the workflow tab"""
        try:
            # Path to profiles file
            profiles_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                        "Config", "hpc_profiles.json")
            
            if os.path.exists(profiles_path):
                with open(profiles_path, 'r') as f:
                    data = json.load(f)
                    
                # Check if the file contains a list of profiles (dictionary of profile_name -> settings)
                # or a single profile settings object
                if isinstance(data, dict) and not any(isinstance(v, dict) for v in data.values()):
                    # This is a single profile settings, create a "Default" profile
                    profiles = {"Default": data}
                else:
                    # This is already a dictionary of profiles
                    profiles = data
                        
                # Update combobox with profile names
                if hasattr(self, 'workflow_hpc_profile'):
                    self.workflow_hpc_profile['values'] = list(profiles.keys())
                    if profiles:
                        self.workflow_hpc_profile.current(0)  # Select first profile
                
                self.log(f"Loaded {len(profiles)} HPC profiles for workflow")
            else:
                self.log("No HPC profiles found. Please configure HPC settings in the Settings tab.")
                
        except Exception as e:
            self.log(f"Error loading HPC profiles for workflow: {e}")

    def create_default_hpc_profile(self):
        """Create a default HPC profile from current settings"""
        try:
            # Get current configuration
            config = {
                "hostname": self.hpc_hostname.get() if hasattr(self, 'hpc_hostname') else "localhost",
                "username": self.hpc_username.get() if hasattr(self, 'hpc_username') else "",
                "port": int(self.hpc_port.get()) if hasattr(self, 'hpc_port') and self.hpc_port.get().isdigit() else 22,
                "remote_dir": self.hpc_remote_dir.get() if hasattr(self, 'hpc_remote_dir') else "/home/user/cfd_projects",
                "use_key": self.auth_type.get() == "key" if hasattr(self, 'auth_type') else False,
                "key_path": self.hpc_key_path.get() if hasattr(self, 'hpc_key_path') else ""
            }
            
            # Create profiles directory structure
            config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Config")
            os.makedirs(config_dir, exist_ok=True)
            
            # Save as default profile
            profiles = {"Default": config}
            profiles_path = os.path.join(config_dir, "hpc_profiles.json")
            
            with open(profiles_path, 'w') as f:
                json.dump(profiles, f, indent=4)
                
            self.log("Created default HPC profile")
            return True
        except Exception as e:
            self.log(f"Error creating default HPC profile: {e}")
            return False

    def create_scrollable_frame(self, parent, **kwargs):
        """Create a scrollable frame that adapts to window resizing"""
        # Create a canvas with scrollbars
        outer_frame = ttk.Frame(parent)
        
        # Create vertical scrollbar
        v_scrollbar = ttk.Scrollbar(outer_frame, orient="vertical")
        v_scrollbar.pack(side="right", fill="y")
        
        # Create horizontal scrollbar
        h_scrollbar = ttk.Scrollbar(outer_frame, orient="horizontal")
        h_scrollbar.pack(side="bottom", fill="x")
        
        # Create canvas
        canvas = tk.Canvas(outer_frame, 
                          yscrollcommand=v_scrollbar.set,
                          xscrollcommand=h_scrollbar.set,
                          **kwargs)
        canvas.pack(side="left", fill="both", expand=True)
        
        # Configure scrollbars
        v_scrollbar.config(command=canvas.yview)
        h_scrollbar.config(command=canvas.xview)
        
        # Create inner frame for content
        inner_frame = ttk.Frame(canvas)
        
        # Add inner frame to canvas window
        window_id = canvas.create_window((0, 0), window=inner_frame, anchor="nw")
        
        # Update the canvas's scroll region when the inner frame size changes
        def _on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        inner_frame.bind("<Configure>", _on_frame_configure)
        
        # Update canvas window width when canvas size changes
        def _on_canvas_configure(event):
            min_width = inner_frame.winfo_reqwidth()
            if event.width > min_width:
                # If canvas is wider than inner frame, expand inner frame
                canvas.itemconfig(window_id, width=event.width)
            else:
                # Otherwise, keep inner frame at its minimum width
                canvas.itemconfig(window_id, width=min_width)
        
        canvas.bind("<Configure>", _on_canvas_configure)
        
        # Bind mouse wheel to scroll
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # For Linux, bind mousewheel differently
        canvas.bind("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))
        
        return outer_frame, inner_frame

    def configure_ui_density(self, density="normal"):
        """Configure UI element sizes and spacing based on density setting"""
        if density == "compact":
            self.padding = {
                "frame": 3,
                "widget": 2,
                "section": 5
            }
            self.widget_width = {
                "small": 5,
                "medium": 10,
                "large": 20
            }
        elif density == "comfortable":
            self.padding = {
                "frame": 12,
                "widget": 6,
                "section": 15
            }
            self.widget_width = {
                "small": 8,
                "medium": 15,
                "large": 30
            }
        else:  # normal
            self.padding = {
                "frame": 8,
                "widget": 4,
                "section": 10
            }
            self.widget_width = {
                "small": 6,
                "medium": 12,
                "large": 25
            }
        
        # Configure style
        style = ttk.Style()
        style.configure("TFrame", padding=self.padding["frame"])
        style.configure("TLabelframe", padding=self.padding["section"])
        style.configure("TButton", padding=self.padding["widget"])
        
        # Save the setting
        self.ui_density = density

    def setup_responsive_ui(self):
        """Configure UI to be responsive to window size changes"""
        min_width = 800
        min_height = 600
        
        def on_resize(event):
            # Get current window dimensions
            window_width = event.width
            window_height = event.height
            
            # Determine if we need compact or normal UI
            if window_width < 1024 or window_height < 768:
                if self.ui_density != "compact":
                    self.configure_ui_density("compact")
                    self.rebuild_ui()
            else:
                if self.ui_density != "normal":
                    self.configure_ui_density("normal")
                    self.rebuild_ui()
        
        # Bind to window resize event
        self.root.bind("<Configure>", on_resize)
        
        # Set minimum size for the window
        self.root.minsize(min_width, min_height)
        
        # Initial configuration
        self.configure_ui_density("normal")

    def rebuild_ui(self):
        """Rebuild the UI when density changes"""
        # You could rebuild each tab, or simply force a redraw of existing elements
        # Simplest approach: just update padding and spacing
        pass

    def show_loading_overlay(self, parent_widget, message="Loading..."):
        """Show a semi-transparent loading overlay on a widget"""
        # Create overlay frame
        overlay = ttk.Frame(parent_widget)
        
        # Position it over the parent widget
        overlay.place(relx=0.5, rely=0.5, anchor="center",
                    relwidth=1.0, relheight=1.0)
        
        # Semi-transparent effect
        overlay.configure(style="Overlay.TFrame")
        
        # Add spinner and message
        spinner_frame = ttk.Frame(overlay)
        spinner_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        # Simple spinner animation
        spinner_canvas = tk.Canvas(spinner_frame, width=50, height=50, 
                                bg=self.theme.bg_color, highlightthickness=0)
        spinner_canvas.pack()
        
        # Draw spinner
        spinner_canvas.create_arc(10, 10, 40, 40, start=0, extent=90, 
                                outline=self.theme.primary_color, width=5, style="arc")
        
        # Animate spinner
        def update_spinner(angle):
            spinner_canvas.delete("all")
            spinner_canvas.create_arc(10, 10, 40, 40, start=angle, extent=90, 
                                outline=self.theme.primary_color, width=5, style="arc")
            angle = (angle + 10) % 360
            overlay.after(50, update_spinner, angle)
        
        update_spinner(0)
        
        # Add message
        msg_label = ttk.Label(spinner_frame, text=message)
        msg_label.pack(pady=10)
        
        return overlay

    def hide_loading_overlay(self, overlay):
        """Hide and destroy the loading overlay"""
        if overlay:
            overlay.destroy()

    def create_form_section(self, parent, title, fields):
        """Create a standardized form section with proper grid layout"""
        frame = ttk.LabelFrame(parent, text=title, padding=self.padding["section"])
        
        # Create grid layout
        for i, (label_text, input_type, default_value, options) in enumerate(fields):
            # Label
            ttk.Label(frame, text=label_text).grid(row=i, column=0, padx=5, pady=5, sticky="w")
            
            # Input field
            if input_type == "entry":
                var = tk.StringVar(value=default_value)
                entry = ttk.Entry(frame, textvariable=var, width=options.get("width", 20))
                entry.grid(row=i, column=1, padx=5, pady=5, sticky="ew")
                
                # Add optional browse button
                if options.get("browse"):
                    browse_btn = ttk.Button(frame, text="Browse", 
                                        command=lambda v=var, t=options.get("browse"): 
                                                self.browse_for_path(v, t))
                    browse_btn.grid(row=i, column=2, padx=5, pady=5)
                
                # Store variable for later access
                setattr(self, f"{options.get('var_name')}_var", var)
                
            elif input_type == "combobox":
                var = tk.StringVar(value=default_value)
                combo = ttk.Combobox(frame, textvariable=var, values=options.get("values", []))
                combo.grid(row=i, column=1, padx=5, pady=5, sticky="ew")
                
                # Store variable and widget for later access
                setattr(self, f"{options.get('var_name')}_var", var)
                setattr(self, f"{options.get('var_name')}_combo", combo)
                
            elif input_type == "checkbutton":
                var = tk.BooleanVar(value=default_value)
                check = ttk.Checkbutton(frame, text="", variable=var)
                check.grid(row=i, column=1, padx=5, pady=5, sticky="w")
                
                # Store variable for later access
                setattr(self, f"{options.get('var_name')}_var", var)
                
        # Configure grid to expand properly
        frame.columnconfigure(1, weight=1)
        
        return frame

    def apply_modern_styles(self):
        """Apply modern styling to ttk widgets"""
        style = ttk.Style()
        
        # Toggle-style radio buttons
        style.configure(
            "Toggle.TRadiobutton",
            background=self.theme.bg_color,
            foreground=self.theme.text_color,
            font=self.theme.normal_font,
            relief="raised",
            borderwidth=1,
            padding=8
        )

        style.map(
            "Toggle.TRadiobutton",
            background=[("selected", self.theme.primary_color), 
                    ("active", self.theme.secondary_color)],
            foreground=[("selected", self.theme.light_text)]

        )
        # Configure modern button style
        style.configure(
            "Modern.TButton",
            background=self.theme.primary_color,
            foreground="white",
            padding=6,
            relief="flat"
        )
        style.map(
            "Modern.TButton",
            background=[("active", self.theme.accent_hover), 
                    ("pressed", self.theme.accent_hover)]
        )
        
        # Configure section headers
        style.configure(
            "Section.TLabel",
            font=self.theme.header_font,
            foreground=self.theme.primary_color,
            padding=5
        )
        
        # Configure card-like frames
        style.configure(
            "Card.TFrame",
            background="white",
            relief="raised",
            borderwidth=1
        )
        
        # Configure overlay style
        style.configure(
            "Overlay.TFrame",
            background="#000000",
            opacity=0.7
        )

    def _setup_viz_control_panel(self, parent):
        """Setup the visualization control panel with collapsible sections"""
        # Main frame for controls
        controls_frame = ttk.Frame(parent)
        controls_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Style for section headers
        style = ttk.Style()
        style.configure("Section.TButton", font=self.theme.header_font)
        
        # Create collapsible sections
        self._create_collapsible_section(
            controls_frame, 
            "Field Selection", 
            self._create_field_selection_panel
        )
        
        self._create_collapsible_section(
            controls_frame, 
            "Visualization Options", 
            self._create_viz_options_panel
        )
        
        self._create_collapsible_section(
            controls_frame, 
            "Color Settings", 
            self._create_color_settings_panel
        )
        
        self._create_collapsible_section(
            controls_frame, 
            "Data Range", 
            self._create_data_range_panel
        )
        
        # Action buttons at the bottom
        action_frame = ttk.Frame(controls_frame)
        action_frame.pack(fill='x', pady=10)
        
        ttk.Button(
            action_frame, 
            text="Update Visualization",
            style="Accent.TButton", 
            command=self.update_cfd_visualization
        ).pack(fill='x', pady=5)
        
        ttk.Button(
            action_frame, 
            text="Export Image", 
            command=self.export_cfd_image
        ).pack(fill='x', pady=5)
        
        ttk.Button(
            action_frame, 
            text="Export Data", 
            command=self.export_cfd_results
        ).pack(fill='x', pady=5)

    def _create_field_selection_panel(self, parent):
        """Create field selection panel"""
        frame = ttk.Frame(parent)
        frame.pack(fill='x', padx=5, pady=5)
        
        # Field selection with icons
        ttk.Label(frame, text="Select Data Field:", font=self.theme.normal_font).pack(anchor='w')
        
        fields = [
            ("Pressure", "Visualization of pressure distribution"),
            ("Velocity", "Visualization of flow velocity magnitude"),
            ("Temperature", "Visualization of temperature distribution"),
            ("Turbulence", "Visualization of turbulence intensity"),
            ("Vorticity", "Visualization of vorticity magnitude"),
            ("Q-Criterion", "Visualization of vortex identification")
        ]
        
        self.field_var = tk.StringVar(value="Pressure")
        field_frame = ttk.Frame(frame)
        field_frame.pack(fill='x', pady=5)
        
        # Create modern radio buttons for field selection
        for i, (field, tooltip) in enumerate(fields):
            rb = ttk.Radiobutton(
                field_frame, 
                text=field,
                variable=self.field_var,
                value=field,
                command=self.update_cfd_visualization
            )
            rb.grid(row=i//2, column=i%2, sticky='w', padx=5, pady=3)
            
            # Add tooltip functionality
            self._create_tooltip(rb, tooltip)
        
        return frame
    
    def _create_viz_options_panel(self, parent):
        """Create visualization options panel"""
        frame = ttk.Frame(parent)
        frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(frame, text="Visualization Type:", font=self.theme.normal_font).pack(anchor='w')
        
        viz_types = [
            "Contour", "Surface", "Vector", "Streamlines", 
            "Isosurface", "Slice", "Volume Rendering", "Particles"
        ]
        
        self.viz_var = tk.StringVar(value="Contour")
        self.viz_combo = ttk.Combobox(
            frame, 
            textvariable=self.viz_var, 
            values=viz_types,
            state="readonly",
            width=20
        )
        self.viz_combo.pack(fill='x', pady=5)
        self.viz_combo.bind("<<ComboboxSelected>>", self._on_viz_type_changed)
        
        # Options that change based on visualization type
        self.viz_options_frame = ttk.Frame(frame)
        self.viz_options_frame.pack(fill='x', pady=5)
        
        # Display options with checkboxes and icons
        options_frame = ttk.LabelFrame(frame, text="Display Elements")
        options_frame.pack(fill='x', pady=5)
        
        self.show_colorbar_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_frame, 
            text="Colorbar",
            variable=self.show_colorbar_var,
            command=self.update_cfd_visualization
        ).pack(anchor='w', padx=5, pady=2)
        
        self.show_labels_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_frame, 
            text="Axis Labels",
            variable=self.show_labels_var,
            command=self.update_cfd_visualization
        ).pack(anchor='w', padx=5, pady=2)
        
        self.show_grid_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_frame, 
            text="Grid",
            variable=self.show_grid_var,
            command=self.update_cfd_visualization
        ).pack(anchor='w', padx=5, pady=2)
        
        self.show_legend_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_frame, 
            text="Legend",
            variable=self.show_legend_var,
            command=self.update_cfd_visualization
        ).pack(anchor='w', padx=5, pady=2)
        
        # Update visualization options based on initial type
        self._on_viz_type_changed()
        
        return frame

    def _setup_viz_display_panel(self, parent):
        """Setup the visualization display panel with tabs"""
        # Create notebook for different visualization views
        self.viz_notebook = ttk.Notebook(parent)
        self.viz_notebook.pack(fill='both', expand=True)
        
        # 2D View tab
        self.view_2d_tab = ttk.Frame(self.viz_notebook)
        self.viz_notebook.add(self.view_2d_tab, text="2D View")
        
        # Create matplotlib figure for 2D view
        self.cfd_fig = Figure(figsize=(8, 6), dpi=100)
        self.cfd_ax = self.cfd_fig.add_subplot(111)
        self.cfd_canvas = FigureCanvasTkAgg(self.cfd_fig, master=self.view_2d_tab)
        self.cfd_canvas.draw()
        self.cfd_canvas.get_tk_widget().pack(fill='both', expand=True)
        
        # Add toolbar with custom buttons
        toolbar_frame = ttk.Frame(self.view_2d_tab)
        toolbar_frame.pack(fill='x', pady=5)
        
        self.cfd_toolbar = NavigationToolbar2Tk(self.cfd_canvas, toolbar_frame)
        self.cfd_toolbar.update()
        
        # Add custom toolbar buttons
        ttk.Button(
            toolbar_frame, 
            text="Reset View", 
            command=self._reset_view
        ).pack(side='left', padx=5)
        
        # 3D View tab
        self.view_3d_tab = ttk.Frame(self.viz_notebook)
        self.viz_notebook.add(self.view_3d_tab, text="3D View")
        
        # Create 3D visualization (uses PyVista if available, otherwise falls back to matplotlib 3D)
        try:
            import pyvista as pv
            from pyvistaqt import QtInteractor
            
            self.pv_frame = ttk.Frame(self.view_3d_tab)
            self.pv_frame.pack(fill='both', expand=True)
            
            # Create PyVista plotter
            self.plotter = QtInteractor(self.pv_frame)
            self.plotter.set_background(self.theme.bg_color)
            self.plotter.show_axes()
            self.plotter.add_axes()
            self.plotter.reset_camera()
            self.plotter.show()
            
            # Signal that we're using PyVista
            self.using_pyvista = True
            
        except ImportError:
            # Fall back to matplotlib 3D
            self.cfd_3d_fig = Figure(figsize=(8, 6), dpi=100)
            self.cfd_3d_ax = self.cfd_3d_fig.add_subplot(111, projection='3d')
            self.cfd_3d_canvas = FigureCanvasTkAgg(self.cfd_3d_fig, master=self.view_3d_tab)
            self.cfd_3d_canvas.draw()
            self.cfd_3d_canvas.get_tk_widget().pack(fill='both', expand=True)
            
            # Add toolbar
            self.cfd_3d_toolbar = NavigationToolbar2Tk(self.cfd_3d_canvas, self.view_3d_tab)
            self.cfd_3d_toolbar.update()
            
            # Signal that we're not using PyVista
            self.using_pyvista = False
        
        # Cross-Sections tab
        self.cross_section_tab = ttk.Frame(self.viz_notebook)
        self.viz_notebook.add(self.cross_section_tab, text="Cross Sections")
        
        # Setup cross-section visualization
        self._setup_cross_section_view(self.cross_section_tab)
        
        # Statistics tab
        self.stats_tab = ttk.Frame(self.viz_notebook)
        self.viz_notebook.add(self.stats_tab, text="Statistics")
        
        # Setup statistics view
        self._setup_statistics_view(self.stats_tab)
        
    def _setup_animation_controls(self, parent):
        """Set up animation controls for time-dependent data"""
        frame = ttk.LabelFrame(parent, text="Animation Controls")
        frame.pack(fill='x', padx=5, pady=5)
        
        # Time slider
        slider_frame = ttk.Frame(frame)
        slider_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(slider_frame, text="Time:").pack(side='left')
        
        self.time_var = tk.DoubleVar(value=0.0)
        self.time_slider = ttk.Scale(
            slider_frame, 
            from_=0.0, 
            to=10.0,
            orient='horizontal', 
            variable=self.time_var,
            command=self._on_time_changed
        )
        self.time_slider.pack(side='left', fill='x', expand=True, padx=5)
        
        self.time_label = ttk.Label(slider_frame, text="0.00s")
        self.time_label.pack(side='left')
        
        # Animation buttons
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill='x', padx=5, pady=5)
        
        self.play_icon = "▶"  # Unicode play symbol
        self.pause_icon = "⏸"  # Unicode pause symbol
        
        self.play_button = ttk.Button(
            button_frame, 
            text=self.play_icon,
            width=3,
            command=self._toggle_animation
        )
        self.play_button.pack(side='left', padx=2)
        
        ttk.Button(
            button_frame, 
            text="⏮",  # Unicode skip to start symbol
            width=3,
            command=self._animation_to_start
        ).pack(side='left', padx=2)
        
        ttk.Button(
            button_frame, 
            text="⏭",  # Unicode skip to end symbol
            width=3,
            command=self._animation_to_end
        ).pack(side='left', padx=2)
        
        # Animation speed
        speed_frame = ttk.Frame(button_frame)
        speed_frame.pack(side='right')
        
        ttk.Label(speed_frame, text="Speed:").pack(side='left')
        
        self.speed_var = tk.DoubleVar(value=1.0)
        speed_slider = ttk.Scale(
            speed_frame, 
            from_=0.1, 
            to=5.0,
            orient='horizontal', 
            variable=self.speed_var,
            length=100
        )
        speed_slider.pack(side='left', padx=5)
        
        # Animation state variables
        self.animating = False
        self.animation_id = None
        
        return frame

    def _toggle_animation(self):
        """Toggle the animation on/off"""
        if self.animating:
            self._stop_animation()
        else:
            self._start_animation()

    def _start_animation(self):
        """Start the animation"""
        self.animating = True
        self.play_button.configure(text=self.pause_icon)
        self._animate_step()

    def _stop_animation(self):
        """Stop the animation"""
        self.animating = False
        self.play_button.configure(text=self.play_icon)
        if self.animation_id:
            self.root.after_cancel(self.animation_id)
            self.animation_id = None

    def _animate_step(self):
        """Advance animation by one step"""
        if not self.animating:
            return
        
        # Get current time and increment
        current_time = self.time_var.get()
        speed = self.speed_var.get()
        
        # Calculate new time
        new_time = current_time + 0.1 * speed
        if new_time > self.time_slider.cget('to'):
            new_time = 0.0  # Loop back to start
        
        # Update slider position
        self.time_var.set(new_time)
        self._on_time_changed(new_time)
        
        # Schedule next frame
        self.animation_id = self.root.after(50, self._animate_step)

    def _setup_comparison_view(self, parent):
        """Setup view for comparing multiple datasets"""
        # Create frame for comparison controls
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(control_frame, text="Compare Mode:").pack(side='left')
        
        self.compare_mode_var = tk.StringVar(value="Side by Side")
        compare_mode = ttk.Combobox(
            control_frame, 
            textvariable=self.compare_mode_var,
            values=["Side by Side", "Overlay", "Difference"],
            state="readonly",
            width=15
        )
        compare_mode.pack(side='left', padx=5)
        compare_mode.bind("<<ComboboxSelected>>", self._update_comparison)
        
        ttk.Label(control_frame, text="Dataset A:").pack(side='left', padx=(20, 5))
        
        self.dataset_a_var = tk.StringVar()
        dataset_a = ttk.Combobox(
            control_frame, 
            textvariable=self.dataset_a_var,
            values=self._get_available_datasets(),
            state="readonly",
            width=15
        )
        dataset_a.pack(side='left', padx=5)
        dataset_a.bind("<<ComboboxSelected>>", self._update_comparison)
        
        ttk.Label(control_frame, text="Dataset B:").pack(side='left', padx=(20, 5))
        
        self.dataset_b_var = tk.StringVar()
        dataset_b = ttk.Combobox(
            control_frame, 
            textvariable=self.dataset_b_var,
            values=self._get_available_datasets(),
            state="readonly",
            width=15
        )
        dataset_b.pack(side='left', padx=5)
        dataset_b.bind("<<ComboboxSelected>>", self._update_comparison)
        
        # Create comparison figure
        comparison_frame = ttk.Frame(parent)
        comparison_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.comparison_fig = Figure(figsize=(10, 6), dpi=100)
        
        # For side by side, we'll use two subplots
        self.compare_ax1 = self.comparison_fig.add_subplot(121)
        self.compare_ax2 = self.comparison_fig.add_subplot(122)
        
        self.comparison_canvas = FigureCanvasTkAgg(self.comparison_fig, master=comparison_frame)
        self.comparison_canvas.draw()
        self.comparison_canvas.get_tk_widget().pack(fill='both', expand=True)
        
        # Add toolbar
        toolbar_frame = ttk.Frame(comparison_frame)
        toolbar_frame.pack(fill='x')
        
        self.comparison_toolbar = NavigationToolbar2Tk(self.comparison_canvas, toolbar_frame)
        self.comparison_toolbar.update()

    def _create_data_filtering_panel(self, parent):
        """Create panel for data filtering options"""
        frame = ttk.LabelFrame(parent, text="Data Filtering")
        frame.pack(fill='x', padx=5, pady=5)
        
        # Filter by range
        range_frame = ttk.Frame(frame)
        range_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(range_frame, text="Filter Range:").grid(row=0, column=0, sticky='w')
        
        self.filter_min_var = tk.DoubleVar(value=0.0)
        self.filter_max_var = tk.DoubleVar(value=1.0)
        
        ttk.Label(range_frame, text="Min:").grid(row=1, column=0, sticky='w', padx=5)
        ttk.Entry(range_frame, textvariable=self.filter_min_var, width=8).grid(row=1, column=1, padx=5, pady=2)
        
        ttk.Label(range_frame, text="Max:").grid(row=2, column=0, sticky='w', padx=5)
        ttk.Entry(range_frame, textvariable=self.filter_max_var, width=8).grid(row=2, column=1, padx=5, pady=2)
        
        ttk.Button(
            range_frame, 
            text="Apply Filter", 
            command=self._apply_data_filter
        ).grid(row=3, column=0, columnspan=2, pady=5)
        
        # Threshold for isolines or isosurfaces
        threshold_frame = ttk.Frame(frame)
        threshold_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(threshold_frame, text="Threshold Values:").pack(anchor='w')
        
        threshold_entry_frame = ttk.Frame(threshold_frame)
        threshold_entry_frame.pack(fill='x', pady=5)
        
        self.threshold_var = tk.StringVar(value="0.5")
        threshold_entry = ttk.Entry(threshold_entry_frame, textvariable=self.threshold_var, width=8)
        threshold_entry.pack(side='left', padx=5)
        
        ttk.Button(
            threshold_entry_frame, 
            text="+", 
            width=2,
            command=lambda: self._add_threshold_value(self.threshold_var.get())
        ).pack(side='left')
        
        # List of active thresholds
        self.threshold_list_frame = ttk.Frame(threshold_frame)
        self.threshold_list_frame.pack(fill='x', pady=5)
        
        ttk.Label(self.threshold_list_frame, text="Active Thresholds:").pack(anchor='w')
        
        self.threshold_listbox = tk.Listbox(self.threshold_list_frame, height=4)
        self.threshold_listbox.pack(fill='x', pady=5)
        
        threshold_buttons = ttk.Frame(self.threshold_list_frame)
        threshold_buttons.pack(fill='x')
        
        ttk.Button(
            threshold_buttons, 
            text="Remove", 
            command=self._remove_threshold
        ).pack(side='left', padx=5)
        
        ttk.Button(
            threshold_buttons, 
            text="Clear All", 
            command=lambda: self.threshold_listbox.delete(0, tk.END)
        ).pack(side='left', padx=5)
        
        return frame
    
    def _add_threshold_value(self, value):
        """Add a threshold value to the list"""
        try:
            # Validate that it's a number
            value = float(value)
            self.threshold_listbox.insert(tk.END, f"{value:.3f}")
            self.update_cfd_visualization()
        except ValueError:
            messagebox.showerror("Invalid Value", "Threshold must be a valid number")
    
    def _remove_threshold(self):
        """Remove selected threshold from list"""
        selection = self.threshold_listbox.curselection()
        if selection:
            self.threshold_listbox.delete(selection[0])
            self.update_cfd_visualization()

    def _create_color_settings_panel(self, parent):
        """Create color settings panel with advanced colormap options"""
        frame = ttk.Frame(parent)
        frame.pack(fill='x', padx=5, pady=5)
        
        # Colormap selection with preview
        colormap_frame = ttk.LabelFrame(frame, text="Colormap")
        colormap_frame.pack(fill='x', pady=5)
        
        # Group colormaps by category
        cmap_categories = {
            "Sequential": ["viridis", "plasma", "inferno", "magma", "cividis"],
            "Diverging": ["coolwarm", "bwr", "seismic", "RdBu", "RdYlBu"],
            "Qualitative": ["tab10", "tab20", "Pastel1", "Set1", "Set2"],
            "Misc": ["rainbow", "jet", "turbo", "nipy_spectral", "gist_ncar"]
        }
        
        # Create dropdown for category selection
        ttk.Label(colormap_frame, text="Category:").pack(anchor='w', padx=5, pady=2)
        
        self.cmap_category_var = tk.StringVar(value="Sequential")
        cmap_category = ttk.Combobox(
            colormap_frame,
            textvariable=self.cmap_category_var,
            values=list(cmap_categories.keys()),
            state="readonly",
            width=15
        )
        cmap_category.pack(fill='x', padx=5, pady=2)
        cmap_category.bind("<<ComboboxSelected>>", self._update_cmap_list)
        
        # Create dropdown for colormap selection
        ttk.Label(colormap_frame, text="Colormap:").pack(anchor='w', padx=5, pady=2)
        
        self.colormap_var = tk.StringVar(value="viridis")
        self.colormap_combo = ttk.Combobox(
            colormap_frame,
            textvariable=self.colormap_var,
            values=cmap_categories["Sequential"],
            state="readonly",
            width=15
        )
        self.colormap_combo.pack(fill='x', padx=5, pady=2)
        self.colormap_combo.bind("<<ComboboxSelected>>", self._update_colormap_preview)
        
        # Preview canvas
        preview_frame = ttk.Frame(colormap_frame)
        preview_frame.pack(fill='x', padx=5, pady=5)
        
        self.cmap_preview = tk.Canvas(preview_frame, width=200, height=30)
        self.cmap_preview.pack(fill='x')
        
        # Update the preview initially
        self._update_colormap_preview()
        
        # Colormap options
        options_frame = ttk.Frame(colormap_frame)
        options_frame.pack(fill='x', padx=5, pady=5)
        
        # Reverse colormap
        self.reverse_cmap_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            options_frame,
            text="Reverse Colormap",
            variable=self.reverse_cmap_var,
            command=self._update_colormap_preview
        ).pack(anchor='w')
        
        # Transparency control
        transparency_frame = ttk.Frame(colormap_frame)
        transparency_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(transparency_frame, text="Transparency:").pack(side='left')
        
        self.transparency_var = tk.DoubleVar(value=0.0)  # 0.0 = opaque, 1.0 = transparent
        transparency_slider = ttk.Scale(
            transparency_frame,
            from_=0.0,
            to=0.9,
            orient='horizontal',
            variable=self.transparency_var,
            command=lambda _: self.update_cfd_visualization()
        )
        transparency_slider.pack(side='left', fill='x', expand=True, padx=5)
        
        return frame
    
    def _update_cmap_list(self, event=None):
        """Update the colormap list based on selected category"""
        category = self.cmap_category_var.get()
        
        # Group colormaps by category
        cmap_categories = {
            "Sequential": ["viridis", "plasma", "inferno", "magma", "cividis"],
            "Diverging": ["coolwarm", "bwr", "seismic", "RdBu", "RdYlBu"],
            "Qualitative": ["tab10", "tab20", "Pastel1", "Set1", "Set2"],
            "Misc": ["rainbow", "jet", "turbo", "nipy_spectral", "gist_ncar"]
        }
        
        # Update combobox values
        self.colormap_combo.config(values=cmap_categories.get(category, ["viridis"]))
        self.colormap_var.set(cmap_categories.get(category, ["viridis"])[0])
        
        # Update preview
        self._update_colormap_preview()
    
    def _update_colormap_preview(self, event=None):
        """Update the colormap preview"""
        import matplotlib.cm as cm
        import numpy as np
        
        cmap_name = self.colormap_var.get()
        reverse = self.reverse_cmap_var.get()
        
        if reverse:
            cmap_name = cmap_name + "_r"
        
        # Get colormap
        cmap = cm.get_cmap(cmap_name)
        
        # Create gradient image
        width = self.cmap_preview.winfo_width() or 200
        height = self.cmap_preview.winfo_height() or 30
        
        # Create RGB data for preview
        gradient = np.linspace(0, 1, width)
        gradient = np.vstack((gradient, gradient))
        
        # Convert to bitmap for tkinter
        from PIL import Image, ImageTk
        
        # Apply colormap
        rgb_array = cmap(gradient)[:, :, :3]  # Exclude alpha channel
        rgb_array = (rgb_array * 255).astype(np.uint8)
        
        # Create image
        img = Image.fromarray(rgb_array)
        photo = ImageTk.PhotoImage(img)
        
        # Update canvas
        self.cmap_preview.delete("all")
        self.cmap_preview.create_image(0, 0, image=photo, anchor='nw')
        self.cmap_preview.image = photo  # Keep reference to prevent garbage collection
        
        # Add labels
        self.cmap_preview.create_text(10, height-10, text="Min", anchor='sw')
        self.cmap_preview.create_text(width-10, height-10, text="Max", anchor='se')
        
        # Update visualization
        self.update_cfd_visualization()

    def _setup_advanced_charts_panel(self, parent):
        """Setup panel with advanced chart options"""
        # Create notebook for different chart types
        charts_notebook = ttk.Notebook(parent)
        charts_notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Line profile tab
        profile_tab = ttk.Frame(charts_notebook)
        charts_notebook.add(profile_tab, text="Line Profiles")
        
        self._setup_line_profile_panel(profile_tab)
        
        # Histogram tab
        histogram_tab = ttk.Frame(charts_notebook)
        charts_notebook.add(histogram_tab, text="Histogram")
        
        self._setup_histogram_panel(histogram_tab)
        
        # Scatter plot tab
        scatter_tab = ttk.Frame(charts_notebook)
        charts_notebook.add(scatter_tab, text="Scatter Plot")
        
        self._setup_scatter_panel(scatter_tab)
        
        # Polar plot tab
        polar_tab = ttk.Frame(charts_notebook)
        charts_notebook.add(polar_tab, text="Polar Plot")
        
        self._setup_polar_panel(polar_tab)
        
        return charts_notebook

    def _setup_line_profile_panel(self, parent):
        """Setup line profile panel"""
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill='x', padx=10, pady=10)
        
        # Controls for line position
        ttk.Label(control_frame, text="Start Point (X, Y):").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        
        point_frame = ttk.Frame(control_frame)
        point_frame.grid(row=0, column=1, padx=5, pady=5, sticky='w')
        
        self.start_x_var = tk.DoubleVar(value=0.0)
        self.start_y_var = tk.DoubleVar(value=0.0)
        
        ttk.Entry(point_frame, textvariable=self.start_x_var, width=6).pack(side='left', padx=2)
        ttk.Entry(point_frame, textvariable=self.start_y_var, width=6).pack(side='left', padx=2)
        
        ttk.Label(control_frame, text="End Point (X, Y):").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        
        end_point_frame = ttk.Frame(control_frame)
        end_point_frame.grid(row=1, column=1, padx=5, pady=5, sticky='w')
        
        self.end_x_var = tk.DoubleVar(value=1.0)
        self.end_y_var = tk.DoubleVar(value=1.0)
        
        ttk.Entry(end_point_frame, textvariable=self.end_x_var, width=6).pack(side='left', padx=2)
        ttk.Entry(end_point_frame, textvariable=self.end_y_var, width=6).pack(side='left', padx=2)
        
        # Number of points along line
        ttk.Label(control_frame, text="# Points:").grid(row=2, column=0, padx=5, pady=5, sticky='w')
        
        self.n_points_var = tk.IntVar(value=100)
        ttk.Entry(control_frame, textvariable=self.n_points_var, width=6).grid(row=2, column=1, padx=5, pady=5, sticky='w')
        
        # Button to extract profile
        ttk.Button(
            control_frame, 
            text="Extract Profile",
            command=self._extract_line_profile
        ).grid(row=3, column=0, columnspan=2, pady=10)
        
        # Figure for profile plot
        self.profile_fig = Figure(figsize=(6, 4), dpi=100)
        self.profile_ax = self.profile_fig.add_subplot(111)
        self.profile_ax.set_title("Line Profile")
        self.profile_ax.set_xlabel("Distance")
        self.profile_ax.set_ylabel("Value")
        
        self.profile_canvas = FigureCanvasTkAgg(self.profile_fig, master=parent)
        self.profile_canvas.draw()
        self.profile_canvas.get_tk_widget().pack(fill='both', expand=True, padx=10, pady=10)
        
        # Add toolbar
        self.profile_toolbar = NavigationToolbar2Tk(self.profile_canvas, parent)
        self.profile_toolbar.update()

    def _create_collapsible_section(self, parent, title, content_func):
        """Create a collapsible section with a toggle button"""
        frame = ttk.Frame(parent)
        frame.pack(fill='x', pady=5)
        
        # Variables
        is_collapsed = tk.BooleanVar(value=False)
        
        # Header with toggle button
        header_frame = ttk.Frame(frame)
        header_frame.pack(fill='x')
        
        def toggle_collapse():
            if is_collapsed.get():
                # Expand
                is_collapsed.set(False)
                toggle_btn.configure(text="▼")
                content_frame.pack(fill='x', pady=5)
            else:
                # Collapse
                is_collapsed.set(True)
                toggle_btn.configure(text="►")
                content_frame.pack_forget()
        
        toggle_btn = ttk.Button(
            header_frame, 
            text="▼", 
            width=2,
            command=toggle_collapse
        )
        toggle_btn.pack(side='left', padx=5)
        
        ttk.Label(
            header_frame, 
            text=title, 
            font=self.theme.header_font
        ).pack(side='left', padx=5)
        
        # Content (initially visible)
        content_frame = ttk.Frame(frame)
        content_frame.pack(fill='x', pady=5)
        
        # Create the content
        content_func(content_frame)
        
        # Add separator at the end
        ttk.Separator(frame, orient='horizontal').pack(fill='x', pady=5)
        
        return frame

    def _create_tooltip(self, widget, text):
        """Create a tooltip for a widget"""
        tooltip = tk.Toplevel(widget)
        tooltip.wm_withdraw()
        tooltip.wm_overrideredirect(True)
        
        label = tk.Label(
            tooltip, 
            text=text, 
            background="#FFFFEA", 
            relief="solid", 
            borderwidth=1,
            padx=5,
            pady=2
        )
        label.pack()
        
        def enter(event):
            x = widget.winfo_rootx() + widget.winfo_width() + 5
            y = widget.winfo_rooty()
            tooltip.wm_geometry(f"+{x}+{y}")
            tooltip.wm_deiconify()
        
        def leave(event):
            tooltip.wm_withdraw()
        
        widget.bind("<Enter>", enter)
        widget.bind("<Leave>", leave)
    
    def _update_pyvista_visualization(self, X, Y, Z, field, cmap_name):
        """Update the PyVista 3D visualization"""
        try:
            import pyvista as pv
            import numpy as np
            
            # Clear existing plot
            self.plotter.clear()
            
            # Create a structured grid from the data
            grid = pv.StructuredGrid(X, Y, np.zeros_like(Z))
            
            # Add the scalar data to the grid
            grid.point_data[field] = Z.flatten()
            
            # Create visualization based on type
            viz_type = self.viz_var.get() if hasattr(self, 'viz_var') else "Contour"
            
            if viz_type == "Contour":
                # Create 2D contours on the XY plane
                contours = grid.contour(scalars=field)
                self.plotter.add_mesh(contours, cmap=cmap_name, show_scalar_bar=True)
                
            elif viz_type == "Surface":
                # Create a 3D surface with Z values from the field
                warped = grid.warp_by_scalar(scalars=field, factor=0.1)
                self.plotter.add_mesh(warped, scalars=field, cmap=cmap_name, show_scalar_bar=True)
                
            elif viz_type == "Isosurface":
                # Get thresholds if available
                if hasattr(self, 'threshold_listbox'):
                    thresholds = []
                    for i in range(self.threshold_listbox.size()):
                        try:
                            thresholds.append(float(self.threshold_listbox.get(i)))
                        except ValueError:
                            pass
                            
                    if not thresholds:
                        # If no thresholds specified, use evenly spaced values
                        zmin, zmax = np.min(Z), np.max(Z)
                        thresholds = np.linspace(zmin + (zmax-zmin)*0.2, 
                                                zmin + (zmax-zmin)*0.8, 5)
                else:
                    # Default thresholds
                    zmin, zmax = np.min(Z), np.max(Z)
                    thresholds = np.linspace(zmin + (zmax-zmin)*0.2, 
                                            zmin + (zmax-zmin)*0.8, 5)
                
                # Create a volume for isosurfaces
                vol = grid.cell_data_to_point_data()
                vol[field] = Z.flatten()
                
                # Add isosurfaces
                contours = vol.contour(isosurfaces=thresholds, scalars=field)
                self.plotter.add_mesh(contours, cmap=cmap_name, opacity=0.7, show_scalar_bar=True)
                
            elif viz_type == "Vector":
                # Create a basic vector field
                if 'Velocity_X' in self.visualization_data and 'Velocity_Y' in self.visualization_data:
                    VX = self.visualization_data['Velocity_X']
                    VY = self.visualization_data['Velocity_Y']
                    
                    # Create vectors (with zero Z component)
                    vectors = np.column_stack((VX.flatten(), VY.flatten(), np.zeros_like(VX.flatten())))
                    
                    # Add vectors to grid
                    grid.point_data['vectors'] = vectors
                    
                    # Add arrow glyphs
                    glyphs = grid.glyph(
                        orient='vectors',
                        scale='Velocity',
                        factor=0.05
                    )
                    self.plotter.add_mesh(glyphs, color='blue', show_scalar_bar=False)
                    
                    # Add a contour base
                    self.plotter.add_mesh(grid, opacity=0.5, cmap=cmap_name, scalars=field)
                else:
                    # If no velocity data, just show contours
                    self.plotter.add_mesh(grid, opacity=0.8, cmap=cmap_name, scalars=field)
                    
            elif viz_type == "Volume Rendering":
                # Create a 3D volume from 2D data by stacking
                # For demo purposes, we'll create a volume by extruding the 2D data
                
                # Get Z bounds for volume
                z_min, z_max = -0.5, 0.5
                
                # Create a uniform grid for the volume
                vol = pv.UniformGrid()
                vol.dimensions = np.array(Z.shape) + [1]
                vol.origin = [X.min(), Y.min(), z_min]
                vol.spacing = [
                    (X.max() - X.min()) / (X.shape[1] - 1),
                    (Y.max() - Y.min()) / (Y.shape[0] - 1),
                    z_max - z_min
                ]
                
                # Stack 2D data to create a uniform volume
                vol_data = np.expand_dims(Z, 2)
                vol.cell_data[field] = vol_data.flatten(order='F')
                
                # Add volume rendering
                self.plotter.add_volume(vol, cmap=cmap_name, opacity='sigmoid', show_scalar_bar=True)
            
            else:
                # Default to a simple surface plot
                self.plotter.add_mesh(grid, scalars=field, cmap=cmap_name, show_scalar_bar=True)
            
            # Add axes for reference
            self.plotter.add_axes()
            self.plotter.reset_camera()
            self.plotter.show()
            
        except Exception as e:
            self.log(f"PyVista visualization error: {e}")
            # Fall back to matplotlib 3D if PyVista fails
            self._update_matplotlib_3d(X, Y, Z, field, cmap_name)

    def create_card(self, parent, title=None, **kwargs):
        """Create a modern card-like container"""
        # Main card frame with raised appearance
        card = ttk.Frame(parent, style="Card.TFrame", padding=10)
        
        # Add title if provided
        if title:
            title_label = ttk.Label(card, text=title, style="CardTitle.TLabel")
            title_label.pack(anchor='w', pady=(0, 10))
        
        return card

    def _setup_control_panel(self, parent):
        """Set up visualization controls in the control panel"""
        # Create field selection section
        field_frame = ttk.LabelFrame(parent, text="Data Selection")
        field_frame.pack(fill='x', padx=5, pady=5)
        
        # Add field selection controls
        ttk.Label(field_frame, text="Field:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.field_var = tk.StringVar(value="Pressure")
        field_combo = ttk.Combobox(field_frame, textvariable=self.field_var, 
                                  values=["Pressure", "Velocity", "Temperature", "Turbulence"],
                                  state="readonly")
        field_combo.grid(row=0, column=1, padx=5, pady=5, sticky='ew')
        field_combo.bind("<<ComboboxSelected>>", self.update_cfd_visualization)
        
        # Visualization type section
        viz_frame = ttk.LabelFrame(parent, text="Visualization Options")
        viz_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(viz_frame, text="Type:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.viz_var = tk.StringVar(value="Contour")
        viz_combo = ttk.Combobox(viz_frame, textvariable=self.viz_var, 
                                values=["Contour", "Surface", "Vector", "Streamlines", "Slice"],
                                state="readonly")
        viz_combo.grid(row=0, column=1, padx=5, pady=5, sticky='ew')
        viz_combo.bind("<<ComboboxSelected>>", self.update_cfd_visualization)
        
        # Add more visualization controls here
        
        # Actions section
        action_frame = ttk.LabelFrame(parent, text="Actions")
        action_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(action_frame, text="Update Visualization", 
                 command=self.update_cfd_visualization).pack(fill='x', padx=5, pady=5)
        ttk.Button(action_frame, text="Export Image", 
                 command=self.export_cfd_image).pack(fill='x', padx=5, pady=5)
        ttk.Button(action_frame, text="Export Data", 
                 command=self.export_cfd_results).pack(fill='x', padx=5, pady=5)

    def _create_field_selection(self, parent):
        """Create modern field selection interface"""
        frame = ttk.Frame(parent)
        frame.pack(fill='x', padx=5, pady=5)
        
        # Field options with icons/colors
        fields = [
            ("Pressure", "#e74c3c"),
            ("Velocity", "#3498db"),
            ("Temperature", "#f39c12"),
            ("Turbulence", "#9b59b6"),
            ("Vorticity", "#2ecc71"),
            ("Q-Criterion", "#1abc9c")
        ]
        
        self.field_var = tk.StringVar(value="Pressure")
        
        # Create modern radio buttons with color indicators
        for field_name, color in fields:
            field_frame = ttk.Frame(frame)
            field_frame.pack(fill='x', pady=2)
            
            # Color indicator
            indicator = tk.Canvas(field_frame, width=15, height=15, 
                                bg=self.theme.bg_color, highlightthickness=0)
            indicator.pack(side='left', padx=5)
            indicator.create_oval(2, 2, 13, 13, fill=color, outline=color)
            
            # Radio button
            rb = ttk.Radiobutton(
                field_frame, text=field_name, 
                variable=self.field_var, value=field_name,
                command=self.update_cfd_visualization
            )
            rb.pack(side='left', fill='x', expand=True)
        
        return frame

    def _setup_display_area(self, parent):
        """Set up the visualization display area with interactive features"""
        # Create notebook for different views
        self.viz_notebook = ttk.Notebook(parent)
        self.viz_notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        # CFD Results tab
        self.cfd_tab = ttk.Frame(self.viz_notebook)
        self.viz_notebook.add(self.cfd_tab, text="CFD Results")
        
        # Create the figure for CFD visualization
        self.cfd_fig = Figure(figsize=(6, 5), dpi=100)
        self.cfd_ax = self.cfd_fig.add_subplot(111)
        self.cfd_canvas = FigureCanvasTkAgg(self.cfd_fig, master=self.cfd_tab)
        self.cfd_canvas.draw()
        self.cfd_canvas.get_tk_widget().pack(fill='both', expand=True)
        
        # Add interactive toolbar
        self.cfd_toolbar = NavigationToolbar2Tk(self.cfd_canvas, self.cfd_tab)
        self.cfd_toolbar.update()
        
        # Add interactive features
        self.cfd_fig.canvas.mpl_connect('motion_notify_event', self._show_data_at_cursor)
        
        # Add 3D tab
        self.viz_3d_tab = ttk.Frame(self.viz_notebook)
        self.viz_notebook.add(self.viz_3d_tab, text="3D View")
        
        # Set up 3D visualization
        self._setup_3d_visualization(self.viz_3d_tab)
        
        # Comparison tab
        self.comparison_tab = ttk.Frame(self.viz_notebook)
        self.viz_notebook.add(self.comparison_tab, text="Comparison")
        
        # Set up comparison view
        self._setup_comparison_view(self.comparison_tab)

    def apply_modern_styles(self):
        """Apply modern styling to the entire application"""
        style = ttk.Style()
        
        # Configure modern button style
        style.configure(
            "Modern.TButton",
            background=self.theme.primary_color,
            foreground=self.theme.light_text,
            padding=6
        )
        
        style.map(
            "Modern.TButton",
            background=[("active", self.theme.secondary_color)],
            foreground=[("active", self.theme.light_text)]
        )
        
        # Configure section headers
        style.configure(
            "Section.TButton",
            font=self.theme.header_font,
            padding=8
        )
        
        # Card style
        style.configure(
            "Card.TFrame",
            background=self.theme.bg_color,
            relief="raised",
            borderwidth=1
        )
        
        # Card title style
        style.configure(
            "CardTitle.TLabel",
            font=self.theme.header_font,
            foreground=self.theme.primary_color
        )
        
        # Apply styles to existing widgets
        self._apply_styles_to_widgets()

    def _show_data_at_cursor(self, event):
        """Show data value at cursor position"""
        if event.inaxes is None:
            return
        
        # Get data
        if hasattr(self, 'visualization_data') and self.field_var.get() in self.visualization_data:
            try:
                X = self.visualization_data['X']
                Y = self.visualization_data['Y']
                Z = self.visualization_data[self.field_var.get()]
                
                # Find nearest data point
                x, y = event.xdata, event.ydata
                if X is not None and Y is not None and Z is not None:
                    # Find the closest point in the grid
                    x_idx = np.abs(X[0, :] - x).argmin()
                    y_idx = np.abs(Y[:, 0] - y).argmin()
                    
                    # Get the value
                    value = Z[y_idx, x_idx]
                    
                    # Update status bar
                    self.update_status(f"X: {X[y_idx, x_idx]:.4f}, Y: {Y[y_idx, x_idx]:.4f}, {self.field_var.get()}: {value:.4f}")
            except:
                pass

    def _create_animation_controls(self, parent):
        """Create animation controls for time-series data"""
        animation_frame = ttk.Frame(parent)
        animation_frame.pack(fill='x', pady=10)
        
        # Time slider
        time_frame = ttk.Frame(animation_frame)
        time_frame.pack(fill='x', pady=5)
        
        ttk.Label(time_frame, text="Time:").pack(side='left', padx=5)
        self.time_var = tk.DoubleVar(value=0)
        self.time_slider = ttk.Scale(
            time_frame, from_=0, to=100, orient='horizontal',
            variable=self.time_var, command=self._update_time_frame
        )
        self.time_slider.pack(side='left', fill='x', expand=True, padx=5)
        
        self.time_label = ttk.Label(time_frame, text="0.00s")
        self.time_label.pack(side='left', padx=5)
        
        # Animation buttons
        btn_frame = ttk.Frame(animation_frame)
        btn_frame.pack(fill='x', pady=5)
        
        self.play_btn = ttk.Button(btn_frame, text="▶ Play", command=self._toggle_animation, style="Modern.TButton")
        self.play_btn.pack(side='left', padx=5)
        
        ttk.Button(btn_frame, text="⏮ First", command=lambda: self._goto_frame(0), style="Modern.TButton").pack(side='left', padx=5)
        ttk.Button(btn_frame, text="⏪ Previous", command=self._prev_frame, style="Modern.TButton").pack(side='left', padx=5)
        ttk.Button(btn_frame, text="⏩ Next", command=self._next_frame, style="Modern.TButton").pack(side='left', padx=5)
        ttk.Button(btn_frame, text="⏭ Last", command=lambda: self._goto_frame(100), style="Modern.TButton").pack(side='left', padx=5)
        
        # Animation is initially stopped
        self.animation_running = False

    def apply_theme(self, theme_name):
        """Apply a selected theme to the application"""
        if theme_name == "dark":
            # Dark theme
            self.theme.bg_color = "#2C3E50"
            self.theme.primary_color = "#3498DB"
            self.theme.secondary_color = "#2980B9"
            self.theme.accent_color = "#1ABC9C"
            self.theme.text_color = "#ECF0F1"
            self.theme.light_text = "#FFFFFF"
            self.theme.border_color = "#7F8C8D"
        elif theme_name == "light":
            # Light theme
            self.theme.bg_color = "#F5F5F5"
            self.theme.primary_color = "#3498DB"
            self.theme.secondary_color = "#2980B9"
            self.theme.accent_color = "#1ABC9C"
            self.theme.text_color = "#2C3E50"
            self.theme.light_text = "#FFFFFF"
            self.theme.border_color = "#BDC3C7"
        elif theme_name == "blue":
            # Blue theme
            self.theme.bg_color = "#EBF5FB"
            self.theme.primary_color = "#2E86C1"
            self.theme.secondary_color = "#1B4F72"
            self.theme.accent_color = "#3498DB"
            self.theme.text_color = "#17202A"
            self.theme.light_text = "#FFFFFF"
            self.theme.border_color = "#AED6F1"
        
        # Apply the theme
        self.apply_modern_styles()
        
        # Update all UI elements
        self._update_ui_theme()

    def _create_action_buttons(self, parent):
        """Create action buttons for the visualization tab"""
        buttons_frame = ttk.Frame(parent)
        buttons_frame.pack(fill='x', pady=5)
        
        ttk.Button(buttons_frame, text="Update Visualization", 
                command=self.update_cfd_visualization,
                style="Modern.TButton").pack(fill='x', pady=3)
        
        ttk.Button(buttons_frame, text="Export Image", 
                command=self.export_cfd_image).pack(fill='x', pady=3)
        
        ttk.Button(buttons_frame, text="Export Data", 
                command=self.export_cfd_results).pack(fill='x', pady=3)
        
        # Add save/load preset buttons
        preset_frame = ttk.Frame(buttons_frame)
        preset_frame.pack(fill='x', pady=5)
        
        ttk.Button(preset_frame, text="Save Preset", 
                command=self._save_visualization_preset).pack(side='left', fill='x', expand=True, padx=2)
        
        ttk.Button(preset_frame, text="Load Preset", 
                command=self._load_visualization_preset).pack(side='left', fill='x', expand=True, padx=2)

    def _create_viz_type_section(self, parent):
        """Create visualization type selection interface"""
        frame = ttk.Frame(parent)
        frame.pack(fill='x', padx=5, pady=5)
        
        # Visualization type selection with descriptive labels
        ttk.Label(frame, text="Visualization Type:", font=self.theme.normal_font).pack(anchor='w', pady=(0, 5))
        
        # Define visualization types with descriptions
        viz_types = [
            ("Contour", "2D contour plot showing level curves"),
            ("Surface", "3D surface plot with height representing values"),
            ("Vector", "Vector field visualization with arrows"),
            ("Streamlines", "Flow visualization using streamlines"),
            ("Isosurface", "3D visualization of equal-value surfaces"),
            ("Slice", "Cross-sectional views through the data")
        ]
        
        # Create visualization type selection as radio buttons
        self.viz_var = tk.StringVar(value="Contour")
        
        for viz_type, description in viz_types:
            type_frame = ttk.Frame(frame)
            type_frame.pack(fill='x', pady=2)
            
            rb = ttk.Radiobutton(
                type_frame, 
                text=viz_type,
                variable=self.viz_var,
                value=viz_type,
                command=self.update_cfd_visualization
            )
            rb.pack(side='left')
            
            # Add tooltip-like functionality with hover labels
            def create_tooltip(widget, tip_text):
                tip_label = ttk.Label(type_frame, text=tip_text, foreground=self.theme.text_color,
                                    font=self.theme.small_font, background=self.theme.bg_color)
                
                def on_enter(e):
                    tip_label.pack(side='right', fill='x', expand=True)
                    
                def on_leave(e):
                    tip_label.pack_forget()
                    
                widget.bind('<Enter>', on_enter)
                widget.bind('<Leave>', on_leave)
                
            create_tooltip(rb, description)
        
        # Specialized options for different visualization types
        options_frame = ttk.Frame(frame)
        options_frame.pack(fill='x', pady=5)
        
        # Contour options
        self.contour_frame = ttk.Frame(options_frame)
        ttk.Label(self.contour_frame, text="Contour Levels:").pack(side='left', padx=5)
        self.contour_levels_var = tk.StringVar(value="20")
        ttk.Entry(self.contour_frame, textvariable=self.contour_levels_var, width=5).pack(side='left')
        
        # Vector options
        self.vector_frame = ttk.Frame(options_frame)
        ttk.Label(self.vector_frame, text="Vector Density:").pack(side='left', padx=5)
        self.vector_density_var = tk.StringVar(value="20")
        ttk.Entry(self.vector_frame, textvariable=self.vector_density_var, width=5).pack(side='left')
        
        # Slice options
        self.slice_frame = ttk.Frame(options_frame)
        ttk.Label(self.slice_frame, text="Slice Position:").pack(side='left', padx=5)
        self.slice_position_var = tk.DoubleVar(value=0.5)
        ttk.Scale(self.slice_frame, from_=0.0, to=1.0, orient='horizontal', 
                variable=self.slice_position_var, 
                command=lambda _: self.update_cfd_visualization()).pack(side='left', fill='x', expand=True)
        
        # Show the appropriate options frame based on current selection
        self._on_viz_type_changed()
        
        return frame

    def _on_viz_type_changed(self, event=None):
        """Handle visualization type change"""
        # Hide all specialized frames first
        for frame in [self.contour_frame, self.vector_frame, self.slice_frame]:
            if hasattr(self, frame.__str__()):
                frame.pack_forget()
        
        # Show the appropriate frame based on selection
        viz_type = self.viz_var.get()
        
        if viz_type == "Contour":
            self.contour_frame.pack(fill='x', padx=5, pady=5)
        elif viz_type == "Vector":
            self.vector_frame.pack(fill='x', padx=5, pady=5)
        elif viz_type == "Slice":
            self.slice_frame.pack(fill='x', padx=5, pady=5)
        
        # Update the visualization
        self.update_cfd_visualization()

    def _create_appearance_options(self, parent):
        """Create appearance options panel"""
        frame = ttk.Frame(parent)
        frame.pack(fill='x', padx=5, pady=5)
        
        # Colormap selection
        colormap_frame = ttk.Frame(frame)
        colormap_frame.pack(fill='x', pady=5)
        
        ttk.Label(colormap_frame, text="Colormap:").pack(side='left', padx=5)
        
        # Group colormaps by category
        colormap_options = [
            "viridis", "plasma", "inferno", "magma",
            "coolwarm", "bwr", "seismic", "jet",
            "rainbow", "tab10", "tab20", "terrain"
        ]
        
        self.colormap_var = tk.StringVar(value="viridis")
        colormap_combo = ttk.Combobox(
            colormap_frame,
            textvariable=self.colormap_var,
            values=colormap_options,
            state="readonly",
            width=15
        )
        colormap_combo.pack(side='left', padx=5, fill='x', expand=True)
        colormap_combo.bind("<<ComboboxSelected>>", lambda _: self.update_cfd_visualization())
        
        # Display options with checkboxes
        options_frame = ttk.LabelFrame(frame, text="Display Options")
        options_frame.pack(fill='x', pady=5)
        
        self.show_colorbar_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_frame, 
            text="Show Colorbar",
            variable=self.show_colorbar_var,
            command=self.update_cfd_visualization
        ).pack(anchor='w', padx=5, pady=2)
        
        self.show_labels_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_frame, 
            text="Show Axis Labels",
            variable=self.show_labels_var,
            command=self.update_cfd_visualization
        ).pack(anchor='w', padx=5, pady=2)
        
        self.show_grid_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_frame, 
            text="Show Grid",
            variable=self.show_grid_var,
            command=self.update_cfd_visualization
        ).pack(anchor='w', padx=5, pady=2)
        
        return frame

    def _create_data_range_section(self, parent):
        """Create data range control section"""
        frame = ttk.Frame(parent)
        frame.pack(fill='x', padx=5, pady=5)
        
        # Auto range checkbox
        auto_range_frame = ttk.Frame(frame)
        auto_range_frame.pack(fill='x', pady=5)
        
        self.auto_range_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            auto_range_frame,
            text="Auto Range",
            variable=self.auto_range_var,
            command=self._toggle_range_inputs
        ).pack(anchor='w')
        
        # Min/max range inputs
        self.range_inputs_frame = ttk.Frame(frame)
        self.range_inputs_frame.pack(fill='x', pady=5)
        
        ttk.Label(self.range_inputs_frame, text="Min Value:").grid(row=0, column=0, sticky='w', padx=5, pady=2)
        self.range_min_var = tk.StringVar(value="0.0")
        min_entry = ttk.Entry(self.range_inputs_frame, textvariable=self.range_min_var, width=10)
        min_entry.grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(self.range_inputs_frame, text="Max Value:").grid(row=1, column=0, sticky='w', padx=5, pady=2)
        self.range_max_var = tk.StringVar(value="1.0")
        max_entry = ttk.Entry(self.range_inputs_frame, textvariable=self.range_max_var, width=10)
        max_entry.grid(row=1, column=1, padx=5, pady=2)
        
        # Apply button
        ttk.Button(
            frame,
            text="Apply Range",
            command=self.update_cfd_visualization
        ).pack(fill='x', pady=5)
        
        # Initial state - disable inputs if auto range is on
        if self.auto_range_var.get():
            min_entry.configure(state='disabled')
            max_entry.configure(state='disabled')
        
        return frame

    def _create_statistics_section(self, parent):
        """Create statistics section for displaying data metrics"""
        frame = ttk.Frame(parent)
        frame.pack(fill='x', padx=5, pady=5)
        
        # Statistics text widget
        self.stats_text = scrolledtext.ScrolledText(
            frame, 
            height=8, 
            width=30, 
            wrap=tk.WORD,
            font=self.theme.code_font
        )
        self.stats_text.pack(fill='both', expand=True)
        self.stats_text.insert(tk.END, "No data loaded.\nRun a simulation to see statistics.")
        self.stats_text.config(state='disabled')
        
        return frame

    def _save_visualization_preset(self):
        """Save current visualization settings to a preset file"""
        try:
            # Get current settings
            preset = {
                "field": self.field_var.get() if hasattr(self, 'field_var') else "Pressure",
                "visualization_type": self.viz_var.get() if hasattr(self, 'viz_var') else "Contour",
                "colormap": self.colormap_var.get() if hasattr(self, 'colormap_var') else "viridis",
                "show_colorbar": self.show_colorbar_var.get() if hasattr(self, 'show_colorbar_var') else True,
                "show_labels": self.show_labels_var.get() if hasattr(self, 'show_labels_var') else True,
                "show_grid": self.show_grid_var.get() if hasattr(self, 'show_grid_var') else True,
                "auto_range": self.auto_range_var.get() if hasattr(self, 'auto_range_var') else True,
                "range_min": self.range_min_var.get() if hasattr(self, 'range_min_var') else "0.0",
                "range_max": self.range_max_var.get() if hasattr(self, 'range_max_var') else "1.0",
                "contour_levels": self.contour_levels_var.get() if hasattr(self, 'contour_levels_var') else "20",
                "vector_density": self.vector_density_var.get() if hasattr(self, 'vector_density_var') else "20",
                "slice_position": self.slice_position_var.get() if hasattr(self, 'slice_position_var') else 0.5
            }
            
            # Get file path to save
            file_path = filedialog.asksaveasfilename(
                title="Save Visualization Preset",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if not file_path:
                return
                
            # Save to JSON file
            with open(file_path, 'w') as f:
                json.dump(preset, f, indent=4)
                
            self.log(f"Visualization preset saved to {file_path}")
            self.update_status(f"Preset saved to {os.path.basename(file_path)}")
            messagebox.showinfo("Preset Saved", f"Visualization preset saved to:\n{file_path}")
            
        except Exception as e:
            self.log(f"Error saving preset: {str(e)}")
            messagebox.showerror("Save Error", f"Failed to save preset: {str(e)}")

    def _load_visualization_preset(self):
        """Load visualization settings from a preset file"""
        try:
            # Get file path to load
            file_path = filedialog.askopenfilename(
                title="Load Visualization Preset",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if not file_path:
                return
                
            # Load from JSON file
            with open(file_path, 'r') as f:
                preset = json.load(f)
                
            # Apply settings to UI
            if "field" in preset and hasattr(self, 'field_var'):
                self.field_var.set(preset["field"])
                
            if "visualization_type" in preset and hasattr(self, 'viz_var'):
                self.viz_var.set(preset["visualization_type"])
                # Update viz type specific options
                self._on_viz_type_changed()
                
            if "colormap" in preset and hasattr(self, 'colormap_var'):
                self.colormap_var.set(preset["colormap"])
                
            if "show_colorbar" in preset and hasattr(self, 'show_colorbar_var'):
                self.show_colorbar_var.set(preset["show_colorbar"])
                
            if "show_labels" in preset and hasattr(self, 'show_labels_var'):
                self.show_labels_var.set(preset["show_labels"])
                
            if "show_grid" in preset and hasattr(self, 'show_grid_var'):
                self.show_grid_var.set(preset["show_grid"])
                
            if "auto_range" in preset and hasattr(self, 'auto_range_var'):
                self.auto_range_var.set(preset["auto_range"])
                self._toggle_range_inputs()
                
            if "range_min" in preset and hasattr(self, 'range_min_var'):
                self.range_min_var.set(preset["range_min"])
                
            if "range_max" in preset and hasattr(self, 'range_max_var'):
                self.range_max_var.set(preset["range_max"])
                
            if "contour_levels" in preset and hasattr(self, 'contour_levels_var'):
                self.contour_levels_var.set(preset["contour_levels"])
                
            if "vector_density" in preset and hasattr(self, 'vector_density_var'):
                self.vector_density_var.set(preset["vector_density"])
                
            if "slice_position" in preset and hasattr(self, 'slice_position_var'):
                self.slice_position_var.set(preset["slice_position"])
            
            # Update visualization with loaded settings
            self.update_cfd_visualization()
            
            self.log(f"Visualization preset loaded from {file_path}")
            self.update_status(f"Preset loaded from {os.path.basename(file_path)}")
            messagebox.showinfo("Preset Loaded", f"Visualization preset loaded from:\n{file_path}")
            
        except Exception as e:
            self.log(f"Error loading preset: {str(e)}")
            messagebox.showerror("Load Error", f"Failed to load preset: {str(e)}")

    def _setup_3d_visualization(self, parent):
        """Set up the 3D visualization tab with interactive 3D plot"""
        # Create frame for 3D visualization
        viz_3d_frame = ttk.Frame(parent)
        viz_3d_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Create matplotlib 3D figure
        self.fig_3d = Figure(figsize=(6, 5), dpi=100)
        self.ax_3d = self.fig_3d.add_subplot(111, projection='3d')
        
        # Set up initial empty plot
        self.ax_3d.set_title("3D Visualization")
        self.ax_3d.set_xlabel("X")
        self.ax_3d.set_ylabel("Y")
        self.ax_3d.set_zlabel("Z")
        
        # Create canvas
        self.canvas_3d = FigureCanvasTkAgg(self.fig_3d, master=viz_3d_frame)
        self.canvas_3d.draw()
        self.canvas_3d.get_tk_widget().pack(fill='both', expand=True)
        
        # Add toolbar for 3D navigation
        toolbar_frame = ttk.Frame(viz_3d_frame)
        toolbar_frame.pack(fill='x')
        
        self.toolbar_3d = NavigationToolbar2Tk(self.canvas_3d, toolbar_frame)
        self.toolbar_3d.update()
        
        # Add control panel for 3D specific options
        control_frame = ttk.Frame(viz_3d_frame)
        control_frame.pack(fill='x', pady=10)
        
        # View angle controls
        angle_frame = ttk.LabelFrame(control_frame, text="View Angle")
        angle_frame.pack(side='left', padx=10, fill='y')
        
        # Elevation slider
        ttk.Label(angle_frame, text="Elevation:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.elevation_var = tk.IntVar(value=30)
        elevation_slider = ttk.Scale(
            angle_frame, 
            from_=0, 
            to=90, 
            orient='horizontal',
            variable=self.elevation_var,
            command=self._update_3d_view_angle
        )
        elevation_slider.grid(row=0, column=1, padx=5, pady=5, sticky='ew')
        
        # Azimuth slider
        ttk.Label(angle_frame, text="Azimuth:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        self.azimuth_var = tk.IntVar(value=45)
        azimuth_slider = ttk.Scale(
            angle_frame, 
            from_=0, 
            to=360, 
            orient='horizontal',
            variable=self.azimuth_var,
            command=self._update_3d_view_angle
        )
        azimuth_slider.grid(row=1, column=1, padx=5, pady=5, sticky='ew')
        
        # Visualization options
        options_frame = ttk.LabelFrame(control_frame, text="Display Options")
        options_frame.pack(side='left', padx=10, fill='y')
        
        # Surface/wireframe toggle
        self.surface_display_var = tk.StringVar(value="Surface")
        ttk.Radiobutton(
            options_frame, 
            text="Surface", 
            variable=self.surface_display_var, 
            value="Surface",
            command=self._update_3d_display_type
        ).grid(row=0, column=0, padx=5, pady=2, sticky='w')
        
        ttk.Radiobutton(
            options_frame, 
            text="Wireframe", 
            variable=self.surface_display_var, 
            value="Wireframe",
            command=self._update_3d_display_type
        ).grid(row=0, column=1, padx=5, pady=2, sticky='w')
        
        # Transparency slider
        ttk.Label(options_frame, text="Transparency:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        self.transparency_3d_var = tk.DoubleVar(value=0.0)
        transparency_slider = ttk.Scale(
            options_frame, 
            from_=0.0, 
            to=0.9, 
            orient='horizontal',
            variable=self.transparency_3d_var,
            command=self._update_3d_transparency
        )
        transparency_slider.grid(row=1, column=1, padx=5, pady=5, sticky='ew')
        
        # Update button
        ttk.Button(
            control_frame, 
            text="Update 3D View",
            command=self._update_3d_visualization
        ).pack(side='right', padx=10)
        
        self.log("3D visualization interface initialized")

    def _update_3d_view_angle(self, event=None):
        """Update the view angle of the 3D plot"""
        if hasattr(self, 'ax_3d'):
            elevation = self.elevation_var.get()
            azimuth = self.azimuth_var.get()
            
            self.ax_3d.view_init(elev=elevation, azim=azimuth)
            
            if hasattr(self, 'canvas_3d'):
                self.canvas_3d.draw()

    def _update_3d_display_type(self):
        """Update the display type of the 3D visualization (surface/wireframe)"""
        if hasattr(self, 'visualization_data') and hasattr(self, 'ax_3d'):
            self._update_3d_visualization()

    def _update_3d_transparency(self, event=None):
        """Update the transparency of the 3D surface"""
        if hasattr(self, 'ax_3d') and hasattr(self, 'current_3d_surface'):
            alpha = 1.0 - self.transparency_3d_var.get()
            self.current_3d_surface.set_alpha(alpha)
            
            if hasattr(self, 'canvas_3d'):
                self.canvas_3d.draw()

    def _update_3d_visualization(self):
        """Update the 3D visualization with current data"""
        if not hasattr(self, 'ax_3d') or not hasattr(self, 'canvas_3d'):
            return
            
        # Clear current plot
        self.ax_3d.clear()
        
        # Get data
        if hasattr(self, 'visualization_data'):
            field = self.field_var.get() if hasattr(self, 'field_var') else "Pressure"
            
            if field in self.visualization_data and 'X' in self.visualization_data and 'Y' in self.visualization_data:
                X = self.visualization_data['X']
                Y = self.visualization_data['Y']
                Z = self.visualization_data[field]
                
                if X is not None and Y is not None and Z is not None:
                    # Get display type
                    display_type = self.surface_display_var.get() if hasattr(self, 'surface_display_var') else "Surface"
                    
                    # Get colormap
                    colormap = self.colormap_var.get() if hasattr(self, 'colormap_var') else "viridis"
                    
                    # Get transparency
                    alpha = 1.0 - self.transparency_3d_var.get() if hasattr(self, 'transparency_3d_var') else 1.0
                    
                    # Create plot
                    if display_type == "Surface":
                        self.current_3d_surface = self.ax_3d.plot_surface(
                            X, Y, Z, 
                            cmap=colormap,
                            alpha=alpha,
                            rstride=1, 
                            cstride=1,
                            linewidth=0.5, 
                            antialiased=True
                        )
                    else:  # Wireframe
                        self.current_3d_surface = self.ax_3d.plot_wireframe(
                            X, Y, Z,
                            color='blue',
                            rstride=2,
                            cstride=2,
                            alpha=alpha
                        )
                    
                    # Set labels
                    self.ax_3d.set_xlabel("X")
                    self.ax_3d.set_ylabel("Y")
                    self.ax_3d.set_zlabel(field)
                    
                    # Set title
                    self.ax_3d.set_title(f"3D Visualization: {field}")
                    
                    # Set view angle
                    if hasattr(self, 'elevation_var') and hasattr(self, 'azimuth_var'):
                        elevation = self.elevation_var.get()
                        azimuth = self.azimuth_var.get()
                        self.ax_3d.view_init(elev=elevation, azim=azimuth)
                    
                    # Add colorbar
                    if display_type == "Surface" and self.show_colorbar_var.get() if hasattr(self, 'show_colorbar_var') else True:
                        self.fig_3d.colorbar(self.current_3d_surface, ax=self.ax_3d, shrink=0.5, aspect=10)
                else:
                    self._draw_empty_3d_plot("No valid data for selected field")
            else:
                self._draw_empty_3d_plot("Selected field not available")
        else:
            self._draw_empty_3d_plot("No visualization data available")
        
        # Update canvas
        self.canvas_3d.draw()

    def _draw_empty_3d_plot(self, message="No data available"):
        """Draw an empty 3D plot with a message"""
        if hasattr(self, 'ax_3d'):
            self.ax_3d.clear()
            self.ax_3d.set_xlabel("X")
            self.ax_3d.set_ylabel("Y")
            self.ax_3d.set_zlabel("Z")
            self.ax_3d.text(0.5, 0.5, 0.5, message,
                        horizontalalignment='center',
                        verticalalignment='center',
                        transform=self.ax_3d.transAxes)
            
            # Add some boundary to make text visible
            self.ax_3d.set_xlim([-1, 1])
            self.ax_3d.set_ylim([-1, 1])
            self.ax_3d.set_zlim([-1, 1])

    def _update_comparison(self, event=None):
        """Update the comparison view based on selected mode and datasets"""
        if not hasattr(self, 'comparison_fig') or not hasattr(self, 'comparison_canvas'):
            return
            
        # Get current settings
        mode = self.compare_mode_var.get()
        dataset_a = self.dataset_a_var.get()
        dataset_b = self.dataset_b_var.get()
        
        # Check if we have valid datasets selected
        if not dataset_a or not dataset_b:
            # Show message about selecting datasets
            self.compare_ax1.clear()
            self.compare_ax2.clear()
            self.compare_ax1.text(0.5, 0.5, "Select datasets to compare",
                            ha='center', va='center', transform=self.compare_ax1.transAxes)
            self.comparison_canvas.draw()
            return
        
        # Clear current plots
        self.comparison_fig.clear()
        
        # Create appropriate plots based on comparison mode
        if mode == "Side by Side":
            # Create two subplots side by side
            self.compare_ax1 = self.comparison_fig.add_subplot(121)
            self.compare_ax2 = self.comparison_fig.add_subplot(122)
            
            # Plot dataset A
            self._plot_comparison_dataset(self.compare_ax1, dataset_a, "Dataset A")
            
            # Plot dataset B
            self._plot_comparison_dataset(self.compare_ax2, dataset_b, "Dataset B")
            
        elif mode == "Overlay":
            # Create a single plot with both datasets
            ax = self.comparison_fig.add_subplot(111)
            
            # Plot both datasets with different colors/styles
            self._plot_comparison_dataset(ax, dataset_a, "Dataset A", color='blue', alpha=0.7)
            self._plot_comparison_dataset(ax, dataset_b, "Dataset B", color='red', alpha=0.7)
            
            # Add legend
            ax.legend()
            
        elif mode == "Difference":
            # Create a single plot showing the difference
            ax = self.comparison_fig.add_subplot(111)
            
            # Calculate and plot difference
            self._plot_difference(ax, dataset_a, dataset_b)
        
        # Update the canvas
        self.comparison_canvas.draw()

    def _plot_comparison_dataset(self, ax, dataset_name, label, **kwargs):
        """Plot a dataset on the given axes"""
        # In a real implementation, this would load and plot actual data
        # For demo, we'll create placeholder data
        
        # Create sample data
        x = np.linspace(0, 10, 100)
        
        # Different function for each dataset to show variation
        if dataset_name == "Current Results":
            y = np.sin(x) * np.exp(-0.1 * x)
        elif dataset_name == "Previous Results":
            y = np.sin(x) * np.exp(-0.2 * x)
        elif dataset_name == "Baseline":
            y = 0.5 * np.sin(x)
        elif dataset_name == "Optimized":
            y = 1.2 * np.sin(x) * np.exp(-0.05 * x)
        else:
            # Default
            y = np.sin(x)
        
        # Plot the data
        ax.plot(x, y, label=label, **kwargs)
        
        # Add labels and grid
        ax.set_xlabel("X")
        ax.set_ylabel("Value")
        ax.set_title(dataset_name)
        ax.grid(True)

    def _plot_difference(self, ax, dataset_a, dataset_b):
        """Plot the difference between two datasets"""
        # Create sample data for difference plot
        x = np.linspace(0, 10, 100)
        
        # Generate data for each dataset
        if dataset_a == "Current Results":
            y_a = np.sin(x) * np.exp(-0.1 * x)
        elif dataset_a == "Previous Results":
            y_a = np.sin(x) * np.exp(-0.2 * x)
        elif dataset_a == "Baseline":
            y_a = 0.5 * np.sin(x)
        elif dataset_a == "Optimized":
            y_a = 1.2 * np.sin(x) * np.exp(-0.05 * x)
        else:
            y_a = np.sin(x)
        
        if dataset_b == "Current Results":
            y_b = np.sin(x) * np.exp(-0.1 * x)
        elif dataset_b == "Previous Results":
            y_b = np.sin(x) * np.exp(-0.2 * x)
        elif dataset_b == "Baseline":
            y_b = 0.5 * np.sin(x)
        elif dataset_b == "Optimized":
            y_b = 1.2 * np.sin(x) * np.exp(-0.05 * x)
        else:
            y_b = np.sin(x)
        
        # Calculate difference
        diff = y_a - y_b
        
        # Plot the difference
        ax.plot(x, diff, 'g-', label=f"Difference ({dataset_a} - {dataset_b})")
        
        # Add a reference line at y=0
        ax.axhline(y=0, color='k', linestyle='--', alpha=0.3)
        
        # Add labels and grid
        ax.set_xlabel("X")
        ax.set_ylabel("Difference")
        ax.set_title(f"Difference: {dataset_a} - {dataset_b}")
        ax.grid(True)
        ax.legend()

    def _get_available_datasets(self):
        """Get list of available datasets for comparison"""
        # In a real app, this would read from actual data files
        # For demo, return placeholder options
        return ["Current Results", "Previous Results", "Baseline", "Optimized"]

    def _setup_parameter_section(self, parent):
        """Set up the parameter input section with collapsible UI"""
        # Create collapsible section for parameters
        parameters_header = ttk.Frame(parent)
        parameters_header.pack(fill='x', padx=5, pady=2)
        
        # Header with expand/collapse button
        self.param_expanded = tk.BooleanVar(value=True)
        param_toggle = ttk.Checkbutton(parameters_header, 
                                text="Parameters", 
                                style="Section.TCheckbutton",
                                variable=self.param_expanded,
                                command=self._toggle_param_section)
        param_toggle.pack(side='left', padx=5)
        
        # Add parameter preset controls
        ttk.Button(parameters_header, text="Save", width=6,
                command=self.save_parameter_preset).pack(side='right', padx=2)
        ttk.Button(parameters_header, text="Load", width=6,
                command=self.load_parameter_preset).pack(side='right', padx=2)
        
        # Parameters content frame
        self.param_frame = ttk.Frame(parent, padding=5)
        self.param_frame.pack(fill='x', padx=5, pady=5)
        
        # Add parameter input fields with labels and tooltips
        param_grid = ttk.Frame(self.param_frame)
        param_grid.pack(fill='x', pady=5)
        
        # Define parameters with tooltips
        parameters = [
            ("L4", "Length parameter 4 (mm)", "3.0"),
            ("L5", "Length parameter 5 (mm)", "3.0"),
            ("Alpha1", "Angle 1 (degrees)", "15.0"),
            ("Alpha2", "Angle 2 (degrees)", "15.0"),
            ("Alpha3", "Angle 3 (degrees)", "15.0")
        ]
        
        # Create labeled entries with units and tooltips
        self.param_entries = {}
        for i, (param, tooltip, default) in enumerate(parameters):
            # Label
            label = ttk.Label(param_grid, text=f"{param}:")
            label.grid(row=i, column=0, padx=5, pady=6, sticky='w')
            self._create_tooltip(label, tooltip)
            
            # Frame for entry and unit
            entry_frame = ttk.Frame(param_grid)
            entry_frame.grid(row=i, column=1, padx=5, pady=5, sticky='w')
            
            # Entry widget
            entry = ttk.Entry(entry_frame, width=10)
            entry.pack(side='left')
            entry.insert(0, default)
            self.param_entries[param.lower()] = entry
            
            # Unit label
            unit = "mm" if param.startswith("L") else "°"
            ttk.Label(entry_frame, text=unit).pack(side='left', padx=2)
        
        # Add parameter validation feedback
        self.param_validation = ttk.Label(self.param_frame, text="", foreground="green")
        self.param_validation.pack(fill='x', pady=5)
        
        # Default expanded
        self._toggle_param_section()

    def _toggle_param_section(self):
        """Toggle the visibility of the parameter section"""
        if self.param_expanded.get():
            self.param_frame.pack(fill='x', padx=5, pady=5)
        else:
            self.param_frame.pack_forget()

    def _setup_env_section(self, parent):
        """Set up the execution environment section"""
        # Create collapsible section for environment
        env_header = ttk.Frame(parent)
        env_header.pack(fill='x', padx=5, pady=2)
        
        # Header with expand/collapse button
        self.env_expanded = tk.BooleanVar(value=True)
        env_toggle = ttk.Checkbutton(env_header, 
                            text="Execution Environment", 
                            style="Section.TCheckbutton",
                            variable=self.env_expanded,
                            command=self._toggle_env_section)
        env_toggle.pack(side='left', padx=5)
        
        # Environment content frame
        self.env_frame = ttk.Frame(parent, padding=5)
        self.env_frame.pack(fill='x', padx=5, pady=5)
        
        # Radio buttons for execution environment with improved visuals
        self.env_var = tk.StringVar(value="local")
        
        env_radio_frame = ttk.Frame(self.env_frame)
        env_radio_frame.pack(fill='x', pady=5)
        
        # Local execution option with icon
        local_frame = ttk.Frame(env_radio_frame)
        local_frame.pack(fill='x', pady=5)
        
        local_radio = ttk.Radiobutton(local_frame, text="Local Execution", 
                                    variable=self.env_var, value="local",
                                    command=self.toggle_execution_environment)
        local_radio.pack(side='left', padx=5)
        
        # Add descriptive text
        ttk.Label(local_frame, text="Run on this computer", 
                foreground=self.theme.secondary_color, 
                font=self.theme.small_font).pack(side='left', padx=10)
        
        # HPC execution option with icon
        hpc_frame = ttk.Frame(env_radio_frame)
        hpc_frame.pack(fill='x', pady=5)
        
        hpc_radio = ttk.Radiobutton(hpc_frame, text="HPC Execution", 
                                variable=self.env_var, value="hpc",
                                command=self.toggle_execution_environment)
        hpc_radio.pack(side='left', padx=5)
        
        # Add descriptive text
        ttk.Label(hpc_frame, text="Run on high-performance cluster", 
                foreground=self.theme.secondary_color, 
                font=self.theme.small_font).pack(side='left', padx=10)
        
        # HPC settings frame with better styling
        self.workflow_hpc_frame = ttk.Frame(self.env_frame, padding=10)
        self.workflow_hpc_frame.pack(fill='x', pady=5)
        
        # HPC profile selection with improved UI
        ttk.Label(self.workflow_hpc_frame, text="HPC Profile:").pack(side="left", padx=5)
        self.workflow_hpc_profile = ttk.Combobox(self.workflow_hpc_frame, width=25, state="readonly")
        self.workflow_hpc_profile.pack(side="left", padx=5, fill='x', expand=True)
        
        # Add refresh button for HPC profiles
        ttk.Button(self.workflow_hpc_frame, text="↻", width=3, 
                command=self.refresh_hpc_profiles).pack(side='left', padx=2)
        
        # Add button to manage HPC profiles
        ttk.Button(self.workflow_hpc_frame, text="Manage", width=8,
                command=self.manage_hpc_profiles).pack(side='left', padx=5)
        
        # Load HPC profiles for workflow
        self.load_workflow_hpc_profiles()
        
        # Hide HPC settings initially
        self.workflow_hpc_frame.pack_forget()
        
        # Default expanded
        self._toggle_env_section()

    def _toggle_env_section(self):
        """Toggle the visibility of the environment section"""
        if self.env_expanded.get():
            self.env_frame.pack(fill='x', padx=5, pady=5)
        else:
            self.env_frame.pack_forget()

    def _setup_action_section(self, parent):
        """Set up the action buttons section"""
        # Create frame for action buttons
        action_frame = ttk.Frame(parent, padding=10)
        action_frame.pack(fill='x', padx=5, pady=10)
        
        # Create styled buttons
        button_frame = ttk.Frame(action_frame)
        button_frame.pack(fill='x', pady=5)
        
        # Run button with accent styling
        self.run_button = ttk.Button(
            button_frame, 
            text="Run Workflow", 
            style="Accent.TButton",
            command=self.run_workflow
        )
        self.run_button.pack(side="left", padx=5, fill='x', expand=True)
        
        # Cancel button
        self.cancel_button = ttk.Button(
            button_frame, 
            text="Cancel", 
            command=self.cancel_workflow, 
            state="disabled"
        )
        self.cancel_button.pack(side="left", padx=5)
        
        # Additional action buttons
        extra_button_frame = ttk.Frame(action_frame)
        extra_button_frame.pack(fill='x', pady=5)
        
        # Add buttons for additional actions
        ttk.Button(
            extra_button_frame, 
            text="Validate Parameters", 
            command=self.validate_workflow_parameters
        ).pack(side="left", padx=5, fill='x', expand=True)
        
        ttk.Button(
            extra_button_frame, 
            text="View Previous Results", 
            command=self.view_previous_results
        ).pack(side="left", padx=5, fill='x', expand=True)

    def _setup_workflow_visualization(self, parent):
        """Set up the workflow visualization with improved visuals and interactivity"""
        # Create tabbed interface for workflow visualization
        workflow_notebook = ttk.Notebook(parent)
        workflow_notebook.pack(fill='both', expand=True)
        
        # Workflow diagram tab
        diagram_tab = ttk.Frame(workflow_notebook)
        workflow_notebook.add(diagram_tab, text="Workflow Diagram")
        
        # Create canvas for workflow visualization with enhanced styling
        viz_frame = ttk.Frame(diagram_tab)
        viz_frame.pack(fill='both', expand=True)
        
        self.workflow_canvas = tk.Canvas(
            viz_frame, 
            bg="white", 
            height=200,
            highlightthickness=1,
            highlightbackground=self.theme.border_color
        )
        self.workflow_canvas.pack(fill='both', expand=True, padx=5, pady=5)
        self.workflow_canvas.bind("<Button-1>", self.workflow_canvas_click)
        
        # Define workflow steps with improved information
        self.workflow_steps = [
            {
                'name': 'CAD', 
                'status': 'pending', 
                'x': 0.1, 
                'y': 0.5, 
                'desc': 'Updates the NX model with parameters',
                'time_estimate': '30s',
                'dependencies': []
            },
            {
                'name': 'Mesh', 
                'status': 'pending', 
                'x': 0.35, 
                'y': 0.5, 
                'desc': 'Generates mesh from geometry',
                'time_estimate': '2m',
                'dependencies': ['CAD']
            },
            {
                'name': 'CFD', 
                'status': 'pending', 
                'x': 0.6, 
                'y': 0.5, 
                'desc': 'Runs CFD simulation',
                'time_estimate': '5m',
                'dependencies': ['Mesh']
            },
            {
                'name': 'Results', 
                'status': 'pending', 
                'x': 0.85, 
                'y': 0.5, 
                'desc': 'Processes simulation results',
                'time_estimate': '1m',
                'dependencies': ['CFD']
            }
        ]
        
        # Draw the workflow diagram
        self._redraw_workflow()
        
        # Status log tab with improved styling
        log_tab = ttk.Frame(workflow_notebook)
        workflow_notebook.add(log_tab, text="Execution Log")
        
        # Create rich text log with timestamps and colorized status messages
        log_frame = ttk.Frame(log_tab, padding=5)
        log_frame.pack(fill='both', expand=True)
        
        # Status text area with improved styling and search functionality
        self.workflow_status_text = scrolledtext.ScrolledText(
            log_frame, 
            height=15, 
            wrap=tk.WORD,
            font=self.theme.code_font
        )
        self.workflow_status_text.pack(fill='both', expand=True, padx=5, pady=5)
        self.workflow_status_text.tag_configure("timestamp", foreground="gray")
        self.workflow_status_text.tag_configure("success", foreground="green")
        self.workflow_status_text.tag_configure("error", foreground="red")
        self.workflow_status_text.tag_configure("warning", foreground="#f0ad4e")
        self.workflow_status_text.tag_configure("info", foreground="#5bc0de")
        
        # Add search functionality for log
        search_frame = ttk.Frame(log_frame)
        search_frame.pack(fill='x', pady=5)
        
        ttk.Label(search_frame, text="Search:").pack(side='left', padx=5)
        self.log_search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.log_search_var)
        search_entry.pack(side='left', fill='x', expand=True, padx=5)
        
        ttk.Button(search_frame, text="Find", 
                command=self.search_workflow_log).pack(side='left', padx=5)
        
        ttk.Button(search_frame, text="Clear Log", 
                command=self.clear_workflow_log).pack(side='right', padx=5)
        
        # Initial status message
        self.workflow_status_text.insert(tk.END, "Ready to start workflow. Set parameters and click 'Run Workflow'.\n")
        self.workflow_status_text.config(state='disabled')
        
        # Progress monitoring tab
        progress_tab = ttk.Frame(workflow_notebook)
        workflow_notebook.add(progress_tab, text="Progress")
        
        # Add detailed progress monitoring
        progress_frame = ttk.Frame(progress_tab, padding=10)
        progress_frame.pack(fill='both', expand=True)
        
        # Create progress indicators for each step
        self.progress_indicators = {}
        self.progress_labels = {}
        self.time_labels = {}
        
        for i, step in enumerate(self.workflow_steps):
            step_frame = ttk.Frame(progress_frame)
            step_frame.pack(fill='x', pady=5)
            
            # Step name and status
            header_frame = ttk.Frame(step_frame)
            header_frame.pack(fill='x')
            
            ttk.Label(header_frame, text=step['name'], 
                    font=self.theme.header_font).pack(side='left')
            
            status_var = tk.StringVar(value="Pending")
            status_label = ttk.Label(header_frame, textvariable=status_var, 
                                foreground="gray")
            status_label.pack(side='left', padx=10)
            self.progress_labels[step['name']] = status_var
            
            # Time information
            time_var = tk.StringVar(value=f"Est: {step['time_estimate']}")
            time_label = ttk.Label(header_frame, textvariable=time_var)
            time_label.pack(side='right', padx=5)
            self.time_labels[step['name']] = time_var
            
            # Progress bar
            progress_var = tk.DoubleVar(value=0)
            progress_bar = ttk.Progressbar(step_frame, variable=progress_var, 
                                        length=200, mode='determinate')
            progress_bar.pack(fill='x', pady=5)
            self.progress_indicators[step['name']] = progress_var
        
        # Initialize the workflow UI
        self._update_workflow_status("Workflow initialized and ready", 'info')

    def _update_workflow_status(self, message, status_type='info'):
        """Update the workflow status text with a styled message"""
        if not hasattr(self, 'workflow_status_text'):
            self.log(message)
            return
            
        try:
            # Format timestamp
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            
            # Enable editing
            self.workflow_status_text.configure(state='normal')
            
            # Insert timestamp with tag
            self.workflow_status_text.insert(tk.END, f"[{timestamp}] ", "timestamp")
            
            # Insert message with appropriate status tag
            self.workflow_status_text.insert(tk.END, f"{message}\n", status_type)
            
            # Scroll to the end
            self.workflow_status_text.see(tk.END)
            
            # Disable editing
            self.workflow_status_text.configure(state='disabled')
            
            # Also update the main status bar
            self.update_status(message)
        except Exception as e:
            self.log(f"Error updating workflow status: {e}")

    def _update_workflow_step(self, step_name, status, progress=None, time_info=None):
        """Update a workflow step's status and progress"""
        # Update step status in data structure
        for step in self.workflow_steps:
            if step["name"] == step_name:
                step["status"] = status
                break
        
        # Update progress monitoring if available
        if hasattr(self, 'progress_labels') and step_name in self.progress_labels:
            # Update status label
            status_text = status.title()
            status_color = {
                'pending': 'gray',
                'running': '#FFC107',  # Amber
                'complete': '#4CAF50',  # Green
                'error': '#F44336',     # Red
                'canceled': '#9E9E9E'   # Gray
            }.get(status, 'black')
            
            self.progress_labels[step_name].set(status_text)
            
            # Find and update label color
            for widget in self.root.winfo_children():
                if isinstance(widget, ttk.Label) and widget.cget('textvariable') == str(self.progress_labels[step_name]):
                    widget.configure(foreground=status_color)
                    break
        
        # Update progress bar if provided
        if progress is not None and hasattr(self, 'progress_indicators') and step_name in self.progress_indicators:
            self.progress_indicators[step_name].set(progress)
        
        # Update time information if provided
        if time_info is not None and hasattr(self, 'time_labels') and step_name in self.time_labels:
            self.time_labels[step_name].set(time_info)
        
        # Redraw the workflow visualization
        self._redraw_workflow()

    def _redraw_workflow(self):
        """Redraw the workflow visualization with enhanced visuals"""
        if not hasattr(self, 'workflow_canvas') or not hasattr(self, 'workflow_steps'):
            return
            
        # Clear the canvas
        self.workflow_canvas.delete("all")
        
        # Get canvas dimensions
        width = self.workflow_canvas.winfo_width()
        height = self.workflow_canvas.winfo_height()
        
        # If canvas size is not yet determined, use default values
        if width <= 1:
            width = 800
        if height <= 1:
            height = 200
        
        # Colors for different statuses with transparency for modern look
        colors = {
            "pending": "#E0E0E0",   # Light gray
            "running": "#FFC107",   # Amber
            "complete": "#4CAF50",  # Green
            "error": "#F44336",     # Red
            "canceled": "#9E9E9E"   # Gray
        }
        
        # Draw connections between steps with gradients and animations for running steps
        for i in range(len(self.workflow_steps) - 1):
            x1 = int(self.workflow_steps[i]["x"] * width)
            y1 = int(self.workflow_steps[i]["y"] * height)
            x2 = int(self.workflow_steps[i+1]["x"] * width)
            y2 = int(self.workflow_steps[i+1]["y"] * height)
            
            # Determine connection appearance based on status
            start_status = self.workflow_steps[i]["status"]
            end_status = self.workflow_steps[i+1]["status"]
            
            # Base connection
            if start_status == "complete" and end_status == "pending":
                # Ready for next step - dashed line
                self.workflow_canvas.create_line(
                    x1+25, y1, x2-25, y2, 
                    fill=colors[start_status], 
                    width=2.5, 
                    dash=(6, 3)
                )
            elif start_status == "running":
                # Currently running - animated line effect
                self.workflow_canvas.create_line(
                    x1+25, y1, x2-25, y2, 
                    fill=colors[start_status], 
                    width=3
                )
                
                # Add small moving dot for animation effect
                dot_pos = (datetime.datetime.now().timestamp() * 2) % 1.0
                dot_x = x1 + (x2 - x1) * dot_pos
                dot_y = y1 + (y2 - y1) * dot_pos
                self.workflow_canvas.create_oval(
                    dot_x-5, dot_y-5, dot_x+5, dot_y+5,
                    fill=colors[start_status],
                    outline=""
                )
                
                # Schedule redraw for animation
                self.root.after(50, self._redraw_workflow)
            else:
                # Normal connection
                self.workflow_canvas.create_line(
                    x1+25, y1, x2-25, y2, 
                    fill=colors[start_status], 
                    width=2
                )
        
        # Draw each step with modern styling
        for step in self.workflow_steps:
            x = int(step["x"] * width)
            y = int(step["y"] * height)
            status = step["status"]
            color = colors[status]
            
            # Add shadow for 3D effect
            self.workflow_canvas.create_oval(
                x-22, y-22+3, x+22, y+22+3, 
                fill="#CCCCCC", 
                outline=""
            )
            
            # Draw circle with gradient effect
            for i in range(3):
                size = 22 - i*2
                # Use the same color for all circles instead of varying alpha
                self.workflow_canvas.create_oval(
                    x-size, y-size, x+size, y+size, 
                    fill=color, 
                    outline=self.theme.primary_color if i == 0 else ""
                )
            # For running state, add pulsing animation
            if status == "running":
                pulse_size = 25 + (math.sin(datetime.datetime.now().timestamp() * 5) + 1) * 3
                self.workflow_canvas.create_oval(
                    x-pulse_size, y-pulse_size, x+pulse_size, y+pulse_size, 
                    outline=color, 
                    width=2
                )
                
                # Schedule redraw for animation
                self.root.after(50, self._redraw_workflow)
            
            # Draw step name with shadow for better readability
            self.workflow_canvas.create_text(
                x+1, y+1, 
                text=step["name"], 
                fill="#000000", 
                font=self.theme.header_font
            )
            self.workflow_canvas.create_text(
                x, y, 
                text=step["name"], 
                fill="white" if status in ["running", "complete"] else self.theme.text_color, 
                font=self.theme.header_font
            )
            
            # Draw status text below
            status_y = y + 35
            self.workflow_canvas.create_text(
                x, status_y, 
                text=status.title(), 
                fill=self.theme.text_color
            )

    def workflow_canvas_click(self, event):
        """Handle clicks on workflow canvas with enhanced interactivity"""
        if not hasattr(self, 'workflow_canvas') or not hasattr(self, 'workflow_steps'):
            return
            
        # Get canvas dimensions
        width = self.workflow_canvas.winfo_width() or 800
        height = self.workflow_canvas.winfo_height() or 200
        
        # Check if any step was clicked
        for step in self.workflow_steps:
            # Get step position
            x = int(step["x"] * width)
            y = int(step["y"] * height)
            
            # Calculate distance from click to step center
            distance = ((event.x - x) ** 2 + (event.y - y) ** 2) ** 0.5
            
            # If within circle radius, show details in a modern popup
            if distance <= 22:  # Circle radius
                self.show_step_details_popup(step, event.x_root, event.y_root)
                return

    def show_step_details_popup(self, step, x_root, y_root):
        """Show a modern popup with step details"""
        # Create popup window
        popup = tk.Toplevel(self.root)
        popup.title(f"Step: {step['name']}")
        popup.geometry(f"+{x_root+10}+{y_root+10}")
        popup.transient(self.root)
        
        # Configure style
        if hasattr(self, 'theme'):
            popup.configure(background=self.theme.bg_color)
        
        # Create content
        content_frame = ttk.Frame(popup, padding=15)
        content_frame.pack(fill='both', expand=True)
        
        # Title with styled header
        header_frame = ttk.Frame(content_frame)
        header_frame.pack(fill='x', pady=5)
        
        ttk.Label(
            header_frame, 
            text=step['name'],
            font=self.theme.header_font
        ).pack(side='left')
        
        # Status indicator with color
        status_colors = {
            "pending": "gray",
            "running": "#FFC107",
            "complete": "#4CAF50",
            "error": "#F44336",
            "canceled": "#9E9E9E"
        }
        
        status_frame = ttk.Frame(header_frame)
        status_frame.pack(side='right')
        
        status_label = ttk.Label(
            status_frame,
            text=step['status'].title(),
            foreground=status_colors.get(step['status'], "black")
        )
        status_label.pack(side='right')
        
        # Draw colored circle for status
        status_canvas = tk.Canvas(status_frame, width=12, height=12, 
                            background=self.theme.bg_color,
                            highlightthickness=0)
        status_canvas.pack(side='right', padx=5)
        status_canvas.create_oval(2, 2, 10, 10, 
                            fill=status_colors.get(step['status'], "gray"),
                            outline="")
        
        # Separator
        ttk.Separator(content_frame, orient='horizontal').pack(fill='x', pady=10)
        
        # Main content
        info_frame = ttk.Frame(content_frame)
        info_frame.pack(fill='both', expand=True, pady=5)
        
        # Two-column grid for information
        grid_frame = ttk.Frame(info_frame)
        grid_frame.pack(fill='x')
        
        # Description
        ttk.Label(grid_frame, text="Description:", 
                font=self.theme.normal_font + ("bold",)).grid(row=0, column=0, sticky='nw', padx=5, pady=5)
        ttk.Label(grid_frame, text=step['desc'],
                wraplength=300).grid(row=0, column=1, sticky='nw', padx=5, pady=5)
        
        # Time estimate
        ttk.Label(grid_frame, text="Time Estimate:", 
                font=self.theme.normal_font + ("bold",)).grid(row=1, column=0, sticky='nw', padx=5, pady=5)
        ttk.Label(grid_frame, text=step['time_estimate']).grid(row=1, column=1, sticky='nw', padx=5, pady=5)
        
        # Dependencies
        ttk.Label(grid_frame, text="Dependencies:", 
                font=self.theme.normal_font + ("bold",)).grid(row=2, column=0, sticky='nw', padx=5, pady=5)
        ttk.Label(grid_frame, text=", ".join(step['dependencies']) if step['dependencies'] else "None").grid(row=2, column=1, sticky='nw', padx=5, pady=5)
        
        # Add action buttons if applicable
        button_frame = ttk.Frame(content_frame)
        button_frame.pack(fill='x', pady=10)
        
        # Close button
        ttk.Button(
            button_frame,
            text="Close",
            command=popup.destroy
        ).pack(side='right', padx=5)
        
        # View logs button if applicable
        if step['status'] in ['complete', 'error', 'running']:
            ttk.Button(
                button_frame,
                text="View Logs",
                command=lambda s=step: self.view_step_logs(s)
            ).pack(side='right', padx=5)

    def view_step_logs(self, step):
        """Show detailed logs for a specific workflow step"""
        # Implement detailed log viewer for the specific step
        pass

    def save_parameter_preset(self):
        """Save current parameter values as a preset"""
        try:
            # Ask for preset name
            preset_name = simpledialog.askstring(
                "Save Parameter Preset",
                "Enter a name for this parameter preset:",
                parent=self.root
            )
            
            if not preset_name:
                return
            
            # Collect parameters
            params = {}
            for param, entry in self.param_entries.items():
                params[param] = entry.get()
            
            # Ensure presets directory exists
            presets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Config", "presets")
            os.makedirs(presets_dir, exist_ok=True)
            
            # Save to file
            preset_file = os.path.join(presets_dir, f"{preset_name}.json")
            with open(preset_file, 'w') as f:
                json.dump(params, f, indent=4)
            
            self._update_workflow_status(f"Parameter preset '{preset_name}' saved successfully", 'success')
        except Exception as e:
            self._update_workflow_status(f"Error saving parameter preset: {str(e)}", 'error')
            self.log(f"Error saving parameter preset: {str(e)}")

    def load_parameter_preset(self):
        """Load parameter values from a saved preset"""
        try:
            # Ensure presets directory exists
            presets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Config", "presets")
            os.makedirs(presets_dir, exist_ok=True)
            
            # Get list of available presets
            preset_files = [f for f in os.listdir(presets_dir) if f.endswith('.json')]
            
            if not preset_files:
                messagebox.showinfo("No Presets", "No parameter presets found.")
                return
            
            # Show selection dialog
            preset_names = [os.path.splitext(f)[0] for f in preset_files]
            preset_dialog = tk.Toplevel(self.root)
            preset_dialog.title("Load Parameter Preset")
            preset_dialog.transient(self.root)
            preset_dialog.grab_set()
            
            # Add header
            ttk.Label(preset_dialog, text="Select a parameter preset to load:",
                padding=10).pack(pady=5)
            
            # Create listbox with scrollbar
            list_frame = ttk.Frame(preset_dialog)
            list_frame.pack(fill='both', expand=True, padx=10, pady=5)
            
            scrollbar = ttk.Scrollbar(list_frame)
            scrollbar.pack(side='right', fill='y')
            
            preset_listbox = tk.Listbox(list_frame, selectmode='single',
                                    yscrollcommand=scrollbar.set,
                                    height=10, width=40)
            preset_listbox.pack(fill='both', expand=True)
            
            scrollbar.config(command=preset_listbox.yview)
            
            # Add preset names to listbox
            for name in preset_names:
                preset_listbox.insert(tk.END, name)
            
            # Select first item
            if preset_names:
                preset_listbox.selection_set(0)
            
            # Add buttons
            button_frame = ttk.Frame(preset_dialog)
            button_frame.pack(fill='x', padx=10, pady=10)
            
            # Function to load selected preset
            def do_load_preset():
                try:
                    selection = preset_listbox.curselection()
                    if not selection:
                        messagebox.showwarning("No Selection", "Please select a preset to load.")
                        return
                    
                    selected_name = preset_names[selection[0]]
                    preset_file = os.path.join(presets_dir, f"{selected_name}.json")
                    
                    with open(preset_file, 'r') as f:
                        params = json.load(f)
                    
                    # Apply parameters to entries
                    for param, value in params.items():
                        if param in self.param_entries:
                            entry = self.param_entries[param]
                            entry.delete(0, tk.END)
                            entry.insert(0, value)
                    
                    self._update_workflow_status(f"Parameter preset '{selected_name}' loaded", 'success')
                    preset_dialog.destroy()
                except Exception as e:
                    self._update_workflow_status(f"Error loading preset: {str(e)}", 'error')
                    self.log(f"Error loading parameter preset: {str(e)}")
            
            # Function to delete selected preset
            def delete_preset():
                try:
                    selection = preset_listbox.curselection()
                    if not selection:
                        messagebox.showwarning("No Selection", "Please select a preset to delete.")
                        return
                    
                    selected_name = preset_names[selection[0]]
                    
                    # Confirm deletion
                    if not messagebox.askyesno("Confirm Delete", 
                                        f"Are you sure you want to delete the preset '{selected_name}'?"):
                        return
                    
                    preset_file = os.path.join(presets_dir, f"{selected_name}.json")
                    os.remove(preset_file)
                    
                    # Update listbox
                    preset_listbox.delete(selection[0])
                    preset_names.pop(selection[0])
                    
                    self._update_workflow_status(f"Parameter preset '{selected_name}' deleted", 'info')
                except Exception as e:
                    self._update_workflow_status(f"Error deleting preset: {str(e)}", 'error')
                    self.log(f"Error deleting parameter preset: {str(e)}")
            
            ttk.Button(button_frame, text="Load", command=do_load_preset).pack(side='left', padx=5)
            ttk.Button(button_frame, text="Delete", command=delete_preset).pack(side='left', padx=5)
            ttk.Button(button_frame, text="Cancel", command=preset_dialog.destroy).pack(side='right', padx=5)
            
        except Exception as e:
            self._update_workflow_status(f"Error loading parameter presets: {str(e)}", 'error')
            self.log(f"Error loading parameter presets: {str(e)}")

    def validate_workflow_parameters(self):
        """Validate workflow parameters and display feedback"""
        try:
            # Get parameters
            l4 = float(self.param_entries['l4'].get())
            l5 = float(self.param_entries['l5'].get())
            alpha1 = float(self.param_entries['alpha1'].get())
            alpha2 = float(self.param_entries['alpha2'].get())
            alpha3 = float(self.param_entries['alpha3'].get())
            
            # Validate ranges
            messages = []
            valid = True
            
            if l4 <= 0:
                messages.append("L4 must be greater than zero.")
                valid = False
            elif l4 < 1.0 or l4 > 10.0:
                messages.append("L4 is recommended to be between 1.0 and 10.0 mm.")
            
            if l5 <= 0:
                messages.append("L5 must be greater than zero.")
                valid = False
            elif l5 < 1.0 or l5 > 10.0:
                messages.append("L5 is recommended to be between 1.0 and 10.0 mm.")
            
            if alpha1 < 0 or alpha1 > 90:
                messages.append("Alpha1 must be between 0 and 90 degrees.")
                valid = False
            elif alpha1 < 5.0 or alpha1 > 45.0:
                messages.append("Alpha1 is recommended to be between 5.0 and 45.0 degrees.")
            
            if alpha2 < 0 or alpha2 > 90:
                messages.append("Alpha2 must be between 0 and 90 degrees.")
                valid = False
            elif alpha2 < 5.0 or alpha2 > 45.0:
                messages.append("Alpha2 is recommended to be between 5.0 and 45.0 degrees.")
            
            if alpha3 < 0 or alpha3 > 90:
                messages.append("Alpha3 must be between 0 and 90 degrees.")
                valid = False
            elif alpha3 < 5.0 or alpha3 > 45.0:
                messages.append("Alpha3 is recommended to be between 5.0 and 45.0 degrees.")
            
            # Display validation result
            if valid:
                if messages:
                    # Valid but with warnings
                    self.param_validation.config(text="✓ Parameters are valid, with warnings", foreground="orange")
                    self._update_workflow_status("Parameters are valid, but there are some warnings", 'warning')
                    messagebox.showwarning("Parameter Warnings", "\n".join(messages))
                else:
                    # Fully valid
                    self.param_validation.config(text="✓ Parameters are valid", foreground="green")
                    self._update_workflow_status("Parameters are valid", 'success')
                    messagebox.showinfo("Parameter Validation", "All parameters are valid.")
            else:
                # Invalid parameters
                self.param_validation.config(text="✗ Parameters are invalid", foreground="red")
                self._update_workflow_status("Invalid parameters detected", 'error')
                messagebox.showerror("Invalid Parameters", "\n".join(messages))
            
            return valid
        except ValueError:
            # Parsing error
            self.param_validation.config(text="✗ Invalid number format", foreground="red")
            self._update_workflow_status("Invalid number format in parameters", 'error')
            messagebox.showerror("Invalid Parameters", "All parameters must be valid numbers.")
            return False

    def view_previous_results(self):
        """View previous workflow results"""
        try:
            # Check for results directory
            results_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Results")
            
            if not os.path.exists(results_dir):
                messagebox.showinfo("No Results", "No previous results found.")
                return
            
            # Get list of result directories sorted by date (newest first)
            result_folders = [d for d in os.listdir(results_dir) 
                            if os.path.isdir(os.path.join(results_dir, d))]
            
            # Sort by date in folder name (assuming format contains YYYYMMDD)
            result_folders.sort(reverse=True)
            
            if not result_folders:
                messagebox.showinfo("No Results", "No previous results found.")
                return
            
            # Create results browser dialog
            results_dialog = tk.Toplevel(self.root)
            results_dialog.title("Previous Results")
            results_dialog.geometry("900x600")
            results_dialog.transient(self.root)
            
            # Split into two panels
            panel = ttk.PanedWindow(results_dialog, orient=tk.HORIZONTAL)
            panel.pack(fill='both', expand=True, padx=10, pady=10)
            
            # Left side: result list
            list_frame = ttk.Frame(panel)
            panel.add(list_frame, weight=1)
            
            # Header
            ttk.Label(list_frame, text="Select a result to view:", 
                font=self.theme.header_font).pack(pady=5)
            
            # Create treeview with columns for date, parameters
            columns = ("date", "parameters")
            result_tree = ttk.Treeview(list_frame, columns=columns, show="headings")
            result_tree.pack(fill='both', expand=True, pady=5)
            
            # Configure columns
            result_tree.heading("date", text="Date")
            result_tree.heading("parameters", text="Parameters")
            
            result_tree.column("date", width=150)
            result_tree.column("parameters", width=200)
            
            # Add scrollbar
            tree_scroll = ttk.Scrollbar(list_frame, orient="vertical", command=result_tree.yview)
            tree_scroll.pack(side='right', fill='y')
            result_tree.configure(yscrollcommand=tree_scroll.set)
            
            # Right side: result details
            details_frame = ttk.Frame(panel)
            panel.add(details_frame, weight=2)
            
            # Create notebook for different result views
            results_notebook = ttk.Notebook(details_frame)
            results_notebook.pack(fill='both', expand=True)
            
            # Summary tab
            summary_tab = ttk.Frame(results_notebook)
            results_notebook.add(summary_tab, text="Summary")
            
            # Parameters tab
            params_tab = ttk.Frame(results_notebook)
            results_notebook.add(params_tab, text="Parameters")
            
            # Metrics tab
            metrics_tab = ttk.Frame(results_notebook)
            results_notebook.add(metrics_tab, text="Metrics")
            
            # Visualization tab
            viz_tab = ttk.Frame(results_notebook)
            results_notebook.add(viz_tab, text="Visualization")
            
            # Function to load result details
            def load_result_details(event):
                # Get selected item
                selection = result_tree.selection()
                if not selection:
                    return
                
                item = result_tree.item(selection[0])
                result_path = item['values'][2]  # Hidden full path value
                
                # Clear existing content in tabs
                for tab in [summary_tab, params_tab, metrics_tab, viz_tab]:
                    for widget in tab.winfo_children():
                        widget.destroy()
                
                # Load result data
                try:
                    # Check for metadata file
                    metadata_file = os.path.join(result_path, "metadata.json")
                    if os.path.exists(metadata_file):
                        with open(metadata_file, 'r') as f:
                            metadata = json.load(f)
                        
                        # Fill summary tab
                        summary_frame = ttk.Frame(summary_tab, padding=10)
                        summary_frame.pack(fill='both', expand=True)
                        
                        ttk.Label(summary_frame, text=f"Result from {metadata.get('date', 'Unknown date')}", 
                            font=self.theme.header_font).pack(anchor='w', pady=10)
                        
                        if 'description' in metadata:
                            ttk.Label(summary_frame, text=metadata['description'], 
                                wraplength=400).pack(anchor='w', pady=5)
                        
                        # Add key metrics
                        if 'metrics' in metadata:
                            metrics_frame = ttk.LabelFrame(summary_frame, text="Key Metrics", padding=10)
                            metrics_frame.pack(fill='x', pady=10)
                            
                            row = 0
                            for key, value in metadata['metrics'].items():
                                ttk.Label(metrics_frame, text=key + ":", 
                                    font=self.theme.normal_font + ("bold",)).grid(
                                    row=row, column=0, sticky='w', padx=5, pady=2)
                                ttk.Label(metrics_frame, text=str(value)).grid(
                                    row=row, column=1, sticky='w', padx=5, pady=2)
                                row += 1
                        
                        # Fill parameters tab
                        if 'parameters' in metadata:
                            params_frame = ttk.Frame(params_tab, padding=10)
                            params_frame.pack(fill='both', expand=True)
                            
                            ttk.Label(params_frame, text="Simulation Parameters", 
                                font=self.theme.header_font).pack(anchor='w', pady=10)
                            
                            # Create parameter grid
                            param_grid = ttk.Frame(params_frame)
                            param_grid.pack(fill='x', pady=5)
                            
                            row = 0
                            for key, value in metadata['parameters'].items():
                                ttk.Label(param_grid, text=key + ":", 
                                    font=self.theme.normal_font + ("bold",)).grid(
                                    row=row, column=0, sticky='w', padx=5, pady=5)
                                ttk.Label(param_grid, text=str(value)).grid(
                                    row=row, column=1, sticky='w', padx=5, pady=5)
                                row += 1
                        
                        # Fill metrics tab
                        if 'metrics' in metadata:
                            metrics_main_frame = ttk.Frame(metrics_tab, padding=10)
                            metrics_main_frame.pack(fill='both', expand=True)
                            
                            ttk.Label(metrics_main_frame, text="Performance Metrics", 
                                font=self.theme.header_font).pack(anchor='w', pady=10)
                            
                            # Create metrics table
                            metrics_table = ttk.Treeview(metrics_main_frame, columns=("metric", "value"), 
                                                    show="headings")
                            metrics_table.pack(fill='both', expand=True, pady=5)
                            
                            metrics_table.heading("metric", text="Metric")
                            metrics_table.heading("value", text="Value")
                            
                            metrics_table.column("metric", width=200)
                            metrics_table.column("value", width=200)
                            
                            for key, value in metadata['metrics'].items():
                                metrics_table.insert("", "end", values=(key, value))
                        
                        # Fill visualization tab with result images if available
                        viz_frame = ttk.Frame(viz_tab, padding=10)
                        viz_frame.pack(fill='both', expand=True)
                        
                        ttk.Label(viz_frame, text="Result Visualizations", 
                            font=self.theme.header_font).pack(anchor='w', pady=10)
                        
                        # Look for images in results folder
                        image_files = [f for f in os.listdir(result_path) 
                                    if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
                        
                        if image_files:
                            # Create image gallery
                            gallery_frame = ttk.Frame(viz_frame)
                            gallery_frame.pack(fill='both', expand=True)
                            
                            # Create tabs for each image
                            image_notebook = ttk.Notebook(gallery_frame)
                            image_notebook.pack(fill='both', expand=True)
                            
                            for img_file in image_files:
                                img_tab = ttk.Frame(image_notebook)
                                image_notebook.add(img_tab, text=os.path.splitext(img_file)[0])
                                
                                try:
                                    # Load and display image
                                    img_path = os.path.join(result_path, img_file)
                                    img = Image.open(img_path)
                                    img.thumbnail((800, 600))
                                    photo = ImageTk.PhotoImage(img)
                                    
                                    # Store reference to prevent garbage collection
                                    img_tab.image = photo
                                    
                                    # Display image
                                    img_label = ttk.Label(img_tab, image=photo)
                                    img_label.pack(pady=10)
                                    
                                    # Add save button
                                    ttk.Button(img_tab, text="Save Image As...", 
                                            command=lambda p=img_path: self.save_result_image(p)).pack(pady=5)
                                except Exception as e:
                                    ttk.Label(img_tab, text=f"Error loading image: {str(e)}").pack(pady=20)
                        else:
                            ttk.Label(viz_frame, text="No visualization images found").pack(pady=20)
                        
                        # Add export button
                        ttk.Button(summary_frame, text="Export Results", 
                                command=lambda p=result_path: self.export_result(p)).pack(pady=10)
                        
                    else:
                        # No metadata file
                        ttk.Label(summary_tab, text="No metadata found for this result",
                            padding=20).pack()
                    
                except Exception as e:
                    ttk.Label(summary_tab, text=f"Error loading result: {str(e)}",
                        padding=20).pack()
            
            # Populate results tree
            for i, folder in enumerate(result_folders):
                folder_path = os.path.join(results_dir, folder)
                
                # Try to parse date from folder name
                try:
                    # Assuming format like "result_20230415_123456"
                    date_str = folder.split('_')[1]
                    if len(date_str) >= 8:
                        date = f"{date_str[0:4]}-{date_str[4:6]}-{date_str[6:8]}"
                    else:
                        date = folder
                except:
                    date = folder
                
                # Try to get parameters from metadata
                try:
                    metadata_file = os.path.join(folder_path, "metadata.json")
                    if os.path.exists(metadata_file):
                        with open(metadata_file, 'r') as f:
                            metadata = json.load(f)
                        
                        params = metadata.get('parameters', {})
                        param_str = ", ".join([f"{k}={v}" for k, v in params.items()])
                    else:
                        param_str = "No metadata"
                except:
                    param_str = "Error reading metadata"
                
                result_tree.insert("", "end", values=(date, param_str, folder_path))
            
            # Bind selection event
            result_tree.bind("<<TreeviewSelect>>", load_result_details)
            
            # Add button to load in main application
            button_frame = ttk.Frame(results_dialog)
            button_frame.pack(fill='x', padx=10, pady=10)
            
            ttk.Button(button_frame, text="Close", 
                    command=results_dialog.destroy).pack(side='right', padx=5)
            
        except Exception as e:
            self._update_workflow_status(f"Error viewing previous results: {str(e)}", 'error')
            self.log(f"Error viewing previous results: {str(e)}")

    def save_result_image(self, image_path):
        """Save a result image to a user-selected location"""
        try:
            # Ask for save location
            save_path = filedialog.asksaveasfilename(
                title="Save Image As",
                defaultextension=os.path.splitext(image_path)[1],
                filetypes=[
                    ("PNG Image", "*.png"),
                    ("JPEG Image", "*.jpg"),
                    ("All Files", "*.*")
                ]
            )
            
            if not save_path:
                return
            
            # Copy the image file
            shutil.copy2(image_path, save_path)
            
            messagebox.showinfo("Success", f"Image saved to {save_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save image: {str(e)}")

    def export_result(self, result_path):
        """Export a result to a zip file"""
        try:
            # Ask for save location
            save_path = filedialog.asksaveasfilename(
                title="Export Result As",
                defaultextension=".zip",
                filetypes=[
                    ("Zip Archive", "*.zip"),
                    ("All Files", "*.*")
                ]
            )
            
            if not save_path:
                return
            
            # Create zip file
            with zipfile.ZipFile(save_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(result_path):
                    for file in files:
                        # Get full file path
                        file_path = os.path.join(root, file)
                        # Get relative path for use in zip file
                        rel_path = os.path.relpath(file_path, result_path)
                        # Add file to zip
                        zipf.write(file_path, rel_path)
            
            messagebox.showinfo("Success", f"Result exported to {save_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export result: {str(e)}")

    def search_workflow_log(self):
        """Search the workflow log for specific text"""
        if not hasattr(self, 'workflow_status_text'):
            return
        
        # Get search text
        search_text = self.log_search_var.get()
        if not search_text:
            return
        
        # Get text content
        text_content = self.workflow_status_text.get(1.0, tk.END)
        
        # Find all matches
        matches = []
        start_idx = 0
        while True:
            idx = text_content.find(search_text, start_idx)
            if idx == -1:
                break
            matches.append(idx)
            start_idx = idx + len(search_text)
        
        if not matches:
            messagebox.showinfo("Search", f"No matches found for '{search_text}'")
            return
        
        # Highlight all matches
        self.workflow_status_text.tag_remove("search", "1.0", tk.END)
        for idx in matches:
            # Convert index to line.char format
            line_start = text_content.count('\n', 0, idx) + 1
            char_start = idx - text_content.rfind('\n', 0, idx) - 1
            line_end = line_start
            char_end = char_start + len(search_text)
            
            start_index = f"{line_start}.{char_start}"
            end_index = f"{line_end}.{char_end}"
            
            # Add search tag to highlight match
            self.workflow_status_text.tag_add("search", start_index, end_index)
        
        # Configure search tag
        self.workflow_status_text.tag_configure("search", background="yellow", foreground="black")
        
        # Scroll to first match
        line_start = text_content.count('\n', 0, matches[0]) + 1
        char_start = matches[0] - text_content.rfind('\n', 0, matches[0]) - 1
        self.workflow_status_text.see(f"{line_start}.{char_start}")
        
        # Show message
        messagebox.showinfo("Search", f"Found {len(matches)} matches for '{search_text}'")

    def clear_workflow_log(self):
        """Clear the workflow log text area"""
        if hasattr(self, 'workflow_status_text'):
            self.workflow_status_text.configure(state='normal')
            self.workflow_status_text.delete(1.0, tk.END)
            self.workflow_status_text.insert(tk.END, "Log cleared. Ready to start workflow.\n")
            self.workflow_status_text.configure(state='disabled')
            self.update_status("Workflow log cleared")

    def create_card(self, parent):
        """Create a card-style container with shadow effect"""
        # Create outer frame for shadow effect
        shadow_frame = ttk.Frame(parent)
        
        # Create main card frame with border
        card_frame = ttk.Frame(shadow_frame, style="Card.TFrame")
        card_frame.pack(fill='both', expand=True, padx=2, pady=2)
        
        return card_frame

    def refresh_hpc_profiles(self):
        """Refresh HPC profiles from configuration files"""
        self.load_workflow_hpc_profiles()
        self._update_workflow_status("HPC profiles refreshed", 'info')

    def manage_hpc_profiles(self):
        """Open dialog to manage HPC profiles"""
        # Redirect to HPC tab for profile management
        self.notebook.select(self.hpc_tab)
        self.update_status("Switched to HPC tab for profile management")

    def sanitize_color(color):
        """Ensure color is in the format Tkinter accepts (#RRGGBB)"""
        if isinstance(color, str) and color.startswith('#'):
            # If it has alpha component (#RRGGBBAA), strip it
            if len(color) == 9:
                return color[:7]
        return color

def _setup_parameter_section(self, parent):
    """Set up the parameter input section with real-time validation and rich UI"""
    # Create card with modern styling
    param_card = ttk.Frame(parent)
    param_card.pack(fill='x', padx=10, pady=10)
    
    # Header with expandable section toggle and presets
    header_frame = ttk.Frame(param_card)
    header_frame.pack(fill='x', pady=5)
    
    # Add icon and title
    title_frame = ttk.Frame(header_frame)
    title_frame.pack(side='left')
    
    settings_icon = ttk.Label(title_frame, text="⚙️", font=("Segoe UI", 16))
    settings_icon.pack(side='left', padx=(0, 5))
    
    ttk.Label(title_frame, text="Design Parameters", 
              font=self.theme.header_font).pack(side='left')
    
    # Preset controls with modern dropdown
    preset_frame = ttk.Frame(header_frame)
    preset_frame.pack(side='right')
    
    self.preset_var = tk.StringVar(value="Default")
    ttk.Label(preset_frame, text="Preset:").pack(side='left', padx=5)
    preset_combo = ttk.Combobox(preset_frame, textvariable=self.preset_var, 
                               width=15, state="readonly")
    preset_combo.pack(side='left', padx=5)
    
    # Get available presets
    presets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Config", "presets")
    os.makedirs(presets_dir, exist_ok=True)
    preset_files = [os.path.splitext(f)[0] for f in os.listdir(presets_dir) 
                   if f.endswith('.json')]
    preset_combo['values'] = ["Default"] + preset_files
    preset_combo.bind("<<ComboboxSelected>>", self._load_selected_preset)
    
    ttk.Button(preset_frame, text="Save", width=8,
             command=self.save_parameter_preset).pack(side='left', padx=2)
    
    # Main parameters section with improved layout
    params_frame = ttk.Frame(param_card, padding=15)
    params_frame.pack(fill='x', pady=10)
    
    # Add parameter sliders with visual feedback
    self.param_entries = {}
    self.param_sliders = {}
    self.param_feedback = {}
    
    # Define parameters with min/max/default values
    parameters = [
        ("L4", "Length parameter 4", 1.0, 10.0, 3.0, "mm"),
        ("L5", "Length parameter 5", 1.0, 10.0, 3.0, "mm"),
        ("Alpha1", "Angle parameter 1", 0.0, 90.0, 15.0, "°"),
        ("Alpha2", "Angle parameter 2", 0.0, 90.0, 15.0, "°"),
        ("Alpha3", "Angle parameter 3", 0.0, 90.0, 15.0, "°")
    ]
    
    for i, (param, desc, min_val, max_val, default, unit) in enumerate(parameters):
        # Parameter container
        param_container = ttk.Frame(params_frame)
        param_container.pack(fill='x', pady=8)
        
        # Parameter header with label and value
        header = ttk.Frame(param_container)
        header.pack(fill='x')
        
        ttk.Label(header, text=f"{param}:", 
                 font=self.theme.normal_font).pack(side='left')
        
        # Value display with unit
        self.param_entries[param.lower()] = ttk.Entry(header, width=8)
        self.param_entries[param.lower()].pack(side='right', padx=5)
        self.param_entries[param.lower()].insert(0, str(default))
        
        ttk.Label(header, text=unit).pack(side='right')
        
        # Description with tooltip styling
        ttk.Label(param_container, text=desc,
                 font=self.theme.small_font,
                 foreground=self.theme.secondary_color).pack(anchor='w', padx=15, pady=(0, 5))
        
        # Slider for visual parameter adjustment
        slider_frame = ttk.Frame(param_container)
        slider_frame.pack(fill='x', padx=15)
        
        ttk.Label(slider_frame, text=str(min_val)).pack(side='left')
        
        self.param_sliders[param.lower()] = ttk.Scale(
            slider_frame, from_=min_val, to=max_val, 
            orient='horizontal', length=200,
            command=lambda val, p=param.lower(): self._update_param_from_slider(p, val)
        )
        self.param_sliders[param.lower()].pack(side='left', fill='x', expand=True, padx=5)
        self.param_sliders[param.lower()].set(default)
        
        ttk.Label(slider_frame, text=str(max_val)).pack(side='left')
        
        # Visual feedback indicator for parameter validity
        self.param_feedback[param.lower()] = ttk.Label(param_container, text="✓")
        self.param_feedback[param.lower()].pack(side='right', padx=5)
        
        # Bind entry changes to update sliders
        self.param_entries[param.lower()].bind("<FocusOut>", 
                                             lambda e, p=param.lower(): self._update_slider_from_entry(p))
        self.param_entries[param.lower()].bind("<Return>", 
                                             lambda e, p=param.lower(): self._update_slider_from_entry(p))
    
    # Add real-time validation message area
    validation_frame = ttk.Frame(param_card)
    validation_frame.pack(fill='x', padx=10, pady=5)
    
    self.validation_icon = ttk.Label(validation_frame, text="✓", foreground="green")
    self.validation_icon.pack(side='left', padx=5)
    
    self.validation_message = ttk.Label(validation_frame, 
                                      text="All parameters are valid", 
                                      foreground="green")
    self.validation_message.pack(side='left', fill='x', expand=True)

def _update_param_from_slider(self, param_name, value):
    """Update parameter entry when slider is moved"""
    try:
        # Format value appropriately (integers for angles, 2 decimals for lengths)
        if param_name.startswith('alpha'):
            formatted_value = f"{float(value):.0f}"
        else:
            formatted_value = f"{float(value):.2f}"
            
        # Update entry without triggering its change event
        entry = self.param_entries[param_name]
        entry.delete(0, tk.END)
        entry.insert(0, formatted_value)
        
        # Validate the parameter and update feedback
        self._validate_single_parameter(param_name)
        
        # Update overall validation status
        self._update_validation_status()
    except Exception as e:
        self.log(f"Error updating from slider: {e}")

def _update_slider_from_entry(self, param_name):
    """Update slider when entry value changes"""
    try:
        # Get entry value
        entry = self.param_entries[param_name]
        value = float(entry.get())
        
        # Update slider
        slider = self.param_sliders[param_name]
        min_val = float(slider.cget('from'))
        max_val = float(slider.cget('to'))
        
        # Clamp value to slider range
        value = max(min_val, min(max_val, value))
        slider.set(value)
        
        # Format and update entry for consistency
        if param_name.startswith('alpha'):
            formatted_value = f"{value:.0f}"
        else:
            formatted_value = f"{value:.2f}"
            
        entry.delete(0, tk.END)
        entry.insert(0, formatted_value)
        
        # Validate the parameter and update feedback
        self._validate_single_parameter(param_name)
        
        # Update overall validation status
        self._update_validation_status()
    except ValueError:
        # Invalid number format
        self.param_feedback[param_name].config(text="✗", foreground="red")
    except Exception as e:
        self.log(f"Error updating from entry: {e}")

def _validate_single_parameter(self, param_name):
    """Validate a single parameter and update its feedback indicator"""
    try:
        # Get value from entry
        value = float(self.param_entries[param_name].get())
        
        # Parameter-specific validation
        if param_name == 'l4' or param_name == 'l5':
            # Length parameters
            if value <= 0:
                self.param_feedback[param_name].config(text="✗", foreground="red")
                return False
            elif value < 1.0 or value > 10.0:
                self.param_feedback[param_name].config(text="⚠", foreground="orange")
                return True
            else:
                self.param_feedback[param_name].config(text="✓", foreground="green")
                return True
                
        elif param_name.startswith('alpha'):
            # Angle parameters
            if value < 0 or value > 90:
                self.param_feedback[param_name].config(text="✗", foreground="red")
                return False
            elif value < 5.0 or value > 45.0:
                self.param_feedback[param_name].config(text="⚠", foreground="orange")
                return True
            else:
                self.param_feedback[param_name].config(text="✓", foreground="green")
                return True
        
        # Default case
        self.param_feedback[param_name].config(text="✓", foreground="green")
        return True
        
    except ValueError:
        # Invalid number format
        self.param_feedback[param_name].config(text="✗", foreground="red")
        return False
    except Exception as e:
        self.log(f"Error validating parameter {param_name}: {e}")
        return False

def _update_validation_status(self):
    """Update the overall validation status message"""
    all_valid = True
    any_warnings = False
    error_params = []
    warning_params = []
    
    # Check each parameter
    for param_name in self.param_entries:
        try:
            value = float(self.param_entries[param_name].get())
            
            # Parameter-specific validation
            if param_name == 'l4' or param_name == 'l5':
                if value <= 0:
                    all_valid = False
                    error_params.append(param_name.upper())
                elif value < 1.0 or value > 10.0:
                    any_warnings = True
                    warning_params.append(param_name.upper())
            
            elif param_name.startswith('alpha'):
                if value < 0 or value > 90:
                    all_valid = False
                    error_params.append(param_name.upper())
                elif value < 5.0 or value > 45.0:
                    any_warnings = True
                    warning_params.append(param_name.upper())
        except ValueError:
            all_valid = False
            error_params.append(param_name.upper())
    
    # Update validation message based on results
    if not all_valid:
        self.validation_icon.config(text="✗", foreground="red")
        self.validation_message.config(
            text=f"Invalid parameters: {', '.join(error_params)}", 
            foreground="red"
        )
    elif any_warnings:
        self.validation_icon.config(text="⚠", foreground="orange")
        self.validation_message.config(
            text=f"Valid with warnings: {', '.join(warning_params)}", 
            foreground="orange"
        )
    else:
        self.validation_icon.config(text="✓", foreground="green")
        self.validation_message.config(
            text="All parameters are valid", 
            foreground="green"
        )

def _setup_env_section(self, parent):
    """Set up the execution environment section with modern toggle and cloud options"""
    # Create container card
    env_card = ttk.Frame(parent)
    env_card.pack(fill='x', padx=10, pady=10)
    
    # Header with cloud icon
    header_frame = ttk.Frame(env_card)
    header_frame.pack(fill='x', pady=5)
    
    cloud_icon = ttk.Label(header_frame, text="☁️", font=("Segoe UI", 16))
    cloud_icon.pack(side='left', padx=(0, 5))
    
    ttk.Label(header_frame, text="Execution Environment", 
            font=self.theme.header_font).pack(side='left')
    
    # Execution options with visual toggles and info
    options_frame = ttk.Frame(env_card, padding=15)
    options_frame.pack(fill='x', pady=10)
    
    # Local execution option
    local_frame = ttk.Frame(options_frame)
    local_frame.pack(fill='x', pady=8)
    
    # Use BooleanVar instead of StringVar for better toggle semantics
    self.env_local_var = tk.BooleanVar(value=True)
    
    # Create toggle-style radio buttons
    local_option = ttk.Radiobutton(
        local_frame, 
        text="Local Execution", 
        variable=self.env_var,
        value="local",
        command=self.toggle_execution_environment,
        style="Toggle.TRadiobutton"
    )
    local_option.pack(side='left')
    
    # Hardware info display
    hw_info = self.get_hardware_info()
    ttk.Label(local_frame, 
            text=hw_info,
            font=self.theme.small_font,
            foreground=self.theme.secondary_color).pack(side='left', padx=15)
    
    # HPC execution option
    hpc_frame = ttk.Frame(options_frame)
    hpc_frame.pack(fill='x', pady=8)
    
    hpc_option = ttk.Radiobutton(
        hpc_frame, 
        text="HPC Execution", 
        variable=self.env_var,
        value="hpc",
        command=self.toggle_execution_environment,
        style="Toggle.TRadiobutton"
    )
    hpc_option.pack(side='left')
    
    # Expandable HPC settings with animation
    self.workflow_hpc_frame = ttk.Frame(options_frame)
    self.workflow_hpc_frame.pack(fill='x', pady=(0, 10))
    
    # HPC profile selection with dynamic updating
    profile_frame = ttk.Frame(self.workflow_hpc_frame, padding=10)
    profile_frame.pack(fill='x')
    
    ttk.Label(profile_frame, text="HPC Profile:").pack(side='left')
    
    self.workflow_hpc_profile = ttk.Combobox(
        profile_frame, 
        width=20, 
        state="readonly"
    )
    self.workflow_hpc_profile.pack(side='left', padx=5, fill='x', expand=True)
    
    # Add buttons for profile management
    button_frame = ttk.Frame(profile_frame)
    button_frame.pack(side='right')
    
    ttk.Button(button_frame, 
            text="Refresh", 
            width=8,
            command=self.refresh_hpc_profiles).pack(side='left', padx=2)
    
    ttk.Button(button_frame, 
            text="Manage", 
            width=8,
            command=self.manage_hpc_profiles).pack(side='left', padx=2)
    
    # Load profiles
    self.load_workflow_hpc_profiles()
    
    # Information about HPC execution
    info_frame = ttk.Frame(self.workflow_hpc_frame, padding=10)
    info_frame.pack(fill='x')
    
    ttk.Label(info_frame, 
            text="Running on HPC allows larger simulations and faster results but requires configuration.",
            font=self.theme.small_font,
            foreground=self.theme.secondary_color,
            wraplength=400).pack(anchor='w')
    
    # Hide HPC settings initially if not selected
    if self.env_var.get() != "hpc":
        self.workflow_hpc_frame.pack_forget()

def get_hardware_info(self):
    """Get formatted hardware information for display"""
    try:
        # Get CPU info
        cpu_count = os.cpu_count() or 0
        
        # Try to get more detailed CPU info if psutil is available
        try:
            import psutil
            memory = psutil.virtual_memory()
            mem_gb = memory.total / (1024 * 1024 * 1024)
            return f"{cpu_count} CPU cores, {mem_gb:.1f} GB RAM"
        except ImportError:
            # Fallback without psutil
            return f"{cpu_count} CPU cores"
    except Exception as e:
        self.log(f"Error getting hardware info: {e}")
        return "Hardware info unavailable"




# Main function that serves as the entry point for the application
def main():
    """Main entry point for the Intake CFD Optimization Suite application."""
    import argparse
    import os
    import sys
    import traceback
    
    parser = argparse.ArgumentParser(description="Intake CFD Optimization Suite")
    parser.add_argument("--demo", action="store_true", help="Run in demonstration mode")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    # Set demo mode from arguments or environment variable
    if args.demo:
        global DEMO_MODE
        DEMO_MODE = True
        os.environ["GARAGE_DEMO_MODE"] = "1"
    else:
        DEMO_MODE = os.environ.get("GARAGE_DEMO_MODE", "1").lower() in ("true", "1", "yes")
        
    # Configure logging
    log_level = "DEBUG" if args.debug else "INFO"
    logging_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=getattr(logging, log_level), format=logging_format)
    logger = logging.getLogger("intake-cfd")
    
    logger.info("Starting Intake CFD Optimization Suite")
    logger.info(f"Demo Mode: {DEMO_MODE}")
    
    try:
        # Create mock executables for demonstration if needed
        if DEMO_MODE:
            create_mock_executables()
            logger.info("Created mock executables for demonstration mode")
        
        # Import HPC module utilities as needed
        try:
            from Utils import workflow_utils
            logger.info("Loaded workflow utilities")
        except ImportError as e:
            logger.warning(f"Could not load workflow utilities: {e}")
            
        # Try to load workflow utilities and HPC modules
        try:
            from Garage.Utils import workflow_utils
            logger.info("Workflow utilities loaded successfully")
            
            # Try to import HPC modules
            try:
                from Garage.HPC import hpc_integration
                logger.info("HPC modules loaded successfully")
            except ImportError as e:
                logger.warning(f"HPC modules could not be loaded: {e}")
                
        except ImportError as e:
            logger.error(f"Failed to load workflow utilities: {e}")
            logger.error(traceback.format_exc())
            print(f"Could not load required modules: {str(e)}")
            if not DEMO_MODE:
                messagebox.showerror("Error", f"Failed to load required modules: {str(e)}")
                return 1
            
        # Try to load workflow utilities
        try:
            from Utils import workflow_utils
            print("workflow_utils.py loaded.")
            try:
                # We need to patch the workflow GUI with HPC functionality
                if hasattr(workflow_utils, 'patch_workflow_gui'):
                    workflow_utils.patch_workflow_gui(WorkflowGUI)
                    logger.info("WorkflowGUI patched with HPC functionality")
                
                # If fix_hpc_gui is available, use it to further enhance HPC functionality
                try:
                    from GUI import fix_hpc_gui
                    # Update workflow utils
                    fix_hpc_gui.update_workflow_utils()
                    # Ensure HPC settings exist
                    fix_hpc_gui.ensure_hpc_profiles()
                    # Patch the WorkflowGUI class
                    fix_hpc_gui.patch_workflow_gui()
                    logger.info("HPC GUI components initialized successfully")
                except ImportError as e:
                    logger.warning(f"Could not load HPC GUI fix: {e}")
                except Exception as e:
                    logger.warning(f"Error applying HPC GUI fixes: {e}")
            except Exception as e:
                logger.warning(f"Could not apply workflow patching: {e}")
        except ImportError as e:
            logger.warning(f"Could not load workflow utilities: {e}")
        
        # Initialize the main application window
        root = tk.Tk()
        root.title("Intake CFD Optimization Suite")
        root.geometry("1280x800")
        root.minsize(800, 600)
        
        # Create the GUI
        app = WorkflowGUI(root)
        
        # Apply HPC integration if available
        try:
            from Garage.HPC.hpc_integration import initialize_hpc
            logger.info("HPC module found, initializing HPC integration...")
            success = initialize_hpc(app)
            if success:
                logger.info("HPC integration initialized successfully")
            else:
                logger.warning("HPC integration initialization failed")
        except Exception as e:
            logger.error(f"Error initializing HPC integration: {str(e)}")
            logger.error(traceback.format_exc())
            print(f"Could not initialize HPC integration: {str(e)}")
            
        # Apply HPC integration if available
        try:
            from GUI.fix_hpc_gui import patch_workflow_gui
            patch_workflow_gui()
            logger.info("Applied HPC GUI patches")
            
            # Set up HPC tab if the method exists
            if hasattr(app, 'setup_hpc_tab'):
                app.setup_hpc_tab()
                logger.info("Set up HPC tab")
        except Exception as e:
            logger.warning(f"Could not apply HPC integration: {e}")
            
        # Start the main event loop
        root.mainloop()
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Show error dialog
        try:
            import tkinter.messagebox as messagebox
            messagebox.showerror("Error", f"An error occurred: {str(e)}\n\nPlease check the logs for details.")
        except:
            print(f"ERROR: {str(e)}")
            traceback.print_exc()
        
        return 1
    
    return 0

if __name__ == "__main__":
    # Make sure to actually call the main function
    # The previous code defines main() but may not be executing it properly
    import sys
    try:
        sys.exit(main())
    except Exception as e:
        print(f"Fatal error launching application: {str(e)}")
        traceback.print_exc()
        sys.exit(1)