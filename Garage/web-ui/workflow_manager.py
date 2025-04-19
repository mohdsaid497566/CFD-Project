import os
import sys
import time
import json
import platform
import subprocess
import traceback
import datetime
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import math
import reactpy as rp
import logging

# Flag for demonstration mode
DEMO_MODE = True


def run_command(command, cwd=None, timeout=300):
    """Run a shell command with proper error handling and demo mode support"""
    if DEMO_MODE and (command[0].startswith('./') or '/mnt/c/Program Files' in command[0]):
        print(f"DEMO MODE: Simulating command: {' '.join(command)}")
        with open("command_log.txt", "a") as log_file:
            log_file.write(f"DEMO MODE: Simulating: {' '.join(command)}\n")
        
        if 'nx_express2.py' in ' '.join(command) or 'nx_export.py' in ' '.join(command):
            print("Mock NX execution completed successfully.")
            return "Mock NX execution completed successfully."
        elif 'gmsh_process' in command[0]:
            print("Mock mesh generation completed successfully.")
            return "Mock mesh generation completed successfully."
        elif 'cfd_solver' in command[0]:
            print("Mock CFD simulation completed successfully.")
            return "Mock CFD simulation completed successfully."
        elif 'process_results' in command[0]:
            print("Mock results processing completed successfully.")
            return "Mock results processing completed successfully."
        else:
            print("Generic mock command execution.")
            return "Generic mock command execution."
    
    try:
        if command[0].startswith('/') or command[0].startswith('./'):
            if not os.path.exists(command[0]):
                error_msg = f"Executable not found: {command[0]}"
                print(error_msg)
                with open("error_log.txt", "a") as log_file:
                    log_file.write(f"{error_msg}\n")
                
                if DEMO_MODE:
                    print(f"DEMO MODE: Simulating command despite missing executable: {' '.join(command)}")
                    return f"DEMO MODE: Simulated execution of {' '.join(command)}"
                    
                raise FileNotFoundError(error_msg)
        
        cmd_str = ' '.join(command)
        print(f"Executing: {cmd_str}")
        with open("command_log.txt", "a") as log_file:
            log_file.write(f"Executing: {cmd_str}\n")
            
        result = subprocess.run(command, check=True, capture_output=True, text=True, cwd=cwd, timeout=timeout)
        
        print(result.stdout)
        with open("command_log.txt", "a") as log_file:
            log_file.write(f"Success: {cmd_str}\nOutput: {result.stdout}\n")
        
        return result.stdout
    except Exception as e:
        error_msg = f"Error executing command: {e}"
        print(error_msg)
        with open("error_log.txt", "a") as log_file:
            log_file.write(f"{error_msg}\n")
            
        if DEMO_MODE:
            print(f"DEMO MODE: Continuing with mock result despite error...")
            return f"DEMO MODE: Simulated execution (after error) of {' '.join(command)}"
            
        raise


def is_wsl():
    """Check if running on Windows Subsystem for Linux"""
    if platform.system() == "Linux":
        if "microsoft" in platform.release().lower():
            return True
        try:
            with open("/proc/version", "r") as f:
                if "microsoft" in f.read().lower():
                    return True
        except:
            pass
        if os.path.exists("/proc/sys/fs/binfmt_misc/WSLInterop"):
            return True
        if "wsl" in os.environ.get("WSL_DISTRO_NAME", "").lower():
            return True
        if os.path.exists("/mnt/c/Windows"):
            return True
    return False


