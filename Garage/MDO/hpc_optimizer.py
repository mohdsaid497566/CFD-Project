"""
HPC integration for MDO optimization.

This module provides capabilities for distributing MDO tasks to HPC clusters,
including optimization, sensitivity analysis, and design of experiments.
"""

import os
import sys
import json
import time
import logging
import numpy as np
from typing import Dict, List, Tuple, Union, Optional, Any, Callable
from datetime import datetime
import tempfile
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("hpc_optimizer")

class HPCJobStatus:
    """Status codes for HPC jobs"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    UNKNOWN = "unknown"

class HPCOptimizer:
    """
    Class for running optimization tasks on HPC systems.
    """
    def __init__(self, hpc_connector=None, hpc_config: Optional[Dict] = None):
        """
        Initialize the HPC optimizer.
        
        Args:
            hpc_connector: HPC connector object (if None, will create one using hpc_config)
            hpc_config: HPC configuration dictionary (ignored if hpc_connector is provided)
        """
        self.hpc_connector = hpc_connector
        self.running_jobs = {}  # Dictionary to track running jobs
        
        if hpc_connector is None and hpc_config is not None:
            self._initialize_connector(hpc_config)
    
    def _initialize_connector(self, hpc_config):
        """
        Initialize HPC connector based on configuration.
        
        Args:
            hpc_config: HPC configuration dictionary
        """
        try:
            # Import the HPC module dynamically to avoid direct dependency
            sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
            from HPC.connector import HPCConnector
            
            self.hpc_connector = HPCConnector(
                hostname=hpc_config.get("hostname", "localhost"),
                username=hpc_config.get("username", ""),
                password=hpc_config.get("password", ""),
                use_key=hpc_config.get("use_key", False),
                key_path=hpc_config.get("key_path", ""),
                port=hpc_config.get("port", 22),
                scheduler=hpc_config.get("scheduler", "slurm")
            )
            logger.info(f"Initialized HPC connector to {hpc_config.get('hostname')}")
        except ImportError:
            logger.error("Failed to import HPC module. Make sure it's installed.")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize HPC connector: {str(e)}")
            raise
    
    def test_connection(self) -> bool:
        """
        Test the connection to the HPC system.
        
        Returns:
            True if connection is successful, False otherwise
        """
        if self.hpc_connector is None:
            logger.error("HPC connector not initialized")
            return False
        
        try:
            return self.hpc_connector.test_connection()
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False
    
    def submit_optimization_job(self, 
                              problem_file: str, 
                              algorithm: str,
                              options: Dict,
                              job_name: Optional[str] = None,
                              resources: Optional[Dict] = None,
                              callback_url: Optional[str] = None) -> Dict:
        """
        Submit an optimization job to the HPC system.
        
        Args:
            problem_file: Path to optimization problem file (pickle or JSON)
            algorithm: Optimization algorithm to use
            options: Dictionary of algorithm options
            job_name: Name for the job (if None, will generate one)
            resources: Dictionary of HPC resources to request
            callback_url: Optional URL for job status callbacks
            
        Returns:
            Dictionary with job information
        """
        if self.hpc_connector is None:
            raise RuntimeError("HPC connector not initialized")
        
        # Generate job name if not provided
        if job_name is None:
            job_name = f"mdo_opt_{algorithm}_{uuid.uuid4().hex[:8]}"
        
        # Default resources if not provided
        if resources is None:
            resources = {
                "nodes": 1,
                "tasks_per_node": 4,
                "memory_per_node": "8G",
                "walltime": "02:00:00",
                "queue": "compute"
            }
        
        # Create unique working directory for job
        remote_dir = f"/tmp/mdo_opt_{job_name}_{uuid.uuid4().hex[:8]}"
        
        # Create job script
        job_script = self._create_optimization_script(
            problem_file=problem_file,
            algorithm=algorithm,
            options=options,
            remote_dir=remote_dir,
            callback_url=callback_url
        )
        
        # Submit job
        try:
            # Create remote directory
            self.hpc_connector.run_command(f"mkdir -p {remote_dir}")
            
            # Upload problem file
            remote_problem_file = os.path.join(remote_dir, os.path.basename(problem_file))
            self.hpc_connector.upload_file(problem_file, remote_problem_file)
            
            # Create and upload job script
            script_file = os.path.join(remote_dir, "run_optimization.sh")
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
                f.write(job_script)
                local_script = f.name
            
            self.hpc_connector.upload_file(local_script, script_file)
            os.unlink(local_script)  # Remove local temporary file
            
            # Make script executable
            self.hpc_connector.run_command(f"chmod +x {script_file}")
            
            # Submit job
            job_id = self.hpc_connector.submit_job(
                script_file=script_file,
                job_name=job_name,
                nodes=resources.get("nodes", 1),
                tasks=resources.get("tasks_per_node", 4),
                memory=resources.get("memory_per_node", "8G"),
                walltime=resources.get("walltime", "02:00:00"),
                queue=resources.get("queue", "compute")
            )
            
            # Track job
            job_info = {
                "job_id": job_id,
                "job_name": job_name,
                "algorithm": algorithm,
                "status": HPCJobStatus.PENDING,
                "submit_time": datetime.now().isoformat(),
                "remote_dir": remote_dir,
                "problem_file": remote_problem_file,
                "result_file": os.path.join(remote_dir, "optimization_result.pkl")
            }
            
            self.running_jobs[job_id] = job_info
            
            logger.info(f"Submitted optimization job {job_name} with ID {job_id}")
            
            return job_info
            
        except Exception as e:
            logger.error(f"Failed to submit optimization job: {str(e)}")
            raise
    
    def _create_optimization_script(self,
                                  problem_file: str,
                                  algorithm: str,
                                  options: Dict,
                                  remote_dir: str,
                                  callback_url: Optional[str] = None) -> str:
        """
        Create a job script for running optimization on the HPC system.
        
        Args:
            problem_file: Path to optimization problem file
            algorithm: Optimization algorithm to use
            options: Dictionary of algorithm options
            remote_dir: Remote working directory
            callback_url: Optional URL for job status callbacks
            
        Returns:
            Job script as a string
        """
        # Serialized options
        options_json = json.dumps(options)
        
        # Base Python script
        python_script = f"""
