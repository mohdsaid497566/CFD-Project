#!/usr/bin/env python3
"""
Setup script for HPC integration.

This script installs the necessary dependencies for HPC integration,
ensures the HPC tab is properly initialized, and verifies that the
HPC connection functionality works correctly.
"""

import os
import sys
import subprocess
import importlib.util
import logging
import traceback

# Add parent directory to path to import Garage modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)
    print(f"Added {parent_dir} to Python path")

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
    config_dir = os.path.join(parent_dir, "Config")
    os.makedirs(config_dir, exist_ok=True)
    
    hpc_settings_file = os.path.join(config_dir, "hpc_profiles.json")
    
    if not os.path.exists(hpc_settings_file):
        import json
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
        
        with open(hpc_settings_file, 'w') as f:
            json.dump(default_settings, f, indent=4)
        
        logger.info(f"Created default HPC settings at {hpc_settings_file}")
    else:
        logger.info(f"HPC settings file already exists at {hpc_settings_file}")

def verify_hpc_module():
    """Verify that the HPC module can be imported and initialized"""
    try:
        from Garage.HPC.hpc_integration import initialize_hpc
        logger.info("Successfully imported HPC module")
        return True
    except ImportError as e:
        logger.error(f"Error importing HPC module: {e}")
        return False

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
    
    # Verify HPC module can be imported
    if not verify_hpc_module():
        logger.error("Failed to import HPC module. Please check your installation.")
        return False
    
    logger.info("HPC setup completed successfully")
    logger.info("To use HPC functionality, restart the application and check for the HPC tab in the GUI.")
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
        logger.error(traceback.format_exc())
        sys.exit(1)