#!/usr/bin/env python3
"""
Simple launcher for the Intake CFD GUI.
This helps diagnose GUI startup issues by isolating the GUI initialization.
"""
import os
import sys
import traceback

# Set environment variable for demo mode
os.environ["GARAGE_DEMO_MODE"] = "1"

def launch_gui():
    """Launch the GUI with proper error handling"""
    try:
        print("Attempting to launch Intake CFD GUI...")
        
        # Try importing tkinter first to check GUI capability
        import tkinter as tk
        print(f"Successfully imported tkinter version: {tk.TkVersion}")
        
        # Import our main module
        from main import WorkflowGUI
        
        # Create root window
        root = tk.Tk()
        root.title("Intake CFD Optimization Suite")
        root.geometry("1280x800")
        root.minsize(800, 600)
        
        # Create and initialize the GUI
        print("Initializing WorkflowGUI...")
        app = WorkflowGUI(root)
        print("GUI initialized successfully")
        
        # Start the main event loop
        print("Starting main event loop...")
        root.mainloop()
        
        return 0
    except ImportError as e:
        print(f"ERROR: Failed to import required module: {e}")
        print("This might indicate missing dependencies.")
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"ERROR: Failed to launch GUI: {e}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(launch_gui())
