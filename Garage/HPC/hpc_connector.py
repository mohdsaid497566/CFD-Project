#!/usr/bin/env python3
"""
HPC Connector module for the Intake CFD Project.

This module provides functionality for connecting to HPC systems,
submitting jobs, monitoring job status, and transferring files.
"""

import os
import sys
import time
import json
import tempfile
import logging
import subprocess
from pathlib import Path
import threading
from typing import Dict, List, Optional, Any, Tuple, Union

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("hpc_connector")

# Try to import paramiko for SSH connections
try:
    import paramiko
    PARAMIKO_AVAILABLE = True
except ImportError:
    PARAMIKO_AVAILABLE = False
    logger.warning("Paramiko is not available. SSH connections will not work.")

# HPC job status constants
class HPCJobStatus:
    """Job status constants"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"

class HPCJob:
    """HPC job object"""
    
    def __init__(self, job_id=None, name=None, status=None, script=None, 
                config=None, scheduler=None, parameters=None, submit_time=None):
        """
        Initialize HPC job.
        
        Args:
            job_id: Job ID assigned by scheduler
            name: Job name
            status: Job status (use HPCJobStatus constants)
            script: Job script content
            config: Job configuration dictionary
            scheduler: Scheduler type
            parameters: Job parameters dictionary
            submit_time: Job submission time
        """
        self.id = job_id
        self.name = name or "unnamed_job"
        self.status = status or HPCJobStatus.UNKNOWN
        self.script = script
        self.config = config or {}
        self.scheduler = scheduler or "slurm"
        self.parameters = parameters or {}
        self.submit_time = submit_time or time.time()
        self.output = ""
        self.error = ""
        self.exit_code = None
        self.update_time = self.submit_time
        self.start_time = None
        self.end_time = None
        self.duration = 0
        self.working_dir = None
        self.results = {}
    
    def update_status(self, status):
        """Update job status and related timestamps"""
        old_status = self.status
        self.status = status
        self.update_time = time.time()
        
        if old_status != HPCJobStatus.RUNNING and status == HPCJobStatus.RUNNING:
            self.start_time = self.update_time
        
        if status in [HPCJobStatus.COMPLETED, HPCJobStatus.FAILED, 
                     HPCJobStatus.CANCELLED, HPCJobStatus.TIMEOUT]:
            self.end_time = self.update_time
            if self.start_time:
                self.duration = self.end_time - self.start_time
    
    def to_dict(self):
        """Convert job to dictionary for serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status,
            "script": self.script,
            "config": self.config,
            "scheduler": self.scheduler,
            "parameters": self.parameters,
            "submit_time": self.submit_time,
            "update_time": self.update_time,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "working_dir": self.working_dir,
            "exit_code": self.exit_code
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create job from dictionary"""
        job = cls()
        for key, value in data.items():
            if hasattr(job, key):
                setattr(job, key, value)
        return job


class HPCConnector:
    """
    Connector for HPC systems.
    
    This class provides functionality for connecting to HPC systems,
    submitting jobs, monitoring job status, and transferring files.
    """
    
    def __init__(self, config=None):
        """
        Initialize HPC connector.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.ssh_client = None
        self.sftp_client = None
        self.connected = False
        self.hostname = self.config.get("hostname", "localhost")
        self.username = self.config.get("username", "")
        self.port = self.config.get("port", 22)
        self.scheduler = self.config.get("scheduler", "slurm")
        self.remote_dir = self.config.get("remote_dir", "")
        self.jobs = []
        self.job_monitor_thread = None
        self.stop_monitoring = False
        
        # Validate configuration
        if not self.hostname or not self.username:
            logger.warning("Invalid HPC configuration: hostname or username missing")
        
        # Load previous jobs if available
        self.load_jobs()
    
    def connect(self):
        """
        Connect to HPC system.
        
        Returns:
            tuple: (success, message)
        """
        if not PARAMIKO_AVAILABLE:
            return False, "SSH library (paramiko) is not available"
        
        if self.connected:
            return True, "Already connected"
        
        try:
            # Create SSH client
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Connect using either password or key
            if self.config.get("use_key", False):
                key_path = self.config.get("key_path", "")
                if not key_path:
                    return False, "Key authentication selected but no key path provided"
                
                self.ssh_client.connect(
                    self.hostname,
                    port=self.port,
                    username=self.username,
                    key_filename=key_path,
                    timeout=10
                )
            else:
                password = self.config.get("password", "")
                if not password:
                    return False, "Password authentication selected but no password provided"
                
                self.ssh_client.connect(
                    self.hostname,
                    port=self.port,
                    username=self.username,
                    password=password,
                    timeout=10
                )
            
            # Create SFTP client
            self.sftp_client = self.ssh_client.open_sftp()
            
            # Test connection by getting remote system info
            _, stdout, stderr = self.ssh_client.exec_command("uname -a")
            system_info = stdout.read().decode().strip()
            if system_info:
                logger.info(f"Connected to {self.hostname}: {system_info}")
                self.connected = True
                return True, f"Connected to {self.hostname}"
            else:
                logger.error(f"Failed to get system info: {stderr.read().decode().strip()}")
                return False, "Connected but failed to get system information"
                
        except Exception as e:
            logger.error(f"Error connecting to {self.hostname}: {str(e)}")
            self.disconnect()
            return False, f"Connection failed: {str(e)}"
    
    def disconnect(self):
        """
        Disconnect from HPC system.
        
        Returns:
            bool: True if disconnected successfully
        """
        try:
            if self.sftp_client:
                self.sftp_client.close()
                self.sftp_client = None
            
            if self.ssh_client:
                self.ssh_client.close()
                self.ssh_client = None
            
            self.connected = False
            logger.info(f"Disconnected from {self.hostname}")
            return True
            
        except Exception as e:
            logger.error(f"Error disconnecting from {self.hostname}: {str(e)}")
            return False
    
    def execute_command(self, command):
        """
        Execute command on HPC system.
        
        Args:
            command: Command string to execute
            
        Returns:
            tuple: (exit_code, stdout, stderr)
        """
        if not self.connected or not self.ssh_client:
            logger.error("Not connected to HPC system")
            return -1, "", "Not connected to HPC system"
        
        try:
            logger.debug(f"Executing command: {command}")
            stdin, stdout, stderr = self.ssh_client.exec_command(command)
            exit_code = stdout.channel.recv_exit_status()
            out = stdout.read().decode()
            err = stderr.read().decode()
            
            logger.debug(f"Command exited with {exit_code}")
            return exit_code, out, err
            
        except Exception as e:
            logger.error(f"Error executing command '{command}': {str(e)}")
            return -1, "", str(e)
    
    def get_system_info(self):
        """
        Get HPC system information.
        
        Returns:
            dict: System information
        """
        if not self.connected:
            return {"error": "Not connected to HPC system"}
        
        info = {
            "hostname": self.hostname,
            "scheduler": self.scheduler
        }
        
        # Get system information
        _, stdout, _ = self.execute_command("uname -a")
        info["system"] = stdout.strip()
        
        # Get CPU information
        _, stdout, _ = self.execute_command("cat /proc/cpuinfo | grep 'model name' | head -1")
        if stdout:
            info["cpu_model"] = stdout.split(":", 1)[1].strip() if ":" in stdout else stdout.strip()
        
        # Get memory information
        _, stdout, _ = self.execute_command("free -h | grep Mem:")
        if stdout:
            parts = stdout.split()
            if len(parts) >= 2:
                info["memory_total"] = parts[1]
        
        # Get scheduler information
        if self.scheduler == "slurm":
            # Get SLURM version
            _, stdout, _ = self.execute_command("sinfo --version")
            info["scheduler_version"] = stdout.strip()
            
            # Get partition information
            _, stdout, _ = self.execute_command("sinfo --format=\"%P %C %t\"")
            partitions = []
            for i, line in enumerate(stdout.splitlines()):
                if i == 0:  # Skip header
                    continue
                parts = line.split()
                if len(parts) >= 3:
                    partitions.append({
                        "name": parts[0],
                        "cores": parts[1],
                        "state": parts[2]
                    })
            info["partitions"] = partitions
            
        elif self.scheduler == "pbs":
            # Get PBS version
            _, stdout, _ = self.execute_command("qstat --version")
            info["scheduler_version"] = stdout.strip()
            
            # Get queue information
            _, stdout, _ = self.execute_command("qstat -Q")
            queues = []
            for i, line in enumerate(stdout.splitlines()):
                if i == 0:  # Skip header
                    continue
                parts = line.split()
                if len(parts) >= 3:
                    queues.append({
                        "name": parts[0],
                        "running": parts[1],
                        "queued": parts[2]
                    })
            info["queues"] = queues
        
        # Check available software modules
        _, stdout, _ = self.execute_command("module avail 2>&1 | grep -i 'openfoam\\|paraview\\|python'")
        modules = []
        for line in stdout.splitlines():
            if "openfoam" in line.lower() or "paraview" in line.lower() or "python" in line.lower():
                module = line.strip()
                if module and not module.startswith("-"):
                    modules.append(module)
        info["available_modules"] = modules
        
        return info
    
    def upload_file(self, local_path, remote_path):
        """
        Upload file to HPC system.
        
        Args:
            local_path: Local file path
            remote_path: Remote file path
            
        Returns:
            bool: True if uploaded successfully
        """
        if not self.connected or not self.sftp_client:
            logger.error("Not connected to HPC system")
            return False
        
        try:
            # Ensure remote directory exists
            remote_dir = os.path.dirname(remote_path)
            if remote_dir:
                try:
                    self.sftp_client.stat(remote_dir)
                except IOError:
                    # Directory doesn't exist, create it
                    self.execute_command(f"mkdir -p {remote_dir}")
            
            # Upload file
            self.sftp_client.put(local_path, remote_path)
            logger.info(f"Uploaded {local_path} to {remote_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error uploading {local_path} to {remote_path}: {str(e)}")
            return False
    
    def download_file(self, remote_path, local_path):
        """
        Download file from HPC system.
        
        Args:
            remote_path: Remote file path
            local_path: Local file path
            
        Returns:
            bool: True if downloaded successfully
        """
        if not self.connected or not self.sftp_client:
            logger.error("Not connected to HPC system")
            return False
        
        try:
            # Ensure local directory exists
            local_dir = os.path.dirname(local_path)
            if local_dir:
                os.makedirs(local_dir, exist_ok=True)
            
            # Download file
            self.sftp_client.get(remote_path, local_path)
            logger.info(f"Downloaded {remote_path} to {local_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error downloading {remote_path} to {local_path}: {str(e)}")
            return False
    
    def upload_directory(self, local_dir, remote_dir):
        """
        Upload directory to HPC system.
        
        Args:
            local_dir: Local directory path
            remote_dir: Remote directory path
            
        Returns:
            tuple: (success, message)
        """
        if not self.connected:
            return False, "Not connected to HPC system"
        
        try:
            # Create remote directory if it doesn't exist
            self.execute_command(f"mkdir -p {remote_dir}")
            
            # Get list of files to upload
            local_files = []
            for root, _, files in os.walk(local_dir):
                for filename in files:
                    local_path = os.path.join(root, filename)
                    rel_path = os.path.relpath(local_path, local_dir)
                    remote_path = os.path.join(remote_dir, rel_path)
                    local_files.append((local_path, remote_path))
            
            # Upload files
            uploaded = 0
            for local_path, remote_path in local_files:
                remote_subdir = os.path.dirname(remote_path)
                self.execute_command(f"mkdir -p {remote_subdir}")
                if self.upload_file(local_path, remote_path):
                    uploaded += 1
            
            if uploaded == len(local_files):
                logger.info(f"Uploaded {uploaded} files to {remote_dir}")
                return True, f"Uploaded {uploaded} files"
            else:
                logger.warning(f"Only uploaded {uploaded} of {len(local_files)} files to {remote_dir}")
                return False, f"Only uploaded {uploaded} of {len(local_files)} files"
                
        except Exception as e:
            logger.error(f"Error uploading directory {local_dir} to {remote_dir}: {str(e)}")
            return False, f"Error uploading directory: {str(e)}"
    
    def download_directory(self, remote_dir, local_dir, pattern="*"):
        """
        Download directory from HPC system.
        
        Args:
            remote_dir: Remote directory path
            local_dir: Local directory path
            pattern: File pattern to download
            
        Returns:
            tuple: (success, message)
        """
        if not self.connected:
            return False, "Not connected to HPC system"
        
        try:
            # Create local directory if it doesn't exist
            os.makedirs(local_dir, exist_ok=True)
            
            # List files in remote directory
            _, stdout, _ = self.execute_command(f"find {remote_dir} -type f -name '{pattern}' | sort")
            remote_files = stdout.strip().split("\n")
            
            # Download files
            downloaded = 0
            for remote_path in remote_files:
                if not remote_path:
                    continue
                    
                rel_path = os.path.relpath(remote_path, remote_dir)
                local_path = os.path.join(local_dir, rel_path)
                
                # Create local subdirectory if needed
                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                
                if self.download_file(remote_path, local_path):
                    downloaded += 1
            
            if downloaded > 0:
                logger.info(f"Downloaded {downloaded} files from {remote_dir}")
                return True, f"Downloaded {downloaded} files"
            else:
                logger.warning(f"No files downloaded from {remote_dir}")
                return False, "No files downloaded"
                
        except Exception as e:
            logger.error(f"Error downloading directory {remote_dir} to {local_dir}: {str(e)}")
            return False, f"Error downloading directory: {str(e)}"
    
    def submit_job(self, script, job_name=None, working_dir=None, parameters=None):
        """
        Submit job to HPC system.
        
        Args:
            script: Job script content
            job_name: Job name
            working_dir: Working directory on HPC system
            parameters: Job parameters dictionary
            
        Returns:
            HPCJob: Job object or None if submission failed
        """
        if not self.connected:
            logger.error("Not connected to HPC system")
            return None
        
        try:
            # Create temporary script file
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.sh') as f:
                f.write(script)
                temp_script_path = f.name
            
            # Use default working directory if not specified
            if not working_dir:
                working_dir = self.remote_dir or f"/home/{self.username}"
            
            # Create remote script path
            remote_script_name = f"job_{int(time.time())}.sh"
            remote_script_path = f"{working_dir}/{remote_script_name}"
            
            # Upload script
            if not self.upload_file(temp_script_path, remote_script_path):
                logger.error("Failed to upload job script")
                os.unlink(temp_script_path)
                return None
            
            # Delete local temporary file
            os.unlink(temp_script_path)
            
            # Make script executable
            self.execute_command(f"chmod +x {remote_script_path}")
            
            # Submit job
            if self.scheduler == "slurm":
                _, stdout, stderr = self.execute_command(f"cd {working_dir} && sbatch {remote_script_path}")
                if "Submitted batch job" in stdout:
                    job_id = stdout.strip().split()[-1]
                    logger.info(f"Submitted SLURM job {job_id}")
                else:
                    logger.error(f"SLURM job submission failed: {stderr}")
                    return None
                    
            elif self.scheduler == "pbs":
                _, stdout, stderr = self.execute_command(f"cd {working_dir} && qsub {remote_script_path}")
                if stderr:
                    logger.error(f"PBS job submission failed: {stderr}")
                    return None
                job_id = stdout.strip()
                logger.info(f"Submitted PBS job {job_id}")
                
            else:
                logger.error(f"Unsupported scheduler: {self.scheduler}")
                return None
            
            # Create job object
            job = HPCJob(
                job_id=job_id,
                name=job_name or f"job_{job_id}",
                status=HPCJobStatus.PENDING,
                script=script,
                scheduler=self.scheduler,
                parameters=parameters or {},
                submit_time=time.time()
            )
            job.working_dir = working_dir
            
            # Add to jobs list
            self.jobs.append(job)
            self.save_jobs()
            
            return job
            
        except Exception as e:
            logger.error(f"Error submitting job: {str(e)}")
            return None
    
    def submit_job_from_template(self, template_name, parameters=None, job_name=None, 
                                working_dir=None):
        """
        Submit job from a template.
        
        Args:
            template_name: Template name
            parameters: Dictionary of parameter values to use in the template
            job_name: Job name (optional)
            working_dir: Working directory on HPC system
            
        Returns:
            HPCJob: Job object or None if submission failed
        """
        try:
            # Import template manager
            from hpc_job_templates import JobTemplateManager
            template_manager = JobTemplateManager()
            
            # Generate script from template
            success, result = template_manager.generate_script(template_name, parameters)
            if not success:
                logger.error(f"Failed to generate script from template: {result}")
                return None
            
            script = result
            
            # Submit job
            template = template_manager.get_template(template_name)
            job = self.submit_job(
                script=script,
                job_name=job_name or template["name"],
                working_dir=working_dir,
                parameters=parameters
            )
            
            if job:
                job.parameters["template_name"] = template_name
                self.save_jobs()
                
            return job
            
        except Exception as e:
            logger.error(f"Error submitting job from template: {str(e)}")
            return None
    
    def cancel_job(self, job_id):
        """
        Cancel job on HPC system.
        
        Args:
            job_id: Job ID
            
        Returns:
            bool: True if cancelled successfully
        """
        if not self.connected:
            logger.error("Not connected to HPC system")
            return False
        
        try:
            # Check if SSH client is still valid
            if not self.ssh_client or self.ssh_client._transport is None or not self.ssh_client._transport.is_active():
                logger.error("SSH connection is closed or invalid")
                self.connected = False
                return False
                
            if self.scheduler == "slurm":
                _, stdout, stderr = self.execute_command(f"scancel {job_id}")
                if stderr and 'error' in stderr.lower():
                    logger.error(f"Error cancelling SLURM job {job_id}: {stderr}")
                    return False
                    
            elif self.scheduler == "pbs":
                _, stdout, stderr = self.execute_command(f"qdel {job_id}")
                if stderr and 'error' in stderr.lower() and 'unknown job' not in stderr.lower():
                    logger.error(f"Error cancelling PBS job {job_id}: {stderr}")
                    return False
                    
            else:
                logger.error(f"Unsupported scheduler: {self.scheduler}")
                return False
            
            # Update job status
            job_found = False
            for job in self.jobs:
                if job.id == job_id:
                    job.update_status(HPCJobStatus.CANCELLED)
                    job.end_time = time.time()
                    if job.start_time:
                        job.duration = job.end_time - job.start_time
                    job_found = True
                    break
            
            # Save jobs if we updated one
            if job_found:
                self.save_jobs()
            
            logger.info(f"Cancelled job {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling job {job_id}: {str(e)}")
            return False
    
    def get_job_status(self, job_id):
        """
        Get job status from HPC system.
        
        Args:
            job_id: Job ID
            
        Returns:
            str: Job status (use HPCJobStatus constants)
        """
        if not self.connected:
            logger.error("Not connected to HPC system")
            return HPCJobStatus.UNKNOWN
        
        try:
            if self.scheduler == "slurm":
                _, stdout, stderr = self.execute_command(f"squeue -j {job_id} -h -o '%T'")
                if stderr and "not found" in stderr.lower():
                    # Job not in queue, check if it completed
                    _, stdout, _ = self.execute_command(f"sacct -j {job_id} -n -X --format=State")
                    if stdout:
                        state = stdout.strip().split()[0].lower()
                        if "completed" in state:
                            return HPCJobStatus.COMPLETED
                        elif "failed" in state or "timeout" in state or "cancelled" in state:
                            return HPCJobStatus.FAILED
                        elif "running" in state:
                            return HPCJobStatus.RUNNING
                        else:
                            return HPCJobStatus.UNKNOWN
                    else:
                        # Job not found in accounting either
                        return HPCJobStatus.UNKNOWN
                elif stdout:
                    state = stdout.strip().lower()
                    if "pending" in state:
                        return HPCJobStatus.PENDING
                    elif "running" in state:
                        return HPCJobStatus.RUNNING
                    else:
                        return HPCJobStatus.UNKNOWN
                else:
                    return HPCJobStatus.UNKNOWN
                    
            elif self.scheduler == "pbs":
                _, stdout, stderr = self.execute_command(f"qstat -f {job_id} | grep job_state")
                if stderr:
                    return HPCJobStatus.UNKNOWN
                if not stdout:
                    # Job not in queue, might be completed
                    return HPCJobStatus.COMPLETED
                
                state = stdout.split("=")[1].strip().lower()
                if state == "q":
                    return HPCJobStatus.PENDING
                elif state == "r":
                    return HPCJobStatus.RUNNING
                elif state == "c":
                    return HPCJobStatus.COMPLETED
                elif state in ["e", "f"]:
                    return HPCJobStatus.FAILED
                else:
                    return HPCJobStatus.UNKNOWN
                    
            else:
                logger.error(f"Unsupported scheduler: {self.scheduler}")
                return HPCJobStatus.UNKNOWN
                
        except Exception as e:
            logger.error(f"Error getting status for job {job_id}: {str(e)}")
            return HPCJobStatus.UNKNOWN
    
    def get_job_output(self, job_id):
        """
        Get job output from HPC system.
        
        Args:
            job_id: Job ID
            
        Returns:
            tuple: (stdout, stderr)
        """
        if not self.connected:
            logger.error("Not connected to HPC system")
            return ("", "Not connected to HPC system")
        
        job = None
        for j in self.jobs:
            if j.id == job_id:
                job = j
                break
        
        if not job or not job.working_dir:
            logger.error(f"Job {job_id} not found or working directory unknown")
            return ("", f"Job {job_id} not found or working directory unknown")
        
        try:
            # Get output files based on scheduler
            if self.scheduler == "slurm":
                output_file = f"slurm-{job_id}.out"
                error_file = f"slurm-{job_id}.err"
                
                # Check if job has specified output/error files in script
                if job.script:
                    import re
                    out_match = re.search(r'#SBATCH\s+--output=(\S+)', job.script)
                    err_match = re.search(r'#SBATCH\s+--error=(\S+)', job.script)
                    
                    if out_match:
                        output_file = out_match.group(1).replace("%j", job_id)
                    
                    if err_match:
                        error_file = err_match.group(1).replace("%j", job_id)
                
                # Get output
                _, stdout, _ = self.execute_command(f"cat {job.working_dir}/{output_file} 2>/dev/null || echo ''")
                output = stdout
                
                # Get error
                _, stderr, _ = self.execute_command(f"cat {job.working_dir}/{error_file} 2>/dev/null || echo ''")
                error = stderr
                
            elif self.scheduler == "pbs":
                # PBS typically combines stdout and stderr into one file
                output_file = f"{job.name}.o{job_id}"
                error_file = f"{job.name}.e{job_id}"
                
                # Get output
                _, stdout, _ = self.execute_command(f"cat {job.working_dir}/{output_file} 2>/dev/null || echo ''")
                output = stdout
                
                # Get error if separate
                _, stderr, _ = self.execute_command(f"cat {job.working_dir}/{error_file} 2>/dev/null || echo ''")
                error = stderr
                
            else:
                logger.error(f"Unsupported scheduler: {self.scheduler}")
                return ("", f"Unsupported scheduler: {self.scheduler}")
            
            # Update job output
            job.output = output
            job.error = error
            
            return (output, error)
            
        except Exception as e:
            logger.error(f"Error getting output for job {job_id}: {str(e)}")
            return ("", f"Error getting output: {str(e)}")
    
    def update_job_statuses(self):
        """
        Update status of all jobs.
        
        Returns:
            int: Number of updated jobs
        """
        if not self.connected:
            logger.warning("Not connected to HPC system, cannot update job statuses")
            return 0
        
        updated = 0
        for job in self.jobs:
            # Skip completed, failed or cancelled jobs
            if job.status in [HPCJobStatus.COMPLETED, HPCJobStatus.FAILED, HPCJobStatus.CANCELLED]:
                continue
            
            # Get current status
            status = self.get_job_status(job.id)
            
            # Update job if status changed
            if status != job.status:
                job.update_status(status)
                updated += 1
                
                # If job completed or failed, get output
                if status in [HPCJobStatus.COMPLETED, HPCJobStatus.FAILED]:
                    self.get_job_output(job.id)
        
        if updated > 0:
            self.save_jobs()
            
        return updated
    
    def start_job_monitoring(self, interval=60):
        """
        Start background thread for job monitoring.
        
        Args:
            interval: Update interval in seconds
            
        Returns:
            bool: True if monitoring thread started
        """
        if self.job_monitor_thread and self.job_monitor_thread.is_alive():
            logger.warning("Job monitoring already active")
            return False
        
        self.stop_monitoring = False
        self.job_monitor_thread = threading.Thread(
            target=self._job_monitoring_worker,
            args=(interval,)
        )
        self.job_monitor_thread.daemon = True
        self.job_monitor_thread.start()
        
        logger.info(f"Started job monitoring thread (interval: {interval}s)")
        return True
    
    def stop_job_monitoring(self):
        """
        Stop job monitoring thread.
        
        Returns:
            bool: True if monitoring thread stopped
        """
        if not self.job_monitor_thread or not self.job_monitor_thread.is_alive():
            logger.warning("No active job monitoring thread")
            return False
        
        self.stop_monitoring = True
        self.job_monitor_thread.join(timeout=5.0)
        if self.job_monitor_thread.is_alive():
            logger.warning("Failed to stop job monitoring thread")
            return False
        
        logger.info("Stopped job monitoring thread")
        return True
    
    def _job_monitoring_worker(self, interval):
        """Worker thread for job monitoring"""
        logger.info("Job monitoring thread started")
        while not self.stop_monitoring:
            try:
                if self.connected:
                    updated = self.update_job_statuses()
                    if updated > 0:
                        logger.info(f"Updated status of {updated} jobs")
                
                # Sleep for interval
                for _ in range(min(60, interval)):
                    if self.stop_monitoring:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Error in job monitoring thread: {str(e)}")
                # Sleep briefly to avoid tight loop on error
                time.sleep(5)
        
        logger.info("Job monitoring thread stopped")
    
    def save_jobs(self, filename=None):
        """
        Save jobs to file.
        
        Args:
            filename: File path to save jobs
            
        Returns:
            bool: True if saved successfully
        """
        if filename is None:
            # Use default location in user home directory
            filename = os.path.expanduser("~/.hpc_jobs.json")
        
        try:
            # Convert jobs to dictionaries
            jobs_data = [job.to_dict() for job in self.jobs]
            
            # Save to file
            with open(filename, 'w') as f:
                json.dump(jobs_data, f, indent=2)
            
            logger.debug(f"Saved {len(self.jobs)} jobs to {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving jobs to {filename}: {str(e)}")
            return False
    
    def load_jobs(self, filename=None):
        """
        Load jobs from file.
        
        Args:
            filename: File path to load jobs from
            
        Returns:
            bool: True if loaded successfully
        """
        if filename is None:
            # Use default location in user home directory
            filename = os.path.expanduser("~/.hpc_jobs.json")
        
        if not os.path.exists(filename):
            logger.debug(f"Jobs file {filename} not found")
            return False
        
        try:
            # Load from file
            with open(filename, 'r') as f:
                jobs_data = json.load(f)
            
            # Convert dictionaries to job objects
            self.jobs = [HPCJob.from_dict(data) for data in jobs_data]
            
            logger.debug(f"Loaded {len(self.jobs)} jobs from {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading jobs from {filename}: {str(e)}")
            return False


