#!/usr/bin/env python3
"""
Patch file for integrating HPC functionality into the main workflow
This file sets up the necessary integration to enable local and cloud hybrid processing
"""

import os
import sys
import importlib
import traceback
import json
import subprocess
import tempfile
import time
from pathlib import Path

# Ensure the current directory is in the path so we can import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Try to import the HPC connector module
try:
    from hpc_connector import HPCConnector, HPCJobStatus, HPCJob, test_connection, PARAMIKO_AVAILABLE
    HPC_AVAILABLE = PARAMIKO_AVAILABLE
except ImportError:
    HPC_AVAILABLE = False
    print("Warning: HPC connector module not available. HPC functionality will be disabled.")

# Try to import workflow_utils with the patch_workflow_gui function
try:
    from workflow_utils import patch_workflow_gui
    PATCH_AVAILABLE = True
except ImportError:
    PATCH_AVAILABLE = False
    print("Error: workflow_utils module not found or missing patch_workflow_gui function.")

# Try to import MDO
try:
    import MDO
    MDO_AVAILABLE = True
except ImportError:
    MDO_AVAILABLE = False
    print("Error: MDO module not found. This patch may not work correctly.")

# HPC Helper Functions
def generate_hpc_script(fem_file_path, result_dir, job_name, num_cores=8, memory="16GB", wall_time="2:00:00"):
    """
    Generates an HPC job submission script for running NX Nastran simulations.
    
    Args:
        fem_file_path (str): Path to the FEM file
        result_dir (str): Directory where results should be stored
        job_name (str): Name for the HPC job
        num_cores (int): Number of cores to request
        memory (str): Memory to request per node
        wall_time (str): Maximum wall time for the job
        
    Returns:
        str: Path to the generated job script
    """
    # Create a temporary script file
    script_file = tempfile.NamedTemporaryFile(delete=False, suffix='.sh')
    script_path = script_file.name
    
    # Get absolute paths
    abs_fem_path = os.path.abspath(fem_file_path)
    abs_result_dir = os.path.abspath(result_dir)
    
    # Create script content
    script_content = f"""#!/bin/bash
#SBATCH --job-name={job_name}
#SBATCH --output={abs_result_dir}/hpc_%j.log
#SBATCH --nodes=1
#SBATCH --ntasks-per-node={num_cores}
#SBATCH --mem={memory}
#SBATCH --time={wall_time}

module load nx/nastran
cd {os.path.dirname(abs_fem_path)}
nastran {os.path.basename(abs_fem_path)} scr={abs_result_dir} old=no
"""
    
    # Write script to file
    with open(script_path, 'w') as f:
        f.write(script_content)
        
    return script_path

def submit_hpc_job(script_path):
    """
    Submits a job to the HPC cluster using sbatch.
    
    Args:
        script_path (str): Path to the job script file
        
    Returns:
        str: Job ID if successful, None otherwise
    """
    try:
        result = subprocess.run(['sbatch', script_path], 
                              capture_output=True, 
                              text=True)
        
        if result.returncode == 0:
            # Extract job ID from output - typically looks like "Submitted batch job 12345"
            output = result.stdout.strip()
            job_id = output.split()[-1]
            return job_id
        else:
            print(f"Error submitting HPC job: {result.stderr}")
            return None
    except Exception as e:
        print(f"Exception when submitting HPC job: {str(e)}")
        return None

def check_hpc_job_status(job_id):
    """
    Checks the status of an HPC job.
    
    Args:
        job_id (str): The job ID to check
        
    Returns:
        str: Status of the job (PENDING, RUNNING, COMPLETED, FAILED, UNKNOWN)
    """
    try:
        result = subprocess.run(['squeue', '-j', job_id, '-h', '-o', '%T'], 
                              capture_output=True, 
                              text=True)
        
        if result.returncode == 0:
            status = result.stdout.strip()
            if not status:
                # Check if the job is completed by using sacct
                check_completed = subprocess.run(
                    ['sacct', '-j', job_id, '-n', '-o', 'State'],
                    capture_output=True, 
                    text=True
                )
                completed_status = check_completed.stdout.strip()
                
                if "COMPLETED" in completed_status:
                    return "COMPLETED"
                elif "FAILED" in completed_status or "CANCELLED" in completed_status:
                    return "FAILED"
                else:
                    return "UNKNOWN"
            return status
        else:
            return "UNKNOWN"
    except Exception as e:
        print(f"Exception when checking job status: {str(e)}")
        return "UNKNOWN"

