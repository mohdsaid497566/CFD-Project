#!/usr/bin/env python3
"""
HPC DoE Runner module for running Design of Experiments studies on HPC systems.

This module interfaces the DoE (Design of Experiments) module with the HPC connector
to enable running large parameter studies on remote HPC systems.
"""

import os
import json
import time
import logging
import numpy as np
from datetime import datetime
from pathlib import Path
import tempfile
from typing import Dict, List, Optional, Tuple, Union, Any

# Import DoE module
from .doe import DoEGenerator, DesignSpace

# Import HPC connector
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from HPC.hpc_connector import HPCConnector, HPCJobStatus, HPCJob

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("hpc_doe")

class HPCDoERunner:
    """
    Class for running DoE studies on HPC systems.
    """
    def __init__(self, hpc_config_path: Optional[str] = None):
        """
        Initialize the HPC DoE Runner.
        
        Args:
            hpc_config_path: Path to HPC configuration file. If None, use default.
        """
        self.hpc_config_path = hpc_config_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "Config", "hpc_profiles.json"
        )
        
        # Load HPC configuration
        self.hpc_config = self._load_hpc_config()
        
        # Initialize HPC connector
        self.hpc = HPCConnector(self.hpc_config)
        
        # Track submitted jobs
        self.jobs = {}
        
    def _load_hpc_config(self) -> Dict[str, Any]:
        """
        Load HPC configuration from file.
        
        Returns:
            Dictionary containing HPC configuration
        """
        if not os.path.exists(self.hpc_config_path):
            logger.warning(f"HPC config file not found: {self.hpc_config_path}")
            return {}
            
        try:
            with open(self.hpc_config_path, 'r') as f:
                config = json.load(f)
                
            # Ensure required fields are present
            config.setdefault("hpc_enabled", False)
            config.setdefault("hpc_host", "localhost")
            config.setdefault("hpc_username", "")
            config.setdefault("hpc_port", 22)
            config.setdefault("hpc_remote_dir", "/home/user/cfd_projects")
            config.setdefault("use_key_auth", False)
            config.setdefault("key_path", "")
            
            return config
            
        except Exception as e:
            logger.error(f"Error loading HPC config: {str(e)}")
            return {}
            
    def _save_hpc_config(self) -> bool:
        """
        Save HPC configuration to file.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.hpc_config_path), exist_ok=True)
            
            with open(self.hpc_config_path, 'w') as f:
                json.dump(self.hpc_config, f, indent=4)
                
            logger.info(f"Saved HPC config to {self.hpc_config_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving HPC config: {str(e)}")
            return False
            
    def connect(self, **kwargs) -> Tuple[bool, str]:
        """
        Connect to the HPC system.
        
        Args:
            **kwargs: Override connection parameters (hostname, username, etc.)
            
        Returns:
            Tuple of (success, message)
        """
        # Update config with any provided parameters
        for key, value in kwargs.items():
            if value is not None:
                self.hpc_config[key] = value
                
        # Try to connect
        success, message = self.hpc.connect(
            hostname=self.hpc_config.get("hpc_host"),
            username=self.hpc_config.get("hpc_username"),
            port=self.hpc_config.get("hpc_port"),
            use_key=self.hpc_config.get("use_key_auth"),
            key_path=self.hpc_config.get("key_path"),
            password=kwargs.get("password")  # Password is never stored in config
        )
        
        if success:
            logger.info(f"Connected to HPC system: {self.hpc_config.get('hpc_host')}")
            
            # Save config (without password)
            self._save_hpc_config()
        else:
            logger.error(f"Failed to connect to HPC system: {message}")
            
        return success, message
        
    def disconnect(self) -> None:
        """
        Disconnect from the HPC system.
        """
        self.hpc.disconnect()
        logger.info("Disconnected from HPC system")
        
    def test_connection(self, **kwargs) -> Tuple[bool, str]:
        """
        Test connection to the HPC system.
        
        Args:
            **kwargs: Override connection parameters
            
        Returns:
            Tuple of (success, message)
        """
        success, message = self.connect(**kwargs)
        
        if success:
            # Get system info as a test
            info = self.hpc.get_cluster_info()
            
            if not info or "error" in info:
                success = False
                message = f"Connected but failed to get system info: {info.get('error', 'Unknown error')}"
                
            # Disconnect
            self.disconnect()
            
        return success, message
        
    def setup_remote_environment(self) -> bool:
        """
        Set up the remote environment for running DoE studies.
        Creates necessary directories and uploads required files.
        
        Returns:
            True if successful, False otherwise
        """
        if not self.hpc.connected:
            logger.error("Not connected to HPC system")
            return False
            
        try:
            # Create the main project directory
            remote_dir = self.hpc_config.get("hpc_remote_dir")
            _, stdout, stderr = self.hpc.execute_command(f"mkdir -p {remote_dir}")
            
            if stderr and "error" in stderr.lower():
                logger.error(f"Error creating remote directory: {stderr}")
                return False
                
            # Create subdirectories
            for subdir in ["config", "doe", "results", "scripts"]:
                _, stdout, stderr = self.hpc.execute_command(f"mkdir -p {remote_dir}/{subdir}")
                
            # Upload a basic README
            readme_content = f"""# Intake CFD Project DoE Studies
Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
This directory contains Design of Experiments studies for the Intake CFD Project.

