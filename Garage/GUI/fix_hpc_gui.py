#!/usr/bin/env python3

"""
Script to fix HPC GUI integration issues
"""

import os
import sys
import json
import importlib
import traceback

def ensure_hpc_profiles():
    """Create default HPC settings if they don't exist"""
    # Try in both possible locations
    config_dirs = [
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Config"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "config")
    ]
    
    settings_created = False
    
    for config_dir in config_dirs:
        # Create config directory if it doesn't exist
        os.makedirs(config_dir, exist_ok=True)
        
        settings_path = os.path.join(config_dir, "hpc_profiles.json")
        
        if not os.path.exists(settings_path):
            print(f"Creating default HPC settings file in {settings_path}...")
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
            
            with open(settings_path, 'w') as f:
                json.dump(default_settings, f, indent=4)
            print("Default HPC settings created successfully")
            settings_created = True
    
    return settings_created

def patch_workflow_gui():
    """Patch the WorkflowGUI class to properly initialize HPC components"""
    try:
        # Import the necessary modules to patch - corrected to import from main
        import main
        WorkflowGUI = main.WorkflowGUI
        
        # Check if the class already has the required HPC methods
        has_hpc_init = hasattr(WorkflowGUI, "initialize_hpc_components")
        has_hpc_tab = hasattr(WorkflowGUI, "create_hpc_tab")
        has_hpc_test = hasattr(WorkflowGUI, "test_hpc_connection")
        has_hpc_save = hasattr(WorkflowGUI, "save_hpc_profiles")
        
        if has_hpc_init and has_hpc_tab and has_hpc_test and has_hpc_save:
            print("WorkflowGUI already has HPC methods. No patching needed.")
            return False
        
        # Define the HPC methods
        def initialize_hpc_components(self):
            """Initialize HPC components in the GUI"""
            try:
                import importlib
                import sys
                
                # Try to import workflow_utils from different possible locations
                workflow_utils = None
                try:
                    import workflow_utils
                except ImportError:
                    try:
                        from Utils import workflow_utils
                    except ImportError:
                        print("Warning: Could not import workflow_utils. Creating minimal version.")
                        # Create a minimal module if not found
                        class MinimalWorkflowUtils:
                            @staticmethod
                            def load_hpc_profiles():
                                """Minimal implementation to load HPC settings"""
                                import json
                                import os
                                
                                settings_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                                           "Config", "hpc_profiles.json")
                                
                                if not os.path.exists(settings_path):
                                    return {
                                        "hpc_enabled": True,
                                        "visible_in_gui": True,
                                        "hpc_host": "localhost",
                                        "hpc_username": "",
                                        "hpc_port": 22
                                    }
                                    
                                with open(settings_path, 'r') as f:
                                    return json.load(f)
                        workflow_utils = MinimalWorkflowUtils()
                
                # Load HPC settings
                self.hpc_profiles = workflow_utils.load_hpc_profiles()
                
                # Only proceed if HPC should be visible in GUI
                if not self.hpc_profiles.get("visible_in_gui", True):
                    print("HPC GUI components disabled by configuration")
                    return
                
                # Create HPC tab or components
                self.create_hpc_tab()
                
                print("HPC components initialized successfully")
            except Exception as e:
                print(f"Error initializing HPC components: {e}")
                print(traceback.format_exc())
                
        def create_hpc_tab(self):
            """Create the HPC tab in the GUI"""
            try:
                # Import necessary modules
                import tkinter as tk
                from tkinter import ttk
                
                # Create HPC tab if not already created
                if not hasattr(self, 'notebook') or not self.notebook:
                    print("Notebook widget not found, cannot add HPC tab")
                    return
                
                # Check if HPC tab already exists
                for tab_id in self.notebook.tabs():
                    tab_text = self.notebook.tab(tab_id, "text")
                    if tab_text == "HPC":
                        print("HPC tab already exists")
                        return
                
                # Create HPC tab
                hpc_frame = ttk.Frame(self.notebook)
                self.notebook.add(hpc_frame, text="HPC")
                
                # Add HPC settings to the tab
                ttk.Label(hpc_frame, text="HPC Settings", font=("Arial", 12, "bold")).grid(row=0, column=0, padx=10, pady=10, sticky="w")
                
                # HPC host
                ttk.Label(hpc_frame, text="HPC Host:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
                self.hpc_host_entry = ttk.Entry(hpc_frame, width=30)
                self.hpc_host_entry.grid(row=1, column=1, padx=10, pady=5, sticky="w")
                self.hpc_host_entry.insert(0, self.hpc_profiles.get("hpc_host", "localhost"))
                
                # HPC username
                ttk.Label(hpc_frame, text="Username:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
                self.hpc_username_entry = ttk.Entry(hpc_frame, width=30)
                self.hpc_username_entry.grid(row=2, column=1, padx=10, pady=5, sticky="w")
                self.hpc_username_entry.insert(0, self.hpc_profiles.get("hpc_username", ""))
                
                # HPC port
                ttk.Label(hpc_frame, text="Port:").grid(row=3, column=0, padx=10, pady=5, sticky="w")
                self.hpc_port_entry = ttk.Entry(hpc_frame, width=10)
                self.hpc_port_entry.grid(row=3, column=1, padx=10, pady=5, sticky="w")
                self.hpc_port_entry.insert(0, str(self.hpc_profiles.get("hpc_port", 22)))
                
                # HPC remote dir
                ttk.Label(hpc_frame, text="Remote Directory:").grid(row=4, column=0, padx=10, pady=5, sticky="w")
                self.hpc_remote_dir_entry = ttk.Entry(hpc_frame, width=30)
                self.hpc_remote_dir_entry.grid(row=4, column=1, padx=10, pady=5, sticky="w")
                self.hpc_remote_dir_entry.insert(0, self.hpc_profiles.get("hpc_remote_dir", "/home/user/cfd_projects"))
                
                # Authentication options
                ttk.Label(hpc_frame, text="Authentication:").grid(row=5, column=0, padx=10, pady=5, sticky="w")
                self.auth_method_var = tk.StringVar()
                self.auth_method_var.set("password" if not self.hpc_profiles.get("use_key_auth", False) else "key")
                
                auth_frame = ttk.Frame(hpc_frame)
                auth_frame.grid(row=5, column=1, padx=10, pady=5, sticky="w")
                
                ttk.Radiobutton(auth_frame, text="Password", value="password", variable=self.auth_method_var, 
                               command=self.toggle_auth_type).grid(row=0, column=0, padx=5)
                ttk.Radiobutton(auth_frame, text="SSH Key", value="key", variable=self.auth_method_var,
                               command=self.toggle_auth_type).grid(row=0, column=1, padx=5)
                
                # Password entry
                self.password_frame = ttk.Frame(hpc_frame)
                self.password_frame.grid(row=6, column=0, columnspan=2, padx=10, pady=5, sticky="w")
                
                ttk.Label(self.password_frame, text="Password:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
                self.password_entry = ttk.Entry(self.password_frame, show="*", width=30)
                self.password_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
                
                # SSH key path
                self.key_frame = ttk.Frame(hpc_frame)
                self.key_frame.grid(row=7, column=0, columnspan=2, padx=10, pady=5, sticky="w")
                
                ttk.Label(self.key_frame, text="Key Path:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
                self.key_path_entry = ttk.Entry(self.key_frame, width=30)
                self.key_path_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
                self.key_path_entry.insert(0, self.hpc_profiles.get("key_path", ""))
                
                self.browse_key_button = ttk.Button(self.key_frame, text="Browse", 
                                                  command=self.browse_key_file)
                self.browse_key_button.grid(row=0, column=2, padx=5, pady=5)
                
                # Show/hide authentication based on selection
                self.toggle_auth_type()
                
                # Test connection and save settings
                button_frame = ttk.Frame(hpc_frame)
                button_frame.grid(row=8, column=0, columnspan=2, padx=10, pady=10)
                
                ttk.Button(button_frame, text="Test Connection", command=self.test_hpc_connection).grid(row=0, column=0, padx=5)
                ttk.Button(button_frame, text="Save Settings", command=self.save_hpc_profiles).grid(row=0, column=1, padx=5)
                
                # Connection status
                self.connection_status = ttk.Label(hpc_frame, text="Not connected")
                self.connection_status.grid(row=9, column=0, columnspan=2, padx=10, pady=5, sticky="w")
                
                print("HPC tab created successfully")
                
            except Exception as e:
                print(f"Error creating HPC tab: {e}")
                print(traceback.format_exc())
                
        def toggle_auth_type(self):
            """Toggle between password and SSH key authentication"""
            if self.auth_method_var.get() == "password":
                self.password_frame.grid()
                self.key_frame.grid_remove()
            else:
                self.password_frame.grid_remove()
                self.key_frame.grid()
                
        def browse_key_file(self):
            """Open file dialog to browse for SSH key file"""
            from tkinter import filedialog
            
            key_path = filedialog.askopenfilename(
                title="Select SSH Key File",
                filetypes=[("SSH Key Files", "*.pem *.ppk *.key"), ("All Files", "*.*")]
            )
            
            if key_path:
                self.key_path_entry.delete(0, tk.END)
                self.key_path_entry.insert(0, key_path)
                
        def test_hpc_connection(self):
            """Test connection to HPC system"""
            from tkinter import messagebox
            
            # Get connection details
            host = self.hpc_host_entry.get()
            username = self.hpc_username_entry.get()
            port_str = self.hpc_port_entry.get()
            use_key = self.auth_method_var.get() == "key"
            key_path = self.key_path_entry.get() if use_key else None
            
            # Simple validation
            if not host:
                messagebox.showerror("Validation Error", "HPC host cannot be empty")
                return
                
            if not username:
                messagebox.showerror("Validation Error", "Username cannot be empty")
                return
                
            try:
                port = int(port_str)
                if port < 1 or port > 65535:
                    raise ValueError("Port must be between 1 and 65535")
            except ValueError:
                messagebox.showerror("Validation Error", "Port must be a valid number between 1 and 65535")
                return
                
            if use_key and not key_path:
                messagebox.showerror("Validation Error", "SSH key path cannot be empty when using key authentication")
                return
                
            # Update status
            self.connection_status.config(text="Testing connection...", foreground="black")
            self.update_idletasks()
            
            # Try to connect
            try:
                # Try to import paramiko
                try:
                    import paramiko
                except ImportError:
                    self.connection_status.config(text="Paramiko SSH library not found", foreground="red")
                    messagebox.showwarning("Missing Dependency", 
                                         "The Paramiko SSH library is required for SSH connections.\n" +
                                         "Please install it using: pip install paramiko")
                    return
                    
                # Set up SSH client
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                
                # Connect
                try:
                    if use_key:
                        client.connect(hostname=host, port=port, username=username, key_filename=key_path, timeout=5)
                    else:
                        password = self.password_entry.get()
                        client.connect(hostname=host, port=port, username=username, password=password, timeout=5)
                    
                    # Test successful
                    self.connection_status.config(text="Connected successfully", foreground="green")
                    messagebox.showinfo("Connection Test", "Successfully connected to HPC system")
                    
                finally:
                    # Always close the client
                    client.close()
                    
            except ImportError as e:
                print(f"Error importing paramiko: {e}")
                self.connection_status.config(text="SSH library error", foreground="red")
                
            except Exception as e:
                print(f"Error connecting to HPC: {e}")
                self.connection_status.config(text="Connection failed", foreground="red")
                messagebox.showerror("Connection Failed", f"Failed to connect: {str(e)}")
        
        def save_hpc_profiles(self):
            """Save HPC settings to config file"""
            try:
                import json
                import tkinter.messagebox as messagebox
                
                # Create settings dict from UI values
                settings = {
                    "hpc_enabled": True,
                    "hpc_host": self.hpc_host_entry.get(),
                    "hpc_username": self.hpc_username_entry.get(),
                    "hpc_port": int(self.hpc_port_entry.get()),
                    "hpc_remote_dir": self.hpc_remote_dir_entry.get(),
                    "use_key_auth": self.auth_method_var.get() == "key",
                    "key_path": self.key_path_entry.get(),
                    "visible_in_gui": True
                }
                
                # Save to file
                settings_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Config", "hpc_profiles.json")
                os.makedirs(os.path.dirname(settings_path), exist_ok=True)
                
                with open(settings_path, 'w') as f:
                    json.dump(settings, f, indent=4)
                
                messagebox.showinfo("Settings Saved", "HPC settings saved successfully")
            except Exception as e:
                print(f"Error saving HPC settings: {e}")
                print(traceback.format_exc())
                messagebox.showerror("Error", f"Failed to save HPC settings: {str(e)}")
                
        # Patch the WorkflowGUI class with HPC methods
        setattr(WorkflowGUI, "initialize_hpc_components", initialize_hpc_components)
        setattr(WorkflowGUI, "create_hpc_tab", create_hpc_tab)
        setattr(WorkflowGUI, "toggle_auth_type", toggle_auth_type)
        setattr(WorkflowGUI, "browse_key_file", browse_key_file)
        setattr(WorkflowGUI, "test_hpc_connection", test_hpc_connection)
        setattr(WorkflowGUI, "save_hpc_profiles", save_hpc_profiles)
        
        # Patch the __init__ method to call initialize_hpc_components
        original_init = WorkflowGUI.__init__
        
        def patched_init(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            self.initialize_hpc_components()
        
        WorkflowGUI.__init__ = patched_init
        
        print("WorkflowGUI patched with HPC methods")
        return True
        
    except ImportError as e:
        print(f"ImportError while patching WorkflowGUI: {e}")
        print(traceback.format_exc())
        return False
    except Exception as e:
        print(f"Error while patching WorkflowGUI: {e}")
        print(traceback.format_exc())
        return False

def update_workflow_utils():
    """Update workflow_utils.py to include HPC settings loading"""
    try:
        # Try to import workflow_utils
        try:
            from Utils import workflow_utils
            print("workflow_utils.py loaded.")
        except ImportError:
            print("Could not import workflow_utils module. Skipping update.")
            return False
            
        # Check if load_hpc_profiles function already exists
        if hasattr(workflow_utils, "load_hpc_profiles"):
            print("load_hpc_profiles already exists in workflow_utils.")
            return False
            
        # Add the load_hpc_profiles function
        def load_hpc_profiles():
            """Load HPC settings from the config file, creating default settings if not found"""
            import os
            import json
            
            settings_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                       "Config", "hpc_profiles.json")
            
            if not os.path.exists(settings_path):
                print("No HPC settings file found. Creating default settings...")
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
                
                # Ensure Config directory exists
                os.makedirs(os.path.dirname(settings_path), exist_ok=True)
                
                with open(settings_path, 'w') as f:
                    json.dump(default_settings, f, indent=4)
                return default_settings
            
            try:
                with open(settings_path, 'r') as f:
                    settings = json.load(f)
                print("HPC settings loaded successfully")
                # Ensure visibility key exists
                if "visible_in_gui" not in settings:
                    settings["visible_in_gui"] = True
                return settings
            except Exception as e:
                print(f"Error loading HPC settings: {e}")
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
                
        # Add the function to the module
        setattr(workflow_utils, "load_hpc_profiles", load_hpc_profiles)
        print("Added load_hpc_profiles to workflow_utils module")
        return True
        
    except Exception as e:
        print(f"Error updating workflow_utils: {e}")
        print(traceback.format_exc())
        return False

def check_hpc_dependencies():
    """Check if required HPC dependencies are installed"""
    try:
        import paramiko
        print("Paramiko SSH library is installed")
        return True
    except ImportError:
        print("Paramiko SSH library is not installed. HPC functionality will be limited.")
        print("To install paramiko, run: pip install paramiko")
        return False

def main():
    """Main function to fix HPC GUI issues"""
    print("Starting HPC GUI fix...")
    
    # Check dependencies
    check_hpc_dependencies()
    
    # Ensure HPC settings exist
    ensure_hpc_profiles()
    
    # Update workflow_utils
    update_workflow_utils()
    
    # Patch WorkflowGUI
    patch_workflow_gui()
    
    print("HPC GUI fix completed. Please restart the application.")
    print("If the HPC tab still doesn't appear, run 'pip install paramiko' and try again.")

if __name__ == "__main__":
    main()