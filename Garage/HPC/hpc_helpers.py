import os
import json
import subprocess
import tempfile
import time
from pathlib import Path

def generate_hpc_script(fem_file_path, result_dir, job_name, num_cores=8, memory="16GB", wall_time="2:00:00"):
    """
    Generates an HPC job submission script for running NX Nastran simulations.
    
    Args:
        fem_file_path (str): Path to the FEM file
        result_dir (str): Directory where results should be stored
        job_name (str): Name for the HPC job
        num_cores (int): Number of cores to request
        memory (str): Memory to request per node
        wall_time (str): Maximum wall time for the job
        
    Returns:
        str: Path to the generated job script
    """
    # Create a temporary script file
    script_file = tempfile.NamedTemporaryFile(delete=False, suffix='.sh')
    script_path = script_file.name
    
    # Get absolute paths
    abs_fem_path = os.path.abspath(fem_file_path)
    abs_result_dir = os.path.abspath(result_dir)
    
    # Create script content
    script_content = f"""#!/bin/bash
#SBATCH --job-name={job_name}
#SBATCH --output={abs_result_dir}/hpc_%j.log
#SBATCH --nodes=1
#SBATCH --ntasks-per-node={num_cores}
#SBATCH --mem={memory}
#SBATCH --time={wall_time}

module load nx/nastran
cd {os.path.dirname(abs_fem_path)}
nastran {os.path.basename(abs_fem_path)} scr={abs_result_dir} old=no
"""
    
    # Write script to file
    with open(script_path, 'w') as f:
        f.write(script_content)
        
    return script_path

def submit_hpc_job(script_path):
    """
    Submits a job to the HPC cluster using sbatch.
    
    Args:
        script_path (str): Path to the job script file
        
    Returns:
        str: Job ID if successful, None otherwise
    """
    try:
        result = subprocess.run(['sbatch', script_path], 
                              capture_output=True, 
                              text=True)
        
        if result.returncode == 0:
            # Extract job ID from output - typically looks like "Submitted batch job 12345"
            output = result.stdout.strip()
            job_id = output.split()[-1]
            return job_id
        else:
            print(f"Error submitting HPC job: {result.stderr}")
            return None
    except Exception as e:
        print(f"Exception when submitting HPC job: {str(e)}")
        return None

def check_hpc_job_status(job_id):
    """
    Checks the status of an HPC job.
    
    Args:
        job_id (str): The job ID to check
        
    Returns:
        str: Status of the job (PENDING, RUNNING, COMPLETED, FAILED, UNKNOWN)
    """
    try:
        result = subprocess.run(['squeue', '-j', job_id, '-h', '-o', '%T'], 
                              capture_output=True, 
                              text=True)
        
        if result.returncode == 0:
            status = result.stdout.strip()
            if not status:
                # Check if the job is completed by using sacct
                check_completed = subprocess.run(
                    ['sacct', '-j', job_id, '-n', '-o', 'State'],
                    capture_output=True, 
                    text=True
                )
                completed_status = check_completed.stdout.strip()
                
                if "COMPLETED" in completed_status:
                    return "COMPLETED"
                elif "FAILED" in completed_status or "CANCELLED" in completed_status:
                    return "FAILED"
                else:
                    return "UNKNOWN"
            return status
        else:
            return "UNKNOWN"
    except Exception as e:
        print(f"Exception when checking job status: {str(e)}")
        return "UNKNOWN"

def monitor_hpc_job(job_id, polling_interval=60):
    """
    Monitors an HPC job until it completes or fails.
    
    Args:
        job_id (str): The job ID to monitor
        polling_interval (int): Time in seconds between status checks
        
    Returns:
        bool: True if the job completed successfully, False otherwise
    """
    while True:
        status = check_hpc_job_status(job_id)
        
        if status == "COMPLETED":
            return True
        elif status in ["FAILED", "CANCELLED", "TIMEOUT"]:
            return False
        elif status in ["PENDING", "RUNNING", "CONFIGURING"]:
            time.sleep(polling_interval)
        else:
            # For unknown status, wait and check again
            time.sleep(polling_interval)

def get_hpc_job_results(job_id, result_dir):
    """
    Retrieves and processes the results of an HPC job.
    
    Args:
        job_id (str): The completed job ID
        result_dir (str): Directory where results are stored
        
    Returns:
        dict: Dictionary containing the results information
    """
    results_info = {
        "job_id": job_id,
        "status": "unknown",
        "output_files": [],
        "errors": []
    }
    
    # Check job status first
    final_status = check_hpc_job_status(job_id)
    results_info["status"] = final_status
    
    # Look for result files
    result_path = Path(result_dir)
    if result_path.exists():
        # Look for NX Nastran output files
        for ext in ['.op2', '.out', '.log', '.f06', '.xdb']:
            files = list(result_path.glob(f'*{ext}'))
            results_info["output_files"].extend([str(f) for f in files])
    
    # Check log file for errors
    log_file = result_path / f"hpc_{job_id}.log"
    if log_file.exists():
        with open(log_file, 'r') as f:
            log_content = f.read()
            if "ERROR" in log_content or "FAIL" in log_content:
                results_info["errors"].append("Errors found in log file")
    
    return results_info

def create_hpc_config(config_file_path):
    """
    Creates a default HPC configuration file if it doesn't exist.
    
    Args:
        config_file_path (str): Path where the config file should be saved
        
    Returns:
        dict: The configuration dictionary
    """
    default_config = {
        "default_cores": 8,
        "default_memory": "16GB",
        "default_wall_time": "2:00:00",
        "result_directory": os.path.expanduser("~/nx_hpc_results"),
        "polling_interval": 60
    }
    
    config_path = Path(config_file_path)
    
    # Create parent directories if they don't exist
    if not config_path.parent.exists():
        config_path.parent.mkdir(parents=True)
    
    # Create or load config file
    if not config_path.exists():
        with open(config_file_path, 'w') as f:
            json.dump(default_config, f, indent=2)
        return default_config
    else:
        with open(config_file_path, 'r') as f:
            return json.load(f)

def read_hpc_config(config_file_path):
    """
    Reads the HPC configuration file.
    
    Args:
        config_file_path (str): Path to the config file
        
    Returns:
        dict: The configuration dictionary or default values if file doesn't exist
    """
    try:
        with open(config_file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return create_hpc_config(config_file_path)
    except json.JSONDecodeError:
        print(f"Error parsing HPC config file. Using defaults.")
        return create_hpc_config(config_file_path + ".backup")