def get_nx_command():
    """Get NX command path based on platform"""
    if is_wsl():
        nx_exe = "/mnt/c/Program Files/Siemens/NX2406/NXBIN/run_journal.exe"
        if not os.path.exists(nx_exe):
            alternatives = [
                "/mnt/c/Program Files/Siemens/NX2207/NXBIN/run_journal.exe",
                "/mnt/c/Program Files/Siemens/NX2306/NXBIN/run_journal.exe",
                "/mnt/c/Program Files/Siemens/NX1980/NXBIN/run_journal.exe"
            ]
            for alt in alternatives:
                if os.path.exists(alt):
                    nx_exe = alt
                    break
        if not os.path.exists(nx_exe):
            found = False
            for root, dirs, files in os.walk("/mnt/c/Program Files"):
                if "run_journal.exe" in files:
                    nx_exe = os.path.join(root, "run_journal.exe")
                    print(f"Found NX executable at: {nx_exe}")
                    found = True
                    break
            if not found:
                raise FileNotFoundError(f"NX executable not found. Please install NX or update the path.")
        return nx_exe
    elif platform.system() == "Windows":
        nx_exe = "C:\\Program Files\\Siemens\\NX2406\\NXBIN\\run_journal.exe"
        if not os.path.exists(nx_exe):
            raise FileNotFoundError(f"NX executable not found at {nx_exe}. Please install NX or update the path.")
        return nx_exe
    else:
        if os.path.exists("/mnt/c/Windows"):
            return get_nx_command()  # Recursive call after detecting WSL
        raise RuntimeError(f"Unsupported platform: {platform.system()}. NX automation is only supported on Windows or WSL.")


def create_mock_executables():
    """Create mock executables for demonstration mode"""
    print("Creating mock executables and files for demonstration...")
    
    # Create mock gmsh_process script
    with open("./gmsh_process", "w") as f:
        f.write("#!/bin/bash\n")
        f.write("echo 'Mock gmsh_process running...'\n")
        f.write("echo 'Processing $2 to $4'\n")
        f.write("echo 'Created mock mesh file'\n")
        f.write("touch $4\n")
    
    # Create mock cfd_solver script
    with open("./cfd_solver", "w") as f:
        f.write("#!/bin/bash\n")
        f.write("echo 'Mock CFD solver running...'\n")
        f.write("echo 'Processing $2'\n")
        f.write("echo 'Created mock result files'\n")
        f.write("mkdir -p cfd_results\n")
        f.write("echo '0.123' > cfd_results/pressure.dat\n")
    
    # Create mock process_results script
    with open("./process_results", "w") as f:
        f.write("#!/bin/bash\n")
        f.write("echo 'Mock results processor running...'\n")
        f.write("echo 'Processing results from $2 to $4'\n")
        f.write("echo '0.123' > $4\n")
    
    # Create mock STEP file if it doesn't exist
    if not os.path.exists("INTAKE3D.step"):
        with open("INTAKE3D.step", "w") as f:
            f.write("Mock STEP file for intake geometry\n")
    
    # Create mock mesh file if it doesn't exist
    if not os.path.exists("INTAKE3D.msh"):
        with open("INTAKE3D.msh", "w") as f:
            f.write("Mock mesh file for intake geometry\n")
    
    # Create mock results directory and files
    os.makedirs("cfd_results", exist_ok=True)
    with open("cfd_results/pressure.dat", "w") as f:
        f.write("0.123\n")
        
    with open("processed_results.csv", "w") as f:
        f.write("0.123\n")
    
    # Make scripts executable
    try:
        os.chmod("./gmsh_process", 0o755)
        os.chmod("./cfd_solver", 0o755)
        os.chmod("./process_results", 0o755)
    except Exception as e:
        print(f"Warning: Could not set executable permissions: {str(e)}")
    
    print("Mock executables and files created successfully.")


