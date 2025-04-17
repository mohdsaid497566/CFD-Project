#!/usr/bin/env python3
"""
This script checks and fixes the HPC module structure.
Run it once to ensure all modules are properly set up.
"""

import os
import sys
import shutil
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("fix_hpc_structure")

def ensure_directory(path):
    """Ensure a directory exists"""
    if not os.path.exists(path):
        os.makedirs(path)
        logger.info(f"Created directory: {path}")
    return os.path.exists(path)

def ensure_init_file(directory):
    """Ensure an __init__.py file exists in the directory"""
    init_path = os.path.join(directory, "__init__.py")
    if not os.path.exists(init_path):
        with open(init_path, 'w') as f:
            f.write('"""\n')
            f.write(f"Python package initialization for {os.path.basename(directory)}\n")
            f.write('"""\n')
        logger.info(f"Created __init__.py in {directory}")
    return os.path.exists(init_path)

def check_import(module_name):
    """Check if a module can be imported"""
    try:
        __import__(module_name)
        logger.info(f"Successfully imported {module_name}")
        return True
    except ImportError as e:
        logger.error(f"Failed to import {module_name}: {e}")
        return False

def ensure_file_exists(filepath, default_content=None):
    """Ensure a file exists, with optional default content"""
    if not os.path.exists(filepath):
        if default_content:
            with open(filepath, 'w') as f:
                f.write(default_content)
            logger.info(f"Created file with default content: {filepath}")
        else:
            # Create empty file
            open(filepath, 'w').close()
            logger.info(f"Created empty file: {filepath}")
    return os.path.exists(filepath)