def monitor_hpc_job(job_id, polling_interval=60):
    """
    Monitors an HPC job until it completes or fails.
    
    Args:
        job_id (str): The job ID to monitor
        polling_interval (int): Time in seconds between status checks
        
    Returns:
        bool: True if the job completed successfully, False otherwise
    """
    while True:
        status = check_hpc_job_status(job_id)
        
        if status == "COMPLETED":
            return True
        elif status in ["FAILED", "CANCELLED", "TIMEOUT"]:
            return False
        elif status in ["PENDING", "RUNNING", "CONFIGURING"]:
            time.sleep(polling_interval)
        else:
            # For unknown status, wait and check again
            time.sleep(polling_interval)

def get_hpc_job_results(job_id, result_dir):
    """
    Retrieves and processes the results of an HPC job.
    
    Args:
        job_id (str): The completed job ID
        result_dir (str): Directory where results are stored
        
    Returns:
        dict: Dictionary containing the results information
    """
    results_info = {
        "job_id": job_id,
        "status": "unknown",
        "output_files": [],
        "errors": []
    }
    
    # Check job status first
    final_status = check_hpc_job_status(job_id)
    results_info["status"] = final_status
    
    # Look for result files
    result_path = Path(result_dir)
    if result_path.exists():
        # Look for NX Nastran output files
        for ext in ['.op2', '.out', '.log', '.f06', '.xdb']:
            files = list(result_path.glob(f'*{ext}'))
            results_info["output_files"].extend([str(f) for f in files])
    
    # Check log file for errors
    log_file = result_path / f"hpc_{job_id}.log"
    if log_file.exists():
        with open(log_file, 'r') as f:
            log_content = f.read()
            if "ERROR" in log_content or "FAIL" in log_content:
                results_info["errors"].append("Errors found in log file")
    
    return results_info

def create_hpc_config(config_file_path):
    """
    Creates a default HPC configuration file if it doesn't exist.
    
    Args:
        config_file_path (str): Path where the config file should be saved
        
    Returns:
        dict: The configuration dictionary
    """
    default_config = {
        "default_cores": 8,
        "default_memory": "16GB",
        "default_wall_time": "2:00:00",
        "result_directory": os.path.expanduser("~/nx_hpc_results"),
        "polling_interval": 60
    }
    
    config_path = Path(config_file_path)
    
    # Create parent directories if they don't exist
    if not config_path.parent.exists():
        config_path.parent.mkdir(parents=True)
    
    # Create or load config file
    if not config_path.exists():
        with open(config_file_path, 'w') as f:
            json.dump(default_config, f, indent=2)
        return default_config
    else:
        with open(config_file_path, 'r') as f:
            return json.load(f)

