import os
import json
import platform
import logging
import datetime
import subprocess

# Try to import psutil, but provide fallback if not available
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

class SettingsManager:
    """
    Manages application settings for the Intake CFD Project
    """
    def __init__(self, settings_path=None):
        """
        Initialize the SettingsManager with an optional settings file path
        """
        self.settings_path = settings_path
        if not self.settings_path:
            # Default settings path in the project directory
            self.settings_path = os.path.abspath(os.path.join(
                os.path.dirname(__file__), 
                '..', '..', 'settings.json'
            ))
        
        # Initialize logging
        logging.basicConfig(
            filename=os.path.join(os.path.dirname(self.settings_path), 'app.log'),
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Create default settings if not exists
        if not os.path.exists(self.settings_path):
            self._create_default_settings()
    
    def _create_default_settings(self):
        """Create a default settings file"""
        # Get system information
        if PSUTIL_AVAILABLE:
            cpu_count = psutil.cpu_count(logical=True)
            memory_gb = round(psutil.virtual_memory().total / (1024**3))
        else:
            # Fallback values if psutil is not available
            cpu_count = 2
            memory_gb = 8
        
        default_settings = {
            # General settings
            "project_location": os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')),
            "data_location": os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data')),
            "default_units": "metric",
            "auto_save_interval": 5,
            "check_updates": True,
            "telemetry": True,
            
            # Theme settings
            "theme": "light",
            "font_size": "medium",
            "accent_color": "#007bff",
            "animations_enabled": True,
            
            # CAD settings
            "cad_software_path": self._get_default_cad_path(),
            "export_format": "step",
            "mesh_quality": "normal",
            "cad_template": "default",
            "auto_save_cad": True,
            
            # Solver settings
            "solver_path": self._get_default_solver_path(),
            "default_solver": "simpleFoam",
            "max_threads": max(1, cpu_count - 1) if cpu_count else 2,
            "max_memory": min(8, max(1, memory_gb // 2)),
            "gpu_acceleration": False,
            "convergence_criteria": 0.0001
        }
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self.settings_path), exist_ok=True)
        
        # Write default settings
        with open(self.settings_path, 'w') as f:
            json.dump(default_settings, f, indent=4)
        
        self.logger.info("Created default settings file")
    
    def _get_default_cad_path(self):
        """Get the default path for CAD software based on the OS"""
        system = platform.system()
        
        if system == "Windows":
            # Look for common CAD software on Windows
            possible_paths = [
                r"C:\Program Files\FreeCAD 0.19\bin\FreeCAD.exe",
                r"C:\Program Files\FreeCAD\bin\FreeCAD.exe"
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    return path
            return r"C:\Program Files\FreeCAD\bin\FreeCAD.exe"
        
        elif system == "Darwin":  # macOS
            return "/Applications/FreeCAD.app/Contents/MacOS/FreeCAD"
        
        else:  # Linux or other
            # Check if FreeCAD is in the PATH
            try:
                path = subprocess.check_output(["which", "freecad"], text=True).strip()
                if path:
                    return path
            except (subprocess.SubprocessError, FileNotFoundError):
                pass
            
            return "/usr/bin/freecad"
    
    def _get_default_solver_path(self):
        """Get the default path for CFD solver based on the OS"""
        system = platform.system()
        
        if system == "Windows":
            return r"C:\OpenFOAM\OpenFOAM-v2112\platforms\windows\bin\simpleFoam.exe"
        
        elif system == "Darwin":  # macOS
            return "/opt/openfoam/openfoam2112/platforms/darwin64Clang/bin/simpleFoam"
        
        else:  # Linux or other
            # Check if OpenFOAM is in the PATH
            try:
                path = subprocess.check_output(["which", "simpleFoam"], text=True).strip()
                if path:
                    return path
            except (subprocess.SubprocessError, FileNotFoundError):
                pass
            
            return "/usr/bin/simpleFoam"
    
    def get_settings(self):
        """
        Read and return the settings
        """
        try:
            with open(self.settings_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.logger.error(f"Error reading settings file: {e}")
            # If settings file is missing or corrupt, create a new one
            self._create_default_settings()
            with open(self.settings_path, 'r') as f:
                return json.load(f)
    
    def save_settings(self, section, new_settings):
        """
        Save updated settings for a specific section
        
        Args:
            section: String indicating which section of settings to update
            new_settings: Dictionary with new settings values
        """
        # Read existing settings to preserve values not in new_settings
        current_settings = self.get_settings()
        
        # Update with new values based on section
        if section == 'general':
            for key, value in new_settings.items():
                if key in ['project_location', 'data_location', 'default_units', 
                           'auto_save_interval', 'check_updates', 'telemetry']:
                    current_settings[key] = value
        
        elif section == 'theme':
            for key, value in new_settings.items():
                if key in ['theme', 'font_size', 'accent_color', 'animations_enabled']:
                    current_settings[key] = value
        
        elif section == 'cad':
            for key, value in new_settings.items():
                if key in ['cad_software_path', 'export_format', 'mesh_quality', 
                           'cad_template', 'auto_save_cad']:
                    current_settings[key] = value
        
        elif section == 'solver':
            for key, value in new_settings.items():
                if key in ['solver_path', 'default_solver', 'max_threads', 
                           'max_memory', 'gpu_acceleration', 'convergence_criteria']:
                    current_settings[key] = value
        
        else:
            # If section is not recognized, update all settings
            current_settings.update(new_settings)
        
        # Save the updated settings
        with open(self.settings_path, 'w') as f:
            json.dump(current_settings, f, indent=4)
        
        self.logger.info(f"Updated settings for section: {section}")
        return current_settings
    
    def reset_to_defaults(self):
        """Reset all settings to default values"""
        if os.path.exists(self.settings_path):
            # Backup existing settings
            backup_path = self.settings_path + ".backup"
            try:
                os.rename(self.settings_path, backup_path)
                self.logger.info(f"Backed up settings to {backup_path}")
            except Exception as e:
                self.logger.error(f"Failed to backup settings: {e}")
        
        # Create new default settings
        self._create_default_settings()
        return True
    
    def get_system_info(self):
        """Get system information for display in settings"""
        if PSUTIL_AVAILABLE:
            cpu_count = psutil.cpu_count(logical=True)
            memory_gb = round(psutil.virtual_memory().total / (1024**3))
        else:
            # Fallback values if psutil is not available
            cpu_count = "Unknown (psutil not installed)"
            memory_gb = "Unknown (psutil not installed)"
        
        # Get GPU info if available
        gpu_info = "Not detected"
        try:
            if platform.system() == "Windows":
                import wmi
                computer = wmi.WMI()
                gpu_info = "\n".join([gpu.Name for gpu in computer.Win32_VideoController()])
            else:
                # For Linux, try lspci
                try:
                    output = subprocess.check_output("lspci | grep -i 'vga\|3d\|2d'", shell=True, text=True)
                    if output:
                        gpu_info = output.strip()
                except:
                    pass
        except:
            pass
        
        return {
            "os": platform.system(),
            "os_version": platform.version(),
            "cpu_count": cpu_count,
            "memory_gb": memory_gb,
            "gpu_info": gpu_info
        }
    
    def test_cad_connection(self, cad_path=None):
        """Test connection to CAD software"""
        if not cad_path:
            cad_path = self.get_settings().get('cad_software_path')
        
        if not os.path.exists(cad_path):
            return {
                "success": False,
                "message": f"CAD software not found at path: {cad_path}"
            }
        
        try:
            # Try to get version info
            # This will need to be customized based on the actual CAD software
            if platform.system() == "Windows":
                output = subprocess.check_output([cad_path, "--version"], text=True, stderr=subprocess.STDOUT)
            else:
                output = subprocess.check_output([cad_path, "--version"], text=True, stderr=subprocess.STDOUT)
            
            version = output.strip()
            return {
                "success": True,
                "version": version
            }
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            self.logger.error(f"Error testing CAD connection: {e}")
            return {
                "success": False,
                "message": f"Error running CAD software: {str(e)}"
            }
    
    def test_solver_connection(self, solver_path=None):
        """Test connection to CFD solver"""
        if not solver_path:
            solver_path = self.get_settings().get('solver_path')
        
        if not os.path.exists(solver_path):
            return {
                "success": False,
                "message": f"CFD solver not found at path: {solver_path}"
            }
        
        try:
            # Try to get version info
            # This will need to be customized based on the actual solver
            cmd = [solver_path, "-help"]
            output = subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT, timeout=5)
            
            # Extract version from output
            version = "Unknown"
            if "OpenFOAM" in output:
                import re
                version_match = re.search(r"OpenFOAM-(\d+\.\d+)", output)
                if version_match:
                    version = version_match.group(1)
            
            return {
                "success": True,
                "version": version
            }
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            self.logger.error(f"Error testing solver connection: {e}")
            return {
                "success": False,
                "message": f"Error running solver: {str(e)}"
            }
    
    def get_log_files(self):
        """Get list of available log files"""
        log_dir = os.path.join(os.path.dirname(self.settings_path), 'logs')
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        log_files = []
        for file in os.listdir(log_dir):
            if file.endswith('.log'):
                log_files.append(os.path.join(log_dir, file))
        
        # Add the main app log if it exists
        app_log = os.path.join(os.path.dirname(self.settings_path), 'app.log')
        if os.path.exists(app_log):
            log_files.append(app_log)
        
        return log_files
    
    def get_log_content(self, log_file):
        """Get content of a log file"""
        if not os.path.exists(log_file):
            return {
                "success": False,
                "message": f"Log file not found: {log_file}"
            }
        
        try:
            with open(log_file, 'r') as f:
                content = f.read()
            
            return {
                "success": True,
                "content": content
            }
        except Exception as e:
            self.logger.error(f"Error reading log file: {e}")
            return {
                "success": False,
                "message": f"Error reading log file: {str(e)}"
            }
    
    def clear_log(self, log_file):
        """Clear content of a log file"""
        if not os.path.exists(log_file):
            return {
                "success": False,
                "message": f"Log file not found: {log_file}"
            }
        
        try:
            with open(log_file, 'w') as f:
                f.write(f"Log cleared on {datetime.datetime.now()}\n")
            
            return {
                "success": True,
                "message": "Log file cleared successfully"
            }
        except Exception as e:
            self.logger.error(f"Error clearing log file: {e}")
            return {
                "success": False,
                "message": f"Error clearing log file: {str(e)}"
            }
    
    def browse_files(self, path):
        """Browse files and directories at the given path"""
        if not os.path.exists(path):
            return {
                "success": False,
                "message": f"Path not found: {path}"
            }
        
        try:
            files = []
            with os.scandir(path) as entries:
                for entry in entries:
                    files.append({
                        "name": entry.name,
                        "isDirectory": entry.is_dir(),
                        "size": entry.stat().st_size if entry.is_file() else 0
                    })
            
            # Sort directories first, then files
            files.sort(key=lambda x: (0 if x["isDirectory"] else 1, x["name"].lower()))
            
            return {
                "success": True,
                "files": files
            }
        except Exception as e:
            self.logger.error(f"Error browsing files: {e}")
            return {
                "success": False,
                "message": f"Error browsing files: {str(e)}"
            }