def fix_hpc_structure():
    """Check and fix the HPC module structure"""
    # Get base directory
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    garage_dir = base_dir
    
    logger.info(f"Base directory: {base_dir}")
    
    # Ensure Garage directory exists
    if not ensure_directory(garage_dir):
        logger.error(f"Failed to create/confirm Garage directory: {garage_dir}")
        return False
        
    # Ensure Garage/__init__.py exists
    if not ensure_init_file(garage_dir):
        logger.error(f"Failed to create/confirm __init__.py in {garage_dir}")
        return False
    
    # Ensure Garage/HPC directory exists
    hpc_dir = os.path.join(garage_dir, "HPC")
    if not ensure_directory(hpc_dir):
        logger.error(f"Failed to create/confirm HPC directory: {hpc_dir}")
        return False
        
    # Ensure Garage/HPC/__init__.py exists
    if not ensure_init_file(hpc_dir):
        logger.error(f"Failed to create/confirm __init__.py in {hpc_dir}")
        return False
    
    # Ensure Garage/Utils directory exists
    utils_dir = os.path.join(garage_dir, "Utils")
    if not ensure_directory(utils_dir):
        logger.error(f"Failed to create/confirm Utils directory: {utils_dir}")
        return False
        
    # Ensure Garage/Utils/__init__.py exists
    if not ensure_init_file(utils_dir):
        logger.error(f"Failed to create/confirm __init__.py in {utils_dir}")
        return False
    
    # Check if hpc_connector.py exists in the right place
    hpc_connector_path = os.path.join(hpc_dir, "hpc_connector.py")
    if not os.path.exists(hpc_connector_path):
        logger.warning(f"hpc_connector.py not found at {hpc_connector_path}")
        
        # Check if it's in the legacy location
        old_connector_dir = os.path.join(garage_dir, "hpc_connector")
        old_connector_path = os.path.join(old_connector_dir, "__init__.py")
        
        if os.path.exists(old_connector_dir) and os.path.exists(old_connector_path):
            logger.info(f"Found legacy hpc_connector at {old_connector_path}")
            
            # Copy the content to the new location
            with open(old_connector_path, 'r') as f:
                content = f.read()
                
            with open(hpc_connector_path, 'w') as f:
                f.write('"""\n')
                f.write("HPC Connector module - moved from legacy location\n")
                f.write('"""\n\n')
                f.write(content)
                
            logger.info(f"Copied content from {old_connector_path} to {hpc_connector_path}")
        else:
            logger.warning(f"Legacy hpc_connector not found, creating placeholder")
            
            # Create a placeholder hpc_connector.py with HPCJobStatus class
            placeholder_content = '''#!/usr/bin/env python3
"""
HPC Connector module for the Intake CFD Project.

This is a placeholder module providing basic functionality.
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("hpc_connector")

class HPCJobStatus:
    """Job status constants"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"

class HPCJob:
    """
    Placeholder HPC job object
    """
    def __init__(self, job_id=None, name=None, status=None):
        self.id = job_id
        self.name = name or "unnamed_job"
        self.status = status or HPCJobStatus.UNKNOWN
        self.submit_time = None
        self.start_time = None
        self.end_time = None

class HPCConnector:
    """
    Placeholder connector for HPC systems.
    """
    def __init__(self, config=None):
        self.config = config or {}
        self.connected = False
        logger.warning("Using placeholder HPCConnector class")
    
    def connect(self):
        """
        Placeholder connect method
        
        Returns:
            tuple: (success, message)
        """
        logger.warning("Placeholder connect method called")
        return False, "Placeholder HPCConnector - Cannot connect"
        
    def disconnect(self):
        """
        Placeholder disconnect method
        
        Returns:
            bool: Always False for placeholder
        """
        logger.warning("Placeholder disconnect method called")
        return False

def test_connection(config):
    """
    Test connection to HPC system.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        tuple: (success, message)
    """
    logger.warning("Placeholder test_connection function called")
    return False, "Placeholder test_connection - Cannot test connection"
'''
            with open(hpc_connector_path, 'w') as f:
                f.write(placeholder_content)
                
            logger.info(f"Created placeholder hpc_connector.py at {hpc_connector_path}")
    
    # Ensure workflow_utils.py exists
    workflow_utils_path = os.path.join(utils_dir, "workflow_utils.py")
    if not os.path.exists(workflow_utils_path):
        workflow_utils_content = '''#!/usr/bin/env python3
"""
Workflow utilities for Intake CFD Project.

This module provides utility functions for the workflow, 
including HPC integration support.
"""

import os
import sys
import json
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("workflow_utils")

class HPCConnector:
    """
    Simple class representing an HPC Connector.
    This is a placeholder for compatibility with code that expects this class.
    The actual implementation is in Garage.HPC.hpc_connector.
    """
    def __init__(self, config=None):
        self.config = config or {}
        self.connected = False
        
    def connect(self):
        """
        Placeholder for connect method
        
        Returns:
            tuple: (success, message)
        """
        return False, "Placeholder HPCConnector - Use the actual implementation"
        
    def disconnect(self):
        """
        Placeholder for disconnect method
        
        Returns:
            bool: Always False for placeholder
        """
        return False

def load_hpc_settings():
    """
    Load HPC settings from configuration file
    
    Returns:
        dict: HPC settings dictionary
    """
    try:
        # Try to locate the config directory
        base_dir = Path(__file__).resolve().parent.parent
        config_dir = base_dir / "Config"
        
        # Create Config directory if it doesn't exist
        os.makedirs(config_dir, exist_ok=True)
        
        # HPC settings file path
        settings_path = config_dir / "hpc_profiles.json"
        
        # If settings file exists, load it
        if os.path.exists(settings_path):
            with open(settings_path, 'r') as f:
                settings = json.load(f)
                logger.info(f"Loaded HPC settings from {settings_path}")
                return settings
        
        # If not, create default settings
        default_settings = {
            "hpc_host": "localhost",
            "hpc_username": "",
            "hpc_port": 22,
            "use_key_auth": False,
            "key_path": "",
            "hpc_remote_dir": "/home/user/cfd_projects"
        }
        
        # Save default settings
        with open(settings_path, 'w') as f:
            json.dump(default_settings, f, indent=4)
            logger.info(f"Created default HPC settings at {settings_path}")
        
        return default_settings
        
    except Exception as e:
        logger.error(f"Error loading HPC settings: {e}")
        
        # Return minimal default settings if there's an error
        return {
            "hpc_host": "localhost",
            "hpc_username": "",
            "hpc_port": 22
        }

def save_hpc_settings(settings):
    """
    Save HPC settings to configuration file
    
    Args:
        settings: Dictionary with settings to save
        
    Returns:
        bool: True if saved successfully
    """
    try:
        # Try to locate the config directory
        base_dir = Path(__file__).resolve().parent.parent
        config_dir = base_dir / "Config"
        
        # Create Config directory if it doesn't exist
        os.makedirs(config_dir, exist_ok=True)
        
        # HPC settings file path
        settings_path = config_dir / "hpc_profiles.json"
        
        # Save settings
        with open(settings_path, 'w') as f:
            json.dump(settings, f, indent=4)
            logger.info(f"Saved HPC settings to {settings_path}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error saving HPC settings: {e}")
        return False

def patch_workflow_gui(gui_class):
    """
    Patch the WorkflowGUI class with additional HPC functionality
    
    Args:
        gui_class: The WorkflowGUI class to patch
    """
    logger.info(f"Patching {gui_class.__name__} with HPC functionality")
    
    # Make sure the GUI class has update_status method
    if not hasattr(gui_class, 'update_status'):
        def update_status(self, message, show_progress=False):
            """Update status bar message"""
            print(f"Status: {message}")
        
        gui_class.update_status = update_status
        logger.info("Added update_status method to GUI class")
    
    # Make sure the class has a log method
    if not hasattr(gui_class, 'log'):
        def log(self, message):
            """Log a message"""
            print(message)
            
        gui_class.log = log
        logger.info("Added log method to GUI class")
    
    # Return the patched class
    return gui_class
'''
        with open(workflow_utils_path, 'w') as f:
            f.write(workflow_utils_content)
            
        logger.info(f"Created workflow_utils.py at {workflow_utils_path}")
    
    # Check imports
    logger.info("Checking imports...")
    sys.path.insert(0, os.path.dirname(base_dir))
    
    import_checks = [
        "Garage.HPC.hpc_connector",
        "Garage.Utils.workflow_utils"
    ]
    
    all_imports_ok = True
    for module_name in import_checks:
        if not check_import(module_name):
            all_imports_ok = False
    
    if not all_imports_ok:
        logger.warning("Some imports failed. Consider adding parent directory to PYTHONPATH.")
        parent_dir = os.path.dirname(base_dir)
        logger.info(f"Try: export PYTHONPATH={parent_dir}:$PYTHONPATH")
    
    # Add a fix_gui.py script in GUI folder
    gui_dir = os.path.join(garage_dir, "GUI")
    if not ensure_directory(gui_dir):
        logger.error(f"Failed to create/confirm GUI directory: {gui_dir}")
    else:
        ensure_init_file(gui_dir)
        
        fix_gui_path = os.path.join(gui_dir, "fix_hpc_gui.py")
        if not os.path.exists(fix_gui_path):
            fix_gui_content = '''"""
HPC GUI fixes for Intake CFD Project.

This module provides fixes and enhancements for the HPC GUI components.
"""

import os
import sys
import json
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("fix_hpc_gui")

def update_workflow_utils():
    """Update workflow_utils.py with the necessary HPC functions"""
    try:
        from Garage.Utils import workflow_utils
        logger.info("workflow_utils.py loaded.")
        
        # Add load_hpc_settings function if it doesn't exist
        if not hasattr(workflow_utils, 'load_hpc_settings'):
            def load_hpc_settings():
                """
                Load HPC settings from configuration file
                
                Returns:
                    dict: HPC settings dictionary
                """
                try:
                    # Try to locate the config directory
                    base_dir = Path(__file__).resolve().parent.parent
                    config_dir = base_dir / "Config"
                    
                    # Create Config directory if it doesn't exist
                    os.makedirs(config_dir, exist_ok=True)
                    
                    # HPC settings file path
                    settings_path = config_dir / "hpc_profiles.json"
                    
                    # If settings file exists, load it
                    if os.path.exists(settings_path):
                        with open(settings_path, 'r') as f:
                            settings = json.load(f)
                            logger.info(f"Loaded HPC settings from {settings_path}")
                            return settings
                    
                    # If not, create default settings
                    default_settings = {
                        "hpc_host": "localhost",
                        "hpc_username": "",
                        "hpc_port": 22,
                        "use_key_auth": False,
                        "key_path": "",
                        "hpc_remote_dir": "/home/user/cfd_projects"
                    }
                    
                    # Save default settings
                    with open(settings_path, 'w') as f:
                        json.dump(default_settings, f, indent=4)
                        logger.info(f"Created default HPC settings at {settings_path}")
                    
                    return default_settings
                    
                except Exception as e:
                    logger.error(f"Error loading HPC settings: {e}")
                    
                    # Return minimal default settings if there's an error
                    return {
                        "hpc_host": "localhost",
                        "hpc_username": "",
                        "hpc_port": 22
                    }
            
            # Add the function to the module
            workflow_utils.load_hpc_settings = load_hpc_settings
            logger.info("workflow_utils updated with load_hpc_settings function")
        else:
            logger.info("load_hpc_settings already exists in workflow_utils")
        
        return True
    except Exception as e:
        logger.error(f"Error updating workflow_utils: {e}")
        return False

def ensure_hpc_settings():
    """Ensure HPC settings file exists"""
    try:
        # Try to locate the config directory
        base_dir = Path(__file__).resolve().parent.parent
        config_dir = base_dir / "Config"
        
        # Create Config directory if it doesn't exist
        os.makedirs(config_dir, exist_ok=True)
        
        # HPC settings file path
        settings_path = config_dir / "hpc_profiles.json"
        
        # If settings file exists, we're done
        if os.path.exists(settings_path):
            logger.info("HPC settings file already exists")
            return True
        
        # If not, create default settings
        default_settings = {
            "hpc_host": "localhost",
            "hpc_username": "",
            "hpc_port": 22,
            "use_key_auth": False,
            "key_path": "",
            "hpc_remote_dir": "/home/user/cfd_projects"
        }
        
        # Save default settings
        with open(settings_path, 'w') as f:
            json.dump(default_settings, f, indent=4)
            logger.info(f"Created default HPC settings at {settings_path}")
        
        return True
    except Exception as e:
        logger.error(f"Error ensuring HPC settings: {e}")
        return False

def patch_workflow_gui():
    """Patch WorkflowGUI class with HPC methods"""
    try:
        import main
        
        # Add or update HPC methods
        if not hasattr(main.WorkflowGUI, 'get_hpc_config'):
            def get_hpc_config(self):
                """
                Get HPC configuration from UI
                
                Returns:
                    dict: HPC configuration
                """
                # Define a minimal config if fields don't exist
                config = {
                    "hostname": getattr(self, 'hpc_host', "").get() if hasattr(self, 'hpc_host') else "",
                    "username": getattr(self, 'hpc_username', "").get() if hasattr(self, 'hpc_username') else "",
                    "port": int(getattr(self, 'hpc_port', "22").get()) if hasattr(self, 'hpc_port') else 22,
                    "use_key": False,
                    "remote_dir": getattr(self, 'remote_dir', "").get() if hasattr(self, 'remote_dir') else ""
                }
                
                # Add authentication
                if hasattr(self, 'auth_method'):
                    config["use_key"] = self.auth_method.get() == "key"
                    
                    if config["use_key"]:
                        config["key_path"] = getattr(self, 'hpc_key_path', "").get() if hasattr(self, 'hpc_key_path') else ""
                    else:
                        config["password"] = getattr(self, 'hpc_password', "").get() if hasattr(self, 'hpc_password') else ""
                
                return config
            
            main.WorkflowGUI.get_hpc_config = get_hpc_config
        
        logger.info("WorkflowGUI patched with HPC methods")
        return True
    except Exception as e:
        logger.error(f"Error patching WorkflowGUI: {e}")
        return False
'''
            with open(fix_gui_path, 'w') as f:
                f.write(fix_gui_content)
                
            logger.info(f"Created fix_hpc_gui.py at {fix_gui_path}")
    
    # Create Config directory and ensure hpc_profiles.json exists
    config_dir = os.path.join(garage_dir, "Config")
    if not ensure_directory(config_dir):
        logger.error(f"Failed to create/confirm Config directory: {config_dir}")
    else:
        settings_path = os.path.join(config_dir, "hpc_profiles.json")
        if not os.path.exists(settings_path):
            default_settings = {
                "hpc_host": "localhost",
                "hpc_username": "",
                "hpc_port": 22,
                "use_key_auth": False,
                "key_path": "",
                "hpc_remote_dir": "/home/user/cfd_projects"
            }
            
            with open(settings_path, 'w') as f:
                json.dump(default_settings, f, indent=4)
                
            logger.info(f"Created default HPC settings at {settings_path}")
    
    logger.info("HPC structure fix completed")
    return True

if __name__ == "__main__":
    print("Starting HPC structure fix...")
    success = fix_hpc_structure()
    print(f"HPC structure fix completed {'successfully' if success else 'with errors'}")
