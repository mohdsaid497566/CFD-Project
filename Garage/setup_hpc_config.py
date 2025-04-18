#!/usr/bin/env python3
"""
Setup HPC Configuration
Create and verify HPC configuration files are in the correct location
"""

import os
import json
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("setup_hpc_config")

def ensure_config_directory():
    """Ensure the Config directory exists"""
    config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Config")
    os.makedirs(config_dir, exist_ok=True)
    logger.info(f"Config directory exists at {config_dir}")
    return config_dir

def check_gui_directory():
    """Check if the GUI/config directory exists and fix any issues"""
    gui_config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "GUI", "config")
    
    # If GUI/config exists but is lowercase, we need to fix references to it
    if os.path.exists(gui_config_dir):
        logger.info(f"GUI/config directory exists at {gui_config_dir}")
        
        # Check for settings files in GUI/config
        settings_file = os.path.join(gui_config_dir, "hpc_profiles.json")
        if os.path.exists(settings_file):
            logger.info(f"Found HPC settings in GUI/config, copying to main Config directory")
            
            # Load settings
            try:
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
                
                # Save to proper location
                config_dir = ensure_config_directory()
                main_settings_file = os.path.join(config_dir, "hpc_profiles.json")
                
                with open(main_settings_file, 'w') as f:
                    json.dump(settings, f, indent=4)
                
                logger.info(f"Copied settings to {main_settings_file}")
            except Exception as e:
                logger.error(f"Error copying settings: {e}")

def create_hpc_profiles(config_dir):
    """Create default HPC settings if they don't exist"""
    hpc_profiles_file = os.path.join(config_dir, "hpc_profiles.json")
    
    if not os.path.exists(hpc_profiles_file):
        logger.info("Creating default HPC settings...")
        default_settings = {
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
            }
        }
        
        with open(hpc_profiles_file, 'w') as f:
            json.dump(default_settings, f, indent=4)
        
        logger.info(f"Created default HPC settings at {hpc_profiles_file}")
        return True
    else:
        # Ensure that visible_in_gui is set to True
        try:
            with open(hpc_profiles_file, 'r') as f:
                settings = json.load(f)
            
            if "visible_in_gui" not in settings or not settings["visible_in_gui"]:
                logger.info("Updating HPC settings to ensure visibility...")
                settings["visible_in_gui"] = True
                
                with open(hpc_profiles_file, 'w') as f:
                    json.dump(settings, f, indent=4)
                
                logger.info(f"Updated HPC settings at {hpc_profiles_file}")
                return True
        except Exception as e:
            logger.error(f"Error updating HPC settings: {e}")
            
        logger.info(f"HPC settings file already exists at {hpc_profiles_file}")
        return False

def create_hpc_profiles(config_dir):
    """Create default HPC profiles if they don't exist"""
    hpc_profiles_file = os.path.join(config_dir, "hpc_profiles.json")
    
    if not os.path.exists(hpc_profiles_file):
        logger.info("Creating default HPC profiles file...")
        default_profiles = {
            "Default": {
                "hostname": "localhost",
                "username": "",
                "port": 22,
                "remote_dir": "/home/user/cfd_projects",
                "use_key": False,
                "key_path": ""
            }
        }
        
        with open(hpc_profiles_file, 'w') as f:
            json.dump(default_profiles, f, indent=4)
        
        logger.info(f"Created default HPC profiles at {hpc_profiles_file}")
        return True
    else:
        logger.info(f"HPC profiles file already exists at {hpc_profiles_file}")
        return False

def check_module_paths():
    """Ensure HPC module can be found in Python path"""
    import sys
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
        logger.info(f"Added current directory to Python path: {current_dir}")
    
    # Check for HPC directory
    hpc_dir = os.path.join(current_dir, "HPC")
    if os.path.exists(hpc_dir) and os.path.isdir(hpc_dir):
        logger.info(f"HPC directory exists at {hpc_dir}")
        
        # Create __init__.py if needed
        init_file = os.path.join(hpc_dir, "__init__.py")
        if not os.path.exists(init_file):
            with open(init_file, 'w') as f:
                f.write("# HPC module initialization\n")
            logger.info(f"Created __init__.py in HPC directory")
    else:
        logger.warning(f"HPC directory not found at {hpc_dir}")

