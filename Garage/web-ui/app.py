from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file
import os
import json
import subprocess
import sys
import glob
import platform

# Try to import psutil, but provide fallback if not available
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("Warning: psutil package not found. Some system information will be unavailable.")
    print("To install psutil, run: pip install psutil")

# Import both settings managers to handle both formats
from utils.settings_manager import SettingsManager
from settings_manager import Settings_Manager

app = Flask(__name__)

# Add the project root to the path so we can import modules
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

# Import local utilities instead of trying to import from project root
from utils.config_reader import ConfigReader
from utils.parameter_calculator import ParameterCalculator

# Initialize our enhanced settings manager
settings_manager_v2 = Settings_Manager()
# Register the enhanced settings API routes
settings_manager_v2.register_routes(app)

# Add a function to get the basename of a file to use in templates
@app.template_filter('basename')
def get_basename(path):
    return os.path.basename(path)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/cad', methods=['GET', 'POST'])
def cad_page():
    config_reader = ConfigReader()
    config = config_reader.get_config()
    
    if request.method == 'POST':
        # Handle form submission
        updated_config = {}
        for key in request.form:
            if key in config:
                value = request.form[key]
                # Convert to appropriate type
                if isinstance(config[key], float):
                    updated_config[key] = float(value)
                elif isinstance(config[key], int):
                    updated_config[key] = int(value)
                else:
                    updated_config[key] = value
        
        # Save updated config
        config_reader.save_config(updated_config)
        return redirect(url_for('cad_page'))
    
    return render_template('cad.html', config=config)

@app.route('/simulation', methods=['GET', 'POST'])
def simulation_page():
    config_reader = ConfigReader()
    config = config_reader.get_config()
    
    sim_files = []
    simulations_dir = os.path.join(project_root, 'simulations')
    if os.path.exists(simulations_dir):
        sim_files = glob.glob(os.path.join(simulations_dir, '*.sim'))
    
    return render_template('simulation.html', config=config, sim_files=sim_files, os=os)

@app.route('/results')
def results_page():
    # Get available results
    results_dir = os.path.join(project_root, 'results')
    results = []
    
    if os.path.exists(results_dir):
        for result_folder in os.listdir(results_dir):
            path = os.path.join(results_dir, result_folder)
            if os.path.isdir(path):
                results.append(result_folder)
    
    return render_template('results.html', results=results)

@app.route('/settings')
def settings_page():
    # Use the legacy SettingsManager for backward compatibility
    settings_manager = SettingsManager()
    settings = settings_manager.get_settings()
    
    # But also get settings from our enhanced settings manager
    system_info = settings_manager_v2.get_system_info()
    enhanced_settings = settings_manager_v2.get_all_settings()
    
    # Get system information
    if PSUTIL_AVAILABLE:
        cpu_count = psutil.cpu_count(logical=True)
        available_memory = round(psutil.virtual_memory().total / (1024**3))
    else:
        cpu_count = "Unknown"
        available_memory = "Unknown"
    
    # Get list of log files
    log_files = settings_manager.get_log_files()
    
    # App version
    app_version = "1.0.0"
    
    # Project root path
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    data_dir = os.path.join(project_root, 'data')
    
    return render_template('settings.html', 
                          settings=settings, 
                          enhanced_settings=enhanced_settings,
                          system_info=system_info,
                          cpu_count=cpu_count, 
                          available_memory=available_memory,
                          log_files=log_files,
                          app_version=app_version,
                          project_root=project_root,
                          data_dir=data_dir,
                          os=os)

