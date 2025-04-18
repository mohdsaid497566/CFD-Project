"""
CFD Batch Processing module for the Intake CFD Optimization Suite.

This module provides functionality for running multiple CFD simulations
in batch mode, with parametric variations and result collection.
"""

import os
import sys
import logging
import json
import time
import concurrent.futures
from typing import Dict, List, Tuple, Union, Optional, Any, Callable
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np
import threading

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("cfd_batch")

from .cfd_runner import (
    CFDRunner, 
    CFDModel, 
    CFDSolverType, 
    CFDAnalysisType,
    validate_cfd_model,
    get_case_summary
)

class CFDParametricStudy:
    """Class for running parametric CFD studies with varying parameters."""
    
    def __init__(self, 
                base_model: CFDModel,
                solver_type: CFDSolverType = CFDSolverType.OPENFOAM,
                analysis_type: CFDAnalysisType = CFDAnalysisType.STEADY,
                num_processors: int = 1,
                max_parallel_cases: int = 1):
        """
        Initialize a parametric CFD study.
        
        Args:
            base_model: Base CFD model to use as a template
            solver_type: Type of solver to use
            analysis_type: Type of analysis (steady/transient)
            num_processors: Number of processors per simulation
            max_parallel_cases: Maximum number of cases to run in parallel
        """
        self.base_model = base_model
        self.solver_type = solver_type
        self.analysis_type = analysis_type
        self.num_processors = num_processors
        self.max_parallel_cases = max_parallel_cases
        
        # Directory for parametric study
        self.study_dir = os.path.join(base_model.working_dir, "parametric_study")
        os.makedirs(self.study_dir, exist_ok=True)
        
        # Tracking for cases
        self.cases = []  # List of case dictionaries
        self.active_jobs = {}  # job_id -> case_index
        self.case_results = {}  # case_index -> results
        
        # Runner for simulations
        self.runner = CFDRunner(
            solver_type=solver_type,
            analysis_type=analysis_type,
            num_processors=num_processors
        )
        
        # Lock for thread safety
        self._lock = threading.Lock()
    
    def add_case(self, case_name: str, parameters: Dict[str, Any]) -> int:
        """
        Add a case to the parametric study.
        
        Args:
            case_name: Name for this case
            parameters: Dictionary of parameters to modify
            
        Returns:
            Index of the added case
        """
        case = {
            "name": case_name,
            "parameters": parameters,
            "status": "pending",
            "case_dir": None,
            "job_id": None,
            "start_time": None,
            "end_time": None,
            "results": None
        }
        
        with self._lock:
            self.cases.append(case)
            case_index = len(self.cases) - 1
        
        logger.info(f"Added case {case_index}: {case_name}")
        return case_index
    
    def add_parametric_sweep(self, parameter_sweeps: Dict[str, List[Any]], 
                           name_template: str = "case_{index}") -> List[int]:
        """
        Add a parametric sweep with multiple parameter combinations.
        
        Args:
            parameter_sweeps: Dictionary mapping parameter names to lists of values
            name_template: Template for case names, with {index} placeholder
            
        Returns:
            List of case indices added
        """
        # Generate parameter combinations
        import itertools
        
        param_names = list(parameter_sweeps.keys())
        param_values = list(parameter_sweeps.values())
        
        added_indices = []
        
        for i, values in enumerate(itertools.product(*param_values)):
            # Create parameter dictionary for this combination
            params = {name: value for name, value in zip(param_names, values)}
            
            # Create case name with the current index
            case_name = name_template.format(index=i)
            
            # Add this case
            case_index = self.add_case(case_name, params)
            added_indices.append(case_index)
        
        logger.info(f"Added {len(added_indices)} cases for parametric sweep")
        return added_indices
    
    def _apply_parameters(self, model: CFDModel, parameters: Dict[str, Any]) -> None:
        """
        Apply parameters to a model.
        
        Args:
            model: Model to modify
            parameters: Parameters to apply
        """
        # Handle boundary condition parameters (format: "boundary_name.parameter")
        for param, value in parameters.items():
            if "." in param:
                boundary, param_name = param.split(".", 1)
                
                if boundary in model.boundary_conditions:
                    if "values" not in model.boundary_conditions[boundary]:
                        model.boundary_conditions[boundary]["values"] = {}
                        
                    model.boundary_conditions[boundary]["values"][param_name] = value
                    logger.debug(f"Set {boundary}.{param_name} = {value}")
            else:
                # Assume it's a solver setting
                model.solver_settings[param] = value
                logger.debug(f"Set solver setting {param} = {value}")
    
    def _prepare_case(self, case_index: int) -> Tuple[bool, Optional[CFDModel], Optional[str]]:
        """
        Prepare a case for running.
        
        Args:
            case_index: Index of the case to prepare
            
        Returns:
            Tuple of (success, model, case_dir)
        """
        case = self.cases[case_index]
        
        # Create a new model based on the base model
        model = CFDModel(
            name=case["name"],
            mesh_file=self.base_model.mesh_file,
            boundary_conditions=self.base_model.boundary_conditions.copy(),
            solver_settings=self.base_model.solver_settings.copy(),
            working_dir=os.path.join(self.study_dir, case["name"])
        )
        
        # Apply parameters
        self._apply_parameters(model, case["parameters"])
        
        # Validate model
        valid, reason = validate_cfd_model(model)
        if not valid:
            logger.error(f"Invalid model for case {case_index}: {reason}")
            return False, None, None
        
        # Prepare case directory
        try:
            case_dir = self.runner.setup_case(model)
            logger.info(f"Prepared case directory for case {case_index}: {case_dir}")
            return True, model, case_dir
        except Exception as e:
            logger.error(f"Error preparing case {case_index}: {e}")
            return False, None, None
    
    def _run_case(self, case_index: int) -> None:
        """
        Run a single case.
        
        Args:
            case_index: Index of the case to run
        """
        with self._lock:
            case = self.cases[case_index]
            
            # Update status
            case["status"] = "setting_up"
            case["start_time"] = time.time()
        
        # Prepare the case
        success, model, case_dir = self._prepare_case(case_index)
        
        if not success:
            with self._lock:
                case["status"] = "failed"
                case["end_time"] = time.time()
                self.case_results[case_index] = {"error": "Case preparation failed"}
            return
        
        with self._lock:
            case["case_dir"] = case_dir
            case["status"] = "running"
        
        try:
            # Run the case in background mode
            job_id = self.runner.run_case(case_dir, background=True)
            
            with self._lock:
                case["job_id"] = job_id
                self.active_jobs[job_id] = case_index
            
            logger.info(f"Started case {case_index} with job ID {job_id}")
            
            # Monitor job status
            while True:
                time.sleep(5)  # Check every 5 seconds
                
                status = self.runner.get_job_status(job_id)
                
                if status["status"] in ["COMPLETED", "FAILED"]:
                    with self._lock:
                        case["status"] = status["status"].lower()
                        case["end_time"] = time.time()
                        
                        # Get results if completed
                        if status["status"] == "COMPLETED":
                            try:
                                results = self.runner.get_job_results(job_id)
                                self.case_results[case_index] = results
                                logger.info(f"Case {case_index} completed successfully")
                            except Exception as e:
                                logger.error(f"Error getting results for case {case_index}: {e}")
                                self.case_results[case_index] = {"error": str(e)}
                        else:
                            logger.warning(f"Case {case_index} failed")
                            self.case_results[case_index] = {"error": status["message"]}
                        
                        # Remove from active jobs
                        del self.active_jobs[job_id]
                    
                    break
        
        except Exception as e:
            with self._lock:
                case["status"] = "failed"
                case["end_time"] = time.time()
                self.case_results[case_index] = {"error": str(e)}
                
                # Remove from active jobs if job_id exists
                if "job_id" in case and case["job_id"] in self.active_jobs:
                    del self.active_jobs[case["job_id"]]
            
            logger.error(f"Error running case {case_index}: {e}")
    
    def run_all_cases(self) -> None:
        """Run all cases sequentially."""
        for i in range(len(self.cases)):
            if self.cases[i]["status"] == "pending":
                self._run_case(i)
    
    def run_cases_parallel(self) -> None:
        """Run cases in parallel up to max_parallel_cases."""
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_parallel_cases) as executor:
            # Submit all pending cases
            futures = []
            for i in range(len(self.cases)):
                if self.cases[i]["status"] == "pending":
                    futures.append(executor.submit(self._run_case, i))
            
            # Wait for all to complete
            concurrent.futures.wait(futures)
    
    def get_case_status(self, case_index: int) -> Dict[str, Any]:
        """
        Get status of a specific case.
        
        Args:
            case_index: Index of the case
            
        Returns:
            Dictionary with case status information
        """
        with self._lock:
            if case_index >= len(self.cases):
                raise ValueError(f"Invalid case index: {case_index}")
            
            case = self.cases[case_index].copy()
            
            # Add results if available
            if case_index in self.case_results:
                case["results"] = self.case_results[case_index]
            
            return case
    
    def get_all_results(self) -> pd.DataFrame:
        """
        Get results for all completed cases as a pandas DataFrame.
        
        Returns:
            DataFrame with case parameters and results
        """
        # Prepare data for DataFrame
        data = []
        
        with self._lock:
            for i, case in enumerate(self.cases):
                if case["status"] == "completed" and i in self.case_results:
                    # Start with parameters
                    row = case["parameters"].copy()
                    
                    # Add case name
                    row["case_name"] = case["name"]
                    
                    # Add case directory
                    row["case_dir"] = case["case_dir"]
                    
                    # Add runtime
                    if case["start_time"] and case["end_time"]:
                        row["runtime"] = case["end_time"] - case["start_time"]
                    
                    # Add results
                    results = self.case_results[i]
                    
                    # Add force coefficients
                    if "force_coefficients" in results:
                        for k, v in results["force_coefficients"].items():
                            row[f"force_{k}"] = v
                    
                    # Add final residuals
                    if "residuals" in results:
                        for k, v in results["residuals"].items():
                            row[f"residual_{k}"] = v
                    
                    data.append(row)
        
        # Create DataFrame
        df = pd.DataFrame(data)
        
        return df
    
    def save_results(self, filepath: str) -> None:
        """
        Save results to a CSV file.
        
        Args:
            filepath: Path to save the results
        """
        df = self.get_all_results()
        df.to_csv(filepath, index=False)
        logger.info(f"Saved results to {filepath}")
    
    def save_study(self, filepath: str) -> None:
        """
        Save the entire study configuration and results to a JSON file.
        
        Args:
            filepath: Path to save the study
        """
        # Create dictionary for serialization
        data = {
            "base_model": self.base_model.to_dict(),
            "solver_type": str(self.solver_type),
            "analysis_type": str(self.analysis_type),
            "num_processors": self.num_processors,
            "max_parallel_cases": self.max_parallel_cases,
            "study_dir": self.study_dir,
            "cases": self.cases,
            "results": {}
        }
        
        # Add serializable results
        for case_index, results in self.case_results.items():
            # Filter out non-serializable parts of results
            serializable_results = {}
            for k, v in results.items():
                if k in ["case_dir", "force_coefficients", "residuals"]:
                    serializable_results[k] = v
            
            data["results"][str(case_index)] = serializable_results
        
        # Save to file
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=4)
        
        logger.info(f"Saved study to {filepath}")
    
    @classmethod
    def load_study(cls, filepath: str) -> 'CFDParametricStudy':
        """
        Load a study from a JSON file.
        
        Args:
            filepath: Path to the study file
            
        Returns:
            Loaded CFDParametricStudy instance
        """
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # Recreate base model
        base_model = CFDModel.from_dict(data["base_model"])
        
        # Create study instance
        study = cls(
            base_model=base_model,
            solver_type=CFDSolverType(data["solver_type"]),
            analysis_type=CFDAnalysisType(data["analysis_type"]),
            num_processors=data["num_processors"],
            max_parallel_cases=data["max_parallel_cases"]
        )
        
        # Update study directory
        study.study_dir = data["study_dir"]
        
        # Set cases
        study.cases = data["cases"]
        
        # Set results
        for case_index_str, results in data["results"].items():
            study.case_results[int(case_index_str)] = results
        
        return study

