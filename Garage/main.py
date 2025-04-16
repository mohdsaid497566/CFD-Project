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
            self.accent_color = "#0078d7"
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
        self.accent_color = "#0078d7"
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

    def save_hpc_settings(self):
        """Save HPC settings to configuration file"""
        try:
            import os
            import json
            
            # Get values from UI
            settings = {
                "hpc_enabled": True,
                "hpc_host": self.hpc_host_entry.get(),
                "hpc_username": self.hpc_username_entry.get(),
                "hpc_port": int(self.hpc_port_entry.get()),
                "use_key_auth": self.auth_method_var.get() == "key",
                "key_path": self.key_path_entry.get() if self.auth_method_var.get() == "key" else "",
                "visible_in_gui": True
            }
            
            # Save to file
            config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Config")
            os.makedirs(config_dir, exist_ok=True)
            
            settings_path = os.path.join(config_dir, "hpc_settings.json")
            with open(settings_path, 'w') as f:
                json.dump(settings, f, indent=4)
            
            messagebox.showinfo("Settings Saved", "HPC settings saved successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {str(e)}")

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

    def save_hpc_settings(self):
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
            settings_file = os.path.join(config_dir, "hpc_settings.json")
            with open(settings_file, 'w') as f:
                json.dump(settings, f, indent=4)
            
            self.log("HPC settings saved successfully")
            messagebox.showinfo("Success", "HPC settings saved successfully")
            return True
        except Exception as e:
            self.log(f"Error saving HPC settings: {e}")
            messagebox.showerror("Error", f"Failed to save HPC settings: {str(e)}")
            return False

    def load_hpc_settings(self):
        """Load HPC settings from config file"""
        try:
            import os
            import json
            
            # First, look in the Config directory
            config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Config")
            settings_file = os.path.join(config_dir, "hpc_settings.json")
            
            # If not found, try the GUI/config directory (previous location)
            if not os.path.exists(settings_file):
                alt_config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "GUI", "config")
                alt_settings_file = os.path.join(alt_config_dir, "hpc_settings.json")
                
                if os.path.exists(alt_settings_file):
                    settings_file = alt_settings_file
                    self.log(f"Using HPC settings from alternate location: {alt_settings_file}")
                else:
                    self.log("No HPC settings file found, creating default")
                    return self._create_default_hpc_settings()
            
            # Load settings
            with open(settings_file, 'r') as f:
                settings = json.load(f)
            
            # Store settings for later use
            self.hpc_settings = settings
            self.log("HPC settings loaded successfully")
            return settings
        except Exception as e:
            self.log(f"Error loading HPC settings: {e}")
            return self._create_default_hpc_settings()

    def _create_default_hpc_settings(self):
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
        
        self.hpc_settings = default_settings
        return default_settings

    def apply_hpc_settings(self):
        """Apply loaded HPC settings to UI widgets"""
        try:
            settings = getattr(self, 'hpc_settings', None)
            if not settings:
                settings = self.load_hpc_settings()
            
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
                      value="small", command=lambda: self.apply_font_size(10, 12, 14)).grid(
                      row=0, column=0, sticky='w', pady=5)
        ttk.Radiobutton(font_frame, text="Normal", variable=self.font_size_var, 
                      value="normal", command=lambda: self.apply_font_size(12, 14, 16)).grid(
                      row=0, column=1, sticky='w', pady=5)
        ttk.Radiobutton(font_frame, text="Large", variable=self.font_size_var, 
                      value="large", command=lambda: self.apply_font_size(14, 16, 18)).grid(
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
        """Apply appearance settings from the form"""
        theme = self.theme_var.get()
        if theme == "light":
            self.apply_light_theme()
        elif theme == "dark":
            self.apply_dark_theme()
        else:
            self.apply_system_theme()
        
        font_size = self.font_size_var.get()
        if font_size == "small":
            self.apply_font_size(10, 12, 14)
        elif font_size == "large":
            self.apply_font_size(14, 16, 18)
        else:
            self.apply_font_size(12, 14, 16)
    
    def apply_dark_theme(self):
        """Apply dark theme to the application"""
        self.theme.primary_color = "#3949ab"  # Indigo
        self.theme.secondary_color = "#00897b"  # Teal
        self.theme.bg_color = "#2d2d2d"  # Dark gray
        self.theme.text_color = "#e0e0e0"  # Light gray text
        self.theme.border_color = "#555555"  # Medium gray border
        
        # Apply theme to the root window
        self.theme.apply_theme(self.root)
        
        # Switch to dark theme variants for all canvases
        if hasattr(self, 'workflow_canvas'):
            self.workflow_canvas.configure(bg="#1e1e1e", highlightbackground="#555555")
        
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
    
    def apply_font_size(self, small, normal, large):
        """Apply font size settings"""
        self.theme.small_font = ("Helvetica", small)
        self.theme.normal_font = ("Helvetica", normal)
        self.theme.header_font = ("Helvetica", normal, "bold")
        self.theme.title_font = ("Helvetica", large, "bold")
        
        # Apply these to any text elements that use them
        style = ttk.Style()
        style.configure("Title.TLabel", font=self.theme.title_font)
        style.configure("Header.TLabel", font=self.theme.header_font)
        style.configure("TLabel", font=self.theme.normal_font)
        
        # Update status
        self.update_status("Applied font size settings")
    
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
                messagebox.showwarning("Workflow Running", 
                                    "A workflow is already in progress. Please wait or cancel it.")
                return
            
            # Validate inputs
            try:
                validation_result = self._validate_workflow_inputs()
                if not validation_result:
                    return
            except Exception as ve:
                messagebox.showerror("Validation Error", str(ve))
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
            
            # Create and start a worker thread to avoid freezing the UI
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
            self._update_workflow_step("NX Model", "running")
            
            # Generate expression file
            try:
                exp(L4, L5, alpha1, alpha2, alpha3)
                self._update_workflow_status("Expressions generated")
            except Exception as e:
                self._update_workflow_status(f"Error generating expressions: {str(e)}")
                self._update_workflow_step("NX Model", "error")
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
                self._update_workflow_step("NX Model", "complete")
            except Exception as e:
                self._update_workflow_status(f"Error updating NX model: {str(e)}")
                self._update_workflow_step("NX Model", "error")
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
        if hasattr(self, 'opt_env_var') and hasattr(self, 'opt_hpc_settings_frame'):
            if self.opt_env_var.get() == "hpc":
                self.opt_hpc_settings_frame.pack(anchor='w', pady=5)
            else:
                self.opt_hpc_settings_frame.pack_forget()

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
        import tempfile
        import os
        
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
            if config.get("use_key", False):
                key_path = config.get("key_path", "")
                if not key_path:
                    self.root.after(0, lambda: messagebox.showerror("Error", "No SSH key specified in profile"))
                    self.root.after(0, lambda: self.update_status("Job submission failed", show_progress=False))
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
                sftp.mkdir(remote_dir)
            
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
            scheduler_cmd = stdout.read().decode().strip().split('\n')[0]
            
            submission_cmd = ""
            if 'sbatch' in scheduler_cmd:
                submission_cmd = f"cd {remote_dir} && sbatch {script_filename}"
            elif 'qsub' in scheduler_cmd:
                submission_cmd = f"cd {remote_dir} && qsub {script_filename}"
            elif 'bsub' in scheduler_cmd:
                submission_cmd = f"cd {remote_dir} && bsub < {script_filename}"
            else:
                self.root.after(0, lambda: messagebox.showerror("Error", "Could not identify job scheduler (SLURM/PBS/LSF)"))
                self.root.after(0, lambda: self.update_status("Job submission failed", show_progress=False))
                client.close()
                return
            
            # Submit job
            stdin, stdout, stderr = client.exec_command(submission_cmd)
            response = stdout.read().decode().strip()
            error = stderr.read().decode().strip()
            
            # Close connection
            client.close()
            
            if error:
                self.log(f"Job submission error: {error}")
                self.root.after(0, lambda: messagebox.showerror("Submission Error", f"Error submitting job: {error}"))
                self.root.after(0, lambda: self.update_status("Job submission failed", show_progress=False))
            else:
                self.log(f"Job submitted: {response}")
                self.root.after(0, lambda: self.update_status("Job submitted successfully", show_progress=False))
                
                # Show success message and close dialog if provided
                self.root.after(0, lambda: messagebox.showinfo("Job Submitted", f"Job successfully submitted:\n{response}"))
                if dialog:
                    self.root.after(0, dialog.destroy)
                
                # Refresh job list after submission
                self.root.after(1000, self.refresh_job_list)
                
        except Exception as e:
            self.log(f"Error submitting job: {str(e)}")
            self.root.after(0, lambda: messagebox.showerror("Submission Error", f"Failed to submit job: {str(e)}"))
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
            main_frame = ttk.Frame(self.optimization_tab, padding=self.theme.padding)
            main_frame.pack(fill='both', expand=True)
            
            # Split into input panel and results panel
            input_frame = ttk.LabelFrame(main_frame, text="Optimization Settings", padding=self.theme.padding)
            input_frame.pack(side='left', fill='y', padx=self.theme.padding, pady=self.theme.padding, anchor='n')
            
            results_frame = ttk.LabelFrame(main_frame, text="Optimization Results", padding=self.theme.padding)
            results_frame.pack(side='right', fill='both', expand=True, padx=self.theme.padding, pady=self.theme.padding)
            
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
            
            # Environment radio buttons
            self.opt_env_var = tk.StringVar(value="local")
            ttk.Radiobutton(exec_frame, text="Local Execution", 
                        variable=self.opt_env_var, value="local",
                        command=lambda: self.toggle_opt_execution_environment()).pack(anchor='w', pady=2)
            
            ttk.Radiobutton(exec_frame, text="HPC Execution", 
                        variable=self.opt_env_var, value="hpc",
                        command=lambda: self.toggle_opt_execution_environment()).pack(anchor='w', pady=2)
            
            # HPC settings frame (initially hidden)
            self.opt_hpc_settings_frame = ttk.Frame(exec_frame)
            ttk.Label(self.opt_hpc_settings_frame, text="HPC Profile:").pack(side="left", padx=5)
            self.opt_hpc_profile = ttk.Combobox(self.opt_hpc_settings_frame, width=20)
            self.opt_hpc_profile.pack(side="left", padx=5)
            
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
            self.opt_hpc_settings_frame.pack_forget()
            
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
        
        # Parameter inputs
        ttk.Label(parameters_frame, text="L4:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.l4_workflow = ttk.Entry(parameters_frame, width=10)
        self.l4_workflow.grid(row=0, column=1, padx=5, pady=5)
        self.l4_workflow.insert(0, "3.0")
        
        ttk.Label(parameters_frame, text="L5:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        self.l5_workflow = ttk.Entry(parameters_frame, width=10)
        self.l5_workflow.grid(row=1, column=1, padx=5, pady=5)
        self.l5_workflow.insert(0, "3.0")
        
        ttk.Label(parameters_frame, text="Alpha1:").grid(row=2, column=0, padx=5, pady=5, sticky='w')
        self.alpha1_workflow = ttk.Entry(parameters_frame, width=10)
        self.alpha1_workflow.grid(row=2, column=1, padx=5, pady=5)
        self.alpha1_workflow.insert(0, "15.0")
        
        ttk.Label(parameters_frame, text="Alpha2:").grid(row=3, column=0, padx=5, pady=5, sticky='w')
        self.alpha2_workflow = ttk.Entry(parameters_frame, width=10)
        self.alpha2_workflow.grid(row=3, column=1, padx=5, pady=5)
        self.alpha2_workflow.insert(0, "15.0")
        
        ttk.Label(parameters_frame, text="Alpha3:").grid(row=4, column=0, padx=5, pady=5, sticky='w')
        self.alpha3_workflow = ttk.Entry(parameters_frame, width=10)
        self.alpha3_workflow.grid(row=4, column=1, padx=5, pady=5)
        self.alpha3_workflow.insert(0, "15.0")
        
        # Execution environment
        env_frame = ttk.Frame(parameters_frame)
        env_frame.grid(row=5, column=0, columnspan=2, pady=10, sticky='w')
        ttk.Label(env_frame, text="Execution:").pack(side='left')
        self.env_var = tk.StringVar(value="local")
        ttk.Radiobutton(env_frame, text="Local", variable=self.env_var, value="local", 
                    command=self.toggle_execution_environment).pack(side='left', padx=5)
        ttk.Radiobutton(env_frame, text="HPC", variable=self.env_var, value="hpc",
                    command=self.toggle_execution_environment).pack(side='left', padx=5)
        
        # HPC settings frame (initially hidden)
        self.workflow_hpc_frame = ttk.Frame(parameters_frame)
        self.workflow_hpc_frame.grid(row=6, column=0, columnspan=2, pady=5, sticky='w')
        ttk.Label(self.workflow_hpc_frame, text="HPC Profile:").pack(side='left')
        self.workflow_hpc_profile = ttk.Combobox(self.workflow_hpc_frame, width=15)
        self.workflow_hpc_profile.pack(side='left', padx=5)
        
        # Buttons
        button_frame = ttk.Frame(parameters_frame)
        button_frame.grid(row=7, column=0, columnspan=2, pady=10)
        self.run_button = ttk.Button(button_frame, text="Run Workflow", command=self.run_workflow)
        self.run_button.pack(side='left', padx=5)
        self.cancel_button = ttk.Button(button_frame, text="Cancel", command=self.cancel_workflow, state='disabled')
        self.cancel_button.pack(side='left', padx=5)
        
        # Workflow visualization area
        self.workflow_canvas = tk.Canvas(workflow_frame, bg="white", highlightthickness=1,
                                        highlightbackground=self.theme.border_color)
        self.workflow_canvas.pack(side='top', fill='both', expand=True, padx=5, pady=5)
        self.workflow_canvas.bind("<Button-1>", self.workflow_canvas_click)
        
        # Initialize workflow steps
        self.workflow_steps = [
            {"name": "NX Model", "x": 0.15, "y": 0.5, "desc": "Update NX model with parameters", "status": "pending"},
            {"name": "Mesh", "x": 0.38, "y": 0.5, "desc": "Generate mesh from STEP file", "status": "pending"},
            {"name": "CFD", "x": 0.62, "y": 0.5, "desc": "Run CFD simulation", "status": "pending"},
            {"name": "Results", "x": 0.85, "y": 0.5, "desc": "Process and analyze results", "status": "pending"}
        ]
        
        # Draw initial workflow
        self._redraw_workflow()
        
        # Status text area
        self.workflow_status_text = scrolledtext.ScrolledText(workflow_frame, height=10, wrap=tk.WORD)
        self.workflow_status_text.pack(side='bottom', fill='x', expand=False, padx=5, pady=5)
        self.workflow_status_text.insert(tk.END, "Ready to run workflow. Set parameters and click 'Run Workflow'.")
        self.workflow_status_text.configure(state='disabled')
        
        # Hide HPC settings initially
        self.workflow_hpc_frame.grid_remove()
        
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
        """Redraw the workflow visualization"""
        if not hasattr(self, 'workflow_canvas') or not hasattr(self, 'workflow_steps'):
            return
            
        # Clear the canvas
        self.workflow_canvas.delete("all")
        
        # Get canvas dimensions
        width = self.workflow_canvas.winfo_width()
        height = self.workflow_canvas.winfo_height()
        
        # If canvas size is not yet determined, use default values
        if width <= 1:
            width = 600
        if height <= 1:
            height = 120
        
        # Colors for different statuses
        colors = {
            "pending": "#E0E0E0",  # Light gray
            "running": "#FFC107",  # Amber
            "complete": "#4CAF50",  # Green
            "error": "#F44336",    # Red
            "canceled": "#9E9E9E"  # Gray
        }
        
        # Draw connections between steps
        for i in range(len(self.workflow_steps) - 1):
            x1 = int(self.workflow_steps[i]["x"] * width)
            y1 = int(self.workflow_steps[i]["y"] * height)
            x2 = int(self.workflow_steps[i+1]["x"] * width)
            y2 = int(self.workflow_steps[i+1]["y"] * height)
            
            # Draw line with appropriate color based on status
            line_color = colors[self.workflow_steps[i]["status"]]
            if self.workflow_steps[i]["status"] == "complete" and self.workflow_steps[i+1]["status"] == "pending":
                self.workflow_canvas.create_line(x1+20, y1, x2-20, y2, fill=line_color, width=2, dash=(4, 2))
            else:
                self.workflow_canvas.create_line(x1+20, y1, x2-20, y2, fill=line_color, width=2)
        
        # Draw each step
        for step in self.workflow_steps:
            x = int(step["x"] * width)
            y = int(step["y"] * height)
            status = step["status"]
            color = colors[status]
            
            # Draw circle
            self.workflow_canvas.create_oval(x-20, y-20, x+20, y+20, fill=color, outline=self.theme.primary_color)
            
            # Draw step name
            self.workflow_canvas.create_text(x, y, text=step["name"], fill=self.theme.text_color)
            
            # Draw status indicator
            status_y = y + 30
            self.workflow_canvas.create_text(x, status_y, text=status.title(), fill=self.theme.text_color)

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
                self.workflow_hpc_frame.grid()
            else:
                self.workflow_hpc_frame.grid_remove()
            
    def setup_visualization_tab(self):
        """Set up the visualization tab"""
        # Main frame for visualization tab
        main_frame = ttk.Frame(self.visualization_tab, padding=self.theme.padding)
        main_frame.pack(fill='both', expand=True)
        
        # Create a notebook for different result types
        self.results_notebook = ttk.Notebook(main_frame)
        self.results_notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Mesh visualization tab
        self.mesh_tab = ttk.Frame(self.results_notebook)
        self.results_notebook.add(self.mesh_tab, text="Mesh")
        
        # Figure placeholder for mesh
        self.mesh_fig = Figure(figsize=(6, 5), dpi=100)
        self.mesh_ax = self.mesh_fig.add_subplot(111, projection='3d')
        self.mesh_ax.set_title("Mesh Visualization")
        self.mesh_ax.set_xlabel("X")
        self.mesh_ax.set_ylabel("Y")
        self.mesh_ax.set_zlabel("Z")
        self.mesh_canvas = FigureCanvasTkAgg(self.mesh_fig, master=self.mesh_tab)
        self.mesh_canvas.draw()
        self.mesh_canvas.get_tk_widget().pack(fill='both', expand=True)
        
        # Toolbar
        mesh_toolbar = NavigationToolbar2Tk(self.mesh_canvas, self.mesh_tab)
        mesh_toolbar.update()
        
        # CFD Results visualization tab
        self.cfd_results_tab = ttk.Frame(self.results_notebook)
        self.results_notebook.add(self.cfd_results_tab, text="CFD Results")
        
        # Controls for CFD results
        controls_frame = ttk.Frame(self.cfd_results_tab)
        controls_frame.pack(side='top', fill='x', padx=5, pady=5)
        
        ttk.Label(controls_frame, text="Field:").pack(side='left', padx=5)
        self.field_var = tk.StringVar(value="Pressure")
        fields = ["Pressure", "Velocity", "Temperature", "Turbulence"]
        self.field_combo = ttk.Combobox(controls_frame, textvariable=self.field_var, values=fields, width=15)
        self.field_combo.pack(side='left', padx=5)
        self.field_combo.bind("<<ComboboxSelected>>", self.update_cfd_visualization)
        
        ttk.Label(controls_frame, text="Visualization:").pack(side='left', padx=5)
        self.viz_var = tk.StringVar(value="Contour")
        viz_types = ["Contour", "Surface", "Vector", "Streamlines"]
        self.viz_combo = ttk.Combobox(controls_frame, textvariable=self.viz_var, values=viz_types, width=15)
        self.viz_combo.pack(side='left', padx=5)
        self.viz_combo.bind("<<ComboboxSelected>>", self.update_cfd_visualization)
        
        # Figure for CFD results
        self.cfd_fig = Figure(figsize=(6, 5), dpi=100)
        self.cfd_ax = self.cfd_fig.add_subplot(111)
        self.cfd_ax.set_title("CFD Results")
        self.cfd_canvas = FigureCanvasTkAgg(self.cfd_fig, master=self.cfd_results_tab)
        self.cfd_canvas.draw()
        self.cfd_canvas.get_tk_widget().pack(fill='both', expand=True)
        
        # Toolbar
        cfd_toolbar = NavigationToolbar2Tk(self.cfd_canvas, self.cfd_results_tab)
        cfd_toolbar.update()
        
        # Geometry visualization tab
        self.geometry_tab = ttk.Frame(self.results_notebook)
        self.results_notebook.add(self.geometry_tab, text="Geometry")
        
        # Create 3D geometry visualization placeholder
        geometry_placeholder = ttk.Label(self.geometry_tab, 
                                    text="Geometry visualization will appear here\nafter running workflow",
                                    font=self.theme.normal_font)
        geometry_placeholder.pack(expand=True, pady=50)
        
        self.log("Visualization tab initialized")

    def update_cfd_visualization(self, event=None):
        """Update the CFD visualization based on selected field and visualization type"""
        if not hasattr(self, 'cfd_ax') or not hasattr(self, 'visualization_data'):
            return
            
        # Clear the current plot
        self.cfd_ax.clear()
        
        # Get selected field and visualization type
        field = self.field_var.get()
        viz_type = self.viz_var.get()
        
        # Get data - if we have it
        if hasattr(self, 'visualization_data'):
            X = self.visualization_data.get('X')
            Y = self.visualization_data.get('Y')
            Z = self.visualization_data.get(field)
            
            if X is not None and Y is not None and Z is not None:
                # Create visualization based on selected type
                if viz_type == "Contour":
                    cs = self.cfd_ax.contourf(X, Y, Z, cmap=cm.viridis, levels=20)
                    self.cfd_fig.colorbar(cs, ax=self.cfd_ax)
                elif viz_type == "Surface":
                    # Convert mesh grid to 3D
                    self.cfd_ax.remove()
                    self.cfd_ax = self.cfd_fig.add_subplot(111, projection='3d')
                    surf = self.cfd_ax.plot_surface(X, Y, Z, cmap=cm.coolwarm, linewidth=0, antialiased=False)
                    self.cfd_fig.colorbar(surf, ax=self.cfd_ax, shrink=0.5, aspect=5)
                elif viz_type == "Vector":
                    # Show a quiver plot for vector fields
                    # For demo, use gradients of Z as vector components
                    dx, dy = np.gradient(Z)
                    # Subsample for clearer display
                    step = 4
                    self.cfd_ax.quiver(X[::step, ::step], Y[::step, ::step], 
                                    dx[::step, ::step], dy[::step, ::step],
                                    scale=50)
                elif viz_type == "Streamlines":
                    # Compute gradients for streamlines
                    dx, dy = np.gradient(Z)
                    self.cfd_ax.streamplot(X, Y, dx, dy, color='k', density=1)
                    
                # Set title and labels
                self.cfd_ax.set_title(f"{field} - {viz_type}")
                self.cfd_ax.set_xlabel("X")
                self.cfd_ax.set_ylabel("Y")
        else:
            # No data available, show message
            self.cfd_ax.text(0.5, 0.5, "No CFD data available.\nRun workflow to generate results.",
                        horizontalalignment='center', verticalalignment='center',
                        transform=self.cfd_ax.transAxes)
        
        # Redraw the canvas
        self.cfd_canvas.draw()       
            
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

    def get_memory_info(self):
        """Get current memory usage information"""
        try:
            # Try to get memory info using psutil if available
            import psutil
            process = psutil.Process(os.getpid())
            memory = process.memory_info().rss
            
            # Convert bytes to MB
            memory_mb = memory / (1024 * 1024)
            
            # Format memory info
            return f"{memory_mb:.1f} MB, {psutil.virtual_memory().percent}% used"
        except ImportError:
            # If psutil is not available, use a platform-specific approach
            if platform.system() == "Linux":
                try:
                    # Read memory info from /proc/self/status
                    with open('/proc/self/status', 'r') as f:
                        for line in f:
                            if line.startswith('VmRSS:'):
                                memory_kb = int(line.split()[1])
                                memory_mb = memory_kb / 1024
                                return f"{memory_mb:.1f} MB"
                except:
                    pass
            
            # If all else fails, return a placeholder
            return "Memory info unavailable"

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
            self.theme.accent_color = "#3498DB"
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
        
    def apply_font_size(self, small, normal, large):
            """Apply font size settings"""
            # Update theme font sizes
            self.theme.small_font = ("Segoe UI", small)
            self.theme.normal_font = ("Segoe UI", normal)
            self.theme.header_font = ("Segoe UI", large, "bold")
            self.theme.button_font = ("Segoe UI", normal)
            self.theme.code_font = ("Consolas", small+1)
            
            # Apply theme to reapply fonts
            self.theme.apply_theme(self.root)
        
    def update_memory_display(self):
            """Update the memory usage display"""
            if not hasattr(self, 'memory_usage_var'):
                return
                
            try:
                mem_info = self.get_memory_info()
                self.memory_usage_var.set(f"Current Memory Usage: {mem_info}")
            except Exception as e:
                self.memory_usage_var.set(f"Memory info unavailable: {e}")
            
            # Schedule next update
            self.root.after(10000, self.update_memory_display)  # Update every 10 seconds

    def save_settings(self):
            """Save application settings to settings.json file"""
            try:
                settings = {
                    "paths": {
                        "nx_path": self.nx_path.get() if hasattr(self, 'nx_path') else "",
                        "project_dir": self.project_dir.get() if hasattr(self, 'project_dir') else ""
                    },
                    "appearance": {
                        "theme": self.theme_combo.get() if hasattr(self, 'theme_combo') else "Light",
                        "font_size": self.font_size.get() if hasattr(self, 'font_size') else "Medium"
                    },
                    "simulation": {
                        "solver": self.solver_combo.get() if hasattr(self, 'solver_combo') else "OpenFOAM",
                        "mesher": self.mesher_combo.get() if hasattr(self, 'mesher_combo') else "GMSH",
                        "mesh_size": self.mesh_size.get() if hasattr(self, 'mesh_size') else "0.1",
                        "viscosity": self.viscosity.get() if hasattr(self, 'viscosity') else "1.8e-5",
                        "density": self.density.get() if hasattr(self, 'density') else "1.225"
                    },
                    "advanced": {
                        "threads": self.threads.get() if hasattr(self, 'threads') else str(multiprocessing.cpu_count()),
                        "debug": str(self.debug_var.get()) if hasattr(self, 'debug_var') else "False",
                        "autosave": self.autosave.get() if hasattr(self, 'autosave') else "10",
                        "memory_limit": str(self.memory_limit.get()) if hasattr(self, 'memory_limit') else "70"
                    }
                }
                
                with open("settings.json", "w") as f:
                    json.dump(settings, f, indent=4)
                
                self.log("Settings saved to settings.json")
                self.update_status("Settings saved")
                messagebox.showinfo("Settings Saved", "Application settings have been saved successfully.")
            except Exception as e:
                self.log(f"Error saving settings: {e}")
                messagebox.showerror("Error", f"Failed to save settings: {e}")
        
    def load_settings(self):
            """Load application settings from settings.json file"""
            try:
                if not os.path.exists("settings.json"):
                    self.log("Settings file not found. Using defaults.")
                    messagebox.showinfo("Settings Not Found", "Settings file not found. Using default settings.")
                    return
                    
                with open("settings.json", "r") as f:
                    settings = json.load(f)
                
                # Update UI with loaded settings
                # Paths
                if "paths" in settings:
                    if hasattr(self, 'nx_path') and "nx_path" in settings["paths"]:
                        self.nx_path.delete(0, tk.END)
                        self.nx_path.insert(0, settings["paths"]["nx_path"])
                    
                    if hasattr(self, 'project_dir') and "project_dir" in settings["paths"]:
                        self.project_dir.delete(0, tk.END)
                        self.project_dir.insert(0, settings["paths"]["project_dir"])
                
                # Appearance
                if "appearance" in settings:
                    if hasattr(self, 'theme_combo') and "theme" in settings["appearance"]:
                        self.theme_combo.set(settings["appearance"]["theme"])
                    
                    if hasattr(self, 'font_size') and "font_size" in settings["appearance"]:
                        self.font_size.set(settings["appearance"]["font_size"])
                
                # Simulation
                if "simulation" in settings:
                    if hasattr(self, 'solver_combo') and "solver" in settings["simulation"]:
                        self.solver_combo.set(settings["simulation"]["solver"])
                    
                    if hasattr(self, 'mesher_combo') and "mesher" in settings["simulation"]:
                        self.mesher_combo.set(settings["simulation"]["mesher"])
                    
                    if hasattr(self, 'mesh_size') and "mesh_size" in settings["simulation"]:
                        self.mesh_size.delete(0, tk.END)
                        self.mesh_size.insert(0, settings["simulation"]["mesh_size"])
                    
                    if hasattr(self, 'viscosity') and "viscosity" in settings["simulation"]:
                        self.viscosity.delete(0, tk.END)
                        self.viscosity.insert(0, settings["simulation"]["viscosity"])
                    
                    if hasattr(self, 'density') and "density" in settings["simulation"]:
                        self.density.delete(0, tk.END)
                        self.density.insert(0, settings["simulation"]["density"])
                
                # Advanced
                if "advanced" in settings:
                    if hasattr(self, 'threads') and "threads" in settings["advanced"]:
                        self.threads.delete(0, tk.END)
                        self.threads.insert(0, settings["advanced"]["threads"])
                    
                    if hasattr(self, 'debug_var') and "debug" in settings["advanced"]:
                        self.debug_var.set(settings["advanced"]["debug"].lower() == "true")
                    
                    if hasattr(self, 'autosave') and "autosave" in settings["advanced"]:
                        self.autosave.delete(0, tk.END)
                        self.autosave.insert(0, settings["advanced"]["autosave"])
                    
                    if hasattr(self, 'memory_limit') and "memory_limit" in settings["advanced"]:
                        try:
                            self.memory_limit.set(float(settings["advanced"]["memory_limit"]))
                        except ValueError:
                            self.memory_limit.set(70.0)
                
                self.log("Settings loaded from settings.json")
                self.update_status("Settings loaded")
                messagebox.showinfo("Settings Loaded", "Application settings have been loaded successfully.")
            except Exception as e:
                self.log(f"Error loading settings: {e}")
                messagebox.showerror("Error", f"Failed to load settings: {e}")
        
    def reset_settings(self):
            """Reset application settings to defaults"""
            if not messagebox.askyesno("Confirm Reset", "Are you sure you want to reset all settings to defaults?"):
                return
                
            try:
                # Reset paths
                if hasattr(self, 'nx_path'):
                    self.nx_path.delete(0, tk.END)
                
                if hasattr(self, 'project_dir'):
                    self.project_dir.delete(0, tk.END)
                
                # Reset appearance
                if hasattr(self, 'theme_combo'):
                    self.theme_combo.set("Light")
                
                if hasattr(self, 'font_size'):
                    self.font_size.set("Medium")
                    
                # Apply default theme
                self.apply_light_theme()
                self.apply_font_size(10, 12, 14)  # Medium font size
                
                # Reset simulation settings
                if hasattr(self, 'solver_combo'):
                    self.solver_combo.set("OpenFOAM")
                
                if hasattr(self, 'mesher_combo'):
                    self.mesher_combo.set("GMSH")
                
                if hasattr(self, 'mesh_size'):
                    self.mesh_size.delete(0, tk.END)
                    self.mesh_size.insert(0, "0.1")
                
                if hasattr(self, 'viscosity'):
                    self.viscosity.delete(0, tk.END)
                    self.viscosity.insert(0, "1.8e-5")
                
                if hasattr(self, 'density'):
                    self.density.delete(0, tk.END)
                    self.density.insert(0, "1.225")
                
                # Reset advanced settings
                if hasattr(self, 'threads'):
                    self.threads.delete(0, tk.END)
                    self.threads.insert(0, str(multiprocessing.cpu_count()))
                
                if hasattr(self, 'debug_var'):
                    self.debug_var.set(False)
                
                if hasattr(self, 'autosave'):
                    self.autosave.delete(0, tk.END)
                    self.autosave.insert(0, "10")
                
                if hasattr(self, 'memory_limit'):
                    self.memory_limit.set(70.0)
                
                self.log("Settings reset to defaults")
                self.update_status("Settings reset to defaults")
                messagebox.showinfo("Settings Reset", "Application settings have been reset to defaults.")
            except Exception as e:
                self.log(f"Error resetting settings: {e}")
                messagebox.showerror("Error", f"Failed to reset settings: {e}")

    def check_updates(self):
            """Check for application updates"""
            self.update_status("Checking for updates...", show_progress=True)
            
            try:
                # Simulate checking for updates
                time.sleep(1)
                
                # For demonstration purposes, we'll just show a message
                # In a real implementation, this would check a server or repository
                version = "1.0"  # Current version
                latest_version = "1.1"  # Latest version (simulated)
                
                if version != latest_version:
                    messagebox.showinfo("Update Available", 
                                    f"An update is available!\n\n"
                                    f"Current version: {version}\n"
                                    f"Latest version: {latest_version}\n\n"
                                    "Visit the project website to download the latest version.")
                    self.log(f"Update available: version {latest_version}")
                else:
                    messagebox.showinfo("No Update Available", 
                                    f"You are running the latest version ({version}).")
                    self.log("No updates available")
                    
                self.update_status("Update check complete", show_progress=False)
            except Exception as e:
                self.log(f"Error checking for updates: {e}")
                messagebox.showerror("Update Check Failed", f"Failed to check for updates: {e}")
                self.update_status("Update check failed", show_progress=False)

    def run_diagnostics(self):
            """Run system diagnostics to check for issues"""
            self.update_status("Running diagnostics...", show_progress=True)
            self.log("Starting system diagnostics")
            
            # Create a new thread for running diagnostics to keep UI responsive
            threading.Thread(target=self._run_diagnostics_thread, daemon=True).start()
        
    def _run_diagnostics_thread(self):
        """Thread function to run diagnostics without blocking the UI"""
        try:
            diagnostics_results = {}
            
            # Check for required Python modules
            missing_modules = []
            for module in ["pandas", "numpy", "matplotlib", "scipy", "tkinter"]:
                try:
                    importlib.import_module(module)
                except ImportError:
                    missing_modules.append(module)
            
            diagnostics_results["missing_modules"] = missing_modules
            
            # Check system resources
            mem_info = self.get_memory_info()
            diagnostics_results["memory"] = mem_info
            
            # CPU cores
            diagnostics_results["cpu_cores"] = multiprocessing.cpu_count()
            
            # Check for disk space
            disk_usage = shutil.disk_usage("/")
            free_gb = disk_usage.free / (1024 * 1024 * 1024)
            total_gb = disk_usage.total / (1024 * 1024 * 1024)
            diagnostics_results["disk_space"] = {
                "free_gb": round(free_gb, 2),
                "total_gb": round(total_gb, 2),
                "percent_free": round((free_gb / total_gb) * 100, 2)
            }
            
            # Check for required binaries
            binaries = ["./gmsh_process", "./cfd_solver", "./process_results"]
            missing_binaries = []
            for binary in binaries:
                if not os.path.exists(binary) or not os.access(binary, os.X_OK):
                    missing_binaries.append(binary)
            
            diagnostics_results["missing_binaries"] = missing_binaries
            
            # Check for required data files
            data_files = ["INTAKE3D.step", "expressions.exp", "settings.json"]
            missing_files = []
            for file in data_files:
                if not os.path.exists(file):
                    missing_files.append(file)
            
            diagnostics_results["missing_files"] = missing_files
            
            # Check for WSL issues if running in WSL
            wsl_issues = []
            if is_wsl():
                # Check for X11 forwarding
                if not os.environ.get("DISPLAY"):
                    wsl_issues.append("No DISPLAY environment variable set")
                
                # Check for access to Windows drives
                if not os.path.exists("/mnt/c"):
                    wsl_issues.append("Cannot access /mnt/c")
            
            diagnostics_results["wsl_issues"] = wsl_issues
            
            # Simulate some processing time
            for i in range(5):
                time.sleep(0.5)  # Simulate checking different systems
            
            # Update UI with results in the main thread
            self.root.after(0, lambda: self._show_diagnostics_result(diagnostics_results))
            
        except Exception as e:
            self.root.after(0, lambda: self._show_diagnostics_error(str(e)))

    def _show_diagnostics_result(self, results):
        """Show the diagnostics results in a dialog"""
        self.update_status("Diagnostics complete", show_progress=False)
        
        # Build the results message
        message = "System Diagnostics Results:\n\n"
        
        # Python modules
        message += "Required Python Modules:\n"
        if not results["missing_modules"]:
            message += "✅ All required Python modules are installed.\n"
        else:
            message += "❌ Missing Python modules: " + ", ".join(results["missing_modules"]) + "\n"
        
        # System resources
        message += "\nSystem Resources:\n"
        message += f"✅ Memory: {results['memory']}\n"
        message += f"✅ CPU Cores: {results['cpu_cores']}\n"
        
        # Disk space
        disk_space = results["disk_space"]
        if disk_space["percent_free"] < 10:
            message += f"⚠️ Low disk space: {disk_space['free_gb']} GB free ({disk_space['percent_free']}%)\n"
        else:
            message += f"✅ Disk space: {disk_space['free_gb']} GB free of {disk_space['total_gb']} GB total\n"
        
        # Required binaries
        message += "\nRequired Binaries:\n"
        if not results["missing_binaries"]:
            message += "✅ All required binaries are present and executable.\n"
        else:
            message += "❌ Missing or non-executable binaries:\n"
            for binary in results["missing_binaries"]:
                message += f"   - {binary}\n"
        
        # Required data files
        message += "\nRequired Data Files:\n"
        if not results["missing_files"]:
            message += "✅ All required data files are present.\n"
        else:
            message += "❌ Missing data files:\n"
            for file in results["missing_files"]:
                message += f"   - {file}\n"
        
        # WSL issues if applicable
        if is_wsl():
            message += "\nWSL Environment:\n"
            if not results["wsl_issues"]:
                message += "✅ WSL environment appears to be properly configured.\n"
            else:
                message += "❌ WSL issues detected:\n"
                for issue in results["wsl_issues"]:
                    message += f"   - {issue}\n"
        
        # Show dialog with results
        max_height = 600
        dialog = tk.Toplevel(self.root)
        dialog.title("Diagnostics Results")
        dialog.geometry(f"600x{max_height}")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Create scrollable text area
        diagnostics_text = scrolledtext.ScrolledText(dialog, wrap=tk.WORD, width=80, height=25)
        diagnostics_text.pack(fill='both', expand=True, padx=10, pady=10)
        diagnostics_text.insert(tk.END, message)
        diagnostics_text.config(state='disabled')
        
        # Button to close dialog
        ttk.Button(dialog, text="Close", command=dialog.destroy).pack(pady=10)
        
        # Log results summary
        self.log("Diagnostics completed: " + 
                    (f"{len(results['missing_modules'])} missing modules, " if results['missing_modules'] else "All modules found, ") +
                    (f"{len(results['missing_binaries'])} missing binaries, " if results['missing_binaries'] else "All binaries found, ") +
                    (f"{len(results['missing_files'])} missing files" if results['missing_files'] else "All files found"))

    def _show_diagnostics_error(self, error_message):
        """Show error when diagnostics fail"""
        self.update_status("Diagnostics failed", show_progress=False)
        messagebox.showerror("Diagnostics Error", f"Failed to run diagnostics: {error_message}")
        self.log(f"Diagnostics failed with error: {error_message}")

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
            self.root.after(0, lambda: self._update_workflow_step("NX Model", "running"))
            
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
                self.root.after(0, lambda: self._update_workflow_step("NX Model", "complete"))
            except Exception as e:
                self.log(f"Error in NX workflow: {str(e)}")
                self.root.after(0, lambda: self._update_workflow_step("NX Model", "error"))
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
        ttk.Label(about_frame, text="© 2024 Mohammed").pack(pady=5)
        
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

    def save_hpc_settings(self):
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
            
            settings_file = os.path.join(config_dir, "hpc_settings.json")
            with open(settings_file, 'w') as f:
                json.dump(settings, f, indent=4)
            
            self.log("HPC settings saved successfully")
            messagebox.showinfo("Success", "HPC settings saved successfully")
            
            return True
        except Exception as e:
            self.log(f"Error saving HPC settings: {e}")
            messagebox.showerror("Error", f"Failed to save HPC settings: {str(e)}")
            return False

    def load_hpc_settings(self):
        """Load HPC settings from config file"""
        try:
            import os
            import json
            
            config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Config")
            settings_file = os.path.join(config_dir, "hpc_settings.json")
            
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
            ttk.Button(button_frame, text="Save Settings", command=self.save_hpc_settings).pack(side="left", padx=5)
            ttk.Button(button_frame, text="Load Settings", command=self.load_hpc_settings).pack(side="left", padx=5)
            
            # Connection status
            status_frame = ttk.Frame(self.hpc_tab)
            status_frame.pack(fill="x", padx=20, pady=10)
            
            self.connection_status_var = tk.StringVar(value="Status: Not Connected")
            self.connection_status_label = ttk.Label(status_frame, textvariable=self.connection_status_var, foreground="red")
            self.connection_status_label.pack(side="left", padx=5)
            
            # Load HPC settings
            self.load_hpc_settings()
            
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
            self.load_hpc_settings()
            
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
                    command=self.save_hpc_settings).pack(side="left", padx=5)
            
            ttk.Button(button_frame, text="Load Settings", 
                    command=self.load_hpc_settings).pack(side="left", padx=5)
            
            # Connection status
            status_frame = ttk.Frame(self.hpc_tab)
            status_frame.pack(fill="x", padx=20, pady=10)
            
            self.connection_status_var = tk.StringVar(value="Status: Not Connected")
            self.connection_status_label = ttk.Label(status_frame, textvariable=self.connection_status_var, 
                                                foreground="red")
            self.connection_status_label.pack(side="left", padx=5)
            
            # Apply settings from config
            self.apply_hpc_settings()
            
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
                    fix_hpc_gui.ensure_hpc_settings()
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
