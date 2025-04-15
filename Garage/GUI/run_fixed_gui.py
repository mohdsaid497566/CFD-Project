#!/usr/bin/env python3
"""
Fixed GUI Launcher
This script launches the CFD Workflow Assistant with proper initialization and error handling.
"""

import os
import sys
import tkinter as tk
import traceback

def setup_environment():
    """Set up the environment for the GUI"""
    # Add current directory to path
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    # Create necessary directories
    gui_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gui")
    config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config")
    
    os.makedirs(gui_dir, exist_ok=True)
    os.makedirs(config_dir, exist_ok=True)
    
    # Create __init__.py in gui directory if it doesn't exist
    init_file = os.path.join(gui_dir, "__init__.py")
    if not os.path.exists(init_file):
        with open(init_file, 'w') as f:
            f.write('"""GUI package for CFD Workflow Assistant"""\n')  # Fixed missing \n
            
    # Create HPC settings file if it doesn't exist
    settings_file = os.path.join(config_dir, "hpc_settings.json")
    if not os.path.exists(settings_file):
        import json
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
        with open(settings_file, 'w') as f:
            json.dump(default_settings, f, indent=4)

def create_error_window(exception, traceback_str):
    """Create an error window to display the exception"""
    error_root = tk.Tk()
    error_root.title("CFD Workflow Assistant - Error")
    error_root.geometry("800x600")
    
    frame = tk.Frame(error_root, padx=20, pady=20)
    frame.pack(fill='both', expand=True)
    
    tk.Label(frame, text="An error occurred while starting the application:", 
            font=("Arial", 12, "bold")).pack(pady=(0, 10), anchor='w')
    
    tk.Label(frame, text=str(exception), fg="red", 
            font=("Arial", 12)).pack(pady=(0, 20), anchor='w')
    
    tk.Label(frame, text="Traceback:", font=("Arial", 10, "bold")).pack(anchor='w')
    
    text = tk.Text(frame, height=20, width=90, wrap='word')
    text.pack(pady=10, fill='both', expand=True)
    text.insert('1.0', traceback_str)
    text.config(state='disabled')
    
    scrollbar = tk.Scrollbar(text)
    scrollbar.pack(side='right', fill='y')
    text.config(yscrollcommand=scrollbar.set)
    scrollbar.config(command=text.yview)
    
    tk.Label(frame, text="Please fix the above issue and restart the application.").pack(pady=10, anchor='w')
    
    btn_frame = tk.Frame(frame)
    btn_frame.pack(fill='x', pady=10)
    
    tk.Button(btn_frame, text="Exit", command=error_root.destroy).pack(side='right')
    tk.Button(btn_frame, text="Run Repair Tool", 
             command=lambda: (os.system(f"{sys.executable} {os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gui_repair.py')}"), 
                             error_root.destroy())).pack(side='right', padx=10)
    
    error_root.mainloop()

def main():
    """Main entry point"""
    try:
        # Setup environment
        setup_environment()
        
        # Import necessary modules
        from gui.workflow_gui import WorkflowGUI
        
        # Create root window
        root = tk.Tk()
        root.title("CFD Workflow Assistant")
        root.geometry("1000x700")
        
        # Initialize GUI
        app = WorkflowGUI(root)
        
        # Set up HPC tab if it exists
        if hasattr(app, 'setup_hpc_tab'):
            app.setup_hpc_tab()
        
        # Start the main loop
        root.mainloop()
        
    except Exception as e:
        # Show error dialog
        create_error_window(e, traceback.format_exc())

if __name__ == "__main__":
    main()
