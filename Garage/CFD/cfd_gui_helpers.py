"""
CFD GUI Helper module for the Intake CFD Optimization Suite.

This module provides utility functions and classes to help with
GUI integration of CFD simulation capabilities.
"""

import os
import sys
import logging
import json
import time
import threading
from typing import Dict, List, Tuple, Union, Optional, Any, Callable
from pathlib import Path
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("cfd_gui_helpers")

from .cfd_runner import (
    CFDRunner, 
    CFDModel, 
    CFDSolverType, 
    CFDAnalysisType,
    CFDCaseStatus,
    CFDCaseManager,
    get_case_summary
)

class CFDBackgroundTask:
    """Class for running CFD tasks in the background and reporting progress."""
    
    def __init__(self, name: str, callback: Optional[Callable[[Dict[str, Any]], None]] = None):
        """
        Initialize a background task.
        
        Args:
            name: Name of the task
            callback: Function to call with progress updates
        """
        self.name = name
        self.callback = callback
        self.thread = None
        self.running = False
        self.status = "ready"
        self.progress = 0.0
        self.result = None
        self.error = None
        self.start_time = None
        self.end_time = None
    
    def start(self, target: Callable, args: Optional[Tuple] = None, kwargs: Optional[Dict] = None) -> bool:
        """
        Start the task.
        
        Args:
            target: Function to run
            args: Arguments for the function
            kwargs: Keyword arguments for the function
            
        Returns:
            True if started successfully
        """
        if self.running:
            return False
        
        args = args or ()
        kwargs = kwargs or {}
        
        # Wrap the target function to catch exceptions and update status
        def wrapped_target(*args, **kwargs):
            self.start_time = time.time()
            self.running = True
            self.status = "running"
            self.progress = 0.0
            self.error = None
            self.result = None
            
            # Report initial status
            self._report_status()
            
            try:
                # Run the actual function
                result = target(*args, **kwargs)
                self.result = result
                self.status = "completed"
                self.progress = 100.0
            except Exception as e:
                self.error = str(e)
                self.status = "failed"
                logger.error(f"Error in background task '{self.name}': {e}")
                logger.error(traceback.format_exc())
            finally:
                self.running = False
                self.end_time = time.time()
                # Report final status
                self._report_status()
        
        # Create and start the thread
        self.thread = threading.Thread(target=wrapped_target, args=args, kwargs=kwargs)
        self.thread.daemon = True
        self.thread.start()
        
        return True
    
    def update_progress(self, progress: float, status: Optional[str] = None) -> None:
        """
        Update the progress of the task.
        
        Args:
            progress: Progress percentage (0-100)
            status: Optional status message
        """
        self.progress = max(0.0, min(100.0, progress))
        if status:
            self.status = status
        
        # Report status update
        self._report_status()
    
    def _report_status(self) -> None:
        """Report status via callback."""
        if self.callback:
            status_info = {
                "name": self.name,
                "running": self.running,
                "status": self.status,
                "progress": self.progress,
                "result": self.result,
                "error": self.error,
                "start_time": self.start_time,
                "end_time": self.end_time,
                "elapsed": time.time() - (self.start_time or time.time()) if self.start_time else 0
            }
            
            try:
                self.callback(status_info)
            except Exception as e:
                logger.error(f"Error in callback for task '{self.name}': {e}")
    
    def is_running(self) -> bool:
        """Check if the task is still running."""
        return self.running
    
    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the task."""
        return {
            "name": self.name,
            "running": self.running,
            "status": self.status,
            "progress": self.progress,
            "result": self.result,
            "error": self.error,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "elapsed": time.time() - (self.start_time or time.time()) if self.start_time else 0
        }

class CFDSimulationController:
    """Controller class for managing CFD simulations from a GUI."""
    
    def __init__(self, working_dir: str):
        """
        Initialize the controller.
        
        Args:
            working_dir: Working directory for simulations
        """
        self.working_dir = working_dir
        os.makedirs(working_dir, exist_ok=True)
        
        # Create a case manager
        self.case_manager = CFDCaseManager()
        
        # Background tasks
        self.tasks = {}
        
        # Default mesh and configuration paths
        self.config_dir = os.path.join(working_dir, "configs")
        os.makedirs(self.config_dir, exist_ok=True)
    
    def load_model(self, filepath: str) -> Optional[CFDModel]:
        """
        Load a CFD model from a file.
        
        Args:
            filepath: Path to the model file
            
        Returns:
            Loaded model or None if error
        """
        try:
            return CFDModel.load_from_file(filepath)
        except Exception as e:
            logger.error(f"Error loading model from {filepath}: {e}")
            return None
    
    def save_model(self, model: CFDModel, filepath: str) -> bool:
        """
        Save a CFD model to a file.
        
        Args:
            model: Model to save
            filepath: Path to save to
            
        Returns:
            True if saved successfully
        """
        try:
            model.save_to_file(filepath)
            return True
        except Exception as e:
            logger.error(f"Error saving model to {filepath}: {e}")
            return False
    
    def create_task(self, name: str, callback: Optional[Callable] = None) -> str:
        """
        Create a new background task.
        
        Args:
            name: Name for the task
            callback: Callback function for progress updates
            
        Returns:
            Task ID
        """
        task_id = f"task_{int(time.time())}_{name}"
        self.tasks[task_id] = CFDBackgroundTask(name, callback)
        return task_id
    
    def run_simulation(self, model: CFDModel, 
                       solver_type: Union[CFDSolverType, str] = CFDSolverType.OPENFOAM,
                       analysis_type: Union[CFDAnalysisType, str] = CFDAnalysisType.STEADY,
                       num_processors: int = 1,
                       task_id: Optional[str] = None,
                       callback: Optional[Callable] = None) -> str:
        """
        Run a CFD simulation.
        
        Args:
            model: CFD model to simulate
            solver_type: Type of solver to use
            analysis_type: Type of analysis
            num_processors: Number of processors to use
            task_id: Optional task ID (created if not provided)
            callback: Callback function for progress updates
            
        Returns:
            Task ID
        """
        # Create task if not provided
        if not task_id:
            task_id = self.create_task(f"Simulate {model.name}", callback)
        
        # Get the task
        task = self.tasks[task_id]
        
        # Function to run in background
        def run_simulation_task():
            runner = CFDRunner(
                solver_type=solver_type,
                analysis_type=analysis_type,
                num_processors=num_processors
            )
            
            # Update progress
            task.update_progress(5, "Setting up case")
            
            # Set up the case
            case_dir = runner.setup_case(model)
            
            # Add to case manager
            case_id = f"case_{int(time.time())}_{model.name}"
            self.case_manager.add_case(case_id, case_dir, CFDCaseStatus.RUNNING)
            
            # Update progress
            task.update_progress(10, "Running simulation")
            
            # Run the case
            job_id = runner.run_case(case_dir, background=True)
            
            # Monitor job
            while True:
                time.sleep(1)  # Check every second
                
                try:
                    status = runner.get_job_status(job_id)
                    
                    # Extract progress information
                    progress = 10  # Start at 10%
                    message = status.get('message', 'Running simulation')
                    
                    # Try to parse log for progress
                    if 'log_tail' in status:
                        log_tail = status['log_tail']
                        # Look for iteration or time information
                        for line in log_tail.splitlines():
                            if "Time =" in line:
                                try:
                                    time_val = float(line.split("=")[1].strip().split()[0])
                                    # Convert time into progress (assuming end_time in model settings)
                                    end_time = model.solver_settings.get('end_time', 1000)
                                    progress = 10 + min(89, 89 * time_val / end_time)
                                except:
                                    pass
                    
                    # Update task progress
                    task.update_progress(progress, f"Running: {message}")
                    
                    # Check if completed
                    if status['status'] in ['COMPLETED', 'FAILED']:
                        # Update case manager
                        self.case_manager.update_status(
                            case_id, 
                            CFDCaseStatus.COMPLETED if status['status'] == 'COMPLETED' else CFDCaseStatus.FAILED
                        )
                        
                        if status['status'] == 'COMPLETED':
                            # Get results
                            results = runner.get_job_results(job_id)
                            self.case_manager.set_result(case_id, results)
                            
                            # Update task
                            task.update_progress(100, "Simulation completed")
                            
                            # Return results
                            return {
                                'case_id': case_id,
                                'case_dir': case_dir,
                                'results': results
                            }
                        else:
                            # Simulation failed
                            task.update_progress(100, f"Simulation failed: {status.get('message', 'Unknown error')}")
                            return {
                                'case_id': case_id,
                                'case_dir': case_dir,
                                'error': status.get('message', 'Unknown error')
                            }
                            
                except Exception as e:
                    logger.error(f"Error monitoring job: {e}")
                    task.update_progress(100, f"Error: {str(e)}")
                    return {
                        'case_id': case_id,
                        'case_dir': case_dir,
                        'error': str(e)
                    }
        
        # Start the task
        task.start(run_simulation_task)
        
        return task_id
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Get the status of a task.
        
        Args:
            task_id: ID of the task
            
        Returns:
            Status dictionary
        """
        if task_id in self.tasks:
            return self.tasks[task_id].get_status()
        else:
            return {
                "name": "unknown",
                "running": False,
                "status": "not_found",
                "progress": 0.0,
                "error": "Task not found"
            }
    
    def get_case_list(self) -> List[Dict[str, Any]]:
        """
        Get a list of all cases.
        
        Returns:
            List of case information dictionaries
        """
        case_list = []
        
        for case_id in self.case_manager.list_cases():
            case_info = self.case_manager.get_case_info(case_id)
            
            # Add summary information
            if case_info and 'case_dir' in case_info:
                case_dir = case_info['case_dir']
                summary = get_case_summary(case_dir)
                
                case_list.append({
                    'case_id': case_id,
                    'case_dir': case_dir,
                    'status': case_info.get('status', CFDCaseStatus.UNKNOWN),
                    'start_time': case_info.get('start_time'),
                    'end_time': case_info.get('end_time'),
                    'summary': summary
                })
        
        return case_list
    
    def get_case_details(self, case_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a case.
        
        Args:
            case_id: ID of the case
            
        Returns:
            Case details dictionary
        """
        case_info = self.case_manager.get_case_info(case_id)
        
        if not case_info:
            return {'error': 'Case not found'}
        
        # Get summary for the case directory
        if 'case_dir' in case_info:
            summary = get_case_summary(case_info['case_dir'])
            
            # Add to case info
            case_info['summary'] = summary
        
        return case_info
    
    def generate_case_report(self, case_id: str) -> str:
        """
        Generate a report for a case.
        
        Args:
            case_id: ID of the case
            
        Returns:
            Path to the generated report
        """
        case_info = self.case_manager.get_case_info(case_id)
        
        if not case_info or 'case_dir' not in case_info:
            return ""
        
        # Import visualizer here to avoid circular imports
        from .cfd_visualizer import CFDVisualizer
        
        # Generate report
        return CFDVisualizer.generate_report(case_info['case_dir'])