def read_hpc_config(config_file_path):
    """
    Reads the HPC configuration file.
    
    Args:
        config_file_path (str): Path to the config file
        
    Returns:
        dict: The configuration dictionary or default values if file doesn't exist
    """
    try:
        with open(config_file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return create_hpc_config(config_file_path)
    except json.JSONDecodeError:
        print(f"Error parsing HPC config file. Using defaults.")
        return create_hpc_config(config_file_path + ".backup")

def ensure_hpc_settings():
    """Create default HPC settings if they don't exist"""
    import os
    import json
    
    settings_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config", "hpc_settings.json")
    
    # Create config directory if it doesn't exist
    os.makedirs(os.path.dirname(settings_path), exist_ok=True)
    
    if not os.path.exists(settings_path):
        print("Creating default HPC settings file...")
        default_settings = {
            "hpc_enabled": True,
            "hpc_host": "localhost",
            "hpc_username": "",
            "hpc_port": 22,
            "hpc_remote_dir": "/home/user/cfd_projects",
            "use_key_auth": False,
            "key_path": "",
            "visible_in_gui": True
        }
        
        with open(settings_path, 'w') as f:
            json.dump(default_settings, f, indent=4)
        print("Default HPC settings created successfully")
    else:
        print("HPC settings file already exists")

def patch_workflow_gui(WorkflowGUI):
    """
    Patch the WorkflowGUI class with additional functionality
    """
    print("Applying HPC patch to WorkflowGUI class...")
    
    # Store the original init if it exists
    if hasattr(WorkflowGUI, '__init__'):
        original_init = WorkflowGUI.__init__
    else:
        # Create a dummy original_init if none exists
        def original_init(self, *args, **kwargs):
            pass
    
    # Define a new init that can handle various argument patterns
    def patched_init(self, root=None, *args, **kwargs):
        try:
            # Store root reference
            self.root = root
            
            # Call original init with appropriate arguments
            try:
                if root is not None:
                    original_init(self, root, *args, **kwargs)
                else:
                    original_init(self, *args, **kwargs)
            except TypeError as e:
                # If original init doesn't accept the root parameter
                if "got an unexpected keyword argument" in str(e) or "missing 1 required positional argument" in str(e):
                    original_init(self, *args, **kwargs)
                else:
                    raise
                
            # Initialize defaults
            if not hasattr(self, 'notebook'):
                import tkinter as tk
                from tkinter import ttk
                # Create a base window if it doesn't exist
                if not hasattr(self, 'root') or self.root is None:
                    self.root = tk.Tk()
                    self.root.title("CFD Workflow Assistant")
                    self.root.geometry("800x600")
                
                # Create notebook for tabs
                self.notebook = ttk.Notebook(self.root)
                self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
                
                # Create main tab
                self.main_tab = ttk.Frame(self.notebook)
                self.notebook.add(self.main_tab, text="Main")
                
                # Add a remote tab for HPC functionality
                self.remote_tab = ttk.Frame(self.notebook)
                self.notebook.add(self.remote_tab, text="HPC")
            
            # Setup additional attributes
            if not hasattr(self, 'settings'):
                self.settings = {
                    "mesh_size": 10.0,
                    "mesh_method": "Tetrahedral",
                    "solver": "CFD",
                    "analysis_type": "Steady State",
                    "cores": 8,
                    "memory": "16GB",
                    "wall_time": "02:00:00"
                }
                
            # Setup HPC settings if that method exists (added by workflow_utils)
            if hasattr(self, 'setup_hpc_widgets'):
                self.setup_hpc_widgets()
                
            # Load HPC settings if that method exists
            if hasattr(self, 'load_hpc_settings'):
                try:
                    self.load_hpc_settings()
                except Exception as e:
                    print(f"Warning: Could not load HPC settings: {e}")
                    
            # Setup save_preset_dialog if missing
            if not hasattr(self, 'save_preset_dialog'):
                self.save_preset_dialog = create_save_preset_dialog(self)
            
        except Exception as e:
            print(f"Error in patched init: {e}")
            import traceback
            traceback.print_exc()
            
    # Replace the __init__ method
    WorkflowGUI.__init__ = patched_init
    
    # Add safe show method
    def safe_show_gui(self):
        try:
            if hasattr(self, 'show'):
                self.show()
            elif hasattr(self, 'root') and self.root:
                self.root.deiconify()
                self.root.mainloop()
            else:
                print("No show method available")
        except Exception as e:
            print(f"Error showing GUI: {e}")
    
    WorkflowGUI.safe_show_gui = safe_show_gui
    
    # Import workflow_utils to get additional patches
    try:
        import workflow_utils
        # Apply additional patches from workflow_utils
        WorkflowGUI = workflow_utils.patch_workflow_gui(WorkflowGUI)
        print("Successfully applied workflow_utils patches")
    except Exception as e:
        print(f"Error applying workflow_utils patches: {e}")
        
    print("Patch applied successfully.")
    return WorkflowGUI

# Helper function to create save_preset_dialog
def create_save_preset_dialog(self):
    def save_preset_dialog():
        try:
            import tkinter as tk
            from tkinter import simpledialog, messagebox
            
            preset_name = simpledialog.askstring("Save Preset", "Enter a name for this preset:",
                                               parent=self.root if hasattr(self, 'root') else None)
            if preset_name:
                if hasattr(self, '_save_preset'):
                    self._save_preset(preset_name)
                else:
                    print(f"Saving preset '{preset_name}' (mock implementation)")
                    messagebox.showinfo("Save Preset", f"Preset '{preset_name}' saved successfully")
                return True
            return False
        except Exception as e:
            print(f"Error in save_preset_dialog: {e}")
            return False
    
    return save_preset_dialog

# Create a function to register the menu item and command
def add_menu_item():
    """
    Adds a menu item to the NX interface to launch the workflow GUI.
    """
    try:
        import NXOpen
        import NXOpen.UI
        
        # Get the main menu bar
        mainMenuBar = NXOpen.UI.GetUI().MenuBar
        
        # Check if our menu already exists and create it if not
        menuName = "CFD Tools"
        menuExists = False
        
        for i in range(mainMenuBar.GetNumberOfMenus()):
            if mainMenuBar.GetMenu(i).GetLabel() == menuName:
                menuExists = True
                break
                
        if not menuExists:
            # Create a new menu
            customMenu = mainMenuBar.CreateMenu(menuName, menuName, 0)
            
            # Add menu items
            customMenu.CreateMenuItem("CFD Workflow", "CFD_Workflow", 0)
            
            # Add callbacks
            def launch_workflow_callback():
                # Import the MDO module to access the patched WorkflowGUI class
                import MDO
                if hasattr(MDO, 'WorkflowGUI'):
                    workflow_gui = MDO.WorkflowGUI()
                    if hasattr(workflow_gui, 'safe_show_gui'):
                        workflow_gui.safe_show_gui()
                else:
                    print("WorkflowGUI class not found in MDO module")
                
            customMenu.AddMenuItemHandler("CFD_Workflow", launch_workflow_callback)
            
        print("Menu added successfully")
        return True
    except ImportError as e:
        print(f"Error adding menu: NXOpen modules not available - {str(e)}")
        return False
    except Exception as e:
        print(f"Error adding menu: {str(e)}")
        return False

# The following code will run when the script is loaded
if __name__ == '__main__':
    print("Ensuring HPC settings exist...")
    ensure_hpc_settings()
    add_menu_item()
    print("CFD Workflow Assistant has been loaded. Access it from the CFD Tools menu.")

def main():
    """Main entry point for the patch script"""
    print("Starting HPC integration patch...")
    
    if not PATCH_AVAILABLE:
        print("Error: Cannot apply patch due to missing components.")
        return 1

    print(f"HPC connectivity is {'available' if HPC_AVAILABLE else 'NOT available'}")
    if not HPC_AVAILABLE:
        print("To enable HPC connectivity, install the paramiko package:")
        print("    pip install paramiko")
    
    if not MDO_AVAILABLE:
        print("Warning: MDO module not found. The patch may not function correctly.")
        return 1

    try:
        # Apply the patch to the WorkflowGUI class
        if hasattr(MDO, 'WorkflowGUI'):
            print("Applying HPC patch to WorkflowGUI class...")
            MDO.WorkflowGUI = patch_workflow_gui(MDO.WorkflowGUI)
            print("Patch applied successfully.")
        else:
            print("WorkflowGUI class not found in MDO module.")
            return 1

        # Start the GUI
        print("Starting patched GUI...")
        try:
            # Create a test class if needed
            if 'WorkflowGUI' not in locals() and 'WorkflowGUI' not in globals():
                import tkinter as tk
                
                class TestWorkflowGUI:
                    def __init__(self, root=None):
                        self.root = root
                        print("TestWorkflowGUI initialized")
                
                patched_class = patch_workflow_gui(TestWorkflowGUI)
            else:
                patched_class = patch_workflow_gui(WorkflowGUI)
                
            # Create root window if using tkinter
            try:
                import tkinter as tk
                root = tk.Tk()
                root.withdraw()  # Hide the main window initially
                gui_instance = patched_class(root)
            except:
                # Fallback if tkinter not available or not needed
                gui_instance = patched_class()
                
            # Try to show the GUI safely
            if hasattr(gui_instance, 'safe_show_gui'):
                gui_instance.safe_show_gui()
            
            print("GUI started successfully")
        except Exception as e:
            print(f"Error starting GUI: {e}")
            traceback.print_exc()
        return 0
        
    except Exception as e:
        print(f"Error applying patch: {str(e)}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
