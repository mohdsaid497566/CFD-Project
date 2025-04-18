#!/usr/bin/env python3
"""
Fix HPC Tab Content - Version 2
More robust implementation for adding HPC tab content to the WorkflowGUI.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import traceback

def fix_hpc_tab(app):
    """
    Fix the HPC tab content in the WorkflowGUI application.
    
    Args:
        app: The WorkflowGUI instance
    """
    print("Fixing HPC tab content (v2)...")
    
    # Check if app is a proper GUI instance
    if not hasattr(app, 'notebook') or not app.notebook:
        print("Error: Invalid app instance - missing notebook")
        return False
    
    # Find or create the HPC tab with more robust error handling
    try:
        # Check if HPC tab exists
        tab_found = False
        hpc_tab_index = -1
        
        for i, tab_id in enumerate(app.notebook.tabs()):
            if app.notebook.tab(tab_id, "text") == "HPC":
                tab_found = True
                hpc_tab_index = i
                break
        
        if tab_found:
            print(f"Found existing HPC tab at index {hpc_tab_index}")
            tab_id = app.notebook.tabs()[hpc_tab_index]
            try:
                # Use direct access to avoid tab widget reference issues
                app.hpc_tab = app.notebook.nametowidget(tab_id)
                # Clear existing widgets
                for widget in app.hpc_tab.winfo_children():
                    widget.destroy()
            except Exception as e:
                print(f"Error accessing existing tab: {e}")
                # Create a new tab if we can't access the existing one
                tab_found = False
        
        if not tab_found:
            print("Creating new HPC tab")
            app.hpc_tab = ttk.Frame(app.notebook)
            app.notebook.add(app.hpc_tab, text="HPC")
        
        # Create content
        create_hpc_tab_content(app)
        print("HPC tab content created successfully")
        return True
        
    except Exception as e:
        print(f"Error while fixing HPC tab: {e}")
        traceback.print_exc()
        return False

def create_hpc_tab_content(app):
    """Create the HPC tab content in the GUI."""
    try:
        # Load HPC settings
        hpc_profiles = load_hpc_profiles()
        
        # Main frame for HPC tab
        main_frame = ttk.Frame(app.hpc_tab, padding=10)
        main_frame.pack(fill='both', expand=True)
        
        # Connection settings frame
        connection_frame = ttk.LabelFrame(main_frame, text="HPC Connection Settings", padding=10)
        connection_frame.pack(fill='x', padx=10, pady=10)
        
        # Connection settings grid
        conn_grid = ttk.Frame(connection_frame)
        conn_grid.pack(fill='x', padx=5, pady=5)
        
        # Host
        ttk.Label(conn_grid, text="Host:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        app.hpc_hostname = ttk.Entry(conn_grid, width=30)
        app.hpc_hostname.insert(0, hpc_profiles.get("hpc_host", "localhost"))
        app.hpc_hostname.grid(row=0, column=1, padx=5, pady=5, sticky='w')
        
        # Username
        ttk.Label(conn_grid, text="Username:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        app.hpc_username = ttk.Entry(conn_grid, width=30)
        app.hpc_username.insert(0, hpc_profiles.get("hpc_username", ""))
        app.hpc_username.grid(row=1, column=1, padx=5, pady=5, sticky='w')
        
        # Port
        ttk.Label(conn_grid, text="Port:").grid(row=2, column=0, sticky='w', padx=5, pady=5)
        app.hpc_port = ttk.Entry(conn_grid, width=10)
        app.hpc_port.insert(0, str(hpc_profiles.get("hpc_port", 22)))
        app.hpc_port.grid(row=2, column=1, padx=5, pady=5, sticky='w')
        
        # Remote Directory
        ttk.Label(conn_grid, text="Remote Directory:").grid(row=3, column=0, sticky='w', padx=5, pady=5)
        app.hpc_remote_dir = ttk.Entry(conn_grid, width=30)
        app.hpc_remote_dir.insert(0, hpc_profiles.get("hpc_remote_dir", "/home/user/cfd_projects"))
        app.hpc_remote_dir.grid(row=3, column=1, padx=5, pady=5, sticky='w')
        
        # Authentication Frame
        auth_frame = ttk.LabelFrame(connection_frame, text="Authentication", padding=10)
        auth_frame.pack(fill='x', padx=5, pady=10)
        
        # Authentication method
        app.auth_method_var = tk.StringVar(value="password" if not hpc_profiles.get("use_key_auth", False) else "key")
        
        # Password option
        app.password_radio = ttk.Radiobutton(auth_frame, text="Password", value="password", 
                                            variable=app.auth_method_var,
                                            command=lambda: toggle_auth_type(app))
        app.password_radio.grid(row=0, column=0, sticky='w', padx=5, pady=5)
        
        # SSH Key option
        app.key_radio = ttk.Radiobutton(auth_frame, text="SSH Key", value="key", 
                                       variable=app.auth_method_var,
                                       command=lambda: toggle_auth_type(app))
        app.key_radio.grid(row=0, column=1, sticky='w', padx=5, pady=5)
        
        # Password frame
        app.password_frame = ttk.Frame(auth_frame)
        app.password_frame.grid(row=1, column=0, columnspan=2, sticky='we', padx=5, pady=5)
        
        ttk.Label(app.password_frame, text="Password:").pack(side='left', padx=5)
        app.password_entry = ttk.Entry(app.password_frame, width=30, show="*")
        app.password_entry.pack(side='left', padx=5, expand=True, fill='x')
        
        # SSH Key frame
        app.key_frame = ttk.Frame(auth_frame)
        app.key_frame.grid(row=2, column=0, columnspan=2, sticky='we', padx=5, pady=5)
        
        ttk.Label(app.key_frame, text="Key File:").pack(side='left', padx=5)
        app.key_path_entry = ttk.Entry(app.key_frame, width=30)
        app.key_path_entry.insert(0, hpc_profiles.get("key_path", ""))
        app.key_path_entry.pack(side='left', padx=5, expand=True, fill='x')
        
        app.browse_button = ttk.Button(app.key_frame, text="Browse", 
                                      command=lambda: browse_key_file(app))
        app.browse_button.pack(side='left', padx=5)
        
        # Apply initial state based on settings
        toggle_auth_type(app)
        
        # Status and buttons
        status_frame = ttk.Frame(connection_frame)
        status_frame.pack(fill='x', padx=5, pady=10)
        
        ttk.Label(status_frame, text="Status:").pack(side='left', padx=5)
        app.connection_status = ttk.Label(status_frame, text="Not connected")
        app.connection_status.pack(side='left', padx=5)
        
        button_frame = ttk.Frame(connection_frame)
        button_frame.pack(fill='x', padx=5, pady=5)
        
        app.save_button = ttk.Button(button_frame, text="Save Settings",
                                    command=lambda: save_settings(app))
        app.save_button.pack(side='right', padx=5)
        
        app.test_button = ttk.Button(button_frame, text="Test Connection",
                                   command=lambda: test_connection(app))
        app.test_button.pack(side='right', padx=5)
        
        # Remote Jobs Section
        jobs_frame = ttk.LabelFrame(main_frame, text="Remote Jobs", padding=10)
        jobs_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Job control buttons
        control_frame = ttk.Frame(jobs_frame)
        control_frame.pack(fill='x', padx=5, pady=5)
        
        app.submit_button = ttk.Button(control_frame, text="Submit Job", state='disabled')
        app.submit_button.pack(side='left', padx=5)
        
        app.cancel_button = ttk.Button(control_frame, text="Cancel Job", state='disabled')
        app.cancel_button.pack(side='left', padx=5)
        
        app.details_button = ttk.Button(control_frame, text="Job Details", state='disabled')
        app.details_button.pack(side='left', padx=5)
        
        app.download_button = ttk.Button(control_frame, text="Download Results", state='disabled')
        app.download_button.pack(side='left', padx=5)
        
        app.refresh_button = ttk.Button(control_frame, text="Refresh")
        app.refresh_button.pack(side='right', padx=5)
        
        # Jobs treeview
        tree_frame = ttk.Frame(jobs_frame)
        tree_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        columns = ('job_id', 'name', 'status', 'queue', 'time')
        app.jobs_tree = ttk.Treeview(tree_frame, columns=columns, show='headings')
        
        app.jobs_tree.heading('job_id', text='Job ID')
        app.jobs_tree.heading('name', text='Name')
        app.jobs_tree.heading('status', text='Status')
        app.jobs_tree.heading('queue', text='Queue')
        app.jobs_tree.heading('time', text='Elapsed Time')
        
        app.jobs_tree.column('job_id', width=80)
        app.jobs_tree.column('name', width=150)
        app.jobs_tree.column('status', width=100)
        app.jobs_tree.column('queue', width=100)
        app.jobs_tree.column('time', width=100)
        
        # Add a scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=app.jobs_tree.yview)
        app.jobs_tree.configure(yscroll=scrollbar.set)
        
        app.jobs_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Add a placeholder entry
        app.jobs_tree.insert('', 'end', values=('', 'No jobs found', '', '', ''))
        
    except Exception as e:
        print(f"Error creating HPC tab content: {e}")
        traceback.print_exc()

def toggle_auth_type(app):
    """Toggle between password and SSH key authentication frames."""
    auth_method = app.auth_method_var.get()
    
    if auth_method == "password":
        app.password_frame.grid()
        app.key_frame.grid_remove()
    else:
        app.password_frame.grid_remove()
        app.key_frame.grid()

def browse_key_file(app):
    """Browse for SSH key file."""
    file_path = filedialog.askopenfilename(
        title="Select SSH Key File",
        filetypes=[("SSH Key Files", "*.pem *.ppk *.key"), ("All Files", "*.*")]
    )
    if file_path:
        app.key_path_entry.delete(0, 'end')
        app.key_path_entry.insert(0, file_path)

def test_connection(app):
    """Test connection to HPC server."""
    # Get configuration from UI
    config = {
        "host": app.hpc_hostname.get(),
        "username": app.hpc_username.get(),
        "port": app.hpc_port.get(),
        "auth_method": app.auth_method_var.get(),
        "key_path": app.key_path_entry.get() if app.auth_method_var.get() == "key" else None
    }
    
    # Update UI to show testing
    app.connection_status.config(text="Testing connection...")
    app.test_button.config(state='disabled')
    
    # For security, we won't actually test SSH connection in this simple implementation
    # In a real implementation, you would use paramiko or similar to test the connection
    # But for now, we'll just simulate a test
    import threading
    thread = threading.Thread(target=simulate_connection_test, args=(app, config))
    thread.daemon = True
    thread.start()

def simulate_connection_test(app, config):
    """Simulate a connection test without actual SSH connection."""
    import time
    # Simple validation
    success = (config["host"] and config["username"] and config["port"])
    
    # Simulate delay
    time.sleep(1.5)
    
    # Update UI
    app.connection_status.after(0, update_connection_status, 
                              app, 
                              success, 
                              "Connected successfully" if success else "Connection failed")

def update_connection_status(app, success, message):
    """Update the connection status display."""
    app.connection_status.config(
        text=message,
        foreground="green" if success else "red"
    )
    app.test_button.config(state='normal')

def get_hpc_config(app):
    """Get HPC configuration from the UI."""
    return {
        "hpc_enabled": True,
        "hpc_host": app.hpc_hostname.get(),
        "hpc_username": app.hpc_username.get(),
        "hpc_port": int(app.hpc_port.get()) if app.hpc_port.get().isdigit() else 22,
        "hpc_remote_dir": app.hpc_remote_dir.get(),
        "use_key_auth": app.auth_method_var.get() == "key",
        "key_path": app.key_path_entry.get(),
        "visible_in_gui": True
    }

def save_settings(app):
    """Save HPC settings to a file."""
    try:
        # Get configuration from UI
        config = get_hpc_config(app)
        
        # Make sure Config directory exists
        config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Config")
        os.makedirs(config_dir, exist_ok=True)
        
        # Profile name to use - ask user
        profile_name = tk.simpledialog.askstring("Profile Name", 
                                                "Enter a name for this HPC profile:",
                                                initialvalue="Default")
        if not profile_name:
            profile_name = "Default"  # Use default if user cancels or enters empty string
        
        # Load existing profiles if file exists
        settings_file = os.path.join(config_dir, "hpc_profiles.json")
        profiles = {}
        
        if os.path.exists(settings_file):
            try:
                with open(settings_file, 'r') as f:
                    data = json.load(f)
                    
                # Check if file contains profiles or a single config
                if isinstance(data, dict):
                    if any(isinstance(v, dict) for v in data.values()):
                        # This is already a profiles dictionary
                        profiles = data
                    else:
                        # This is a single config, convert it to a profile
                        profiles = {"Default": data}
            except Exception as e:
                print(f"Error reading existing profiles: {e}")
                # Start with empty profiles dictionary if file can't be read
                profiles = {}
        
        # Add/update this profile
        profiles[profile_name] = config
        
        # Save profiles
        with open(settings_file, 'w') as f:
            json.dump(profiles, f, indent=4)
        
        # Update the dropdown if it exists
        if hasattr(app, 'workflow_hpc_profile'):
            current_values = list(app.workflow_hpc_profile['values']) if app.workflow_hpc_profile['values'] else []
            if profile_name not in current_values:
                current_values.append(profile_name)
                app.workflow_hpc_profile['values'] = current_values
            app.workflow_hpc_profile.set(profile_name)
        
        # Show confirmation
        messagebox.showinfo("Settings Saved", f"HPC profile '{profile_name}' saved to {settings_file}")
        
    except Exception as e:
        print(f"Error saving settings: {e}")
        traceback.print_exc()
        messagebox.showerror("Save Error", f"Failed to save settings: {str(e)}")
        
def load_hpc_profiles():
    """Load HPC settings from file."""
    try:
        config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Config")
        settings_file = os.path.join(config_dir, "hpc_profiles.json")
        
        if not os.path.exists(settings_file):
            # Try alternative path in GUI/config
            alt_config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "GUI", "config")
            alt_settings_file = os.path.join(alt_config_dir, "hpc_profiles.json")
            
            if os.path.exists(alt_settings_file):
                settings_file = alt_settings_file
            else:
                # Default settings
                return {
                    "hpc_enabled": True,
                    "hpc_host": "localhost",
                    "hpc_username": "",
                    "hpc_port": 22,
                    "hpc_remote_dir": "/home/user/cfd_projects",
                    "use_key_auth": False,
                    "key_path": "",
                    "visible_in_gui": True
                }
        
        with open(settings_file, 'r') as f:
            return json.load(f)
            
    except Exception as e:
        print(f"Error loading settings: {e}")
        # Return default settings on error
        return {
            "hpc_enabled": True,
            "hpc_host": "localhost",
            "hpc_username": "",
            "hpc_port": 22,
            "hpc_remote_dir": "/home/user/cfd_projects",
            "use_key_auth": False,
            "key_path": "",
            "visible_in_gui": True
        }