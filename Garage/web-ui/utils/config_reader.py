import os
import json

class ConfigReader:
    """
    Class to read and write configuration settings for the Intake CFD Project
    """
    def __init__(self, config_path=None):
        """
        Initialize the ConfigReader with an optional config file path
        """
        self.config_path = config_path
        if not self.config_path:
            # Default config path - parent directory's config file
            self.config_path = os.path.abspath(os.path.join(
                os.path.dirname(__file__), 
                '..', '..', 'config.json'
            ))
        
        # Create default config if not exists
        if not os.path.exists(self.config_path):
            self._create_default_config()
    
    def _create_default_config(self):
        """Create a default configuration file"""
        default_config = {
            "runner_length": 150.0,
            "runner_diameter": 35.0,
            "plenum_volume": 2000.0,
            "throttle_diameter": 45.0,
            "runner_taper": 1.0,
            "runner_spacing": 80.0,
            "wall_thickness": 3.0,
            "engine_rpm": 6000,
            "inlet_pressure": 101.3,
            "outlet_pressure": 80.0,
            "inlet_temperature": 298.0
        }
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        
        # Write default config
        with open(self.config_path, 'w') as f:
            json.dump(default_config, f, indent=4)
    
    def get_config(self):
        """
        Read and return the configuration
        """
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # If config file is missing or corrupt, create a new one
            self._create_default_config()
            with open(self.config_path, 'r') as f:
                return json.load(f)
    
    def save_config(self, new_config):
        """
        Save updated configuration
        """
        # Read existing config to preserve any values not in new_config
        current_config = self.get_config()
        
        # Update with new values
        current_config.update(new_config)
        
        # Save the updated config
        with open(self.config_path, 'w') as f:
            json.dump(current_config, f, indent=4)
        
        return current_config
