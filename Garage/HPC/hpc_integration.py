#!/usr/bin/env python3
"""
HPC Integration Module for Intake CFD Project.

This module connects the HPC connector to the main GUI application.
"""

import os
import sys
import logging
import tkinter as tk
from tkinter import ttk, messagebox

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("hpc_integration")

def initialize_hpc(app):
    """
    Initialize HPC functionality in the main application.
    
    Args:
        app: The main application instance (WorkflowGUI)
    """
    try:
        # Import the HPC connector
        from Garage.Utils.workflow_utils import HPCConnector, load_hpc_settings
        
        # Load HPC settings
        hpc_settings = load_hpc_settings()
        logger.info("Loaded HPC settings")
        
        # Create the HPC tab if it doesn't exist
        if not hasattr(app, 'hpc_tab'):
            create_hpc_tab(app, hpc_settings)
            logger.info("HPC tab created")
        
        logger.info("HPC integration initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Error initializing HPC integration: {e}")
        return False

def create_hpc_tab(app, hpc_settings=None):
    """
    Create the HPC tab in the GUI.
    
    Args:
        app: The main application instance (WorkflowGUI)
        hpc_settings: Dictionary with HPC settings
    """
    # Create default settings if none provided
    if hpc_settings is None:
        from Garage.Utils.workflow_utils import load_hpc_settings
        hpc_settings = load_hpc_settings()
    
    # Create HPC tab if it doesn't exist
    if not hasattr(app, 'notebook') or app.notebook is None:
        logger.error("Cannot create HPC tab: notebook not found")
        return
    
    # Check if HPC tab already exists
    for tab_id in app.notebook.tabs():
        tab_text = app.notebook.tab(tab_id, "text")
        if tab_text == "HPC":
            logger.info("HPC tab already exists")
            return
    
    # Create HPC tab
    app.hpc_tab = ttk.Frame(app.notebook)
    app.notebook.add(app.hpc_tab, text="HPC")
    logger.info("Created HPC tab")
    
    # Connection settings section
    conn_frame = ttk.LabelFrame(app.hpc_tab, text="HPC Connection")
    conn_frame.pack(fill="x", padx=20, pady=10)
    
    # Create a grid for connection settings
    grid = ttk.Frame(conn_frame)
    grid.pack(fill="x", padx=10, pady=10)
    
    # Connection profile selector
    ttk.Label(grid, text="Connection Profile:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
    app.conn_profile = ttk.Combobox(grid)
    app.conn_profile.grid(row=0, column=1, padx=5, pady=5, sticky="w")
    ttk.Button(grid, text="Save Profile", command=lambda: save_hpc_profile(app)).grid(row=0, column=2, padx=5, pady=5)
    ttk.Button(grid, text="Delete Profile", command=lambda: delete_hpc_profile(app)).grid(row=0, column=3, padx=5, pady=5)
    
    # Host settings
    ttk.Label(grid, text="HPC Host:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
    app.hpc_host = ttk.Entry(grid, width=30)
    app.hpc_host.grid(row=1, column=1, padx=5, pady=5, sticky="w")
    app.hpc_host.insert(0, hpc_profiles.get("hpc_host", "localhost"))
    
    ttk.Label(grid, text="Username:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
    app.hpc_username = ttk.Entry(grid, width=30)
    app.hpc_username.grid(row=2, column=1, padx=5, pady=5, sticky="w")
    app.hpc_username.insert(0, hpc_profiles.get("hpc_username", ""))
    
    ttk.Label(grid, text="Port:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
    app.hpc_port = ttk.Entry(grid, width=10)
    app.hpc_port.grid(row=3, column=1, padx=5, pady=5, sticky="w")
    app.hpc_port.insert(0, str(hpc_profiles.get("hpc_port", 22)))
    
    # Authentication method
    ttk.Label(grid, text="Authentication:").grid(row=4, column=0, padx=5, pady=5, sticky="w")
    app.auth_method = tk.StringVar(value="password" if not hpc_profiles.get("use_key_auth", False) else "key")
    ttk.Radiobutton(grid, text="Password", variable=app.auth_method, value="password", 
                    command=lambda: toggle_auth_type(app)).grid(row=4, column=1, padx=5, pady=5, sticky="w")
    ttk.Radiobutton(grid, text="SSH Key", variable=app.auth_method, value="key",
                    command=lambda: toggle_auth_type(app)).grid(row=4, column=2, padx=5, pady=5, sticky="w")
    
    # Password frame
    app.password_frame = ttk.Frame(grid)
    app.password_frame.grid(row=5, column=0, columnspan=4, padx=5, pady=5, sticky="w")
    
    ttk.Label(app.password_frame, text="Password:").pack(side=tk.LEFT, padx=5)
    app.hpc_password = ttk.Entry(app.password_frame, width=30, show="*")
    app.hpc_password.pack(side=tk.LEFT, padx=5)
    
    # Key frame
    app.key_frame = ttk.Frame(grid)
    app.key_frame.grid(row=6, column=0, columnspan=4, padx=5, pady=5, sticky="w")
    
    ttk.Label(app.key_frame, text="SSH Key Path:").pack(side=tk.LEFT, padx=5)
    app.hpc_key_path = ttk.Entry(app.key_frame, width=40)
    app.hpc_key_path.pack(side=tk.LEFT, padx=(0, 5))
    app.hpc_key_path.insert(0, hpc_profiles.get("key_path", ""))
    ttk.Button(app.key_frame, text="Browse...", command=lambda: select_key_file(app)).pack(side=tk.LEFT)
    
    # Show/hide authentication frames based on initial selection
    if app.auth_method.get() == "password":
        app.key_frame.grid_remove()
    else:
        app.password_frame.grid_remove()
    
    # Remote directory
    ttk.Label(grid, text="Remote Directory:").grid(row=7, column=0, padx=5, pady=5, sticky="w")
    app.remote_dir = ttk.Entry(grid, width=40)
    app.remote_dir.grid(row=7, column=1, columnspan=3, padx=5, pady=5, sticky="w")
    app.remote_dir.insert(0, hpc_profiles.get("hpc_remote_dir", "/home/user/cfd_projects"))
    
    # Connection actions
    btn_frame = ttk.Frame(conn_frame)
    btn_frame.pack(fill="x", padx=10, pady=10)
    ttk.Button(btn_frame, text="Test Connection", command=lambda: test_hpc_connection(app)).pack(side="left", padx=5)
    ttk.Button(btn_frame, text="Connect", command=lambda: connect_to_hpc(app)).pack(side="left", padx=5)
    ttk.Button(btn_frame, text="Disconnect", command=lambda: disconnect_from_hpc(app)).pack(side="left", padx=5)
    
    # Connection status indicator
    app.conn_status_var = tk.StringVar(value="Not Connected")
    app.conn_status = ttk.Label(btn_frame, textvariable=app.conn_status_var, 
                              foreground="red", font=("Arial", 10, "bold"))
    app.conn_status.pack(side="right", padx=10)
    
    # Job management section
    job_frame = ttk.LabelFrame(app.hpc_tab, text="HPC Job Management")
    job_frame.pack(fill="both", expand=True, padx=20, pady=10)
    
    # Create job list with scrollbar
    job_list_frame = ttk.Frame(job_frame)
    job_list_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    # Create Treeview for job list
    columns = ("id", "name", "status", "queue", "nodes", "time")
    app.job_tree = ttk.Treeview(job_list_frame, columns=columns, show="headings")
    
    # Define column headings
    app.job_tree.heading("id", text="Job ID")
    app.job_tree.heading("name", text="Name")
    app.job_tree.heading("status", text="Status")
    app.job_tree.heading("queue", text="Queue")
    app.job_tree.heading("nodes", text="Nodes")
    app.job_tree.heading("time", text="Run Time")
    
    # Configure column widths
    app.job_tree.column("id", width=80)
    app.job_tree.column("name", width=150)
    app.job_tree.column("status", width=80)
    app.job_tree.column("queue", width=80)
    app.job_tree.column("nodes", width=60)
    app.job_tree.column("time", width=80)
    
    # Add scrollbar
    scrollbar = ttk.Scrollbar(job_list_frame, orient="vertical", command=app.job_tree.yview)
    app.job_tree.configure(yscrollcommand=scrollbar.set)
    
    # Pack tree and scrollbar
    app.job_tree.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    # Job control buttons
    job_control_frame = ttk.Frame(job_frame)
    job_control_frame.pack(fill="x", padx=10, pady=10)
    
    ttk.Button(job_control_frame, text="Refresh", command=lambda: refresh_job_list(app)).pack(side="left", padx=5)
    ttk.Button(job_control_frame, text="Submit Job", command=lambda: submit_job(app)).pack(side="left", padx=5)
    ttk.Button(job_control_frame, text="Cancel Job", command=lambda: cancel_job(app)).pack(side="left", padx=5)
    ttk.Button(job_control_frame, text="Job Details", command=lambda: show_job_details(app)).pack(side="left", padx=5)
    ttk.Button(job_control_frame, text="Download Results", command=lambda: download_results(app)).pack(side="left", padx=5)
    
    # Load saved HPC profiles
    load_hpc_profiles(app)

def toggle_auth_type(app):
    """
    Toggle between password and key authentication display
    
    Args:
        app: The main application instance
    """
    if app.auth_method.get() == "password":
        app.password_frame.grid()
        app.key_frame.grid_remove()
    else:
        app.password_frame.grid_remove()
        app.key_frame.grid()

def select_key_file(app):
    """
    Open file dialog to select SSH key file
    
    Args:
        app: The main application instance
    """
    from tkinter import filedialog
    key_path = filedialog.askopenfilename(
        title="Select SSH Key",
        filetypes=[("Key Files", "*.pem *.key"), ("All Files", "*.*")]
    )
    if key_path:
        app.hpc_key_path.delete(0, tk.END)
        app.hpc_key_path.insert(0, key_path)

def test_hpc_connection(app):
    """
    Test connection to HPC system
    
    Args:
        app: The main application instance
    """
    import threading
    from Garage.Utils.workflow_utils import HPCConnector

    # Get connection info
    config = get_hpc_config(app)
    
    # Update status
    app.update_status("Testing connection to HPC system...", show_progress=True)
    
    # Run test in a separate thread
    def test_connection_thread():
        try:
            # Test connection using HPC connector
            from Garage.HPC.hpc_connector import test_connection
            success, message = test_connection(config)
            
            # Update UI from the main thread
            app.root.after(0, lambda: update_connection_result(app, success, message))
        except Exception as e:
            logger.error(f"Error testing connection: {e}")
            app.root.after(0, lambda: update_connection_result(app, False, str(e)))
    
    threading.Thread(target=test_connection_thread, daemon=True).start()

def update_connection_result(app, success, message):
    """
    Update the UI with connection test results
    
    Args:
        app: The main application instance
        success: Whether the connection was successful
        message: Connection message
    """
    app.update_status("Connection test completed", show_progress=False)
    
    if success:
        app.conn_status_var.set("Connected")
        app.conn_status.configure(foreground="green")
        messagebox.showinfo("Connection Successful", message)
    else:
        app.conn_status_var.set(f"Failed: {message}")
        app.conn_status.configure(foreground="red")
        messagebox.showerror("Connection Failed", message)

def connect_to_hpc(app):
    """
    Connect to HPC system and initialize connector
    
    Args:
        app: The main application instance
    """
    import threading
    from Garage.Utils.workflow_utils import HPCConnector

    # Get connection info
    config = get_hpc_config(app)
    
    # Update status
    app.update_status("Connecting to HPC system...", show_progress=True)
    
    # Connect in a separate thread
    def connect_thread():
        try:
            # Initialize connector
            hpc_connector = HPCConnector(config)
            success, message = hpc_connector.connect()
            
            # Update UI from the main thread
            if success:
                # Store connector in app
                app.hpc_connector = hpc_connector
                
                # Update UI
                app.root.after(0, lambda: update_connection_result(app, True, message))
                
                # Refresh job list
                app.root.after(100, lambda: refresh_job_list(app))
            else:
                app.root.after(0, lambda: update_connection_result(app, False, message))
        except Exception as e:
            logger.error(f"Error connecting to HPC: {e}")
            app.root.after(0, lambda: update_connection_result(app, False, str(e)))
    
    threading.Thread(target=connect_thread, daemon=True).start()

def disconnect_from_hpc(app):
    """
    Disconnect from HPC system
    
    Args:
        app: The main application instance
    """
    if hasattr(app, 'hpc_connector') and app.hpc_connector:
        try:
            # First check if connection is already closed
            if not app.hpc_connector.connected or not app.hpc_connector.ssh_client:
                app.conn_status_var.set("Not Connected")
                app.conn_status.configure(foreground="red")
                app.update_status("Not connected to HPC system")
                delattr(app, 'hpc_connector')
                return
                
            # Try to disconnect
            app.hpc_connector.disconnect()
            app.conn_status_var.set("Not Connected")
            app.conn_status.configure(foreground="red")
            app.update_status("Disconnected from HPC system")
            
            # Clear job list
            for item in app.job_tree.get_children():
                app.job_tree.delete(item)
                
            # Delete connector
            delattr(app, 'hpc_connector')
        except Exception as e:
            logger.error(f"Error disconnecting: {e}")
            app.update_status(f"Error disconnecting: {e}")
            
            # Force cleanup even if disconnection failed
            app.conn_status_var.set("Not Connected")
            app.conn_status.configure(foreground="red")
            
            # Attempt to clean up resources in case of error
            try:
                if hasattr(app.hpc_connector, 'ssh_client') and app.hpc_connector.ssh_client:
                    app.hpc_connector.ssh_client.close()
                if hasattr(app.hpc_connector, 'sftp_client') and app.hpc_connector.sftp_client:
                    app.hpc_connector.sftp_client.close()
            except:
                pass
            
            # Delete connector even if there was an error
            if hasattr(app, 'hpc_connector'):
                delattr(app, 'hpc_connector')
    else:
        app.conn_status_var.set("Not Connected")
        app.conn_status.configure(foreground="red")
        app.update_status("Not connected to HPC system")

def get_hpc_config(app):
    """
    Get HPC configuration from UI
    
    Args:
        app: The main application instance
        
    Returns:
        dict: HPC configuration
    """
    config = {
        "hostname": app.hpc_host.get(),
        "username": app.hpc_username.get(),
        "port": int(app.hpc_port.get()),
        "use_key": app.auth_method.get() == "key",
        "remote_dir": app.remote_dir.get()
    }
    
    # Add authentication
    if config["use_key"]:
        config["key_path"] = app.hpc_key_path.get()
    else:
        config["password"] = app.hpc_password.get() if hasattr(app, 'hpc_password') else ""
    
    return config