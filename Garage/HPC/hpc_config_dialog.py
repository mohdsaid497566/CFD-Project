#!/usr/bin/env python3
"""
HPC Configuration Dialog for the Intake CFD Project.

This module provides a dialog window for configuring HPC settings,
including connection parameters, job settings, and module selection.
"""

import os
import sys
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("hpc_config")

class HPCConfigDialog:
    """Dialog for configuring HPC settings"""
    
    def __init__(self, parent, config_path=None):
        """
        Initialize the HPC configuration dialog.
        
        Args:
            parent: The parent window
            config_path: Path to the HPC configuration file
        """
        self.parent = parent
        self.config_path = config_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "Config", "hpc_profiles.json"
        )
        
        # Load current configuration
        self.config = self.load_config()
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("HPC Configuration")
        self.dialog.geometry("650x600")
        self.dialog.minsize(600, 500)
        
        # Make dialog modal
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog on parent window
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        
        dialog_width = 650
        dialog_height = 600
        
        position_x = parent_x + (parent_width - dialog_width) // 2
        position_y = parent_y + (parent_height - dialog_height) // 2
        
        self.dialog.geometry(f"{dialog_width}x{dialog_height}+{position_x}+{position_y}")
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.dialog)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create tabs
        self.connection_tab = ttk.Frame(self.notebook)
        self.job_tab = ttk.Frame(self.notebook)
        self.modules_tab = ttk.Frame(self.notebook)
        self.advanced_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.connection_tab, text="Connection")
        self.notebook.add(self.job_tab, text="Job Settings")
        self.notebook.add(self.modules_tab, text="Modules")
        self.notebook.add(self.advanced_tab, text="Advanced")
        
        # Setup tabs
        self.setup_connection_tab()
        self.setup_job_tab()
        self.setup_modules_tab()
        self.setup_advanced_tab()
        
        # Add buttons at bottom
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Button(button_frame, text="Save", command=self.save_config).pack(side="right", padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy).pack(side="right", padx=5)
        ttk.Button(button_frame, text="Test Connection", command=self.test_connection).pack(side="left", padx=5)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(self.dialog, textvariable=self.status_var, relief="sunken", anchor="w")
        status_bar.pack(side="bottom", fill="x")
    
    def load_config(self):
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                logger.info(f"Loaded HPC configuration from {self.config_path}")
                return config
            else:
                logger.warning(f"HPC config file not found: {self.config_path}")
                return self.get_default_config()
        except Exception as e:
            logger.error(f"Error loading HPC config: {str(e)}")
            return self.get_default_config()
    
    def get_default_config(self):
        """Get default configuration"""
        return {
            "hpc_enabled": True,
            "hpc_host": "localhost",
            "hpc_username": "",
            "hpc_port": 22,
            "hpc_remote_dir": "/home/user/cfd_projects",
            "use_key_auth": False,
            "key_path": "",
            "visible_in_gui": True,
            "scheduler": "slurm",
            "default_partition": "compute",
            "default_job_settings": {
                "nodes": 1,
                "cores_per_node": 8,
                "memory": "16G",
                "wall_time": "24:00:00",
                "job_priority": "normal"
            },
            "doe_settings": {
                "max_parallel_jobs": 5,
                "max_parallel_samples_per_job": 4,
                "results_dir": "cfd_results",
                "template_dir": "cfd_templates",
                "auto_download_results": True
            },
            "openfoam_settings": {
                "version": "v2006",
                "solver": "simpleFoam",
                "cores_per_case": 4,
                "decomposition_method": "scotch",
                "max_iterations": 1000,
                "residual_tolerance": 1e-5
            },
            "modules_to_load": [
                "python/3.8",
                "openfoam/v2006",
                "paraview/5.9.0"
            ],
            "environment_variables": {
                "OMP_NUM_THREADS": "4",
                "MPI_BUFFER_SIZE": "20971520"
            }
        }
    
    def setup_connection_tab(self):
        """Set up the connection tab"""
        frame = ttk.Frame(self.connection_tab)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Enable HPC checkbox
        self.hpc_enabled_var = tk.BooleanVar(value=self.config.get("hpc_enabled", True))
        ttk.Checkbutton(frame, text="Enable HPC Integration", variable=self.hpc_enabled_var).grid(row=0, column=0, columnspan=2, sticky="w", padx=5, pady=5)
        
        # Connection settings
        ttk.Label(frame, text="Hostname:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.host_entry = ttk.Entry(frame, width=40)
        self.host_entry.grid(row=1, column=1, sticky="we", padx=5, pady=5)
        self.host_entry.insert(0, self.config.get("hpc_host", "localhost"))
        
        ttk.Label(frame, text="Username:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.username_entry = ttk.Entry(frame, width=40)
        self.username_entry.grid(row=2, column=1, sticky="we", padx=5, pady=5)
        self.username_entry.insert(0, self.config.get("hpc_username", ""))
        
        ttk.Label(frame, text="Port:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        self.port_entry = ttk.Entry(frame, width=10)
        self.port_entry.grid(row=3, column=1, sticky="w", padx=5, pady=5)
        self.port_entry.insert(0, str(self.config.get("hpc_port", 22)))
        
        # Authentication type
        ttk.Label(frame, text="Authentication:").grid(row=4, column=0, sticky="w", padx=5, pady=5)
        self.auth_type_var = tk.StringVar(value="password" if not self.config.get("use_key_auth", False) else "key")
        
        auth_frame = ttk.Frame(frame)
        auth_frame.grid(row=4, column=1, sticky="w", padx=5, pady=5)
        
        ttk.Radiobutton(auth_frame, text="Password", variable=self.auth_type_var, value="password", 
                       command=self.toggle_auth_type).grid(row=0, column=0, padx=5)
        ttk.Radiobutton(auth_frame, text="SSH Key", variable=self.auth_type_var, value="key", 
                       command=self.toggle_auth_type).grid(row=0, column=1, padx=5)
        
        # Password field
        self.password_frame = ttk.Frame(frame)
        self.password_frame.grid(row=5, column=0, columnspan=2, sticky="we", padx=5, pady=5)
        
        ttk.Label(self.password_frame, text="Password:").pack(side="left", padx=5)
        self.password_entry = ttk.Entry(self.password_frame, show="*", width=30)
        self.password_entry.pack(side="left", expand=True, fill="x", padx=5)
        
        # Key field
        self.key_frame = ttk.Frame(frame)
        self.key_frame.grid(row=6, column=0, columnspan=2, sticky="we", padx=5, pady=5)
        
        ttk.Label(self.key_frame, text="Key Path:").pack(side="left", padx=5)
        self.key_path_entry = ttk.Entry(self.key_frame, width=30)
        self.key_path_entry.pack(side="left", expand=True, fill="x", padx=5)
        
        if self.config.get("key_path"):
            self.key_path_entry.insert(0, self.config.get("key_path"))
            
        ttk.Button(self.key_frame, text="Browse...", command=self.browse_key_file).pack(side="left", padx=5)
        
        # Initial visibility of auth frames
        if self.auth_type_var.get() == "password":
            self.key_frame.grid_remove()
        else:
            self.password_frame.grid_remove()
        
        # Remote directory
        ttk.Label(frame, text="Remote Directory:").grid(row=7, column=0, sticky="w", padx=5, pady=5)
        self.remote_dir_entry = ttk.Entry(frame, width=40)
        self.remote_dir_entry.grid(row=7, column=1, sticky="we", padx=5, pady=5)
        self.remote_dir_entry.insert(0, self.config.get("hpc_remote_dir", "/home/user/cfd_projects"))
        
        # Scheduler
        ttk.Label(frame, text="Job Scheduler:").grid(row=8, column=0, sticky="w", padx=5, pady=5)
        self.scheduler_var = tk.StringVar(value=self.config.get("scheduler", "slurm"))
        scheduler_combo = ttk.Combobox(frame, textvariable=self.scheduler_var,
                                     values=["slurm", "pbs", "sge"])
        scheduler_combo.grid(row=8, column=1, sticky="w", padx=5, pady=5)
        scheduler_combo.current(0 if self.scheduler_var.get() == "slurm" else 
                               1 if self.scheduler_var.get() == "pbs" else 2)
        
        # Show in GUI
        self.visible_in_gui_var = tk.BooleanVar(value=self.config.get("visible_in_gui", True))
        ttk.Checkbutton(frame, text="Show HPC options in GUI", variable=self.visible_in_gui_var).grid(row=9, column=0, columnspan=2, sticky="w", padx=5, pady=5)
    
    def setup_job_tab(self):
        """Set up the job settings tab"""
        frame = ttk.Frame(self.job_tab)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        job_settings = self.config.get("default_job_settings", {})
        
        # Default partition
        ttk.Label(frame, text="Default Partition/Queue:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.partition_entry = ttk.Entry(frame, width=20)
        self.partition_entry.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        self.partition_entry.insert(0, self.config.get("default_partition", "compute"))
        
        # Nodes
        ttk.Label(frame, text="Default Nodes:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.nodes_spinbox = ttk.Spinbox(frame, from_=1, to=1000, width=10)
        self.nodes_spinbox.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        self.nodes_spinbox.delete(0, tk.END)
        self.nodes_spinbox.insert(0, job_settings.get("nodes", 1))
        
        # Cores per node
        ttk.Label(frame, text="Cores per Node:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.cores_spinbox = ttk.Spinbox(frame, from_=1, to=128, width=10)
        self.cores_spinbox.grid(row=2, column=1, sticky="w", padx=5, pady=5)
        self.cores_spinbox.delete(0, tk.END)
        self.cores_spinbox.insert(0, job_settings.get("cores_per_node", 8))
        
        # Memory
        ttk.Label(frame, text="Memory:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        self.memory_entry = ttk.Entry(frame, width=20)
        self.memory_entry.grid(row=3, column=1, sticky="w", padx=5, pady=5)
        self.memory_entry.insert(0, job_settings.get("memory", "16G"))
        
        # Wall time
        ttk.Label(frame, text="Wall Time:").grid(row=4, column=0, sticky="w", padx=5, pady=5)
        self.wall_time_entry = ttk.Entry(frame, width=20)
        self.wall_time_entry.grid(row=4, column=1, sticky="w", padx=5, pady=5)
        self.wall_time_entry.insert(0, job_settings.get("wall_time", "24:00:00"))
        
        # Job priority
        ttk.Label(frame, text="Job Priority:").grid(row=5, column=0, sticky="w", padx=5, pady=5)
        self.priority_var = tk.StringVar(value=job_settings.get("job_priority", "normal"))
        priority_combo = ttk.Combobox(frame, textvariable=self.priority_var,
                                    values=["low", "normal", "high"])
        priority_combo.grid(row=5, column=1, sticky="w", padx=5, pady=5)
        
        # Separator
        ttk.Separator(frame, orient="horizontal").grid(row=6, column=0, columnspan=2, sticky="ew", pady=10)
        
        # DoE settings
        doe_settings = self.config.get("doe_settings", {})
        ttk.Label(frame, text="DoE Settings:", font=("TkDefaultFont", 10, "bold")).grid(row=7, column=0, columnspan=2, sticky="w", padx=5, pady=5)
        
        # Max parallel jobs
        ttk.Label(frame, text="Max Parallel Jobs:").grid(row=8, column=0, sticky="w", padx=5, pady=5)
        self.max_jobs_spinbox = ttk.Spinbox(frame, from_=1, to=100, width=10)
        self.max_jobs_spinbox.grid(row=8, column=1, sticky="w", padx=5, pady=5)
        self.max_jobs_spinbox.delete(0, tk.END)
        self.max_jobs_spinbox.insert(0, doe_settings.get("max_parallel_jobs", 5))
        
        # Max parallel samples
        ttk.Label(frame, text="Max Samples per Job:").grid(row=9, column=0, sticky="w", padx=5, pady=5)
        self.max_samples_spinbox = ttk.Spinbox(frame, from_=1, to=1000, width=10)
        self.max_samples_spinbox.grid(row=9, column=1, sticky="w", padx=5, pady=5)
        self.max_samples_spinbox.delete(0, tk.END)
        self.max_samples_spinbox.insert(0, doe_settings.get("max_parallel_samples_per_job", 4))
        
        # Results directory
        ttk.Label(frame, text="Results Directory:").grid(row=10, column=0, sticky="w", padx=5, pady=5)
        self.results_dir_entry = ttk.Entry(frame, width=20)
        self.results_dir_entry.grid(row=10, column=1, sticky="w", padx=5, pady=5)
        self.results_dir_entry.insert(0, doe_settings.get("results_dir", "cfd_results"))
        
        # Template directory
        ttk.Label(frame, text="Template Directory:").grid(row=11, column=0, sticky="w", padx=5, pady=5)
        self.template_dir_entry = ttk.Entry(frame, width=20)
        self.template_dir_entry.grid(row=11, column=1, sticky="w", padx=5, pady=5)
        self.template_dir_entry.insert(0, doe_settings.get("template_dir", "cfd_templates"))
        
        # Auto download results
        self.auto_download_var = tk.BooleanVar(value=doe_settings.get("auto_download_results", True))
        ttk.Checkbutton(frame, text="Auto-Download Results", variable=self.auto_download_var).grid(row=12, column=0, columnspan=2, sticky="w", padx=5, pady=5)
    
    def setup_modules_tab(self):
        """Set up the modules tab"""
        frame = ttk.Frame(self.modules_tab)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # OpenFOAM settings
        openfoam_settings = self.config.get("openfoam_settings", {})
        ttk.Label(frame, text="OpenFOAM Settings:", font=("TkDefaultFont", 10, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", padx=5, pady=5)
        
        # OpenFOAM version
        ttk.Label(frame, text="Version:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.openfoam_version_entry = ttk.Entry(frame, width=20)
        self.openfoam_version_entry.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        self.openfoam_version_entry.insert(0, openfoam_settings.get("version", "v2006"))
        
        # OpenFOAM solver
        ttk.Label(frame, text="Solver:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.openfoam_solver_var = tk.StringVar(value=openfoam_settings.get("solver", "simpleFoam"))
        solvers = ["simpleFoam", "pimpleFoam", "buoyantPimpleFoam", "rhoSimpleFoam"]
        solver_combo = ttk.Combobox(frame, textvariable=self.openfoam_solver_var, values=solvers)
        solver_combo.grid(row=2, column=1, sticky="w", padx=5, pady=5)
        
        # Cores per case
        ttk.Label(frame, text="Cores per Case:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        self.openfoam_cores_spinbox = ttk.Spinbox(frame, from_=1, to=128, width=10)
        self.openfoam_cores_spinbox.grid(row=3, column=1, sticky="w", padx=5, pady=5)
        self.openfoam_cores_spinbox.delete(0, tk.END)
        self.openfoam_cores_spinbox.insert(0, openfoam_settings.get("cores_per_case", 4))
        
        # Decomposition method
        ttk.Label(frame, text="Decomposition Method:").grid(row=4, column=0, sticky="w", padx=5, pady=5)
        self.decomp_var = tk.StringVar(value=openfoam_settings.get("decomposition_method", "scotch"))
        decomp_combo = ttk.Combobox(frame, textvariable=self.decomp_var,
                                  values=["scotch", "simple", "hierarchical"])
        decomp_combo.grid(row=4, column=1, sticky="w", padx=5, pady=5)
        
        # Max iterations
        ttk.Label(frame, text="Max Iterations:").grid(row=5, column=0, sticky="w", padx=5, pady=5)
        self.max_iter_spinbox = ttk.Spinbox(frame, from_=100, to=10000, width=10)
        self.max_iter_spinbox.grid(row=5, column=1, sticky="w", padx=5, pady=5)
        self.max_iter_spinbox.delete(0, tk.END)
        self.max_iter_spinbox.insert(0, openfoam_settings.get("max_iterations", 1000))
        
        # Residual tolerance
        ttk.Label(frame, text="Residual Tolerance:").grid(row=6, column=0, sticky="w", padx=5, pady=5)
        self.tolerance_entry = ttk.Entry(frame, width=20)
        self.tolerance_entry.grid(row=6, column=1, sticky="w", padx=5, pady=5)
        self.tolerance_entry.insert(0, str(openfoam_settings.get("residual_tolerance", 1e-5)))
        
        # Separator
        ttk.Separator(frame, orient="horizontal").grid(row=7, column=0, columnspan=2, sticky="ew", pady=10)
        
        # Modules to load
        ttk.Label(frame, text="Modules to Load:", font=("TkDefaultFont", 10, "bold")).grid(row=8, column=0, columnspan=2, sticky="w", padx=5, pady=5)
        
        # Module list
        modules_frame = ttk.Frame(frame)
        modules_frame.grid(row=9, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        
        # Scrollbar and listbox for modules
        scrollbar = ttk.Scrollbar(modules_frame, orient=tk.VERTICAL)
        self.modules_listbox = tk.Listbox(modules_frame, height=5, width=40, yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.modules_listbox.yview)
        
        self.modules_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Add default modules
        for module in self.config.get("modules_to_load", []):
            self.modules_listbox.insert(tk.END, module)
        
        # Module management buttons
        module_btn_frame = ttk.Frame(frame)
        module_btn_frame.grid(row=10, column=0, columnspan=2, sticky="w", padx=5, pady=5)
        
        self.module_entry = ttk.Entry(module_btn_frame, width=30)
        self.module_entry.pack(side="left", padx=5)
        
        ttk.Button(module_btn_frame, text="Add", command=self.add_module).pack(side="left", padx=5)
        ttk.Button(module_btn_frame, text="Remove Selected", command=self.remove_module).pack(side="left", padx=5)
    
    def setup_advanced_tab(self):
        """Set up the advanced settings tab"""
        frame = ttk.Frame(self.advanced_tab)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Environment variables
        ttk.Label(frame, text="Environment Variables:", font=("TkDefaultFont", 10, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", padx=5, pady=5)
        
        # Create a treeview for environment variables
        columns = ("name", "value")
        self.env_tree = ttk.Treeview(frame, columns=columns, show="headings", height=6)
        self.env_tree.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        
        self.env_tree.heading("name", text="Name")
        self.env_tree.heading("value", text="Value")
        self.env_tree.column("name", width=150)
        self.env_tree.column("value", width=250)
        
        # Add scrollbar
        env_scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.env_tree.yview)
        env_scrollbar.grid(row=1, column=2, sticky="ns")
        self.env_tree.configure(yscrollcommand=env_scrollbar.set)
        
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(1, weight=1)
        frame.grid_rowconfigure(1, weight=1)
        
        # Add environment variables from config
        env_vars = self.config.get("environment_variables", {})
        for name, value in env_vars.items():
            self.env_tree.insert("", "end", values=(name, value))
        
        # Environment variable controls
        env_control_frame = ttk.Frame(frame)
        env_control_frame.grid(row=2, column=0, columnspan=2, sticky="w", padx=5, pady=5)
        
        ttk.Label(env_control_frame, text="Name:").pack(side="left", padx=5)
        self.env_name_entry = ttk.Entry(env_control_frame, width=15)
        self.env_name_entry.pack(side="left", padx=5)
        
        ttk.Label(env_control_frame, text="Value:").pack(side="left", padx=5)
        self.env_value_entry = ttk.Entry(env_control_frame, width=20)
        self.env_value_entry.pack(side="left", padx=5)
        
        ttk.Button(env_control_frame, text="Add/Update", command=self.add_env_var).pack(side="left", padx=5)
        ttk.Button(env_control_frame, text="Remove", command=self.remove_env_var).pack(side="left", padx=5)
        
        # Separator
        ttk.Separator(frame, orient="horizontal").grid(row=3, column=0, columnspan=2, sticky="ew", pady=10)
        
        # Configuration file path
        ttk.Label(frame, text="Configuration File:").grid(row=4, column=0, sticky="w", padx=5, pady=5)
        self.config_path_entry = ttk.Entry(frame, width=40)
        self.config_path_entry.grid(row=4, column=1, sticky="we", padx=5, pady=5)
        self.config_path_entry.insert(0, self.config_path)
        
        # Configure additional buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=5, column=0, columnspan=2, sticky="w", padx=5, pady=5)
        
        ttk.Button(btn_frame, text="Browse...", command=self.browse_config_path).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Reset to Defaults", command=self.reset_to_defaults).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Import Configuration", command=self.import_config).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Export Configuration", command=self.export_config).pack(side="left", padx=5)
    
    def toggle_auth_type(self):
        """Toggle between password and key authentication frames"""
        if self.auth_type_var.get() == "password":
            self.password_frame.grid()
            self.key_frame.grid_remove()
        else:
            self.password_frame.grid_remove()
            self.key_frame.grid()
    
    def browse_key_file(self):
        """Browse for SSH key file"""
        filename = filedialog.askopenfilename(
            title="Select SSH Key File",
            filetypes=[
                ("All Files", "*.*"),
                ("SSH Private Key", "*.pem"),
                ("OpenSSH Key", "*.key")
            ]
        )
        if filename:
            self.key_path_entry.delete(0, tk.END)
            self.key_path_entry.insert(0, filename)
    
    def browse_config_path(self):
        """Browse for configuration file path"""
        filename = filedialog.asksaveasfilename(
            title="Select Configuration File",
            defaultextension=".json",
            filetypes=[
                ("JSON Files", "*.json"),
                ("All Files", "*.*")
            ]
        )
        if filename:
            self.config_path_entry.delete(0, tk.END)
            self.config_path_entry.insert(0, filename)
    
    def add_module(self):
        """Add a module to the list"""
        module_name = self.module_entry.get().strip()
        if module_name:
            self.modules_listbox.insert(tk.END, module_name)
            self.module_entry.delete(0, tk.END)
    
    def remove_module(self):
        """Remove selected module from the list"""
        selected_indices = self.modules_listbox.curselection()
        if selected_indices:
            # Remove in reverse order to maintain indices
            for i in sorted(selected_indices, reverse=True):
                self.modules_listbox.delete(i)
    
    def add_env_var(self):
        """Add or update an environment variable"""
        name = self.env_name_entry.get().strip()
        value = self.env_value_entry.get().strip()
        
        if name:
            # Check if variable already exists
            for item in self.env_tree.get_children():
                if self.env_tree.item(item)['values'][0] == name:
                    self.env_tree.delete(item)
                    break
            
            self.env_tree.insert("", "end", values=(name, value))
            self.env_name_entry.delete(0, tk.END)
            self.env_value_entry.delete(0, tk.END)
    
    def remove_env_var(self):
        """Remove selected environment variable"""
        selected_items = self.env_tree.selection()
        if selected_items:
            for item in selected_items:
                self.env_tree.delete(item)
    
    def reset_to_defaults(self):
        """Reset configuration to defaults"""
        if messagebox.askyesno("Reset to Defaults", "Reset all settings to defaults?"):
            self.config = self.get_default_config()
            self.dialog.destroy()
            self.__init__(self.parent, self.config_path)
    
    def import_config(self):
        """Import configuration from a file"""
        filename = filedialog.askopenfilename(
            title="Import Configuration",
            defaultextension=".json",
            filetypes=[
                ("JSON Files", "*.json"),
                ("All Files", "*.*")
            ]
        )
        
        if filename:
            try:
                with open(filename, 'r') as f:
                    imported_config = json.load(f)
                
                # Merge with current config to ensure all fields are present
                self.config.update(imported_config)
                
                # Reload the dialog
                self.dialog.destroy()
                self.__init__(self.parent, self.config_path)
                
                self.status_var.set(f"Configuration imported from {filename}")
                
            except Exception as e:
                messagebox.showerror("Import Error", f"Failed to import configuration: {str(e)}")
    
    def export_config(self):
        """Export configuration to a file"""
        filename = filedialog.asksaveasfilename(
            title="Export Configuration",
            defaultextension=".json",
            filetypes=[
                ("JSON Files", "*.json"),
                ("All Files", "*.*")
            ]
        )
        
        if filename:
            # Get current configuration
            config = self.collect_config_from_ui()
            
            try:
                with open(filename, 'w') as f:
                    json.dump(config, f, indent=4)
                
                self.status_var.set(f"Configuration exported to {filename}")
                
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export configuration: {str(e)}")
    
    def collect_config_from_ui(self):
        """Collect configuration settings from UI"""
        config = {}
        
        # Connection settings
        config["hpc_enabled"] = self.hpc_enabled_var.get()
        config["hpc_host"] = self.host_entry.get().strip()
        config["hpc_username"] = self.username_entry.get().strip()
        config["hpc_port"] = int(self.port_entry.get().strip())
        config["hpc_remote_dir"] = self.remote_dir_entry.get().strip()
        config["use_key_auth"] = self.auth_type_var.get() == "key"
        config["key_path"] = self.key_path_entry.get().strip() if config["use_key_auth"] else ""
        config["visible_in_gui"] = self.visible_in_gui_var.get()
        config["scheduler"] = self.scheduler_var.get()
        config["default_partition"] = self.partition_entry.get().strip()
        
        # Job settings
        config["default_job_settings"] = {
            "nodes": int(self.nodes_spinbox.get()),
            "cores_per_node": int(self.cores_spinbox.get()),
            "memory": self.memory_entry.get().strip(),
            "wall_time": self.wall_time_entry.get().strip(),
            "job_priority": self.priority_var.get()
        }
        
        # DoE settings
        config["doe_settings"] = {
            "max_parallel_jobs": int(self.max_jobs_spinbox.get()),
            "max_parallel_samples_per_job": int(self.max_samples_spinbox.get()),
            "results_dir": self.results_dir_entry.get().strip(),
            "template_dir": self.template_dir_entry.get().strip(),
            "auto_download_results": self.auto_download_var.get()
        }
        
        # OpenFOAM settings
        config["openfoam_settings"] = {
            "version": self.openfoam_version_entry.get().strip(),
            "solver": self.openfoam_solver_var.get(),
            "cores_per_case": int(self.openfoam_cores_spinbox.get()),
            "decomposition_method": self.decomp_var.get(),
            "max_iterations": int(self.max_iter_spinbox.get()),
            "residual_tolerance": float(self.tolerance_entry.get().strip())
        }
        
        # Modules
        config["modules_to_load"] = list(self.modules_listbox.get(0, tk.END))
        
        # Environment variables
        env_vars = {}
        for item in self.env_tree.get_children():
            name, value = self.env_tree.item(item)['values']
            env_vars[name] = value
        
        config["environment_variables"] = env_vars
        
        return config
    
    def save_config(self):
        """Save configuration to file"""
        try:
            # Get configuration from UI
            config = self.collect_config_from_ui()
            
            # Update config path
            self.config_path = self.config_path_entry.get().strip()
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            # Save to file
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=4)
            
            self.status_var.set(f"Configuration saved to {self.config_path}")
            logger.info(f"Saved HPC configuration to {self.config_path}")
            
            # Close dialog
            self.dialog.destroy()
            
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save configuration: {str(e)}")
            logger.error(f"Error saving HPC configuration: {str(e)}")
    
    def test_connection(self):
        """Test connection to HPC system"""
        # Get configuration from UI
        config = self.collect_config_from_ui()
        
        # Use a temporary file for password if using password auth
        password = None
        if not config["use_key_auth"]:
            password = self.password_entry.get()
        
        try:
            # Import HPC connector
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from HPC.hpc_connector import test_connection
            
            # Test connection
            success, message = test_connection({
                "hostname": config["hpc_host"],
                "username": config["hpc_username"],
                "password": password,
                "port": config["hpc_port"],
                "use_key": config["use_key_auth"],
                "key_path": config["key_path"],
                "scheduler": config["scheduler"]
            })
            
            if success:
                messagebox.showinfo("Connection Test", f"Connection successful!\n\n{message}")
                self.status_var.set("Connection test: Success")
            else:
                messagebox.showerror("Connection Test", f"Connection failed!\n\n{message}")
                self.status_var.set("Connection test: Failed")
                
        except Exception as e:
            messagebox.showerror("Connection Test", f"Error during connection test:\n\n{str(e)}")
            self.status_var.set("Connection test: Error")
            logger.error(f"Error testing HPC connection: {str(e)}")


if __name__ == "__main__":
    # Example usage
    root = tk.Tk()
    root.title("HPC Configuration Test")
    root.geometry("800x600")
    
    def open_dialog():
        dialog = HPCConfigDialog(root)
    
    ttk.Button(root, text="Configure HPC", command=open_dialog).pack(pady=20)
    
    root.mainloop()