## Directory Structure
- config/: Configuration files
- doe/: Design of Experiments definition files
- results/: Simulation results
- scripts/: Job scripts
"""
            
            # Create a temporary README file
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as f:
                f.write(readme_content)
                readme_path = f.name
                
            # Upload the README
            self.hpc.upload_file(readme_path, f"{remote_dir}/README.md")
            
            # Clean up
            os.unlink(readme_path)
            
            logger.info(f"Set up remote environment at {remote_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting up remote environment: {str(e)}")
            return False
            
    def upload_doe_definition(self, doe_samples: np.ndarray, 
                            design_space: DesignSpace,
                            name: str = "doe_study") -> Tuple[bool, str]:
        """
        Upload a DoE definition to the remote system.
        
        Args:
            doe_samples: Array of design points
            design_space: Design space defining variables
            name: Name for the DoE study
            
        Returns:
            Tuple of (success, remote_path)
        """
        if not self.hpc.connected:
            logger.error("Not connected to HPC system")
            return False, ""
            
        try:
            # Convert samples to dictionary
            samples_dict = design_space.to_dict(doe_samples)
            
            # Create metadata
            metadata = {
                "name": name,
                "timestamp": datetime.now().isoformat(),
                "n_samples": doe_samples.shape[0],
                "dimension": doe_samples.shape[1],
                "variables": list(design_space.variables.keys())
            }
            
            # Create save data
            save_data = {
                "metadata": metadata,
                "samples": samples_dict
            }
            
            # Create a temporary file
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
                json.dump(save_data, f, indent=4)
                temp_path = f.name
                
            # Remote path
            remote_dir = self.hpc_config.get("hpc_remote_dir")
            remote_path = f"{remote_dir}/doe/{name}.json"
            
            # Upload the file
            success, message = self.hpc.upload_file(temp_path, remote_path)
            
            # Clean up
            os.unlink(temp_path)
            
            if success:
                logger.info(f"Uploaded DoE definition to {remote_path}")
                return True, remote_path
            else:
                logger.error(f"Failed to upload DoE definition: {message}")
                return False, ""
                
        except Exception as e:
            logger.error(f"Error uploading DoE definition: {str(e)}")
            return False, ""
            
    def generate_doe_job_script(self, doe_path: str, name: str, 
                            template_file: Optional[str] = None) -> str:
        """
        Generate a job script for running a DoE study.
        
        Args:
            doe_path: Path to the DoE definition file on the remote system
            name: Name of the DoE study
            template_file: Path to a template job script (optional)
            
        Returns:
            Job script content
        """
        # If template file is provided and exists, use it
        if template_file and os.path.exists(template_file):
            with open(template_file, 'r') as f:
                template = f.read()
                
            # Replace placeholders
            script = template.replace("{{DOE_PATH}}", doe_path)
            script = script.replace("{{NAME}}", name)
            script = script.replace("{{TIMESTAMP}}", datetime.now().strftime("%Y%m%d_%H%M%S"))
            
            return script
            
        # Otherwise, generate a basic script
        remote_dir = self.hpc_config.get("hpc_remote_dir")
        
        script = f"""#!/bin/bash
#SBATCH --job-name=doe_{name}
#SBATCH --output={remote_dir}/results/{name}_%j.out
#SBATCH --error={remote_dir}/results/{name}_%j.err
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=4
#SBATCH --time=24:00:00
#SBATCH --mem=16G

# Print job info
echo "Job started at $(date)"
echo "Running on $(hostname)"
echo "Working directory: $(pwd)"

