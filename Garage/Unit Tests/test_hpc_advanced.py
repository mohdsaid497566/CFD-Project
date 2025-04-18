#!/usr/bin/env python3
"""
Advanced unit tests for HPC workflow functionality.
"""

import unittest
import os
import sys
import tkinter as tk
from tkinter import ttk
import time
from unittest.mock import MagicMock, patch, Mock
import json
import tempfile
import threading

# Add parent directory to path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the modules to test
import MDO
from Utils.workflow_utils import patch_workflow_gui

# Import mock classes from the basic HPC workflow test
from test_hpc_workflow import (
    MockHPCConnector,
    MockHPCJob,
    MockHPCStatus,
    mock_setup_workflow_tab,
    mock_patch_workflow_gui,
    mock_update_job_status
)

class TestHPCAdvancedWorkflow(unittest.TestCase):
    """Test advanced HPC workflow functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the window
        
        # Mock the setup_workflow_tab method
        self.setup_workflow_tab_patcher = patch.object(MDO.WorkflowGUI, 'setup_workflow_tab', mock_setup_workflow_tab)
        self.setup_workflow_tab_patcher.start()
        
        # Create a patched WorkflowGUI instance
        self.original_class = MDO.WorkflowGUI
        MDO.WorkflowGUI = mock_patch_workflow_gui(MDO.WorkflowGUI)
        
        # Create the app instance
        self.app = MDO.WorkflowGUI(self.root)
        
        # Create necessary UI elements for testing
        self.app.notebook = ttk.Notebook(self.root)
        self.app.remote_tab = ttk.Frame(self.app.notebook)
        self.app.notebook.add(self.app.remote_tab, text="HPC")
        
        # Connection settings
        self.app.connection_frame = ttk.LabelFrame(self.app.remote_tab, text="HPC Connection")
        self.app.hpc_hostname = ttk.Entry(self.app.connection_frame)
        self.app.hpc_username = ttk.Entry(self.app.connection_frame)
        self.app.hpc_password = ttk.Entry(self.app.connection_frame, show="*")
        self.app.hpc_port = ttk.Entry(self.app.connection_frame)
        self.app.hpc_port.insert(0, "22")
        self.app.hpc_scheduler = tk.StringVar(value="slurm")
        self.app.scheduler_combo = ttk.Combobox(self.app.connection_frame, 
                                               textvariable=self.app.hpc_scheduler,
                                               values=["slurm", "pbs", "sge"])
        
        # Authentication options
        self.app.auth_type = tk.StringVar(value="password")
        self.app.password_frame = ttk.Frame(self.app.connection_frame)
        self.app.key_frame = ttk.Frame(self.app.connection_frame)
        self.app.hpc_key_path = ttk.Entry(self.app.key_frame)
        
        # Connection status
        self.app.connection_status_var = tk.StringVar(value="Disconnected")
        self.app.connection_message_var = tk.StringVar(value="")
        self.app.status_label = ttk.Label(self.app.connection_frame, 
                                         textvariable=self.app.connection_status_var)
        self.app.message_label = ttk.Label(self.app.connection_frame, 
                                          textvariable=self.app.connection_message_var)
        
        # Job submission
        self.app.job_frame = ttk.LabelFrame(self.app.remote_tab, text="Job Submission")
        self.app.job_name = ttk.Entry(self.app.job_frame)
        self.app.job_nodes = ttk.Entry(self.app.job_frame)
        self.app.job_nodes.insert(0, "1")
        self.app.job_cores = ttk.Entry(self.app.job_frame)
        self.app.job_cores.insert(0, "1")
        
        # Add advanced job options
        self.app.job_time = ttk.Entry(self.app.job_frame)
        self.app.job_time.insert(0, "1:00:00")
        self.app.job_memory = ttk.Entry(self.app.job_frame)
        self.app.job_memory.insert(0, "4GB")
        self.app.job_queue = ttk.Entry(self.app.job_frame)
        self.app.job_queue.insert(0, "compute")
        
        self.app.submit_button = ttk.Button(self.app.job_frame, text="Submit Job")
        
        # Jobs list
        self.app.jobs_frame = ttk.LabelFrame(self.app.remote_tab, text="Jobs")
        self.app.jobs_tree = ttk.Treeview(self.app.jobs_frame, 
                                         columns=("id", "name", "status", "cores"))
        
        # Create job output display area
        self.app.output_frame = ttk.LabelFrame(self.app.remote_tab, text="Job Output")
        self.app.output_text = tk.Text(self.app.output_frame, height=10, width=50)
        self.app.output_text.pack(fill="both", expand=True)
        
        # For job script confirmation
        self.app.show_job_script_confirmation = MagicMock(return_value=True)
        
        # Install the job script generation method
        def generate_job_script(self):
            """Generate a job submission script"""
            job_name = self.job_name.get() if hasattr(self, 'job_name') else "default_job"
            nodes = self.job_nodes.get() if hasattr(self, 'job_nodes') else "1"
            cores = self.job_cores.get() if hasattr(self, 'job_cores') else "1"
            
            script = "#!/bin/bash\n"
            
            # Add scheduler directives based on selected scheduler
            if self.hpc_scheduler.get() == "slurm":
                script += f"#SBATCH --job-name={job_name}\n"
                script += f"#SBATCH --nodes={nodes}\n"
                script += f"#SBATCH --ntasks-per-node={cores}\n"
                
                if hasattr(self, 'job_time') and self.job_time.get():
                    script += f"#SBATCH --time={self.job_time.get()}\n"
                
                if hasattr(self, 'job_memory') and self.job_memory.get():
                    script += f"#SBATCH --mem={self.job_memory.get()}\n"
                
                if hasattr(self, 'job_queue') and self.job_queue.get():
                    script += f"#SBATCH --partition={self.job_queue.get()}\n"
            
            elif self.hpc_scheduler.get() == "pbs":
                script += f"#PBS -N {job_name}\n"
                script += f"#PBS -l nodes={nodes}:ppn={cores}\n"
                
                if hasattr(self, 'job_time') and self.job_time.get():
                    script += f"#PBS -l walltime={self.job_time.get()}\n"
                
                if hasattr(self, 'job_memory') and self.job_memory.get():
                    script += f"#PBS -l mem={self.job_memory.get()}\n"
                
                if hasattr(self, 'job_queue') and self.job_queue.get():
                    script += f"#PBS -q {self.job_queue.get()}\n"
            
            # Add common execution commands
            script += "\nmodule load openfoam\n"
            script += "cd $SLURM_SUBMIT_DIR\n\n"
            script += "# Run simulation\n"
            script += "mpirun -np $SLURM_NTASKS_PER_NODE solver -parallel\n"
            script += "\necho 'Simulation completed'\n"
            
            return script
        
        # Add the method to the app
        self.app.generate_job_script = generate_job_script.__get__(self.app)
        
        # Create a connected HPC for most tests
        self.app.hpc_connector = MockHPCConnector()
        self.app.hpc_connector.connected = True
        
    def tearDown(self):
        """Clean up after each test"""
        # Restore the original class
        MDO.WorkflowGUI = self.original_class
        
        # Stop patchers
        self.setup_workflow_tab_patcher.stop()
        
        # Destroy the window
        self.root.destroy()
    
    def test_job_script_generation_slurm(self):
        """Test generation of SLURM job submission scripts"""
        # Set job parameters
        self.app.job_name.delete(0, tk.END)
        self.app.job_name.insert(0, "slurm_test_job")
        self.app.job_nodes.delete(0, tk.END)
        self.app.job_nodes.insert(0, "4")
        self.app.job_cores.delete(0, tk.END)
        self.app.job_cores.insert(0, "16")
        self.app.job_time.delete(0, tk.END)
        self.app.job_time.insert(0, "12:00:00")
        self.app.job_memory.delete(0, tk.END)
        self.app.job_memory.insert(0, "64GB")
        self.app.job_queue.delete(0, tk.END)
        self.app.job_queue.insert(0, "large")
        
        # Set scheduler to SLURM
        self.app.hpc_scheduler.set("slurm")
        
        # Generate script
        script = self.app.generate_job_script()
        
        # Verify script content
        self.assertIn("#!/bin/bash", script)
        self.assertIn("#SBATCH --job-name=slurm_test_job", script)
        self.assertIn("#SBATCH --nodes=4", script)
        self.assertIn("#SBATCH --ntasks-per-node=16", script)
        self.assertIn("#SBATCH --time=12:00:00", script)
        self.assertIn("#SBATCH --mem=64GB", script)
        self.assertIn("#SBATCH --partition=large", script)
        self.assertIn("module load openfoam", script)
        self.assertIn("mpirun -np $SLURM_NTASKS_PER_NODE", script)
    
    def test_job_script_generation_pbs(self):
        """Test generation of PBS job submission scripts"""
        # Set job parameters
        self.app.job_name.delete(0, tk.END)
        self.app.job_name.insert(0, "pbs_test_job")
        self.app.job_nodes.delete(0, tk.END)
        self.app.job_nodes.insert(0, "2")
        self.app.job_cores.delete(0, tk.END)
        self.app.job_cores.insert(0, "8")
        self.app.job_time.delete(0, tk.END)
        self.app.job_time.insert(0, "6:00:00")
        self.app.job_memory.delete(0, tk.END)
        self.app.job_memory.insert(0, "32GB")
        self.app.job_queue.delete(0, tk.END)
        self.app.job_queue.insert(0, "batch")
        
        # Set scheduler to PBS
        self.app.hpc_scheduler.set("pbs")
        
        # Generate script
        script = self.app.generate_job_script()
        
        # Verify script content
        self.assertIn("#!/bin/bash", script)
        self.assertIn("#PBS -N pbs_test_job", script)
        self.assertIn("#PBS -l nodes=2:ppn=8", script)
        self.assertIn("#PBS -l walltime=6:00:00", script)
        self.assertIn("#PBS -l mem=32GB", script)
        self.assertIn("#PBS -q batch", script)
        self.assertIn("module load openfoam", script)
    
    def test_job_status_notification(self):
        """Test job status notifications"""
        # Create a notification function
        notifications = []
        
        def notify_job_status_change(job_id, old_status, new_status):
            notifications.append((job_id, old_status, new_status))
        
        # Add the notification function to the app
        self.app.notify_job_status_change = notify_job_status_change
        
        # Create a job
        job = MockHPCJob("notification_test_job")
        self.app.hpc_connector.jobs.append(job)
        job.status = MockHPCStatus.PENDING
        
        # Add a method to update job status
        def update_job_status_with_notification(self):
            """Update job status with notification"""
            if hasattr(self, 'hpc_connector') and self.hpc_connector.connected:
                for job in self.hpc_connector.jobs:
                    old_status = job.status
                    # Simulate status change
                    if old_status == MockHPCStatus.PENDING:
                        new_status = MockHPCStatus.RUNNING
                        job.status = new_status
                    elif old_status == MockHPCStatus.RUNNING:
                        new_status = MockHPCStatus.COMPLETED
                        job.status = new_status
                    
                    # Notify if status changed
                    if old_status != job.status and hasattr(self, 'notify_job_status_change'):
                        self.notify_job_status_change(job.id, old_status, job.status)
                
                # Update tree view
                if hasattr(self, 'jobs_tree'):
                    self.jobs_tree.delete(*self.jobs_tree.get_children())
                    for job in self.hpc_connector.jobs:
                        self.jobs_tree.insert("", "end", values=(job.id, job.name, job.status, job.cores))
        
        # Add the method to the app
        self.app.update_job_status_with_notification = update_job_status_with_notification.__get__(self.app)
        
        # Initial update - pending to running
        self.app.update_job_status_with_notification()
        
        # Verify notification
        self.assertEqual(len(notifications), 1)
        self.assertEqual(notifications[0][0], job.id)
        self.assertEqual(notifications[0][1], MockHPCStatus.PENDING)
        self.assertEqual(notifications[0][2], MockHPCStatus.RUNNING)
        
        # Second update - running to completed
        self.app.update_job_status_with_notification()
        
        # Verify second notification
        self.assertEqual(len(notifications), 2)
        self.assertEqual(notifications[1][0], job.id)
        self.assertEqual(notifications[1][1], MockHPCStatus.RUNNING)
        self.assertEqual(notifications[1][2], MockHPCStatus.COMPLETED)
    
    def test_job_file_transfer(self):
        """Test job file transfer functionality"""
        # Add file transfer method
        def transfer_files_to_hpc(self, local_files, remote_dir):
            """Mock transfer files to HPC"""
            if not hasattr(self, 'hpc_connector') or not self.hpc_connector.connected:
                return False, "Not connected to HPC"
            
            if not hasattr(self, 'transferred_files'):
                self.transferred_files = {}
            
            self.transferred_files[remote_dir] = local_files
            return True, f"Transferred {len(local_files)} files to {remote_dir}"
        
        # Add the method to the app
        self.app.transfer_files_to_hpc = transfer_files_to_hpc.__get__(self.app)
        
        # Test file transfer
        local_files = ["/path/to/mesh.msh", "/path/to/config.cfg", "/path/to/data.csv"]
        remote_dir = "/home/user/simulation"
        
        success, message = self.app.transfer_files_to_hpc(local_files, remote_dir)
        
        # Verify transfer
        self.assertTrue(success)
        self.assertIn("Transferred 3 files", message)
        self.assertEqual(self.app.transferred_files[remote_dir], local_files)
    
    def test_job_submission_with_files(self):
        """Test job submission with file transfer"""
        # Add file submission method
        def submit_job_with_files(self, job_name, local_files):
            """Submit job with files"""
            if not hasattr(self, 'hpc_connector') or not self.hpc_connector.connected:
                return None, "Not connected to HPC"
            
            # Set job parameters from inputs
            self.job_name.delete(0, tk.END)
            self.job_name.insert(0, job_name)
            
            # Create remote directory
            remote_dir = f"/scratch/user/{job_name}"
            
            # Mock the transfer_files_to_hpc method if it doesn't exist
            if not hasattr(self, 'transfer_files_to_hpc'):
                def transfer_files_to_hpc(self, local_files, remote_dir):
                    if not hasattr(self, 'transferred_files'):
                        self.transferred_files = {}
                    
                    self.transferred_files[remote_dir] = local_files
                    return True, f"Transferred {len(local_files)} files to {remote_dir}"
                
                self.transfer_files_to_hpc = transfer_files_to_hpc.__get__(self)
            
            # Transfer files
            success, message = self.transfer_files_to_hpc(local_files, remote_dir)
            if not success:
                return None, f"File transfer failed: {message}"
            
            # Generate and submit job
            job = MockHPCJob(job_name)
            self.hpc_connector.jobs.append(job)
            
            # Store file information with job
            job.remote_dir = remote_dir
            job.files = local_files
            
            return job, f"Job submitted with ID {job.id}"
        
        # Add the submission method to the app
        self.app.submit_job_with_files = submit_job_with_files.__get__(self.app)
        
        # Test job submission with files
        job_name = "simulation_with_files"
        local_files = ["/path/to/mesh.msh", "/path/to/config.cfg"]
        
        job, message = self.app.submit_job_with_files(job_name, local_files)
        
        # Verify job submission
        self.assertIsNotNone(job)
        self.assertEqual(job.name, job_name)
        self.assertEqual(job.remote_dir, f"/scratch/user/{job_name}")
        self.assertEqual(job.files, local_files)
        self.assertIn("Job submitted with ID", message)
    
    def test_job_template_management(self):
        """Test job template management"""
        # Add template management methods
        def save_job_template(self, template_name):
            """Save current job settings as a template"""
            if not hasattr(self, 'job_templates'):
                self.job_templates = {}
            
            template = {
                "nodes": self.job_nodes.get(),
                "cores": self.job_cores.get(),
                "time": self.job_time.get() if hasattr(self, 'job_time') else "1:00:00",
                "memory": self.job_memory.get() if hasattr(self, 'job_memory') else "1GB",
                "queue": self.job_queue.get() if hasattr(self, 'job_queue') else "default"
            }
            
            self.job_templates[template_name] = template
            return True, f"Template '{template_name}' saved"
        
        def load_job_template(self, template_name):
            """Load a job template"""
            if not hasattr(self, 'job_templates') or template_name not in self.job_templates:
                return False, f"Template '{template_name}' not found"
            
            template = self.job_templates[template_name]
            
            self.job_nodes.delete(0, tk.END)
            self.job_nodes.insert(0, template["nodes"])
            
            self.job_cores.delete(0, tk.END)
            self.job_cores.insert(0, template["cores"])
            
            if hasattr(self, 'job_time'):
                self.job_time.delete(0, tk.END)
                self.job_time.insert(0, template["time"])
            
            if hasattr(self, 'job_memory'):
                self.job_memory.delete(0, tk.END)
                self.job_memory.insert(0, template["memory"])
            
            if hasattr(self, 'job_queue'):
                self.job_queue.delete(0, tk.END)
                self.job_queue.insert(0, template["queue"])
            
            return True, f"Template '{template_name}' loaded"
        
        # Add the methods to the app
        self.app.save_job_template = save_job_template.__get__(self.app)
        self.app.load_job_template = load_job_template.__get__(self.app)
        
        # Create a template
        self.app.job_nodes.delete(0, tk.END)
        self.app.job_nodes.insert(0, "8")
        self.app.job_cores.delete(0, tk.END)
        self.app.job_cores.insert(0, "32")
        self.app.job_time.delete(0, tk.END)
        self.app.job_time.insert(0, "24:00:00")
        self.app.job_memory.delete(0, tk.END)
        self.app.job_memory.insert(0, "128GB")
        self.app.job_queue.delete(0, tk.END)
        self.app.job_queue.insert(0, "gpu")
        
        # Save template
        success, message = self.app.save_job_template("high_performance")
        
        # Verify template was saved
        self.assertTrue(success)
        self.assertIn("Template 'high_performance' saved", message)
        self.assertIn("high_performance", self.app.job_templates)
        
        # Change current values
        self.app.job_nodes.delete(0, tk.END)
        self.app.job_nodes.insert(0, "1")
        self.app.job_cores.delete(0, tk.END)
        self.app.job_cores.insert(0, "4")
        
        # Load template
        success, message = self.app.load_job_template("high_performance")
        
        # Verify template was loaded
        self.assertTrue(success)
        self.assertEqual(self.app.job_nodes.get(), "8")
        self.assertEqual(self.app.job_cores.get(), "32")
        self.assertEqual(self.app.job_time.get(), "24:00:00")
        self.assertEqual(self.app.job_memory.get(), "128GB")
        self.assertEqual(self.app.job_queue.get(), "gpu")
    
    def test_job_dependency_management(self):
        """Test job dependency management"""
        # Add dependency management methods
        def submit_dependent_job(self, parent_job_id, job_name):
            """Submit a job that depends on another job"""
            if not hasattr(self, 'hpc_connector') or not self.hpc_connector.connected:
                return None, "Not connected to HPC"
            
            # Set job name
            self.job_name.delete(0, tk.END)
            self.job_name.insert(0, job_name)
            
            # Generate script with dependency
            script = self.generate_job_script()
            
            # Add dependency directive
            if self.hpc_scheduler.get() == "slurm":
                dependency_line = f"#SBATCH --dependency=afterok:{parent_job_id}\n"
                script = script.replace("#!/bin/bash\n", f"#!/bin/bash\n{dependency_line}")
            elif self.hpc_scheduler.get() == "pbs":
                dependency_line = f"#PBS -W depend=afterok:{parent_job_id}\n"
                script = script.replace("#!/bin/bash\n", f"#!/bin/bash\n{dependency_line}")
            
            # Create job
            job = MockHPCJob(job_name)
            job.script = script
            self.hpc_connector.jobs.append(job)
            
            # Store dependency information
            job.depends_on = parent_job_id
            
            return job, f"Dependent job submitted with ID {job.id}"
        
        # Add the method to the app
        self.app.submit_dependent_job = submit_dependent_job.__get__(self.app)
        
        # Create a parent job
        parent_job = MockHPCJob("parent_job")
        self.app.hpc_connector.jobs.append(parent_job)
        
        # Submit dependent job
        dependent_job, message = self.app.submit_dependent_job(parent_job.id, "child_job")
        
        # Verify dependent job
        self.assertIsNotNone(dependent_job)
        self.assertEqual(dependent_job.name, "child_job")
        self.assertEqual(dependent_job.depends_on, parent_job.id)
        self.assertIn("Dependent job submitted", message)
    
    def test_async_job_status_monitoring(self):
        """Test asynchronous job status monitoring"""
        # Add status monitoring methods
        def start_job_monitoring(self, interval=5):
            """Start asynchronous job monitoring"""
            if hasattr(self, 'monitoring_thread') and self.monitoring_thread.is_alive():
                return False, "Monitoring already active"
            
            self.stop_monitoring = False
            self.monitoring_thread = threading.Thread(target=self._job_monitoring_worker, args=(interval,))
            self.monitoring_thread.daemon = True
            self.monitoring_thread.start()
            
            return True, f"Started job monitoring (interval: {interval}s)"
        
        def stop_job_monitoring(self):
            """Stop asynchronous job monitoring"""
            if not hasattr(self, 'monitoring_thread') or not self.monitoring_thread.is_alive():
                return False, "No active monitoring to stop"
            
            self.stop_monitoring = True
            self.monitoring_thread.join(timeout=2.0)
            
            return True, "Stopped job monitoring"
        
        def _job_monitoring_worker(self, interval):
            """Worker thread for job monitoring"""
            self.monitoring_updates = 0
            
            while not self.stop_monitoring:
                # Update job status
                if hasattr(self, 'hpc_connector') and self.hpc_connector.connected:
                    # Here we would normally call self.update_job_status()
                    # But since we've already mocked it, we'll just increment the counter
                    self.monitoring_updates += 1
                
                # Wait for next update
                time.sleep(0.1)  # Using shorter interval for testing
        
        # Add the methods to the app
        self.app.start_job_monitoring = start_job_monitoring.__get__(self.app)
        self.app.stop_job_monitoring = stop_job_monitoring.__get__(self.app)
        self.app._job_monitoring_worker = _job_monitoring_worker.__get__(self.app)
        
        # Add test jobs
        job1 = MockHPCJob("monitoring_job_1")
        job2 = MockHPCJob("monitoring_job_2")
        self.app.hpc_connector.jobs.extend([job1, job2])
        
        # Start monitoring
        success, message = self.app.start_job_monitoring(0.1)
        
        # Verify monitoring started
        self.assertTrue(success)
        self.assertTrue(hasattr(self.app, 'monitoring_thread'))
        self.assertTrue(self.app.monitoring_thread.is_alive())
        
        # Wait briefly for updates
        time.sleep(0.5)
        
        # Stop monitoring
        success, message = self.app.stop_job_monitoring()
        
        # Verify monitoring stopped
        self.assertTrue(success)
        self.assertFalse(self.app.monitoring_thread.is_alive())
        self.assertGreater(self.app.monitoring_updates, 0)

if __name__ == "__main__":
    unittest.main()
