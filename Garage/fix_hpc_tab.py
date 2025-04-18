#!/usr/bin/env python3
"""
Fix HPC Tab Content - Adds HPC tab content to the WorkflowGUI.
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
    print("Fixing HPC tab content...")
    
    # Check if app is a proper GUI instance
    if not hasattr(app, 'notebook') or not app.notebook:
        print("Error: Invalid app instance - missing notebook")
        return False
    
    # Check if HPC tab exists
    hpc_tab_exists = False
    hpc_tab_index = -1
    
    for i, tab_id in enumerate(app.notebook.tabs()):
        if app.notebook.tab(tab_id, "text") == "HPC":
            hpc_tab_exists = True
            hpc_tab_index = i
            break
    
    if not hpc_tab_exists:
        print("HPC tab doesn't exist. Creating new HPC tab...")
        app.hpc_tab = ttk.Frame(app.notebook)
        app.notebook.add(app.hpc_tab, text="HPC")
    else:
        # Get the HPC tab widget
        app.hpc_tab = app.notebook.children[app.notebook.tabs()[hpc_tab_index].replace('.', '')]
        
        # Clear previous content
        for widget in app.hpc_tab.winfo_children():
            widget.destroy()
    
    # Create content in the HPC tab
    create_hpc_tab_content(app)
    
    print("HPC tab content fixed successfully")
    return True

def create_hpc_tab_content(app):
    """Create the HPC tab content in the GUI."""
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
    app.hpc_hostname.grid(row=0, column=1, padx=5, pady=5, sticky='w')
    app.hpc_hostname.insert(0, hpc_profiles.get("hpc_host", "localhost"))
    
    # Username
    ttk.Label(conn_grid, text="Username:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
    app.hpc_username = ttk.Entry(conn_grid, width=30)
    app.hpc_username.grid(row=1, column=1, padx=5, pady=5, sticky='w')
    app.hpc_username.insert(0, hpc_profiles.get("hpc_username", ""))
    
    # Port
    ttk.Label(conn_grid, text="Port:").grid(row=2, column=0, sticky='w', padx=5, pady=5)
    app.hpc_port = ttk.Entry(conn_grid, width=10)
    app.hpc_port.grid(row=2, column=1, padx=5, pady=5, sticky='w')
    app.hpc_port.insert(0, str(hpc_profiles.get("hpc_port", 22)))
    
    # Remote directory
    ttk.Label(conn_grid, text="Remote Directory:").grid(row=3, column=0, sticky='w', padx=5, pady=5)
    app.hpc_remote_dir = ttk.Entry(conn_grid, width=30)
    app.hpc_remote_dir.grid(row=3, column=1, padx=5, pady=5, sticky='w')
    app.hpc_remote_dir.insert(0, hpc_profiles.get("hpc_remote_dir", "/home/user/cfd_projects"))
    
    # Authentication frame
    auth_frame = ttk.LabelFrame(connection_frame, text="Authentication", padding=10)
    auth_frame.pack(fill='x', padx=5, pady=5)
    
    # Authentication method
    app.auth_type = tk.StringVar(value="password" if not hpc_profiles.get("use_key_auth", False) else "key")
    ttk.Radiobutton(auth_frame, text="Password", variable=app.auth_type, 
                  value="password", command=lambda: toggle_auth_type(app)).pack(anchor='w')
    ttk.Radiobutton(auth_frame, text="SSH Key", variable=app.auth_type,
                  value="key", command=lambda: toggle_auth_type(app)).pack(anchor='w')
    
    # Password frame
    app.password_frame = ttk.Frame(auth_frame)
    app.password_frame.pack(fill='x', pady=5)
    
    ttk.Label(app.password_frame, text="Password:").pack(side='left')
    app.hpc_password = ttk.Entry(app.password_frame, show="*")
    app.hpc_password.pack(side='left', padx=5, fill='x', expand=True)
    
    # SSH Key frame
    app.key_frame = ttk.Frame(auth_frame)
    app.key_frame.pack(fill='x', pady=5)
    
    ttk.Label(app.key_frame, text="Key File:").pack(side='left')
    app.hpc_key_path = ttk.Entry(app.key_frame)
    app.hpc_key_path.pack(side='left', padx=5, fill='x', expand=True)
    app.hpc_key_path.insert(0, hpc_profiles.get("key_path", ""))
    
    ttk.Button(app.key_frame, text="Browse...",
             command=lambda: browse_key_file(app)).pack(side='right')
    
    # Button frame
    button_frame = ttk.Frame(connection_frame)
    button_frame.pack(fill='x', pady=10)
    
    # Connection status
    app.connection_status_var = tk.StringVar(value="Status: Not connected")
    app.connection_status_label = ttk.Label(button_frame, textvariable=app.connection_status_var)
    app.connection_status_label.pack(side='left', padx=5)
    
    # Test connection button
    app.test_connection_button = ttk.Button(button_frame, text="Test Connection",
                                          command=lambda: test_connection(app))
    app.test_connection_button.pack(side='right', padx=5)
    
    # Save settings button
    ttk.Button(button_frame, text="Save Settings",
             command=lambda: save_settings(app)).pack(side='right', padx=5)
    
    # Jobs management section
    jobs_frame = ttk.LabelFrame(main_frame, text="Remote Jobs", padding=10)
    jobs_frame.pack(fill='both', expand=True, padx=10, pady=10)
    
    # Jobs toolbar
    toolbar_frame = ttk.Frame(jobs_frame)
    toolbar_frame.pack(fill='x', pady=5)
    
    ttk.Button(toolbar_frame, text="Submit Job",
             command=lambda: submit_job(app)).pack(side='left', padx=5)
    
    ttk.Button(toolbar_frame, text="Cancel Job",
             command=lambda: cancel_job(app)).pack(side='left', padx=5)
    
    ttk.Button(toolbar_frame, text="Job Details",
             command=lambda: show_job_details(app)).pack(side='left', padx=5)
    
    ttk.Button(toolbar_frame, text="Download Results",
             command=lambda: download_results(app)).pack(side='left', padx=5)
    
    app.refresh_jobs_button = ttk.Button(toolbar_frame, text="Refresh",
                                       command=lambda: refresh_jobs(app))
    app.refresh_jobs_button.pack(side='right', padx=5)
    
    # Jobs treeview
    tree_frame = ttk.Frame(jobs_frame)
    tree_frame.pack(fill='both', expand=True, pady=5)
    
    columns = ('id', 'name', 'status', 'queue', 'time')
    app.jobs_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', selectmode='browse')
    
    # Define column headings
    app.jobs_tree.heading('id', text='Job ID')
    app.jobs_tree.heading('name', text='Name')
    app.jobs_tree.heading('status', text='Status')
    app.jobs_tree.heading('queue', text='Queue')
    app.jobs_tree.heading('time', text='Elapsed Time')
    
    # Define column widths
    app.jobs_tree.column('id', width=80)
    app.jobs_tree.column('name', width=150)
    app.jobs_tree.column('status', width=100)
    app.jobs_tree.column('queue', width=100)
    app.jobs_tree.column('time', width=120)
    
    # Add scrollbar
    scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=app.jobs_tree.yview)
    app.jobs_tree.configure(yscroll=scrollbar.set)
    
    # Pack tree and scrollbar
    app.jobs_tree.pack(side='left', fill='both', expand=True)
    scrollbar.pack(side='right', fill='y')
    
    # Initialize empty jobs list
    app.jobs_tree.insert('', 'end', values=('', 'No jobs found', '', '', ''))
    
    # Add a binding for selection
    app.jobs_tree.bind('<<TreeviewSelect>>', lambda e: on_job_select(app))
    
    # Use the correct authentication frame
    toggle_auth_type(app)

def toggle_auth_type(app):
    """Toggle between password and SSH key authentication frames."""
    if app.auth_type.get() == "password":
        app.password_frame.pack(fill='x', pady=5)
        app.key_frame.pack_forget()
    else:
        app.key_frame.pack(fill='x', pady=5)
        app.password_frame.pack_forget()

def browse_key_file(app):
    """Browse for SSH key file."""
    file_path = filedialog.askopenfilename(
        title="Select SSH Key File",
        filetypes=[("All files", "*.*")]
    )
    if file_path:
        app.hpc_key_path.delete(0, tk.END)
        app.hpc_key_path.insert(0, file_path)

def test_connection(app):
    """Test connection to HPC server."""
    app.connection_status_var.set("Status: Testing...")
    app.connection_status_label.config(foreground="orange")
    app.test_connection_button.config(state=tk.DISABLED)
    
    # Create configuration
    config = get_hpc_config(app)
    
    # Start test in a thread
    import threading
    thread = threading.Thread(target=lambda: test_connection_thread(app, config), daemon=True)
    thread.start()

def test_connection_thread(app, config):
    """Test connection in a background thread."""
    try:
        # Check if paramiko is available
        try:
            import paramiko
        except ImportError:
            app.root.after(100, lambda: update_connection_status(
                app, False, "Error: paramiko module not installed"))
            return
            
        # Connect to the server
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        connect_args = {
            'hostname': config.get('hostname', 'localhost'),
            'port': int(config.get('port', 22)),
            'username': config.get('username', '')
        }
        
        # Add auth method
        if config.get('use_key', False):
            key_path = config.get('key_path', '')
            if not key_path:
                app.root.after(100, lambda: update_connection_status(
                    app, False, "Error: SSH key path not specified"))
                return
                
            try:
                connect_args['key_filename'] = key_path
            except Exception as e:
                app.root.after(100, lambda: update_connection_status(
                    app, False, f"Error with key file: {str(e)}"))
                return
        else:
            connect_args['password'] = config.get('password', '')
        
        # Attempt connection
        client.connect(**connect_args, timeout=10)
        
        # Execute a simple command
        stdin, stdout, stderr = client.exec_command('hostname')
        hostname = stdout.read().decode().strip()
        
        # Close connection
        client.close()
        
        # Update UI in main thread
        app.root.after(100, lambda: update_connection_status(
            app, True, f"Connected successfully to {hostname}"))
            
    except Exception as e:
        # Update UI in main thread
        app.root.after(100, lambda: update_connection_status(
            app, False, f"Connection failed: {str(e)}"))

def update_connection_status(app, success, message):
    """Update the connection status display."""
    if success:
        app.connection_status_var.set(f"Status: {message}")
        app.connection_status_label.config(foreground="green")
    else:
        app.connection_status_var.set(f"Status: {message}")
        app.connection_status_label.config(foreground="red")
    
    app.test_connection_button.config(state=tk.NORMAL)

def get_hpc_config(app):
    """Get HPC configuration from the UI."""
    config = {
        'hostname': app.hpc_hostname.get(),
        'username': app.hpc_username.get(),
        'port': app.hpc_port.get(),
        'remote_dir': app.hpc_remote_dir.get(),
        'use_key': app.auth_type.get() == "key"
    }
    
    if app.auth_type.get() == "key":
        config['key_path'] = app.hpc_key_path.get()
    else:
        config['password'] = app.hpc_password.get()
        
    return config

def save_settings(app):
    """Save HPC settings to a file."""
    config = get_hpc_config(app)
    
    # Don't save passwords to file
    if 'password' in config:
        del config['password']
    
    # Convert to standard format
    settings = {
        "hpc_enabled": True,
        "hpc_host": config.get('hostname', 'localhost'),
        "hpc_username": config.get('username', ''),
        "hpc_port": int(config.get('port', 22)),
        "hpc_remote_dir": config.get('remote_dir', '/home/user/cfd_projects'),
        "use_key_auth": config.get('use_key', False),
        "key_path": config.get('key_path', ''),
        "visible_in_gui": True
    }
    
    # Save to Config directory
    config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Config")
    os.makedirs(config_dir, exist_ok=True)
    
    settings_path = os.path.join(config_dir, "hpc_profiles.json")
    
    try:
        with open(settings_path, 'w') as f:
            json.dump(settings, f, indent=4)
        messagebox.showinfo("Settings Saved", "HPC settings saved successfully.")
    except Exception as e:
        messagebox.showerror("Save Error", f"Failed to save settings: {str(e)}")

def load_hpc_profiles():
    """Load HPC settings from file."""
    # Check Config directory first
    config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Config")
    settings_path = os.path.join(config_dir, "hpc_profiles.json")
    
    # If not found in Config, check GUI/config
    if not os.path.exists(settings_path):
        gui_config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "GUI", "config")
        settings_path = os.path.join(gui_config_dir, "hpc_profiles.json")
    
    # If still not found, use default settings
    if not os.path.exists(settings_path):
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
    
    # Load settings from file
    try:
        with open(settings_path, 'r') as f:
            settings = json.load(f)
        
        # Ensure required fields exist
        if "visible_in_gui" not in settings:
            settings["visible_in_gui"] = True
            
        return settings
    except Exception as e:
        print(f"Error loading HPC settings: {e}")
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

def refresh_jobs(app):
    """Refresh the list of jobs."""
    app.refresh_jobs_button.config(state=tk.DISABLED)
    
    # Clear existing jobs
    for item in app.jobs_tree.get_children():
        app.jobs_tree.delete(item)
        
    # Show "refreshing" indicator
    app.jobs_tree.insert('', 'end', values=('', 'Refreshing jobs...', '', '', ''))
    
    # In a real implementation, you would fetch jobs from the HPC server here
    # For now, just simulate a delay and show demo data
    import threading
    threading.Thread(target=lambda: refresh_jobs_thread(app), daemon=True).start()

def refresh_jobs_thread(app):
    """Refresh jobs in a background thread."""
    import time
    import random
    
    # Simulate network delay
    time.sleep(1.5)
    
    # Generate some sample jobs
    jobs = []
    statuses = ['RUNNING', 'QUEUED', 'COMPLETED', 'FAILED']
    queues = ['compute', 'gpu', 'debug']
    
    for i in range(5):
        job_id = f"job_{random.randint(1000, 9999)}"
        status = random.choice(statuses)
        queue = random.choice(queues)
        hours = random.randint(0, 24)
        mins = random.randint(0, 59)
        
        jobs.append({
            'id': job_id,
            'name': f"CFD_Simulation_{i+1}",
            'status': status,
            'queue': queue,
            'time': f"{hours}h {mins}m"
        })
    
    # Update UI in the main thread
    app.root.after(100, lambda: update_jobs_list(app, jobs))

def update_jobs_list(app, jobs):
    """Update the jobs list in the UI."""
    # Clear existing jobs
    for item in app.jobs_tree.get_children():
        app.jobs_tree.delete(item)
        
    # Add jobs to the tree
    if not jobs:
        app.jobs_tree.insert('', 'end', values=('', 'No jobs found', '', '', ''))
    else:
        for job in jobs:
            values = (job['id'], job['name'], job['status'], job['queue'], job['time'])
            app.jobs_tree.insert('', 'end', values=values)
            
    # Re-enable the refresh button
    app.refresh_jobs_button.config(state=tk.NORMAL)

def on_job_select(app):
    """Handle job selection in the tree."""
    selection = app.jobs_tree.selection()
    if not selection:
        return
        
    # Get the selected job info
    item = app.jobs_tree.item(selection[0])
    job_id = item['values'][0]
    
    # Enable/disable buttons based on selection
    # In a real implementation, you would also check job status
    if job_id:
        for button in app.jobs_tree.master.master.winfo_children()[0].winfo_children()[1:4]:
            button.config(state=tk.NORMAL)
    else:
        for button in app.jobs_tree.master.master.winfo_children()[0].winfo_children()[1:4]:
            button.config(state=tk.DISABLED)

def submit_job(app):
    """Show dialog to submit a new job."""
    messagebox.showinfo("Submit Job", 
                      "This would open a dialog to configure and submit a new job.\n\n"
                      "Feature not implemented in this demo.")

def cancel_job(app):
    """Cancel the selected job."""
    selection = app.jobs_tree.selection()
    if not selection:
        return
        
    # Get the selected job info
    item = app.jobs_tree.item(selection[0])
    job_id = item['values'][0]
    job_name = item['values'][1]
    
    # Confirm cancellation
    answer = messagebox.askyesno("Confirm Cancel", f"Are you sure you want to cancel job {job_name} ({job_id})?")
    if not answer:
        return
        
    # In a real implementation, you would send a cancel request to the HPC server here
    messagebox.showinfo("Job Cancelled", f"Job {job_name} ({job_id}) has been cancelled.")
    
    # Update the job status in the tree
    app.jobs_tree.item(selection[0], values=(job_id, job_name, "CANCELLED", item['values'][3], item['values'][4]))

def show_job_details(app):
    """Show details for the selected job."""
    selection = app.jobs_tree.selection()
    if not selection:
        return
        
    # Get the selected job info
    item = app.jobs_tree.item(selection[0])
    job_id = item['values'][0]
    job_name = item['values'][1]
    
    # Create a details dialog
    details_dialog = tk.Toplevel(app.root)
    details_dialog.title(f"Job Details: {job_name}")
    details_dialog.geometry("600x400")
    details_dialog.transient(app.root)
    details_dialog.grab_set()
    
    # Add job details
    frame = ttk.Frame(details_dialog, padding=10)
    frame.pack(fill='both', expand=True)
    
    ttk.Label(frame, text=f"Job ID: {job_id}").pack(anchor='w', pady=2)
    ttk.Label(frame, text=f"Job Name: {job_name}").pack(anchor='w', pady=2)
    ttk.Label(frame, text=f"Status: {item['values'][2]}").pack(anchor='w', pady=2)
    ttk.Label(frame, text=f"Queue: {item['values'][3]}").pack(anchor='w', pady=2)
    ttk.Label(frame, text=f"Elapsed Time: {item['values'][4]}").pack(anchor='w', pady=2)
    
    # Output tabs
    notebook = ttk.Notebook(frame)
    notebook.pack(fill='both', expand=True, pady=10)
    
    # Standard output tab
    stdout_tab = ttk.Frame(notebook)
    notebook.add(stdout_tab, text="Standard Output")
    
    stdout_text = tk.Text(stdout_tab, wrap=tk.WORD)
    stdout_text.pack(fill='both', expand=True)
    stdout_text.insert(tk.END, "Sample job output would appear here.\n\nRunning CFD simulation with parameters:\n- Input mesh: intake3d.msh\n- Solver: OpenFOAM\n- Iterations: 1000\n\nConvergence reached after 568 iterations.\nPressure drop: 124.35 Pa\nFlow uniformity: 92.7%")
    
    # Error output tab
    stderr_tab = ttk.Frame(notebook)
    notebook.add(stderr_tab, text="Error Output")
    
    stderr_text = tk.Text(stderr_tab, wrap=tk.WORD)
    stderr_text.pack(fill='both', expand=True)
    stderr_text.insert(tk.END, "No errors reported.")
    
    # Close button
    ttk.Button(frame, text="Close", command=details_dialog.destroy).pack(pady=10)

def download_results(app):
    """Download results from the selected job."""
    selection = app.jobs_tree.selection()
    if not selection:
        return
        
    # Get the selected job info
    item = app.jobs_tree.item(selection[0])
    job_id = item['values'][0]
    job_name = item['values'][1]
    
    # Create a download dialog
    download_dialog = tk.Toplevel(app.root)
    download_dialog.title(f"Download Results: {job_name}")
    download_dialog.geometry("500x300")
    download_dialog.transient(app.root)
    download_dialog.grab_set()
    
    # Dialog content
    frame = ttk.Frame(download_dialog, padding=10)
    frame.pack(fill='both', expand=True)
    
    ttk.Label(frame, text=f"Job ID: {job_id}").pack(anchor='w', pady=2)
    ttk.Label(frame, text=f"Job Name: {job_name}").pack(anchor='w', pady=2)
    ttk.Label(frame, text="Select destination:").pack(anchor='w', pady=10)
    
    # Destination directory
    dir_frame = ttk.Frame(frame)
    dir_frame.pack(fill='x', pady=5)
    
    dir_var = tk.StringVar(value=os.path.expanduser("~/cfd_results"))
    dir_entry = ttk.Entry(dir_frame, textvariable=dir_var, width=40)
    dir_entry.pack(side='left', fill='x', expand=True)
    
    browse_button = ttk.Button(dir_frame, text="Browse...",
                             command=lambda: browse_dir(dir_var))
    browse_button.pack(side='right', padx=5)
    
    # Options
    options_frame = ttk.LabelFrame(frame, text="Options", padding=5)
    options_frame.pack(fill='x', pady=10)
    
    overwrite_var = tk.BooleanVar(value=False)
    ttk.Checkbutton(options_frame, text="Overwrite existing files",
                  variable=overwrite_var).pack(anchor='w', pady=2)
    
    # Progress
    progress_frame = ttk.Frame(frame)
    progress_frame.pack(fill='x', pady=10)
    
    progress_var = tk.DoubleVar(value=0.0)
    progress_bar = ttk.Progressbar(progress_frame, variable=progress_var, maximum=100)
    progress_bar.pack(fill='x')
    
    status_var = tk.StringVar(value="Ready to download")
    status_label = ttk.Label(progress_frame, textvariable=status_var)
    status_label.pack(anchor='w', pady=5)
    
    # Buttons
    button_frame = ttk.Frame(frame)
    button_frame.pack(fill='x', pady=10)
    
    download_button = ttk.Button(button_frame, text="Download",
                               command=lambda: simulate_download(
                                   progress_var, status_var, download_button, cancel_button))
    download_button.pack(side='left', padx=5)
    
    cancel_button = ttk.Button(button_frame, text="Cancel",
                             command=download_dialog.destroy)
    cancel_button.pack(side='right', padx=5)

def browse_dir(dir_var):
    """Browse for a directory."""
    directory = filedialog.askdirectory(
        title="Select Download Directory"
    )
    if directory:
        dir_var.set(directory)

def simulate_download(progress_var, status_var, download_button, cancel_button):
    """Simulate a download process."""
    download_button.config(state=tk.DISABLED)
    
    def update_progress():
        import time
        import random
        
        for i in range(1, 101):
            if i < 100:
                status_var.set(f"Downloading... ({i}%)")
            else:
                status_var.set("Download completed successfully")
                download_button.config(state=tk.NORMAL)
                
            progress_var.set(i)
            
            # Random delay to simulate network activity
            time.sleep(0.05 + random.random() * 0.05)
            
    import threading
    threading.Thread(target=update_progress, daemon=True).start()

if __name__ == "__main__":
    # Test with a dummy app
    class DummyApp:
        def __init__(self):
            self.root = tk.Tk()
            self.root.title("HPC Tab Test")
            self.root.geometry("800x600")
            
            self.notebook = ttk.Notebook(self.root)
            self.notebook.pack(fill='both', expand=True)
            
            # Create a dummy tab
            dummy_tab = ttk.Frame(self.notebook)
            self.notebook.add(dummy_tab, text="Dummy")
            
            # Create HPC tab
            self.hpc_tab = ttk.Frame(self.notebook)
            self.notebook.add(self.hpc_tab, text="HPC")
    
    app = DummyApp()
    create_hpc_tab_content(app)
    app.root.mainloop()