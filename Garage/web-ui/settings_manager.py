import json
import os
import platform
import sys
from flask import jsonify, request

class Settings_Manager:
    """Manages application settings for the web interface"""
    
    def __init__(self):
        """Initialize settings manager"""
        self.settings = {
            "general": {
                "theme": "light",
                "language": "en",
                "autoSaveInterval": 5,
                "nxPath": "",
                "projectDir": ""
            },
            "appearance": {
                "fontSize": "medium",
                "accentColor": "#1976d2",
                "enableAnimations": True
            },
            "display": {
                "show_grid": True,
                "show_axes": True,
                "default_colormap": "viridis"
            },
            "simulation": {
                "cfdSolver": "OpenFOAM",
                "mesher": "GMSH",
                "defaultMeshSize": 0.1,
                "viscosity": 1.8e-5,
                "density": 1.225
            },
            "solver": {
                "max_iterations": 1000,
                "tolerance": 1e-6,
                "solver_type": "SIMPLE",
                "num_threads": 4
            },
            "paths": {
                "default_save_location": "./results",
                "templates_directory": "./templates",
                "mesh_directory": "./mesh"
            },
            "advanced": {
                "debugMode": False,
                "log_level": "INFO",
                "use_gpu": False,
                "precision": "double",
                "threads": 4,
                "memoryLimit": 70
            }
        }
        self.load_settings()
        
    def load_settings(self):
        """Load settings from file if it exists"""
        try:
            if os.path.exists("settings.json"):
                with open("settings.json", "r") as f:
                    loaded_settings = json.load(f)
                    # Update settings from loaded file using deep merge
                    self._deep_merge(self.settings, loaded_settings)
        except Exception as e:
            print(f"Error loading settings: {str(e)}")
    
    def _deep_merge(self, target, source):
        """Deep merge two dictionaries"""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_merge(target[key], value)
            elif key in target:  # Only update keys that already exist
                target[key] = value
    
    def save_settings(self):
        """Save current settings to file"""
        try:
            with open("settings.json", "w") as f:
                json.dump(self.settings, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving settings: {str(e)}")
            return False
    
    def get_all_settings(self):
        """Get all settings as a single dictionary, flattened for API response"""
        flattened = {}
        for category, values in self.settings.items():
            for key, value in values.items():
                flattened[key] = value
        return flattened
    
    def get_setting(self, category, key, default=None):
        """Get a specific setting"""
        try:
            return self.settings[category][key]
        except:
            return default
            
    def update_setting(self, category, key, value):
        """Update a specific setting"""
        if category in self.settings and key in self.settings[category]:
            self.settings[category][key] = value
            return True
        return False
    
    def update_settings_from_dict(self, settings_dict):
        """Update settings from a dictionary (from frontend)"""
        try:
            # Map frontend keys to backend categories
            category_map = {
                # General settings
                "nxPath": "general",
                "projectDir": "general",
                "autoSaveInterval": "general",
                
                # Appearance settings
                "theme": "general",
                "fontSize": "appearance",
                "accentColor": "appearance",
                "enableAnimations": "appearance",
                
                # Simulation settings
                "cfdSolver": "simulation",
                "mesher": "simulation",
                "defaultMeshSize": "simulation",
                "viscosity": "simulation",
                "density": "simulation",
                
                # Advanced settings
                "debugMode": "advanced",
                "threads": "advanced",
                "memoryLimit": "advanced"
            }
            
            # Update settings based on mapping
            for key, value in settings_dict.items():
                category = category_map.get(key)
                if category and key in self.settings[category]:
                    self.settings[category][key] = value
            
            # Save settings to file
            self.save_settings()
            return True
        except Exception as e:
            print(f"Error updating settings from dict: {str(e)}")
            return False
    
    def reset_to_defaults(self):
        """Reset settings to default values"""
        self.__init__()
        return self.save_settings()
    
    def get_system_info(self):
        """Get system information for display in settings"""
        try:
            cpu_info = platform.processor()
            if not cpu_info:
                cpu_info = "Unknown CPU"
            
            memory = psutil.virtual_memory()
            memory_gb = round(memory.total / (1024 ** 3), 1)
            
            return {
                "cpu": cpu_info,
                "memory": f"{memory_gb} GB",
                "os": f"{platform.system()} {platform.release()}",
                "pythonVersion": platform.python_version()
            }
        except Exception as e:
            print(f"Error getting system info: {str(e)}")
            return {
                "cpu": "Error retrieving CPU info",
                "memory": "Error retrieving memory info",
                "os": "Error retrieving OS info",
                "pythonVersion": "Error retrieving Python version"
            }
    
    # Flask API routes
    def register_routes(self, app):
        """Register settings API routes"""
        
        @app.route('/api/settings', methods=['GET'])
        def get_settings():
            return jsonify(self.get_all_settings())
        
        @app.route('/api/settings', methods=['POST'])
        def save_settings_api():
            try:
                settings_data = request.json
                success = self.update_settings_from_dict(settings_data)
                if success:
                    return jsonify({"success": True, "message": "Settings saved successfully"})
                else:
                    return jsonify({"success": False, "message": "Failed to save settings"}), 500
            except Exception as e:
                return jsonify({"success": False, "message": str(e)}), 500
        
        @app.route('/api/settings/reset', methods=['POST'])
        def reset_settings():
            success = self.reset_to_defaults()
            if success:
                return jsonify({"success": True, "message": "Settings reset to defaults"})
            else:
                return jsonify({"success": False, "message": "Failed to reset settings"}), 500
        
        @app.route('/api/system-info', methods=['GET'])
        def get_system_info_api():
            return jsonify(self.get_system_info())
        
        @app.route('/api/check-updates', methods=['GET'])
        def check_updates():
            # Mock implementation - would connect to update server in production
            return jsonify({
                "success": True,
                "upToDate": True,
                "currentVersion": "1.0.0",
                "latestVersion": "1.0.0"
            })
        
        @app.route('/api/run-diagnostics', methods=['POST'])
        def run_diagnostics():
            # Mock implementation - would run actual diagnostics in production
            return jsonify({
                "success": True,
                "results": {
                    "system": "OK",
                    "network": "OK",
                    "disk": "OK",
                    "dependencies": "OK"
                },
                "message": "All diagnostics passed"
            })
    
    # UI rendering methods
    def render(self):
        """Render the settings manager UI"""
        return rp.html.div(
            {"className": "settings-manager"},
            [
                self._render_general_settings(),
                self._render_appearance_settings(),
                self._render_display_settings(),
                self._render_solver_settings(),
                self._render_path_settings(),
                self._render_advanced_settings(),
                self._render_actions()
            ]
        )
    
    def _render_general_settings(self):
        """Render general application settings"""
        settings = self.settings["general"]
        
        return rp.html.div(
            {"className": "settings-category"},
            [
                rp.html.h3("General Settings"),
                rp.html.div(
                    {"className": "settings-grid"},
                    [
                        rp.html.div(
                            {"className": "setting-item"},
                            [
                                rp.html.label({"htmlFor": "theme"}, "Theme:"),
                                rp.html.select(
                                    {
                                        "id": "theme",
                                        "value": settings["theme"],
                                        "onChange": lambda e: self.update_setting("general", "theme", e["target"]["value"])
                                    },
                                    [
                                        rp.html.option({"value": "light"}, "Light"),
                                        rp.html.option({"value": "dark"}, "Dark"),
                                        rp.html.option({"value": "system"}, "System Default")
                                    ]
                                )
                            ]
                        ),
                        rp.html.div(
                            {"className": "setting-item"},
                            [
                                rp.html.label({"htmlFor": "language"}, "Language:"),
                                rp.html.select(
                                    {
                                        "id": "language",
                                        "value": settings["language"],
                                        "onChange": lambda e: self.update_setting("general", "language", e["target"]["value"])
                                    },
                                    [
                                        rp.html.option({"value": "en"}, "English"),
                                        rp.html.option({"value": "fr"}, "French"),
                                        rp.html.option({"value": "de"}, "German"),
                                        rp.html.option({"value": "es"}, "Spanish")
                                    ]
                                )
                            ]
                        ),
                        rp.html.div(
                            {"className": "setting-item"},
                            [
                                rp.html.label({"htmlFor": "save_interval"}, "Auto-save interval (minutes):"),
                                rp.html.input({
                                    "type": "number",
                                    "id": "save_interval",
                                    "value": settings["autoSaveInterval"],
                                    "min": "1",
                                    "max": "60",
                                    "onChange": lambda e: self.update_setting("general", "autoSaveInterval", int(e["target"]["value"]))
                                })
                            ]
                        ),
                        rp.html.div(
                            {"className": "setting-item"},
                            [
                                rp.html.label({"htmlFor": "nxPath"}, "NX Path:"),
                                rp.html.div(
                                    {"className": "path-input-group"},
                                    [
                                        rp.html.input({
                                            "type": "text",
                                            "id": "nxPath",
                                            "className": "path-input",
                                            "value": settings["nxPath"],
                                            "onChange": lambda e: self.update_setting("general", "nxPath", e["target"]["value"])
                                        }),
                                        rp.html.button({"className": "browse-button"}, "Browse...")
                                    ]
                                )
                            ]
                        ),
                        rp.html.div(
                            {"className": "setting-item"},
                            [
                                rp.html.label({"htmlFor": "projectDir"}, "Project Directory:"),
                                rp.html.div(
                                    {"className": "path-input-group"},
                                    [
                                        rp.html.input({
                                            "type": "text",
                                            "id": "projectDir",
                                            "className": "path-input",
                                            "value": settings["projectDir"],
                                            "onChange": lambda e: self.update_setting("general", "projectDir", e["target"]["value"])
                                        }),
                                        rp.html.button({"className": "browse-button"}, "Browse...")
                                    ]
                                )
                            ]
                        )
                    ]
                )
            ]
        )
    
    def _render_appearance_settings(self):
        """Render appearance settings"""
        settings = self.settings["appearance"]
        
        return rp.html.div(
            {"className": "settings-category"},
            [
                rp.html.h3("Appearance Settings"),
                rp.html.div(
                    {"className": "settings-grid"},
                    [
                        rp.html.div(
                            {"className": "setting-item"},
                            [
                                rp.html.label({"htmlFor": "fontSize"}, "Font Size:"),
                                rp.html.select(
                                    {
                                        "id": "fontSize",
                                        "value": settings["fontSize"],
                                        "onChange": lambda e: self.update_setting("appearance", "fontSize", e["target"]["value"])
                                    },
                                    [
                                        rp.html.option({"value": "small"}, "Small"),
                                        rp.html.option({"value": "medium"}, "Medium"),
                                        rp.html.option({"value": "large"}, "Large"),
                                        rp.html.option({"value": "x-large"}, "X-Large")
                                    ]
                                )
                            ]
                        ),
                        rp.html.div(
                            {"className": "setting-item"},
                            [
                                rp.html.label({"htmlFor": "accentColor"}, "Accent Color:"),
                                rp.html.div(
                                    {"className": "color-input-group"},
                                    [
                                        rp.html.input({
                                            "type": "color",
                                            "id": "accentColor",
                                            "value": settings["accentColor"],
                                            "onChange": lambda e: self.update_setting("appearance", "accentColor", e["target"]["value"])
                                        }),
                                        rp.html.input({
                                            "type": "text",
                                            "value": settings["accentColor"],
                                            "onChange": lambda e: self.update_setting("appearance", "accentColor", e["target"]["value"])
                                        })
                                    ]
                                )
                            ]
                        ),
                        rp.html.div(
                            {"className": "setting-item checkbox-item"},
                            [
                                rp.html.input({
                                    "type": "checkbox",
                                    "id": "enableAnimations",
                                    "checked": settings["enableAnimations"],
                                    "onChange": lambda e: self.update_setting("appearance", "enableAnimations", e["target"]["checked"])
                                }),
                                rp.html.label({"htmlFor": "enableAnimations"}, "Enable UI animations")
                            ]
                        )
                    ]
                )
            ]
        )
        
    def _render_display_settings(self):
        """Render display settings"""
        settings = self.settings["display"]
        
        return rp.html.div(
            {"className": "settings-category"},
            [
                rp.html.h3("Display Settings"),
                rp.html.div(
                    {"className": "settings-grid"},
                    [
                        rp.html.div(
                            {"className": "setting-item checkbox-item"},
                            [
                                rp.html.input({
                                    "type": "checkbox",
                                    "id": "show_grid",
                                    "checked": settings["show_grid"],
                                    "onChange": lambda e: self.update_setting("display", "show_grid", e["target"]["checked"])
                                }),
                                rp.html.label({"htmlFor": "show_grid"}, "Show grid in visualizations")
                            ]
                        ),
                        rp.html.div(
                            {"className": "setting-item checkbox-item"},
                            [
                                rp.html.input({
                                    "type": "checkbox",
                                    "id": "show_axes",
                                    "checked": settings["show_axes"],
                                    "onChange": lambda e: self.update_setting("display", "show_axes", e["target"]["checked"])
                                }),
                                rp.html.label({"htmlFor": "show_axes"}, "Show axes in visualizations")
                            ]
                        ),
                        rp.html.div(
                            {"className": "setting-item"},
                            [
                                rp.html.label({"htmlFor": "colormap"}, "Default color map:"),
                                rp.html.select(
                                    {
                                        "id": "colormap",
                                        "value": settings["default_colormap"],
                                        "onChange": lambda e: self.update_setting("display", "default_colormap", e["target"]["value"])
                                    },
                                    [
                                        rp.html.option({"value": "viridis"}, "Viridis"),
                                        rp.html.option({"value": "plasma"}, "Plasma"),
                                        rp.html.option({"value": "inferno"}, "Inferno"),
                                        rp.html.option({"value": "magma"}, "Magma"),
                                        rp.html.option({"value": "jet"}, "Jet"),
                                        rp.html.option({"value": "rainbow"}, "Rainbow"),
                                        rp.html.option({"value": "coolwarm"}, "Cool-Warm")
                                    ]
                                )
                            ]
                        )
                    ]
                )
            ]
        )
    
    def _render_solver_settings(self):
        """Render solver settings"""
        settings = self.settings["solver"]
        simulation_settings = self.settings["simulation"]
        
        return rp.html.div(
            {"className": "settings-category"},
            [
                rp.html.h3("Solver Settings"),
                rp.html.div(
                    {"className": "settings-grid"},
                    [
                        rp.html.div(
                            {"className": "setting-item"},
                            [
                                rp.html.label({"htmlFor": "cfdSolver"}, "CFD Solver:"),
                                rp.html.select(
                                    {
                                        "id": "cfdSolver",
                                        "value": simulation_settings["cfdSolver"],
                                        "onChange": lambda e: self.update_setting("simulation", "cfdSolver", e["target"]["value"])
                                    },
                                    [
                                        rp.html.option({"value": "OpenFOAM"}, "OpenFOAM"),
                                        rp.html.option({"value": "Fluent"}, "Fluent"),
                                        rp.html.option({"value": "Star-CCM+"}, "Star-CCM+"),
                                        rp.html.option({"value": "Custom"}, "Custom")
                                    ]
                                )
                            ]
                        ),
                        rp.html.div(
                            {"className": "setting-item"},
                            [
                                rp.html.label({"htmlFor": "mesher"}, "Mesher:"),
                                rp.html.select(
                                    {
                                        "id": "mesher",
                                        "value": simulation_settings["mesher"],
                                        "onChange": lambda e: self.update_setting("simulation", "mesher", e["target"]["value"])
                                    },
                                    [
                                        rp.html.option({"value": "GMSH"}, "GMSH"),
                                        rp.html.option({"value": "Fluent Meshing"}, "Fluent Meshing"),
                                        rp.html.option({"value": "Star-CCM+ Meshing"}, "Star-CCM+ Meshing"),
                                        rp.html.option({"value": "Custom"}, "Custom")
                                    ]
                                )
                            ]
                        ),
                        rp.html.div(
                            {"className": "setting-item"},
                            [
                                rp.html.label({"htmlFor": "defaultMeshSize"}, "Default Mesh Size (m):"),
                                rp.html.input({
                                    "type": "number",
                                    "id": "defaultMeshSize",
                                    "value": simulation_settings["defaultMeshSize"],
                                    "step": "0.01",
                                    "min": "0.001",
                                    "onChange": lambda e: self.update_setting("simulation", "defaultMeshSize", float(e["target"]["value"]))
                                })
                            ]
                        ),
                        rp.html.div(
                            {"className": "setting-item"},
                            [
                                rp.html.label({"htmlFor": "solver_type"}, "Solver type:"),
                                rp.html.select(
                                    {
                                        "id": "solver_type",
                                        "value": settings["solver_type"],
                                        "onChange": lambda e: self.update_setting("solver", "solver_type", e["target"]["value"])
                                    },
                                    [
                                        rp.html.option({"value": "SIMPLE"}, "SIMPLE"),
                                        rp.html.option({"value": "PISO"}, "PISO"),
                                        rp.html.option({"value": "PIMPLE"}, "PIMPLE")
                                    ]
                                )
                            ]
                        ),
                        rp.html.div(
                            {"className": "setting-item"},
                            [
                                rp.html.label({"htmlFor": "max_iterations"}, "Maximum iterations:"),
                                rp.html.input({
                                    "type": "number",
                                    "id": "max_iterations",
                                    "value": settings["max_iterations"],
                                    "min": "100",
                                    "max": "10000",
                                    "onChange": lambda e: self.update_setting("solver", "max_iterations", int(e["target"]["value"]))
                                })
                            ]
                        ),
                        rp.html.div(
                            {"className": "setting-item"},
                            [
                                rp.html.label({"htmlFor": "viscosity"}, "Default Viscosity (kg/m·s):"),
                                rp.html.input({
                                    "type": "number",
                                    "id": "viscosity",
                                    "value": simulation_settings["viscosity"],
                                    "step": "0.000001",
                                    "min": "0",
                                    "onChange": lambda e: self.update_setting("simulation", "viscosity", float(e["target"]["value"]))
                                })
                            ]
                        ),
                        rp.html.div(
                            {"className": "setting-item"},
                            [
                                rp.html.label({"htmlFor": "density"}, "Default Density (kg/m³):"),
                                rp.html.input({
                                    "type": "number",
                                    "id": "density",
                                    "value": simulation_settings["density"],
                                    "step": "0.001",
                                    "min": "0",
                                    "onChange": lambda e: self.update_setting("simulation", "density", float(e["target"]["value"]))
                                })
                            ]
                        )
                    ]
                )
            ]
        )
    
    def _render_path_settings(self):
        """Render file path settings"""
        settings = self.settings["paths"]
        
        return rp.html.div(
            {"className": "settings-category"},
            [
                rp.html.h3("File Paths"),
                rp.html.div(
                    {"className": "path-settings"},
                    [
                        rp.html.div(
                            {"className": "path-item"},
                            [
                                rp.html.label({"htmlFor": "default_save"}, "Default save location:"),
                                rp.html.div(
                                    {"className": "path-input-group"},
                                    [
                                        rp.html.input({
                                            "type": "text",
                                            "id": "default_save",
                                            "className": "path-input",
                                            "value": settings["default_save_location"],
                                            "onChange": lambda e: self.update_setting("paths", "default_save_location", e["target"]["value"])
                                        }),
                                        rp.html.button(
                                            {"className": "browse-button"},
                                            "Browse..."
                                        )
                                    ]
                                )
                            ]
                        ),
                        rp.html.div(
                            {"className": "path-item"},
                            [
                                rp.html.label({"htmlFor": "templates_dir"}, "Templates directory:"),
                                rp.html.div(
                                    {"className": "path-input-group"},
                                    [
                                        rp.html.input({
                                            "type": "text",
                                            "id": "templates_dir",
                                            "className": "path-input",
                                            "value": settings["templates_directory"],
                                            "onChange": lambda e: self.update_setting("paths", "templates_directory", e["target"]["value"])
                                        }),
                                        rp.html.button(
                                            {"className": "browse-button"},
                                            "Browse..."
                                        )
                                    ]
                                )
                            ]
                        ),
                        rp.html.div(
                            {"className": "path-item"},
                            [
                                rp.html.label({"htmlFor": "mesh_dir"}, "Mesh directory:"),
                                rp.html.div(
                                    {"className": "path-input-group"},
                                    [
                                        rp.html.input({
                                            "type": "text",
                                            "id": "mesh_dir",
                                            "className": "path-input",
                                            "value": settings["mesh_directory"],
                                            "onChange": lambda e: self.update_setting("paths", "mesh_directory", e["target"]["value"])
                                        }),
                                        rp.html.button(
                                            {"className": "browse-button"},
                                            "Browse..."
                                        )
                                    ]
                                )
                            ]
                        )
                    ]
                )
            ]
        )
    
    def _render_advanced_settings(self):
        """Render advanced settings"""
        settings = self.settings["advanced"]
        
        return rp.html.div(
            {"className": "settings-category"},
            [
                rp.html.h3("Advanced Settings"),
                rp.html.div(
                    {"className": "settings-grid"},
                    [
                        rp.html.div(
                            {"className": "setting-item checkbox-item"},
                            [
                                rp.html.input({
                                    "type": "checkbox",
                                    "id": "debugMode",
                                    "checked": settings["debugMode"],
                                    "onChange": lambda e: self.update_setting("advanced", "debugMode", e["target"]["checked"])
                                }),
                                rp.html.label({"htmlFor": "debugMode"}, "Debug mode")
                            ]
                        ),
                        rp.html.div(
                            {"className": "setting-item"},
                            [
                                rp.html.label({"htmlFor": "log_level"}, "Log level:"),
                                rp.html.select(
                                    {
                                        "id": "log_level",
                                        "value": settings["log_level"],
                                        "onChange": lambda e: self.update_setting("advanced", "log_level", e["target"]["value"])
                                    },
                                    [
                                        rp.html.option({"value": "DEBUG"}, "Debug"),
                                        rp.html.option({"value": "INFO"}, "Info"),
                                        rp.html.option({"value": "WARNING"}, "Warning"),
                                        rp.html.option({"value": "ERROR"}, "Error")
                                    ]
                                )
                            ]
                        ),
                        rp.html.div(
                            {"className": "setting-item checkbox-item"},
                            [
                                rp.html.input({
                                    "type": "checkbox",
                                    "id": "use_gpu",
                                    "checked": settings["use_gpu"],
                                    "onChange": lambda e: self.update_setting("advanced", "use_gpu", e["target"]["checked"])
                                }),
                                rp.html.label({"htmlFor": "use_gpu"}, "Use GPU acceleration when available")
                            ]
                        ),
                        rp.html.div(
                            {"className": "setting-item"},
                            [
                                rp.html.label({"htmlFor": "threads"}, "Number of Threads:"),
                                rp.html.input({
                                    "type": "number",
                                    "id": "threads",
                                    "value": settings["threads"],
                                    "min": "1",
                                    "max": "64",
                                    "onChange": lambda e: self.update_setting("advanced", "threads", int(e["target"]["value"]))
                                })
                            ]
                        ),
                        rp.html.div(
                            {"className": "setting-item"},
                            [
                                rp.html.label({"htmlFor": "memoryLimit"}, "Memory Limit (%):"),
                                rp.html.input({
                                    "type": "number",
                                    "id": "memoryLimit",
                                    "value": settings["memoryLimit"],
                                    "min": "10",
                                    "max": "90",
                                    "onChange": lambda e: self.update_setting("advanced", "memoryLimit", int(e["target"]["value"]))
                                })
                            ]
                        ),
                        rp.html.div(
                            {"className": "setting-item"},
                            [
                                rp.html.label({"htmlFor": "precision"}, "Calculation precision:"),
                                rp.html.select(
                                    {
                                        "id": "precision",
                                        "value": settings["precision"],
                                        "onChange": lambda e: self.update_setting("advanced", "precision", e["target"]["value"])
                                    },
                                    [
                                        rp.html.option({"value": "single"}, "Single (32-bit)"),
                                        rp.html.option({"value": "double"}, "Double (64-bit)")
                                    ]
                                )
                            ]
                        )
                    ]
                )
            ]
        )
    
    def _render_actions(self):
        """Render action buttons"""
        return rp.html.div(
            {"className": "settings-actions"},
            [
                rp.html.button(
                    {
                        "className": "save-button",
                        "onClick": lambda e: self.save_settings()
                    },
                    "Save Settings"
                ),
                rp.html.button(
                    {
                        "className": "reset-button",
                        "onClick": lambda e: self.reset_to_defaults()
                    },
                    "Reset to Defaults"
                )
            ]
        )
