"""
GUI Helper Functions - Utility functions for GUI creation and error handling
"""

import os
import sys
import traceback

def setup_logging():
    """Set up logging for the GUI application"""
    import logging
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    
    # Create logs directory if it doesn't exist
    if not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir)
        except:
            log_dir = os.path.dirname(os.path.abspath(__file__))
    
    log_file = os.path.join(log_dir, "gui.log")
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger('CFD_GUI')

def create_tkinter_gui(title="CFD Workflow Assistant", size="900x700"):
    """Create a basic Tkinter GUI"""
    try:
        import tkinter as tk
        from tkinter import ttk
        
        # Create the root window
        root = tk.Tk()
        root.title(title)
        root.geometry(size)
        
        # Add a notebook for tabs
        notebook = ttk.Notebook(root)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Add main tab
        main_tab = ttk.Frame(notebook)
        notebook.add(main_tab, text="Main")
        
        # Create a status bar
        status_frame = ttk.Frame(root)
        status_frame.pack(side='bottom', fill='x')
        
        status_label = ttk.Label(status_frame, text="Ready")
        status_label.pack(side='left', padx=5, pady=2)
        
        return root, notebook, main_tab
    except Exception as e:
        print(f"Error creating Tkinter GUI: {e}")
        traceback.print_exc()
        return None, None, None

def safely_load_module(module_name):
    """Safely import a module and return None if not found"""
    try:
        module = __import__(module_name)
        return module
    except ImportError:
        print(f"Warning: Module {module_name} not available")
        return None

def check_required_attributes(obj, required_attrs, create_missing=False, default_value=None):
    """Check if an object has required attributes and optionally create them"""
    missing = []
    
    for attr in required_attrs:
        if not hasattr(obj, attr):
            if create_missing:
                setattr(obj, attr, default_value)
                print(f"Created missing attribute: {attr}")
            else:
                missing.append(attr)
    
    return missing

def is_running_in_nx():
    """Check if the script is running within NX"""
    try:
        import NXOpen
        return True
    except ImportError:
        return False