def exp(L4, L5, alpha1, alpha2, alpha3):
    """Generate expressions for NX parameters"""
    expressions_list = []
    try:
        from Models.Expressions import format_exp, write_exp_file
        L4_expression = format_exp('L4', 'number', L4, unit='Meter')
        L5_expression = format_exp('L5', 'number', L5, unit='Meter')
        alpha1_expression = format_exp('alpha1', 'number', alpha1, unit='Degrees')
        alpha2_expression = format_exp('alpha2', 'number', alpha2, unit='Degrees')
        alpha3_expression = format_exp('alpha3', 'number', alpha3, unit='Degrees')
        expressions_list.append(L4_expression)
        expressions_list.append(L5_expression)
        expressions_list.append(alpha1_expression)
        expressions_list.append(alpha2_expression)
        expressions_list.append(alpha3_expression)
        write_exp_file(expressions_list, "expressions")
    except ImportError:
        # Simplified approach if Models.Expressions is not available
        with open("expressions.exp", "w") as f:
            f.write(f"L4={L4}\n")
            f.write(f"L5={L5}\n")
            f.write(f"alpha1={alpha1}\n")
            f.write(f"alpha2={alpha2}\n")
            f.write(f"alpha3={alpha3}\n")
    return expressions_list


class Workflow_Manager:
    """ReactPy component for workflow management - connects to main.py WorkflowManager"""
    def __init__(self, main_workflow_manager=None):
        """Initialize with reference to main workflow manager if available"""
        self.logger = logging.getLogger("intake-cfd-web.workflow")
        self.main_workflow_manager = main_workflow_manager
        
        # Create a fallback workflow manager if none was provided
        if self.main_workflow_manager is None:
            self.logger.info("No main workflow manager provided, creating fallback manager")
            self.main_workflow_manager = WorkflowManager(
                logger=self.logger.info,
                demo_mode=True
            )
            
            # Define standard workflow steps
            self.main_workflow_manager.define_workflow([
                {'name': 'CAD', 'status': 'pending', 'desc': 'Updates the NX model with parameters'},
                {'name': 'Mesh', 'status': 'pending', 'desc': 'Generates mesh from geometry'},
                {'name': 'CFD', 'status': 'pending', 'desc': 'Runs CFD simulation'},
                {'name': 'Results', 'status': 'pending', 'desc': 'Processes simulation results'}
            ])
            
        # Set up state for the React component
        self.workflow_running = False
        self.workflow_canceled = False
        self.parameters = {
            'L4': 3.0,
            'L5': 3.0,
            'alpha1': 15.0,
            'alpha2': 15.0,
            'alpha3': 15.0
        }
        self.current_step = None
        self.step_statuses = {step['name']: step['status'] for step in self.main_workflow_manager.workflow_steps}
        self.results = {}
        self.log_messages = []
        
    def render(self):
        """Render the workflow management UI component"""
        return rp.html.div(
            {"className": "workflow-manager"},
            [
                self._render_parameters_section(),
                self._render_workflow_visualization(),
                self._render_action_buttons(),
                self._render_status_section()
            ]
        )
        
    def _render_parameters_section(self):
        """Render the parameters input section"""
        parameters_inputs = []
        
        # Parameter inputs for L4, L5, alpha1, alpha2, alpha3
        for param_name in ['L4', 'L5', 'alpha1', 'alpha2', 'alpha3']:
            parameters_inputs.append(
                rp.html.div(
                    {"className": "parameter-input"},
                    [
                        rp.html.label({"htmlFor": f"param-{param_name}"}, f"{param_name}:"),
                        rp.html.input({
                            "id": f"param-{param_name}",
                            "type": "number",
                            "value": str(self.parameters.get(param_name, 0)),
                            "step": "0.1",
                            "onChange": lambda event, name=param_name: self._update_parameter(name, event)
                        })
                    ]
                )
            )
            
        return rp.html.div(
            {"className": "parameters-section"},
            [
                rp.html.h3("Parameters"),
                rp.html.div(
                    {"className": "parameters-grid"},
                    parameters_inputs
                )
            ]
        )
        
    def _update_parameter(self, param_name, event):
        """Update a parameter value"""
        try:
            new_value = float(event['target']['value'])
            self.parameters[param_name] = new_value
            self.logger.info(f"Parameter {param_name} updated to {new_value}")
        except (ValueError, TypeError) as e:
            self.logger.error(f"Error updating parameter {param_name}: {str(e)}")
            
    def _render_workflow_visualization(self):
        """Render the workflow visualization section"""
        workflow_steps = []
        
        for step in self.main_workflow_manager.workflow_steps:
            name = step['name']
            status = step['status']
            description = step.get('desc', '')
            
            # Update from main workflow manager
            self.step_statuses[name] = status
            
            status_class = f"step-status-{status}"
            
            workflow_steps.append(
                rp.html.div(
                    {"className": f"workflow-step {status_class}"},
                    [
                        rp.html.div(
                            {"className": "step-icon"},
                            self._get_status_icon(status)
                        ),
                        rp.html.div(
                            {"className": "step-content"},
                            [
                                rp.html.div({"className": "step-name"}, name),
                                rp.html.div({"className": "step-description"}, description)
                            ]
                        )
                    ]
                )
            )
            
            # Add connector between steps (except after last step)
            if name != self.main_workflow_manager.workflow_steps[-1]['name']:
                workflow_steps.append(
                    rp.html.div({"className": "step-connector"}, "→")
                )
                
        return rp.html.div(
            {"className": "workflow-visualization"},
            [
                rp.html.h3("Workflow"),
                rp.html.div(
                    {"className": "workflow-steps"},
                    workflow_steps
                )
            ]
        )
        
    def _get_status_icon(self, status):
        """Get the appropriate icon for a step status"""
        if status == 'completed':
            return "✓"
        elif status == 'running':
            return "⟳"
        elif status == 'error':
            return "✗"
        elif status == 'canceled':
            return "⊘"
        else:  # pending
            return "○"
            
    def _render_action_buttons(self):
        """Render the action buttons section"""
        buttons = []
        
        # Run button
        run_button = rp.html.button(
            {
                "className": "run-button",
                "onClick": lambda event: self._run_workflow(),
                "disabled": self.workflow_running
            },
            "Run Workflow"
        )
        buttons.append(run_button)
        
        # Cancel button (only enabled when workflow is running)
        cancel_button = rp.html.button(
            {
                "className": "cancel-button",
                "onClick": lambda event: self._cancel_workflow(),
                "disabled": not self.workflow_running
            },
            "Cancel"
        )
        buttons.append(cancel_button)
        
        # Reset button
        reset_button = rp.html.button(
            {
                "className": "reset-button",
                "onClick": lambda event: self._reset_workflow(),
                "disabled": self.workflow_running
            },
            "Reset"
        )
        buttons.append(reset_button)
        
        return rp.html.div(
            {"className": "action-buttons"},
            buttons
        )
        
    def _render_status_section(self):
        """Render the status section"""
        # Get last 10 log messages
        log_entries = []
        for message in self.log_messages[-10:]:
            log_entries.append(
                rp.html.div(
                    {"className": "log-entry"},
                    message
                )
            )
            
        return rp.html.div(
            {"className": "status-section"},
            [
                rp.html.h3("Status"),
                rp.html.div(
                    {"className": "status-display"},
                    f"Status: {'Running' if self.workflow_running else 'Ready'}"
                ),
                rp.html.div(
                    {"className": "log-display"},
                    log_entries
                )
            ]
        )
        
    def _run_workflow(self):
        """Run the workflow with current parameters"""
        if self.workflow_running:
            return
            
        self.workflow_running = True
        self.workflow_canceled = False
        self._add_log_message("Starting workflow...")
        
        # Run in a separate thread to avoid blocking the UI
        import threading
        self.workflow_thread = threading.Thread(
            target=self._run_workflow_thread,
            args=(self.parameters,)
        )
        self.workflow_thread.daemon = True
        self.workflow_thread.start()
        
    def _run_workflow_thread(self, parameters):
        """Run the workflow process in a thread"""
        try:
            # Call the main workflow manager
            results = self.main_workflow_manager.run_workflow(
                parameters,
                callback=self._update_step_status
            )
            
            if results:
                self.results = results
                self._add_log_message("Workflow completed successfully")
            elif self.workflow_canceled:
                self._add_log_message("Workflow was canceled")
            else:
                self._add_log_message("Workflow failed")
                
        except Exception as e:
            self._add_log_message(f"Error in workflow: {str(e)}")
            traceback.print_exc()
            
        finally:
            self.workflow_running = False
            
    def _update_step_status(self, step_name, status, error_message=None):
        """Update the status of a workflow step (callback for main workflow manager)"""
        self.step_statuses[step_name] = status
        
        if status == 'running':
            self._add_log_message(f"Running step: {step_name}")
        elif status == 'completed':
            self._add_log_message(f"Step completed: {step_name}")
        elif status == 'error':
            message = f"Error in step {step_name}"
            if error_message:
                message += f": {error_message}"
            self._add_log_message(message)
            
    def _cancel_workflow(self):
        """Cancel the running workflow"""
        if not self.workflow_running:
            return
            
        self._add_log_message("Canceling workflow...")
        self.workflow_canceled = True
        self.main_workflow_manager.cancel_workflow()
        
    def _reset_workflow(self):
        """Reset the workflow state"""
        if self.workflow_running:
            return
            
        self._add_log_message("Resetting workflow...")
        
        # Reset step statuses
        for step in self.main_workflow_manager.workflow_steps:
            step['status'] = 'pending'
            self.step_statuses[step['name']] = 'pending'
            
        # Clear results
        self.results = {}
        
    def _add_log_message(self, message):
        """Add a message to the log"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        self.log_messages.append(log_message)
        self.logger.info(message)


# Keep the original WorkflowManager class for compatibility
class WorkflowManager:
    """Manages the execution of CFD workflow processes"""
    def __init__(self, logger=None, demo_mode=False):
        self.logger = logger or print
        self.demo_mode = demo_mode
        self.workflow_steps = []
        self.current_step = None
        self.workflow_running = False
        self.workflow_canceled = False
        self.results = {}
        self.parameters = {}
        
        # Initialize resources
        self._initialize_resources()
        
    def _initialize_resources(self):
        """Initialize any resources needed by the workflow"""
        # Create necessary directories
        os.makedirs("cfd_results", exist_ok=True)
        
        # Create mock executables if in demo mode
        if self.demo_mode:
            create_mock_executables()
        
    def define_workflow(self, steps):
        """Define the workflow steps"""
        self.workflow_steps = steps
        self.logger(f"Workflow defined with {len(steps)} steps")
    
    def get_step_status(self, step_name):
        """Get the status of a specific workflow step"""
        for step in self.workflow_steps:
            if step['name'] == step_name:
                return step.get('status', 'pending')
        return None
    
    def update_step_status(self, step_name, status):
        """Update the status of a workflow step"""
        for step in self.workflow_steps:
            if step['name'] == step_name:
                step['status'] = status
                self.logger(f"Step '{step_name}' status updated to '{status}'")
                break

    def run_workflow(self, parameters, callback=None):
        """Run the complete workflow with the given parameters"""
        if self.workflow_running:
            self.logger("Workflow already running")
            return None
            
        self.workflow_running = True
        self.workflow_canceled = False
        self.parameters = parameters
        self.results = {}
        
        # Reset all steps to pending
        for step in self.workflow_steps:
            step['status'] = 'pending'
        
        # Execute each step in sequence
        try:
            for step in self.workflow_steps:
                if self.workflow_canceled:
                    self.logger("Workflow canceled")
                    break
                    
                step_name = step['name']
                self.current_step = step_name
                self.update_step_status(step_name, 'running')
                
                if callback:
                    callback(step_name, 'running')
                
                try:
                    result = self._execute_step(step, parameters)
                    self.results[step_name] = result
                    self.update_step_status(step_name, 'completed')
                    
                    if callback:
                        callback(step_name, 'completed')
                        
                except Exception as e:
                    self.logger(f"Error in step '{step_name}': {str(e)}")
                    self.update_step_status(step_name, 'error')
                    
                    if callback:
                        callback(step_name, 'error', str(e))
                        
                    raise
            
            if not self.workflow_canceled:
                self.logger("Workflow completed successfully")
                return self.results
                
        except Exception as e:
            self.logger(f"Workflow failed: {str(e)}")
            traceback.print_exc()
            return None
            
        finally:
            self.workflow_running = False
            self.current_step = None

    def _execute_step(self, step, parameters):
        """Execute a single workflow step"""
        step_name = step['name']
        self.logger(f"Executing step: {step_name}")
        
        if step_name == "CAD":
            return self._execute_cad_step(parameters)
        elif step_name == "Mesh":
            return self._execute_mesh_step(parameters)
        elif step_name == "CFD":
            return self._execute_cfd_step(parameters)
        elif step_name == "Results":
            return self._execute_results_step(parameters)
        else:
            raise ValueError(f"Unknown step: {step_name}")

    def _execute_cad_step(self, parameters):
        """Execute CAD step to update geometry"""
        self.logger("Updating NX model...")
        
        # Extract parameters
        L4 = parameters.get('L4', 3.0)
        L5 = parameters.get('L5', 3.0)
        alpha1 = parameters.get('alpha1', 15.0)
        alpha2 = parameters.get('alpha2', 15.0)
        alpha3 = parameters.get('alpha3', 15.0)
        
        # Generate expressions file
        exp(L4, L5, alpha1, alpha2, alpha3)
        
        # Run NX workflow
        if self.demo_mode:
            self.logger("DEMO MODE: Simulating NX workflow")
            time.sleep(2)  # Simulate processing time
            step_file = "INTAKE3D.step"
            
            # Create a mock STEP file if it doesn't exist
            if not os.path.exists(step_file):
                with open(step_file, "w") as f:
                    f.write("Mock STEP file for demo mode\n")
                    
            self.logger(f"DEMO MODE: Mock STEP file created at {step_file}")
        else:
            nx_exe = get_nx_command()
            self.logger(f"Using NX executable: {nx_exe}")
            
            express_script = "C:/Users/Mohammed/Desktop/Intake-CFD-Project/nx/nx_express2.py"
            export_script = "C:/Users/Mohammed/Desktop/Intake-CFD-Project/nx/nx_export.py"
            part_file = "C:/Users/Mohammed/Desktop/Intake-CFD-Project/nx/INTAKE3D.prt"
            
            # Check if files exist
            for file_path in [express_script, export_script, part_file]:
                if not os.path.exists(file_path):
                    raise FileNotFoundError(f"Required file not found: {file_path}")
            
            self.logger(f"Running NX script: {express_script} with part: {part_file}")
            run_command([
                nx_exe,
                express_script,
                "-args", part_file
            ])
            
            self.logger(f"Running NX export script: {export_script} with part: {part_file}")
            run_command([
                nx_exe,
                export_script,
                "-args", part_file
            ])
            
            step_file = "C:/Users/Mohammed/Desktop/Intake-CFD-Project/nx/INTAKE3D.step"
            wsl_step_file = step_file.replace('C:', '/mnt/c') if is_wsl() else step_file
            
            if not os.path.exists(wsl_step_file):
                raise FileNotFoundError(f"STEP file not found at {wsl_step_file}")
                
            # Copy to local directory
            import shutil
            local_step_file = "INTAKE3D.step"
            shutil.copy(wsl_step_file, local_step_file)
            step_file = local_step_file
            
            self.logger(f"STEP file successfully created: {step_file}")
        
        return step_file
    
    def _execute_mesh_step(self, parameters):
        """Execute meshing step"""
        # Get input from previous step
        step_file = self.results.get("CAD")
        if not step_file:
            raise ValueError("CAD step result not found")
        
        mesh_file = "INTAKE3D.msh"
        
        if self.demo_mode:
            self.logger("DEMO MODE: Simulating mesh generation")
            time.sleep(2)  # Simulate processing time
            
            # Create a mock mesh file
            with open(mesh_file, "w") as f:
                f.write("Mock mesh file for demo mode\n")
                
            self.logger(f"DEMO MODE: Mock mesh file created at {mesh_file}")
        else:
            self.logger(f"Generating mesh from {step_file}")
            run_command(["./gmsh_process", "--input", step_file, "--output", mesh_file, "--auto-refine", "--curvature-adapt"])
            
            if not os.path.exists(mesh_file):
                raise FileNotFoundError(f"Mesh file not found at {mesh_file}")
                
            self.logger(f"Mesh file successfully created: {mesh_file}")
        
        return mesh_file
    
    def _execute_cfd_step(self, parameters):
        """Execute CFD simulation step"""
        # Get input from previous step
        mesh_file = self.results.get("Mesh")
        if not mesh_file:
            raise ValueError("Mesh step result not found")
        
        results_dir = "cfd_results"
        
        if self.demo_mode:
            self.logger("DEMO MODE: Simulating CFD simulation")
            time.sleep(3)  # Simulate longer processing time
            
            # Create demo CFD results
            os.makedirs(results_dir, exist_ok=True)
            self._create_demo_cfd_results(results_dir, parameters)
                
            self.logger(f"DEMO MODE: Mock CFD results created in {results_dir}")
        else:
            self.logger(f"Running CFD simulation with mesh {mesh_file}")
            run_command(["./cfd_solver", "--mesh", mesh_file, "--solver", "openfoam"])
            
            if not os.path.exists(results_dir):
                raise FileNotFoundError(f"CFD results directory not found at {results_dir}")
                
            self.logger(f"CFD simulation completed successfully")
        
        return results_dir
    
    def _execute_results_step(self, parameters):
        """Process simulation results"""
        # Get input from previous step
        results_dir = self.results.get("CFD")
        if not results_dir:
            raise ValueError("CFD step result not found")
        
        output_file = "processed_results.csv"
        
        if self.demo_mode:
            self.logger("DEMO MODE: Simulating results processing")
            time.sleep(1)  # Simulate processing time
            
            # Create a mock results file
            with open(output_file, "w") as f:
                f.write("parameter,value\n")
                f.write(f"pressure_drop,{0.5 + 0.1*parameters.get('L4', 3.0) - 0.05*parameters.get('alpha1', 15.0)}\n")
                f.write(f"flow_rate,{2.0 + 0.2*parameters.get('L5', 3.0) + 0.02*parameters.get('alpha2', 15.0)}\n")
                f.write(f"uniformity,{85.0 + 0.3*parameters.get('alpha3', 15.0)}\n")
                
            self.logger(f"DEMO MODE: Mock processed results created at {output_file}")
            
            # Also create visualization data
            viz_data = self._generate_visualization_data(parameters)
            
            processed_results = {
                'file': output_file,
                'metrics': {
                    'pressure_drop': 0.5 + 0.1*parameters.get('L4', 3.0) - 0.05*parameters.get('alpha1', 15.0),
                    'flow_rate': 2.0 + 0.2*parameters.get('L5', 3.0) + 0.02*parameters.get('alpha2', 15.0),
                    'uniformity': 85.0 + 0.3*parameters.get('alpha3', 15.0)
                },
                'visualization': viz_data
            }
        else:
            self.logger(f"Processing CFD results from {results_dir}")
            run_command(["./process_results", "--input", results_dir, "--output", output_file])
            
            if not os.path.exists(output_file):
                raise FileNotFoundError(f"Results file not found at {output_file}")
                
            self.logger(f"Results processing completed successfully")
            
            # Parse results file
            processed_results = self._parse_results_file(output_file)
        
        return processed_results

    def cancel_workflow(self):
        """Cancel the running workflow"""
        if self.workflow_running:
            self.workflow_canceled = True
            self.logger("Canceling workflow...")
            return True
        return False
    
    def _create_demo_cfd_results(self, results_dir, parameters):
        """Create demo CFD results files"""
        os.makedirs(results_dir, exist_ok=True)
        
        # Extract parameters
        L4 = parameters.get('L4', 3.0)
        L5 = parameters.get('L5', 3.0)
        alpha1 = parameters.get('alpha1', 15.0)
        alpha2 = parameters.get('alpha2', 15.0)
        alpha3 = parameters.get('alpha3', 15.0)
        
        # Create pressure data file
        with open(f"{results_dir}/pressure.dat", "w") as f:
            f.write(f"# Pressure data for L4={L4}, L5={L5}, alpha1={alpha1}, alpha2={alpha2}, alpha3={alpha3}\n")
            f.write("# x y z pressure\n")
            for i in range(100):
                x = i * 0.1
                y = 0.0
                z = 0.0
                pressure = 0.5 + 0.1*L4 - 0.05*alpha1 + 0.2*math.sin(x)
                f.write(f"{x} {y} {z} {pressure}\n")
        
        # Create velocity data file
        with open(f"{results_dir}/velocity.dat", "w") as f:
            f.write(f"# Velocity data for L4={L4}, L5={L5}, alpha1={alpha1}, alpha2={alpha2}, alpha3={alpha3}\n")
            f.write("# x y z vx vy vz\n")
            for i in range(100):
                x = i * 0.1
                y = 0.0
                z = 0.0
                vx = 2.0 + 0.2*L5 + 0.02*alpha2 + 0.3*math.cos(x)
                vy = 0.1*math.sin(x)
                vz = 0.05*math.cos(x)
                f.write(f"{x} {y} {z} {vx} {vy} {vz}\n")
    
    def _generate_visualization_data(self, parameters):
        """Generate visualization data for demo mode"""
        # Extract parameters
        L4 = parameters.get('L4', 3.0)
        L5 = parameters.get('L5', 3.0)
        alpha1 = parameters.get('alpha1', 15.0)
        alpha2 = parameters.get('alpha2', 15.0)
        alpha3 = parameters.get('alpha3', 15.0)
        
        # Create sample data
        X, Y = np.meshgrid(np.linspace(-5, 5, 50), np.linspace(-5, 5, 50))
        R = np.sqrt(X**2 + Y**2)
        
        # Calculate fields based on parameters
        intensity = 0.5 + 0.1 * L4 + 0.05 * L5 + 0.01 * (alpha1 + alpha2 + alpha3)
        phase = 0.1 * alpha1
        
        return {
            'X': X.tolist(),
            'Y': Y.tolist(),
            'Z': (intensity * np.sin(R + phase) / (R + 0.1)).tolist(),
            'Pressure': (intensity * (1 - np.exp(-0.1 * R**2)) * (1 + 0.2 * np.sin(5*R))).tolist(),
            'Velocity': (intensity * 2 * np.exp(-0.2 * R**2) * (1 + 0.1 * np.cos(5*Y))).tolist(),
            'Temperature': (intensity * (0.5 + 0.5 * np.tanh(R - 2))).tolist(),
            'Turbulence': (intensity * 0.1 * (X**2 + Y**2) * np.exp(-0.1 * R)).tolist()
        }
    
    def _parse_results_file(self, file_path):
        """Parse results from CSV file"""
        metrics = {}
        
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
                
            for line in lines:
                if ',' in line:
                    key, value = line.strip().split(',', 1)
                    try:
                        metrics[key] = float(value)
                    except ValueError:
                        metrics[key] = value
        except Exception as e:
            self.logger(f"Error parsing results file: {str(e)}")
        
        return {
            'file': file_path,
            'metrics': metrics
        }