@app.route('/api/run-generation', methods=['POST'])
def run_generation():
    try:
        # Get configuration parameters from request
        data = request.json
        
        # Run the CAD generation script
        subprocess.run(['python', os.path.join(project_root, 'generate_cad.py')], check=True)
        
        return jsonify({'success': True, 'message': 'CAD model generation completed'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/run-simulation', methods=['POST'])
def run_simulation():
    try:
        # Get simulation parameters from request
        data = request.json
        sim_file = data.get('simulation_file')
        
        # Run the simulation script
        subprocess.run(['python', os.path.join(project_root, 'run_simulation.py'), sim_file], check=True)
        
        return jsonify({'success': True, 'message': 'Simulation started successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/calculate-parameters', methods=['POST'])
def calculate_parameters():
    try:
        data = request.json
        calculator = ParameterCalculator()
        results = calculator.calculate(data)
        return jsonify({'success': True, 'results': results})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/save-simulation', methods=['POST'])
def save_simulation():
    try:
        # Get simulation data from request
        data = request.json
        
        # Validate required fields
        if not data.get('simulation_name'):
            return jsonify({'success': False, 'message': 'Simulation name is required'})
        
        # Create simulations directory if it doesn't exist
        simulations_dir = os.path.join(project_root, 'simulations')
        os.makedirs(simulations_dir, exist_ok=True)
        
        # Create sim file path
        sim_file = os.path.join(simulations_dir, f"{data['simulation_name']}.sim")
        
        # Save simulation data to file
        with open(sim_file, 'w') as f:
            json.dump(data, f, indent=4)
        
        return jsonify({'success': True, 'message': 'Simulation saved successfully', 'file': sim_file})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/get-simulation', methods=['POST'])
def get_simulation():
    try:
        # Get simulation file from request
        data = request.json
        sim_file = data.get('simulation_file')
        
        if not sim_file or not os.path.exists(sim_file):
            return jsonify({'success': False, 'message': 'Simulation file not found'})
        
        # Read simulation data from file
        with open(sim_file, 'r') as f:
            sim_data = json.load(f)
        
        return jsonify({'success': True, 'simulation': sim_data})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/settings/<section>', methods=['POST'])
def save_settings(section):
    try:
        # Use the legacy SettingsManager for backward compatibility
        settings_manager = SettingsManager()
        data = request.json
        
        # Save settings for the specified section
        updated_settings = settings_manager.save_settings(section, data)
        
        # Also update our enhanced settings manager for new clients
        # Map section names to categories in the enhanced settings manager
        category_map = {
            'general': 'general',
            'theme': 'appearance',
            'solver': 'solver',
            'advanced': 'advanced'
        }
        
        # If there's a mapped category, update it in the enhanced settings manager
        if section in category_map:
            for key, value in data.items():
                settings_manager_v2.update_setting(category_map[section], key, value)
            settings_manager_v2.save_settings()
        
        return jsonify({'success': True, 'message': f'{section.capitalize()} settings saved successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/browse-files', methods=['POST'])
def browse_files():
    try:
        settings_manager = SettingsManager()
        data = request.json
        path = data.get('path', '/')
        
        result = settings_manager.browse_files(path)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/test-cad-connection', methods=['POST'])
def test_cad_connection():
    try:
        settings_manager = SettingsManager()
        data = request.json
        cad_path = data.get('cad_path')
        
        result = settings_manager.test_cad_connection(cad_path)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/test-solver-connection', methods=['POST'])
def test_solver_connection():
    try:
        settings_manager = SettingsManager()
        data = request.json
        solver_path = data.get('solver_path')
        
        result = settings_manager.test_solver_connection(solver_path)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/get-log-content', methods=['POST'])
def get_log_content():
    try:
        settings_manager = SettingsManager()
        data = request.json
        log_file = data.get('log_file')
        
        result = settings_manager.get_log_content(log_file)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/clear-log', methods=['POST'])
def clear_log():
    try:
        settings_manager = SettingsManager()
        data = request.json
        log_file = data.get('log_file')
        
        result = settings_manager.clear_log(log_file)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/download-log')
def download_log():
    try:
        log_file = request.args.get('file')
        if not log_file or not os.path.exists(log_file):
            return "Log file not found", 404
        
        return send_file(log_file, as_attachment=True, attachment_filename=os.path.basename(log_file))
    except Exception as e:
        return str(e), 500

@app.route('/api/reset-settings', methods=['POST'])
def reset_settings():
    try:
        # Reset both settings managers for backward compatibility
        legacy_settings_manager = SettingsManager()
        legacy_result = legacy_settings_manager.reset_to_defaults()
        
        enhanced_result = settings_manager_v2.reset_to_defaults()
        
        return jsonify({'success': True, 'message': 'Settings reset to defaults'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

if __name__ == '__main__':
    app.run(debug=True)
