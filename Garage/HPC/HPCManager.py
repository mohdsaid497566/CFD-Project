import os
import json
import time
import pandas as pd
import paramiko
from tkinter import messagebox

class HPCManager:
    """Class to manage HPC connections and job operations"""
    
    def __init__(self, logger=None, update_status_callback=None):
        """Initialize the HPC Manager
        
        Args:
            logger: Function to log messages
            update_status_callback: Function to update UI status
        """
        self.logger = logger or print
        self.update_status = update_status_callback
        self.profiles_path = None
        self.profiles = {}
        self.load_profiles()
    
    def load_profiles(self, config_dir=None):
        """Load HPC profiles from configuration file"""
        try:
            if config_dir is None:
                config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Config")
            
            self.profiles_path = os.path.join(config_dir, "hpc_profiles.json")
            
            if not os.path.exists(self.profiles_path):
                self.logger("No HPC profiles found, using defaults")
                self.profiles = {}
                return False
                
            with open(self.profiles_path, 'r') as f:
                self.profiles = json.load(f)
                
            self.logger(f"Loaded {len(self.profiles)} HPC profiles")
            return True
        except Exception as e:
            self.logger(f"Error loading HPC profiles: {e}")
            return False
    
    def get_profile_names(self):
        """Get list of available profile names"""
        return list(self.profiles.keys())
    
    def submit_job(self, script_content, profile_name, callback=None):
        """Submit a job to the HPC cluster
        
        Args:
            script_content: Content of the job script
            profile_name: Name of the HPC profile to use
            callback: Function to call with submission result
            
        Returns:
            Boolean indicating success/failure
        """
        try:
            if profile_name not in self.profiles:
                self.logger(f"HPC profile '{profile_name}' not found")
                if callback:
                    callback(False, f"Profile '{profile_name}' not found")
                return False
                
            config = self.profiles[profile_name]
            
            # Create SSH client
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Connect based on authentication method
            try:
                if config.get("use_key", False):
                    key_path = config.get("key_path", "")
                    if not key_path:
                        self.logger("No SSH key specified in profile")
                        if callback:
                            callback(False, "No SSH key specified in profile")
                        return False
                        
                    key = paramiko.RSAKey.from_private_key_file(key_path)
                    client.connect(
                        hostname=config.get("hostname", ""),
                        port=int(config.get("port", 22)),
                        username=config.get("username", ""),
                        pkey=key,
                        timeout=15
                    )
                else:
                    password = config.get("password", "")
                    if not password:
                        self.logger("No password provided in profile")
                        if callback:
                            callback(False, "No password provided in profile")
                        return False
                    
                    client.connect(
                        hostname=config.get("hostname", ""),
                        port=int(config.get("port", 22)),
                        username=config.get("username", ""),
                        password=password,
                        timeout=15
                    )
            except Exception as e:
                self.logger(f"Error connecting to HPC: {e}")
                if callback:
                    callback(False, f"Connection error: {str(e)}")
                return False
            
            # Successfully connected, now submit job
            result = self._submit_script(client, config, script_content)
            
            if callback:
                callback(result[0], result[1])
                
            return result[0]
                
        except Exception as e:
            self.logger(f"Error submitting job: {e}")
            if callback:
                callback(False, f"Unexpected error: {str(e)}")
            return False
            
    def _submit_script(self, client, config, script_content):
        """Internal method to submit a script to the connected HPC system"""
        try:
            sftp = client.open_sftp()
            
            # Get remote directory
            remote_dir = config.get("remote_dir", "")
            if not remote_dir:
                # Try to get home directory
                stdin, stdout, stderr = client.exec_command("echo $HOME")
                remote_dir = stdout.read().decode().strip()
            
            # Make sure remote directory exists
            try:
                sftp.stat(remote_dir)
            except FileNotFoundError:
                self.logger(f"Remote directory {remote_dir} does not exist. Creating it...")
                client.exec_command(f"mkdir -p {remote_dir}")
            
            # Change to remote directory
            sftp.chdir(remote_dir)
            
            # Create job script file remotely
            script_filename = f"job_script_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.sh"
            remote_script_path = f"{remote_dir}/{script_filename}"
            
            with sftp.file(script_filename, 'w') as f:
                f.write(script_content)
            
            # Make script executable
            client.exec_command(f"chmod +x {remote_script_path}")
            
            # Determine job submission command based on available scheduler
            stdin, stdout, stderr = client.exec_command("command -v sbatch qsub bsub")
            scheduler_cmds = stdout.read().decode().strip().split('\n')
            
            submission_cmd = ""
            if scheduler_cmds and '/sbatch' in scheduler_cmds[0]:
                submission_cmd = f"cd {remote_dir} && sbatch {script_filename}"
                scheduler = "SLURM"
            elif scheduler_cmds and '/qsub' in scheduler_cmds[0]:
                submission_cmd = f"cd {remote_dir} && qsub {script_filename}"
                scheduler = "PBS"
            elif scheduler_cmds and '/bsub' in scheduler_cmds[0]:
                submission_cmd = f"cd {remote_dir} && bsub < {script_filename}"
                scheduler = "LSF"
            else:
                client.close()
                return (False, "Could not identify job scheduler (SLURM/PBS/LSF)")
            
            # Submit job
            self.logger(f"Submitting job with command: {submission_cmd}")
            stdin, stdout, stderr = client.exec_command(submission_cmd)
            response = stdout.read().decode().strip()
            error = stderr.read().decode().strip()
            
            # Close connection
            client.close()
            
            if error and ('error' in error.lower() or 'not found' in error.lower()):
                self.logger(f"Job submission error: {error}")
                return (False, f"Error submitting job: {error}")
            else:
                self.logger(f"Job submitted successfully: {response}")
                return (True, response)
                
        except Exception as e:
            self.logger(f"Error in submission process: {e}")
            return (False, f"Submission error: {str(e)}")
            
    def get_job_list(self, profile_name, callback=None):
        """Get list of running jobs from HPC system"""
        # Implementation for fetching job list would go here
        # Placeholder for future implementation
        self.logger("get_job_list method is a placeholder for future implementation")
        if callback:
            callback(False, "Method not implemented", [])
        return []
    
    def cancel_job(self, profile_name, job_id, callback=None):
        """Cancel a job on the HPC system"""
        # Implementation for canceling jobs would go here
        # Placeholder for future implementation
        self.logger("cancel_job method is a placeholder for future implementation")
        if callback:
            callback(False, "Method not implemented")
        return False