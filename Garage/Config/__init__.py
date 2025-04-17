"""
Configuration management for the Intake CFD Optimization Suite.

This package handles loading, saving, and managing configuration settings
for the application, including user preferences, simulation parameters,
and system settings.
"""

import os
import json

# Default configuration values
DEFAULT_CONFIG = {
    "demo_mode": True,
    "parallel_processes": 4,
    "mesh_size": 20.0,
    "paths": {
        "nx_journal": "C:/Users/Mohammed/Desktop/Intake-CFD-Project/nx/nx_express2.py",
        "gmsh": "./gmsh_process",
        "cfd_solver": "./cfd_solver",
        "results_dir": "cfd_results"
    }
}

# Configuration file path
CONFIG_FILE = "settings.json"

def load_config():
    """Load configuration from file or return defaults if file doesn't exist."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config: {str(e)}")
            return DEFAULT_CONFIG.copy()
    else:
        return DEFAULT_CONFIG.copy()

def save_config(config):
    """Save configuration to file."""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving config: {str(e)}")
        return False

# Load the configuration on module import
config = load_config()

# Define what's available when importing *
__all__ = [
    'config',
    'load_config',
    'save_config',
    'DEFAULT_CONFIG'
]