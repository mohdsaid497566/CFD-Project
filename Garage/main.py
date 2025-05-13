import os
import sys
import time
import json
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
from tkinter import scrolledtext
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from PIL import Image, ImageTk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from matplotlib import cm
import math
from tkinter import ttk, filedialog, messagebox, scrolledtext
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from matplotlib import cm
from PIL import Image, ImageTk
from Models.Expressions import format_exp, write_exp_file
try:
    import paramiko
    PARAMIKO_AVAILABLE = True
except ImportError:
    PARAMIKO_AVAILABLE = False
    print("Warning: Paramiko SSH library not available. HPC functionality will be disabled.")
# Flag for demonstration mode
DEMO_MODE = True

class Process:
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
        if Process.is_wsl():
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
                return Process.get_nx_command()
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
    def run_nx():
        try:
            if DEMO_MODE:
                print("DEMO MODE: Using mock NX workflow.")
                with open("INTAKE3D.step", "w") as f:
                    f.write("MOCK STEP FILE - This is not a real STEP file\n")
                    f.write("Generated by mock NX workflow\n")
                    f.write(f"Date: {pd.Timestamp.now()}\n")
                    f.write(f"Parameters: Demo run\n")
                return "INTAKE3D.step"
                
            nx_exe = Process.get_nx_command()
            print(f"Using NX executable: {nx_exe}")
            
            express_script = "C:/Users/Mohammed/Desktop/Intake-CFD-Project/nx/nx_express2.py"
            export_script = "C:/Users/Mohammed/Desktop/Intake-CFD-Project/nx/nx_export.py"
            part_file = "C:/Users/Mohammed/Desktop/Intake-CFD-Project/nx/INTAKE3D.prt"
            
            for file_path in [express_script, export_script, part_file]:
                if not os.path.exists(file_path.replace('C:', '/mnt/c')):
                    raise FileNotFoundError(f"Required file not found: {file_path}")
            
            print(f"Running NX script: {express_script} with part: {part_file}")
            Process.run_command([
                nx_exe,
                express_script,
                "-args", part_file
            ])
            
            print(f"Running NX export script: {export_script} with part: {part_file}")
            Process.run_command([
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
                
            Process.run_command(["./gmsh_process", "--input", step_file, "--output", mesh_file, "--auto-refine", "--curvature-adapt"])
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
                
            Process.run_command(["./cfd_solver", "--mesh", mesh_file, "--solver", "openfoam"])
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
                
            Process.run_command(["./process_results", "--input", results_dir, "--output", output_file])
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
            Process.run_command(["./run_tests.sh", "--category", "all"])
        except subprocess.CalledProcessError as e:
            print("Unit tests failed. Please check the output below:")
            print(e.stderr)
            print("Detailed logs can be found in 'error_log.txt'.")
            raise RuntimeError("Unit tests did not pass. Fix the issues and try again.")

class GUI:
    """Main GUI class for the Intake CFD Optimization Suite""" 
    def __init__(self, root):
        """Initialize the GUI with the root Tk window"""
        self.root = root
        self.theme = self.ModernTheme()
        self.theme.apply_theme(root)
        
        # Add application header with logo and title
        # GUI.Workflow.setup_app_header(self, root, self.theme)
        
        self.steps = [
            {'name': 'CAD', 'status': 'pending', 'x': 0.1, 'y': 0.5, 'desc': 'Updates the NX model with parameters'},
            {'name': 'Mesh', 'status': 'pending', 'x': 0.35, 'y': 0.5, 'desc': 'Generates mesh from geometry'},
            {'name': 'CFD', 'status': 'pending', 'x': 0.6, 'y': 0.5, 'desc': 'Runs CFD simulation'},
            {'name': 'Results', 'status': 'pending', 'x': 0.85, 'y': 0.5, 'desc': 'Processes simulation results'}
        ]
                
        # Initialize commonly referenced attributes with defaults
        self.demo_var = tk.BooleanVar(value=DEMO_MODE)
        self.gmsh_path = tk.StringVar(value="")
        self.cfd_path = tk.StringVar(value="")
        self.results_dir = tk.StringVar(value="")
        self.step_file = tk.StringVar(value="")
        self.mesh_file = tk.StringVar(value="")
        self.results_file = tk.StringVar(value="")
        self.hpc_host = tk.StringVar(value="")
        self.parallel_processes = tk.IntVar(value=4)
        self.hpc_username = tk.StringVar(value="")
        self.hpc_password = tk.StringVar(value="")
        self.hpc_key_path = tk.StringVar(value="")
        self.hpc_auth_type = tk.StringVar(value="password")
        self.hpc_key_file = tk.StringVar(value="")
        self.hpc_key_file_path = tk.StringVar(value="")
        self.hpc_key_file_password = tk.StringVar(value="")
        self.hpc_key_file_passphrase = tk.StringVar(value="")
        self.memory_scale = tk.DoubleVar(value=1.0)
        self.results_notebook = None
        self.theme_combo = None
        
        self.theme_var = tk.StringVar(value="Light")
        self.font_size_var = tk.StringVar(value="12")
        self.font_family_var = tk.StringVar(value="Default") 
        self.font_size = 12  # Add this numeric version of font size

        # Initialize visualization frames as None
        self.contour_frame = None
        self.vector_frame = None
        self.slice_frame = None
        
        # Initialize 3D visualization variables
        GUI.elevation_var = tk.IntVar(value=30)
        GUI.azimuth_var = tk.IntVar(value=45)
        self.surface_display_var = tk.StringVar(value="Surface")
        
        self.animation_running = False
        self.animation_timer_id = None

        # Setup the UI components
        self.setup_ui()

        # Load settings
        GUI.Settings.load(self)
        
        # Variable to track if workflow is running
        self.running = False
        self.running = False
        
        # Check for HPC module availability
        if not PARAMIKO_AVAILABLE:
            # Disable HPC functionality
            if hasattr(self, 'notebook') and hasattr(self, 'hpc_tab'):
                self.notebook.tab(self.hpc_tab, state='disabled')
        
        # Initialize demo mode if needed
        if DEMO_MODE:
            GUI.log(self,"Running in demonstration mode")
            # Create mock executables for demonstration
            Process.create_mock_executables()
        
        # Set up basic visualization data structure
        self.visualization_data = {
            'X': None,
            'Y': None,
            'Pressure': None,
            'Velocity': None,
            'Temperature': None,
            'Turbulence': None
        }
                        
        GUI.log(self,"Intake CFD Optimization Suite initialized")
        
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
        def is_system_in_dark_mode(self):
            """Detect if system is using dark mode"""
            # This is a simplified implementation
            # In practice, you would use platform-specific methods
            # For now, just always return False (default to light theme)
            return False
        
        def update_widget_colors(self, widget):
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
                    self.update_widget_colors(child)
                    
            except Exception as e:
                # Just log the error and continue - don't let theme issues crash the app
                print(f"Error updating widget colors: {e}")
                pass
        
        def get_timestamp(self):
            """Get current timestamp for logging"""
            return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    class Workflow:
        def redraw(self):
            """Redraw the workflow visualization with enhanced visuals"""
            if not hasattr(self, 'canvas') or not hasattr(self, 'steps'):
                return
                
            # Clear the canvas
            self.canvas.delete("all")
            
            # Get canvas dimensions
            width = self.canvas.winfo_width()
            height = self.canvas.winfo_height()
            
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
            for i in range(len(self.steps) - 1):
                x1 = int(self.steps[i]["x"] * width)
                y1 = int(self.steps[i]["y"] * height)
                x2 = int(self.steps[i+1]["x"] * width)
                y2 = int(self.steps[i+1]["y"] * height)
                
                # Determine connection appearance based on status
                start_status = self.steps[i]["status"]
                end_status = self.steps[i+1]["status"]
                
                # Base connection
                if start_status == "complete" and end_status == "pending":
                    # Ready for next step - dashed line
                    self.canvas.create_line(
                        x1+25, y1, x2-25, y2, 
                        fill=colors[start_status], 
                        width=2.5, 
                        dash=(6, 3)
                    )
                elif start_status == "running":
                    # Currently running - animated line effect
                    self.canvas.create_line(
                        x1+25, y1, x2-25, y2, 
                        fill=colors[start_status], 
                        width=3
                    )
                    
                    # Add small moving dot for animation effect
                    dot_pos = (datetime.datetime.now().timestamp() * 2) % 1.0
                    dot_x = x1 + (x2 - x1) * dot_pos
                    dot_y = y1 + (y2 - y1) * dot_pos
                    self.canvas.create_oval(
                        dot_x-5, dot_y-5, dot_x+5, dot_y+5,
                        fill=colors[start_status],
                        outline=""
                    )
                    
                    # Schedule redraw for animation
                    self.root.after(50, self.redraw)
                else:
                    # Normal connection
                    self.canvas.create_line(
                        x1+25, y1, x2-25, y2, 
                        fill=colors[start_status], 
                        width=2
                    )
            
            # Draw each step with modern styling
            for step in self.steps:
                x = int(step["x"] * width)
                y = int(step["y"] * height)
                status = step["status"]
                color = colors[status]
                
                # Add shadow for 3D effect
                self.canvas.create_oval(
                    x-22, y-22+3, x+22, y+22+3, 
                    fill="#CCCCCC", 
                    outline=""
                )
                
                # Draw circle with gradient effect
                for i in range(3):
                    size = 22 - i*2
                    # Use the same color for all circles instead of varying alpha
                    self.canvas.create_oval(
                        x-size, y-size, x+size, y+size, 
                        fill=color, 
                        outline=self.theme.primary_color if i == 0 else ""
                    )
                # For running state, add pulsing animation
                if status == "running":
                    pulse_size = 25 + (math.sin(datetime.datetime.now().timestamp() * 5) + 1) * 3
                    self.canvas.create_oval(
                        x-pulse_size, y-pulse_size, x+pulse_size, y+pulse_size, 
                        outline=color, 
                        width=2
                    )
                    
                    # Schedule redraw for animation
                    self.root.after(50, self.redraw)
                
                # Draw step name with shadow for better readability
                self.canvas.create_text(
                    x+1, y+1, 
                    text=step["name"], 
                    fill="#000000", 
                    font=self.theme.header_font
                )
                self.canvas.create_text(
                    x, y, 
                    text=step["name"], 
                    fill="white" if status in ["running", "complete"] else self.theme.text_color, 
                    font=self.theme.header_font
                )
                
                # Draw status text below
                status_y = y + 35
                self.canvas.create_text(
                    x, status_y, 
                    text=status.title(), 
                    fill=self.theme.text_color
                )

        def canvas_click(self, event):
            """Handle clicks on workflow canvas with enhanced interactivity"""
            if not hasattr(self, 'canvas') or not hasattr(self, 'steps'):
                return
                
            # Get canvas dimensions
            width = self.canvas.winfo_width() or 800
            height = self.canvas.winfo_height() or 200
            
            # Check if any step was clicked
            for step in self.steps:
                # Get step position
                x = int(step["x"] * width)
                y = int(step["y"] * height)
                
                # Calculate distance from click to step center
                distance = ((event.x - x) ** 2 + (event.y - y) ** 2) ** 0.5
                
                # If within circle radius, show details in a modern popup
                if distance <= 22:  # Circle radius
                    GUI.Workflow.show_step_details_popup(step, event.x_root, event.y_root)
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
        
        def validate_inputs(self):
            """Validate workflow input parameters"""
            try:
                # Check that all parameters are valid numbers
                L4 = float(self.l4.get())
                L5 = float(self.l5.get())
                alpha1 = float(self.alpha1.get())
                alpha2 = float(self.alpha2.get())
                alpha3 = float(self.alpha3.get())
                
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
    
        def run(self):
            """Execute the complete workflow process"""
            try:
                # Validate inputs before running
                GUI.Workflow.validate_inputs(self)
                # Check if a workflow is already running
                if hasattr(self, 'running') and self.running:
                    messagebox.showwarning("Workflow Running", 
                                            "A workflow is already in progress. Please wait or cancel it first.")
                    return
                
                # Get parameters from UI
                L4 = float(self.l4.get())
                L5 = float(self.l5.get())
                alpha1 = float(self.alpha1.get())
                alpha2 = float(self.alpha2.get())
                alpha3 = float(self.alpha3.get())
                
                # Get execution environment
                env = self.env_var.get() if hasattr(self, 'env_var') else "local"
                
                # Update UI to show processing
                GUI.Settings.update_status(self, "Running simulation workflow...", show_progress=True)
                self.status_text.configure(state='normal')
                self.status_text.delete(1.0, tk.END)
                self.status_text.insert(tk.END, f"Starting workflow with parameters:\n")
                self.status_text.insert(tk.END, f"L4: {L4}, L5: {L5}, Alpha1: {alpha1}, Alpha2: {alpha2}, Alpha3: {alpha3}\n")
                self.status_text.configure(state='disabled')
                
                # Update status in workflow visualization
                for step in self.steps:
                    step["status"] = "pending"
                GUI.Workflow.redraw(self)
                
                # Set workflow running flag
                self.running = True
                self.run_button.config(state="disabled")
                self.cancel_button.config(state="normal")
                
                if env == "local":
                    # Start workflow in separate thread to keep UI responsive
                    self.current_workflow = threading.Thread(
                        target=GUI.Workflow.run_thread,
                        args=(L4, L5, alpha1, alpha2, alpha3),
                        daemon=True
                    )
                    self.current_workflow.start()
                else:  # HPC
                    # Get HPC profile
                    if hasattr(self, 'hpc_profile'):
                        hpc_profile = self.hpc_profile.get()
                        if not hpc_profile:
                            messagebox.showerror("Profile Required", "Please select an HPC profile to continue.")
                            self.running = False
                            self.run_button.config(state="normal")
                            self.cancel_button.config(state="disabled")
                            return
                        
                        # Submit workflow to HPC
                        GUI.Workflow.submit_to_hpc(L4, L5, alpha1, alpha2, alpha3)
                    else:
                        messagebox.showerror("HPC Not Available", "HPC execution is not available.")
                        self.running = False
                        self.run_button.config(state="normal")
                        self.cancel_button.config(state="disabled")
            except ValueError as ve:
                # Handle validation errors
                GUI.log(self,f"Input validation error: {str(ve)}")
                messagebox.showerror("Invalid Input", str(ve))
            except Exception as e:
                # Handle other exceptions
                GUI.log(self,f"Error starting workflow: {str(e)}")
                messagebox.showerror("Error", f"Failed to start workflow: {str(e)}")
                GUI.Settings.update_status(self, "Workflow failed", show_progress=False)

        def run_thread(self, L4, L5, alpha1, alpha2, alpha3):
            """Execute the workflow in a separate thread"""
            try:
                # Set up flag to allow cancellation
                self.cancel = False
                
                # STEP 1: Update NX model using expressions
                self.root.after(0, lambda: GUI.Workflow.update_status("Updating NX model..."))
                self.root.after(0, lambda: self.update_step("CAD", "running"))
                
                # Generate expressions file
                try:
                    Process.exp(L4, L5, alpha1, alpha2, alpha3)
                    GUI.log(self,f"Generated expressions file with parameters: L4={L4}, L5={L5}, Alpha1={alpha1}, Alpha2={alpha2}, Alpha3={alpha3}")
                except Exception as e:
                    GUI.log(self,f"Error generating expressions file: {str(e)}")
                    raise
                
                # Check for cancellation before proceeding
                if self.cancel:
                    self.root.after(0, lambda: self.cancel())
                    return
                    
                # Run NX automation to update model and export STEP
                try:
                    step_file = Process.run_nx()
                    GUI.log(self,f"NX workflow completed, generated: {step_file}")
                    self.root.after(0, lambda: self.update_step("CAD", "complete"))
                except Exception as e:
                    GUI.log(self,f"Error in NX workflow: {str(e)}")
                    self.root.after(0, lambda: self.update_step("CAD", "error"))
                    raise RuntimeError(f"NX workflow failed: {str(e)}")
                
                # Check for cancellation before proceeding
                if self.cancel:
                    self.root.after(0, lambda: self.cancel())
                    return
                    
                # STEP 2: Generate mesh from STEP
                self.root.after(0, lambda: GUI.Workflow.update_status("Generating mesh..."))
                self.root.after(0, lambda: self.update_step("Mesh", "running"))
                
                # Define mesh file
                mesh_file = "INTAKE3D.msh"
                
                # Process mesh
                try:
                    Process.process_mesh(step_file, mesh_file)
                    GUI.log(self,f"Mesh generation completed: {mesh_file}")
                    self.root.after(0, lambda: self.update_step("Mesh", "complete"))
                except Exception as e:
                    GUI.log(self,f"Error in mesh generation: {str(e)}")
                    self.root.after(0, lambda: self.update_step("Mesh", "error"))
                    raise RuntimeError(f"Mesh generation failed: {str(e)}")
                
                # Check for cancellation before proceeding
                if self.cancel:
                    self.root.after(0, lambda: self.cancel())
                    return
                    
                # STEP 3: Run CFD simulation
                self.root.after(0, lambda: GUI.Workflow.update_status("Running CFD simulation..."))
                self.root.after(0, lambda: self.update_step("CFD", "running"))
                
                # Run CFD solver
                try:
                    Process.run_cfd(mesh_file)
                    GUI.log(self,f"CFD simulation completed")
                    self.root.after(0, lambda: self.update_step("CFD", "complete"))
                except Exception as e:
                    GUI.log(self,f"Error in CFD simulation: {str(e)}")
                    self.root.after(0, lambda: self.update_step("CFD", "error"))
                    raise RuntimeError(f"CFD simulation failed: {str(e)}")
                
                # Check for cancellation before proceeding
                if self.cancel:
                    self.root.after(0, lambda: self.cancel())
                    return
                    
                # STEP 4: Process results
                self.root.after(0, lambda: GUI.Workflow.update_status("Processing results..."))
                self.root.after(0, lambda: self.update_step("Results", "running"))
                
                # Define results file
                results_output = "processed_results.csv"
                
                # Process CFD results
                try:
                    Process.process_results("cfd_results", results_output)
                    GUI.log(self,f"Results processing completed: {results_output}")
                    self.root.after(0, lambda: self.update_step("Results", "complete"))
                    
                    # Load and display results
                    self.load_and_display_results(results_output, L4, L5, alpha1, alpha2, alpha3)
                except Exception as e:
                    GUI.log(self,f"Error in results processing: {str(e)}")
                    self.root.after(0, lambda: self.update_step("Results", "error"))
                    raise RuntimeError(f"Results processing failed: {str(e)}")
                
                # Workflow completed successfully
                self.root.after(0, lambda: self.complete())
                
            except Exception as e:
                # Handle uncaught exceptions
                GUI.log(self,f"Workflow error: {str(e)}")
                self.root.after(0, lambda: self.fail(str(e)))

        def complete(self):
            """Handle workflow completion"""
            self.running = False
            self.run_button.config(state="normal")
            self.cancel_button.config(state="disabled")
            
            GUI.Settings.update_status("Workflow completed", show_progress=False)
            messagebox.showinfo("Workflow Complete", "The simulation workflow has completed successfully.")
            
        def cancel(self):
            """Handle workflow cancellation"""
            self.running = False
            self.run_button.config(state="normal")
            self.cancel_button.config(state="disabled")
            
            GUI.Workflow.update_status("Workflow was canceled")
            GUI.Settings.update_status("Workflow canceled", show_progress=False)

        def fail(self, error_message):
            """Handle workflow failure"""
            self.running = False
            self.run_button.config(state="normal")
            self.cancel_button.config(state="disabled")
            
            GUI.Workflow.update_status(f"Workflow failed: {error_message}")
            GUI.Settings.update_status("Workflow failed", show_progress=False)
            messagebox.showerror("Workflow Failed", f"The simulation workflow failed:\n\n{error_message}")

        def cancel_workflow(self):
                """Cancel the running workflow"""
                if not hasattr(self, 'running') or not self.running:
                    return
                    
                answer = messagebox.askyesno("Confirm Cancel", "Are you sure you want to cancel the current workflow?")
                if not answer:
                    return
                    
                GUI.log(self,"User requested workflow cancellation")
                
                # Set cancellation flag for thread to detect
                self.cancel = True
                
                # Disable cancel button while canceling
                self.cancel_button.config(state="disabled")
                GUI.Workflow.update_status("Canceling workflow...")
                GUI.Settings.update_status("Canceling workflow...", show_progress=False)
        
        def submit_to_hpc(self, L4, L5, alpha1, alpha2, alpha3):
            """Submit workflow job to HPC system"""
            try:
                # Check if HPC profile is selected
                if not hasattr(self, 'hpc_profile') or not self.hpc_profile.get():
                    messagebox.showerror("HPC Error", "Please select an HPC profile")
                    self.fail("No HPC profile selected")
                    return
                    
                profile_name = self.hpc_profile.get()
                GUI.Workflow.update_status(f"Preparing to submit job to HPC using profile '{profile_name}'...")
                
                # Create submission dialog
                GUI.HPC.create_submission_dialog(L4, L5, alpha1, alpha2, alpha3, profile_name)
                
            except Exception as e:
                GUI.log(self,f"Error preparing HPC workflow: {str(e)}")
                self.fail(f"Failed to prepare HPC workflow: {str(e)}")

        def load_hpc_profiles(self):
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
                    if hasattr(self, 'hpc_profile'):
                        self.hpc_profile['values'] = list(profiles.keys())
                        if profiles:
                            self.hpc_profile.current(0)  # Select first profile
                    
                    GUI.log(self,f"Loaded {len(profiles)} HPC profiles for workflow")
                else:
                    GUI.log(self,"No HPC profiles found. Please configure HPC settings in the Settings tab.")
                    
            except Exception as e:
                GUI.log(self,self, f"Error loading HPC profiles for workflow: {e}")
        
        def refresh_hpc_profiles(self):
            """Refresh HPC profiles from configuration files"""
            GUI.Workflow.load_hpc_profiles(self)
            GUI.Workflow.update_status("HPC profiles refreshed", 'info')

        def manage_hpc_profiles(self):
            """Open dialog to manage HPC profiles"""
            # Redirect to HPC tab for profile management
            self.notebook.select(self.hpc_tab)
            GUI.Workflow.update_status("Switched to HPC tab for profile management")
            
        def update_status(self, message, status_type='info'):
            """Update the workflow status text with a styled message"""
            if not hasattr(self, 'status_text'):
                GUI.log(self,message)
                return
                
            try:
                # Format timestamp
                timestamp = datetime.datetime.now().strftime("%H:%M:%S")
                
                # Enable editing
                self.status_text.configure(state='normal')
                
                # Insert timestamp with tag
                self.status_text.insert(tk.END, f"[{timestamp}] ", "timestamp")
                
                # Insert message with appropriate status tag
                self.status_text.insert(tk.END, f"{message}\n", status_type)
                
                # Scroll to the end
                self.status_text.see(tk.END)
                
                # Disable editing
                self.status_text.configure(state='disabled')
                
                # Also update the main status bar
                GUI.Workflow.update_status(message)
            except Exception as e:
                GUI.log(self,f"Error updating workflow status: {e}")
    
        def update_step(self, step_name, status, progress=None, time_info=None):
            """Update a workflow step's status and progress"""
            # Update step status in data structure
            for step in self.steps:
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
            GUI.Workflow.redraw(self)
        
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
            
            help_button = ttk.Button(button_frame, text="Help", command=lambda: GUI.Workflow.show_help())
            help_button.pack(side='right', padx=5)
            
            about_button = ttk.Button(button_frame, text="About", command=lambda: GUI.Workflow.show_about(self))
            about_button.pack(side='right', padx=5)
            
        def show_help(self):
            """Show help dialog"""
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
                GUI.log(self,f"Error loading logo: {e}")
            
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
        
        def toggle_execution_environment(self):
            """Toggle between local and HPC execution for workflow"""
            if hasattr(self, 'env_var') and hasattr(self, 'hpc_frame'):
                if self.env_var.get() == "hpc":
                    self.hpc_frame.pack(anchor='w', pady=5)
                else:
                    self.hpc_frame.pack_forget()
        
        def search_log(self):
            """Search the workflow log for specific text"""
            if not hasattr(self, 'status_text'):
                return
            
            # Get search text
            search_text = self.log_search_var.get()
            if not search_text:
                return
            
            # Get text content
            text_content = self.status_text.get(1.0, tk.END)
            
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
            self.status_text.tag_remove("search", "1.0", tk.END)
            for idx in matches:
                # Convert index to line.char format
                line_start = text_content.count('\n', 0, idx) + 1
                char_start = idx - text_content.rfind('\n', 0, idx) - 1
                line_end = line_start
                char_end = char_start + len(search_text)
                
                start_index = f"{line_start}.{char_start}"
                end_index = f"{line_end}.{char_end}"
                
                # Add search tag to highlight match
                self.status_text.tag_add("search", start_index, end_index)
            
            # Configure search tag
            self.status_text.tag_configure("search", background="yellow", foreground="black")
            
            # Scroll to first match
            line_start = text_content.count('\n', 0, matches[0]) + 1
            char_start = matches[0] - text_content.rfind('\n', 0, matches[0]) - 1
            self.status_text.see(f"{line_start}.{char_start}")
            
            # Show message
            messagebox.showinfo("Search", f"Found {len(matches)} matches for '{search_text}'")

        def clear_log(self):
            """Clear the workflow log text area"""
            if hasattr(self, 'status_text'):
                self.status_text.configure(state='normal')
                self.status_text.delete(1.0, tk.END)
                self.status_text.insert(tk.END, "Log cleared. Ready to start workflow.\n")
                self.status_text.configure(state='disabled')
                GUI.Workflow.update_status("Workflow log cleared")      
    class HPC:
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
                GUI.log(self,f"Error toggling auth type: {e}")
                
        def create_default_profiles(self):
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
        
        def apply_profiles(self):
            """Apply loaded HPC settings to UI widgets"""
            try:
                settings = getattr(self, 'hpc_profiles', None)
                if not settings:
                    settings = GUI.Workflow.load_hpc_profiles(self)
                
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
                
                GUI.log(self,"HPC settings applied to UI")
                return True
            except Exception as e:
                GUI.log(self,f"Error applying HPC settings: {e}")
                return False

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
                GUI.Workflow.update_status("No jobs found")
            else:
                GUI.Workflow.update_status(f"Found {len(jobs)} jobs")

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
                        GUI.log(self,f"Error updating script template: {e}")
                
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
                        GUI.Settings.update_status("Submitting job...", show_progress=True)
                        
                        # Submit in a separate thread to keep UI responsive
                        threading.Thread(
                            target=lambda: GUI.HPC.submit_job_script_thread(script_content, profile_name, job_dialog),
                            daemon=True
                        ).start()
                        
                    except Exception as e:
                        GUI.log(self,f"Error preparing job submission: {e}")
                        messagebox.showerror("Error", f"Failed to prepare job: {str(e)}")
                
                ttk.Button(button_frame, text="Submit Job", 
                        command=submit_job_script).pack(side="left", padx=5)
                
                ttk.Button(button_frame, text="Cancel", 
                        command=job_dialog.destroy).pack(side="right", padx=5)
                
                # Update script with initial values
                update_script_template()
                
            except Exception as e:
                GUI.log(self,f"Error creating job submission dialog: {e}")
                messagebox.showerror("Error", f"Failed to create job submission dialog: {str(e)}")

        def submit_job_script_thread(self, script_content, profile_name, dialog=None):
            """Submit a job script to the HPC cluster in a separate thread"""            
            try:
                # Load the HPC profile
                profiles_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                        "Config", "hpc_profiles.json")
                
                if not os.path.exists(profiles_path):
                    self.root.after(0, lambda: messagebox.showerror("Error", "HPC profiles configuration not found"))
                    self.root.after(0, lambda: GUI.Settings.update_status("Job submission failed", show_progress=False))
                    return
                        
                with open(profiles_path, 'r') as f:
                    profiles = json.load(f)
                
                if profile_name not in profiles:
                    self.root.after(0, lambda: messagebox.showerror("Error", f"HPC profile '{profile_name}' not found"))
                    self.root.after(0, lambda: GUI.Settings.update_status("Job submission failed", show_progress=False))
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
                            self.root.after(0, lambda: GUI.Settings.update_status("Job submission failed: Missing key path", show_progress=False))
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
                            self.root.after(0, lambda: GUI.Settings.update_status("Job submission failed: Missing password", show_progress=False))
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
                    self.root.after(0, lambda: GUI.Settings.update_status("Job submission failed: Authentication error", show_progress=False))
                    return
                except paramiko.SSHException as e:
                    self.root.after(0, lambda: messagebox.showerror("SSH Error", f"SSH error: {str(e)}"))
                    self.root.after(0, lambda: GUI.Settings.update_status("Job submission failed: SSH error", show_progress=False))
                    return
                except Exception as e:
                    self.root.after(0, lambda: messagebox.showerror("Connection Error", f"Error connecting to server: {str(e)}"))
                    self.root.after(0, lambda: GUI.Settings.update_status("Job submission failed: Connection error", show_progress=False))
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
                        GUI.log(self,f"Remote directory {remote_dir} does not exist. Creating it...")
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
                        self.root.after(0, lambda: GUI.Settings.update_status("Job submission failed", show_progress=False))
                        client.close()
                        return
                    
                    # Submit job
                    GUI.log(self,f"Submitting job with command: {submission_cmd}")
                    stdin, stdout, stderr = client.exec_command(submission_cmd)
                    response = stdout.read().decode().strip()
                    error = stderr.read().decode().strip()
                    
                    # Close connection
                    client.close()
                    
                    if error and ('error' in error.lower() or 'not found' in error.lower()):
                        GUI.log(self,f"Job submission error: {error}")
                        self.root.after(0, lambda: messagebox.showerror("Submission Error", 
                                                                    f"Failed to submit job: {error}"))
                        self.root.after(0, lambda: GUI.Settings.update_status("Job submission failed", show_progress=False))
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
                        
                        GUI.log(self,success_message)
                        self.root.after(0, lambda: GUI.Settings.update_status(success_message, show_progress=False))
                        self.root.after(0, lambda: messagebox.showinfo("Job Submitted", success_message))
                        
                        # Close the dialog if provided
                        if dialog:
                            self.root.after(0, dialog.destroy)
                        
                        # Refresh job list to show new job
                        if hasattr(self, 'refresh_job_list'):
                            self.root.after(2000, GUI.HPC.refresh_job_list)
                        
                except Exception as e:
                    GUI.log(self,f"Error submitting job: {str(e)}")
                    self.root.after(0, lambda: messagebox.showerror("Submission Error", 
                                                                f"Failed to submit job: {str(e)}"))
                    self.root.after(0, lambda: GUI.Settings.update_status("Job submission failed", show_progress=False))
                    client.close()
            except Exception as e:
                GUI.log(self,f"Error preparing job submission: {str(e)}")
                self.root.after(0, lambda: messagebox.showerror("Error", 
                                                            f"Unexpected error during job submission: {str(e)}"))
                self.root.after(0, lambda: GUI.Settings.update_status("Job submission failed", show_progress=False))

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
                GUI.Settings.update_status(f"Cancelling job {job_id}...", show_progress=True)
                
                # Execute cancellation in separate thread
                threading.Thread(
                    target=lambda: GUI.HPC.cancel_job_thread(profile_name, job_id),
                    daemon=True
                ).start()
                
            except Exception as e:
                GUI.log(self,f"Error preparing job cancellation: {str(e)}")
                messagebox.showerror("Error", f"Failed to prepare job cancellation: {str(e)}")

        def cancel_job_thread(self, profile_name, job_id):
            """Cancel a job in a separate thread"""
            try:
                # Load the HPC profile
                profiles_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                        "Config", "hpc_profiles.json")
                
                if not os.path.exists(profiles_path):
                    self.root.after(0, lambda: messagebox.showerror("Error", "HPC profiles configuration not found"))
                    self.root.after(0, lambda: GUI.Settings.update_status("Job cancellation failed", show_progress=False))
                    return
                    
                with open(profiles_path, 'r') as f:
                    profiles = json.load(f)
                
                if profile_name not in profiles:
                    self.root.after(0, lambda: messagebox.showerror("Error", f"HPC profile '{profile_name}' not found"))
                    self.root.after(0, lambda: GUI.Settings.update_status("Job cancellation failed", show_progress=False))
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
                        self.root.after(0, lambda: GUI.Settings.update_status("Job cancellation failed", show_progress=False))
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
                    self.root.after(0, lambda: GUI.Settings.update_status("Job cancellation failed", show_progress=False))
                    client.close()
                    return
                
                # Execute job cancellation
                stdin, stdout, stderr = client.exec_command(cancel_cmd)
                response = stdout.read().decode().strip()
                error = stderr.read().decode().strip()
                
                # Close connection
                client.close()
                
                if error and 'not found' in error.lower():
                    GUI.log(self,f"Job cancellation error: {error}")
                    self.root.after(0, lambda: messagebox.showerror("Cancellation Error", f"Error cancelling job: {error}"))
                    self.root.after(0, lambda: GUI.Settings.update_status("Job cancellation failed", show_progress=False))
                else:
                    GUI.log(self,f"Job {job_id} cancelled: {response if response else 'Successfully cancelled'}")
                    self.root.after(0, lambda: GUI.Settings.update_status("Job cancelled successfully", show_progress=False))
                    
                    # Show success message
                    self.root.after(0, lambda: messagebox.showinfo("Job Cancelled", f"Job {job_id} has been cancelled"))
                    
                    # Refresh job list after cancellation
                    self.root.after(1000, GUI.HPC.refresh_job_list)
                    
            except Exception as e:
                GUI.log(self,f"Error cancelling job: {str(e)}")
                self.root.after(0, lambda: messagebox.showerror("Cancellation Error", f"Failed to cancel job: {str(e)}"))
                self.root.after(0, lambda: GUI.Settings.update_status("Job cancellation failed", show_progress=False))

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
                GUI.Settings.update_status(f"Fetching details for job {job_id}...", show_progress=True)
                
                # Execute details fetch in separate thread
                threading.Thread(
                    target=lambda: self.get_job_details_thread(profile_name, job_id, job_name),
                    daemon=True
                ).start()
                
            except Exception as e:
                GUI.log(self,f"Error preparing job details retrieval: {str(e)}")
                messagebox.showerror("Error", f"Failed to prepare job details view: {str(e)}")

        def get_job_details_thread(self, profile_name, job_id, job_name):
            """Fetch job details in a separate thread"""            
            try:
                # Load the HPC profile
                profiles_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                        "Config", "hpc_profiles.json")
                
                if not os.path.exists(profiles_path):
                    self.root.after(0, lambda: messagebox.showerror("Error", "HPC profiles configuration not found"))
                    self.root.after(0, lambda: GUI.Settings.update_status("Job details fetch failed", show_progress=False))
                    return
                    
                with open(profiles_path, 'r') as f:
                    profiles = json.load(f)
                
                if profile_name not in profiles:
                    self.root.after(0, lambda: messagebox.showerror("Error", f"HPC profile '{profile_name}' not found"))
                    self.root.after(0, lambda: GUI.Settings.update_status("Job details fetch failed", show_progress=False))
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
                        self.root.after(0, lambda: GUI.Settings.update_status("Job details fetch failed", show_progress=False))
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
                    self.root.after(0, lambda: GUI.Settings.update_status("Job details fetch failed", show_progress=False))
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
                    GUI.log(self,f"Job details error: {error}")
                    self.root.after(0, lambda: messagebox.showerror("Details Error", f"Error fetching job details: {error}"))
                    self.root.after(0, lambda: GUI.Settings.update_status("Job details fetch failed", show_progress=False))
                    return
                    
                if not details:
                    GUI.log(self,f"No details found for job {job_id}")
                    self.root.after(0, lambda: messagebox.showinfo("No Details", f"No details found for job {job_id}"))
                    self.root.after(0, lambda: GUI.Settings.update_status("Job details fetch complete", show_progress=False))
                    return
                    
                # Create job details dialog on main thread
                self.root.after(0, lambda: self.display_job_details(job_id, job_name, scheduler, details, output_files, profile_name))
                self.root.after(0, lambda: GUI.Settings.update_status("Job details fetched successfully", show_progress=False))
                
            except Exception as e:
                GUI.log(self,f"Error fetching job details: {str(e)}")
                self.root.after(0, lambda: messagebox.showerror("Details Error", f"Failed to fetch job details: {str(e)}"))
                self.root.after(0, lambda: GUI.Settings.update_status("Job details fetch failed", show_progress=False))

        def display_job_details(self, job_id, job_name, scheduler, details_text, output_files, profile_name):
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
                        GUI.Settings.update_status(f"Loading file content: {os.path.basename(selected_file)}...", show_progress=True)
                        
                        # Load file content in thread
                        threading.Thread(
                            target=lambda: GUI.HPC.load_remote_file_content(profile_name, selected_file, content_view),
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
                        command=lambda: GUI.HPC.refresh_job_details(
                            job_id, job_name, details_dialog)).pack(side='left')
                
            except Exception as e:
                GUI.log(self,f"Error displaying job details: {str(e)}")
                messagebox.showerror("Display Error", f"Failed to display job details: {str(e)}")

        def load_remote_file_content(self, profile_name, file_path, text_widget):
            """Load content of a remote file"""            
            try:
                # Load the HPC profile
                profiles_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                        "Config", "hpc_profiles.json")
                
                if not os.path.exists(profiles_path):
                    self.root.after(0, lambda: GUI.Settings.update_status("File content fetch failed", show_progress=False))
                    return
                    
                with open(profiles_path, 'r') as f:
                    profiles = json.load(f)
                
                if profile_name not in profiles:
                    self.root.after(0, lambda: GUI.Settings.update_status("File content fetch failed", show_progress=False))
                    return
                    
                config = profiles[profile_name]
                
                # Create SSH client
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                
                # Connect based on authentication method
                if config.get("use_key", False):
                    key_path = config.get("key_path", "")
                    if not key_path:
                        self.root.after(0, lambda: GUI.Settings.update_status("File content fetch failed", show_progress=False))
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
                    GUI.Settings.update_status("File content loaded", show_progress=False)
                    
                self.root.after(0, update_text_widget)
                
            except Exception as e:
                GUI.log(self,f"Error loading remote file content: {str(e)}")
                self.root.after(0, lambda: GUI.Settings.update_status(f"Error: {str(e)}", show_progress=False))

        def refresh_job_details(self, job_id, job_name, dialog=None):
            """Refresh job details"""
            # Close existing dialog if provided
            if dialog:
                dialog.destroy()
            
            # Show job details again
            selection = self.job_tree.selection()
            GUI.HPC.show_job_details(self)

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
                        target=lambda: GUI.HPC.download_results_thread(
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
                GUI.log(self,f"Error setting up download dialog: {str(e)}")
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
            try:
                # Set up cancellation flag
                self.download_canceled = False
                
                # Load the HPC profile
                profiles_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                        "Config", "hpc_profiles.json")
                
                if not os.path.exists(profiles_path):
                    self.status_text(status_text, "Error: HPC profiles configuration not found")
                    self.root.after(0, lambda: GUI.Settings.update_status("Download failed", show_progress=False))
                    return
                    
                with open(profiles_path, 'r') as f:
                    profiles = json.load(f)
                
                if profile_name not in profiles:
                    self.status_text(status_text, f"Error: HPC profile '{profile_name}' not found")
                    self.root.after(0, lambda: GUI.Settings.update_status("Download failed", show_progress=False))
                    return
                    
                config = profiles[profile_name]
                
                # Create SSH client
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                
                # Connect based on authentication method
                if config.get("use_key", False):
                    key_path = config.get("key_path", "")
                    if not key_path:
                        self.status_text(status_text, "Error: No SSH key specified in profile")
                        self.root.after(0, lambda: GUI.Settings.update_status("Download failed", show_progress=False))
            except Exception as e:
                # Handle any exceptions
                GUI.log(self,f"Error downloading results: {str(e)}")
                self.root.after(0, lambda: GUI.Settings.update_status(f"Download failed: {str(e)}", show_progress=False))
                if status_text:
                    self.root.after(0, lambda: self.status_text(status_text, f"Error: {str(e)}"))
    
        def refresh_job_list(self):
            """Refresh the HPC job list"""
            try:
                # Check if we have connection details
                if not hasattr(self, 'conn_profile') or not self.conn_profile.get():
                    messagebox.showerror("Error", "No HPC profile selected.")
                    return
                    
                # Get connection config
                config = GUI.HPC.get_config()
                
                # Clear existing job list
                if hasattr(self, 'job_tree'):
                    for item in self.job_tree.get_children():
                        self.job_tree.delete(item)
                
                GUI.Settings.update_status("Refreshing job list...", show_progress=True)
                
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
                                self.root.after(0, lambda: GUI.Settings.update_status("Error: No key file specified", show_progress=False))
                                return
                            
                            try:
                                key = paramiko.RSAKey.from_private_key_file(key_path)
                                client.connect(hostname=config["hostname"], 
                                            port=config["port"], 
                                            username=config["username"], 
                                            pkey=key, 
                                            timeout=10)
                            except Exception as e:
                                self.root.after(0, lambda: GUI.Settings.update_status(f"Error: {str(e)}", show_progress=False))
                                return
                        else:
                            # Password authentication
                            password = config["password"]
                            if not password:
                                self.root.after(0, lambda: GUI.Settings.update_status("Error: No password provided", show_progress=False))
                                return
                            
                            try:
                                client.connect(hostname=config["hostname"], 
                                            port=config["port"], 
                                            username=config["username"], 
                                            password=password,
                                            timeout=10)
                            except Exception as e:
                                self.root.after(0, lambda: GUI.Settings.update_status(f"Error: {str(e)}", show_progress=False))
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
                            self.root.after(0, lambda: GUI.Settings.update_status("Could not determine job scheduler type", show_progress=False))
                            
                        client.close()
                        
                        # Update UI when complete
                        self.root.after(0, lambda: GUI.Settings.update_status("Job list refreshed successfully", show_progress=False))
                        
                    except Exception as e:
                        GUI.log(self,f"Error fetching HPC jobs: {str(e)}")
                        self.root.after(0, lambda: GUI.Settings.update_status(f"Error: {str(e)}", show_progress=False))
                
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
                    self.root.after(0, lambda: self.HPC.update_job_tree(jobs))
                    
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
                    self.root.after(0, lambda: self.HPC.update_job_tree(jobs))
                    
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
                    self.root.after(0, lambda: self.HPC.update_job_tree(jobs))
                
                # Start the fetch in a separate thread
                threading.Thread(target=fetch_jobs_thread, daemon=True).start()
                
            except ImportError:
                messagebox.showerror("Module Error", "Paramiko SSH library not installed. Install using: pip install paramiko")
            except Exception as e:
                GUI.log(self,f"Error refreshing job list: {e}")
                GUI.Settings.update_status(f"Error: {str(e)}", show_progress=False)
    
        def test_connection(self):
            """Test connection to HPC"""
            try:
                self.connection_status_var.set("Status: Testing...")
                self.connection_status_label.config(foreground="orange")
                
                # Get connection details
                config = GUI.HPC.get_config()
                if not config:
                    return
                    
                # Disable test button during test
                for widget in self.hpc_tab.winfo_children():
                    if isinstance(widget, ttk.Button) and widget.cget("text") == "Test Connection":
                        widget.config(state=tk.DISABLED)
                        break
                
                # Run the test in a thread
                thread = threading.Thread(target=self.HPC.test_connection_thread, args=(config,), daemon=True)
                thread.start()
            except Exception as e:
                GUI.log(self,f"Error testing HPC connection: {e}")
                self.connection_status_var.set(f"Status: Error - {str(e)}")
                self.connection_status_label.config(foreground="red")

        def test_connection_thread(self, config):
            """Thread to test HPC connection"""
            try:            
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
                    self.root.after(0, lambda: GUI.HPC.update_connection_status(True, f"Connected: {result.strip()}"))
                    
                except Exception as e:
                    # Update UI in main thread
                    self.root.after(0, lambda: GUI.HPC.update_connection_status(False, str(e)))
                    
            except Exception as e:
                # Update UI in main thread
                self.root.after(0, lambda: GUI.HPC.update_connection_status(False, f"Error: {str(e)}"))

        def update_connection_status(self, success, message):
            """Update connection status UI"""
            try:
                if success:
                    self.connection_status_var.set(f"Status: Connected")
                    self.connection_status_label.config(foreground="green")
                    GUI.log(self,f"HPC connection successful: {message}")
                else:
                    self.connection_status_var.set(f"Status: Failed")
                    self.connection_status_label.config(foreground="red")
                    GUI.log(self,f"HPC connection failed: {message}")
                    messagebox.showerror("Connection Failed", f"Failed to connect: {message}")
                
                # Re-enable test button
                for widget in self.hpc_tab.winfo_children():
                    if isinstance(widget, ttk.Button) and widget.cget("text") == "Test Connection":
                        widget.config(state=tk.NORMAL)
                        break
            except Exception as e:
                GUI.log(self,f"Error updating connection status: {e}")

        def get_config(self):
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
                GUI.log(self,f"Error getting HPC config: {e}")
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
                config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Config")
                os.makedirs(config_dir, exist_ok=True)
                
                settings_file = os.path.join(config_dir, "hpc_profiles.json")
                with open(settings_file, 'w') as f:
                    json.dump(settings, f, indent=4)
                
                GUI.log(self,"HPC settings saved successfully")
                messagebox.showinfo("Success", "HPC settings saved successfully")
                
                return True
            except Exception as e:
                GUI.log(self,f"Error saving HPC settings: {e}")
                messagebox.showerror("Error", f"Failed to save HPC settings: {str(e)}")
                return False

        def create_submission_dialog(self, L4, L5, alpha1, alpha2, alpha3, profile_name):
            """Create dialog for HPC job submission"""        
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
            script_template = self.create_script_template(job_name_var.get(), nodes_var.get(), cores_var.get(), 
                                                            memory_var.get(), walltime_var.get(), queue_var.get(),
                                                            L4, L5, alpha1, alpha2, alpha3)
            
            script_editor = scrolledtext.ScrolledText(script_frame, wrap=tk.WORD, height=15, width=80)
            script_editor.pack(fill='both', expand=True, padx=5, pady=5)
            script_editor.insert(tk.END, script_template)
            
            # Function to update script template
            def update_script_template():
                script = self.create_script_template(job_name_var.get(), nodes_var.get(), cores_var.get(), 
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
                        
        def create_script_template(self, job_name, nodes, cores, memory, walltime, queue, L4, L5, alpha1, alpha2, alpha3):
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

        def create_hpc_tab_content(self):
            """Create the HPC tab content"""
            # HPC Connection settings
            settings_frame = ttk.LabelFrame(self.hpc_tab, text="HPC Connection Settings")
            settings_frame.pack(fill="x", padx=20, pady=20)
            
            # HPC Host
            host_frame = ttk.Frame(settings_frame)
            host_frame.pack(fill="x", padx=10, pady=5)
            
            ttk.Label(host_frame, text="HPC Host:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
            self.hpc_host = ttk.Entry(host_frame, width=30)
            self.hpc_host.grid(row=0, column=1, padx=5, pady=5, sticky="w")
            
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
            self.hpc_remote_dir = ttk.Entry(host_frame, width=40)
            self.hpc_remote_dir.grid(row=3, column=1, padx=5, pady=5, sticky="w")
            
            # Authentication
            auth_frame = ttk.Frame(settings_frame)
            auth_frame.pack(fill="x", padx=10, pady=10)
            
            ttk.Label(auth_frame, text="Authentication:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
            self.auth_method = tk.StringVar(value="password")
            ttk.Radiobutton(auth_frame, text="Password", variable=self.auth_method, value="password").grid(row=0, column=1, padx=5, pady=5, sticky="w")
            ttk.Radiobutton(auth_frame, text="SSH Key", variable=self.auth_method, value="key").grid(row=0, column=2, padx=5, pady=5, sticky="w")
            
            # SSH Key path
            ttk.Label(auth_frame, text="SSH Key Path:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
            self.key_path = ttk.Entry(auth_frame, width=40)
            self.key_path.grid(row=1, column=1, columnspan=2, padx=5, pady=5, sticky="w")
            
            # Button frame
            button_frame = ttk.Frame(settings_frame)
            button_frame.pack(fill="x", padx=10, pady=10)
            
            ttk.Button(button_frame, text="Test Connection", command=GUI.HPC.test_connection).pack(side="left", padx=5)
            ttk.Button(button_frame, text="Save Settings", command=GUI.HPC.save_hpc_profiles).pack(side="left", padx=5)
            
            # Load settings
            GUI.Workflow.load_hpc_profiles(self)
    class Optimization:
        def initialize_convergence_plot(self):
            """Initialize the convergence plot in the optimization tab"""
            if not hasattr(self, 'ax') or not hasattr(self, 'canvas'):
                return
                
            # Clear any existing plot
            self.ax.clear()
            
            # Set up the axes
            self.ax.set_title("Optimization Convergence")
            self.ax.set_xlabel("Generation")
            self.ax.set_ylabel("Objective Value")
            self.ax.grid(True)
            
            # Initialize empty data for the plot
            self.convergence_data = {
                'generations': [],
                'best_values': [],
                'mean_values': []
            }
            
            # Add a legend placeholder
            self.ax.legend(['Best Value', 'Mean Value'], loc='upper right')
            
            # Draw the canvas
            if hasattr(self, 'canvas'):
                self.canvas.draw()
            
            GUI.log(self,"Convergence plot initialized")

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
            
            GUI.log(self,"Pareto front plot initialized")

        def start(self):
            """Start the optimization process"""
            try:
                # Validate inputs
                GUI.Optimization.validate_inputs(self)
                
                # Check if optimization is already running
                if hasattr(self, 'running') and self.running:
                    messagebox.showwarning("Optimization Running", 
                                        "An optimization is already in progress. Please wait or stop it first.")
                    return
                
                # Get optimization parameters
                method = self.method.get() if hasattr(self, 'method') else "Genetic Algorithm"
                
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
                goal = self.obj_var.get() if hasattr(self, 'obj_var') else "minimize"
                
                # Get execution environment
                env = self.env_var.get() if hasattr(self, 'env_var') else "local"
                
                # Update UI
                self.status_var.set("Initializing optimization...")
                self.progress["value"] = 0
                
                # Initialize plots
                GUI.Optimization.initialize_convergence_plot(self)
                GUI.Optimization.initialize_pareto_front(self)
                
                # Set optimization running flag
                self.running = True
                self.start_button.config(state="disabled")
                
                if env == "local":
                    # Start optimization in a separate thread
                    self.thread = threading.Thread(
                        target=GUI.Optimization.run_thread,
                        args=(method, bounds, pop_size, max_gen, mut_rate, cross_rate, objective, goal),
                        daemon=True
                    )
                    self.thread.start()
                else:  # HPC
                    # Get HPC profile
                    if hasattr(self, 'hpc_profile'):
                        hpc_profile = self.hpc_profile.get()
                        if not hpc_profile:
                            messagebox.showerror("Profile Required", "Please select an HPC profile to continue.")
                            self.running = False
                            self.start_button.config(state="normal")
                            return
                        
                        # Submit optimization to HPC
                        GUI.Optimization.submit_to_hpc(method, bounds, pop_size, max_gen, 
                                                    mut_rate, cross_rate, objective, goal)
                    else:
                        messagebox.showerror("HPC Not Available", "HPC execution is not available.")
                        self.running = False
                        self.start_button.config(state="normal")
                
            except ValueError as ve:
                # Handle validation errors
                GUI.log(self,f"Optimization input validation error: {str(ve)}")
                messagebox.showerror("Invalid Input", str(ve))
            except Exception as e:
                # Handle other exceptions
                GUI.log(self,f"Error starting optimization: {str(e)}")
                messagebox.showerror("Error", f"Failed to start optimization: {str(e)}")
                self.status_var.set("Optimization failed")

        def validate_inputs(self):
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
                if hasattr(self, 'env_var') and self.env_var.get() == "hpc":
                    if hasattr(self, 'hpc_profile') and not self.hpc_profile.get():
                        raise ValueError("Please select an HPC profile")
            
            except ValueError as e:
                if "could not convert string to float" in str(e).lower():
                    raise ValueError("All parameter bounds must be valid numbers")
                raise

        def run_thread(self, method, bounds, pop_size, max_gen, mut_rate, cross_rate, objective, goal):
            """Run optimization in a separate thread"""
            try:
                # Set up flag to allow stopping
                self.stopped = False
                
                # Initialize random population
                GUI.log(self,f"Starting {method} optimization with population size {pop_size}")
                self.root.after(0, lambda: self.status_var.set(f"Generation 1/{max_gen}"))
                
                # Initialize best solution storage
                best_solution = None
                best_fitness = float('inf') if goal == "minimize" else float('-inf')
                
                # Initialize convergence data
                self.convergence_data = {
                    'generations': [],
                    'best_values': [],
                    'mean_values': []
                }
                
                # Simulate optimization iterations
                for gen in range(1, max_gen + 1):
                    # Check if optimization was stopped
                    if self.stopped:
                        self.root.after(0, lambda: self.stopped())
                        return
                        
                    # Update progress
                    progress = (gen / max_gen) * 100
                    self.root.after(0, lambda p=progress: self.progress.config(value=p))
                    self.root.after(0, lambda g=gen: self.status_var.set(f"Generation {g}/{max_gen}"))
                    
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
                        if ((goal == "minimize" and fitness < best_fitness) or 
                            (goal == "maximize" and fitness > best_fitness)):
                            best_fitness = fitness
                            best_solution = solution.copy()
                    
                    # Calculate statistics for this generation
                    mean_fitness = np.mean(pop_fitness)
                    best_gen_fitness = min(pop_fitness) if goal == "minimize" else max(pop_fitness)
                    
                    # Update convergence data
                    self.convergence_data['generations'].append(gen)
                    self.convergence_data['best_values'].append(best_gen_fitness)
                    self.convergence_data['mean_values'].append(mean_fitness)
                    
                    # Update convergence plot
                    self.root.after(0, lambda: GUI.Optimization.update_convergence_plot(self))
                    
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
                        self.root.after(0, lambda: GUI.Optimization.update_pareto_front(self))
                    
                    # Simulate some delay for visual effect
                    time.sleep(0.2)
                
                # Optimization complete
                if best_solution:
                    # Update best design tab with the best solution
                    self.root.after(0, lambda: self.update_best_design(best_solution, best_fitness, objective))
                
                # Mark optimization as complete
                self.root.after(0, lambda: self.complete())
                
            except Exception as e:
                GUI.log(self,f"Optimization error: {str(e)}")
                self.root.after(0, lambda: self.fail(str(e)))

        def update_convergence_plot(self):
            """Update the convergence plot with latest data"""
            if not hasattr(self, 'ax') or not hasattr(self, 'convergence_data'):
                return
                
            # Clear existing plot
            self.ax.clear()
            
            # Plot data if available
            if self.convergence_data['generations']:
                self.ax.plot(self.convergence_data['generations'], 
                                self.convergence_data['best_values'], 
                                'b-', linewidth=2, label='Best Value')
                self.ax.plot(self.convergence_data['generations'], 
                                self.convergence_data['mean_values'], 
                                'r--', linewidth=1, label='Mean Value')
                
            # Update labels
            self.ax.set_title("Optimization Convergence")
            self.ax.set_xlabel("Generation")
            self.ax.set_ylabel("Objective Value")
            self.ax.grid(True)
            
            # Add legend
            self.ax.legend(loc='upper right')
            
            # Redraw the canvas
            self.canvas.draw()

        def update_pareto_front(self):
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

        def update_best_design(self, solution, fitness, objective_name):
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

        def stop(self):
            """Stop the running optimization"""
            if not hasattr(self, 'running') or not self.running:
                return
                
            answer = messagebox.askyesno("Confirm Stop", "Are you sure you want to stop the current optimization?")
            if not answer:
                return
                
            GUI.log(self,"User requested optimization stop")
            
            # Set stopping flag for thread to detect
            self.stopped = True
            
            # Update status
            self.status_var.set("Stopping optimization...")

        def complete(self):
            """Handle optimization completion"""
            self.running = False
            self.start_button.config(state="normal")
            
            self.status_var.set("Optimization completed")
            self.progress["value"] = 100
            
            messagebox.showinfo("Optimization Complete", "The optimization process has completed successfully.")
            
        def stopped(self):
            """Handle optimization being stopped by user"""
            self.running = False
            self.start_button.config(state="normal")
            
            self.status_var.set("Optimization stopped by user")
            
        def fail(self, error_message):
            """Handle optimization failure"""
            self.running = False
            self.start_button.config(state="normal")
            
            self.status_var.set("Optimization failed")
            messagebox.showerror("Optimization Failed", f"The optimization process failed:\n\n{error_message}")

        def import_config(self):
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
                    self.method.set(config['method'])
                    
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
                
                GUI.log(self,f"Imported optimization configuration from {file_path}")
                GUI.Workflow.update_status(f"Imported optimization configuration")
                messagebox.showinfo("Import Complete", "Optimization configuration imported successfully.")
                
            except Exception as e:
                GUI.log(self,f"Error importing optimization configuration: {str(e)}")
                messagebox.showerror("Import Error", f"Failed to import configuration: {str(e)}")

        def export_config(self):
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
                    'method': self.method.get(),
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
                
                GUI.log(self,f"Exported optimization configuration to {file_path}")
                GUI.Workflow.update_status(f"Exported optimization configuration")
                messagebox.showinfo("Export Complete", "Optimization configuration exported successfully.")
                
            except Exception as e:
                GUI.log(self,f"Error exporting optimization configuration: {str(e)}")
                messagebox.showerror("Export Error", f"Failed to export configuration: {str(e)}")

        def submit_to_hpc(self, method, bounds, pop_size, max_gen, mut_rate, cross_rate, objective, goal):
            """Submit optimization job to HPC"""
            try:
                # Get HPC profile
                hpc_profile = self.hpc_profile.get()
                
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
                job_name.insert(0, f"{method}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}")
                
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
                frame = ttk.LabelFrame(main_frame, text="Optimization Parameters", padding=self.theme.padding)
                frame.pack(fill='x', pady=5)
                
                # Create string representation of bounds
                bounds_str = f"""L4: [{bounds['L4'][0]}, {bounds['L4'][1]}]
        L5: [{bounds['L5'][0]}, {bounds['L5'][1]}]
        alpha1: [{bounds['alpha1'][0]}, {bounds['alpha1'][1]}]
        alpha2: [{bounds['alpha2'][0]}, {bounds['alpha2'][1]}]
        alpha3: [{bounds['alpha3'][0]}, {bounds['alpha3'][1]}]"""
                
                ttk.Label(frame, text="Method:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
                ttk.Label(frame, text=method).grid(row=0, column=1, padx=5, pady=5, sticky='w')
                
                ttk.Label(frame, text="Population Size:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
                ttk.Label(frame, text=str(pop_size)).grid(row=1, column=1, padx=5, pady=5, sticky='w')
                
                ttk.Label(frame, text="Max Generations:").grid(row=2, column=0, padx=5, pady=5, sticky='w')
                ttk.Label(frame, text=str(max_gen)).grid(row=2, column=1, padx=5, pady=5, sticky='w')
                
                ttk.Label(frame, text="Parameter Bounds:").grid(row=3, column=0, padx=5, pady=5, sticky='nw')
                ttk.Label(frame, text=bounds_str).grid(row=3, column=1, padx=5, pady=5, sticky='w')
                
                # Job script section
                script_frame = ttk.LabelFrame(main_frame, text="Job Script", padding=self.theme.padding)
                script_frame.pack(fill='both', expand=True, pady=5)
                
                # Create script editor with template
                script_template = "#!/bin/bash\n\n"
                script_template += "#SBATCH --job-name={job_name}\n"
                script_template += "#SBATCH --output=%j.out\n"
                script_template += "#SBATCH --error=%j.err\n"
                script_template += "#SBATCH --partition={queue}\n"
                script_template += "#SBATCH --nodes={nodes}\n"
                script_template += "#SBATCH --ntasks-per-node={cores}\n"
                script_template += "#SBATCH --mem={memory}G\n"
                script_template += "#SBATCH --time={wall_time}\n\n"
                script_template += "# Load required modules\nmodule load python\nmodule load openfoam\n\n"
                script_template += "# Change to working directory\ncd $SLURM_SUBMIT_DIR\n\n"
                script_template += "# Create optimization config file\ncat > config.json << 'EOL'\n"
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
                script_template += "    \"goal\": \"{goal}\"\n"
                script_template += "  }}\n"
                script_template += "}}\n"
                script_template += "EOL\n\n"
                script_template += "# Run the optimization\n"
                script_template += "python -m optimizer --config config.json --parallel {total_cores}\n\n"
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
                            goal=goal
                        )
                        
                        # Update script editor
                        script_editor.delete(1.0, tk.END)
                        script_editor.insert(tk.END, script)
                    except Exception as e:
                        GUI.log(self,f"Error updating script template: {e}")
                
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
                        GUI.Settings.update_status("Submitting optimization to HPC...", show_progress=True)
                        
                        # Submit in a separate thread to keep UI responsive
                        threading.Thread(
                            target=lambda: GUI.HPC.submit_hpc_script(script_content, hpc_profile, job_dialog),
                            daemon=True
                        ).start()
                        
                        # Update status for optimization UI
                        self.status_var.set("Submitted to HPC. Check HPC tab for status.")
                        
                    except Exception as e:
                        GUI.log(self,f"Error preparing job submission: {e}")
                        messagebox.showerror("Error", f"Failed to prepare job: {str(e)}")
                
                ttk.Button(button_frame, text="Submit Job", 
                        command=submit_job_script).pack(side="left", padx=5)
                
                ttk.Button(button_frame, text="Cancel", 
                        command=job_dialog.destroy).pack(side="right", padx=5)
                
                # Mark optimization as submitted
                self.running = False
                self.start_button.config(state="normal")
                
            except Exception as e:
                GUI.log(self,f"Error submitting optimization to HPC: {str(e)}")
                messagebox.showerror("Submission Error", f"Failed to submit optimization to HPC: {str(e)}")
                
                # Reset UI state
                self.running = False
                self.start_button.config(state="normal")
                self.status_var.set("Optimization submission failed")
            
        def toggle_execution_environment(self):
            """Toggle between local and HPC execution for optimization"""
            if hasattr(self, 'env_var') and hasattr(self, 'hpc_profiles_frame'):
                if self.env_var.get() == "hpc":
                    self.hpc_profiles_frame.pack(anchor='w', pady=5)
                else:
                    self.hpc_profiles_frame.pack_forget()

        def load_hpc_profiles(self):
            """Load HPC profiles for optimization tab"""
            
            try:
                profiles_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                        "Config", "hpc_profiles.json")
                
                if os.path.exists(profiles_path):
                    with open(profiles_path, 'r') as f:
                        profiles = json.load(f)
                        
                    if hasattr(self, 'hpc_profile'):
                        self.hpc_profile['values'] = list(profiles.keys())
                        if profiles:
                            self.hpc_profile.current(0)
            except Exception as e:
                GUI.log(self,f"Error loading HPC profiles for optimization: {e}")            
    class Visualization:
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
                GUI.Settings.update_status(f"Importing mesh from {file_path}...", show_progress=True)
                
                # For demonstration, we'll create a sample visualization
                if DEMO_MODE or not GUI.Visualization.load_real_mesh(file_path):
                    self.create_sample_mesh()
                    
                GUI.Settings.update_status(f"Mesh imported successfully", show_progress=False)
                messagebox.showinfo("Import Complete", f"Mesh imported from {os.path.basename(file_path)}")
                
            except Exception as e:
                GUI.log(self,f"Error importing mesh: {str(e)}")
                GUI.Settings.update_status("Mesh import failed", show_progress=False)
                messagebox.showerror("Import Error", f"Failed to import mesh:\n\n{str(e)}")
        
        def load_real_mesh(self, file_path):
            """Load a real mesh file - returns True if successful"""
            try:
                # This would use a proper mesh parser in a real implementation
                # For now, we'll return False to fall back to demo mode
                return False
            except Exception as e:
                GUI.log(self,f"Error loading mesh file: {str(e)}")
                return False
    
        def create_sample_mesh(self):
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
                GUI.Settings.update_status(f"Exporting mesh to {file_path}...", show_progress=True)
                
                # In a real app, this would save the actual mesh
                # For demo, just create a placeholder file
                with open(file_path, 'w') as f:
                    f.write("# Demo Mesh File\n")
                    f.write("# This is a placeholder file for demonstration purposes\n")
                    f.write("# In a real application, this would contain mesh data\n")
                    
                GUI.Settings.update_status(f"Mesh exported successfully", show_progress=False)
                messagebox.showinfo("Export Complete", f"Mesh exported to {os.path.basename(file_path)}")
                
            except Exception as e:
                GUI.log(self,f"Error exporting mesh: {str(e)}")
                GUI.Settings.update_status("Mesh export failed", show_progress=False)
                messagebox.showerror("Export Error", f"Failed to export mesh:\n\n{str(e)}")
        
        def update_mesh_display(self):
            """Update mesh display based on selected options"""
            try:
                display_mode = self.mesh_display_var.get()
                
                # Simply redraw the mesh for demonstration purposes
                self.create_sample_mesh()
                
                # In a real app, you would change the display style based on the mode
                self.mesh_ax.set_title(f"Mesh - {display_mode}")
                self.mesh_canvas.draw()
                
            except Exception as e:
                GUI.log(self,f"Error updating mesh display: {str(e)}")
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
                GUI.Settings.update_status(f"Importing geometry from {file_path}...", show_progress=True)
                
                # For demonstration, we'll create a sample visualization
                if DEMO_MODE or not self.load_real_geometry(file_path):
                    self.create_sample_geometry()
                    
                GUI.Settings.update_status(f"Geometry imported successfully", show_progress=False)
                messagebox.showinfo("Import Complete", f"Geometry imported from {os.path.basename(file_path)}")
                
            except Exception as e:
                GUI.log(self,f"Error importing geometry: {str(e)}")
                GUI.Settings.update_status("Geometry import failed", show_progress=False)
                messagebox.showerror("Import Error", f"Failed to import geometry:\n\n{str(e)}")
        
        def load_real_geometry(self, file_path):
            """Load a real geometry file - returns True if successful"""
            try:
                # This would use a proper CAD parser in a real implementation
                # For now, we'll return False to fall back to demo mode
                return False
            except Exception as e:
                GUI.log(self,f"Error loading geometry file: {str(e)}")
                return False
        
        def create_sample_geometry(self):
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
                GUI.Settings.update_status(f"Exporting geometry to {file_path}...", show_progress=True)
                
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
                    
                GUI.Settings.update_status(f"Geometry exported successfully", show_progress=False)
                messagebox.showinfo("Export Complete", f"Geometry exported to {os.path.basename(file_path)}")
                
            except Exception as e:
                GUI.log(self,f"Error exporting geometry: {str(e)}")
                GUI.Settings.update_status("Geometry export failed", show_progress=False)
                messagebox.showerror("Export Error", f"Failed to export geometry:\n\n{str(e)}")
        
        def update_geometry_display(self):
            """Update geometry display based on selected options"""
            try:
                display_mode = self.geometry_display_var.get()
                
                # Simply redraw the geometry for demonstration purposes
                self.create_sample_geometry()
                
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
                GUI.log(self,f"Error updating geometry display: {str(e)}")
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
                GUI.Settings.update_status(f"Exporting {field_name} results to {file_path}...", show_progress=True)
                
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
                    self.export_to_vtk(file_path, field_name)
                    
                elif file_path.endswith('.npy'):
                    # Export as NumPy array
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
                        
                GUI.Settings.update_status(f"Results exported successfully", show_progress=False)
                messagebox.showinfo("Export Complete", f"Results exported to {os.path.basename(file_path)}")
                
            except Exception as e:
                GUI.log(self,f"Error exporting results: {str(e)}")
                GUI.Settings.update_status("Results export failed", show_progress=False)
                messagebox.showerror("Export Error", f"Failed to export results:\n\n{str(e)}")
        
        def export_to_vtk(self, file_path, field_name):
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
                GUI.log(self,f"Error creating VTK file: {str(e)}")
                raise
              
        def switch_result_view(self, event=None):
            """Switch between different result view types in the Results View tab"""
            view_type = self.view_type_var.get()
            
            # Hide all frames first
            self.cfd_view_frame.pack_forget()
            self.view_3d_frame.pack_forget()
            self.comparison_frame.pack_forget()
            
            # Show the selected frame
            if view_type == "CFD Results":
                self.cfd_view_frame.pack(fill='both', expand=True)
            elif view_type == "3D View":
                self.view_3d_frame.pack(fill='both', expand=True)
            elif view_type == "Comparison":
                self.comparison_frame.pack(fill='both', expand=True)
            
            GUI.log(self,f"Switched to {view_type} view")
            
        def setup_3d_view(self, parent):
            """Setup 3D visualization view"""
            try:
                # Create matplotlib 3D figure
                self.fig_3d = Figure(figsize=(8, 6), dpi=100)
                self.ax_3d = self.fig_3d.add_subplot(111, projection='3d')
                self.canvas_3d = FigureCanvasTkAgg(self.fig_3d, master=parent)
                self.canvas_3d.draw()
                self.canvas_3d.get_tk_widget().pack(fill='both', expand=True)
                
                # Add toolbar
                toolbar_frame = ttk.Frame(parent)
                toolbar_frame.pack(fill='x')
                self.toolbar_3d = NavigationToolbar2Tk(self.canvas_3d, toolbar_frame)
                self.toolbar_3d.update()
                
                # Add some controls specific to 3D view
                controls_frame = ttk.Frame(parent)
                controls_frame.pack(fill='x', pady=5)
                
                ttk.Label(controls_frame, text="Elevation:").grid(row=0, column=0, padx=5, pady=2)
                elevation_slider = ttk.Scale(controls_frame, from_=0, to=90, 
                                            orient='horizontal', length=200,
                                            variable=self.elevation_var,
                                            command=GUI.Visualization.update_3d_view_angle)
                elevation_slider.grid(row=0, column=1, padx=5, pady=2)
                
                ttk.Label(controls_frame, text="Azimuth:").grid(row=1, column=0, padx=5, pady=2)
                azimuth_slider = ttk.Scale(controls_frame, from_=0, to=360, 
                                            orient='horizontal', length=200,
                                            variable=self.azimuth_var,
                                            command=GUI.Visualization.update_3d_view_angle)
                azimuth_slider.grid(row=1, column=1, padx=5, pady=2)
                
                # Draw empty 3D plot
                GUI.Visualization.draw_empty_3d_plot(self)
                
            except Exception as e:
                GUI.log(self,f"Error setting up 3D view: {str(e)}")
                ttk.Label(parent, text=f"Error setting up 3D view: {str(e)}").pack(pady=20)      

        def update_cfd_visualization(self, event=None):
            """Update the CFD visualization based on selected field and visualization type"""
            try:
                # Check if the required components are available
                if not hasattr(self, 'cfd_ax') or not hasattr(self, 'visualization_data'):
                    GUI.log(self,"Warning: Visualization components not initialized")
                    return
                
                # Clear the current plot
                self.cfd_ax.clear()
                
                # Get selected field and visualization type
                field = self.field_var.get() if hasattr(self, 'field_var') else "Pressure"
                viz_type = self.viz_var.get() if hasattr(self, 'viz_var') else "Contour"
                colormap = self.colormap_var.get() if hasattr(self, 'colormap_var') else "viridis"
                
                # Get data range
                vmin, vmax = None, None
                if hasattr(self, 'auto_range_var') and not self.auto_range_var.get():
                    try:
                        vmin = float(self.range_min_var.get())
                        vmax = float(self.range_max_var.get())
                    except (ValueError, TypeError, AttributeError):
                        pass
                
                # Check if we have the necessary data
                if 'X' in self.visualization_data and 'Y' in self.visualization_data and field in self.visualization_data:
                    X = self.visualization_data['X']
                    Y = self.visualization_data['Y']
                    Z = self.visualization_data[field]
                    
                    if X is not None and Y is not None and Z is not None:
                        # Create contour plot as a safe default
                        contour = self.cfd_ax.contourf(X, Y, Z, cmap=colormap, levels=20, vmin=vmin, vmax=vmax)
                        
                        # Add colorbar if requested
                        if hasattr(self, 'show_colorbar_var') and self.show_colorbar_var.get():
                            self.cfd_fig.colorbar(contour, ax=self.cfd_ax)
                        
                        # Set title and labels
                        self.cfd_ax.set_title(f"{field} Visualization")
                        self.cfd_ax.set_xlabel("X")
                        self.cfd_ax.set_ylabel("Y")
                        
                        # Add grid if requested
                        if hasattr(self, 'show_grid_var') and self.show_grid_var.get():
                            self.cfd_ax.grid(True)
                    else:
                        # No data available, show message
                        self.cfd_ax.text(0.5, 0.5, "No data available for selected field",
                                horizontalalignment='center', verticalalignment='center',
                                transform=self.cfd_ax.transAxes)
                else:
                    # No data available, show message
                    self.cfd_ax.text(0.5, 0.5, "No CFD data available.\nRun workflow to generate results.",
                            horizontalalignment='center', verticalalignment='center',
                            transform=self.cfd_ax.transAxes)
                
                # Redraw the canvas if it exists
                if hasattr(self, 'cfd_canvas'):
                    self.cfd_canvas.draw()
                    
            except Exception as e:
                GUI.log(self,f"Error updating CFD visualization: {str(e)}")
                GUI.log(self,f"Detailed error: {traceback.format_exc()}")
                
                # Try to display error in plot if possible
                if hasattr(self, 'cfd_ax'):
                    try:
                        self.cfd_ax.clear()
                        self.cfd_ax.text(0.5, 0.5, f"Error updating visualization:\n{str(e)}",
                                horizontalalignment='center', verticalalignment='center',
                                transform=self.cfd_ax.transAxes, color='red')
                        if hasattr(self, 'cfd_canvas'):
                            self.cfd_canvas.draw()
                    except:
                        pass
        
        def update_statistics(self, data, field_name):
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
                GUI.Settings.update_status(f"Exporting visualization to {file_path}...", show_progress=True)
                
                # Save figure with tight layout and high DPI for quality
                self.cfd_fig.savefig(file_path, dpi=300, bbox_inches='tight')
                
                GUI.Settings.update_status(f"Image exported successfully", show_progress=False)
                messagebox.showinfo("Export Complete", f"Visualization exported to {os.path.basename(file_path)}")
                
            except Exception as e:
                GUI.log(self,f"Error exporting image: {str(e)}")
                GUI.Settings.update_status("Image export failed", show_progress=False)
                messagebox.showerror("Export Error", f"Failed to export image:\n\n{str(e)}")
        
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
                GUI.log(self,f"Error browsing for key file: {e}")
        
        def load_and_display_results(self, results_file, L4, L5, alpha1, alpha2, alpha3):
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
                GUI.Workflow.update_status("Simulation completed successfully!")
                GUI.Workflow.update_status(f"\nParameters: L4={L4}, L5={L5}, Alpha1={alpha1}, Alpha2={alpha2}, Alpha3={alpha3}")
                GUI.Workflow.update_status("\nResults Summary:")
                
                # Simulate extracting key metrics
                pressure_drop = 100 * (0.5 + 0.2 * L4 - 0.1 * L5 + 0.01 * alpha1 + 0.005 * alpha2 + 0.003 * alpha3)
                flow_rate = 50 * (1 + 0.1 * L4 + 0.15 * L5 - 0.01 * alpha1 - 0.02 * alpha2 - 0.01 * alpha3)
                uniformity = 85 * (1 - 0.02 * abs(L4 - 3) - 0.02 * abs(L5 - 3) - 0.01 * abs(alpha1 - 15) - 0.01 * abs(alpha2 - 15) - 0.01 * abs(alpha3 - 15))
                
                GUI.Workflow.update_status(f"Pressure Drop: {pressure_drop:.4f} Pa")
                GUI.Workflow.update_status(f"Flow Rate: {flow_rate:.4f} m³/s")
                GUI.Workflow.update_status(f"Flow Uniformity: {uniformity:.2f}%")
                
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
                GUI.log(self,f"Error loading and displaying results: {str(e)}")
                GUI.Workflow.update_status(f"Error displaying results: {str(e)}") 
        
        def setup_control_panel(self, parent):
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
            field_combo.bind("<<ComboboxSelected>>", GUI.Visualization.update_cfd_visualization(self))
            
            # Visualization type section
            viz_frame = ttk.LabelFrame(parent, text="Visualization Options")
            viz_frame.pack(fill='x', padx=5, pady=5)
            
            ttk.Label(viz_frame, text="Type:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
            self.viz_var = tk.StringVar(value="Contour")
            viz_combo = ttk.Combobox(viz_frame, textvariable=self.viz_var, 
                                    values=["Contour", "Surface", "Vector", "Streamlines", "Slice"],
                                    state="readonly")
            viz_combo.grid(row=0, column=1, padx=5, pady=5, sticky='ew')
            viz_combo.bind("<<ComboboxSelected>>", GUI.Visualization.update_cfd_visualization(self))
            
            # Add more visualization controls here
            
            # Actions section
            action_frame = ttk.LabelFrame(parent, text="Actions")
            action_frame.pack(fill='x', padx=5, pady=5)
            
            ttk.Button(action_frame, text="Update Visualization", 
                    command=GUI.Visualization.update_cfd_visualization(self)).pack(fill='x', padx=5, pady=5)
            ttk.Button(action_frame, text="Export Image", 
                    command=GUI.Visualization.export_cfd_image).pack(fill='x', padx=5, pady=5)
            ttk.Button(action_frame, text="Export Data", 
                    command=GUI.Visualization.export_cfd_results).pack(fill='x', padx=5, pady=5)
    
        def setup_statistics_view(self, parent):
            """Set up statistics view tab"""
            # Create statistics display area
            stats_frame = ttk.Frame(parent)
            stats_frame.pack(fill='both', expand=True, padx=10, pady=10)
            
            # Add statistics text widget
            self.stats_text = scrolledtext.ScrolledText(stats_frame, height=15, width=50, wrap=tk.WORD)
            self.stats_text.pack(fill='both', expand=True, padx=5, pady=5)
            self.stats_text.insert(tk.END, "No data available for statistical analysis")
            self.stats_text.config(state='disabled')
            
            # Add export button
            ttk.Button(stats_frame, text="Export Statistics", 
                    command=GUI.Visualization.export_statistics).pack(pady=10)
        
        def setup_mesh_view(self, parent):
            """Set up mesh visualization tab"""
            mesh_frame = ttk.Frame(parent)
            mesh_frame.pack(fill='both', expand=True, padx=10, pady=10)
            
            # Create 3D figure for mesh visualization
            self.mesh_fig = Figure(figsize=(6, 5), dpi=100)
            self.mesh_ax = self.mesh_fig.add_subplot(111, projection='3d')
            self.mesh_canvas = FigureCanvasTkAgg(self.mesh_fig, master=mesh_frame)
            self.mesh_canvas.draw()
            self.mesh_canvas.get_tk_widget().pack(fill='both', expand=True)
            
            # Add toolbar
            self.mesh_toolbar = NavigationToolbar2Tk(self.mesh_canvas, mesh_frame)
            self.mesh_toolbar.update()
            
            # Add controls for mesh display
            control_frame = ttk.Frame(mesh_frame)
            control_frame.pack(fill='x', pady=10)
            
            ttk.Label(control_frame, text="Display:").pack(side='left', padx=5)
            self.mesh_display_var = tk.StringVar(value="Wireframe")
            mesh_display = ttk.Combobox(control_frame, textvariable=self.mesh_display_var, 
                                        values=["Wireframe", "Surface", "Points"],
                                        state="readonly", width=15)
            mesh_display.pack(side='left', padx=5)
            mesh_display.bind("<<ComboboxSelected>>", lambda _: self.update_mesh_display())
            
            # Add buttons for mesh operations
            btn_frame = ttk.Frame(mesh_frame)
            btn_frame.pack(fill='x', pady=5)
            
            ttk.Button(btn_frame, text="Import Mesh", 
                    command=GUI.Visualization.import_mesh).pack(side='left', padx=5)
            
            ttk.Button(btn_frame, text="Export Mesh", 
                    command=GUI.Visualization.export_mesh).pack(side='left', padx=5)
        
        def export_statistics(self):
            """Export statistics to a text file"""
            file_path = filedialog.asksaveasfilename(
                title="Export Statistics",
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
            )
            
            if not file_path:
                return
                
            try:
                GUI.Settings.update_status(f"Exporting statistics to {file_path}...", show_progress=True)
                
                # Get statistics text
                statistics_text = self.stats_text.get(1.0, tk.END)
                
                # Write to file
                with open(file_path, 'w') as f:
                    f.write(statistics_text)
                    
                GUI.Settings.update_status(f"Statistics exported successfully", show_progress=False)
                messagebox.showinfo("Export Complete", f"Statistics exported to {os.path.basename(file_path)}")
                
            except Exception as e:
                GUI.log(self,f"Error exporting statistics: {str(e)}")
                GUI.Settings.update_status("Statistics export failed", show_progress=False)
                messagebox.showerror("Export Error", f"Failed to export statistics:\n\n{str(e)}")
        
        def setup_comparison_view(self, parent):
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
            compare_mode.bind("<<ComboboxSelected>>", GUI.Visualization.update_comparison)
            
            ttk.Label(control_frame, text="Dataset A:").pack(side='left', padx=(20, 5))
            
            self.dataset_a_var = tk.StringVar()
            dataset_a = ttk.Combobox(
                control_frame, 
                textvariable=self.dataset_a_var,
                values=GUI.Visualization.get_available_datasets(self),
                state="readonly",
                width=15
            )
            dataset_a.pack(side='left', padx=5)
            dataset_a.bind("<<ComboboxSelected>>", GUI.Visualization.update_comparison)
            
            ttk.Label(control_frame, text="Dataset B:").pack(side='left', padx=(20, 5))
            
            self.dataset_b_var = tk.StringVar()
            dataset_b = ttk.Combobox(
                control_frame, 
                textvariable=self.dataset_b_var,
                values=GUI.Visualization.get_available_datasets(self),
                state="readonly",
                width=15
            )
            dataset_b.pack(side='left', padx=5)
            dataset_b.bind("<<ComboboxSelected>>", GUI.Visualization.update_comparison)
            
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

        def setup_display_area(self, parent):
            """Setup the main visualization display area with matplotlib integration"""
            try:
                # Create frame for the visualization
                viz_frame = ttk.Frame(parent)
                viz_frame.pack(fill='both', expand=True, padx=5, pady=5)
                
                # Create matplotlib figure
                self.cfd_fig = Figure(figsize=(8, 6), dpi=100)
                self.cfd_ax = self.cfd_fig.add_subplot(111)
                
                # Create canvas
                self.cfd_canvas = FigureCanvasTkAgg(self.cfd_fig, master=viz_frame)
                self.cfd_canvas.draw()
                self.cfd_canvas.get_tk_widget().pack(fill='both', expand=True)
                
                # Add toolbar
                toolbar_frame = ttk.Frame(viz_frame)
                toolbar_frame.pack(fill='x', pady=5)
                self.cfd_toolbar = NavigationToolbar2Tk(self.cfd_canvas, toolbar_frame)
                self.cfd_toolbar.update()
                
                # Add field selection
                field_frame = ttk.Frame(parent)
                field_frame.pack(fill='x', padx=5, pady=5)
                
                ttk.Label(field_frame, text="Field:").pack(side='left', padx=5)
                self.field_var = tk.StringVar(value="Pressure")
                field_combo = ttk.Combobox(
                    field_frame,
                    textvariable=self.field_var,
                    values=["Pressure", "Velocity", "Temperature", "Turbulence"],
                    state="readonly",
                    width=15
                )
                field_combo.pack(side='left', padx=5)
                field_combo.bind("<<ComboboxSelected>>", GUI.Visualization.update_cfd_visualization(self))
                
                # Add colormap selection
                cmap_frame = ttk.Frame(parent)
                cmap_frame.pack(fill='x', padx=5, pady=5)
                
                ttk.Label(cmap_frame, text="Colormap:").pack(side='left', padx=5)
                self.colormap_var = tk.StringVar(value="viridis")
                colormap_combo = ttk.Combobox(
                    cmap_frame,
                    textvariable=self.colormap_var,
                    values=["viridis", "plasma", "inferno", "jet", "coolwarm", "rainbow"],
                    state="readonly",
                    width=15
                )
                colormap_combo.pack(side='left', padx=5)
                colormap_combo.bind("<<ComboboxSelected>>", GUI.Visualization.update_cfd_visualization(self))
                
                # Range control
                range_frame = ttk.LabelFrame(parent, text="Data Range")
                range_frame.pack(fill='x', padx=5, pady=5)
                
                self.auto_range_var = tk.BooleanVar(value=True)
                ttk.Checkbutton(
                    range_frame, 
                    text="Auto Range",
                    variable=self.auto_range_var,
                    command=GUI.Visualization.toggle_range_inputs
                ).pack(anchor='w', padx=5, pady=2)
                
                # Create range inputs frame
                self.range_inputs_frame = ttk.Frame(range_frame)
                self.range_inputs_frame.pack(fill='x', padx=5, pady=5)
                
                ttk.Label(self.range_inputs_frame, text="Min:").grid(row=0, column=0, padx=5, pady=2, sticky='w')
                self.range_min_var = tk.StringVar(value="0.0")
                ttk.Entry(self.range_inputs_frame, textvariable=self.range_min_var, width=10).grid(row=0, column=1, padx=5, pady=2)
                
                ttk.Label(self.range_inputs_frame, text="Max:").grid(row=1, column=0, padx=5, pady=2, sticky='w')
                self.range_max_var = tk.StringVar(value="1.0")
                ttk.Entry(self.range_inputs_frame, textvariable=self.range_max_var, width=10).grid(row=1, column=1, padx=5, pady=2)
                
                # Options for visualization
                viz_options_frame = ttk.LabelFrame(parent, text="Visualization Options")
                viz_options_frame.pack(fill='x', padx=5, pady=5)
                
                self.viz_var = tk.StringVar(value="Contour")
                viz_types = ["Contour", "Surface", "Vector", "Streamlines", "Isosurface", "Slice"]
                
                # Create a grid for visualization types (3 columns)
                for i, viz_type in enumerate(viz_types):
                    ttk.Radiobutton(
                        viz_options_frame,
                        text=viz_type,
                        variable=self.viz_var,
                        value=viz_type,
                        command=GUI.Visualization.update_cfd_visualization(self)
                    ).grid(row=i//3, column=i%3, padx=10, pady=2, sticky='w')
                
                # Add display options
                display_frame = ttk.LabelFrame(parent, text="Display Options")
                display_frame.pack(fill='x', padx=5, pady=5)
                
                self.show_colorbar_var = tk.BooleanVar(value=True)
                ttk.Checkbutton(
                    display_frame,
                    text="Show Colorbar",
                    variable=self.show_colorbar_var,
                    command=GUI.Visualization.update_cfd_visualization(self)
                ).pack(anchor='w', padx=5, pady=2)
                
                self.show_grid_var = tk.BooleanVar(value=True)
                ttk.Checkbutton(
                    display_frame,
                    text="Show Grid",
                    variable=self.show_grid_var,
                    command=GUI.Visualization.update_cfd_visualization(self)
                ).pack(anchor='w', padx=5, pady=2)
                
                self.show_labels_var = tk.BooleanVar(value=True)
                ttk.Checkbutton(
                    display_frame,
                    text="Show Labels",
                    variable=self.show_labels_var,
                    command=GUI.Visualization.update_cfd_visualization(self)
                ).pack(anchor='w', padx=5, pady=2)
                
                # Special visualization options - initially hidden
                # Contour-specific options
                self.contour_frame = ttk.Frame(parent)
                self.contour_frame.pack(fill='x', padx=5, pady=5)
                
                ttk.Label(self.contour_frame, text="Contour Levels:").pack(side='left', padx=5)
                self.contour_levels_var = tk.StringVar(value="20")
                ttk.Entry(self.contour_frame, textvariable=self.contour_levels_var, width=5).pack(side='left', padx=5)
                ttk.Button(self.contour_frame, text="Apply", command=GUI.Visualization.update_cfd_visualization(self)).pack(side='left', padx=5)
                
                # Vector-specific options
                self.vector_frame = ttk.Frame(parent)
                
                ttk.Label(self.vector_frame, text="Vector Density:").pack(side='left', padx=5)
                self.vector_density_var = tk.StringVar(value="20")
                ttk.Entry(self.vector_frame, textvariable=self.vector_density_var, width=5).pack(side='left', padx=5)
                ttk.Button(self.vector_frame, text="Apply", command=GUI.Visualization.update_cfd_visualization(self)).pack(side='left', padx=5)
                
                # Slice-specific options
                self.slice_frame = ttk.Frame(parent)
                
                ttk.Label(self.slice_frame, text="Slice Position:").pack(side='left', padx=5)
                self.slice_position_var = tk.DoubleVar(value=0.5)
                ttk.Scale(
                    self.slice_frame,
                    from_=0.0,
                    to=1.0,
                    orient='horizontal',
                    variable=self.slice_position_var,
                    command=lambda _: GUI.Visualization.update_cfd_visualization(self)()
                ).pack(side='left', fill='x', expand=True, padx=5)
                
                # Draw placeholder visualization
                GUI.Visualization.draw_placeholder(self)
                
                # Toggle range inputs initially
                GUI.Visualization.toggle_range_inputs(self)
                
            except Exception as e:
                GUI.log(self,f"Error setting up display area: {str(e)}")
                ttk.Label(parent, text=f"Error setting up visualization: {str(e)}").pack(pady=20)

        def update_3d_view_angle(self, event=None):
            """Update the view angle of the 3D plot"""
            if hasattr(self, 'ax_3d'):
                elevation = self.elevation_var.get()
                azimuth = self.azimuth_var.get()
                
                self.ax_3d.view_init(elev=elevation, azim=azimuth)
                
                if hasattr(self, 'canvas_3d'):
                    self.canvas_3d.draw()

        def draw_empty_3d_plot(self, message="No data available"):
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

        def update_comparison(self, event=None):
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
                self.plot_comparison_dataset(self.compare_ax1, dataset_a, "Dataset A")
                
                # Plot dataset B
                self.plot_comparison_dataset(self.compare_ax2, dataset_b, "Dataset B")
                
            elif mode == "Overlay":
                # Create a single plot with both datasets
                ax = self.comparison_fig.add_subplot(111)
                
                # Plot both datasets with different colors/styles
                self.plot_comparison_dataset(ax, dataset_a, "Dataset A", color='blue', alpha=0.7)
                self.plot_comparison_dataset(ax, dataset_b, "Dataset B", color='red', alpha=0.7)
                
                # Add legend
                ax.legend()
                
            elif mode == "Difference":
                # Create a single plot showing the difference
                ax = self.comparison_fig.add_subplot(111)
                
                # Calculate and plot difference
                self.plot_difference(ax, dataset_a, dataset_b)
            
            # Update the canvas
            self.comparison_canvas.draw()

        def plot_comparison_dataset(self, ax, dataset_name, label, **kwargs):
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

        def plot_difference(self, ax, dataset_a, dataset_b):
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

        def draw_placeholder(self):
            """Draw a placeholder visualization when no data is available"""
            try:
                # Clear the axis
                self.cfd_ax.clear()
                
                # Add a text message
                self.cfd_ax.text(0.5, 0.5, "No CFD data available.\nRun workflow to generate results.",
                        horizontalalignment='center', verticalalignment='center',
                        transform=self.cfd_ax.transAxes, fontsize=14)
                
                # Set axis limits
                self.cfd_ax.set_xlim(0, 1)
                self.cfd_ax.set_ylim(0, 1)
                
                # Hide ticks
                self.cfd_ax.set_xticks([])
                self.cfd_ax.set_yticks([])
                
                # Draw the canvas
                self.cfd_canvas.draw()
                
            except Exception as e:
                GUI.log(self,f"Error drawing placeholder: {str(e)}")
        
        def toggle_range_inputs(self):
            """Toggle min/max range inputs based on auto range setting"""
            if not hasattr(self, 'range_inputs_frame'):
                return
                
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
            GUI.Visualization.update_cfd_visualization(self)
        
        def get_available_datasets(self):
            """Get list of available datasets"""
            # In a real application, this would look at actual data files
            # For now, return some placeholder datasets
            return ["Current", "Previous Run", "Baseline", "Optimized"]
        
    class Settings:
        def font_family(self):
            """Apply just the font family change without changing size"""
            try:
                # Get the selected font family
                font_family = GUI.Settings.font_family_var.get()
                
                # Apply the font family at the current font size
                current_size = self.font_size if hasattr(self, 'font_size') else 12
                GUI.Settings.font_size(current_size, font_family)
                
                # Update the preview if it exists
                if hasattr(self, 'font_preview'):
                    # Use the actual font to show a preview
                    preview_font = (font_family if font_family != "Default" else "TkDefaultFont", 
                                current_size, "normal")
                    self.font_preview.config(font=preview_font)
                    
                GUI.log(self,f"Font family updated to {font_family}")
                
            except Exception as e:
                GUI.log(self,f"Error applying font family: {e}")
                messagebox.showerror("Font Error", 
                                    f"Could not apply font family '{font_family}'. It may not be available on your system.")
            
        def font_size(self, size_num, font_family=None):
            """Apply font size settings based on numeric value
            
            Args:
                size_num: Numeric font size (can be int or float)
            """
            try:
                # Convert input to a number if it's a string
                if isinstance(size_num, str):
                    size_num = float(size_num)
                        
                # Ensure we have a valid positive number
                if size_num <= 0:
                    size_num = 10  # Default to medium size
                
                # Store the numeric font size value
                self.font_size = size_num
                if font_family is None and hasattr(self, 'font_family_var'):
                    font_family = self.font_family_var.get()

                # Default to Segoe UI if nothing is specified
                if font_family is None or font_family == "Default":
                        font_family = "Bookman"
                                            
                # Calculate proportional sizes for different UI elements
                small = max(int(size_num * 0.8), 6)  # Minimum 6pt
                normal = int(size_num)
                large = int(size_num * 1.2)
                    
                # Update theme font sizes
                self.theme.small_font = (font_family, small)
                self.theme.normal_font = (font_family, normal)
                self.theme.header_font = (font_family, large, "bold")
                self.theme.button_font = (font_family, normal)
                self.theme.code_font = ("Consolas", small+1)
            
                if font_family == "Courier":
                    self.theme.code_font = (font_family, small+1)
                else:
                    self.theme.code_font = ("Consolas", small+1)

                # Update font_size_var to match the applied size
                if hasattr(self, 'font_size_var'):
                    self.font_size_var.set(str(size_num))
                        
                if hasattr(self, 'font_family_var'):
                    current = self.font_family_var.get()
                    if current != font_family and font_family != "Default":
                        self.font_family_var.set(font_family)

                # Apply theme to reapply fonts
                self.theme.apply_theme(self.root)
                    
                # Log the change
                GUI.log(self,f"Font size updated to {size_num}")
                    
            except (ValueError, TypeError) as e:
                # Handle conversion errors
                GUI.log(self,f"Error applying font size: {e}")
                # Fall back to a default size
                self.font_size = 12  # Set default here too
                self.theme.small_font = ("Segoe UI", 10)
                self.theme.normal_font = ("Segoe UI", 12)
                self.theme.header_font = ("Segoe UI", 14, "bold")
                self.theme.button_font = ("Segoe UI", 12)
                self.theme.code_font = ("Consolas", 11)
                self.theme.apply_theme(self.root)
                
        def appearance_settings(self):
            """Apply selected appearance settings"""
            if hasattr(self, 'theme_combo') and self.theme_combo is not None:
                theme_name = self.theme_combo.get()
            else:
                theme_name = self.theme_var.get() if hasattr(self, 'theme_var') else "Light"
            
            font_size = self.font_size_var.get()
            font_family = self.font_family_var.get() if hasattr(self, 'font_family_var') else "Default"

            GUI.log(self,f"Applying appearance settings: Theme={theme_name}, Font Size={font_size}")
            
            try:
                # Apply theme
                if theme_name == "Dark":
                    GUI.Settings.dark_theme()
                elif theme_name == "Light":
                    GUI.Settings.light_theme()
                elif theme_name == "System":
                    GUI.Settings.system_theme()
                
                size_num = None
                if font_size == "8":
                    size_num = 8
                elif font_size == "12":
                    size_num = 12
                elif font_size == "16":
                    size_num = 16
                else:
                    # If it's not one of the predefined options, try to convert it to a number
                    try:
                        size_num = float(font_size)
                    except ValueError:
                        GUI.log(self,f"Invalid font size: {font_size}, defaulting to 12")
                        size_num = 12  # Default to size 12 if conversion fails
                            
                if size_num is not None:
                    GUI.Settings.font_size(size_num, font_family)
                                    
                messagebox.showinfo("Settings Applied", "Appearance settings have been applied.")
                GUI.Workflow.update_status("Appearance settings applied")
            except Exception as e:
                GUI.log(self,f"Error applying appearance settings: {e}")
                messagebox.showerror("Error", f"Failed to apply appearance settings: {e}")
                                                     
        def available_fonts(self):
            """Get a list of available fonts on the system"""
            try:
                import tkinter.font as tkfont
                
                # Get available fonts from the system
                available_fonts = sorted(list(set(tkfont.families())))
                
                # Filter out special font names and duplicates
                filtered_fonts = []
                for font in available_fonts:
                    # Skip fonts that start with @ (vertical fonts on Windows)
                    if not font.startswith('@') and font not in filtered_fonts:
                        filtered_fonts.append(font)
                
                return filtered_fonts
            except Exception as e:
                GUI.log(self,f"Error getting available fonts: {e}")
                # Return safe defaults
                return ["Default", "Arial", "Helvetica", "Times", "Courier", "Verdana"]
    
        def light_theme(self):
            """Apply light theme to the application"""
            self.theme.primary_color = "#4a6fa5"  # Blue
            self.theme.secondary_color = "#45b29d"  # Teal
            self.theme.bg_color = "#f5f5f5"  # Light gray
            self.theme.text_color = "#333333"  # Dark gray
            self.theme.border_color = "#dddddd"  # Light gray border
            
            # Apply theme to the root window
            self.theme.apply_theme(self.root)
            
            # Switch to light theme variants for all canvases
            if hasattr(self, 'canvas'):
                self.canvas.configure(bg="white", highlightbackground="#dddddd")
            
            # Update status
            GUI.Workflow.update_status("Applied light theme")
            
            # Redraw workflow if available
            if hasattr(self, 'redraw'):
                GUI.Workflow.redraw()
            
        def save(self):
            """Save settings to a configuration file"""
            try:
                # Collect settings
                settings = {
                    "general": {
                        "project_dir": self.project_dir_var.get() if hasattr(self, 'project_dir_var') else "",
                        "nx_path": self.nx_path_var.get() if hasattr(self, 'nx_path_var') else "",
                        # Added gmsh_path with proper hasattr check
                        "gmsh_path": self.gmsh_path.get() if hasattr(self, 'gmsh_path') else "",
                        "cores": self.cores_var.get() if hasattr(self, 'cores_var') else "1",
                        "debug": self.debug_var.get() if hasattr(self, 'debug_var') else False,
                        "demo_mode": self.demo_var.get() if hasattr(self, 'demo_var') else False
                    },
                    "appearance": {
                        "theme": self.theme_var.get() if hasattr(self, 'theme_var') else "Light",
                        "font_size": self.font_size_var.get() if hasattr(self, 'font_size_var') else "12",
                        "font_family": self.font_family_var.get() if hasattr(self, 'font_family_var') else "Default"
                    }
                }
                
                # Save to file
                with open("settings.json", "w") as f:
                    json.dump(settings, f, indent=4)
                    
                GUI.Workflow.update_status("Settings saved successfully")
                messagebox.showinfo("Settings Saved", "Your settings have been saved successfully.")
                
            except Exception as e:
                GUI.log(self,f"Error saving settings: {str(e)}")
                messagebox.showerror("Error", f"Failed to save settings: {str(e)}")
                    
        def load(self):
            """Load settings from configuration file"""
            try:
                if not os.path.exists("settings.json"):
                    GUI.log(self,"Settings file not found, using defaults")
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
                        
                    if "font_size" in app and hasattr(self, 'font_size_var'):
                        self.font_size_var.set(app["font_size"])
                        GUI.Settings.appearance_settings()
                
                    if "font_family" in app and hasattr(self, 'font_family_var'):
                        self.font_family_var.set(app["font_family"])
                
                GUI.log(self,"Settings loaded successfully")
                
            except Exception as e:
                GUI.log(self,f"Error loading settings: {str(e)}")
                # Don't show an error dialog here since this is called during initialization
        
        def reset(self):
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
                
                if hasattr(self, 'font_family_var'):
                    self.font_family_var.set("Default")
                # Apply reset settings
                GUI.Settings.appearance_settings()
                
                # Delete settings file if it exists
                if os.path.exists("settings.json"):
                    os.remove("settings.json")
                
                GUI.Workflow.update_status("Settings reset to defaults")
                messagebox.showinfo("Settings Reset", "All settings have been reset to their default values.")
                
            except Exception as e:
                GUI.log(self,f"Error resetting settings: {str(e)}")
                messagebox.showerror("Error", f"Failed to reset settings: {str(e)}")
        
        def check_updates(self):
            """Check for application updates"""
            # In a real app, this would connect to a server to check for updates
            # For this demo, just show a message
            messagebox.showinfo("Update Check", "You are using the latest version of the Intake CFD Optimization Suite.")
    
        def show_diagnostics_result(self, results, memory_message, disk_message):
            """Display system diagnostics results in a formatted message box"""
            try:
                # Create a dialog to show results
                result_dialog = tk.Toplevel(self.root)
                result_dialog.title("Diagnostics Results")
                result_dialog.geometry("600x400")
                result_dialog.transient(self.root)
                result_dialog.grab_set()
                
                # Add content
                main_frame = ttk.Frame(result_dialog, padding=10)
                main_frame.pack(fill='both', expand=True)
                
                ttk.Label(main_frame, text="System Diagnostics Results", 
                        font=self.theme.header_font).pack(pady=10)
                
                # Display results in a scrolled text widget
                results_text = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, height=15, width=70)
                results_text.pack(fill='both', expand=True, pady=10)
                
                # Format and insert results
                results_text.insert(tk.END, "=== SYSTEM DIAGNOSTICS SUMMARY ===\n\n")
                
                # Insert system info
                results_text.insert(tk.END, f"Memory: {memory_message}\n")
                results_text.insert(tk.END, f"Disk: {disk_message}\n\n")
                
                # Insert test results or error messages
                results_text.insert(tk.END, "--- Detailed Results ---\n")
                for test, result in results.items():
                    results_text.insert(tk.END, f"{test}: {result}\n")
                
                # Add close button
                ttk.Button(main_frame, text="Close", 
                        command=result_dialog.destroy).pack(pady=10)
                
            except Exception as e:
                GUI.log(self,f"Error showing diagnostics results: {str(e)}")
                messagebox.showerror("Error", f"Failed to display diagnostics results: {str(e)}")
            
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
                    GUI.Settings.run_diagnostics_thread(status_var, results_text, progress, close_button)
                except Exception as e:
                    # Handle errors
                    GUI.log(self,f"Diagnostics error: {str(e)}")
                    # Create a dictionary with the error message instead of passing the string directly
                    error_dict = {"Error": str(e)}
                    # Use _show_diagnostics_result with appropriate error messages
                    self.root.after(0, lambda: GUI.Settings.show_diagnostics_result(error_dict, "Memory info unavailable", "Disk info unavailable"))
                    self.root.after(0, lambda: status_var.set("Diagnostics failed"))
                    self.root.after(0, lambda: progress.stop())
                    self.root.after(0, lambda: close_button.config(state='normal'))
            
            # Start diagnostics thread
            threading.Thread(target=run_thread, daemon=True).start()

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
                GUI.log(self,f"Error getting memory info: {e}")
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
                GUI.log(self,f"Updated NX path: {file_path}")
    
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
            GUI.Settings.update_memory_usage(self)

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
            
            GUI.log(self,message)

        def update_memory_display(self):
            """Update the memory usage display in the settings tab"""
            try:
                # Get memory information
                memory_info = GUI.Settings.get_memory_info(self)
                
                # Update the progress bar and label if they exist
                if hasattr(self, 'memory_bar') and self.memory_bar is not None:
                    if memory_info and 'percent' in memory_info:
                        self.memory_bar['value'] = memory_info['percent']
                        memory_text = f"Memory: {memory_info['used']:.1f} GB / {memory_info['total']:.1f} GB ({memory_info['percent']}%)"
                        if hasattr(self, 'memory_label') and self.memory_label is not None:
                            self.memory_label.config(text=memory_text)
                
                # IMPORTANT: Schedule the next update correctly
                # Use a lambda to avoid immediate execution
                self.root.after(5000, lambda: self.update_memory_display())
                
            except Exception as e:
                # Log error without causing more recursion
                print(f"Error updating memory display: {str(e)}")
                # Still schedule next update to try again
                self.root.after(5000, lambda: self.update_memory_display())


        def update_memory_usage(self):
            """Update the memory usage display"""
            if hasattr(self, 'memory_var'):
                try:
                    memory_info = GUI.Settings.get_memory_info(self).split(",")[0]  # Just get the total part
                    self.memory_var.set(f"Memory: {memory_info}")
                except:
                    self.memory_var.set("Memory: --")
            
            # Schedule next update
            self.root.after(10000, lambda: GUI.Settings.update_memory_usage(self))  # Update every 10 seconds   
            
        def browse_project_dir(self):
                """Open directory browser to select project directory"""
                dir_path = filedialog.askdirectory(
                    title="Select Project Directory"
                )
                if dir_path:
                    self.project_dir.delete(0, tk.END)
                    self.project_dir.insert(0, dir_path)
                    GUI.log(self,f"Updated project directory: {dir_path}")
            
        def dark_theme(self):
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
                            
        def system_theme(self):
                """Apply system-based theme"""
                try:
                    # Try to detect system theme (simplified approach)
                    if platform.system() == "Windows":
                        import winreg
                        registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
                        key = winreg.OpenKey(registry, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
                        value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                        
                        if value == 0:
                            GUI.Settings.dark_theme()
                        else:
                            GUI.Settings.light_theme()
                    else:
                        # Default to light theme for other platforms
                        GUI.Settings.light_theme()
                except Exception:
                    # If detection fails, fall back to light theme
                    GUI.Settings.light_theme()
            
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
        GUI.setup_workflow_tab(self)
        GUI.setup_visualization_tab(self)
        GUI.setup_optimization_tab(self)
        GUI.setup_hpc_tab(self)
        GUI.setup_settings_tab(self)
        
        # Set up status bar
        GUI.Settings.setup_status_bar(self)
        
        GUI.log(self,"UI setup complete")
        
    def setup_optimization_tab(self):
        """Set up the Optimization tab"""
        # Main frame for optimization tab
        outer_frame, main_frame = GUI.create_scrollable_frame(self, self.optimization_tab, 
                                                            bg=self.theme.bg_color,
                                                            highlightthickness=0)
        outer_frame.pack(fill='both', expand=True)

        # Split into input panel and results panel
        left_pane = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        left_pane.pack(fill='both', expand=True, padx=self.theme.padding, pady=self.theme.padding)

        # Create scrollable frame specifically for input section
        input_scroll_frame, input_inner = GUI.create_scrollable_frame(self, left_pane, 
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
        self.method = ttk.Combobox(method_frame, values=[
            "Gradient Descent", "Genetic Algorithm", "Particle Swarm", "Bayesian Optimization"
        ])
        self.method.pack(fill='x', pady=5)
        self.method.current(1)  # Default to Genetic Algorithm
        
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
        self.env_var = tk.StringVar(value="local")
        
        # Add radio buttons with more padding and clearer styling
        local_radio = ttk.Radiobutton(exec_frame, text="Local Execution", 
                                    variable=self.env_var, value="local",
                                    command=GUI.Optimization.toggle_execution_environment)
        local_radio.pack(anchor='w', pady=4, padx=10)  # Increased padding
        
        hpc_radio = ttk.Radiobutton(exec_frame, text="HPC Execution", 
                                  variable=self.env_var, value="hpc",
                                  command=GUI.Optimization.toggle_execution_environment)
        hpc_radio.pack(anchor='w', pady=4, padx=10)  # Increased padding
        
        # HPC settings frame with better visibility
        self.hpc_profiles_frame = ttk.Frame(exec_frame, padding=5)
        self.hpc_profiles_frame.pack(fill='x', pady=5, padx=5)  # Fill horizontally with padding
        
        ttk.Label(self.hpc_profiles_frame, text="HPC Profile:").pack(side="left", padx=5)
        self.hpc_profile = ttk.Combobox(self.hpc_profiles_frame, width=20)
        self.hpc_profile.pack(side="left", padx=5, fill='x', expand=True)
        
        # Add a visual separator to make the section more distinct
        ttk.Separator(exec_frame, orient='horizontal').pack(fill='x', pady=5)
        
        # Load HPC profiles for optimization
        GUI.Optimization.load_hpc_profiles(self)
        
        # Buttons
        button_frame = ttk.Frame(input_frame)
        button_frame.pack(fill='x', pady=10)
        
        self.start_button = ttk.Button(button_frame, text="Start Optimization", 
                                        command=lambda: GUI.Optimization.start())
        self.start_button.pack(side="left", padx=5)
        
        ttk.Button(button_frame, text="Stop", command=lambda: GUI.Optimization.stop()).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Import Config", 
                command=lambda: GUI.Optimization.import_config()).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Export Config", 
                command=lambda: GUI.Optimization.export_config()).pack(side="left", padx=5)
        
        # Results display section - create notebook for different result views
        self.notebook = ttk.Notebook(results_frame)
        self.notebook.pack(fill='both', expand=True)
        
        # Convergence history tab
        self.conv_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.conv_tab, text="Convergence")
        
        # Set up matplotlib figure for convergence plot
        self.fig = Figure(figsize=(6, 5), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.conv_tab)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill='both', expand=True)
        
        # Add toolbar
        toolbar_frame = ttk.Frame(self.conv_tab)
        toolbar_frame.pack(fill='x', expand=False)
        self.toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        self.toolbar.update()
        
        # Pareto front tab for multi-objective optimization
        self.pareto_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.pareto_tab, text="Pareto Front")
        
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
        self.best_design_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.best_design_tab, text="Best Design")
        
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
        self.progress = ttk.Progressbar(progress_frame, orient='horizontal', length=300, mode='determinate')
        self.progress.pack(side='left', padx=5, expand=True, fill='x')
        
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(progress_frame, textvariable=self.status_var).pack(side='right', padx=5)
        
        # Initialize plots
        GUI.Optimization.initialize_convergence_plot(self)
        GUI.Optimization.initialize_pareto_front(self)
        
        # Hide HPC settings initially
        self.hpc_profiles_frame.pack_forget()
        
        GUI.log(self,"Optimization tab initialized")
    
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
        self.l4 = ttk.Entry(l4_frame, width=10)
        self.l4.pack(side='right', padx=5)
        self.l4.insert(0, "3.0")
        
        # L5 parameter
        l5_frame = ttk.Frame(param_entry_frame)
        l5_frame.pack(fill='x', pady=2)
        ttk.Label(l5_frame, text="L5:").pack(side='left', padx=5)
        self.l5 = ttk.Entry(l5_frame, width=10)
        self.l5.pack(side='right', padx=5)
        self.l5.insert(0, "3.0")
        
        # Alpha1 parameter
        alpha1_frame = ttk.Frame(param_entry_frame)
        alpha1_frame.pack(fill='x', pady=2)
        ttk.Label(alpha1_frame, text="Alpha1:").pack(side='left', padx=5)
        self.alpha1 = ttk.Entry(alpha1_frame, width=10)
        self.alpha1.pack(side='right', padx=5)
        self.alpha1.insert(0, "15.0")
        
        # Alpha2 parameter
        alpha2_frame = ttk.Frame(param_entry_frame)
        alpha2_frame.pack(fill='x', pady=2)
        ttk.Label(alpha2_frame, text="Alpha2:").pack(side='left', padx=5)
        self.alpha2 = ttk.Entry(alpha2_frame, width=10)
        self.alpha2.pack(side='right', padx=5)
        self.alpha2.insert(0, "15.0")
        
        # Alpha3 parameter
        alpha3_frame = ttk.Frame(param_entry_frame)
        alpha3_frame.pack(fill='x', pady=2)
        ttk.Label(alpha3_frame, text="Alpha3:").pack(side='left', padx=5)
        self.alpha3 = ttk.Entry(alpha3_frame, width=10)
        self.alpha3.pack(side='right', padx=5)
        self.alpha3.insert(0, "15.0")
        
        # Execution environment
        env_frame = ttk.LabelFrame(parameters_frame, text="Execution Environment", padding=5)
        env_frame.pack(fill='x', pady=10)  # Using pack() instead of grid()
        
        # Radio buttons for execution environment
        self.env_var = tk.StringVar(value="local")
        ttk.Radiobutton(env_frame, text="Local Execution", 
                    variable=self.env_var, value="local",
                    command=GUI.Workflow.toggle_execution_environment(self)).pack(anchor='w', pady=2)
        ttk.Radiobutton(env_frame, text="HPC Execution", 
                    variable=self.env_var, value="hpc",
                    command=GUI.Workflow.toggle_execution_environment(self)).pack(anchor='w', pady=2)
        
        # HPC settings (initially hidden)
        self.hpc_frame = ttk.Frame(env_frame)
        
        ttk.Label(self.hpc_frame, text="HPC Profile:").pack(side="left", padx=5)
        self.hpc_profile = ttk.Combobox(self.hpc_frame, width=20)
        self.hpc_profile.pack(side="left", padx=5)
        
        # Load HPC profiles for workflow
        GUI.Workflow.load_hpc_profiles(self)
        
        # Hide HPC settings initially
        self.hpc_frame.pack_forget()
        
        # Run/Cancel buttons
        button_frame = ttk.Frame(parameters_frame)
        button_frame.pack(pady=10)  # Using pack() instead of grid()
        
        status_frame = ttk.LabelFrame(workflow_frame, text="Status")
        status_frame.pack(fill='x', expand=False, padx=5, pady=5)
        
        self.status_text = scrolledtext.ScrolledText(status_frame, height=10, wrap=tk.WORD)

        self.run_button = ttk.Button(button_frame, text="Run Workflow", command=GUI.Workflow.run(self))
        self.run_button.pack(side="left", padx=5)
        
        self.cancel_button = ttk.Button(button_frame, text="Cancel", command=GUI.Workflow.cancel, state="disabled")
        self.cancel_button.pack(side="left", padx=5)
                
        # Workflow visualization
        viz_frame = ttk.Frame(workflow_frame)
        viz_frame.pack(fill='both', expand=True)
        
        # Create canvas for workflow visualization
        self.canvas = tk.Canvas(viz_frame, bg="white", height=120)
        self.canvas.pack(fill='both', expand=True, padx=5, pady=5)
        self.canvas.bind("<Button-1>", GUI.Workflow.canvas_click)
        
        # Draw the workflow
        GUI.Workflow.redraw(self)
        
        # Status text area
        status_frame = ttk.LabelFrame(workflow_frame, text="Status")
        status_frame.pack(fill='x', expand=False, padx=5, pady=5)
        
        self.status_text = scrolledtext.ScrolledText(status_frame, height=10, wrap=tk.WORD)
        self.status_text.pack(fill='both', expand=True, padx=5, pady=5)
        self.status_text.insert(tk.END, "Ready to start workflow. Set parameters and click 'Run Workflow'.")
        self.status_text.config(state='disabled')
        
        GUI.log(self,"Workflow tab initialized")
        
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
                 command=GUI.Settings.browse_project_dir).grid(row=0, column=2, padx=5, pady=5)
        
        # NX path settings
        nx_frame = ttk.LabelFrame(general_tab, text="NX Integration", padding=10)
        nx_frame.pack(fill='x', pady=5, padx=5)
        
        ttk.Label(nx_frame, text="NX Executable:").grid(row=0, column=0, sticky='w', pady=5)
        self.nx_path_var = tk.StringVar()
        nx_entry = ttk.Entry(nx_frame, textvariable=self.nx_path_var, width=40)
        nx_entry.grid(row=0, column=1, sticky='ew', padx=5, pady=5)
        ttk.Button(nx_frame, text="Browse...", 
                 command=GUI.Settings.browse_nx_path).grid(row=0, column=2, padx=5, pady=5)
        
        # Appearance settings tab
        appearance_tab = ttk.Frame(settings_notebook)
        settings_notebook.add(appearance_tab, text="Appearance")
        
        # Theme settings
        theme_frame = ttk.LabelFrame(appearance_tab, text="Theme", padding=10)
        theme_frame.pack(fill='x', pady=5, padx=5)
        
        self.theme_var = tk.StringVar(value="system")
        ttk.Radiobutton(theme_frame, text="System", variable=self.theme_var, 
                      value="system", command=GUI.Settings.system_theme).grid(
                      row=0, column=0, sticky='w', pady=5)
        ttk.Radiobutton(theme_frame, text="Light", variable=self.theme_var, 
                      value="light", command=GUI.Settings.light_theme).grid(
                      row=0, column=1, sticky='w', pady=5)
        ttk.Radiobutton(theme_frame, text="Dark", variable=self.theme_var, 
                      value="dark", command=GUI.Settings.dark_theme).grid(
                      row=0, column=2, sticky='w', pady=5)
        
        # Font size settings
        font_frame = ttk.LabelFrame(appearance_tab, text="Font Size", padding=10)
        font_frame.pack(fill='x', pady=5, padx=5)
        
        self.font_size_var = tk.StringVar(value="normal")
        ttk.Radiobutton(font_frame, text="8", variable=self.font_size_var, 
                    value="small", command=lambda: GUI.Settings.font_size(8)).grid(
                    row=0, column=0, sticky='w', pady=5)
        ttk.Radiobutton(font_frame, text="12", variable=self.font_size_var, 
                    value="normal", command=lambda: GUI.Settings.font_size(10)).grid(
                    row=0, column=1, sticky='w', pady=5)
        ttk.Radiobutton(font_frame, text="16", variable=self.font_size_var, 
                    value="large", command=lambda: GUI.Settings.font_size(12)).grid(
                    row=0, column=2, sticky='w', pady=5)
        
        font_family_frame = ttk.LabelFrame(appearance_tab, text="Font Family", padding=10)
        font_family_frame.pack(fill='x', pady=5, padx=5)

        available_fonts = GUI.Settings.available_fonts(self)
        
        self.font_family_var = tk.StringVar(value="Default")
                        
        if len(available_fonts) > 6:
            ttk.Label(font_family_frame, text="Fonts:").pack(anchor='w', pady=(10, 2))
            self.additional_font_var = tk.StringVar()
            additional_font_combo = ttk.Combobox(font_family_frame, textvariable=self.additional_font_var, 
                                            values=available_fonts, state="readonly")
        additional_font_combo.pack(fill='x', pady=2)
        
        def apply_selected_font(event):
            selected = self.additional_font_var.get()
            if selected:
                self.font_family_var.set(selected)
                GUI.Settings.font_family()
        
        additional_font_combo.bind("<<ComboboxSelected>>", apply_selected_font)        
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
                 command=GUI.Settings.update_memory_display(self)).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Run Diagnostics", 
                 command=GUI.Settings.run_diagnostics).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Check for Updates", 
                 command=GUI.Settings.check_updates).pack(side='left', padx=5)
        
        # Buttons at the bottom
        button_frame = ttk.Frame(settings_frame)
        button_frame.pack(fill='x', pady=10)
        
        ttk.Button(button_frame, text="Save Settings", 
                 command=GUI.Settings.save).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Reset to Default", 
                 command=GUI.Settings.reset).pack(side='left', padx=5)
        
        GUI.log(self,"Settings tab initialized")
        
        # Update memory info
        GUI.Settings.update_memory_display(self)
   
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
                    GUI.log(self,"Rebuilding existing HPC tab")
                    break
            else:
                # Create new HPC tab
                self.hpc_tab = ttk.Frame(self.notebook)
                self.notebook.add(self.hpc_tab, text="HPC")
                GUI.log(self,"Created new HPC tab")
                GUI.HPC.create_hpc_tab_content(self)
            # Load settings first to use for defaults
            GUI.Workflow.load_hpc_profiles(self)
            
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
                            value="password", command=GUI.HPC.toggle_auth_type).pack(anchor="w", padx=10, pady=5)
            ttk.Radiobutton(auth_frame, text="Key File", variable=self.auth_type, 
                            value="key", command=GUI.HPC.toggle_auth_type).pack(anchor="w", padx=10, pady=5)
            
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
            ttk.Button(self.key_frame, text="Browse...", command=GUI.Visualization.browse_key_file).grid(row=0, column=2, padx=5, pady=5)
            
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
                                                command=GUI.HPC.test_connection)
            self.test_connection_button.pack(side="left", padx=5)
            
            ttk.Button(button_frame, text="Save Settings", 
                    command=GUI.HPC.save_hpc_profiles).pack(side="left", padx=5)
            
            ttk.Button(button_frame, text="Load Settings", 
                    command=GUI.Workflow.load_hpc_profiles).pack(side="left", padx=5)
            
            # Connection status
            status_frame = ttk.Frame(self.hpc_tab)
            status_frame.pack(fill="x", padx=20, pady=10)
            
            self.connection_status_var = tk.StringVar(value="Status: Not Connected")
            self.connection_status_label = ttk.Label(status_frame, textvariable=self.connection_status_var, 
                                                foreground="red")
            self.connection_status_label.pack(side="left", padx=5)
            
            # Apply settings from config
            GUI.HPC.apply_profiles(self)
            
            # Initialize with default auth type
            GUI.HPC.toggle_auth_type(self)
            
            GUI.log(self,"HPC tab initialized successfully")
            return True
        except Exception as e:
            GUI.log(self,f"Error initializing HPC tab: {e}")
            print(f"Error initializing HPC tab: {e}")
            print(traceback.format_exc())
            return False
   
    def setup_visualization_tab(self):
        """Set up the visualization tab with proper notebook structure"""
        # Create main container with scrollable functionality
        outer_frame, main_frame = GUI.create_scrollable_frame(self, self.visualization_tab, 
                                                        bg=self.theme.bg_color,
                                                        highlightthickness=0)
        outer_frame.pack(fill='both', expand=True)
        
        # Create a horizontal paned window for control panel and visualization area
        paned_window = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Left control panel
        control_panel = ttk.Frame(paned_window)
        
        # Right visualization area 
        visualization_area = ttk.Frame(paned_window)
        
        # Add both to the paned window
        paned_window.add(control_panel, weight=1)
        paned_window.add(visualization_area, weight=3)
        
        # Set up visualization controls in the control panel
        GUI.Visualization.setup_control_panel(self, control_panel)
        
        # Create a single notebook for different result views in the visualization area
        self.results_notebook = ttk.Notebook(visualization_area)
        self.results_notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Create results view tab with integrated visualization display
        self.cfd_results_tab = ttk.Frame(self.results_notebook)
        self.results_notebook.add(self.cfd_results_tab, text="Results View")
        
        # Create main visualization display frame
        viz_display_frame = ttk.Frame(self.cfd_results_tab)
        viz_display_frame.pack(fill='both', expand=True)
        
        # Create visualization options bar at the top of the results view
        options_bar = ttk.Frame(viz_display_frame)
        options_bar.pack(fill='x', padx=5, pady=5)
        
        # Add viz type selector in the options bar
        ttk.Label(options_bar, text="View:").pack(side='left', padx=5)
        view_types = ["CFD Results", "3D View", "Comparison"]
        self.view_type_var = tk.StringVar(value="CFD Results")
        view_type_combo = ttk.Combobox(options_bar, textvariable=self.view_type_var, 
                                    values=view_types, state="readonly", width=15)
        view_type_combo.pack(side='left', padx=5)
        view_type_combo.bind("<<ComboboxSelected>>", GUI.Visualization.switch_result_view)
        
        # Create a frame stack to hold different view types
        self.view_stack_frame = ttk.Frame(viz_display_frame)
        self.view_stack_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Create container frames for each view type (only one will be visible at a time)
        self.cfd_view_frame = ttk.Frame(self.view_stack_frame)
        self.view_3d_frame = ttk.Frame(self.view_stack_frame)
        self.comparison_frame = ttk.Frame(self.view_stack_frame)
        
        # Setup the actual visualization display in each view frame
        GUI.Visualization.setup_display_area(self, self.cfd_view_frame)
        GUI.Visualization.setup_3d_view(self, self.view_3d_frame)
        GUI.Visualization.setup_comparison_view(self, self.comparison_frame)
        
        # Default to showing CFD view
        self.cfd_view_frame.pack(fill='both', expand=True)
        
        # Add additional tabs for statistics and mesh at the same level as Results View
        self.statistics_tab = ttk.Frame(self.results_notebook)
        self.results_notebook.add(self.statistics_tab, text="Statistics")
        GUI.Visualization.setup_statistics_view(self, self.statistics_tab)
        
        # Add tab for mesh visualization
        self.mesh_tab = ttk.Frame(self.results_notebook)
        self.results_notebook.add(self.mesh_tab, text="Mesh")
        GUI.Visualization.setup_mesh_view(self, self.mesh_tab)
        
        GUI.log(self,"Visualization tab initialized")
          
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
        if hasattr(self, 'status_text'):
            try:
                self.status_text.configure(state='normal')
                self.status_text.insert(tk.END, log_message + "\n")
                self.status_text.see(tk.END)
                self.status_text.configure(state='disabled')
            except:
                pass
        
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
        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        inner_frame.bind("<Configure>", on_frame_configure)
        
        # Update canvas window width when canvas size changes
        def on_canvas_configure(event):
            min_width = inner_frame.winfo_reqwidth()
            if event.width > min_width:
                # If canvas is wider than inner frame, expand inner frame
                canvas.itemconfig(window_id, width=event.width)
            else:
                # Otherwise, keep inner frame at its minimum width
                canvas.itemconfig(window_id, width=min_width)
        
        canvas.bind("<Configure>", on_canvas_configure)
        
        # Bind mouse wheel to scroll
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind_all("<MouseWheel>", on_mousewheel)
        
        # For Linux, bind mousewheel differently
        canvas.bind("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))
        
        return outer_frame, inner_frame
        
# Main function that serves as the entry point for the application
def main():
    """Main entry point for the Intake CFD Optimization Suite application."""    
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
            Process.create_mock_executables()
            logger.info("Created mock executables for demonstration mode")
        
        # Import HPC module utilities as needed
        try:
            from Utils import workflow_utils
            logger.info("Loaded workflow utilities")
        except ImportError as e:
            logger.warning(f"Could not load workflow utilities: {e}")
            
        # Try to load workflow utilities and HPC modules
        try:
            from Utils import workflow_utils
            logger.info("Workflow utilities loaded successfully")
            
            # Try to import HPC modules
            try:
                from HPC import hpc_integration
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
                    workflow_utils.patch_workflow_gui(GUI)
                    logger.info("GUI patched with HPC functionality")
                
                # If fix_hpc_gui is available, use it to further enhance HPC functionality
                try:
                    from GUI import fix_hpc_gui
                    # Update workflow utils
                    fix_hpc_gui.update_workflow_utils()
                    # Ensure HPC settings exist
                    fix_hpc_gui.ensure_hpc_profiles()
                    # Patch the GUI class
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
        app = GUI(root)
        
        # Apply HPC integration if available
        try:
            from HPC.hpc_integration import initialize_hpc
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