#!/usr/bin/env python3
"""
Simplified launcher for the Intake CFD GUI.
This provides a clean startup process with enhanced error handling.
"""
import os
import sys
import traceback
import tkinter as tk  # This import is fine, but needs to be referenced correctly
from tkinter import messagebox
import main
# Set environment variable for demo mode
os.environ["GARAGE_DEMO_MODE"] = "1"

def initialize_path():
    """Setup Python path to properly find all modules"""
    # Add current directory to path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    # Add parent directory to path
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    
    return current_dir, parent_dir

def launch_gui():
    """Launch the GUI with comprehensive error handling"""
    current_dir, parent_dir = initialize_path()
    
    print(f"Starting Intake CFD GUI from {current_dir}")
    print(f"Python version: {sys.version}")
    print(f"sys.path: {sys.path}")
    
    try:
        # First test tkinter - use the global tk module instead of trying to reference a local variable
        print("Initializing tkinter...")
        root = tk.Tk()  # Use the imported tk module
        root.withdraw()  # Hide the window until fully ready
        
        # The rest of your function remains the same...
        # ...
        # Prepare root window
        root.title("Intake CFD Optimization Suite")
        root.geometry("1280x800")
        root.minsize(800, 600)
        
        # Create GUI instance
        print("Creating GUI instance...")
        app = main.WorkflowGUI(root)
        
        # Configure any GUI patches if needed
        try:
            from Utils import workflow_utils
            if hasattr(workflow_utils, 'patch_workflow_gui'):
                print("Applying GUI patches...")
                workflow_utils.patch_workflow_gui(main.WorkflowGUI)
        except Exception as e:
            print(f"Warning: Could not apply GUI patches: {e}")
            
        # Ensure Config directory exists
        os.makedirs(os.path.join(current_dir, "Config"), exist_ok=True)
        
        # Try multiple methods to fix the HPC tab
        hpc_tab_fixed = False
        
        # Method 1: Use fix_hpc_tab_v2 if available
        if not hpc_tab_fixed:
            try:
                sys.path.insert(0, current_dir)  # Ensure current dir is first in path
                import fix_hpc_tab_v2
                fix_hpc_tab_v2.fix_hpc_tab(app)
                print("HPC tab configured with fix_hpc_tab_v2")
                hpc_tab_fixed = True
            except ImportError:
                print("Could not find fix_hpc_tab_v2 module")
            except Exception as e:
                print(f"Error with fix_hpc_tab_v2: {e}")
                traceback.print_exc()
        
        # Method 2: Use GUI.fix_hpc_gui if available
        if not hpc_tab_fixed:
            try:
                from GUI import fix_hpc_gui
                if hasattr(fix_hpc_gui, 'fix_hpc_tab'):
                    fix_hpc_gui.fix_hpc_tab(app)
                    print("HPC tab configured with GUI.fix_hpc_gui.fix_hpc_tab")
                    hpc_tab_fixed = True
            except ImportError:
                print("Could not find GUI.fix_hpc_gui module")
            except Exception as e:
                print(f"Error with GUI.fix_hpc_gui: {e}")
        
        # Method 3: Use original fix_hpc_tab if available
        if not hpc_tab_fixed:
            try:
                from fix_hpc_tab import fix_hpc_tab
                fix_hpc_tab(app)
                print("HPC tab configured with original fix_hpc_tab")
                hpc_tab_fixed = True
            except ImportError:
                print("Could not find fix_hpc_tab module")
            except Exception as e:
                print(f"Error with fix_hpc_tab: {e}")
        
        # Method 4: Last resort - create minimal HPC tab directly
        if not hpc_tab_fixed:
            try:
                print("Creating minimal HPC tab as last resort")
                # Don't redefine tkinter modules here - use the ones already imported
                # import tkinter as tk  <- This was causing the issue
                from tkinter import ttk
                
                # Check if HPC tab already exists
                hpc_tab_exists = False
                for i, tab_id in enumerate(app.notebook.tabs()):
                    if app.notebook.tab(tab_id, "text") == "HPC":
                        hpc_tab_exists = True
                        break
                
                if not hpc_tab_exists:
                    # Create HPC tab
                    app.hpc_tab = ttk.Frame(app.notebook)
                    app.notebook.add(app.hpc_tab, text="HPC")
                    
                    # Add minimal content
                    frame = ttk.Frame(app.hpc_tab, padding=20)
                    frame.pack(fill='both', expand=True)
                    
                    ttk.Label(frame, text="HPC Connection Settings", font=("Arial", 12, "bold")).pack(pady=10)
                    
                    settings_frame = ttk.LabelFrame(frame, text="Connection Details")
                    settings_frame.pack(fill='x', padx=10, pady=10)
                    
                    # Host
                    host_frame = ttk.Frame(settings_frame)
                    host_frame.pack(fill='x', padx=10, pady=5)
                    ttk.Label(host_frame, text="Host:").pack(side='left', padx=5)
                    ttk.Entry(host_frame, width=30).pack(side='left', padx=5, fill='x', expand=True)
                    
                    # Status
                    status_frame = ttk.Frame(settings_frame)
                    status_frame.pack(fill='x', padx=10, pady=10)
                    ttk.Label(status_frame, text="Status:").pack(side='left', padx=5)
                    ttk.Label(status_frame, text="Not configured").pack(side='left', padx=5)
                    
                    # Buttons
                    button_frame = ttk.Frame(settings_frame)
                    button_frame.pack(fill='x', padx=10, pady=10)
                    ttk.Button(button_frame, text="Configure HPC").pack(side='right', padx=5)
                
                hpc_tab_fixed = True
                print("Minimal HPC tab created successfully")
                
            except Exception as e:
                print(f"Failed to create minimal HPC tab: {e}")
                traceback.print_exc()
                
        # Show the main window
        print("Displaying main window...")
        root.deiconify()
        
        # Start the main event loop
        print("Starting main event loop...")
        root.mainloop()
        
        return 0
    except Exception as e:
        print(f"ERROR: {str(e)}")
        traceback.print_exc()
        
        try:
            messagebox.showerror("Launch Error", 
                            f"Failed to start the application: {str(e)}\n\n"
                            f"See console for more details.")
        except:
            pass
        
        return 1

if __name__ == "__main__":
    sys.exit(launch_gui())