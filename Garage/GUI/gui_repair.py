#!/usr/bin/env python3

"""
GUI Repair Utility
This script diagnoses and fixes issues with the CFD Workflow Assistant GUI.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
import importlib
import traceback
import json
import time

class GUIRepairer:
    def __init__(self):
        self.issues_found = 0
        self.issues_fixed = 0
        self.root = None
        self.progress = None
        self.log_text = None
        
    def create_ui(self):
        """Create a simple UI to show repair progress"""
        self.root = tk.Tk()
        self.root.title("CFD GUI Repair Utility")
        self.root.geometry("700x500")
        
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill='both', expand=True)
        
        ttk.Label(main_frame, text="CFD Workflow GUI Repair Utility", 
                  font=("Arial", 16, "bold")).pack(pady=(0, 20))
        
        ttk.Label(main_frame, text="This utility will diagnose and fix issues with the CFD Workflow GUI").pack(pady=(0, 20))
        
        progress_frame = ttk.LabelFrame(main_frame, text="Progress")
        progress_frame.pack(fill='x', pady=10)
        
        self.progress = ttk.Progressbar(progress_frame, length=600, mode="determinate")
        self.progress.pack(padx=10, pady=10, fill='x')
        
        log_frame = ttk.LabelFrame(main_frame, text="Diagnostic Log")
        log_frame.pack(fill='both', expand=True, pady=10)
        
        self.log_text = tk.Text(log_frame, height=15, width=80)
        self.log_text.pack(padx=10, pady=10, fill='both', expand=True)
        scrollbar = ttk.Scrollbar(self.log_text, command=self.log_text.yview)
        scrollbar.pack(side='right', fill='y')
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=10)
        
        ttk.Button(button_frame, text="Start Repair", 
                   command=self.run_all_repairs).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Exit", 
                   command=self.root.quit).pack(side='right', padx=5)
        
        self.log("Repair utility initialized")
        self.log("Ready to diagnose and fix GUI issues")
        
    def log(self, message):
        """Add message to the log text widget"""
        if self.log_text:
            self.log_text.config(state='normal')
            self.log_text.insert('end', f"{message}\n")
            self.log_text.see('end')
            self.log_text.config(state='disabled')
        print(message)
        
    def update_progress(self, value):
        """Update the progress bar"""
        if self.progress:
            self.progress['value'] = value
            self.root.update_idletasks()
            
    def run_all_repairs(self):
        """Run all repair functions"""
        try:
            self.log("Starting repair process...")
            self.update_progress(5)
            
            # Check and fix basic structure
            self.check_directory_structure()
            self.update_progress(15)
            
            # Fix workflow_utils.py
            fixed = self.fix_workflow_utils()
            self.update_progress(30)
            
            # Fix GUI components
            fixed = self.fix_gui_classes() or fixed
            self.update_progress(50)
            
            # Fix HPC settings
            fixed = self.fix_hpc_settings() or fixed
            self.update_progress(70)
            
            # Fix initialization issues
            fixed = self.fix_initialization_issues() or fixed
            self.update_progress(85)
            
            # Create a fixed launcher
            self.create_fixed_launcher()
            self.update_progress(100)
            
            if fixed:
                self.log("\n✅ Repairs completed successfully!")
                self.log(f"Found {self.issues_found} issues, fixed {self.issues_fixed}")
                self.log("\nPlease restart the application using the new launcher:")
                self.log("python run_fixed_gui.py")
                messagebox.showinfo("Repair Complete", 
                                   "Repairs completed successfully!\nPlease restart the application using: python run_fixed_gui.py")
            else:
                self.log("\n✅ No issues found that needed fixing.")
                self.log("If you're still experiencing problems, please try running:")
                self.log("python run_fixed_gui.py")
        except Exception as e:
            self.log(f"\n❌ Error during repair: {str(e)}")
            self.log(traceback.format_exc())
            messagebox.showerror("Error", f"Error during repair: {str(e)}")
            
    def check_directory_structure(self):
        """Check and create necessary directory structure"""
        self.log("Checking directory structure...")
        
        # Check for gui directory
        gui_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gui")
        if not os.path.exists(gui_dir):
            self.log("Creating missing gui directory")
            os.makedirs(gui_dir)
            self.issues_found += 1
            self.issues_fixed += 1
            
        # Check for config directory
        config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config")
        if not os.path.exists(config_dir):
            self.log("Creating missing config directory")
            os.makedirs(config_dir)
            self.issues_found += 1
            self.issues_fixed += 1
            
        # Check for __init__.py in gui directory
        init_file = os.path.join(gui_dir, "__init__.py")
        if not os.path.exists(init_file):
            self.log("Creating missing __init__.py in gui directory")
            with open(init_file, 'w') as f:
                f.write('"""GUI package for CFD Workflow Assistant"""\n')
            self.issues_found += 1
            self.issues_fixed += 1
            
        self.log("Directory structure check complete")
        
    def fix_workflow_utils(self):
        """Fix issues in workflow_utils.py"""
        self.log("Checking workflow_utils.py...")
        fixed = False
        
        try:
            import workflow_utils
            # Check if critical functions exist
            if not hasattr(workflow_utils, 'load_hpc_settings'):
                self.log("Adding missing load_hpc_settings function")
                
                def load_hpc_settings():
                    """Load HPC settings from config file"""
                    config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config")
                    settings_file = os.path.join(config_dir, "hpc_settings.json")
                    
                    if not os.path.exists(settings_file):
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
                        
                        # Ensure config directory exists
                        os.makedirs(config_dir, exist_ok=True)
                        
                        with open(settings_file, 'w') as f:
                            json.dump(default_settings, f, indent=4)
                        return default_settings
                    
                    try:
                        with open(settings_file, 'r') as f:
                            return json.load(f)
                    except Exception as e:
                        print(f"Error loading HPC settings: {e}")
                        return {"hpc_enabled": False}
                
                # Add the function to workflow_utils
                setattr(workflow_utils, 'load_hpc_settings', load_hpc_settings)
                self.issues_found += 1
                self.issues_fixed += 1
                fixed = True
                
            self.log("workflow_utils.py check complete")
            
        except ImportError:
            self.log("⚠️ Could not import workflow_utils module")
        except Exception as e:
            self.log(f"❌ Error fixing workflow_utils.py: {str(e)}")
            
        return fixed
        
    def fix_gui_classes(self):
        """Fix issues with GUI classes"""
        self.log("Checking GUI classes...")
        fixed = False
        
        try:
            # Check workflow_gui.py in gui directory
            gui_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gui")
            workflow_gui_path = os.path.join(gui_dir, "workflow_gui.py")
            
            if not os.path.exists(workflow_gui_path):
                self.log("Creating missing workflow_gui.py")
                with open(workflow_gui_path, 'w') as f:
                    f.write('''"""
