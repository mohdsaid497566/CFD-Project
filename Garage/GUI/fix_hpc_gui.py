#!/usr/bin/env python3

"""
Script to fix HPC GUI integration issues
"""

import os
import sys
import json
import importlib
import traceback

def ensure_hpc_settings():
    """Create default HPC settings if they don't exist"""
    settings_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config", "hpc_settings.json")
    
    # Create config directory if it doesn't exist
    os.makedirs(os.path.dirname(settings_path), exist_ok=True)
    
    if not os.path.exists(settings_path):
        print("Creating default HPC settings file...")
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
        return True
    else:
        print("HPC settings file already exists")
        return False

def patch_workflow_gui():
    """Patch the WorkflowGUI class to properly initialize HPC components"""
    try:
        from gui.workflow_gui import WorkflowGUI
        
        # Check if the class already has the required HPC methods
        has_hpc_init = hasattr(WorkflowGUI, "initialize_hpc_components")
        has_hpc_tab = hasattr(WorkflowGUI, "create_hpc_tab")
        has_hpc_test = hasattr(WorkflowGUI, "test_hpc_connection")
        has_hpc_save = hasattr(WorkflowGUI, "save_hpc_settings")
        
        if has_hpc_init and has_hpc_tab and has_hpc_test and has_hpc_save:
            print("WorkflowGUI already has HPC methods. No patching needed.")
            return False
        
        # Import the necessary modules to patch
        from gui import workflow_gui
        
        # Define the HPC methods
        def initialize_hpc_components(self):
            """Initialize HPC components in the GUI"""
            try:
                import workflow_utils
                
                # Load HPC settings
                self.hpc_settings = workflow_utils.load_hpc_settings()
                
                # Only proceed if HPC should be visible in GUI
                if not self.hpc_settings.get("visible_in_gui", True):
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
                self.hpc_host_entry.insert(0, self.hpc_settings.get("hpc_host", "localhost"))
                
                # HPC username
                ttk.Label(hpc_frame, text="Username:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
                self.hpc_username_entry = ttk.Entry(hpc_frame, width=30)
                self.hpc_username_entry.grid(row=2, column=1, padx=10, pady=5, sticky="w")
                self.hpc_username_entry.insert(0, self.hpc_settings.get("hpc_username", ""))
                
                # HPC port
                ttk.Label(hpc_frame, text="Port:").grid(row=3, column=0, padx=10, pady=5, sticky="w")
                self.hpc_port_entry = ttk.Entry(hpc_frame, width=10)
                self.hpc_port_entry.grid(row=3, column=1, padx=10, pady=5, sticky="w")
                self.hpc_port_entry.insert(0, str(self.hpc_settings.get("hpc_port", 22)))
                
                # Remote directory
                ttk.Label(hpc_frame, text="Remote Directory:").grid(row=4, column=0, padx=10, pady=5, sticky="w")
                self.hpc_remote_dir_entry = ttk.Entry(hpc_frame, width=40)
                self.hpc_remote_dir_entry.grid(row=4, column=1, padx=10, pady=5, sticky="w")
                self.hpc_remote_dir_entry.insert(0, self.hpc_settings.get("hpc_remote_dir", "/home/user/cfd_projects"))
                
                # Authentication method
                ttk.Label(hpc_frame, text="Authentication:").grid(row=5, column=0, padx=10, pady=5, sticky="w")
                self.auth_method_var = tk.StringVar(value="password" if not self.hpc_settings.get("use_key_auth", False) else "key")
                ttk.Radiobutton(hpc_frame, text="Password", variable=self.auth_method_var, value="password").grid(row=5, column=1, padx=10, pady=5, sticky="w")
                ttk.Radiobutton(hpc_frame, text="SSH Key", variable=self.auth_method_var, value="key").grid(row=5, column=2, padx=10, pady=5, sticky="w")
                
                # SSH key path
                ttk.Label(hpc_frame, text="SSH Key Path:").grid(row=6, column=0, padx=10, pady=5, sticky="w")
                self.key_path_entry = ttk.Entry(hpc_frame, width=40)
                self.key_path_entry.grid(row=6, column=1, columnspan=2, padx=10, pady=5, sticky="w")
                self.key_path_entry.insert(0, self.hpc_settings.get("key_path", ""))
                
                # Test connection button
                ttk.Button(hpc_frame, text="Test Connection", command=self.test_hpc_connection).grid(row=7, column=0, padx=10, pady=10, sticky="w")
                
                # Save settings button
                ttk.Button(hpc_frame, text="Save Settings", command=self.save_hpc_settings).grid(row=7, column=1, padx=10, pady=10, sticky="w")
                
                print("HPC tab created successfully")
            except Exception as e:
                print(f"Error creating HPC tab: {e}")
                print(traceback.format_exc())
        
        def test_hpc_connection(self):
            """Test connection to HPC system"""
            try:
                import paramiko
                import tkinter.messagebox as messagebox
                
                host = self.hpc_host_entry.get()
                username = self.hpc_username_entry.get()
                port = int(self.hpc_port_entry.get())
                
                # Create SSH client
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                
                try:
                    # Connect based on authentication method
                    if self.auth_method_var.get() == "key":
                        key_path = self.key_path_entry.get()
                        key = paramiko.RSAKey.from_private_key_file(key_path)
                        client.connect(hostname=host, port=port, username=username, pkey=key, timeout=10)
                    else:
                        # This will prompt for password
                        client.connect(hostname=host, port=port, username=username, timeout=10)
                        
                    # Run a simple command
                    stdin, stdout, stderr = client.exec_command("hostname")
                    result = stdout.read().decode().strip()
                    
                    messagebox.showinfo("Connection Success", f"Connected to HPC system: {result}")
                    
                    # Close connection
                    client.close()
                except Exception as e:
                    messagebox.showerror("Connection Error", f"Failed to connect to HPC: {str(e)}")
                    
            except ImportError:
                messagebox.showerror("Module Error", "Paramiko SSH module not installed. Install using: pip install paramiko")
            except Exception as e:
                messagebox.showerror("Error", f"An unexpected error occurred: {str(e)}")
        
        def save_hpc_settings(self):
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
                settings_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "hpc_settings.json")
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
        setattr(WorkflowGUI, "test_hpc_connection", test_hpc_connection)
        setattr(WorkflowGUI, "save_hpc_settings", save_hpc_settings)
        
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
        return False
    except Exception as e:
        print(f"Error while patching WorkflowGUI: {e}")
        print(traceback.format_exc())
        return False