def create_hpc_integration_file():
    """Create or update the HPC integration file"""
    hpc_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "HPC")
    os.makedirs(hpc_dir, exist_ok=True)
    
    integration_file = os.path.join(hpc_dir, "hpc_integration.py")
    
    if not os.path.exists(integration_file):
        logger.info(f"Creating HPC integration file at {integration_file}")
        
        with open(integration_file, 'w') as f:
            f.write("""#!/usr/bin/env python3
\"\"\"
HPC Integration Module
Provides core functionality for HPC integration with the main application
\"\"\"

import os
import sys
import json
import logging
import importlib.util

logger = logging.getLogger("hpc_integration")

def initialize_hpc():
    \"\"\"Initialize HPC functionality\"\"\"
    logger.info("Initializing HPC integration")
    
    # Load HPC settings
    settings = load_hpc_profiles()
    
    if not settings.get("hpc_enabled", False):
        logger.info("HPC functionality is disabled in settings")
        return False
    
    # Check for paramiko
    try:
        import paramiko
        logger.info("Paramiko SSH library is available")
    except ImportError:
        logger.warning("Paramiko SSH library not found. SSH functionality will be limited.")
        logger.warning("Install paramiko using: pip install paramiko")
    
    logger.info("HPC integration initialized successfully")
    return True

def load_hpc_profiles():
    \"\"\"Load HPC settings from the configuration file\"\"\"
    settings_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                               "Config", "hpc_profiles.json")
    
    if not os.path.exists(settings_path):
        logger.warning(f"HPC settings file not found at {settings_path}")
        return {"hpc_enabled": False, "visible_in_gui": False}
    
    try:
        with open(settings_path, 'r') as f:
            settings = json.load(f)
        logger.info(f"Loaded HPC settings from {settings_path}")
        
        # Make sure visibility setting exists
        if "visible_in_gui" not in settings:
            settings["visible_in_gui"] = True
        
        return settings
    except Exception as e:
        logger.error(f"Error loading HPC settings: {e}")
        return {"hpc_enabled": False, "visible_in_gui": False}

def is_hpc_tab_enabled():
    \"\"\"Check if HPC tab should be displayed\"\"\"
    settings = load_hpc_profiles()
    return settings.get("hpc_enabled", False) and settings.get("visible_in_gui", False)
"""
            )
        logger.info(f"Created HPC integration file at {integration_file}")
    else:
        logger.info(f"HPC integration file already exists at {integration_file}")

def update_gui_fix_module():
    """Create or update GUI fix module to ensure it properly patches the GUI"""
    gui_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "GUI")
    fix_file = os.path.join(gui_dir, "fix_hpc_gui.py")
    
    if os.path.exists(fix_file):
        logger.info(f"Backing up existing fix_hpc_gui.py to fix_hpc_gui.py.bak")
        backup_file = fix_file + ".bak"
        try:
            import shutil
            shutil.copy2(fix_file, backup_file)
        except Exception as e:
            logger.error(f"Error backing up fix file: {e}")

def main():
    """Main function to set up HPC configuration"""
    logger.info("Setting up HPC configuration...")
    
    # Check Python paths
    check_module_paths()
    
    # Check if there's a lowercase 'config' directory in GUI that might be causing confusion
    check_gui_directory()
    
    # Ensure Config directory exists
    config_dir = ensure_config_directory()
    
    # Create HPC settings
    create_hpc_profiles(config_dir)
    
    # Create HPC profiles
    create_hpc_profiles(config_dir)
    
    # Create or verify HPC integration file
    create_hpc_integration_file()
    
    # Update GUI fix module
    update_gui_fix_module()
    
    logger.info("HPC configuration setup complete")
    logger.info("To use HPC functionality, restart the application and check for the HPC tab in the GUI.")
    print("\nIf the HPC tab still doesn't appear, please check that:")
    print("1. You are running the application from the Garage directory")
    print("2. The python environment has paramiko installed")
    print("3. The HPC settings are properly configured in Config/hpc_profiles.json")
    return 0

if __name__ == "__main__":
    sys.exit(main())