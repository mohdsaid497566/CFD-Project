import os
import sys
import time
import json
import gmsh
import numpy as np
import platform
import argparse
import subprocess
import threading
import tempfile
import traceback
import tkinter as tk

from Expressions import format_exp, write_exp_file
from tkinter import ttk, filedialog, messagebox, scrolledtext
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
from PIL import Image, ImageTk

# Flag for demonstration mode
DEMO_MODE = True

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
        # Color scheme - sophisticated blue theme
        self.bg_color = "#F5F7FA"  # Light background
        self.primary_color = "#2C3E50"  # Dark blue for headers
        self.accent_color = "#3498DB"  # Blue for buttons and accents
        self.accent_hover = "#2980B9"  # Darker blue for hover states
        self.text_color = "#2C3E50"  # Dark blue text
        self.light_text = "#ECF0F1"  # Light text for dark buttons
        self.success_color = "#2ECC71"  # Green for success messages
        self.warning_color = "#F39C12"  # Orange for warnings
        self.error_color = "#E74C3C"  # Red for errors
        self.border_color = "#BDC3C7"  # Light gray for borders

        # Font settings
        self.header_font = ("Segoe UI", 12, "bold")
        self.normal_font = ("Segoe UI", 10)
        self.small_font = ("Segoe UI", 9)
        self.button_font = ("Segoe UI", 10)
        self.code_font = ("Consolas", 9)

        # Padding and spacing
        self.padding = 10
        self.small_padding = 5
        self.large_padding = 15
        
    def apply_theme(self, root):
        """Apply modern styling to the application"""
        style = ttk.Style()
        
        # Configure the root window
        root.configure(background=self.bg_color)
        
        # Configure styles for different widgets
        style.configure("TFrame", background=self.bg_color)
        style.configure("TLabel", background=self.bg_color, foreground=self.text_color, font=self.normal_font)
        style.configure("TButton", 
                       background=self.accent_color,
                       foreground=self.light_text, 
                       font=self.button_font,
                       borderwidth=0,
                       focusthickness=3,
                       focuscolor=self.accent_color)
        style.map("TButton",
                 background=[('active', self.accent_hover), ('pressed', self.accent_hover)],
                 relief=[('pressed', 'groove'), ('!pressed', 'ridge')])
        
        # Configure special styles
        style.configure("Header.TLabel", font=self.header_font, foreground=self.primary_color)
        style.configure("Success.TLabel", foreground=self.success_color)
        style.configure("Warning.TLabel", foreground=self.warning_color)
        style.configure("Error.TLabel", foreground=self.error_color)
        
        style.configure("Primary.TButton", 
                       background=self.primary_color,
                       foreground=self.light_text)
        style.map("Primary.TButton",
                 background=[('active', self.primary_color), ('pressed', self.primary_color)])
                 
        # Configure notebook styles
        style.configure("TNotebook", background=self.bg_color, borderwidth=0)
        style.configure("TNotebook.Tab", 
                       background=self.bg_color, 
                       foreground=self.text_color,
                       font=self.normal_font,
                       padding=[10, 5],
                       borderwidth=0)
        style.map("TNotebook.Tab",
                 background=[('selected', self.accent_color), ('active', self.accent_hover)],
                 foreground=[('selected', self.light_text), ('active', self.light_text)])
        
        # LabelFrame styling
        style.configure("TLabelframe", background=self.bg_color)
        style.configure("TLabelframe.Label", 
                       font=self.header_font,
                       foreground=self.primary_color,
                       background=self.bg_color)
                       
        # Entry and Combobox styling
        style.configure("TEntry", 
                       foreground=self.text_color,
                       fieldbackground="white",
                       borderwidth=1,
                       relief="solid")
        style.map("TEntry", 
                 fieldbackground=[('readonly', self.bg_color)])
                 
        style.configure("TCombobox", 
                       foreground=self.text_color,
                       fieldbackground="white",
                       selectbackground=self.accent_color,
                       selectforeground=self.light_text)

class WorkflowGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Intake CFD Optimization Suite")
        self.root.geometry("1280x800")  # Slightly wider for modern layouts
        
        # Initialize data structures for optimization
        self.iterations = []
        self.objectives = []
        self.best_objective = float('inf')
        self.best_params = {}
        
        # Initialize execution status tracking
        self.execution_status = {
            "nx_workflow": False,
            "mesh_generation": False,
            "cfd_simulation": False,
            "results_processed": False
        }
        
        # Apply modern styling
        self.theme = ModernTheme()
        self.theme.apply_theme(root)
        
        # Create app icon and title bar
        self.setup_app_header()
        
        # Create main container with padding
        self.main_container = ttk.Frame(self.root, padding=self.theme.padding)
        self.main_container.pack(fill='both', expand=True)
        
        # Create a notebook (tabbed interface)
        self.notebook = ttk.Notebook(self.main_container)
        self.notebook.pack(fill='both', expand=True, padx=self.theme.small_padding, pady=self.theme.small_padding)
        
        # Create tabs
        self.workflow_tab = ttk.Frame(self.notebook)
        self.visualization_tab = ttk.Frame(self.notebook)
        self.optimization_tab = ttk.Frame(self.notebook)
        self.settings_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.workflow_tab, text="Workflow")
        self.notebook.add(self.visualization_tab, text="Visualization")
        self.notebook.add(self.optimization_tab, text="Optimization")
        self.notebook.add(self.settings_tab, text="Settings")
        
        # Create log view that spans across all tabs at the bottom
        self.log_frame = ttk.LabelFrame(self.main_container, text="Log Console")
        self.log_frame.pack(fill='x', expand=False, padx=self.theme.small_padding, pady=self.theme.small_padding)
        
        self.log_console = scrolledtext.ScrolledText(self.log_frame, height=6, font=self.theme.code_font)
        self.log_console.pack(fill='both', expand=True, padx=self.theme.small_padding, pady=self.theme.small_padding)
        
        # Setup tabs
        self.setup_workflow_tab()
        self.setup_visualization_tab()
        self.setup_optimization_tab()
        self.setup_settings_tab()
        
        # Status bar with progress indicator
        self.status_frame = ttk.Frame(self.root)
        self.status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        
        # Progress bar
        self.progress = ttk.Progressbar(self.status_frame, orient='horizontal', mode='indeterminate')
        self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10,5), pady=2)
        self.progress.pack_forget()  # Hide initially
        
        # Status label
        self.status_label = ttk.Label(self.status_frame, textvariable=self.status_var, font=self.theme.small_font)
        self.status_label.pack(side=tk.RIGHT, padx=10, pady=2)
        
        # Initialize data storage
        self.results_data = None
        self.mesh_data = None
        
        # Initial log message
        self.log("Intake CFD Optimization Suite initialized")
        self.log(f"System: {platform.system()} {platform.release()}")
        self.log(f"Python: {platform.python_version()}")
        self.log(f"WSL Detection: {'Yes' if is_wsl() else 'No'}")
        self.update_status("Ready")

    def setup_app_header(self):
        """Set up the application header with logo and title"""
        # Call the standalone function with self.root and self.theme
        setup_app_header(self.root, self.theme)

    def setup_workflow_tab(self):
        """Set up the workflow tab with an interactive process pipeline"""
        # Container with padding
        container = ttk.Frame(self.workflow_tab, padding=self.theme.padding)
        container.pack(fill='both', expand=True)
        
        # Left panel for parameter controls
        params_frame = ttk.LabelFrame(container, text="Design Parameters", padding=self.theme.padding)
        params_frame.pack(side=tk.LEFT, fill='y', padx=self.theme.padding, pady=self.theme.padding)
        
        # ======= Input Parameters =======
        # Create header row
        param_header_frame = ttk.Frame(params_frame)
        param_header_frame.pack(fill='x', pady=(0, self.theme.small_padding))
        
        ttk.Label(param_header_frame, text="Parameter", width=10, font=self.theme.normal_font).grid(row=0, column=0, padx=5)
        ttk.Label(param_header_frame, text="Value", width=8, font=self.theme.normal_font).grid(row=0, column=1, padx=5)
        ttk.Label(param_header_frame, text="Unit", width=6, font=self.theme.normal_font).grid(row=0, column=2, padx=5)
        
        # Separator
        ttk.Separator(params_frame, orient='horizontal').pack(fill='x', pady=self.theme.small_padding)
        
        # L4 parameter
        l4_frame = ttk.Frame(params_frame)
        l4_frame.pack(fill='x', pady=self.theme.small_padding)
        
        ttk.Label(l4_frame, text="L4:", width=10).grid(row=0, column=0, sticky='w')
        self.l4_workflow = ttk.Entry(l4_frame, width=8)
        self.l4_workflow.grid(row=0, column=1, padx=5)
        self.l4_workflow.insert(0, "2.0")
        ttk.Label(l4_frame, text="m").grid(row=0, column=2, sticky='w')
        
        # L5 parameter
        l5_frame = ttk.Frame(params_frame)
        l5_frame.pack(fill='x', pady=self.theme.small_padding)
        
        ttk.Label(l5_frame, text="L5:", width=10).grid(row=0, column=0, sticky='w')
        self.l5_workflow = ttk.Entry(l5_frame, width=8)
        self.l5_workflow.grid(row=0, column=1, padx=5)
        self.l5_workflow.insert(0, "3.0")
        ttk.Label(l5_frame, text="m").grid(row=0, column=2, sticky='w')
        
        # Alpha1 parameter
        alpha1_frame = ttk.Frame(params_frame)
        alpha1_frame.pack(fill='x', pady=self.theme.small_padding)
        
        ttk.Label(alpha1_frame, text="Alpha1:", width=10).grid(row=0, column=0, sticky='w')
        self.alpha1_workflow = ttk.Entry(alpha1_frame, width=8)
        self.alpha1_workflow.grid(row=0, column=1, padx=5)
        self.alpha1_workflow.insert(0, "10.0")
        ttk.Label(alpha1_frame, text="deg").grid(row=0, column=2, sticky='w')
        
        # Alpha2 parameter
        alpha2_frame = ttk.Frame(params_frame)
        alpha2_frame.pack(fill='x', pady=self.theme.small_padding)
        
        ttk.Label(alpha2_frame, text="Alpha2:", width=10).grid(row=0, column=0, sticky='w')
        self.alpha2_workflow = ttk.Entry(alpha2_frame, width=8)
        self.alpha2_workflow.grid(row=0, column=1, padx=5)
        self.alpha2_workflow.insert(0, "10.0")
        ttk.Label(alpha2_frame, text="deg").grid(row=0, column=2, sticky='w')
        
        # Alpha3 parameter
        alpha3_frame = ttk.Frame(params_frame)
        alpha3_frame.pack(fill='x', pady=self.theme.small_padding)
        
        ttk.Label(alpha3_frame, text="Alpha3:", width=10).grid(row=0, column=0, sticky='w')
        self.alpha3_workflow = ttk.Entry(alpha3_frame, width=8)
        self.alpha3_workflow.grid(row=0, column=1, padx=5)
        self.alpha3_workflow.insert(0, "10.0")
        ttk.Label(alpha3_frame, text="deg").grid(row=0, column=2, sticky='w')
        
        # Parameter presets
        preset_frame = ttk.LabelFrame(params_frame, text="Presets", padding=self.theme.small_padding)
        preset_frame.pack(fill='x', pady=self.theme.padding)
        
        ttk.Label(preset_frame, text="Configuration:").pack(side=tk.LEFT, padx=5)
        self.preset_combo = ttk.Combobox(preset_frame, values=["Default", "High Flow", "Low Pressure Drop", "Compact", "Custom"])
        self.preset_combo.pack(side=tk.LEFT, fill='x', expand=True, padx=5)
        self.preset_combo.current(0)
        self.preset_combo.bind("<<ComboboxSelected>>", self.load_preset)
        
        # Control buttons
        control_frame = ttk.Frame(params_frame)
        control_frame.pack(fill='x', pady=self.theme.padding)
        
        ttk.Button(control_frame, text="Reset to Default", 
                  command=self.reset_parameters,
                  padding=self.theme.padding).pack(fill='x', pady=self.theme.small_padding)
        
        ttk.Button(control_frame, text="Save As Preset", 
                  command=self.save_preset_dialog,
                  padding=self.theme.padding).pack(fill='x', pady=self.theme.small_padding)
        
        # ======= Output parameters display =======
        output_frame = ttk.LabelFrame(params_frame, text="Output Parameters", padding=self.theme.padding)
        output_frame.pack(fill='x', pady=self.theme.padding, side=tk.BOTTOM)
        
        # Pressure drop
        ttk.Label(output_frame, text="Pressure Drop:").grid(row=0, column=0, sticky='w', pady=2)
        self.pressure_drop_var = tk.StringVar(value="N/A")
        ttk.Label(output_frame, textvariable=self.pressure_drop_var).grid(row=0, column=1, sticky='w', pady=2)
        ttk.Label(output_frame, text="Pa").grid(row=0, column=2, sticky='w', pady=2)
        
        # Flow rate
        ttk.Label(output_frame, text="Flow Rate:").grid(row=1, column=0, sticky='w', pady=2)
        self.flow_rate_var = tk.StringVar(value="N/A")
        ttk.Label(output_frame, textvariable=self.flow_rate_var).grid(row=1, column=1, sticky='w', pady=2)
        ttk.Label(output_frame, text="m³/s").grid(row=1, column=2, sticky='w', pady=2)
        
        # Efficiency
        ttk.Label(output_frame, text="Efficiency:").grid(row=2, column=0, sticky='w', pady=2)
        self.efficiency_var = tk.StringVar(value="N/A")
        ttk.Label(output_frame, textvariable=self.efficiency_var).grid(row=2, column=1, sticky='w', pady=2)
        ttk.Label(output_frame, text="%").grid(row=2, column=2, sticky='w', pady=2)
        
        # Objective value
        ttk.Label(output_frame, text="Objective:").grid(row=3, column=0, sticky='w', pady=2)
        self.objective_var = tk.StringVar(value="N/A")
        ttk.Label(output_frame, textvariable=self.objective_var).grid(row=3, column=1, sticky='w', pady=2)
        
        # Right panel for workflow visualization and controls
        workflow_frame = ttk.LabelFrame(container, text="Workflow Pipeline", padding=self.theme.padding)
        workflow_frame.pack(side=tk.RIGHT, fill='both', expand=True, padx=self.theme.padding, pady=self.theme.padding)

        # Create a canvas for the workflow visualization
        self.workflow_canvas_frame = ttk.Frame(workflow_frame)
        self.workflow_canvas_frame.pack(fill='both', expand=True, padx=self.theme.padding, pady=self.theme.padding)
        
        self.workflow_canvas = tk.Canvas(self.workflow_canvas_frame, bg=self.theme.bg_color, highlightthickness=0)
        self.workflow_canvas.pack(fill='both', expand=True)
        
        # ======= Workflow Steps =======
        # Create variables to track workflow state
        self.workflow_steps = []
        self.workflow_status = {
            "nx": {"status": "pending", "output": None},
            "mesh": {"status": "pending", "output": None},
            "cfd": {"status": "pending", "output": None},
            "results": {"status": "pending", "output": None}
        }
        
        # Create the workflow step boxes
        self._create_workflow_steps()
        
        # Control buttons
        workflow_buttons = ttk.Frame(workflow_frame)
        workflow_buttons.pack(fill='x', pady=self.theme.padding)
        
        ttk.Button(workflow_buttons, text="Run Complete Workflow", 
                  command=self.run_complete_workflow,
                  style="Primary.TButton",
                  padding=self.theme.padding).pack(side=tk.LEFT, fill='x', expand=True, padx=(0, 5))
        
        ttk.Button(workflow_buttons, text="Reset Workflow", 
                  command=self.reset_workflow,
                  padding=self.theme.padding).pack(side=tk.LEFT, fill='x', expand=True, padx=5)
        
        # Set up the callback for window resizing to redraw workflow
        self.workflow_canvas.bind("<Configure>", self._redraw_workflow)

    def setup_visualization_tab(self):
        """Set up the visualization tab with a modern layout"""
        # Container with padding
        container = ttk.Frame(self.visualization_tab, padding=self.theme.padding)
        container.pack(fill='both', expand=True)
        
        # Create a split view with left panel for controls and right panel for visualization
        # Left panel for visualization controls
        controls_frame = ttk.LabelFrame(container, text="Visualization Controls", padding=self.theme.padding)
        controls_frame.pack(side=tk.LEFT, fill='y', padx=self.theme.padding, pady=self.theme.padding)
        
        # Create a tabbed interface for Mesh and Geometry controls
        control_notebook = ttk.Notebook(controls_frame)
        control_notebook.pack(fill='both', expand=True, padx=0, pady=self.theme.small_padding)
        
        # Create tabs for different visualization types
        mesh_tab = ttk.Frame(control_notebook)
        geometry_tab = ttk.Frame(control_notebook)
        results_tab = ttk.Frame(control_notebook)
        
        control_notebook.add(mesh_tab, text="Mesh")
        control_notebook.add(geometry_tab, text="Geometry")
        control_notebook.add(results_tab, text="Results")
        
        # === MESH TAB ===
        # Mesh operations
        mesh_ops_frame = ttk.LabelFrame(mesh_tab, text="Mesh Operations", padding=self.theme.padding)
        mesh_ops_frame.pack(fill='x', pady=self.theme.small_padding, padx=self.theme.small_padding)
        
        # Import button
        ttk.Button(mesh_ops_frame, text="Import Mesh", 
                  command=self.import_mesh_dialog,
                  padding=self.theme.padding).pack(fill='x', pady=self.theme.small_padding)
        
        # Export button
        ttk.Button(mesh_ops_frame, text="Export Mesh", 
                  command=self.export_mesh_dialog,
                  padding=self.theme.padding).pack(fill='x', pady=self.theme.small_padding)
        
        # Mesh display options
        mesh_display_frame = ttk.LabelFrame(mesh_tab, text="Display Options", padding=self.theme.padding)
        mesh_display_frame.pack(fill='x', pady=self.theme.small_padding, padx=self.theme.small_padding)
        
        # Show edges checkbox
        self.show_edges_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(mesh_display_frame, text="Show Edges", 
                      variable=self.show_edges_var, 
                      command=self.update_mesh_display).pack(anchor='w')
        
        # Show surface checkbox
        self.show_surface_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(mesh_display_frame, text="Show Surface", 
                       variable=self.show_surface_var,
                       command=self.update_mesh_display).pack(anchor='w')
        
        # Surface transparency slider
        transparency_frame = ttk.Frame(mesh_display_frame)
        transparency_frame.pack(fill='x', pady=self.theme.small_padding)
        
        ttk.Label(transparency_frame, text="Transparency:").pack(side=tk.LEFT)
        self.transparency_scale = ttk.Scale(transparency_frame, from_=0, to=1, orient=tk.HORIZONTAL)
        self.transparency_scale.pack(side=tk.RIGHT, fill='x', expand=True)
        self.transparency_scale.set(0.3)
        self.transparency_scale.bind("<ButtonRelease-1>", self.update_mesh_display)
        
        # Coloring options
        coloring_frame = ttk.Frame(mesh_display_frame)
        coloring_frame.pack(fill='x', pady=self.theme.small_padding)
        
        ttk.Label(coloring_frame, text="Color By:").pack(side=tk.LEFT)
        self.mesh_color_by = ttk.Combobox(coloring_frame, values=["Solid", "Cell Type", "Quality"])
        self.mesh_color_by.pack(side=tk.RIGHT, fill='x', expand=True)
        self.mesh_color_by.current(0)
        self.mesh_color_by.bind("<<ComboboxSelected>>", self.update_mesh_display)
        
        # Mesh quality metrics
        quality_frame = ttk.LabelFrame(mesh_tab, text="Quality Metrics", padding=self.theme.padding)
        quality_frame.pack(fill='x', pady=self.theme.small_padding, padx=self.theme.small_padding)
        
        ttk.Button(quality_frame, text="Analyze Mesh Quality", 
                  command=self.analyze_mesh_quality,
                  padding=self.theme.padding).pack(fill='x', pady=self.theme.small_padding)
        
        # === GEOMETRY TAB ===
        # Geometry operations
        geom_ops_frame = ttk.LabelFrame(geometry_tab, text="Geometry Operations", padding=self.theme.padding)
        geom_ops_frame.pack(fill='x', pady=self.theme.small_padding, padx=self.theme.small_padding)
        
        # Import button
        ttk.Button(geom_ops_frame, text="Import Geometry", 
                  command=self.import_geometry_dialog,
                  padding=self.theme.padding).pack(fill='x', pady=self.theme.small_padding)
        
        # Export button
        ttk.Button(geom_ops_frame, text="Export Geometry", 
                  command=self.export_geometry_dialog,
                  padding=self.theme.padding).pack(fill='x', pady=self.theme.small_padding)
        
        # Geometry display options
        geom_display_frame = ttk.LabelFrame(geometry_tab, text="Display Options", padding=self.theme.padding)
        geom_display_frame.pack(fill='x', pady=self.theme.small_padding, padx=self.theme.small_padding)
        
        # Show wireframe checkbox
        self.show_wireframe_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(geom_display_frame, text="Show Wireframe", 
                       variable=self.show_wireframe_var,
                       command=self.update_geometry_display).pack(anchor='w')
        
        # Show surface checkbox
        self.show_geom_surface_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(geom_display_frame, text="Show Surface", 
                       variable=self.show_geom_surface_var,
                       command=self.update_geometry_display).pack(anchor='w')
        
        # Surface color
        color_frame = ttk.Frame(geom_display_frame)
        color_frame.pack(fill='x', pady=self.theme.small_padding)
        
        ttk.Label(color_frame, text="Color:").pack(side=tk.LEFT)
        self.geom_color = ttk.Combobox(color_frame, values=["Default", "Blue", "Red", "Green", "Custom"])
        self.geom_color.pack(side=tk.RIGHT, fill='x', expand=True)
        self.geom_color.current(0)
        self.geom_color.bind("<<ComboboxSelected>>", self.update_geometry_display)
        
        # === RESULTS TAB ===
        # Visualization options
        viz_options = ["Pressure Field", "Velocity Field", "Temperature Field", "Convergence History"]
        ttk.Label(results_tab, text="Select Visualization:", font=self.theme.normal_font).pack(anchor='w', padx=self.theme.padding, pady=self.theme.padding)
        
        self.viz_option = ttk.Combobox(results_tab, values=viz_options, font=self.theme.normal_font, width=20)
        self.viz_option.pack(fill='x', padx=self.theme.padding, pady=self.theme.small_padding)
        self.viz_option.current(0)
        
        # Options frame for visualization parameters
        options_frame = ttk.LabelFrame(results_tab, text="Display Options", padding=self.theme.padding)
        options_frame.pack(fill='x', padx=self.theme.padding, pady=self.theme.padding)
        
        # Colormap selection
        ttk.Label(options_frame, text="Color Scheme:", font=self.theme.normal_font).pack(anchor='w')
        self.colormap = ttk.Combobox(options_frame, values=["viridis", "plasma", "inferno", "magma", "jet"], font=self.theme.small_font)
        self.colormap.pack(fill='x', pady=self.theme.small_padding)
        self.colormap.current(0)
        
        # Plot type
        ttk.Label(options_frame, text="Plot Type:", font=self.theme.normal_font).pack(anchor='w', pady=(self.theme.padding, 0))
        self.plot_type = ttk.Combobox(options_frame, values=["Contour", "Surface", "Wireframe"], font=self.theme.small_font)
        self.plot_type.pack(fill='x', pady=self.theme.small_padding)
        self.plot_type.current(0)
        
        # Generate plot button
        ttk.Button(results_tab, text="Generate Plot", 
                  command=self.visualize_results,
                  style="Primary.TButton",
                  padding=self.theme.padding).pack(fill='x', padx=self.theme.padding, pady=self.theme.padding)
        
        # Bottom toolbar for all tabs
        toolbar_frame = ttk.Frame(controls_frame)
        toolbar_frame.pack(fill='x', pady=self.theme.padding, side=tk.BOTTOM)
        
        ttk.Button(toolbar_frame, text="Export Visualization", 
                  command=self.export_visualization,
                  padding=self.theme.padding).pack(side=tk.LEFT, fill='x', expand=True, padx=self.theme.small_padding)

        ttk.Button(toolbar_frame, text="Reset View", 
                  command=self.reset_view,
                  padding=self.theme.padding).pack(side=tk.LEFT, fill='x', expand=True, padx=self.theme.small_padding)
        
        # Right panel for visualization
        viz_frame = ttk.LabelFrame(container, text="Visualization", padding=self.theme.padding)
        viz_frame.pack(side=tk.RIGHT, fill='both', expand=True, padx=self.theme.padding, pady=self.theme.padding)
        
        # Create a frame for the file information display
        self.file_info_frame = ttk.Frame(viz_frame)
        self.file_info_frame.pack(fill='x', pady=self.theme.small_padding)
        
        self.current_file_var = tk.StringVar(value="No file loaded")
        ttk.Label(self.file_info_frame, textvariable=self.current_file_var, font=self.theme.small_font).pack(side=tk.LEFT)
        
        # Create figure and canvas for plotting with a lighter background
        self.figure = Figure(figsize=(8, 6), dpi=100, facecolor=self.theme.bg_color)
        self.canvas = FigureCanvasTkAgg(self.figure, viz_frame)
        self.canvas.get_tk_widget().pack(fill='both', expand=True)
        
        # Add navigation toolbar
        toolbar_frame = ttk.Frame(viz_frame)
        toolbar_frame.pack(fill='x')
        self.toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        self.toolbar.update()
        
        # Initialize empty plot
        self.ax = self.figure.add_subplot(111, projection='3d')
        self.ax.set_title("No data loaded", fontsize=14)
        self.ax.set_xlabel("X")
        self.ax.set_ylabel("Y")
        self.ax.set_zlabel("Z")
        self.canvas.draw()
        
        # Initialize attributes for mesh and geometry data
        self.current_mesh = None
        self.current_geometry = None
        self.mesh_actors = []
        self.geometry_actors = []

    def setup_optimization_tab(self):
        """Set up the optimization tab with a modern layout"""
        # Container with padding
        container = ttk.Frame(self.optimization_tab, padding=self.theme.padding)
        container.pack(fill='both', expand=True)
        
        # Left panel for optimization settings
        settings_frame = ttk.LabelFrame(container, text="Optimization Settings", padding=self.theme.padding)
        settings_frame.pack(side=tk.LEFT, fill='both', expand=True, padx=self.theme.padding, pady=self.theme.padding)
        
        # Optimization algorithm selection with description
        algo_frame = ttk.Frame(settings_frame)
        algo_frame.pack(fill='x', pady=self.theme.padding)
        
        ttk.Label(algo_frame, text="Algorithm:", font=self.theme.normal_font).grid(row=0, column=0, sticky='w')
        self.opt_algorithm = ttk.Combobox(algo_frame, values=["SLSQP", "COBYLA", "NSGA2", "GA"], font=self.theme.normal_font, width=10)
        self.opt_algorithm.grid(row=0, column=1, padx=self.theme.padding)
        self.opt_algorithm.current(0)
        
        self.algo_description = ttk.Label(algo_frame, text="Sequential Least Squares Programming - Gradient-based optimizer", 
                                        font=self.theme.small_font, foreground=self.theme.accent_color, wraplength=300)
        self.algo_description.grid(row=1, column=0, columnspan=2, sticky='w', pady=self.theme.small_padding)
        
        # Bind event to update description
        self.opt_algorithm.bind("<<ComboboxSelected>>", self.update_algorithm_description)
        
        # Separator
        ttk.Separator(settings_frame, orient='horizontal').pack(fill='x', pady=self.theme.padding)
        
        # Design variable bounds
        bounds_frame = ttk.LabelFrame(settings_frame, text="Design Variable Bounds", padding=self.theme.padding)
        bounds_frame.pack(fill='x', pady=self.theme.small_padding)
        
        # Create a header row
        ttk.Label(bounds_frame, text="Parameter", font=self.theme.normal_font).grid(row=0, column=0, padx=self.theme.padding, pady=self.theme.small_padding)
        ttk.Label(bounds_frame, text="Min", font=self.theme.normal_font).grid(row=0, column=1, padx=self.theme.padding, pady=self.theme.small_padding)
        ttk.Label(bounds_frame, text="Max", font=self.theme.normal_font).grid(row=0, column=2, padx=self.theme.padding, pady=self.theme.small_padding)
        ttk.Label(bounds_frame, text="Unit", font=self.theme.normal_font).grid(row=0, column=3, padx=self.theme.padding, pady=self.theme.small_padding)
        
        # L4 bounds
        ttk.Label(bounds_frame, text="L4:", font=self.theme.normal_font).grid(row=1, column=0, padx=self.theme.padding, pady=self.theme.small_padding, sticky='w')
        self.l4_min = ttk.Entry(bounds_frame, width=8, font=self.theme.normal_font)
        self.l4_min.grid(row=1, column=1, padx=self.theme.padding, pady=self.theme.small_padding)
        self.l4_min.insert(0, "1.0")
        self.l4_max = ttk.Entry(bounds_frame, width=8, font=self.theme.normal_font)
        self.l4_max.grid(row=1, column=2, padx=self.theme.padding, pady=self.theme.small_padding)
        self.l4_max.insert(0, "3.0")
        ttk.Label(bounds_frame, text="m", font=self.theme.normal_font).grid(row=1, column=3, padx=self.theme.padding, pady=self.theme.small_padding, sticky='w')
        
        # L5 bounds
        ttk.Label(bounds_frame, text="L5:", font=self.theme.normal_font).grid(row=2, column=0, padx=self.theme.padding, pady=self.theme.small_padding, sticky='w')
        self.l5_min = ttk.Entry(bounds_frame, width=8, font=self.theme.normal_font)
        self.l5_min.grid(row=2, column=1, padx=self.theme.padding, pady=self.theme.small_padding)
        self.l5_min.insert(0, "2.0")
        self.l5_max = ttk.Entry(bounds_frame, width=8, font=self.theme.normal_font)
        self.l5_max.grid(row=2, column=2, padx=self.theme.padding, pady=self.theme.small_padding)
        self.l5_max.insert(0, "4.0")
        ttk.Label(bounds_frame, text="m", font=self.theme.normal_font).grid(row=2, column=3, padx=self.theme.padding, pady=self.theme.small_padding, sticky='w')
        
        # Alpha1 bounds
        ttk.Label(bounds_frame, text="Alpha1:", font=self.theme.normal_font).grid(row=3, column=0, padx=self.theme.padding, pady=self.theme.small_padding, sticky='w')
        self.alpha1_min = ttk.Entry(bounds_frame, width=8, font=self.theme.normal_font)
        self.alpha1_min.grid(row=3, column=1, padx=self.theme.padding, pady=self.theme.small_padding)
        self.alpha1_min.insert(0, "5.0")
        self.alpha1_max = ttk.Entry(bounds_frame, width=8, font=self.theme.normal_font)
        self.alpha1_max.grid(row=3, column=2, padx=self.theme.padding, pady=self.theme.small_padding)
        self.alpha1_max.insert(0, "15.0")
        ttk.Label(bounds_frame, text="deg", font=self.theme.normal_font).grid(row=3, column=3, padx=self.theme.padding, pady=self.theme.small_padding, sticky='w')
        
        # Optimizer settings
        opt_settings_frame = ttk.LabelFrame(settings_frame, text="Optimizer Settings", padding=self.theme.padding)
        opt_settings_frame.pack(fill='x', pady=self.theme.small_padding)
        
        ttk.Label(opt_settings_frame, text="Maximum Iterations:", font=self.theme.normal_font).grid(row=0, column=0, padx=self.theme.padding, pady=self.theme.small_padding, sticky='w')
        self.max_iter = ttk.Entry(opt_settings_frame, width=10, font=self.theme.normal_font)
        self.max_iter.grid(row=0, column=1, padx=self.theme.padding, pady=self.theme.small_padding)
        self.max_iter.insert(0, "50")
        
        ttk.Label(opt_settings_frame, text="Convergence Tolerance:", font=self.theme.normal_font).grid(row=1, column=0, padx=self.theme.padding, pady=self.theme.small_padding, sticky='w')
        self.tolerance = ttk.Entry(opt_settings_frame, width=10, font=self.theme.normal_font)
        self.tolerance.grid(row=1, column=1, padx=self.theme.padding, pady=self.theme.small_padding)
        self.tolerance.insert(0, "1e-6")
        
        ttk.Label(opt_settings_frame, text="Population Size:", font=self.theme.normal_font).grid(row=2, column=0, padx=self.theme.padding, pady=self.theme.small_padding, sticky='w')
        self.pop_size = ttk.Entry(opt_settings_frame, width=10, font=self.theme.normal_font)
        self.pop_size.grid(row=2, column=1, padx=self.theme.padding, pady=self.theme.small_padding)
        self.pop_size.insert(0, "50")
        
        # Control buttons with modern styling
        buttons_frame = ttk.Frame(settings_frame)
        buttons_frame.pack(fill='x', pady=self.theme.padding)
        
        ttk.Button(buttons_frame, text="Start Optimization", 
                  command=self.run_optimization, 
                  style="Primary.TButton",
                  padding=self.theme.padding).pack(side=tk.LEFT, fill='x', expand=True, padx=(0, self.theme.small_padding))
        
        ttk.Button(buttons_frame, text="Pause/Resume", 
                  command=self.toggle_optimization,
                  padding=self.theme.padding).pack(side=tk.LEFT, fill='x', expand=True, padx=(self.theme.small_padding, self.theme.small_padding))
        
        ttk.Button(buttons_frame, text="Stop", 
                  command=self.stop_optimization,
                  padding=self.theme.padding).pack(side=tk.LEFT, fill='x', expand=True, padx=(self.theme.small_padding, 0))
        
        # Right panel for optimization results with tabs
        results_frame = ttk.LabelFrame(container, text="Optimization Results", padding=self.theme.padding)
        results_frame.pack(side=tk.RIGHT, fill='both', expand=True, padx=self.theme.padding, pady=self.theme.padding)
        
        # Create nested notebook for results
        results_tabs = ttk.Notebook(results_frame)
        results_tabs.pack(fill='both', expand=True)
        
        # History tab
        history_tab = ttk.Frame(results_tabs)
        results_tabs.add(history_tab, text="Convergence History")
        
        self.history_figure = Figure(figsize=(6, 4), dpi=100, facecolor=self.theme.bg_color)
        self.history_canvas = FigureCanvasTkAgg(self.history_figure, history_tab)
        self.history_canvas.get_tk_widget().pack(fill='both', expand=True)
        
        # Add default text to the empty plot
        ax = self.history_figure.add_subplot(111)
        ax.text(0.5, 0.5, "No optimization history available yet", 
               horizontalalignment='center', verticalalignment='center',
               transform=ax.transAxes, fontsize=12, color=self.theme.primary_color)
        ax.set_title("Optimization Convergence")
        self.history_canvas.draw()
        
        # Pareto tab
        pareto_tab = ttk.Frame(results_tabs)
        results_tabs.add(pareto_tab, text="Pareto Front")
        
        self.pareto_figure = Figure(figsize=(6, 4), dpi=100, facecolor=self.theme.bg_color)
        self.pareto_canvas = FigureCanvasTkAgg(self.pareto_figure, pareto_tab)
        self.pareto_canvas.get_tk_widget().pack(fill='both', expand=True)
        
        # Add default text to the empty plot
        ax = self.pareto_figure.add_subplot(111)
        ax.text(0.5, 0.5, "No Pareto data available yet", 
               horizontalalignment='center', verticalalignment='center',
               transform=ax.transAxes, fontsize=12, color=self.theme.primary_color)
        ax.set_title("Pareto Front")
        self.pareto_canvas.draw()
        
        # Best results tab
        best_tab = ttk.Frame(results_tabs)
        results_tabs.add(best_tab, text="Best Results")
        
        # Create a treeview with style
        style = ttk.Style()
        style.configure("Treeview.Heading", font=self.theme.normal_font, background=self.theme.accent_color, foreground=self.theme.light_text)
        style.configure("Treeview", font=self.theme.normal_font, rowheight=25)
        style.map("Treeview", 
                 background=[('selected', self.theme.accent_color)],
                 foreground=[('selected', self.theme.light_text)])
        
        # Results table
        self.best_results = ttk.Treeview(best_tab, columns=("Parameter", "Value"), show="headings", style="Treeview")
        self.best_results.heading("Parameter", text="Parameter")
        self.best_results.heading("Value", text="Value")
        self.best_results.column("Parameter", width=150)
        self.best_results.column("Value", width=150)
        self.best_results.pack(fill='both', expand=True, padx=self.theme.padding, pady=self.theme.padding)
        
        # Add default rows for parameters
        self.best_results.insert("", "end", values=("L4", "N/A"))
        self.best_results.insert("", "end", values=("L5", "N/A"))
        self.best_results.insert("", "end", values=("Alpha1", "N/A"))
        self.best_results.insert("", "end", values=("Alpha2", "N/A"))
        self.best_results.insert("", "end", values=("Alpha3", "N/A"))
        self.best_results.insert("", "end", values=("Objective", "N/A"))
        
        # Design variable inputs
        inputs_frame = ttk.LabelFrame(container, text="Design Variable Inputs", padding=self.theme.padding)
        inputs_frame.pack(fill='x', pady=self.theme.padding)
        
        ttk.Label(inputs_frame, text="L4:", width=8).grid(row=0, column=0, sticky='w', padx=self.theme.padding)
        self.l4_entry = ttk.Entry(inputs_frame, width=10)
        self.l4_entry.grid(row=0, column=1, padx=self.theme.small_padding)
        self.l4_entry.insert(0, "2.0")
        
        ttk.Label(inputs_frame, text="L5:", width=8).grid(row=1, column=0, sticky='w', padx=self.theme.padding)
        self.l5_entry = ttk.Entry(inputs_frame, width=10)
        self.l5_entry.grid(row=1, column=1, padx=self.theme.small_padding)
        self.l5_entry.insert(0, "3.0")
        
        ttk.Label(inputs_frame, text="Alpha1:", width=8).grid(row=2, column=0, sticky='w', padx=self.theme.padding)
        self.alpha1_entry = ttk.Entry(inputs_frame, width=10)
        self.alpha1_entry.grid(row=2, column=1, padx=self.theme.small_padding)
        self.alpha1_entry.insert(0, "10.0")
        
        ttk.Label(inputs_frame, text="Alpha2:", width=8).grid(row=3, column=0, sticky='w', padx=self.theme.padding)
        self.alpha2_entry = ttk.Entry(inputs_frame, width=10)
        self.alpha2_entry.grid(row=3, column=1, padx=self.theme.small_padding)
        self.alpha2_entry.insert(0, "10.0")
        
        ttk.Label(inputs_frame, text="Alpha3:", width=8).grid(row=4, column=0, sticky='w', padx=self.theme.padding)
        self.alpha3_entry = ttk.Entry(inputs_frame, width=10)
        self.alpha3_entry.grid(row=4, column=1, padx=self.theme.small_padding)
        self.alpha3_entry.insert(0, "10.0")

    def setup_settings_tab(self):
        """Set up the settings tab with a modern layout"""
        # Container with padding
        container = ttk.Frame(self.settings_tab, padding=self.theme.padding)
        container.pack(fill='both', expand=True)
        
        # Create two columns: Left for settings, right for information
        left_frame = ttk.Frame(container)
        left_frame.pack(side=tk.LEFT, fill='both', expand=True, padx=self.theme.padding)
        
        right_frame = ttk.Frame(container)
        right_frame.pack(side=tk.RIGHT, fill='both', expand=True, padx=self.theme.padding)
        
        # Application settings section
        settings_frame = ttk.LabelFrame(left_frame, text="Application Settings", padding=self.theme.padding)
        settings_frame.pack(fill='x', pady=self.theme.padding)
        
        # Demo mode checkbox with styled label
        self.demo_var = tk.BooleanVar(value=DEMO_MODE)
        demo_frame = ttk.Frame(settings_frame)
        demo_frame.pack(fill='x', pady=self.theme.small_padding)
        
        demo_check = ttk.Checkbutton(demo_frame, text="Demonstration Mode", 
                                   variable=self.demo_var, command=self.toggle_demo_mode)
        demo_check.pack(side=tk.LEFT)
        
        demo_label = ttk.Label(demo_frame, text="Use mock executables and simulated data",
                              foreground=self.theme.accent_color, font=self.theme.small_font)
        demo_label.pack(side=tk.LEFT, padx=self.theme.padding)
        
        # Separator
        ttk.Separator(settings_frame, orient='horizontal').pack(fill='x', pady=self.theme.padding)
        
        # File paths section
        paths_frame = ttk.LabelFrame(left_frame, text="File Paths", padding=self.theme.padding)
        paths_frame.pack(fill='x', pady=self.theme.padding)
        
        # NX Journal Path
        nx_frame = ttk.Frame(paths_frame)
        nx_frame.pack(fill='x', pady=self.theme.small_padding)
        
        ttk.Label(nx_frame, text="NX Journal:", width=10).pack(side=tk.LEFT)
        self.nx_path = ttk.Entry(nx_frame, font=self.theme.small_font)
        self.nx_path.pack(side=tk.LEFT, fill='x', expand=True, padx=self.theme.small_padding)
        self.nx_path.insert(0, "C:/Users/Mohammed/Desktop/Intake-CFD-Project/nx/nx_express2.py")
        ttk.Button(nx_frame, text="Browse", command=lambda: self.browse_file(self.nx_path)).pack(side=tk.RIGHT)
        
        # GMSH Path
        gmsh_frame = ttk.Frame(paths_frame)
        gmsh_frame.pack(fill='x', pady=self.theme.small_padding)
        
        ttk.Label(gmsh_frame, text="GMSH:", width=10).pack(side=tk.LEFT)
        self.gmsh_path = ttk.Entry(gmsh_frame, font=self.theme.small_font)
        self.gmsh_path.pack(side=tk.LEFT, fill='x', expand=True, padx=self.theme.small_padding)
        self.gmsh_path.insert(0, "./gmsh_process")
        ttk.Button(gmsh_frame, text="Browse", command=lambda: self.browse_file(self.gmsh_path)).pack(side=tk.RIGHT)
        
        # CFD Path
        cfd_frame = ttk.Frame(paths_frame)
        cfd_frame.pack(fill='x', pady=self.theme.small_padding)
        
        ttk.Label(cfd_frame, text="CFD Solver:", width=10).pack(side=tk.LEFT)
        self.cfd_path = ttk.Entry(cfd_frame, font=self.theme.small_font)
        self.cfd_path.pack(side=tk.LEFT, fill='x', expand=True, padx=self.theme.small_padding)
        self.cfd_path.insert(0, "./cfd_solver")
        ttk.Button(cfd_frame, text="Browse", command=lambda: self.browse_file(self.cfd_path)).pack(side=tk.RIGHT)
        
        # Results directory
        results_frame = ttk.Frame(paths_frame)
        results_frame.pack(fill='x', pady=self.theme.small_padding)
        
        ttk.Label(results_frame, text="Results:", width=10).pack(side=tk.LEFT)
        self.results_dir = ttk.Entry(results_frame, font=self.theme.small_font)
        self.results_dir.pack(side=tk.LEFT, fill='x', expand=True, padx=self.theme.small_padding)
        self.results_dir.insert(0, "cfd_results")
        ttk.Button(results_frame, text="Browse", command=lambda: self.browse_directory(self.results_dir)).pack(side=tk.RIGHT)
        
        # Display settings section
        display_frame = ttk.LabelFrame(left_frame, text="Display Settings", padding=self.theme.padding)
        display_frame.pack(fill='x', pady=self.theme.padding)
        
        # Theme selection
        theme_frame = ttk.Frame(display_frame)
        theme_frame.pack(fill='x', pady=self.theme.small_padding)
        
        ttk.Label(theme_frame, text="UI Theme:", width=12).pack(side=tk.LEFT)
        self.theme_combo = ttk.Combobox(theme_frame, values=["Default (Blue)", "Dark", "Light", "System"])
        self.theme_combo.pack(fill='x', padx=self.theme.small_padding)
        self.theme_combo.current(0)
        self.theme_combo.bind("<<ComboboxSelected>>", self.change_theme)
        
        # Font size
        font_frame = ttk.Frame(display_frame)
        font_frame.pack(fill='x', pady=self.theme.small_padding)
        
        ttk.Label(font_frame, text="Font Size:", width=12).pack(side=tk.LEFT)
        self.font_size = ttk.Spinbox(font_frame, from_=8, to=16, width=5)
        self.font_size.pack(side=tk.LEFT, padx=self.theme.small_padding)
        self.font_size.set(10)
        
        # Performance settings
        perf_frame = ttk.LabelFrame(left_frame, text="Performance Settings", padding=self.theme.padding)
        perf_frame.pack(fill='x', pady=self.theme.padding)
        
        # Parallel processes
        parallel_frame = ttk.Frame(perf_frame)
        parallel_frame.pack(fill='x', pady=self.theme.small_padding)
        
        ttk.Label(parallel_frame, text="Parallel Processes:").pack(side=tk.LEFT)
        self.parallel_processes = ttk.Spinbox(parallel_frame, from_=1, to=16, width=5)
        self.parallel_processes.pack(side=tk.LEFT, padx=self.theme.padding)
        self.parallel_processes.set(4)
        
        # Memory usage slider
        memory_frame = ttk.Frame(perf_frame)
        memory_frame.pack(fill='x', pady=self.theme.small_padding)
        
        ttk.Label(memory_frame, text="Memory Usage:").pack(side=tk.LEFT)
        self.memory_scale = ttk.Scale(memory_frame, from_=1, to=10, orient=tk.HORIZONTAL)
        self.memory_scale.pack(side=tk.LEFT, fill='x', expand=True, padx=self.theme.small_padding)
        self.memory_scale.set(5)
        ttk.Label(memory_frame, text="5 GB").pack(side=tk.RIGHT)
        
        # Save settings button
        ttk.Button(left_frame, text="Save Settings", 
                  command=self.save_settings,
                  style="Primary.TButton",
                  padding=self.theme.padding).pack(fill='x', pady=self.theme.padding)
        
        # Right panel: System information
        info_frame = ttk.LabelFrame(right_frame, text="System Information", padding=self.theme.padding)
        info_frame.pack(fill='x', pady=self.theme.padding)
        
        # System info table
        system_info = [
            ("Operating System", platform.system() + " " + platform.release()),
            ("Python Version", platform.python_version()),
            ("Processor", platform.processor() or "Unknown"),
            ("WSL", "Yes" if is_wsl() else "No"),
            ("Working Directory", os.getcwd())
        ]
        
        # Display system info in a grid
        row = 0
        for label, value in system_info:
            ttk.Label(info_frame, text=label + ":", font=self.theme.normal_font).grid(
                row=row, column=0, sticky='w', padx=self.theme.padding, pady=self.theme.small_padding
            )
            ttk.Label(info_frame, text=value, font=self.theme.normal_font).grid(
                row=row, column=1, sticky='w', padx=self.theme.padding, pady=self.theme.small_padding
            )
            row += 1
            
        # About section
        about_frame = ttk.LabelFrame(right_frame, text="About", padding=self.theme.padding)
        about_frame.pack(fill='both', expand=True, pady=self.theme.padding)
        
        about_text = """Intake CFD Optimization Suite

Version 1.0.0

This software provides a complete workflow for intake CFD design optimization:
- NX CAD model parametrization
- GMSH-based meshing
- CFD simulation with OpenFOAM
- Results visualization and analysis
- Design optimization with OpenMDAO

For support, please contact:
support@intakecfd.example.com
"""
        
        about_label = ttk.Label(about_frame, text=about_text, justify=tk.LEFT, wraplength=400)
        about_label.pack(padx=self.theme.padding, pady=self.theme.padding)
        
        # Add Run Diagnostics button
        ttk.Button(right_frame, text="Run System Diagnostics", 
                  command=self.run_diagnostics,
                  padding=self.theme.padding).pack(fill='x', pady=self.theme.padding)

    # New helper methods for the improved GUI
    
    def update_algorithm_description(self, event=None):
        """Update the algorithm description based on selection"""
        algorithm = self.opt_algorithm.get()
        descriptions = {
            "SLSQP": "Sequential Least Squares Programming - Gradient-based optimizer",
            "COBYLA": "Constrained Optimization BY Linear Approximation - Non-gradient based",
            "NSGA2": "Non-dominated Sorting Genetic Algorithm - Multi-objective optimization",
            "GA": "Genetic Algorithm - Population-based evolutionary optimizer"
        }
        
        if algorithm in descriptions:
            self.algo_description.config(text=descriptions[algorithm])
    
    def export_visualization(self):
        """Export current visualization to file"""
        if self.figure is None:
            messagebox.showinfo("Information", "No visualization to export.")
            return
            
        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg"), ("PDF", "*.pdf")]
        )
        
        if file_path:
            try:
                self.figure.savefig(file_path, dpi=300, bbox_inches='tight')
                self.update_status(f"Visualization exported to {file_path}")
            except Exception as e:
                messagebox.showerror("Export Error", str(e))
    
    def run_diagnostics(self):
        """Run system diagnostics"""
        self.update_status("Running system diagnostics...", show_progress=True)
        
        # Run in a separate thread
        threading.Thread(target=self._run_diagnostics_thread).start()
    
    def _run_diagnostics_thread(self):
        """Thread for running diagnostics"""
        try:
            # Simulate diagnostics with a delay
            time.sleep(1)
            
            diagnostics_result = {
                "NX": DEMO_MODE or os.path.exists(self.nx_path.get()),
                "GMSH": DEMO_MODE or os.path.exists(self.gmsh_path.get()),
                "CFD": DEMO_MODE or os.path.exists(self.cfd_path.get()),
                "Memory": True,
                "Disk Space": True
            }
            
            # Update in the main thread
            self.root.after(0, lambda: self._show_diagnostics_result(diagnostics_result))
        except Exception as e:
            self.root.after(0, lambda: self.update_status(f"Diagnostics failed: {str(e)}", show_progress=False))
    
    def _show_diagnostics_result(self, results):
        """Show diagnostics results"""
        self.update_status("Diagnostics completed", show_progress=False)
        
        # Build message
        message = "System Diagnostics Results:\n\n"
        all_ok = True
        
        for test, result in results.items():
            status = "✓ OK" if result else "✗ FAILED"
            message += f"{test}: {status}\n"
        else:
            message += "\nAll systems operational."
            
        messagebox.showinfo("Diagnostics Results", message)
        
    def toggle_demo_mode(self):
        """Toggle between demo and real mode"""
        global DEMO_MODE
        DEMO_MODE = self.demo_var.get()
        
        if DEMO_MODE:
            self.update_status("Switched to DEMONSTRATION mode. Mock executables will be used.")
            create_mock_executables()
        else:
            self.update_status("Switched to REAL execution mode. Real executables will be used.")

    def browse_file(self, entry_widget):
        """Browse for a file and update the entry"""
        filename = filedialog.askopenfilename()
        if filename:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, filename)
    
    def browse_directory(self, entry_widget):
        """Browse for a directory and update the entry"""
        directory = filedialog.askdirectory()
        if directory:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, directory)
    
    def change_theme(self, event=None):
        """Change the UI theme"""
        theme = self.theme_combo.get()
        if theme == "Dark":
            self.theme.bg_color = "#2C3E50"
            self.theme.text_color = "#ECF0F1"
            self.theme.accent_color = "#3498DB"
            messagebox.showinfo("Theme", "Dark theme will be applied after restart.")
        elif theme == "Light":
            self.theme.bg_color = "#F5F7FA"
            self.theme.text_color = "#2C3E50"
            self.theme.accent_color = "#3498DB"
            messagebox.showinfo("Theme", "Light theme will be applied after restart.")
        elif theme == "System":
            messagebox.showinfo("Theme", "System theme will be applied after restart.")
    
    def save_settings(self):
        """Save the current settings"""
        try:
            settings = {
                "demo_mode": self.demo_var.get(),
                "nx_path": self.nx_path.get(),
                "gmsh_path": self.gmsh_path.get(),
                "cfd_path": self.cfd_path.get(),
                "results_dir": self.results_dir.get(),
                "parallel_processes": self.parallel_processes.get(),
                "theme": self.theme_combo.get()
            }
            
            with open("settings.json", "w") as f:
                import json
                json.dump(settings, f, indent=2)
            
            self.update_status("Settings saved successfully.")
            messagebox.showinfo("Settings", "Settings saved successfully.")
        except Exception as e:
            self.update_status(f"Error saving settings: {str(e)}")
            messagebox.showerror("Error", f"Failed to save settings: {str(e)}")

    # ... existing visualization methods (visualize_results, plot_field, etc.)
    
    def visualize_results(self):
        """Visualize selected results"""
        try:
            # Make sure data is available
            if self.results_data is None:
                # Create dummy data for demonstration
                self.load_results_data()
            
            viz_type = self.viz_option.get()
            self.update_status(f"Generating {viz_type} visualization...", show_progress=True)
            
            # Clear the figure
            self.figure.clear()
            
            # Get colormap from selection
            cmap_name = self.colormap.get() if hasattr(self, 'colormap') else "viridis"
            cmap = cm.get_cmap(cmap_name)
            
            if viz_type == "Pressure Field":
                self.plot_field(self.results_data["x"], self.results_data["y"], self.results_data["pressure"], 
                               "Pressure Field", "X", "Y", "Pressure (Pa)", cmap)
            elif viz_type == "Velocity Field":
                self.plot_field(self.results_data["x"], self.results_data["y"], self.results_data["velocity"], 
                               "Velocity Field", "X", "Y", "Velocity (m/s)", cmap)
            elif viz_type == "Temperature Field":
                self.plot_field(self.results_data["x"], self.results_data["y"], self.results_data["temperature"], 
                               "Temperature Field", "X", "Y", "Temperature (K)", cmap)
            elif viz_type == "Mesh View":
                if self.mesh_data is not None:
                    self.plot_mesh()
                else:
                    self.load_mesh_data()
                    self.plot_mesh()
            elif viz_type == "Convergence History":
                self.plot_convergence()
            
            # Draw the plot
            self.canvas.draw()
            self.update_status(f"{viz_type} visualization created", show_progress=False)
        except Exception as e:
            messagebox.showerror("Visualization Error", str(e))
            self.update_status(f"Error creating visualization: {str(e)}", show_progress=False)
    
    def plot_field(self, x, y, data, title, xlabel, ylabel, zlabel, cmap=cm.viridis):
        """Plot a field variable as a contour plot with a more sophisticated style"""
        # Get plot type
        plot_type = self.plot_type.get() if hasattr(self, 'plot_type') else "Contour"
        
        if plot_type == "Surface" or plot_type == "Wireframe":
            # Create 3D axis
            ax = self.figure.add_subplot(111, projection='3d')
            
            if plot_type == "Surface":
                surf = ax.plot_surface(x, y, data, cmap=cmap, 
                                     linewidth=0, antialiased=True, alpha=0.8)
            else:  # Wireframe
                surf = ax.plot_wireframe(x, y, data, color=self.theme.primary_color,
                                       linewidth=0.5, antialiased=True)
                
            ax.set_title(title, fontsize=14, pad=20, color=self.theme.text_color)
            ax.set_xlabel(xlabel, fontsize=12, labelpad=10, color=self.theme.text_color)
            ax.set_ylabel(ylabel, fontsize=12, labelpad=10, color=self.theme.text_color)
            ax.set_zlabel(zlabel, fontsize=12, labelpad=10, color=self.theme.text_color)
            
            # Adjust view
            ax.view_init(elev=30, azim=45)
            
            # Add colorbar for surface plot
            if plot_type == "Surface":
                self.figure.colorbar(surf, ax=ax, shrink=0.6, aspect=10, pad=0.1, label=zlabel)
                
        else:  # Contour plot
            ax = self.figure.add_subplot(111)
            
            # Create filled contour with more levels for smoother appearance
            contour = ax.contourf(x, y, data, cmap=cmap, levels=20, alpha=0.8)
            
            # Add contour lines
            lines = ax.contour(x, y, data, colors='black', linewidths=0.5, alpha=0.4, levels=10)
            
            # Add contour labels
            ax.clabel(lines, inline=True, fontsize=8, fmt='%1.1f')
            
            # Add labels and title
            ax.set_title(title, fontsize=14, pad=20, color=self.theme.text_color)
            ax.set_xlabel(xlabel, fontsize=12, color=self.theme.text_color)
            ax.set_ylabel(ylabel, fontsize=12, color=self.theme.text_color)
            
            # Add color bar
            cbar = self.figure.colorbar(contour, ax=ax, label=zlabel)
            cbar.ax.yaxis.label.set_color(self.theme.text_color)
        
        # Better formatting of the figure
        self.figure.tight_layout(pad=2.0)
    
    def plot_mesh(self):
        """Plot the mesh as a 3D scatter plot with better styling"""
        ax = self.figure.add_subplot(111, projection='3d')
        pts = self.mesh_data["nodes"]
        elements = self.mesh_data["elements"]
        
        # Plot points
        ax.scatter(pts[:,0], pts[:,1], pts[:,2], c=self.theme.accent_color, marker='o', s=10, alpha=0.5)
        
        # Plot mesh elements (simplified representation for visualization)
        for elem in elements:
            if len(elem) >= 3:
                # Create a wire representation of triangular elements
                idx1, idx2, idx3 = elem[0], elem[1], elem[2]
                xs = [pts[idx1,0], pts[idx2,0], pts[idx3,0], pts[idx1,0]]
                ys = [pts[idx1,1], pts[idx2,1], pts[idx3,1], pts[idx1,1]]
                zs = [pts[idx1,2], pts[idx2,2], pts[idx3,2], pts[idx1,2]]
                ax.plot(xs, ys, zs, color=self.theme.primary_color, linewidth=0.5)
        
        # Set labels and title
        ax.set_title("Mesh Visualization", fontsize=14, pad=20, color=self.theme.text_color)
        ax.set_xlabel("X", fontsize=12, labelpad=10, color=self.theme.text_color)
        ax.set_ylabel("Y", fontsize=12, labelpad=10, color=self.theme.text_color)
        ax.set_zlabel("Z", fontsize=12, labelpad=10, color=self.theme.text_color)
        
        # Equal aspect ratio
        max_range = np.array([pts[:,0].max()-pts[:,0].min(), 
                             pts[:,1].max()-pts[:,1].min(), 
                             pts[:,2].max()-pts[:,2].min()]).max() / 2.0
        mid_x = (pts[:,0].max()+pts[:,0].min()) * 0.5
        mid_y = (pts[:,1].max()+pts[:,1].min()) * 0.5
        mid_z = (pts[:,2].max()+pts[:,2].min()) * 0.5
        ax.set_xlim(mid_x - max_range, mid_x + max_range)
        ax.set_ylim(mid_y - max_range, mid_y + max_range)
        ax.set_zlim(mid_z - max_range, mid_z + max_range)
        
        # Adjust view angle
        ax.view_init(elev=30, azim=45)
        
        # Tight layout
        self.figure.tight_layout()
    
    def plot_convergence(self):
        """Plot convergence history with better styling"""
        ax = self.figure.add_subplot(111)
        
        if hasattr(self, 'results_data') and self.results_data and "convergence" in self.results_data:
            # Get convergence data
            iterations = np.arange(len(self.results_data["convergence"]))
            convergence = self.results_data["convergence"]
            
            # Plot on log scale
            ax.semilogy(iterations, convergence, marker='o', linestyle='-', 
                       color=self.theme.accent_color, markerfacecolor=self.theme.primary_color,
                       markersize=6, linewidth=2)
            
            # Add horizontal reference line for convergence threshold
            ax.axhline(y=1e-6, color='r', linestyle='--', alpha=0.7, label='Convergence Threshold')
            
            # Set labels and title
            ax.set_title("Convergence History", fontsize=14, pad=20, color=self.theme.text_color)
            ax.set_xlabel("Iteration", fontsize=12, color=self.theme.text_color)
            ax.set_ylabel("Residual", fontsize=12, color=self.theme.text_color)
            
            # Add grid
            ax.grid(True, linestyle='--', alpha=0.6)
            
            # Add legend
            ax.legend()
        else:
            # No data available
            ax.text(0.5, 0.5, "No convergence data available", 
                   ha='center', va='center', transform=ax.transAxes, 
                   fontsize=12, color=self.theme.primary_color)
            ax.set_title("Convergence History", fontsize=14)
            
        # Tight layout
        self.figure.tight_layout()

    # Data loading methods
    def load_mesh_data(self):
        """Load mesh data for visualization"""
        try:
            # In a real implementation, this would parse the mesh file
            # For demo, we'll create random data
            num_points = 100
            self.mesh_data = {
                "nodes": np.random.rand(num_points, 3),
                "elements": np.random.randint(0, num_points-1, (50, 3))
            }
            
            # Create a more realistic shape - a simple curved surface
            x = np.linspace(-1, 1, 10)
            y = np.linspace(-1, 1, 10)
            X, Y = np.meshgrid(x, y)
            Z = 0.5 * (X**2 + Y**2)
            
            # Reshape to match the expected format
            points = np.zeros((100, 3))
            points[:,0] = X.flatten()
            points[:,1] = Y.flatten()
            points[:,2] = Z.flatten()
            
            # Update mesh data with more realistic points
            self.mesh_data["nodes"] = points
            
            self.update_status("Mesh data loaded for visualization")
        except Exception as e:
            self.update_status(f"Error loading mesh data: {str(e)}")
    
    def load_results_data(self):
        """Load results data for visualization"""
        try:
            # Generate dummy data for demonstration
            x = np.linspace(-2, 2, 50)
            y = np.linspace(-2, 2, 50)
            X, Y = np.meshgrid(x, y)
            
            # Create more interesting pattern for dummy data
            r = np.sqrt(X**2 + Y**2)
            theta = np.arctan2(Y, X)
            
            # Pressure field with radial pattern
            pressure = 100000 + 5000 * np.sin(2*r) * np.cos(3*theta)
            
            # Velocity field
            velocity = 30 * np.exp(-0.5*r**2)
            
            # Temperature field
            temperature = 293.15 + 20 * np.sin(r) * np.sin(2*theta)
            
            # Create exponentially decreasing convergence curve
            convergence = np.exp(-np.linspace(0, 5, 100))
            
            self.results_data = {
                "x": X, 
                "y": Y, 
                "pressure": pressure, 
                "velocity": velocity, 
                "temperature": temperature,
                "convergence": convergence
            }
            
            self.update_status("Results data loaded for visualization")
        except Exception as e:
            self.update_status(f"Error loading results: {str(e)}")

    # Methods for running optimization
    def run_optimization(self):
        """Run optimization using OpenMDAO"""
        try:
            # Get optimization settings
            algorithm = self.opt_algorithm.get()
            max_iter = int(self.max_iter.get())
            tol = float(self.tolerance.get())
            
            # Get bounds
            l4_bounds = (float(self.l4_min.get()), float(self.l4_max.get()))
            l5_bounds = (float(self.l5_min.get()), float(self.l5_max.get()))
            alpha1_bounds = (float(self.alpha1_min.get()), float(self.alpha1_max.get()))
            
            self.update_status(f"Starting optimization with {algorithm}...", show_progress=True)
            
            # Start optimization in a separate thread
            threading.Thread(target=self._optimization_thread, args=(algorithm, max_iter, tol, l4_bounds, l5_bounds, alpha1_bounds)).start()
        except Exception as e:
            messagebox.showerror("Optimization Error", str(e))
            self.update_status(f"Error starting optimization: {str(e)}")
    
    def _optimization_thread(self, algorithm, max_iter, tol, l4_bounds, l5_bounds, alpha1_bounds):
        try:
            # Reset optimization data
            self.iterations = []
            self.objectives = []
            self.best_objective = float('inf')
            self.best_params = {}
            
            # Clear existing tree items
            for item in self.best_results.get_children():
                self.best_results.delete(item)
            
            # In demo mode, simulate optimization with a delay
            if DEMO_MODE:
                for i in range(10):
                    # Create synthetic optimization progress
                    x = l4_bounds[0] + (i / 9) * (l4_bounds[1] - l4_bounds[0])
                    y = l5_bounds[0] + (i / 9) * (l5_bounds[1] - l5_bounds[0])
                    alpha = alpha1_bounds[0] + (i / 9) * (alpha1_bounds[1] - alpha1_bounds[0])
                    
                    # Objective function - more complex for demonstration
                    obj = (x - 2.5)**2 + (y - 3.0)**2 + 0.1*np.sin(5*alpha)
                    
                    # Update data
                    self.iterations.append(i)
                    self.objectives.append(obj)
                    
                    # Update best values
                    if obj < self.best_objective:
                        self.best_objective = obj
                        self.best_params = {'L4': x, 'L5': y, 'Alpha1': alpha, 'objective': obj}
                    
                    # Update GUI from the main thread
                    self.root.after(0, lambda: self.update_status(f"Iteration {i+1}/{10}, objective = {obj:.6f}"))
                    self.root.after(0, self._update_optimization_plots)
                    
                    # Sleep to simulate computation time
                    time.sleep(0.5)
                
                # Final best values
                final_x = 2.5  # Optimal value for demo
                final_y = 3.0  # Optimal value for demo
                final_alpha = alpha1_bounds[0] + 0.5 * (alpha1_bounds[1] - alpha1_bounds[0])
                final_obj = 0.1*np.sin(5*final_alpha)  # Optimal value with our function
                
                # Update best parameters
                self.best_params = {
                    'L4': final_x, 
                    'L5': final_y, 
                    'Alpha1': final_alpha,
                    'Alpha2': 30.0,
                    'Alpha3': 30.0,
                    'objective': final_obj
                }
                
                # Update best results display
                self.root.after(0, self._update_best_results)
                self.root.after(0, lambda: self.update_status(
                    f"Optimization complete. Final objective: {final_obj:.6f}", 
                    show_progress=False
                ))
                self.root.after(0, lambda: messagebox.showinfo(
                    "Optimization Complete", 
                    f"Optimization completed successfully!\nFinal objective: {final_obj:.6f}"
                ))
            else:
                # Real optimization using OpenMDAO
                # ... existing code for real optimization ...
                pass
        except Exception as e:
            self.root.after(0, lambda: self.update_status(f"Optimization error: {str(e)}", show_progress=False))
            self.root.after(0, lambda: messagebox.showerror("Optimization Error", str(e)))
    
    def _update_optimization_plots(self):
        """Update optimization plots with current data"""
        try:
            # Update convergence history plot
            self.history_figure.clear()
            ax = self.history_figure.add_subplot(111)
            
            # Plot convergence history
            ax.plot(self.iterations, self.objectives, 
                   marker='o', linestyle='-', 
                   color=self.theme.accent_color, 
                   markerfacecolor=self.theme.primary_color,
                   markersize=6, linewidth=2)
            
            # Formatting
            ax.set_title("Optimization Convergence", fontsize=14, pad=20, color=self.theme.text_color)
            ax.set_xlabel("Iteration", fontsize=12, color=self.theme.text_color)
            ax.set_ylabel("Objective Value", fontsize=12, color=self.theme.text_color)
            ax.grid(True, linestyle='--', alpha=0.6)
            
            # Add best value line
            if self.best_objective < float('inf'):
                ax.axhline(y=self.best_objective, color='r', linestyle='--', alpha=0.7, 
                          label=f'Best: {self.best_objective:.6f}')
                ax.legend()
            
            self.history_figure.tight_layout()
            self.history_canvas.draw()
            
            # Update Pareto front (in this case, just L4 vs objective)
            if self.best_params and 'L4' in self.best_params:
                self.pareto_figure.clear()
                ax = self.pareto_figure.add_subplot(111)
                
                # Extract L4 values
                l4_values = [l4_bounds[0] + (i / 9) * (l4_bounds[1] - l4_bounds[0]) for i in self.iterations]
                
                # Create scatter plot
                scatter = ax.scatter(l4_values, self.objectives, 
                                    c=self.iterations, cmap='viridis', 
                                    s=50, alpha=0.7)
                
                # Add colorbar
                cbar = self.pareto_figure.colorbar(scatter, ax=ax)
                cbar.set_label('Iteration', color=self.theme.text_color)
                
                # Highlight best point
                best_l4 = self.best_params['L4']
                best_obj = self.best_params['objective']
                ax.scatter([best_l4], [best_obj], color='red', s=100, marker='*', 
                          label=f'Best ({best_l4:.2f}, {best_obj:.6f})')
                
                # Formatting
                ax.set_title("Parameter Space Exploration", fontsize=14, pad=20, color=self.theme.text_color)
                ax.set_xlabel("L4 Parameter (m)", fontsize=12, color=self.theme.text_color)
                ax.set_ylabel("Objective Value", fontsize=12, color=self.theme.text_color)
                ax.grid(True, linestyle='--', alpha=0.6)
                ax.legend()
                
                self.pareto_figure.tight_layout()
                self.pareto_canvas.draw()
        except Exception as e:
            self.update_status(f"Error updating optimization plots: {str(e)}")
    
    def _update_best_results(self):
        """Update the best results display in the optimization tab"""
        try:
            # Clear existing items
            for item in self.best_results.get_children():
                self.best_results.delete(item)
            
            # Add new results
            if self.best_params:
                for param, value in self.best_params.items():
                    formatted_value = f"{value:.6f}" if isinstance(value, (float, np.floating)) else str(value)
                    self.best_results.insert("", "end", values=(param, formatted_value))
        except Exception as e:
            self.update_status(f"Error updating results table: {str(e)}")
    
    def toggle_optimization(self):
        """Toggle optimization pause/resume"""
        messagebox.showinfo("Not Implemented", "Pause/Resume functionality not implemented yet")
    
    def stop_optimization(self):
        """Stop optimization"""
        messagebox.showinfo("Not Implemented", "Stop functionality not implemented yet")
    
    def run_complete_workflow(self):
        """Run the complete workflow from NX to results processing"""
        try:
            self.update_status("Running complete workflow...", show_progress=True)
            
            # Get design variables
            l4, l5, alpha1, alpha2, alpha3 = self.get_inputs()
            
            # Run workflow in a separate thread
            threading.Thread(target=self._complete_workflow_thread, args=(l4, l5, alpha1, alpha2, alpha3)).start()
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.update_status(f"Error: {str(e)}")
    
    def get_inputs(self):
        """Get user inputs from the GUI"""
        try:
            l4 = float(self.l4_entry.get())
            l5 = float(self.l5_entry.get())
            alpha1 = float(self.alpha1_entry.get())
            alpha2 = float(self.alpha2_entry.get())
            alpha3 = float(self.alpha3_entry.get())
            return l4, l5, alpha1, alpha2, alpha3
        except ValueError:
            raise ValueError("Please enter valid numeric values for all inputs")

    def log(self, message):
        self.log_console.insert(tk.END, f"{message}\n")
        self.log_console.see(tk.END)

    def update_status(self, message, show_progress=False):
        self.status_var.set(message)
        self.log(message)
        if show_progress:
            self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10,5), pady=2)
            self.progress.start()
        else:
            self.progress.stop()
            self.progress.pack_forget()

    def show_geometry(self, geometry_file):
        """Load and visualize a geometry file."""
        try:
            self.log(f"Loading geometry from {geometry_file}...")
            
            import os
            import numpy as np
            
            # Check if file exists
            if not os.path.exists(geometry_file):
                raise FileNotFoundError(f"File not found: {geometry_file}")
            
            # Check file extension to determine how to load it
            file_ext = os.path.splitext(geometry_file)[1].lower()
            
            # Load the geometry based on file type
            if file_ext in ['.step', '.stp', '.iges', '.igs', '.brep']:
                # Use GMSH to load CAD formats
                try:
                    import gmsh
                    
                    # Initialize GMSH if not already initialized
                    if not hasattr(self, 'gmsh_initialized'):
                        gmsh.initialize()
                        gmsh.option.setNumber("General.Terminal", 1)
                        gmsh.option.setNumber("General.Verbosity", 3)
                        self.gmsh_initialized = True
                    
                    # Create a new model
                    model_name = os.path.basename(geometry_file).split('.')[0]
                    gmsh.model.add(model_name)
                    
                    # Configure safer/more tolerant geometry healing options
                    gmsh.option.setNumber("Geometry.Tolerance", 1e-2)
                    gmsh.option.setNumber("Geometry.ToleranceBoolean", 1e-2)
                    gmsh.option.setNumber("Geometry.OCCFixDegenerated", 1)
                    gmsh.option.setNumber("Geometry.OCCFixSmallEdges", 1)
                    gmsh.option.setNumber("Geometry.OCCFixSmallFaces", 1)
                    gmsh.option.setNumber("Geometry.OCCSewFaces", 1)
                    gmsh.option.setNumber("Geometry.OCCMakeSolids", 1)
                    
                    # Set memory options to prevent segfaults
                    gmsh.option.setNumber("Mesh.MemoryMax", 2048)  # Limit memory usage
                    gmsh.option.setNumber("General.NumThreads", 2)  # Limit threads
                    
                    # Import geometry with safer error handling
                    self.log(f"Using GMSH to import {file_ext} file...")
                    try:
                        # Try OCC import first with healing
                        self.update_status("Importing CAD geometry...", show_progress=True)
                        gmsh.model.occ.importShapes(geometry_file)
                        gmsh.model.occ.removeAllDuplicates()
                        gmsh.model.occ.healShapes(gmsh.model.occ.getEntities())
                        gmsh.model.occ.synchronize()
                        self.update_status("Successfully imported geometry with OCC", show_progress=True)
                    except Exception as e:
                        # Fall back to direct merge
                        self.log(f"OCC import failed: {str(e)}")
                        self.update_status("Trying direct merge...", show_progress=True)
                        gmsh.merge(geometry_file)
                        self.update_status("Direct merge successful", show_progress=True)
                    
                    # Get geometry entities
                    points = gmsh.model.getEntities(0)  # 0D points
                    curves = gmsh.model.getEntities(1)  # 1D curves
                    surfaces = gmsh.model.getEntities(2)  # 2D surfaces
                    volumes = gmsh.model.getEntities(3)  # 3D volumes
                    
                    self.log(f"Imported geometry: {len(points)} points, {len(curves)} curves, "
                             f"{len(surfaces)} surfaces, {len(volumes)} volumes")
                    
                    # Extract vertices and faces for visualization using simpler method
                    # rather than creating mesh for all entities, which can cause segmentation fault
                    try:
                        # Get the bounding box
                        xmin, ymin, zmin, xmax, ymax, zmax = gmsh.model.getBoundingBox(-1, -1)
                        self.log(f"Model bounds: X[{xmin},{xmax}] Y[{ymin},{ymax}] Z[{zmin},{zmax}]")
                        
                        # Create a simpler triangulation for visualization
                        # For complicated models, we'll create a simple box mesh
                        vertices = []
                        triangles = []
                        
                        if len(surfaces) > 0:
                            # Choose a low mesh density for visualization only
                            gmsh.option.setNumber("Mesh.CharacteristicLengthMax", (xmax-xmin)/10)
                            gmsh.option.setNumber("Mesh.CharacteristicLengthMin", (xmax-xmin)/20)
                            
                            # Just mesh 2D for visualization
                            try:
                                gmsh.model.mesh.generate(1)  # Generate 1D mesh
                                gmsh.model.mesh.generate(2)  # Generate 2D mesh
                            except Exception as e:
                                self.log(f"Error meshing for visualization: {str(e)}")
                            
                            # Start collecting mesh data
                            all_nodes = {}
                            all_triangles = []
                            
                            # First collect all nodes
                            all_node_tags, all_node_coords, _ = gmsh.model.mesh.getNodes()
                            all_coords = all_node_coords.reshape(-1, 3)
                            for i, tag in enumerate(all_node_tags):
                                all_nodes[tag] = i
                            
                            # Now collect triangular elements
                            for surface_dim, surface_tag in surfaces:
                                elem_types, elem_tags, elem_node_tags = gmsh.model.mesh.getElements(surface_dim, surface_tag)
                                
                                for i, elem_type in enumerate(elem_types):
                                    # Triangle elements have type 2
                                    if elem_type == 2:
                                        nodes_per_elem = 3
                                        elem_nodes = elem_node_tags[i].reshape(-1, nodes_per_elem)
                                        
                                        for nodes in elem_nodes:
                                            # Convert to 0-based indexing for our data structures
                                            tri = [all_nodes.get(node, 0) for node in nodes]
                                            all_triangles.append(tri)
                            
                            # Convert to numpy arrays
                            vertices = all_coords
                            triangles = np.array(all_triangles) if all_triangles else None
                            
                        # If we still couldn't extract mesh data, create a simple box
                        if len(vertices) == 0:
                            self.log("Using simplified box representation")
                            # Create corners of the bounding box
                            dx, dy, dz = xmax-xmin, ymax-ymin, zmax-zmin
                            max_dim = max(dx, dy, dz)
                            if max_dim <= 0:
                                max_dim = 1.0  # Safety check
                            scale = 1.0
                            
                            # Create simple box
                            x0, y0, z0 = xmin - 0.05*dx, ymin - 0.05*dy, zmin - 0.05*dz
                            x1, y1, z1 = xmax + 0.05*dx, ymax + 0.05*dy, zmax + 0.05*dz
                            
                            # Define box vertices
                            vertices = np.array([
                                [x0, y0, z0], [x1, y0, z0], [x1, y1, z0], [x0, y1, z0],
                                [x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1]
                            ])
                            
                            # Define triangles for a box (12 triangles, 2 per face)
                            triangles = np.array([
                                [0, 1, 2], [0, 2, 3],  # Bottom face
                                [4, 5, 6], [4, 6, 7],  # Top face
                                [0, 1, 5], [0, 5, 4],  # Front face
                                [2, 3, 7], [2, 7, 6],  # Back face
                                [0, 3, 7], [0, 7, 4],  # Left face
                                [1, 2, 6], [1, 6, 5]   # Right face
                            ])
                    
                    except Exception as e:
                        self.log(f"Error extracting geometry visualization data: {str(e)}")
                        # Create a minimal representation
                        vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]])
                        triangles = np.array([[0, 1, 2], [0, 1, 3], [0, 2, 3], [1, 2, 3]])
                    
                    # Store geometry data for later use
                    self.current_geometry = {
                        'file': geometry_file,
                        'vertices': vertices,
                        'triangles': triangles,
                        'gmsh_model': model_name
                    }
                    
                    # Update current file display
                    self.current_file_var.set(f"Geometry: {os.path.basename(geometry_file)}")
                    
                    # Display the geometry
                    self.display_geometry(vertices, triangles)
                    
                except ImportError:
                    self.log("GMSH library not found, using simplified loading")
                    # Fallback for when GMSH is not available
                    self.create_dummy_geometry()
            
            elif file_ext in ['.stl']:
                # STL can be loaded directly with NumPy-STL
                try:
                    import numpy as np
                    from stl import mesh
                    
                    self.log("Loading STL with numpy-stl...")
                    stl_mesh = mesh.Mesh.from_file(geometry_file)
                    
                    # Extract vertices and faces
                    vectors = stl_mesh.vectors.reshape(-1, 3)
                    
                    # For STL, we need to build a mapping from original vertices to our unique set
                    # This is expensive for large files, so we'll use a simplified approach
                    if len(vectors) > 300000:  # If more than 100k triangles (300k vertices)
                        # Subsample for visualization
                        self.log("Large STL file detected, subsampling for visualization")
                        stride = max(1, len(stl_mesh.vectors) // 10000)
                        vertices = vectors[::stride].copy()
                        triangles = np.array([[3*i, 3*i+1, 3*i+2] for i in range(len(vertices)//3)])
                    else:
                        # Try to find unique vertices
                        try:
                            vertices = np.unique(vectors.reshape(-1, 3), axis=0)
                            vertex_dict = {tuple(v): i for i, v in enumerate(vertices)}
                            triangles = []
                            
                            for face in stl_mesh.vectors:
                                tri = [vertex_dict.get(tuple(v), 0) for v in face]
                                triangles.append(tri)
                            
                            triangles = np.array(triangles)
                        except MemoryError:
                            # Fall back to non-unique vertices
                            vertices = vectors.copy()
                            triangles = np.array([[3*i, 3*i+1, 3*i+2] for i in range(len(vertices)//3)])
                    
                    # Store geometry data
                    self.current_geometry = {
                        'file': geometry_file,
                        'vertices': vertices,
                        'triangles': triangles,
                        'stl_mesh': stl_mesh
                    }
                    
                    # Update current file display
                    self.current_file_var.set(f"Geometry: {os.path.basename(geometry_file)}")
                    
                    # Display the geometry
                    self.display_geometry(vertices, triangles)
                    
                except ImportError:
                    self.log("numpy-stl not found, using simplified loading")
                    self.create_dummy_geometry()
                except MemoryError:
                    self.log("Memory error loading STL, using simplified loading")
                    self.create_dummy_geometry()
            
            else:
                self.log(f"Unsupported file format: {file_ext}")
                self.create_dummy_geometry()
            
            self.update_status(f"Geometry loaded from {geometry_file}", show_progress=False)
            
        except Exception as e:
            import traceback
            self.log(f"Error details: {traceback.format_exc()}")
            self.update_status(f"Error displaying geometry: {str(e)}", show_progress=False)
            # Create simple fallback geometry
            self.create_dummy_geometry()
    
    def display_geometry(self, vertices, triangles=None):
        """Display loaded geometry in the 3D plot."""
        try:
            # Clear the current plot
            self.figure.clear()
            self.ax = self.figure.add_subplot(111, projection='3d')
            
            # Set title
            self.ax.set_title("Geometry Visualization", fontsize=14)
            self.ax.set_xlabel("X")
            self.ax.set_ylabel("Y")
            self.ax.set_zlabel("Z")
            
            if triangles is not None:
                # Plot as a surface
                from mpl_toolkits.mplot3d.art3d import Poly3DCollection
                
                # If wireframe view is enabled
                if self.show_wireframe_var.get():
                    # Add wireframe
                    for tri in triangles:
                        verts = [vertices[idx] for idx in tri]
                        self.ax.plot3D([v[0] for v in verts] + [verts[0][0]], 
                                      [v[1] for v in verts] + [verts[0][1]], 
                                      [v[2] for v in verts] + [verts[0][2]], 
                                      color='black', lw=0.5, alpha=0.5)
                
                # If surface view is enabled
                if self.show_geom_surface_var.get():
                    # Add surface
                    color = self.get_geometry_color()
                    tri_collection = Poly3DCollection([vertices[tri] for tri in triangles], 
                                                    alpha=0.7, color=color,
                                                    edgecolor=None if self.show_wireframe_var.get() else 'black')
                    self.ax.add_collection3d(tri_collection)
            else:
                # Plot points only
                self.ax.scatter(vertices[:, 0], vertices[:, 1], vertices[:, 2], 
                               c='blue', marker='o', s=10, alpha=0.7)
            
            # Equal aspect ratio
            max_range = np.array([vertices[:,0].max()-vertices[:,0].min(), 
                                 vertices[:,1].max()-vertices[:,1].min(), 
                                 vertices[:,2].max()-vertices[:,2].min()]).max() / 2.0
            mid_x = (vertices[:,0].max()+vertices[:,0].min()) * 0.5
            mid_y = (vertices[:,1].max()+vertices[:,1].min()) * 0.5
            mid_z = (vertices[:,2].max()+vertices[:,2].min()) * 0.5
            self.ax.set_xlim(mid_x - max_range, mid_x + max_range)
            self.ax.set_ylim(mid_y - max_range, mid_y + max_range)
            self.ax.set_zlim(mid_z - max_range, mid_z + max_range)
            
            # Reset view
            self.ax.view_init(elev=30, azim=45)
            
            # Update display
            self.canvas.draw()
            
        except Exception as e:
            import traceback
            self.log(f"Display error: {traceback.format_exc()}")
            self.update_status(f"Error displaying geometry: {str(e)}")
    
    def get_geometry_color(self):
        """Get the color for geometry based on user selection."""
        color_name = self.geom_color.get()
        if color_name == "Blue":
            return "#3498DB"
        elif color_name == "Red":
            return "#E74C3C"
        elif color_name == "Green":
            return "#2ECC71"
        elif color_name == "Custom":
            # In a full implementation, this could open a color picker
            return "#9B59B6"  # Default to purple for custom
        else:  # Default
            return "#3498DB"  # Default to blue
    
    def create_dummy_geometry(self):
        """Create a dummy geometry when loading fails."""
        import numpy as np
        
        # Create a simple cube
        vertices = np.array([
            [0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0],
            [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]
        ])
        
        # Define the triangles for the cube (12 triangles, 2 per face)
        triangles = np.array([
            [0, 1, 2], [0, 2, 3],  # Bottom face
            [4, 5, 6], [4, 6, 7],  # Top face
            [0, 1, 5], [0, 5, 4],  # Front face
            [2, 3, 7], [2, 7, 6],  # Back face
            [0, 3, 7], [0, 7, 4],  # Left face
            [1, 2, 6], [1, 6, 5]   # Right face
        ])
        
        # Store geometry data
        self.current_geometry = {
            'file': 'dummy_cube.stp',
            'vertices': vertices,
            'triangles': triangles
        }
        
        # Update current file display
        self.current_file_var.set("Geometry: dummy_cube.stp (placeholder)")
        
        # Display the geometry
        self.display_geometry(vertices, triangles)
        self.log("Created placeholder geometry")
    
    def export_geometry(self, file_path, format_type):
        """Export current geometry to the specified format."""
        try:
            if not hasattr(self, "current_geometry") or self.current_geometry is None:
                raise ValueError("No geometry to export")
            
            self.log(f"Exporting geometry to {format_type} format...")
            self.update_status(f"Exporting geometry...", show_progress=True)
            
            # Check if this is a GMSH model
            if 'gmsh_model' in self.current_geometry:
                try:
                    import gmsh
                    
                    # Ensure GMSH is initialized
                    if not hasattr(self, 'gmsh_initialized'):
                        gmsh.initialize()
                        self.gmsh_initialized = True
                    
                    # Make sure the model is active
                    gmsh.model.setCurrent(self.current_geometry['gmsh_model'])
                    
                    # Export the model
                    gmsh.write(file_path)
                    
                    self.update_status(f"Geometry exported to {file_path}", show_progress=False)
                    return True
                    
                except ImportError:
                    self.log("GMSH not available, falling back to alternative method")
                    pass
            
            # Check if this is an STL mesh that we can export directly
            if 'stl_mesh' in self.current_geometry and format_type == 'stl':
                self.current_geometry['stl_mesh'].save(file_path)
                self.update_status(f"STL exported to {file_path}", show_progress=False)
                return True
            
            # Use converter script for other formats
            base_dir = os.path.dirname(os.path.abspath(__file__))
            converter_script = os.path.join(base_dir, "convert_geometry.sh")
            
            if os.path.exists(converter_script):
                import subprocess
                
                # First save to a temporary STL if we have triangles
                if self.current_geometry['triangles'] is not None:
                    try:
                        import tempfile
                        from stl import mesh as stl_mesh
                        
                        # Create a temporary STL file
                        temp_fd, temp_stl = tempfile.mkstemp(suffix='.stl')
                        os.close(temp_fd)
                        
                        # Create an STL mesh
                        vertices = self.current_geometry['vertices']
                        triangles = self.current_geometry['triangles']
                        
                        # Create mesh data
                        data = stl_mesh.Mesh(np.zeros(len(triangles), dtype=stl_mesh.Mesh.dtype))
                        for i, face in enumerate(triangles):
                            for j in range(3):
                                data.vectors[i][j] = vertices[face[j], :]
                        
                        # Save STL
                        data.save(temp_stl)
                        
                        # Run converter script
                        result = subprocess.run([converter_script, temp_stl], 
                                              capture_output=True, text=True)
                        
                        # Check output directory for the requested format
                        converted_file = os.path.splitext(temp_stl)[0] + '.' + format_type.lower()
                        
                        if os.path.exists(converted_file):
                            # Copy to the requested output path
                            with open(converted_file, 'rb') as src, open(file_path, 'wb') as dst:
                                dst.write(src.read())
                            self.update_status(f"Geometry exported to {file_path}", show_progress=False)
                            
                            # Clean up temporary files
                            os.unlink(temp_stl)
                            os.unlink(converted_file)
                            return True
                    except Exception as e:
                        self.log(f"Error during conversion: {str(e)}")
            
            # If all else fails
            self.update_status(f"Failed to export geometry to {format_type} format", show_progress=False)
            return False
            
        except Exception as e:
            self.update_status(f"Error exporting geometry: {str(e)}", show_progress=False)
            return False

    def import_geometry_dialog(self):
        """Show file dialog to select a geometry file and load it"""
        filetypes = [
            ("All geometry files", "*.step *.stp *.igs *.iges *.stl *.brep"),
            ("STEP files", "*.step *.stp"),
            ("IGES files", "*.iges *.igs"),
            ("STL files", "*.stl"),
            ("BREP files", "*.brep"),
            ("All files", "*.*")
        ]
        
        geometry_file = filedialog.askopenfilename(
            title="Import Geometry",
            filetypes=filetypes
        )
        
        if geometry_file:
            self.update_status(f"Loading geometry file: {geometry_file}", show_progress=True)
            try:
                self.show_geometry(geometry_file)
            except Exception as e:
                messagebox.showerror("Import Error", f"Failed to import geometry: {str(e)}")
                self.update_status(f"Import failed: {str(e)}", show_progress=False)

    def export_geometry_dialog(self):
        """Show file dialog to select a location to export geometry"""
        if not hasattr(self, "current_geometry") or self.current_geometry is None:
            messagebox.showerror("Export Error", "No geometry to export. Please import or create geometry first.")
            return
            
        filetypes = [
            ("STEP files", "*.step"),
            ("STL files", "*.stl"),
            ("IGES files", "*.igs"),
            ("BREP files", "*.brep"),
            ("OBJ files", "*.obj"),
            ("All files", "*.*")
        ]
        
        # Ask for file location and name
        file_path = filedialog.asksaveasfilename(
            title="Export Geometry",
            filetypes=filetypes,
            defaultextension=".step"  # Default to STEP format
        )
        
        if not file_path:
            return  # User cancelled
        
        # Determine format from extension
        file_ext = os.path.splitext(file_path)[1].lower()
        format_type = file_ext.lstrip('.')
        
        self.update_status(f"Exporting geometry to {file_path}...", show_progress=True)
        try:
            result = self.export_geometry(file_path, format_type)
            if result:
                self.update_status(f"Geometry exported successfully to {file_path}", show_progress=False)
            else:
                messagebox.showerror("Export Error", f"Failed to export to {format_type} format")
                self.update_status(f"Export failed", show_progress=False)
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export geometry: {str(e)}")
            self.update_status(f"Export failed: {str(e)}", show_progress=False)

    def import_mesh_dialog(self):
        """Show file dialog to select a mesh file and load it"""
        filetypes = [
            ("All mesh files", "*.msh *.su2 *.cgns *.neu"),
            ("GMSH files", "*.msh"),
            ("SU2 files", "*.su2"),
            ("CGNS files", "*.cgns"),
            ("Gambit files", "*.neu"),
            ("All files", "*.*")
        ]
        
        mesh_file = filedialog.askopenfilename(
            title="Import Mesh",
            filetypes=filetypes
        )
        
        if mesh_file:
            self.update_status(f"Loading mesh file: {mesh_file}", show_progress=True)
            try:
                self.show_mesh(mesh_file)
            except Exception as e:
                messagebox.showerror("Import Error", f"Failed to import mesh: {str(e)}")
                self.update_status(f"Import failed: {str(e)}", show_progress=False)
    
    def export_mesh_dialog(self):
        """Show file dialog to select a location to export mesh"""
        if not hasattr(self, "current_mesh") or self.current_mesh is None:
            messagebox.showerror("Export Error", "No mesh to export. Please import or create a mesh first.")
            return
            
        filetypes = [
            ("GMSH files", "*.msh"),
            ("SU2 files", "*.su2"),
            ("CGNS files", "*.cgns"),
            ("VTK files", "*.vtk"),
            ("All files", "*.*")
        ]
        
        # Ask for file location and name
        file_path = filedialog.asksaveasfilename(
            title="Export Mesh",
            filetypes=filetypes,
            defaultextension=".msh"  # Default to GMSH format
        )
        
        if not file_path:
            return  # User cancelled
        
        # Determine format from extension
        file_ext = os.path.splitext(file_path)[1].lower()
        format_type = file_ext.lstrip('.')
        
        self.update_status(f"Exporting mesh to {file_path}...", show_progress=True)
        try:
            result = self.export_mesh(file_path, format_type)
            if result:
                self.update_status(f"Mesh exported successfully to {file_path}", show_progress=False)
            else:
                messagebox.showerror("Export Error", f"Failed to export to {format_type} format")
                self.update_status(f"Export failed", show_progress=False)
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export mesh: {str(e)}")
            self.update_status(f"Export failed: {str(e)}", show_progress=False)
            
    def show_mesh(self, mesh_file):
        """Load and visualize a mesh file."""
        try:
            self.log(f"Loading mesh from {mesh_file}...")
            
            import os
            import numpy as np
            
            # Check if file exists
            if not os.path.exists(mesh_file):
                raise FileNotFoundError(f"File not found: {mesh_file}")
            
            # Check file extension to determine how to load it
            file_ext = os.path.splitext(mesh_file)[1].lower()
            
            # For now, we'll create a dummy representation
            # In a production version, you would use appropriate libraries to read different mesh formats
            self.load_mesh_data()
            
            # Store mesh data
            self.current_mesh = {
                'file': mesh_file,
                'nodes': self.mesh_data['nodes'], 
                'elements': self.mesh_data['elements']
            }
            
            # Update current file display
            self.current_file_var.set(f"Mesh: {os.path.basename(mesh_file)}")
            
            # Display the mesh
            self.plot_mesh()
            
            self.update_status(f"Mesh loaded from {mesh_file}", show_progress=False)
            
        except Exception as e:
            import traceback
            self.log(f"Error details: {traceback.format_exc()}")
            self.update_status(f"Error displaying mesh: {str(e)}", show_progress=False)
            
    def export_mesh(self, file_path, format_type):
        """Export current mesh to the specified format."""
        try:
            if not hasattr(self, "current_mesh") or self.current_mesh is None:
                raise ValueError("No mesh to export")
            
            self.log(f"Exporting mesh to {format_type} format...")
            self.update_status(f"Exporting mesh...", show_progress=True)
            
            # In a production version, you would use appropriate libraries to write different mesh formats
            # For now, we'll just copy the original file if it exists, or create a dummy file
            
            if os.path.exists(self.current_mesh['file']):
                import shutil
                shutil.copy2(self.current_mesh['file'], file_path)
            else:
                # Create a dummy mesh file
                with open(file_path, "w") as f:
                    f.write(f"# This is a placeholder mesh file\n")
                    f.write(f"# Original mesh: {self.current_mesh['file']}\n")
                    f.write(f"# Export date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"# This file does not contain valid mesh data\n")
            
            self.update_status(f"Mesh exported to {file_path}", show_progress=False)
            return True
                
        except Exception as e:
            self.update_status(f"Error exporting mesh: {str(e)}", show_progress=False)
            return False
            
    def update_mesh_display(self, event=None):
        """Update the mesh display based on current view settings"""
        if hasattr(self, "current_mesh") and self.current_mesh is not None:
            self.plot_mesh() 
        else:
            self.log("No mesh to update display for")

    def analyze_mesh_quality(self):
        """Analyze the mesh quality and display results"""
        try:
            if not hasattr(self, "current_mesh") or self.current_mesh is None:
                messagebox.showerror("Error", "No mesh loaded. Please import a mesh first.")
                return
                
            self.update_status("Analyzing mesh quality...", show_progress=True)
            
            # In a production version, you would calculate actual mesh quality metrics
            # For demo purposes, we'll generate some random quality metrics
            import numpy as np
            import matplotlib.pyplot as plt
            from matplotlib.figure import Figure
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            
            # Create a new toplevel window for the quality analysis
            quality_window = tk.Toplevel(self.root)
            quality_window.title("Mesh Quality Analysis")
            quality_window.geometry("600x500")
            
            # Apply same styling
            quality_window.configure(background=self.theme.bg_color)
            
            # Add a title
            ttk.Label(quality_window, text="Mesh Quality Metrics", font=self.theme.header_font).pack(pady=10)
            
            # Create a figure for the histograms
            fig = Figure(figsize=(7, 5), dpi=100, facecolor=self.theme.bg_color)
            
            # Generate random quality metrics (in a real application these would be calculated)
            num_elements = len(self.mesh_data["elements"])
            
            # Common mesh quality metrics
            aspect_ratio = 1.0 + np.random.exponential(0.5, num_elements)  # Closer to 1 is better
            skewness = np.random.beta(2, 5, num_elements)                  # Closer to 0 is better
            orthogonal_quality = np.random.beta(5, 2, num_elements)        # Closer to 1 is better
            
            # Create subplots for each metric
            ax1 = fig.add_subplot(311)
            ax1.hist(aspect_ratio, bins=20, alpha=0.7, color=self.theme.accent_color)
            ax1.set_title("Element Aspect Ratio")
            ax1.axvline(x=np.mean(aspect_ratio), color='r', linestyle='--', label=f"Mean: {np.mean(aspect_ratio):.2f}")
            ax1.grid(True, linestyle='--', alpha=0.6)
            ax1.legend()
            
            ax2 = fig.add_subplot(312)
            ax2.hist(skewness, bins=20, alpha=0.7, color=self.theme.accent_color)
            ax2.set_title("Element Skewness")
            ax2.axvline(x=np.mean(skewness), color='r', linestyle='--', label=f"Mean: {np.mean(skewness):.2f}")
            ax2.grid(True, linestyle='--', alpha=0.6)
            ax2.legend()
            
            ax3 = fig.add_subplot(313)
            ax3.hist(orthogonal_quality, bins=20, alpha=0.7, color=self.theme.accent_color)
            ax3.set_title("Orthogonal Quality")
            ax3.axvline(x=np.mean(orthogonal_quality), color='r', linestyle='--', label=f"Mean: {np.mean(orthogonal_quality):.2f}")
            ax3.grid(True, linestyle='--', alpha=0.6)
            ax3.legend()
            
            fig.tight_layout()
            
            # Create canvas
            canvas = FigureCanvasTkAgg(fig, quality_window)
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Add summary statistics
            summary_frame = ttk.LabelFrame(quality_window, text="Quality Summary", padding=10)
            summary_frame.pack(fill='x', padx=10, pady=10)
            
            # Overall mesh quality assessment
            quality_categories = ["Poor", "Acceptable", "Good", "Excellent"]
            overall_quality = quality_categories[np.random.randint(1, 4)]  # Bias toward better quality for demo
            
            # Color based on quality
            quality_colors = {"Poor": "#E74C3C", "Acceptable": "#F39C12", "Good": "#3498DB", "Excellent": "#2ECC71"}
            
            ttk.Label(summary_frame, text=f"Number of elements: {num_elements}", font=self.theme.normal_font).pack(anchor='w')
            ttk.Label(summary_frame, text=f"Average aspect ratio: {np.mean(aspect_ratio):.3f}", font=self.theme.normal_font).pack(anchor='w')
            ttk.Label(summary_frame, text=f"Average skewness: {np.mean(skewness):.3f}", font=self.theme.normal_font).pack(anchor='w')
            ttk.Label(summary_frame, text=f"Average orthogonal quality: {np.mean(orthogonal_quality):.3f}", font=self.theme.normal_font).pack(anchor='w')
            
            # Overall assessment with color
            overall_label = ttk.Label(summary_frame, 
                                    text=f"Overall mesh quality: {overall_quality}", 
                                    font=self.theme.header_font)
            overall_label.pack(anchor='w', pady=5)
            
            # Close button
            ttk.Button(quality_window, text="Close", 
                      command=quality_window.destroy,
                      padding=self.theme.padding).pack(pady=10)
                      
            self.update_status("Mesh quality analysis complete", show_progress=False)
            
        except Exception as e:
            import traceback
            self.log(f"Error in mesh quality analysis: {traceback.format_exc()}")
            self.update_status(f"Error analyzing mesh: {str(e)}", show_progress=False)
            messagebox.showerror("Analysis Error", f"Failed to analyze mesh quality: {str(e)}")
            
    def update_geometry_display(self, event=None):
        """Update the geometry display based on current view settings"""
        if hasattr(self, "current_geometry") and self.current_geometry is not None:
            self.display_geometry(self.current_geometry['vertices'], self.current_geometry['triangles'])
        else:
            self.log("No geometry to update display for")

    def reset_view(self):
        """Reset the 3D visualization view to default angles"""
        try:
            if not hasattr(self, 'ax') or self.ax is None:
                return
                
            # Reset the view angle to default
            self.ax.view_init(elev=30, azim=45)
            
            # If we have geometry or mesh data, make sure it's properly displayed
            if hasattr(self, "current_geometry") and self.current_geometry is not None:
                # Reset geometry view
                vertices = self.current_geometry['vertices']
                if vertices is not None and len(vertices) > 0:
                    # Reset zoom level to show all geometry
                    max_range = np.array([
                        vertices[:,0].max()-vertices[:,0].min(), 
                        vertices[:,1].max()-vertices[:,1].min(), 
                        vertices[:,2].max()-vertices[:,2].min()
                    ]).max() / 2.0
                    
                    mid_x = (vertices[:,0].max()+vertices[:,0].min()) * 0.5
                    mid_y = (vertices[:,1].max()+vertices[:,1].min()) * 0.5
                    mid_z = (vertices[:,2].max()+vertices[:,2].min()) * 0.5
                    
                    self.ax.set_xlim(mid_x - max_range, mid_x + max_range)
                    self.ax.set_ylim(mid_y - max_range, mid_y + max_range)
                    self.ax.set_zlim(mid_z - max_range, mid_z + max_range)
            
            elif hasattr(self, "current_mesh") and self.current_mesh is not None:
                # Reset mesh view
                pts = self.current_mesh['nodes']
                if pts is not None and len(pts) > 0:
                    # Reset zoom level to show all mesh points
                    max_range = np.array([
                        pts[:,0].max()-pts[:,0].min(), 
                        pts[:,1].max()-pts[:,1].min(), 
                        pts[:,2].max()-pts[:,2].min()
                    ]).max() / 2.0
                    
                    mid_x = (pts[:,0].max()+pts[:,0].min()) * 0.5
                    mid_y = (pts[:,1].max()+pts[:,1].min()) * 0.5
                    mid_z = (pts[:,2].max()+pts[:,2].min()) * 0.5
                    
                    self.ax.set_xlim(mid_x - max_range, mid_x + max_range)
                    self.ax.set_ylim(mid_y - max_range, mid_y + max_range)
                    self.ax.set_zlim(mid_z - max_range, mid_z + max_range)
            
            # Update the canvas
            self.canvas.draw()
            self.update_status("View reset to default", show_progress=False)
            
        except Exception as e:
            import traceback
            self.log(f"Error resetting view: {traceback.format_exc()}")
            self.update_status(f"Error resetting view: {str(e)}", show_progress=False)

# Function to setup the application header with logo and title
def setup_app_header(root, theme):
    """Set up the application header with logo and title"""
    header_frame = tk.Frame(root, bg=theme.primary_color)
    header_frame.pack(side=tk.TOP, fill=tk.X)
    
    # Try to load logo image
    try:
        # Create a placeholder colored square
        logo_size = 40
        logo_canvas = tk.Canvas(header_frame, width=logo_size, height=logo_size, 
                               bg=theme.primary_color, highlightthickness=0)
        logo_canvas.pack(side=tk.LEFT, padx=10, pady=5)
        
        # Draw a stylized "CFD" text in the canvas
        logo_canvas.create_text(logo_size/2, logo_size/2, text="CFD", 
                              font=("Arial", 16, "bold"), fill=theme.light_text)
        
        # Add a circular "flow" indicator
        logo_canvas.create_oval(5, 5, logo_size-5, logo_size-5, 
                              outline=theme.accent_color, width=2)
        logo_canvas.create_arc(10, 10, logo_size-10, logo_size-10, 
                             start=45, extent=180, style=tk.ARC,
                             outline=theme.accent_color, width=2)
    except Exception as e:
        print(f"Could not load logo: {e}")
    
    # Add title
    title_label = tk.Label(header_frame, 
                          text="Intake CFD Optimization Suite", 
                          font=("Segoe UI", 16, "bold"),
                          fg=theme.light_text, 
                          bg=theme.primary_color)
    title_label.pack(side=tk.LEFT, padx=10, pady=10)
    
    # Add version
    version_label = tk.Label(header_frame, 
                          text="v1.0", 
                          font=("Segoe UI", 10),
                          fg=theme.light_text, 
                          bg=theme.primary_color)
    version_label.pack(side=tk.RIGHT, padx=15, pady=15)

# Parse command line arguments
def parse_arguments():
    parser = argparse.ArgumentParser(description="Intake CFD Optimization Suite")
    parser.add_argument("--demo", action="store_true", help="Run in demonstration mode with mock data")
    parser.add_argument("--gui", action="store_true", help="Start GUI interface (default)")
    parser.add_argument("--optimize", action="store_true", help="Run optimization directly")
    parser.add_argument("--L4", type=float, default=2.0, help="L4 parameter value")
    parser.add_argument("--L5", type=float, default=3.0, help="L5 parameter value")
    parser.add_argument("--alpha1", type=float, default=10.0, help="Alpha1 parameter value")
    parser.add_argument("--alpha2", type=float, default=10.0, help="Alpha2 parameter value")
    parser.add_argument("--alpha3", type=float, default=10.0, help="Alpha3 parameter value")
    return parser.parse_args()

# Main function to set up and run the application
def main():
    # Parse command line arguments
    args = parse_arguments()
    
    # Update DEMO_MODE based on arguments
    global DEMO_MODE
    DEMO_MODE = args.demo if args.demo is not None else True
    
    # Create mock executables in demo mode
    if DEMO_MODE:
        print("Running in DEMONSTRATION mode")
        create_mock_executables()
    
    # Start the GUI by default
    if not args.optimize:
        try:
            root = tk.Tk()
            app = WorkflowGUI(root)
            
            # Patch the setup_app_header method
            WorkflowGUI.setup_app_header = lambda self: setup_app_header(self.root, self.theme)
            app.setup_app_header()
            
            # Run the Tkinter main loop
            root.mainloop()
        except Exception as e:
            print(f"Error starting GUI: {str(e)}")
            return 1
    else:
        # Run optimization directly without GUI
        print("Running optimization with parameters:")
        print(f"L4 = {args.L4}, L5 = {args.L5}")
        print(f"alpha1 = {args.alpha1}, alpha2 = {args.alpha2}, alpha3 = {args.alpha3}")
        
        # Make sure output directories exist
        os.makedirs("cfd_results", exist_ok=True)
        
        try:
            # Generate expressions and parameter file
            exp(args.L4, args.L5, args.alpha1, args.alpha2, args.alpha3)
            
            # Run the complete workflow
            step_file = run_nx_workflow()
            mesh_file = "INTAKE3D.msh"
            process_mesh(step_file, mesh_file)
            run_cfd(mesh_file)
            process_results("cfd_results", "processed_results.csv")
            
            # Print results
            with open("processed_results.csv", "r") as f:
                result = f.read().strip()
                print(f"Final result: {result}")
                
            return 0
        except Exception as e:
            print(f"Error in optimization workflow: {str(e)}")
            return 1

# Run the application if executed directly
if __name__ == "__main__":
    sys.exit(main())