WorkflowGUI - Main GUI class for CFD Workflow Assistant
"""
import os
import tkinter as tk
from tkinter import ttk, messagebox
import json
import threading

class WorkflowGUI:
    """Main GUI class for CFD Workflow Assistant"""
    
    def __init__(self, root):
        """Initialize the GUI"""
        self.root = root
        self.root.title("CFD Workflow Assistant")
        self.root.geometry("1000x700")
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Create main tab
        self.main_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.main_tab, text="Main")
        
        # Create content in main tab
        self.create_main_tab()
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief="sunken", anchor="w")
        self.status_bar.pack(side="bottom", fill="x")
        
        # Additional initialization
        self.initialize_themes()
        
        print("WorkflowGUI initialized successfully")
        
    def create_main_tab(self):
        """Create the main tab content"""
        # Welcome message
        welcome_frame = ttk.Frame(self.main_tab, padding=20)
        welcome_frame.pack(fill="both", expand=True)
        
        ttk.Label(welcome_frame, text="Welcome to CFD Workflow Assistant", 
                 font=("Arial", 16, "bold")).pack(pady=(0, 20))
        
        ttk.Label(welcome_frame, text="This tool helps you set up and run CFD simulations.").pack()
        
        # Settings section
        settings_frame = ttk.LabelFrame(welcome_frame, text="Settings")
        settings_frame.pack(fill="x", padx=20, pady=20)
        
        # Theme settings
        theme_frame = ttk.Frame(settings_frame)
        theme_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Label(theme_frame, text="Theme:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.theme_combo = ttk.Combobox(theme_frame, values=["Default", "Dark"])
        self.theme_combo.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.theme_combo.current(0)
        self.theme_combo.bind("<<ComboboxSelected>>", lambda e: self.change_theme())
        
        # Workflow section
        workflow_frame = ttk.LabelFrame(welcome_frame, text="Workflow Steps")
        workflow_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.workflow_canvas = tk.Canvas(workflow_frame, height=150)
        self.workflow_canvas.pack(fill="both", expand=True, padx=10, pady=10)
        
        self._create_workflow_steps()
        
    def initialize_themes(self):
        """Initialize theme settings"""
        self.themes = {
            "Default": {
                "bg": "#f0f0f0",
                "fg": "#000000",
                "accent": "#007acc"
            },
            "Dark": {
                "bg": "#2d2d2d",
                "fg": "#ffffff",
                "accent": "#007acc"
            }
        }
    
    def change_theme(self):
        """Change the application theme"""
        theme_name = self.theme_combo.get()
        theme = self.themes.get(theme_name, self.themes["Default"])
        
        style = ttk.Style()
        if theme_name == "Dark":
            self.root.configure(background=theme["bg"])
            style.configure(".", background=theme["bg"], foreground=theme["fg"])
            style.configure("TLabel", background=theme["bg"], foreground=theme["fg"])
            style.configure("TFrame", background=theme["bg"])
            style.configure("TButton", background=theme["accent"])
            style.configure("TNotebook", background=theme["bg"])
            style.map("TNotebook.Tab", background=[("selected", theme["accent"])])
        else:
            style.theme_use("default")
            
        self.status_var.set(f"Theme changed to {theme_name}")
    
    def _create_workflow_steps(self):
        """Create visual workflow steps"""
        self.workflow_steps = [
            {"name": "NX Model", "status": "pending"},
            {"name": "Mesh", "status": "pending"},
            {"name": "CFD", "status": "pending"},
            {"name": "Results", "status": "pending"}
        ]
        
        # Draw workflow steps
        x_offset = 50
        for i, step in enumerate(self.workflow_steps):
            # Draw circle
            x = x_offset + i * 200
            y = 75
            circle_id = self.workflow_canvas.create_oval(x-30, y-30, x+30, y+30, 
                                                      fill="#f0f0f0", outline="#007acc", width=2)
            # Draw text
            text_id = self.workflow_canvas.create_text(x, y, text=step["name"])
            
            # Store IDs in the step dict
            step["circle_id"] = circle_id
            step["text_id"] = text_id
            
            # Draw connecting line if not the first step
            if i > 0:
                prev_x = x_offset + (i-1) * 200 + 30
                line_id = self.workflow_canvas.create_line(prev_x, y, x-30, y, 
                                                        fill="#007acc", width=2)
                step["line_id"] = line_id
    
    def update_step_status(self, step_index, status):
        """Update the status of a workflow step"""
        if step_index < 0 or step_index >= len(self.workflow_steps):
            return
            
        step = self.workflow_steps[step_index]
        step["status"] = status
        
        # Update visual representation
        color = "#f0f0f0"  # default
        if status == "complete":
            color = "#4caf50"  # green
        elif status == "active":
            color = "#2196f3"  # blue
        elif status == "error":
            color = "#f44336"  # red
            
        self.workflow_canvas.itemconfig(step["circle_id"], fill=color)

    def setup_hpc_tab(self):
        """Set up the HPC tab if not already created"""
        # Check if HPC tab already exists
        for tab_id in self.notebook.tabs():
            if self.notebook.tab(tab_id, "text") == "HPC":
                return  # Tab already exists
        
        # Create HPC tab
        self.hpc_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.hpc_tab, text="HPC")
        
        # Create content in HPC tab
        self.create_hpc_tab_content()
        
    def create_hpc_tab_content(self):
        """Create the HPC tab content"""
        # HPC Connection settings
        settings_frame = ttk.LabelFrame(self.hpc_tab, text="HPC Connection Settings")
        settings_frame.pack(fill="x", padx=20, pady=20)
        
        # HPC Host
        host_frame = ttk.Frame(settings_frame)
        host_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(host_frame, text="HPC Host:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.hpc_host = ttk.Entry(host_frame, width=30)
        self.hpc_host.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # Username
        ttk.Label(host_frame, text="Username:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.hpc_username = ttk.Entry(host_frame, width=30)
        self.hpc_username.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        # Port
        ttk.Label(host_frame, text="Port:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.hpc_port = ttk.Entry(host_frame, width=10)
        self.hpc_port.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        self.hpc_port.insert(0, "22")
        
        # Remote directory
        ttk.Label(host_frame, text="Remote Directory:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.hpc_remote_dir = ttk.Entry(host_frame, width=40)
        self.hpc_remote_dir.grid(row=3, column=1, padx=5, pady=5, sticky="w")
        
        # Authentication
        auth_frame = ttk.Frame(settings_frame)
        auth_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Label(auth_frame, text="Authentication:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.auth_method = tk.StringVar(value="password")
        ttk.Radiobutton(auth_frame, text="Password", variable=self.auth_method, value="password").grid(row=0, column=1, padx=5, pady=5, sticky="w")
        ttk.Radiobutton(auth_frame, text="SSH Key", variable=self.auth_method, value="key").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        
        # SSH Key path
        ttk.Label(auth_frame, text="SSH Key Path:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.key_path = ttk.Entry(auth_frame, width=40)
        self.key_path.grid(row=1, column=1, columnspan=2, padx=5, pady=5, sticky="w")
        
        # Button frame
        button_frame = ttk.Frame(settings_frame)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Button(button_frame, text="Test Connection", command=self.test_connection).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Save Settings", command=self.save_hpc_settings).pack(side="left", padx=5)
        
        # Load settings
        self.load_hpc_settings()
    
    def load_hpc_settings(self):
        """Load HPC settings from config file"""
        try:
            import workflow_utils
            if hasattr(workflow_utils, 'load_hpc_settings'):
                settings = workflow_utils.load_hpc_settings()
                
                if hasattr(self, 'hpc_host'):
                    self.hpc_host.delete(0, tk.END)
                    self.hpc_host.insert(0, settings.get("hpc_host", ""))
                
                if hasattr(self, 'hpc_username'):
                    self.hpc_username.delete(0, tk.END)
                    self.hpc_username.insert(0, settings.get("hpc_username", ""))
                
                if hasattr(self, 'hpc_port'):
                    self.hpc_port.delete(0, tk.END)
                    self.hpc_port.insert(0, str(settings.get("hpc_port", 22)))
                
                if hasattr(self, 'hpc_remote_dir'):
                    self.hpc_remote_dir.delete(0, tk.END)
                    self.hpc_remote_dir.insert(0, settings.get("hpc_remote_dir", ""))
                
                if hasattr(self, 'auth_method'):
                    self.auth_method.set("key" if settings.get("use_key_auth", False) else "password")
                
                if hasattr(self, 'key_path'):
                    self.key_path.delete(0, tk.END)
                    self.key_path.insert(0, settings.get("key_path", ""))
            else:
                print("Warning: load_hpc_settings function not found in workflow_utils")
        except Exception as e:
            print(f"Error loading HPC settings: {e}")
    
    def save_hpc_settings(self):
        """Save HPC settings to config file"""
        try:
            settings = {
                "hpc_enabled": True,
                "hpc_host": self.hpc_host.get(),
                "hpc_username": self.hpc_username.get(),
                "hpc_port": int(self.hpc_port.get()),
                "hpc_remote_dir": self.hpc_remote_dir.get(),
                "use_key_auth": self.auth_method.get() == "key",
                "key_path": self.key_path.get(),
                "visible_in_gui": True
            }
            
            config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config")
            os.makedirs(config_dir, exist_ok=True)
            
            settings_file = os.path.join(config_dir, "hpc_settings.json")
            with open(settings_file, 'w') as f:
                json.dump(settings, f, indent=4)
            
            messagebox.showinfo("Settings Saved", "HPC settings saved successfully")
            self.status_var.set("HPC settings saved")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save HPC settings: {str(e)}")
    
    def test_connection(self):
        """Test connection to HPC"""
        try:
            host = self.hpc_host.get()
            username = self.hpc_username.get()
            port = int(self.hpc_port.get())
            auth_method = self.auth_method.get()
            key_path = self.key_path.get() if auth_method == "key" else None
            
            # Try to import paramiko
            try:
                import paramiko
            except ImportError:
                messagebox.showerror("Missing Dependency", 
                                    "The paramiko module is required for SSH connections.\n"
                                    "Install it with: pip install paramiko")
                return
                
            self.status_var.set("Testing connection...")
            
            # Define a function to test the connection in a separate thread
            def do_test_connection():
                try:
                    client = paramiko.SSHClient()
                    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    
                    if auth_method == "key" and key_path:
                        key = paramiko.RSAKey.from_private_key_file(key_path)
                        client.connect(hostname=host, port=port, username=username, pkey=key, timeout=10)
                    else:
                        # For password auth, this will trigger a password prompt
                        # which we can't handle in a background thread
                        messagebox.showinfo("Password Required", 
                                         "Password authentication requires interactive input.\n"
                                         "This test will only check if the host is reachable.")
                        import socket
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.settimeout(5)
                        result = sock.connect_ex((host, port))
                        sock.close()
                        
                        if result != 0:
                            raise Exception(f"Could not connect to {host}:{port}")
                        return
                    
                    # Run a simple command
                    stdin, stdout, stderr = client.exec_command("hostname")
                    result = stdout.read().decode().strip()
                    
                    # Update GUI from main thread
                    self.root.after(0, lambda: messagebox.showinfo("Connection Success", 
                                                                f"Connected to HPC system: {result}"))
                    self.root.after(0, lambda: self.status_var.set(f"Connected to {result}"))
                    
                    # Close connection
                    client.close()
                except Exception as e:
                    # Update GUI from main thread
                    self.root.after(0, lambda: messagebox.showerror("Connection Error", 
                                                                  f"Failed to connect to HPC: {str(e)}"))
                    self.root.after(0, lambda: self.status_var.set("Connection failed"))
            
            # Start the connection test in a separate thread
            threading.Thread(target=do_test_connection, daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error setting up connection test: {str(e)}")
''')
                self.issues_found += 1
                self.issues_fixed += 1
                fixed = True
                
            # Create missing __init__.py in gui directory
            gui_init_path = os.path.join(gui_dir, "__init__.py") 
            if not os.path.exists(gui_init_path):
                self.log("Creating missing __init__.py in gui directory")
                with open(gui_init_path, 'w') as f:
                    f.write('"""GUI package for CFD Workflow Assistant"""\n')
                self.issues_found += 1
                self.issues_fixed += 1
                fixed = True
                
            self.log("GUI classes check complete")
            
        except Exception as e:
            self.log(f"❌ Error fixing GUI classes: {str(e)}")
            
        return fixed
        
    def fix_hpc_settings(self):
        """Fix issues with HPC settings"""
        self.log("Checking HPC settings...")
        fixed = False
        
        try:
            # Check HPC settings file
            config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config")
            os.makedirs(config_dir, exist_ok=True)
            
            settings_file = os.path.join(config_dir, "hpc_settings.json")
            if not os.path.exists(settings_file):
                self.log("Creating missing HPC settings file")
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
                
                with open(settings_file, 'w') as f:
                    json.dump(default_settings, f, indent=4)
                    
                self.issues_found += 1
                self.issues_fixed += 1
                fixed = True
                
            self.log("HPC settings check complete")
            
        except Exception as e:
            self.log(f"❌ Error fixing HPC settings: {str(e)}")
            
        return fixed
        
    def fix_initialization_issues(self):
        """Fix issues with GUI initialization"""
        self.log("Checking initialization issues...")
        fixed = False
        
        try:
            # Check patch.py for proper initialization
            patch_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "patch.py")
            if os.path.exists(patch_file):
                with open(patch_file, 'r') as f:
                    content = f.read()
                
                # Check for triple backticks that might cause syntax errors
                if '```' in content:
                    self.log("Fixing syntax errors in patch.py")
                    content = content.replace('```', '# ```')
                    with open(patch_file, 'w') as f:
                        f.write(content)
                    self.issues_found += 1
                    self.issues_fixed += 1
                    fixed = True
                
            self.log("Initialization issues check complete")
            
        except Exception as e:
            self.log(f"❌ Error fixing initialization issues: {str(e)}")
            
        return fixed
        
    def create_fixed_launcher(self):
        """Create a fixed launcher script"""
        self.log("Creating fixed launcher...")
        
        launcher_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "run_fixed_gui.py")
        with open(launcher_file, 'w') as f:
            f.write('''#!/usr/bin/env python3
"""
Fixed GUI Launcher
This script launches the CFD Workflow Assistant with proper initialization and error handling.
"""

import os
import sys
import tkinter as tk
import traceback

def setup_environment():
    """Set up the environment for the GUI"""
    # Add current directory to path
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    # Create necessary directories
    gui_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gui")
    config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config")
    
    os.makedirs(gui_dir, exist_ok=True)
    os.makedirs(config_dir, exist_ok=True)
    
    # Create __init__.py in gui directory if it doesn't exist
    init_file = os.path.join(gui_dir, "__init__.py")
    if not os.path.exists(init_file):
        with open(init_file, 'w') as f:
            f.write('"""GUI package for CFD Workflow Assistant"""\n')
            
    # Create HPC settings file if it doesn't exist
    settings_file = os.path.join(config_dir, "hpc_settings.json")
    if not os.path.exists(settings_file):
        import json
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
        with open(settings_file, 'w') as f:
            json.dump(default_settings, f, indent=4)

def create_error_window(exception, traceback_str):
    """Create an error window to display the exception"""
    error_root = tk.Tk()
    error_root.title("CFD Workflow Assistant - Error")
    error_root.geometry("800x600")
    
    frame = tk.Frame(error_root, padx=20, pady=20)
    frame.pack(fill='both', expand=True)
    
    tk.Label(frame, text="An error occurred while starting the application:", 
            font=("Arial", 12, "bold")).pack(pady=(0, 10), anchor='w')
    
    tk.Label(frame, text=str(exception), fg="red", 
            font=("Arial", 12)).pack(pady=(0, 20), anchor='w')
    
    tk.Label(frame, text="Traceback:", font=("Arial", 10, "bold")).pack(anchor='w')
    
    text = tk.Text(frame, height=20, width=90, wrap='word')
    text.pack(pady=10, fill='both', expand=True)
    text.insert('1.0', traceback_str)
    text.config(state='disabled')
    
    scrollbar = tk.Scrollbar(text)
    scrollbar.pack(side='right', fill='y')
    text.config(yscrollcommand=scrollbar.set)
    scrollbar.config(command=text.yview)
    
    tk.Label(frame, text="Please fix the above issue and restart the application.").pack(pady=10, anchor='w')
    
    btn_frame = tk.Frame(frame)
    btn_frame.pack(fill='x', pady=10)
    
    tk.Button(btn_frame, text="Exit", command=error_root.destroy).pack(side='right')
    tk.Button(btn_frame, text="Run Repair Tool", 
             command=lambda: (os.system(f"{sys.executable} {os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gui_repair.py')}"), 
                             error_root.destroy())).pack(side='right', padx=10)
    
    error_root.mainloop()

def main():
    """Main entry point"""
    try:
        # Setup environment
        setup_environment()
        
        # Import necessary modules
        from gui.workflow_gui import WorkflowGUI
        
        # Create root window
        root = tk.Tk()
        root.title("CFD Workflow Assistant")
        root.geometry("1000x700")
        
        # Initialize GUI
        app = WorkflowGUI(root)
        
        # Set up HPC tab if it exists
        if hasattr(app, 'setup_hpc_tab'):
            app.setup_hpc_tab()
        
        # Start the main loop
        root.mainloop()
        
    except Exception as e:
        # Show error dialog
        create_error_window(e, traceback.format_exc())

if __name__ == "__main__":
    main()
''')
        self.log("Fixed launcher created: run_fixed_gui.py")

def main():
    """Main entry point"""
    repairer = GUIRepairer()
    repairer.create_ui()
    repairer.root.mainloop()

if __name__ == "__main__":
    main()