def update_workflow_utils():
    """Update workflow_utils.py to include HPC settings loading"""
    try:
        import workflow_utils
        
        # Check if workflow_utils already has load_hpc_settings
        if hasattr(workflow_utils, "load_hpc_settings"):
            print("workflow_utils already has load_hpc_settings. No update needed.")
            return False
        
        # Define the load_hpc_settings function
        def load_hpc_settings():
            """Load HPC settings from the config file, creating default settings if not found"""
            import os
            import json
            
            settings_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config", "hpc_settings.json")
            
            # Create config directory if it doesn't exist
            os.makedirs(os.path.dirname(settings_path), exist_ok=True)
            
            if not os.path.exists(settings_path):
                print("Creating default HPC settings file...")
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
        
        # Add the function to workflow_utils
        setattr(workflow_utils, "load_hpc_settings", load_hpc_settings)
        
        print("workflow_utils updated with load_hpc_settings function")
        return True
        
    except ImportError as e:
        print(f"ImportError while updating workflow_utils: {e}")
        return False
    except Exception as e:
        print(f"Error while updating workflow_utils: {e}")
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
    ensure_hpc_settings()
    
    # Update workflow_utils
    update_workflow_utils()
    
    # Patch WorkflowGUI
    patch_workflow_gui()
    
    print("HPC GUI fix completed. Please restart the application.")
    print("If the HPC tab still doesn't appear, run 'pip install paramiko' and try again.")

if __name__ == "__main__":
    main()
