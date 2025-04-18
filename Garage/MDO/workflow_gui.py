"""
WorkflowGUI module for the MDO package.

This module provides a simple GUI for setting up and running MDO workflows.
It interfaces with the HPC module to enable remote computing capabilities.
"""

import tkinter as tk
from tkinter import ttk
import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("WorkflowGUI")

class WorkflowGUI:
    """
    GUI for setting up and running MDO workflows with HPC integration.
    This is a minimal implementation to support the unit tests.
    """
    def __init__(self, parent, **kwargs):
        """
        Initialize the WorkflowGUI.
        
        Args:
            parent: Parent tkinter widget/window
            **kwargs: Additional keyword arguments
        """
        self.parent = parent
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill="both", expand=True)
        
        # Create workflow tab
        self.workflow_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.workflow_tab, text="Workflow")
        
        # Create remote tab for HPC integration
        self.remote_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.remote_tab, text="HPC")
        
        # Set up the tabs
        self.setup_workflow_tab()
        self.setup_remote_tab()
        
        # HPC connection status
        self.connection_status_var = tk.StringVar(value="Not connected")
        self.hpc_connector = None
    
    def setup_workflow_tab(self):
        """Set up the workflow tab with necessary components"""
        # This is implemented in the actual application
        pass
    
    def setup_remote_tab(self):
        """Set up the remote HPC tab with connection and job controls"""
        # Connection frame
        self.connection_frame = ttk.LabelFrame(self.remote_tab, text="HPC Connection")
        self.connection_frame.pack(fill="x", padx=10, pady=5)
        
        # Connection settings
        ttk.Label(self.connection_frame, text="Hostname:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.hpc_hostname = ttk.Entry(self.connection_frame)
        self.hpc_hostname.grid(row=0, column=1, sticky="we", padx=5, pady=2)
        
        ttk.Label(self.connection_frame, text="Username:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.hpc_username = ttk.Entry(self.connection_frame)
        self.hpc_username.grid(row=1, column=1, sticky="we", padx=5, pady=2)
        
        ttk.Label(self.connection_frame, text="Authentication:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.auth_type = tk.StringVar(value="password")
        auth_frame = ttk.Frame(self.connection_frame)
        auth_frame.grid(row=2, column=1, sticky="we", padx=5, pady=2)
        ttk.Radiobutton(auth_frame, text="Password", variable=self.auth_type, value="password", 
                      command=self.toggle_auth_type).pack(side="left", padx=5)
        ttk.Radiobutton(auth_frame, text="SSH Key", variable=self.auth_type, value="key", 
                      command=self.toggle_auth_type).pack(side="left", padx=5)
        
        # Password frame
        self.password_frame = ttk.Frame(self.connection_frame)
        self.password_frame.grid(row=3, column=0, columnspan=2, sticky="we", padx=5, pady=2)
        ttk.Label(self.password_frame, text="Password:").pack(side="left", padx=5)
        self.hpc_password = ttk.Entry(self.password_frame, show="*")
        self.hpc_password.pack(side="left", expand=True, fill="x", padx=5)
        
        # Key frame (hidden initially)
        self.key_frame = ttk.Frame(self.connection_frame)
        ttk.Label(self.key_frame, text="Key Path:").pack(side="left", padx=5)
        self.hpc_key_path = ttk.Entry(self.key_frame)
        self.hpc_key_path.pack(side="left", expand=True, fill="x", padx=5)
        ttk.Button(self.key_frame, text="Browse...", command=self.browse_key_file).pack(side="left", padx=5)
        
        # Port and scheduler
        port_frame = ttk.Frame(self.connection_frame)
        port_frame.grid(row=4, column=0, columnspan=2, sticky="we", padx=5, pady=2)
        ttk.Label(port_frame, text="Port:").pack(side="left", padx=5)
        self.hpc_port = ttk.Entry(port_frame, width=6)
        self.hpc_port.pack(side="left", padx=5)
        self.hpc_port.insert(0, "22")
        
        ttk.Label(port_frame, text="Scheduler:").pack(side="left", padx=5)
        self.hpc_scheduler = ttk.Combobox(port_frame, values=["slurm", "pbs", "sge"], width=10)
        self.hpc_scheduler.pack(side="left", padx=5)
        self.hpc_scheduler.current(0)
        
        # Connection buttons
        btn_frame = ttk.Frame(self.connection_frame)
        btn_frame.grid(row=5, column=0, columnspan=2, sticky="we", padx=5, pady=5)
        ttk.Button(btn_frame, text="Test Connection", command=self.test_hpc_connection).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Disconnect", command=self.disconnect_hpc).pack(side="left", padx=5)
        
        # Status indicator
        status_frame = ttk.Frame(self.connection_frame)
        status_frame.grid(row=6, column=0, columnspan=2, sticky="we", padx=5, pady=2)
        ttk.Label(status_frame, text="Status:").pack(side="left", padx=5)
        ttk.Label(status_frame, textvariable=self.connection_status_var).pack(side="left", padx=5)
        
        # Job submission frame
        job_frame = ttk.LabelFrame(self.remote_tab, text="Job Submission")
        job_frame.pack(fill="x", padx=10, pady=5)
        
        # Job settings
        ttk.Label(job_frame, text="Job Name:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.job_name = ttk.Entry(job_frame)
        self.job_name.grid(row=0, column=1, sticky="we", padx=5, pady=2)
        
        ttk.Label(job_frame, text="Nodes:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.job_nodes = ttk.Spinbox(job_frame, from_=1, to=100, width=5)
        self.job_nodes.grid(row=1, column=1, sticky="w", padx=5, pady=2)
        self.job_nodes.insert(0, "1")
        
        ttk.Label(job_frame, text="Cores/Node:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.job_cores = ttk.Spinbox(job_frame, from_=1, to=128, width=5)
        self.job_cores.grid(row=2, column=1, sticky="w", padx=5, pady=2)
        self.job_cores.insert(0, "4")
        
        ttk.Label(job_frame, text="Queue:").grid(row=3, column=0, sticky="w", padx=5, pady=2)
        self.job_queue = ttk.Combobox(job_frame, values=["compute", "gpu", "debug"])
        self.job_queue.grid(row=3, column=1, sticky="we", padx=5, pady=2)
        self.job_queue.current(0)
        
        # Job submission buttons
        job_btn_frame = ttk.Frame(job_frame)
        job_btn_frame.grid(row=4, column=0, columnspan=2, sticky="we", padx=5, pady=5)
        ttk.Button(job_btn_frame, text="Submit Job", command=self.submit_remote_job).pack(side="left", padx=5)
        ttk.Button(job_btn_frame, text="Update Status", command=self.update_job_status).pack(side="left", padx=5)
        
        # Jobs list
        jobs_frame = ttk.LabelFrame(self.remote_tab, text="Jobs")
        jobs_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Create treeview for jobs
        columns = ("id", "name", "status", "submitted", "duration")
        self.jobs_tree = ttk.Treeview(jobs_frame, columns=columns, show="headings")
        
        # Define column headings
        self.jobs_tree.heading("id", text="Job ID")
        self.jobs_tree.heading("name", text="Name")
        self.jobs_tree.heading("status", text="Status")
        self.jobs_tree.heading("submitted", text="Submitted")
        self.jobs_tree.heading("duration", text="Duration")
        
        # Column widths
        self.jobs_tree.column("id", width=100)
        self.jobs_tree.column("name", width=150)
        self.jobs_tree.column("status", width=100)
        self.jobs_tree.column("submitted", width=150)
        self.jobs_tree.column("duration", width=100)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(jobs_frame, orient="vertical", command=self.jobs_tree.yview)
        self.jobs_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack everything
        self.jobs_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Job output
        output_frame = ttk.LabelFrame(self.remote_tab, text="Job Output")
        output_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Text widget for job output
        self.job_output_text = tk.Text(output_frame, height=10, width=40)
        self.job_output_text.pack(side="left", fill="both", expand=True)
        
        # Scrollbar for output
        output_scrollbar = ttk.Scrollbar(output_frame, orient="vertical", command=self.job_output_text.yview)
        self.job_output_text.configure(yscrollcommand=output_scrollbar.set)
        output_scrollbar.pack(side="right", fill="y")
    
    def toggle_auth_type(self):
        """Toggle between password and key authentication methods"""
        if self.auth_type.get() == "password":
            self.password_frame.grid()
            self.key_frame.grid_remove()
        else:
            self.password_frame.grid_remove()
            self.key_frame.grid()
    
    def browse_key_file(self):
        """Open file dialog to browse for SSH key file"""
        from tkinter import filedialog
        filename = filedialog.askopenfilename(title="Select SSH Key File",
                                            filetypes=[("All Files", "*.*"), 
                                                      ("SSH Private Key", "*.pem"),
                                                      ("OpenSSH Key", "*.key")])
        if filename:
            self.hpc_key_path.delete(0, tk.END)
            self.hpc_key_path.insert(0, filename)
    
    def test_hpc_connection(self):
        """Test connection to HPC system"""
        # In the real implementation, this would use the HPC connector
        config = self.get_hpc_config()
        # For now, just update the status
        self._update_connection_result(True, "Connected successfully")
    
    def disconnect_hpc(self):
        """Disconnect from HPC system"""
        if self.hpc_connector:
            self.hpc_connector = None
        self.connection_status_var.set("Disconnected")
    
    def get_hpc_config(self):
        """Get HPC configuration from GUI fields"""
        config = {
            "hostname": self.hpc_hostname.get(),
            "username": self.hpc_username.get(),
            "port": int(self.hpc_port.get()),
            "scheduler": self.hpc_scheduler.get(),
            "use_key": self.auth_type.get() == "key",
        }
        
        if config["use_key"]:
            config["key_path"] = self.hpc_key_path.get()
        else:
            config["password"] = self.hpc_password.get()
            
        return config
    
    def _update_connection_result(self, success, message):
        """Update the connection status display"""
        if success:
            self.connection_status_var.set("Connected")
        else:
            self.connection_status_var.set(f"Failed: {message}")
    
    def submit_remote_job(self):
        """Submit a job to the remote HPC system"""
        # This would actually use the HPC connector
        return None
    
    def update_job_status(self):
        """Update the status of jobs in the tree view"""
        # This would use the HPC connector to fetch job statuses
        pass
    
    def show_job_script_confirmation(self, script):
        """Show a confirmation dialog with the job script"""
        return True  # Always confirm in this mock implementation