import os
import sys
import pickle
import json
import logging
import traceback
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, 
                  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                  filename='{remote_dir}/optimization.log')
logger = logging.getLogger("mdo_optimization")

# Function to update status
def update_status(status, message=""):
    with open('{remote_dir}/status.json', 'w') as f:
        json.dump({{"status": status, "message": message, "timestamp": datetime.now().isoformat()}}, f)
    logger.info(f"Status updated: {{status}} - {{message}}")

# Report callback if provided
callback_url = {f'"{callback_url}"' if callback_url else 'None'}
if callback_url:
    try:
        import requests
        def report_callback(status, message=""):
            try:
                requests.post(callback_url, json={{"job_id": os.environ.get('SLURM_JOB_ID', 'unknown'), 
                                                "status": status, "message": message}}, timeout=5)
            except Exception as e:
                logger.error(f"Failed to report callback: {{str(e)}}")
        
        report_callback("started", "Optimization job started")
    except ImportError:
        logger.warning("requests module not available, cannot report callbacks")
        def report_callback(status, message=""):
            pass
else:
    def report_callback(status, message=""):
        pass

try:
    # Update status
    update_status("running", "Loading optimization problem")
    report_callback("running", "Loading optimization problem")
    
    # Add parent directory to path for importing modules
    parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if parent_dir not in sys.path:
        sys.path.append(parent_dir)
    
    # Import MDO modules
    from MDO.optimizer import Optimizer, OptimizationProblem
    
    # Options from job submission
    algorithm = "{algorithm}"
    options = json.loads('{options_json}')
    
    # Load problem
    problem_file = "{os.path.basename(problem_file)}"
    
    logger.info(f"Loading optimization problem from {{problem_file}}")
    update_status("running", "Loading optimization problem")
    report_callback("running", "Loading optimization problem")
    
    with open(problem_file, 'rb') as f:
        problem = pickle.load(f)
    
    if not isinstance(problem, OptimizationProblem):
        raise TypeError("Loaded object is not an OptimizationProblem")
    
    # Create optimizer
    logger.info(f"Creating optimizer with algorithm {{algorithm}}")
    update_status("running", f"Creating optimizer with algorithm {{algorithm}}")
    report_callback("running", f"Creating optimizer with algorithm {{algorithm}}")
    
    optimizer = Optimizer(algorithm=algorithm, options=options, 
                        output_dir=os.path.join('{remote_dir}', 'output'))
    
    # Run optimization
    logger.info("Starting optimization")
    update_status("running", "Optimization in progress")
    report_callback("running", "Optimization in progress")
    
    # Optimization progress callback
    def progress_callback(iteration, obj_value):
        if iteration % 10 == 0:
            update_status("running", f"Optimization iteration {{iteration}}, objective: {{obj_value:.6f}}")
            report_callback("running", f"Optimization iteration {{iteration}}, objective: {{obj_value:.6f}}")
    
    # Run optimization
    results = optimizer.optimize(problem, callback=progress_callback)
    
    # Save results
    logger.info("Optimization completed, saving results")
    update_status("completed", "Optimization completed successfully")
    report_callback("completed", "Optimization completed successfully")
    
    with open('{remote_dir}/optimization_result.pkl', 'wb') as f:
        pickle.dump(results, f)
    
    # Save summary as JSON for easier parsing
    summary = {{
        "algorithm": algorithm,
        "obj_value": float(results['obj_value']),
        "n_iterations": results['n_iterations'],
        "n_function_evals": results['n_function_evals'],
        "time": results['time'],
        "success": bool(results['success']),
        "x_dict": {{k: float(v) for k, v in results['x_dict'].items()}}
    }}
    
    with open('{remote_dir}/summary.json', 'w') as f:
        json.dump(summary, f, indent=4)
    
    logger.info("Results saved successfully")
    sys.exit(0)
    
