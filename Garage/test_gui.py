#!/usr/bin/env python3
"""
Simple GUI test script for the Intake CFD application.
This isolates the GUI functionality to help diagnose display-related issues.
"""
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
import traceback

def setup_path():
    """Set up Python path to properly find all modules"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

def test_base_gui():
    """Test basic GUI functionality"""
    print("Starting basic GUI test...")
    try:
        # Create the main window
        root = tk.Tk()
        root.title("Intake CFD GUI Test")
        root.geometry("640x480")
        
        # Add some header styling
        header_frame = tk.Frame(root, bg="#2C3E50", padx=10, pady=5)
        header_frame.pack(fill=tk.X)
        
        header_label = tk.Label(
            header_frame, 
            text="Intake CFD GUI Test", 
            font=("Segoe UI", 16, "bold"),
            fg="white",
            bg="#2C3E50"
        )
        header_label.pack(side=tk.LEFT)
        
        # Main content area
        content_frame = ttk.Frame(root, padding=20)
        content_frame.pack(fill='both', expand=True)
        
        # Create a notebook (tabbed interface)
        notebook = ttk.Notebook(content_frame)
        notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Create tabs
        tab1 = ttk.Frame(notebook)
        tab2 = ttk.Frame(notebook)
        tab3 = ttk.Frame(notebook)
        
        notebook.add(tab1, text="Workflow")
        notebook.add(tab2, text="Visualization")
        notebook.add(tab3, text="Settings")
        
        # Add content to first tab
        ttk.Label(tab1, text="Design Parameters", font=("Segoe UI", 12, "bold")).pack(anchor='w', pady=10)
        
        param_frame = ttk.Frame(tab1)
        param_frame.pack(fill='x', pady=5)
        
        ttk.Label(param_frame, text="L4:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        ttk.Entry(param_frame, width=10).grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(param_frame, text="m").grid(row=0, column=2, padx=5, pady=5, sticky='w')
        
        ttk.Label(param_frame, text="L5:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        ttk.Entry(param_frame, width=10).grid(row=1, column=1, padx=5, pady=5)
        ttk.Label(param_frame, text="m").grid(row=1, column=2, padx=5, pady=5, sticky='w')
        
        button_frame = ttk.Frame(tab1)
        button_frame.pack(pady=20)
        ttk.Button(button_frame, text="Run Workflow").pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Reset").pack(side=tk.LEFT, padx=5)
        
        # Status bar
        status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(root, textvariable=status_var, relief="sunken", anchor="w")
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Function to update status
        def update_status():
            status_var.set("GUI test successful - all components rendered correctly")
            messagebox.showinfo("Test Successful", 
                              "The GUI test was successful!\n\n"
                              "This confirms that your display environment is properly configured.")
        
        # Schedule the status update
        root.after(2000, update_status)
        
        # Start the main loop
        print("GUI initialized, starting main loop...")
        root.mainloop()
        print("GUI test completed successfully")
        
        return True
    except Exception as e:
        print(f"GUI test failed with error: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        setup_path()
        success = test_base_gui()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Fatal error: {e}")
        traceback.print_exc()
        sys.exit(1)