# Set up environment (modify as needed)
module load python/3.8
module load openfoam/v2006

# Create a working directory for this job
WORKDIR={remote_dir}/results/job_$SLURM_JOB_ID
mkdir -p $WORKDIR
cd $WORKDIR

# Copy the DoE definition
cp {doe_path} ./doe_definition.json

# Process each DoE sample
echo "Processing DoE samples from {doe_path}"
python3 -c "
import json
import os
import subprocess
import time

# Load DoE definition
with open('doe_definition.json', 'r') as f:
    doe_data = json.load(f)

# Extract samples
samples = doe_data['samples']
n_samples = len(samples)

# Process each sample
for i, sample in enumerate(samples):
    print(f'Processing sample {{i+1}}/{{n_samples}}')
    
    # Create sample directory
    sample_dir = f'sample_{{i+1}}'
    os.makedirs(sample_dir, exist_ok=True)
    os.chdir(sample_dir)
    
    # Write sample parameters
    with open('parameters.json', 'w') as f:
        json.dump(sample, f, indent=2)
    
    # TODO: Run your simulation here
    # This is a placeholder - replace with actual simulation commands
    # Example: subprocess.run(['openfoam', 'simulation', '-parameters', 'parameters.json'])
    
    print(f'  Parameters: {{sample}}')
    time.sleep(1)  # Simulate some work
    
    # Return to working directory
    os.chdir('..')

print('DoE processing complete.')
"

# Collect and organize results
echo "Collecting results..."

# Create a summary file
echo "Summary of DoE results:" > results_summary.txt
echo "Date: $(date)" >> results_summary.txt
echo "Job ID: $SLURM_JOB_ID" >> results_summary.txt
echo "DoE study: {name}" >> results_summary.txt
echo "" >> results_summary.txt

# Add sample results (placeholder)
echo "Sample results would be summarized here" >> results_summary.txt

# Copy results to persistent location
mkdir -p {remote_dir}/results/{name}
cp -r * {remote_dir}/results/{name}/