except Exception as e:
    error_msg = f"Error during optimization: {{str(e)}}"
    logger.error(error_msg)
    logger.error(traceback.format_exc())
    update_status("failed", error_msg)
    report_callback("failed", error_msg)
    sys.exit(1)
"""
        
        # Create shell script that runs the Python script
        shell_script = f"""#!/bin/bash
#
# MDO Optimization Job
#

# Load any required modules (customize for your HPC environment)
module load python/3.8 || echo "Failed to load Python module, continuing with default"

# Create a virtual environment if needed
HAS_VENV=$(command -v python3 -m venv)
if [ ! -z "$HAS_VENV" ]; then
    python3 -m venv {remote_dir}/venv
    source {remote_dir}/venv/bin/activate
    pip install --upgrade pip
    pip install numpy scipy matplotlib
    # Try to install optional packages
    pip install requests || echo "Failed to install requests, callbacks will not work"
fi

# Log job info
echo "Job started at $(date)"
echo "Running on node $(hostname)"
echo "Working directory: {remote_dir}"

# Create Python script
cat > {remote_dir}/run_optimization.py << 'EOL'
{python_script}
EOL

# Run optimization
cd {remote_dir}
python run_optimization.py

# Check exit status
EXIT_STATUS=$?
if [ $EXIT_STATUS -eq 0 ]; then
    echo "Optimization completed successfully"
else
    echo "Optimization failed with exit status $EXIT_STATUS"
fi