class CFDBatchRunner:
    """Simple batch runner for multiple CFD cases."""
    
    def __init__(self, output_dir: str, max_parallel: int = 1):
        """
        Initialize a batch runner.
        
        Args:
            output_dir: Directory for outputs
            max_parallel: Maximum number of parallel cases to run
        """
        self.output_dir = output_dir
        self.max_parallel = max_parallel
        self.cases = []
        self.results = {}
        
        os.makedirs(output_dir, exist_ok=True)
    
    def add_case(self, model: CFDModel, 
                solver_type: CFDSolverType = CFDSolverType.OPENFOAM,
                analysis_type: CFDAnalysisType = CFDAnalysisType.STEADY,
                num_processors: int = 1) -> int:
        """
        Add a case to the batch.
        
        Args:
            model: CFD model to run
            solver_type: Type of solver to use
            analysis_type: Type of analysis
            num_processors: Number of processors per case
            
        Returns:
            Index of the added case
        """
        case = {
            "model": model,
            "solver_type": solver_type,
            "analysis_type": analysis_type,
            "num_processors": num_processors,
            "status": "pending",
            "case_dir": None,
            "job_id": None
        }
        
        self.cases.append(case)
        return len(self.cases) - 1
    
    def _run_case(self, case_index: int) -> None:
        """
        Run a single case.
        
        Args:
            case_index: Index of the case to run
        """
        case = self.cases[case_index]
        model = case["model"]
        
        # Create a runner
        runner = CFDRunner(
            solver_type=case["solver_type"],
            analysis_type=case["analysis_type"],
            num_processors=case["num_processors"]
        )
        
        # Update status
        case["status"] = "setting_up"
        
        try:
            # Create case directory in output directory
            case_dir = runner.setup_case(model, 
                                     case_dir=os.path.join(self.output_dir, model.name))
            case["case_dir"] = case_dir
            
            # Update status
            case["status"] = "running"
            
            # Run the case with reasonable timeout
            results = runner.run_case(case_dir, background=False, timeout=3600)
            
            # Store results
            self.results[case_index] = results
            
            # Update status
            case["status"] = "completed"
            
        except Exception as e:
            logger.error(f"Error running case {case_index}: {e}")
            case["status"] = "failed"
            self.results[case_index] = {"error": str(e)}
    
    def run_all(self) -> None:
        """Run all cases."""
        if self.max_parallel > 1:
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_parallel) as executor:
                # Submit all pending cases
                futures = []
                for i in range(len(self.cases)):
                    if self.cases[i]["status"] == "pending":
                        futures.append(executor.submit(self._run_case, i))
                
                # Wait for all to complete
                concurrent.futures.wait(futures)
        else:
            # Run sequentially
            for i in range(len(self.cases)):
                if self.cases[i]["status"] == "pending":
                    self._run_case(i)
    
    def generate_report(self, filepath: Optional[str] = None) -> str:
        """
        Generate a report of all cases.
        
        Args:
            filepath: Path to save the report (default: output_dir/batch_report.html)
            
        Returns:
            Path to the generated report
        """
        filepath = filepath or os.path.join(self.output_dir, "batch_report.html")
        
        # Write HTML report
        with open(filepath, 'w') as f:
            f.write("""<!DOCTYPE html>
<html>
<head>
    <title>CFD Batch Run Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #333366; }
        h2 { color: #333366; margin-top: 20px; }
        table { border-collapse: collapse; width: 100%; }
        th, td { text-align: left; padding: 8px; border-bottom: 1px solid #ddd; }
        tr:nth-child(even) { background-color: #f2f2f2; }
        th { background-color: #333366; color: white; }
        .success { color: green; }
        .failure { color: red; }
    </style>
</head>
<body>
    <h1>CFD Batch Run Report</h1>
    
    <h2>Case Summary</h2>
    <table>
        <tr>
            <th>Case</th>
            <th>Status</th>
            <th>Directory</th>
            <th>Results</th>
        </tr>
""")
            
            for i, case in enumerate(self.cases):
                status_class = "success" if case["status"] == "completed" else "failure"
                
                # Determine results to show
                result_text = ""
                if i in self.results:
                    if "error" in self.results[i]:
                        result_text = f"Error: {self.results[i]['error']}"
                    elif "force_coefficients" in self.results[i]:
                        coeffs = self.results[i]["force_coefficients"]
                        if "Cd" in coeffs:
                            result_text += f"Cd: {coeffs['Cd']:.4f}, "
                        if "Cl" in coeffs:
                            result_text += f"Cl: {coeffs['Cl']:.4f}, "
                        result_text = result_text.rstrip(", ")
                
                f.write(f"""
        <tr>
            <td>{case['model'].name}</td>
            <td class="{status_class}">{case['status']}</td>
            <td>{case['case_dir'] if case['case_dir'] else '-'}</td>
            <td>{result_text}</td>
        </tr>""")
            
            f.write("""
    </table>
</body>
</html>
""")
        
        logger.info(f"Batch report generated at {filepath}")
        return filepath

def create_structured_parameter_study(
    base_model: CFDModel,
    parameter_ranges: Dict[str, Tuple[float, float, int]],
    name_template: str = "case_{param}_{value}",
    solver_type: CFDSolverType = CFDSolverType.OPENFOAM
) -> CFDParametricStudy:
    """
    Create a structured parameter study with evenly spaced values.
    
    Args:
        base_model: Base CFD model
        parameter_ranges: Dict mapping parameter names to (min, max, num_points) tuples
        name_template: Template for case names
        solver_type: Type of solver to use
        
    Returns:
        Configured parametric study
    """
    # Create parameter sweep dictionary
    parameter_sweeps = {}
    
    for param, (min_val, max_val, num_points) in parameter_ranges.items():
        if num_points > 1:
            parameter_sweeps[param] = np.linspace(min_val, max_val, num_points).tolist()
        else:
            parameter_sweeps[param] = [min_val]
    
    # Create parametric study
    study = CFDParametricStudy(
        base_model=base_model,
        solver_type=solver_type
    )
    
    # Add each parameter combination as a separate case
    for param, values in parameter_sweeps.items():
        for value in values:
            case_name = name_template.format(param=param, value=value)
            study.add_case(case_name, {param: value})
    
    return study