echo "Job completed at $(date)"
"""

        return script
        
    def submit_doe_study(self, doe_samples: np.ndarray, 
                      design_space: DesignSpace,
                      name: str = None,
                      template_file: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """
        Submit a DoE study to the HPC system.
        
        Args:
            doe_samples: Array of design points
            design_space: Design space defining variables
            name: Name for the DoE study (optional)
            template_file: Path to a template job script (optional)
            
        Returns:
            Tuple of (success, job_id)
        """
        if not self.hpc.connected:
            logger.error("Not connected to HPC system")
            return False, None
            
        try:
            # Generate a name if not provided
            if name is None:
                name = f"doe_study_{int(time.time())}"
                
            # Upload DoE definition
            success, remote_doe_path = self.upload_doe_definition(doe_samples, design_space, name)
            
            if not success:
                return False, None
                
            # Generate job script
            job_script = self.generate_doe_job_script(remote_doe_path, name, template_file)
            
            # Remote path for job script
            remote_dir = self.hpc_config.get("hpc_remote_dir")
            remote_script_path = f"{remote_dir}/scripts/{name}_job.sh"
            
            # Create remote script
            with self.hpc.sftp.open(remote_script_path, 'w') as f:
                f.write(job_script)
                
            # Make script executable
            self.hpc.execute_command(f"chmod +x {remote_script_path}")
            
            # Submit job
            job = self.hpc.submit_job(job_script, job_name=name)
            
            if job is None:
                logger.error("Failed to submit DoE job")
                return False, None
                
            # Store job information
            self.jobs[job.id] = {
                "name": name,
                "submit_time": job.submit_time,
                "status": job.status,
                "remote_dir": f"{remote_dir}/results/{name}"
            }
            
            logger.info(f"Submitted DoE job: {job.id} ({name})")
            return True, job.id
            
        except Exception as e:
            logger.error(f"Error submitting DoE study: {str(e)}")
            return False, None
            
    def check_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Check the status of a submitted job.
        
        Args:
            job_id: ID of the job to check
            
        Returns:
            Dictionary with job status information or None if job not found
        """
        if not self.hpc.connected:
            logger.error("Not connected to HPC system")
            return None
            
        try:
            # Get job status from HPC
            job = self.hpc.get_job_status(job_id)
            
            if job is None:
                logger.warning(f"Job {job_id} not found")
                return None
                
            # Update stored job information
            if job_id in self.jobs:
                self.jobs[job_id]["status"] = job.status
                self.jobs[job_id]["duration"] = job.duration
                
            return {
                "id": job_id,
                "name": job.name,
                "status": job.status,
                "submit_time": job.submit_time,
                "duration": job.duration,
                "remote_dir": job.remote_dir
            }
            
        except Exception as e:
            logger.error(f"Error checking job status: {str(e)}")
            return None
            
    def get_doe_results(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the results of a completed DoE study.
        
        Args:
            job_id: ID of the completed job
            
        Returns:
            Dictionary with results information or None if results not available
        """
        if not self.hpc.connected:
            logger.error("Not connected to HPC system")
            return None
            
        # Check job status first
        job_info = self.check_job_status(job_id)
        
        if job_info is None:
            return None
            
        # Only proceed if job is completed
        if job_info["status"] != HPCJobStatus.COMPLETED:
            logger.warning(f"Job {job_id} is not completed (status: {job_info['status']})")
            return {"status": job_info["status"], "message": "Job is not completed"}
            
        try:
            # Get remote directory for results
            remote_dir = None
            
            if job_id in self.jobs:
                remote_dir = self.jobs[job_id]["remote_dir"]
            else:
                remote_dir = job_info["remote_dir"]
                
            if not remote_dir:
                logger.error(f"Remote directory not found for job {job_id}")
                return None
                
            # Check if results directory exists
            _, stdout, stderr = self.hpc.execute_command(f"ls -la {remote_dir}")
            
            if stderr and "No such file or directory" in stderr:
                logger.error(f"Results directory not found: {remote_dir}")
                return None
                
            # Get list of files
            _, stdout, stderr = self.hpc.execute_command(f"find {remote_dir} -type f -name '*.json' | sort")
            json_files = stdout.strip().split('\n') if stdout.strip() else []
            
            # Get summary file if it exists
            summary_content = None
            _, stdout, stderr = self.hpc.execute_command(f"cat {remote_dir}/results_summary.txt 2>/dev/null || true")
            if stdout.strip():
                summary_content = stdout.strip()
                
            # Create temporary directory for downloaded results
            temp_dir = tempfile.mkdtemp()
            
            # Download some key files
            downloaded_files = []
            for json_file in json_files[:5]:  # Limit to first 5 files
                if json_file:
                    local_path = os.path.join(temp_dir, os.path.basename(json_file))
                    success, _ = self.hpc.download_file(json_file, local_path)
                    if success:
                        downloaded_files.append(local_path)
                        
            # Prepare results info
            results_info = {
                "job_id": job_id,
                "job_name": job_info["name"],
                "status": job_info["status"],
                "remote_dir": remote_dir,
                "file_count": len(json_files),
                "summary": summary_content,
                "downloaded_files": downloaded_files,
                "temp_dir": temp_dir
            }
            
            return results_info
            
        except Exception as e:
            logger.error(f"Error getting DoE results: {str(e)}")
            return None

# Example usage
if __name__ == "__main__":
    from doe import LatinHypercubeDoE
    
    # Create a design space
    design_space = DesignSpace("Intake CFD Design Space")
    design_space.add_variable("inlet_velocity", 10.0, 50.0, "m/s", "Inlet velocity")
    design_space.add_variable("outlet_pressure", 0.8, 1.2, "bar", "Outlet pressure")
    design_space.add_variable("angle_of_attack", -10.0, 10.0, "degrees", "Angle of attack")
    
    # Create DoE generator
    lhs_doe = LatinHypercubeDoE(design_space, seed=42)
    
    # Generate samples
    n_samples = 20
    X_lhs = lhs_doe.generate(n_samples, criterion='maximin', iterations=100)
    
    # Create HPC DoE runner
    hpc_runner = HPCDoERunner()
    
    # Connect to HPC system (would require valid credentials)
    success, message = hpc_runner.connect(
        hostname="hpc.example.com",
        username="user",
        password="password",
        use_key_auth=False
    )
    
    # If connected, submit DoE study
    if success:
        success, job_id = hpc_runner.submit_doe_study(X_lhs, design_space, name="intake_cfd_study")
        
        if success:
            print(f"DoE study submitted with job ID: {job_id}")
            
            # Check job status
            job_info = hpc_runner.check_job_status(job_id)
            print(f"Job status: {job_info['status']}")
            
            # Disconnect
            hpc_runner.disconnect()
        else:
            print("Failed to submit DoE study")
    else:
        print(f"Failed to connect to HPC system: {message}")