echo "Job finished at $(date)"
exit $EXIT_STATUS
"""
        
        return shell_script
    
    def get_job_status(self, job_id: str) -> Dict:
        """
        Get the status of a running optimization job.
        
        Args:
            job_id: Job ID
            
        Returns:
            Dictionary with job status information
        """
        if self.hpc_connector is None:
            raise RuntimeError("HPC connector not initialized")
        
        if job_id not in self.running_jobs:
            raise ValueError(f"Job ID {job_id} not found in running jobs")
        
        job_info = self.running_jobs[job_id]
        
        try:
            # Check job status in scheduler
            scheduler_status = self.hpc_connector.get_job_status(job_id)
            
            # Update job status based on scheduler status
            if scheduler_status == "COMPLETED":
                # Check for successful completion
                remote_status_file = os.path.join(job_info["remote_dir"], "status.json")
                try:
                    status_content = self.hpc_connector.read_file(remote_status_file)
                    status_data = json.loads(status_content)
                    job_info["status"] = status_data["status"]
                    job_info["message"] = status_data.get("message", "")
                    job_info["update_time"] = status_data.get("timestamp", datetime.now().isoformat())
                except Exception:
                    # If we can't read the status file, use the scheduler status
                    job_info["status"] = HPCJobStatus.COMPLETED
            elif scheduler_status == "RUNNING":
                job_info["status"] = HPCJobStatus.RUNNING
            elif scheduler_status == "PENDING":
                job_info["status"] = HPCJobStatus.PENDING
            elif scheduler_status in ["FAILED", "TIMEOUT", "NODE_FAIL"]:
                job_info["status"] = HPCJobStatus.FAILED
            elif scheduler_status == "CANCELLED":
                job_info["status"] = HPCJobStatus.CANCELLED
            else:
                job_info["status"] = HPCJobStatus.UNKNOWN
            
            # Update job info
            self.running_jobs[job_id] = job_info
            
            return job_info
            
        except Exception as e:
            logger.error(f"Failed to get job status: {str(e)}")
            job_info["status"] = HPCJobStatus.UNKNOWN
            job_info["message"] = f"Failed to get status: {str(e)}"
            return job_info
    
    def get_all_jobs(self) -> List[Dict]:
        """
        Get information about all tracked jobs.
        
        Returns:
            List of job information dictionaries
        """
        return list(self.running_jobs.values())
    
    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a running optimization job.
        
        Args:
            job_id: Job ID
            
        Returns:
            True if cancellation was successful, False otherwise
        """
        if self.hpc_connector is None:
            raise RuntimeError("HPC connector not initialized")
        
        if job_id not in self.running_jobs:
            raise ValueError(f"Job ID {job_id} not found in running jobs")
        
        try:
            result = self.hpc_connector.cancel_job(job_id)
            if result:
                self.running_jobs[job_id]["status"] = HPCJobStatus.CANCELLED
            return result
        except Exception as e:
            logger.error(f"Failed to cancel job: {str(e)}")
            return False
    
    def get_job_results(self, job_id: str, local_dir: Optional[str] = None) -> Optional[Dict]:
        """
        Get the results of a completed optimization job.
        
        Args:
            job_id: Job ID
            local_dir: Local directory to save result files (if None, will use temp dir)
            
        Returns:
            Optimization results dictionary or None if not available
        """
        if self.hpc_connector is None:
            raise RuntimeError("HPC connector not initialized")
        
        if job_id not in self.running_jobs:
            raise ValueError(f"Job ID {job_id} not found in running jobs")
        
        job_info = self.running_jobs[job_id]
        
        if job_info["status"] != HPCJobStatus.COMPLETED:
            logger.warning(f"Job {job_id} is not completed (status: {job_info['status']})")
            return None
        
        try:
            # Create local directory if needed
            if local_dir is None:
                local_dir = tempfile.mkdtemp(prefix=f"mdo_job_{job_id}_")
            else:
                os.makedirs(local_dir, exist_ok=True)
            
            # Download result file
            remote_result_file = job_info["result_file"]
            local_result_file = os.path.join(local_dir, os.path.basename(remote_result_file))
            
            self.hpc_connector.download_file(remote_result_file, local_result_file)
            
            # Load results
            with open(local_result_file, 'rb') as f:
                import pickle
                results = pickle.load(f)
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to get job results: {str(e)}")
            return None
    
    def cleanup_job(self, job_id: str, delete_remote: bool = False) -> bool:
        """
        Clean up job resources.
        
        Args:
            job_id: Job ID
            delete_remote: Whether to delete remote files
            
        Returns:
            True if cleanup was successful, False otherwise
        """
        if job_id not in self.running_jobs:
            raise ValueError(f"Job ID {job_id} not found in running jobs")
        
        job_info = self.running_jobs[job_id]
        
        try:
            # Delete remote files if requested
            if delete_remote and self.hpc_connector is not None:
                try:
                    remote_dir = job_info["remote_dir"]
                    self.hpc_connector.run_command(f"rm -rf {remote_dir}")
                    logger.info(f"Deleted remote directory {remote_dir}")
                except Exception as e:
                    logger.warning(f"Failed to delete remote directory: {str(e)}")
            
            # Remove job from tracking
            del self.running_jobs[job_id]
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to cleanup job: {str(e)}")
            return False
    
    def submit_doe_job(self, 
                     problem_file: str,
                     doe_type: str,
                     n_samples: int,
                     job_name: Optional[str] = None,
                     resources: Optional[Dict] = None,
                     callback_url: Optional[str] = None) -> Dict:
        """
        Submit a Design of Experiments (DOE) job to the HPC system.
        
        Args:
            problem_file: Path to optimization problem file (pickle or JSON)
            doe_type: Type of DOE (e.g., 'latin_hypercube', 'full_factorial')
            n_samples: Number of samples to generate
            job_name: Name for the job (if None, will generate one)
            resources: Dictionary of HPC resources to request
            callback_url: Optional URL for job status callbacks
            
        Returns:
            Dictionary with job information
        """
        if self.hpc_connector is None:
            raise RuntimeError("HPC connector not initialized")
        
        # Generate job name if not provided
        if job_name is None:
            job_name = f"mdo_doe_{doe_type}_{uuid.uuid4().hex[:8]}"
        
        # Default resources if not provided
        if resources is None:
            resources = {
                "nodes": 1,
                "tasks_per_node": 8,  # DOE can be parallel
                "memory_per_node": "16G",
                "walltime": "04:00:00",
                "queue": "compute"
            }
        
        # Create unique working directory for job
        remote_dir = f"/tmp/mdo_doe_{job_name}_{uuid.uuid4().hex[:8]}"
        
        # Create job script
        job_script = self._create_doe_script(
            problem_file=problem_file,
            doe_type=doe_type,
            n_samples=n_samples,
            remote_dir=remote_dir,
            callback_url=callback_url
        )
        
        # Submit job
        try:
            # Create remote directory
            self.hpc_connector.run_command(f"mkdir -p {remote_dir}")
            
            # Upload problem file
            remote_problem_file = os.path.join(remote_dir, os.path.basename(problem_file))
            self.hpc_connector.upload_file(problem_file, remote_problem_file)
            
            # Create and upload job script
            script_file = os.path.join(remote_dir, "run_doe.sh")
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
                f.write(job_script)
                local_script = f.name
            
            self.hpc_connector.upload_file(local_script, script_file)
            os.unlink(local_script)  # Remove local temporary file
            
            # Make script executable
            self.hpc_connector.run_command(f"chmod +x {script_file}")
            
            # Submit job
            job_id = self.hpc_connector.submit_job(
                script_file=script_file,
                job_name=job_name,
                nodes=resources.get("nodes", 1),
                tasks=resources.get("tasks_per_node", 8),
                memory=resources.get("memory_per_node", "16G"),
                walltime=resources.get("walltime", "04:00:00"),
                queue=resources.get("queue", "compute")
            )
            
            # Track job
            job_info = {
                "job_id": job_id,
                "job_name": job_name,
                "type": "doe",
                "doe_type": doe_type,
                "n_samples": n_samples,
                "status": HPCJobStatus.PENDING,
                "submit_time": datetime.now().isoformat(),
                "remote_dir": remote_dir,
                "problem_file": remote_problem_file,
                "result_file": os.path.join(remote_dir, "doe_result.pkl")
            }
            
            self.running_jobs[job_id] = job_info
            
            logger.info(f"Submitted DOE job {job_name} with ID {job_id}")
            
            return job_info
            
        except Exception as e:
            logger.error(f"Failed to submit DOE job: {str(e)}")
            raise
    
    def _create_doe_script(self,
                         problem_file: str,
                         doe_type: str,
                         n_samples: int,
                         remote_dir: str,
                         callback_url: Optional[str] = None) -> str:
        """
        Create a job script for running DOE on the HPC system.
        
        Args:
            problem_file: Path to optimization problem file
            doe_type: Type of DOE
            n_samples: Number of samples
            remote_dir: Remote working directory
            callback_url: Optional URL for job status callbacks
            
        Returns:
            Job script as a string
        """
        # Base Python script
        python_script = f"""
import os
import sys
import pickle
import json
import logging
import traceback
import numpy as np
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, 
                  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                  filename='{remote_dir}/doe.log')
logger = logging.getLogger("mdo_doe")

# Function to update status
def update_status(status, message=""):
    with open('{remote_dir}/status.json', 'w') as f:
        json.dump({{"status": status, "message": message, "timestamp": datetime.now().isoformat()}}, f)
    logger.info(f"Status updated: {{status}} - {{message}}")

# Report callback if provided
callback_url = {f'"{callback_url}"' if callback_url else 'None'}
if callback_url:
    try:
        import requests
        def report_callback(status, message=""):
            try:
                requests.post(callback_url, json={{"job_id": os.environ.get('SLURM_JOB_ID', 'unknown'), 
                                                "status": status, "message": message}}, timeout=5)
            except Exception as e:
                logger.error(f"Failed to report callback: {{str(e)}}")
        
        report_callback("started", "DOE job started")
    except ImportError:
        logger.warning("requests module not available, cannot report callbacks")
        def report_callback(status, message=""):
            pass
else:
    def report_callback(status, message=""):
        pass

try:
    # Update status
    update_status("running", "Loading problem")
    report_callback("running", "Loading problem")
    
    # Add parent directory to path for importing modules
    parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if parent_dir not in sys.path:
        sys.path.append(parent_dir)
    
    # Import MDO modules
    from MDO.optimizer import OptimizationProblem
    from MDO.doe import DesignOfExperiments
    
    # Parameters
    doe_type = "{doe_type}"
    n_samples = {n_samples}
    
    # Load problem
    problem_file = "{os.path.basename(problem_file)}"
    
    logger.info(f"Loading problem from {{problem_file}}")
    update_status("running", "Loading problem")
    report_callback("running", "Loading problem")
    
    with open(problem_file, 'rb') as f:
        problem = pickle.load(f)
    
    if not isinstance(problem, OptimizationProblem):
        raise TypeError("Loaded object is not an OptimizationProblem")
    
    # Create DOE
    logger.info(f"Creating DOE with type {{doe_type}} and {{n_samples}} samples")
    update_status("running", f"Creating DOE with {{n_samples}} samples")
    report_callback("running", f"Creating DOE with {{n_samples}} samples")
    
    doe = DesignOfExperiments(problem, doe_type=doe_type)
    
    # Generate samples
    logger.info("Generating samples")
    update_status("running", "Generating samples")
    report_callback("running", "Generating samples")
    
    samples = doe.generate_samples(n_samples)
    
    # Evaluate samples
    logger.info(f"Evaluating {{len(samples)}} samples")
    update_status("running", f"Evaluating {{len(samples)}} samples")
    report_callback("running", f"Evaluating {{len(samples)}} samples")
    
    # Try to use parallel processing
    try:
        from joblib import Parallel, delayed
        import multiprocessing
        
        n_cores = int(os.environ.get('SLURM_CPUS_PER_TASK', multiprocessing.cpu_count()))
        logger.info(f"Using {{n_cores}} cores for parallel evaluation")
        
        # Evaluate in parallel
        results = Parallel(n_jobs=n_cores)(delayed(problem.evaluate)(x) for x in samples)
    except ImportError:
        logger.warning("joblib not available, using sequential evaluation")
        
        # Sequential evaluation
        results = []
        for i, x in enumerate(samples):
            if i % 10 == 0:
                logger.info(f"Evaluating sample {{i+1}}/{{len(samples)}}")
                update_status("running", f"Evaluating sample {{i+1}}/{{len(samples)}}")
                report_callback("running", f"Evaluating sample {{i+1}}/{{len(samples)}}")
            
            result = problem.evaluate(x)
            results.append(result)
    
    # Package results
    doe_results = {{
        "problem_name": problem.name,
        "doe_type": doe_type,
        "n_samples": n_samples,
        "samples": samples,
        "results": results,
        "variables": list(problem.design_variables.keys()),
        "objectives": list(problem.objectives.keys()),
        "constraints": list(problem.constraints.keys())
    }}
    
    # Save results
    logger.info("DOE completed, saving results")
    update_status("completed", "DOE completed successfully")
    report_callback("completed", "DOE completed successfully")
    
    with open('{remote_dir}/doe_result.pkl', 'wb') as f:
        pickle.dump(doe_results, f)
    
    # Save summary as JSON for easier parsing
    summary = {{
        "problem_name": problem.name,
        "doe_type": doe_type,
        "n_samples": n_samples,
        "variables": list(problem.design_variables.keys()),
        "objectives": list(problem.objectives.keys()),
        "constraints": list(problem.constraints.keys()),
        "completed": True,
        "timestamp": datetime.now().isoformat()
    }}
    
    with open('{remote_dir}/summary.json', 'w') as f:
        json.dump(summary, f, indent=4)
    
    logger.info("Results saved successfully")
    sys.exit(0)
    
except Exception as e:
    error_msg = f"Error during DOE: {{str(e)}}"
    logger.error(error_msg)
    logger.error(traceback.format_exc())
    update_status("failed", error_msg)
    report_callback("failed", error_msg)
    sys.exit(1)
"""
        
        # Create shell script that runs the Python script
        shell_script = f"""#!/bin/bash
#
# MDO Design of Experiments Job
#

# Load any required modules (customize for your HPC environment)
module load python/3.8 || echo "Failed to load Python module, continuing with default"

# Create a virtual environment if needed
HAS_VENV=$(command -v python3 -m venv)
if [ ! -z "$HAS_VENV" ]; then
    python3 -m venv {remote_dir}/venv
    source {remote_dir}/venv/bin/activate
    pip install --upgrade pip
    pip install numpy scipy matplotlib
    pip install joblib || echo "Failed to install joblib, will use sequential evaluation"
    pip install requests || echo "Failed to install requests, callbacks will not work"
fi

# Log job info
echo "Job started at $(date)"
echo "Running on node $(hostname)"
echo "Working directory: {remote_dir}"

# Create Python script
cat > {remote_dir}/run_doe.py << 'EOL'
{python_script}
EOL

# Run DOE
cd {remote_dir}
python run_doe.py

# Check exit status
EXIT_STATUS=$?
if [ $EXIT_STATUS -eq 0 ]; then
    echo "DOE completed successfully"
else
    echo "DOE failed with exit status $EXIT_STATUS"
fi

echo "Job finished at $(date)"
exit $EXIT_STATUS
"""
        
        return shell_script

# Example usage if this module is run directly
if __name__ == "__main__":
    print("HPC Optimizer Module for MDO")
    print("This module provides classes and functions for running MDO tasks on HPC systems.")
    print("Importing this module directly doesn't perform any actions.")