def test_connection(config):
    """
    Test connection to HPC system.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        tuple: (success, message)
    """
    connector = HPCConnector(config)
    success, message = connector.connect()
    
    if success:
        # Get system info
        info = connector.get_system_info()
        system_info = info.get("system", "Unknown system")
        
        # Get job scheduler info
        if connector.scheduler == "slurm":
            scheduler_info = info.get("scheduler_version", "Unknown SLURM version")
        elif connector.scheduler == "pbs":
            scheduler_info = info.get("scheduler_version", "Unknown PBS version")
        else:
            scheduler_info = f"Unknown scheduler: {connector.scheduler}"
        
        # Get available partitions/queues
        if "partitions" in info:
            partitions = [p["name"] for p in info["partitions"]]
            partition_info = f"Available partitions: {', '.join(partitions)}"
        elif "queues" in info:
            queues = [q["name"] for q in info["queues"]]
            partition_info = f"Available queues: {', '.join(queues)}"
        else:
            partition_info = "No partition/queue information"
        
        # Disconnect
        connector.disconnect()
        
        return True, f"Connected to {config['hostname']}\n{system_info}\n{scheduler_info}\n{partition_info}"
    else:
        return False, message


# Example usage
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="HPC Connector")
    parser.add_argument("--host", required=True, help="HPC hostname")
    parser.add_argument("--user", required=True, help="Username")
    parser.add_argument("--password", help="Password (if not using key)")
    parser.add_argument("--key", help="SSH key file path")
    parser.add_argument("--scheduler", default="slurm", choices=["slurm", "pbs"], help="Job scheduler")
    
    args = parser.parse_args()
    
    # Create configuration
    config = {
        "hostname": args.host,
        "username": args.user,
        "scheduler": args.scheduler,
        "use_key": bool(args.key),
    }
    
    if args.key:
        config["key_path"] = args.key
    else:
        config["password"] = args.password or ""
    
    # Test connection
    success, message = test_connection(config)
    print(f"Connection {'successful' if success else 'failed'}: {message}")
    
    if success:
        # Connect
        connector = HPCConnector(config)
        success, _ = connector.connect()
        
        if success:
            # Get system info
            info = connector.get_system_info()
            print("\nSystem Information:")
            for key, value in info.items():
                if isinstance(value, list):
                    print(f"{key}:")
                    for item in value:
                        print(f"  - {item}")
                else:
                    print(f"{key}: {value}")
            
            # Disconnect
            connector.disconnect()