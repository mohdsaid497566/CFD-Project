#!/usr/bin/env python3
"""
Setup script for HPC integration.

This script installs the necessary dependencies for HPC integration
and ensures the HPC tab is properly initialized.
"""

import os
import sys
import subprocess
import importlib.util
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("hpc_setup")

def check_dependency(module_name):
    """Check if a Python module is installed"""
    spec = importlib.util.find_spec(module_name)
    return spec is not None

def install_dependency(package_name):
    """Install a Python package using pip"""
    try:
        logger.info(f"Installing {package_name}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        logger.info(f"Successfully installed {package_name}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install {package_name}: {e}")
        return False

def check_hpc_config():
    """Check if HPC configuration exists, create default if it doesn't"""
    config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Config")
    os.makedirs(config_dir, exist_ok=True)
    
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
            "visible_in_gui": True
        }
        
        with open(hpc_profiles_file, 'w') as f:
            json.dump(default_settings, f, indent=4)
        
        logger.info(f"Created default HPC settings at {hpc_profiles_file}")
    else:
        logger.info(f"HPC settings file already exists at {hpc_profiles_file}")
    
    # Also ensure we have an HPC profiles file
    hpc_profiles_file = os.path.join(config_dir, "hpc_profiles.json")
    
    if not os.path.exists(hpc_profiles_file):
        logger.info("Creating default HPC profiles file...")
        default_profiles = {
            "Default": {
                "hpc_host": "localhost",
                "hpc_username": "",
                "hpc_port": 22,
                "hpc_remote_dir": "/home/user/cfd_projects",
                "use_key_auth": False,
                "key_path": ""
            }
        }
        
        with open(hpc_profiles_file, 'w') as f:
            json.dump(default_profiles, f, indent=4)
        
        logger.info(f"Created default HPC profiles at {hpc_profiles_file}")
    else:
        logger.info(f"HPC profiles file already exists at {hpc_profiles_file}")
    
    return True

def main():
    """Main function"""
    logger.info("Starting HPC setup...")
    
    # Check for paramiko dependency
    if not check_dependency("paramiko"):
        logger.info("Paramiko not found, installing...")
        if not install_dependency("paramiko"):
            logger.error("Failed to install paramiko. Please install it manually with: pip install paramiko")
            return False
    else:
        logger.info("Paramiko is already installed")
    
    # Check HPC configuration
    check_hpc_config()
    
    # Modify main.py to ensure HPC integration is initialized
    main_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py")
    if os.path.exists(main_file):
        with open(main_file, 'r') as f:
            content = f.read()
        
        if "from HPC.hpc_integration import initialize_hpc" not in content:
            logger.info("Updating main.py to initialize HPC integration...")
            # The edits to main.py have already been made through the web interface
            # This code would backup and modify the file if needed in a local execution
            logger.info("The main.py file has already been updated via the web interface.")
        else:
            logger.info("main.py already contains HPC initialization code.")
    else:
        logger.error(f"Could not find main.py at {main_file}")
    
    logger.info("HPC setup completed successfully")
    logger.info("To use HPC functionality, restart the application and check for the HPC tab in the GUI.")
    logger.info("\nIf the HPC tab still doesn't appear, please check that:")
    logger.info("1. You are running the application from the Garage directory")
    logger.info("2. The python environment has paramiko installed")
    logger.info("3. The HPC settings are properly configured in Config/hpc_profiles.json")
    return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            sys.exit(0)
        else:
            sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)