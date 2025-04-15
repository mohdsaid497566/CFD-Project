#!/usr/bin/env python3
"""
HPC Connector module for connecting to and managing jobs on remote HPC systems
"""

import os
import time
import datetime
import getpass
import socket
import re
from pathlib import Path
import traceback

# Try importing paramiko for SSH connectivity
try:
    import paramiko
    PARAMIKO_AVAILABLE = True
except ImportError:
    PARAMIKO_AVAILABLE = False
    print("Warning: paramiko module not found. HPC functionality will be limited.")

class HPCJobStatus:
    """Constants for job statuses"""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    UNKNOWN = "UNKNOWN"

class HPCJob:
    """Represents a job on the HPC system"""
    def __init__(self, job_id, name=None, status=HPCJobStatus.UNKNOWN, submit_time=None, duration="0:00", remote_dir=None):
        self.id = str(job_id)
        self.name = name if name else f"job_{job_id}"
        self.status = status
        self.submit_time = submit_time if submit_time else datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.duration = duration
        self.remote_dir = remote_dir

    def __repr__(self):
        return f"HPCJob(id={self.id}, name={self.name}, status={self.status})"

class HPCConnector:
    """
    Connector class for HPC systems
    Handles SSH connections, file transfers, and job management
    """
    def __init__(self, config=None):
        self.config = config or {}
        self.client = None
        self.sftp = None
        self.connected = False
        self.scheduler = config.get("scheduler", "slurm") if config else "slurm"
        self.home_dir = None

    def connect(self, **kwargs):
        """
        Connect to the HPC system using SSH
        Returns: (success, message)
        """
        if not PARAMIKO_AVAILABLE:
            return False, "Paramiko SSH module not available"
            
        if self.connected and self.client:
            return True, "Already connected"

        # Get configuration
        config = self.config.copy()
        config.update(kwargs)
        
        hostname = config.get("hostname")
        username = config.get("username")
        port = int(config.get("port", 22))
        use_key = config.get("use_key", False)
        key_path = config.get("key_path") if use_key else None
        password = config.get("password") if not use_key else None

        # Validate required parameters
        if not hostname:
            return False, "Hostname is required"
        if not username:
            return False, "Username is required"

        try:
            # Initialize SSH client
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Connect with appropriate authentication
            if use_key:
                if not key_path or not os.path.exists(key_path):
                    return False, f"Key file not found: {key_path}"
                
                key = paramiko.RSAKey.from_private_key_file(key_path) if not password else \
                      paramiko.RSAKey.from_private_key_file(key_path, password=password)
                
                self.client.connect(
                    hostname=hostname,
                    username=username,
                    port=port,
                    pkey=key,
                    look_for_keys=False,
                    allow_agent=False,
                    timeout=10
                )
            else:
                if not password:
                    return False, "Password is required for password authentication"
                
                self.client.connect(
                    hostname=hostname,
                    username=username,
                    port=port,
                    password=password,
                    look_for_keys=False,
                    allow_agent=False,
                    timeout=10
                )
            
            # Initialize SFTP session
            self.sftp = self.client.open_sftp()
            self.connected = True
            
            # Get home directory
            _, stdout, _ = self.client.exec_command("echo $HOME")
            self.home_dir = stdout.read().decode('utf-8').strip()
            
            return True, "Connected successfully"
        
        except paramiko.AuthenticationException:
            self.client = None
            return False, "Authentication failed"
        except paramiko.SSHException as e:
            self.client = None
            return False, f"SSH error: {str(e)}"
        except socket.error as e:
            self.client = None
            return False, f"Connection error: {str(e)}"
        except Exception as e:
            self.client = None
            traceback.print_exc()
            return False, f"Error: {str(e)}"

    def disconnect(self):
        """Close the SSH connection"""
        if self.sftp:
            try:
                self.sftp.close()
            except Exception:
                pass
            self.sftp = None
        
        if self.client:
            try:
                self.client.close()
            except Exception:
                pass
            self.client = None
        
        self.connected = False

    def execute_command(self, command, timeout=30):
        """Execute a command on the remote system"""
        if not self.connected or not self.client:
            return False, "Not connected", ""
            
        try:
            stdin, stdout, stderr = self.client.exec_command(command, timeout=timeout)
            exit_code = stdout.channel.recv_exit_status()
            stdout_str = stdout.read().decode('utf-8')
            stderr_str = stderr.read().decode('utf-8')
            
            return exit_code == 0, stdout_str, stderr_str
        except Exception as e:
            traceback.print_exc()
            return False, "", str(e)

    def upload_file(self, local_path, remote_path=None):
        """Upload a file to the remote system"""
        if not self.connected or not self.sftp:
            return False, "Not connected"
            
        try:
            if not remote_path:
                # Use same filename in home directory
                filename = os.path.basename(local_path)
                remote_path = f"{self.home_dir}/{filename}"
                
            self.sftp.put(local_path, remote_path)
            return True, f"File uploaded to {remote_path}"
        except Exception as e:
            traceback.print_exc()
            return False, f"Upload failed: {str(e)}"

    def download_file(self, remote_path, local_path=None):
        """Download a file from the remote system"""
        if not self.connected or not self.sftp:
            return False, "Not connected"
            
        try:
            if not local_path:
                # Use same filename in current directory
                filename = os.path.basename(remote_path)
                local_path = os.path.join(os.getcwd(), filename)
                
            self.sftp.get(remote_path, local_path)
            return True, f"File downloaded to {local_path}"
        except Exception as e:
            traceback.print_exc()
            return False, f"Download failed: {str(e)}"

    def get_cluster_info(self):
        """Get information about the HPC cluster"""
        if not self.connected or not self.client:
            return {"error": "Not connected"}
            
        info = {}
        
        try:
            # Get hostname
            _, stdout, _ = self.client.exec_command("hostname")
            info["hostname"] = stdout.read().decode('utf-8').strip()
            
            # Get OS info
            _, stdout, _ = self.client.exec_command("cat /etc/os-release | grep PRETTY_NAME")
            os_line = stdout.read().decode('utf-8').strip()
            if os_line:
                os_match = re.search(r'PRETTY_NAME="(.*)"', os_line)
                if os_match:
                    info["os"] = os_match.group(1)
                else:
                    info["os"] = os_line
            
            # Get memory info
            _, stdout, _ = self.client.exec_command("free -h | grep Mem")
            mem_line = stdout.read().decode('utf-8').strip()
            if mem_line:
                mem_parts = mem_line.split()
                if len(mem_parts) >= 2:
                    info["memory"] = mem_parts[1]
            
            # Get CPU info
            _, stdout, _ = self.client.exec_command("nproc")
            cpu_count = stdout.read().decode('utf-8').strip()
            if cpu_count:
                info["cpu_count"] = cpu_count
                
            # Get scheduler version
            if self.scheduler == "slurm":
                _, stdout, _ = self.client.exec_command("sinfo --version")
                info["scheduler_version"] = stdout.read().decode('utf-8').strip()
            elif self.scheduler == "pbs":
                _, stdout, _ = self.client.exec_command("qstat --version")
                info["scheduler_version"] = stdout.read().decode('utf-8').strip()
            
            return info
        except Exception as e:
            traceback.print_exc()
            return {"error": str(e)}

    def get_partitions(self):
        """Get available partitions/queues on the cluster"""
        if not self.connected or not self.client:
            return []
            
        try:
            if self.scheduler == "slurm":
                _, stdout, _ = self.client.exec_command("sinfo -h -o %P")
                partitions = stdout.read().decode('utf-8').strip().split('\n')
                return [p for p in partitions if p]
            elif self.scheduler == "pbs":
                _, stdout, _ = self.client.exec_command("qstat -Q")
                lines = stdout.read().decode('utf-8').strip().split('\n')[2:]  # Skip header lines
                return [line.split()[0] for line in lines if line]
            else:
                return ["default"]
        except Exception as e:
            traceback.print_exc()
            return []

    def create_job_script(self, parameters):
        """
        Create a job submission script based on parameters
        
        Parameters:
            parameters: dict with job parameters (name, nodes, cores_per_node, walltime, queue)
        """
        name = parameters.get("name", "job")
        nodes = parameters.get("nodes", 1)
        cores = parameters.get("cores_per_node", 4)
        walltime = parameters.get("walltime", "01:00:00")
        queue = parameters.get("queue", "")
        
        script_lines = []
        
        # Create appropriate script for the scheduler
        if self.scheduler == "slurm":
            script_lines.extend([
                "#!/bin/bash",
                f"#SBATCH --job-name={name}",
                f"#SBATCH --nodes={nodes}",
                f"#SBATCH --ntasks-per-node={cores}",
                f"#SBATCH --time={walltime}",
            ])
            
            if queue:
                script_lines.append(f"#SBATCH --partition={queue}")
                
            script_lines.extend([
                "#SBATCH --output=%j.out",
                "#SBATCH --error=%j.err",
                "",
                "# Print job info",
                "echo \"Job started at $(date)\"",
                "echo \"Running on $(hostname)\"",
                "echo \"Working directory: $(pwd)\"",
                "",
                "# Load modules",
                "# module load your-module",
                "",
                "# Run commands",
                "echo \"Hello from HPC job\"",
                "",
                "# End of job",
                "echo \"Job finished at $(date)\""
            ])
        elif self.scheduler == "pbs":
            script_lines.extend([
                "#!/bin/bash",
                f"#PBS -N {name}",
                f"#PBS -l nodes={nodes}:ppn={cores}",
                f"#PBS -l walltime={walltime}",
            ])
            
            if queue:
                script_lines.append(f"#PBS -q {queue}")
                
            script_lines.extend([
                "#PBS -o ${PBS_JOBID}.out",
                "#PBS -e ${PBS_JOBID}.err",
                "",
                "# Print job info",
                "echo \"Job started at $(date)\"",
                "echo \"Running on $(hostname)\"",
                "cd $PBS_O_WORKDIR",
                "echo \"Working directory: $(pwd)\"",
                "",
                "# Load modules",
                "# module load your-module",
                "",
                "# Run commands",
                "echo \"Hello from HPC job\"",
                "",
                "# End of job",
                "echo \"Job finished at $(date)\""
            ])
        else:
            # Generic script
            script_lines.extend([
                "#!/bin/bash",
                f"# Job: {name}",
                "",
                "# Print job info",
                "echo \"Job started at $(date)\"",
                "echo \"Running on $(hostname)\"",
                "",
                "# Run commands",
                "echo \"Hello from HPC job\"",
                "",
                "# End of job",
                "echo \"Job finished at $(date)\""
            ])
            
        return "\n".join(script_lines)

    def submit_job(self, job_script, job_name=None, working_dir=None):
        """Submit a job to the cluster"""
        if not self.connected or not self.client:
            return None
            
        try:
            # Upload job script to remote
            script_filename = f"job_script_{int(time.time())}.sh"
            remote_script_path = f"{self.home_dir}/{script_filename}" if not working_dir else f"{working_dir}/{script_filename}"
            
            # Create script file on remote system
            with self.sftp.open(remote_script_path, 'w') as f:
                f.write(job_script)
                
            # Make script executable
            self.execute_command(f"chmod +x {remote_script_path}")
            
            # Submit job based on scheduler
            if self.scheduler == "slurm":
                success, stdout, stderr = self.execute_command(f"cd {self.home_dir} && sbatch {remote_script_path}")
                if success:
                    # Extract job ID from output (format: "Submitted batch job 123456")
                    job_id_match = re.search(r'Submitted batch job (\d+)', stdout)
                    if job_id_match:
                        job_id = job_id_match.group(1)
                        return HPCJob(job_id, name=job_name, status=HPCJobStatus.PENDING, remote_dir=self.home_dir)
            elif self.scheduler == "pbs":
                success, stdout, stderr = self.execute_command(f"cd {self.home_dir} && qsub {remote_script_path}")
                if success:
                    # Extract job ID (usually just the output line)
                    job_id = stdout.strip()
                    return HPCJob(job_id, name=job_name, status=HPCJobStatus.PENDING, remote_dir=self.home_dir)
            
            print(f"Job submission failed: {stderr}")
            return None
            
        except Exception as e:
            traceback.print_exc()
            return None

    def get_jobs(self):
        """Get list of current jobs for the user"""
        if not self.connected or not self.client:
            return []
            
        try:
            jobs = []
            
            if self.scheduler == "slurm":
                # Format: JobID|Name|State|SubmitTime|RunTime
                _, stdout, _ = self.client.exec_command("squeue -u $USER -h -o '%i|%j|%T|%V|%M'")
                job_lines = stdout.read().decode('utf-8').strip().split('\n')
                
                for line in job_lines:
                    if not line:
                        continue
                        
                    parts = line.split('|')
                    if len(parts) >= 5:
                        job_id, name, state, submit_time, run_time = parts[:5]
                        
                        # Map SLURM state to our status
                        status_map = {
                            "PENDING": HPCJobStatus.PENDING,
                            "RUNNING": HPCJobStatus.RUNNING,
                            "COMPLETED": HPCJobStatus.COMPLETED,
                            "FAILED": HPCJobStatus.FAILED,
                            "CANCELLED": HPCJobStatus.CANCELLED,
                            "TIMEOUT": HPCJobStatus.FAILED
                        }
                        status = status_map.get(state, HPCJobStatus.UNKNOWN)
                        
                        # Get job directory (usually home dir)
                        job_dir = self.home_dir
                        
                        jobs.append(HPCJob(job_id, name=name, status=status, 
                                        submit_time=submit_time, duration=run_time,
                                        remote_dir=job_dir))
                        
            elif self.scheduler == "pbs":
                _, stdout, _ = self.client.exec_command("qstat -f")
                qstat_output = stdout.read().decode('utf-8')
                
                # Parse PBS qstat output
                job_blocks = qstat_output.split('\n\n')
                for block in job_blocks:
                    if not block.strip():
                        continue
                        
                    lines = block.split('\n')
                    job_id = None
                    job_name = None
                    job_state = None
                    submit_time = None
                    run_time = "0:00"
                    
                    for line in lines:
                        line = line.strip()
                        if line.startswith('Job Id:'):
                            job_id = line.split(':', 1)[1].strip()
                        elif line.startswith('Job_Name ='):
                            job_name = line.split('=', 1)[1].strip()
                        elif line.startswith('job_state ='):
                            job_state = line.split('=', 1)[1].strip()
                        elif line.startswith('ctime ='):
                            submit_time = line.split('=', 1)[1].strip()
                            
                    if job_id:
                        # Map PBS state to our status
                        status_map = {
                            "Q": HPCJobStatus.PENDING,
                            "R": HPCJobStatus.RUNNING,
                            "C": HPCJobStatus.COMPLETED,
                            "E": HPCJobStatus.FAILED,
                            "H": HPCJobStatus.PENDING
                        }
                        status = status_map.get(job_state, HPCJobStatus.UNKNOWN)
                        
                        jobs.append(HPCJob(job_id, name=job_name, status=status, 
                                        submit_time=submit_time, duration=run_time,
                                        remote_dir=self.home_dir))
            
            return jobs
        
        except Exception as e:
            traceback.print_exc()
            return []

    def get_job_status(self, job_id):
        """Get status of a specific job"""
        if not self.connected or not self.client:
            return None
            
        try:
            if self.scheduler == "slurm":
                # Get job details
                _, stdout, _ = self.client.exec_command(f"scontrol show job {job_id}")
                output = stdout.read().decode('utf-8').strip()
                
                if "Invalid job id" in output or not output:
                    # Check if job is in sacct (finished jobs)
                    _, stdout, _ = self.client.exec_command(f"sacct -j {job_id} -o JobID,JobName,State,Start,Elapsed -n -P")
                    sacct_output = stdout.read().decode('utf-8').strip()
                    
                    if sacct_output:
                        lines = sacct_output.split('\n')
                        for line in lines:
                            if line.startswith(f"{job_id}|"):
                                parts = line.split('|')
                                if len(parts) >= 5:
                                    job_id, name, state, start_time, elapsed = parts[:5]
                                    
                                    # Map state to our status
                                    status_map = {
                                        "COMPLETED": HPCJobStatus.COMPLETED,
                                        "FAILED": HPCJobStatus.FAILED,
                                        "CANCELLED": HPCJobStatus.CANCELLED,
                                        "TIMEOUT": HPCJobStatus.FAILED
                                    }
                                    status = status_map.get(state, HPCJobStatus.UNKNOWN)
                                    
                                    return HPCJob(job_id, name=name, status=status, 
                                               submit_time=start_time, duration=elapsed,
                                               remote_dir=self.home_dir)
                    return None
                
                # Parse scontrol output
                job_details = {}
                for pair in output.replace("\n", " ").split():
                    if "=" in pair:
                        key, value = pair.split("=", 1)
                        job_details[key] = value
                
                job_name = job_details.get("JobName", "")
                job_state = job_details.get("JobState", "")
                submit_time = job_details.get("SubmitTime", "")
                run_time = job_details.get("RunTime", "00:00:00")
                work_dir = job_details.get("WorkDir", self.home_dir)
                
                # Map SLURM state to our status
                status_map = {
                    "PENDING": HPCJobStatus.PENDING,
                    "RUNNING": HPCJobStatus.RUNNING,
                    "COMPLETED": HPCJobStatus.COMPLETED,
                    "FAILED": HPCJobStatus.FAILED,
                    "CANCELLED": HPCJobStatus.CANCELLED,
                    "TIMEOUT": HPCJobStatus.FAILED
                }
                status = status_map.get(job_state, HPCJobStatus.UNKNOWN)
                
                return HPCJob(job_id, name=job_name, status=status, 
                           submit_time=submit_time, duration=run_time,
                           remote_dir=work_dir)
                           
            elif self.scheduler == "pbs":
                _, stdout, _ = self.client.exec_command(f"qstat -f {job_id}")
                output = stdout.read().decode('utf-8').strip()
                
                if "Unknown Job Id" in output or not output:
                    return None
                
                # Parse PBS qstat output
                job_name = None
                job_state = None
                submit_time = None
                run_time = "0:00"
                
                for line in output.split('\n'):
                    line = line.strip()
                    if line.startswith('Job_Name ='):
                        job_name = line.split('=', 1)[1].strip()
                    elif line.startswith('job_state ='):
                        job_state = line.split('=', 1)[1].strip()
                    elif line.startswith('ctime ='):
                        submit_time = line.split('=', 1)[1].strip()
                    elif line.startswith('resources_used.walltime ='):
                        run_time = line.split('=', 1)[1].strip()
                        
                # Map PBS state to our status
                status_map = {
                    "Q": HPCJobStatus.PENDING,
                    "R": HPCJobStatus.RUNNING,
                    "C": HPCJobStatus.COMPLETED,
                    "E": HPCJobStatus.FAILED,
                    "H": HPCJobStatus.PENDING
                }
                status = status_map.get(job_state, HPCJobStatus.UNKNOWN)
                
                return HPCJob(job_id, name=job_name, status=status, 
                           submit_time=submit_time, duration=run_time,
                           remote_dir=self.home_dir)
                
            return None
            
        except Exception as e:
            traceback.print_exc()
            return None

    def cancel_job(self, job_id):
        """Cancel a job on the cluster"""
        if not self.connected or not self.client:
            return False
            
        try:
            if self.scheduler == "slurm":
                success, _, _ = self.execute_command(f"scancel {job_id}")
                return success
            elif self.scheduler == "pbs":
                success, _, _ = self.execute_command(f"qdel {job_id}")
                return success
            return False
        except Exception as e:
            traceback.print_exc()
            return False

    def get_file_content(self, remote_path):
        """Get the content of a file on the remote system"""
        if not self.connected or not self.sftp:
            return "Error: Not connected to HPC"
            
        try:
            # Handle relative paths
            if remote_path.startswith('~'):
                remote_path = remote_path.replace('~', self.home_dir, 1)
                
            # Check if file exists
            try:
                self.sftp.stat(remote_path)
            except FileNotFoundError:
                return f"Error: File not found: {remote_path}"
                
            # Read file content
            with self.sftp.open(remote_path, 'r') as f:
                content = f.read()
                
            return content.decode('utf-8')
        except Exception as e:
            traceback.print_exc()
            return f"Error reading file: {str(e)}"

def test_connection(config):
    """Test connection to HPC with given configuration"""
    if not PARAMIKO_AVAILABLE:
        return False, "Paramiko SSH module not available"
        
    connector = HPCConnector(config)
    success, message = connector.connect()
    
    if success:
        # Get basic system info
        cluster_info = connector.get_cluster_info()
        if "error" in cluster_info:
            connector.disconnect()
            return False, f"Connected but couldn't get system info: {cluster_info['error']}"
            
        connector.disconnect()
        
    return success, message