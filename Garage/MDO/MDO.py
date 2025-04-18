# Add this method to the WorkflowGUI class:

class WorkflowGUI:
    # ...existing code...
    
    def setup_workflow_tab(self):
        """Set up the workflow tab with HPC connection controls and job submission interface."""
        try:
            from PyQt5.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                                         QLineEdit, QComboBox, QGroupBox, QTextEdit,
                                         QFileDialog, QTabWidget, QWidget, QCheckBox)
            
            # Create the main workflow tab widget if it doesn't exist
            if not hasattr(self, 'workflow_tab'):
                self.workflow_tab = QWidget()
                
            # Main layout
            main_layout = QVBoxLayout(self.workflow_tab)
            
            # Connection section
            connection_group = QGroupBox("HPC Connection")
            connection_layout = QVBoxLayout(connection_group)
            
            # Host and credential inputs
            form_layout = QHBoxLayout()
            
            # Host input
            host_layout = QVBoxLayout()
            host_layout.addWidget(QLabel("Host:"))
            self.host_input = QLineEdit()
            self.host_input.setPlaceholderText("HPC hostname or IP")
            host_layout.addWidget(self.host_input)
            form_layout.addLayout(host_layout)
            
            # Username input
            username_layout = QVBoxLayout()
            username_layout.addWidget(QLabel("Username:"))
            self.username_input = QLineEdit()
            username_layout.addWidget(self.username_input)
            form_layout.addLayout(username_layout)
            
            # Authentication type
            auth_layout = QVBoxLayout()
            auth_layout.addWidget(QLabel("Authentication:"))
            self.auth_type_combo = QComboBox()
            self.auth_type_combo.addItems(["Password", "SSH Key"])
            auth_layout.addWidget(self.auth_type_combo)
            form_layout.addLayout(auth_layout)
            
            # Password field
            password_layout = QVBoxLayout()
            password_layout.addWidget(QLabel("Password:"))
            self.password_input = QLineEdit()
            self.password_input.setEchoMode(QLineEdit.Password)
            password_layout.addWidget(self.password_input)
            form_layout.addLayout(password_layout)
            
            # SSH key selection
            key_file_layout = QVBoxLayout()
            key_file_layout.addWidget(QLabel("SSH Key File:"))
            key_file_form = QHBoxLayout()
            self.key_file_input = QLineEdit()
            self.key_file_input.setEnabled(False)
            key_file_form.addWidget(self.key_file_input)
            self.browse_key_button = QPushButton("Browse")
            self.browse_key_button.setEnabled(False)
            key_file_form.addWidget(self.browse_key_button)
            key_file_layout.addLayout(key_file_form)
            form_layout.addLayout(key_file_layout)
            
            connection_layout.addLayout(form_layout)
            
            # Connect button
            connect_layout = QHBoxLayout()
            self.connect_button = QPushButton("Connect to HPC")
            connect_layout.addWidget(self.connect_button)
            connection_layout.addLayout(connect_layout)
            
            # Status display
            self.connection_status = QLabel("Not connected")
            connection_layout.addWidget(self.connection_status)
            
            # Add the connection group to main layout
            main_layout.addWidget(connection_group)
            
            # Job submission section
            job_group = QGroupBox("Job Submission")
            job_layout = QVBoxLayout(job_group)
            
            # Job script
            script_layout = QVBoxLayout()
            script_layout.addWidget(QLabel("Job Script:"))
            
            script_editor_layout = QHBoxLayout()
            self.script_editor = QTextEdit()
            self.script_editor.setPlaceholderText("Enter job script here\n#!/bin/bash\n#SBATCH --job-name=test\n#SBATCH --nodes=1\n...")
            script_editor_layout.addWidget(self.script_editor)
            
            template_layout = QVBoxLayout()
            template_layout.addWidget(QLabel("Templates:"))
            self.template_combo = QComboBox()
            self.template_combo.addItems(["Slurm Basic", "PBS Basic", "MPI Job", "GPU Job"])
            template_layout.addWidget(self.template_combo)
            self.load_template_button = QPushButton("Load Template")
            template_layout.addWidget(self.load_template_button)
            template_layout.addStretch()
            script_editor_layout.addLayout(template_layout)
            
            script_layout.addLayout(script_editor_layout)
            job_layout.addLayout(script_layout)
            
            # Job submission options
            options_layout = QHBoxLayout()
            
            # Working directory
            workdir_layout = QVBoxLayout()
            workdir_layout.addWidget(QLabel("Remote Working Directory:"))
            workdir_input_layout = QHBoxLayout()
            self.workdir_input = QLineEdit()
            workdir_input_layout.addWidget(self.workdir_input)
            self.browse_remote_button = QPushButton("Browse")
            workdir_input_layout.addWidget(self.browse_remote_button)
            workdir_layout.addLayout(workdir_input_layout)
            options_layout.addLayout(workdir_layout)
            
            # File transfer section
            file_transfer_layout = QVBoxLayout()
            file_transfer_layout.addWidget(QLabel("File Transfer:"))
            self.transfer_files_check = QCheckBox("Transfer Files")
            file_transfer_layout.addWidget(self.transfer_files_check)
            self.add_file_button = QPushButton("Add Files")
            file_transfer_layout.addWidget(self.add_file_button)
            options_layout.addLayout(file_transfer_layout)
            
            job_layout.addLayout(options_layout)
            
            # File list
            file_list_layout = QVBoxLayout()
            file_list_layout.addWidget(QLabel("Files to Transfer:"))
            self.file_list = QTextEdit()
            self.file_list.setMaximumHeight(80)
            self.file_list.setReadOnly(True)
            file_list_layout.addWidget(self.file_list)
            job_layout.addLayout(file_list_layout)
            
            # Submit button
            submit_layout = QHBoxLayout()
            self.submit_button = QPushButton("Submit Job")
            submit_layout.addWidget(self.submit_button)
            job_layout.addLayout(submit_layout)
            
            # Job status
            self.job_status = QLabel("No job submitted")
            job_layout.addWidget(self.job_status)
            
            # Add the job group to main layout
            main_layout.addWidget(job_group)
            
            # Set up the tab
            self.workflow_tab.setLayout(main_layout)
            
            # Connect signals
            self.auth_type_combo.currentIndexChanged.connect(self._toggle_auth_fields)
            self.browse_key_button.clicked.connect(self._browse_ssh_key)
            self.connect_button.clicked.connect(self._connect_to_hpc)
            self.load_template_button.clicked.connect(self._load_script_template)
            self.browse_remote_button.clicked.connect(self._browse_remote_directory)
            self.add_file_button.clicked.connect(self._add_transfer_file)
            self.submit_button.clicked.connect(self._submit_job)
            self.transfer_files_check.toggled.connect(self._toggle_file_transfer)
            
            # Initial state
            self._toggle_auth_fields(0)  # Password is default (index 0)
            self._toggle_file_transfer(False)
            
            return self.workflow_tab
            
        except Exception as e:
            import traceback
            print(f"Error setting up workflow tab: {str(e)}")
            print(traceback.format_exc())
            return QWidget()  # Return empty widget on error
    
    def _toggle_auth_fields(self, index):
        """Toggle between password and key file authentication."""
        password_auth = index == 0
        self.password_input.setEnabled(password_auth)
        self.key_file_input.setEnabled(not password_auth)
        self.browse_key_button.setEnabled(not password_auth)
    
    def _browse_ssh_key(self):
        """Open file dialog to select SSH key file."""
        try:
            from PyQt5.QtWidgets import QFileDialog
            filename, _ = QFileDialog.getOpenFileName(
                self.workflow_tab, "Select SSH Key File", "", "All Files (*)")
            if filename:
                self.key_file_input.setText(filename)
        except Exception as e:
            print(f"Error browsing for SSH key: {str(e)}")
    
    def _connect_to_hpc(self):
        """Connect to the HPC system."""
        try:
            from hpc_connector import HPCConnector
            
            host = self.host_input.text()
            username = self.username_input.text()
            
            if not host or not username:
                self.connection_status.setText("Error: Host and username required")
                return
            
            # Get the appropriate credentials based on auth type
            auth_type = "password" if self.auth_type_combo.currentIndex() == 0 else "key"
            password = self.password_input.text() if auth_type == "password" else None
            key_file = self.key_file_input.text() if auth_type == "key" else None
            
            # Create connector with configuration
            config = {
                'host': host,
                'username': username,
                'auth_type': auth_type
            }
            self.hpc = HPCConnector(config)
            
            # Attempt connection
            self.connection_status.setText("Connecting...")
            connection_result = self.hpc.connect(
                host=host, 
                username=username, 
                password=password, 
                key_file=key_file
            )
            
            if connection_result:
                self.connection_status.setText("Connected to HPC")
                # Update UI with system info
                system_info = self.hpc.get_system_info()
                if system_info:
                    info_text = f"Connected to {system_info['hostname']} ({system_info['system_type']})"
                    self.connection_status.setText(info_text)
            else:
                self.connection_status.setText("Failed to connect")
        
        except Exception as e:
            self.connection_status.setText(f"Error: {str(e)}")
            print(f"Error connecting to HPC: {str(e)}")
    
    def _load_script_template(self):
        """Load a job script template based on selection."""
        template_name = self.template_combo.currentText()
        
        templates = {
            "Slurm Basic": """#!/bin/bash
#SBATCH --job-name=my_job
#SBATCH --output=output_%j.log
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --time=01:00:00
#SBATCH --mem=4G

echo "Job started at $(date)"
echo "Running on host: $(hostname)"

# Your commands here
echo "Hello, HPC World!"

echo "Job finished at $(date)"
""",
            "PBS Basic": """#!/bin/bash
#PBS -N my_job
#PBS -o output.log
#PBS -e error.log
#PBS -l nodes=1:ppn=1
#PBS -l walltime=01:00:00
#PBS -l mem=4gb

echo "Job started at $(date)"
echo "Running on host: $(hostname)"

# Your commands here
echo "Hello, HPC World!"

echo "Job finished at $(date)"
""",
            "MPI Job": """#!/bin/bash
#SBATCH --job-name=mpi_job
#SBATCH --output=mpi_%j.log
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=4
#SBATCH --time=02:00:00
#SBATCH --mem=8G

module load mpi/openmpi-4.0

echo "Job started at $(date)"
echo "Running on host: $(hostname)"

mpirun -np 8 ./my_mpi_program

echo "Job finished at $(date)"
""",
            "GPU Job": """#!/bin/bash
#SBATCH --job-name=gpu_job
#SBATCH --output=gpu_%j.log
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --gres=gpu:1
#SBATCH --time=04:00:00
#SBATCH --mem=16G

module load cuda/11.0

echo "Job started at $(date)"
echo "Running on host: $(hostname)"
echo "GPU information:"
nvidia-smi

# Your GPU program
./my_gpu_program

echo "Job finished at $(date)"
"""
        }
        
        if template_name in templates:
            self.script_editor.setText(templates[template_name])
    
    def _browse_remote_directory(self):
        """Browse remote directory structure."""
        # In a real implementation, this would show a dialog with remote directories
        # For now, just set a placeholder
        self.workdir_input.setText("/home/username/jobs")
    
    def _toggle_file_transfer(self, enabled):
        """Enable or disable file transfer options."""
        self.add_file_button.setEnabled(enabled)
        self.file_list.setEnabled(enabled)
    
    def _add_transfer_file(self):
        """Add files for transfer to HPC."""
        try:
            from PyQt5.QtWidgets import QFileDialog
            filenames, _ = QFileDialog.getOpenFileNames(
                self.workflow_tab, "Select Files to Transfer", "", "All Files (*)")
            
            if filenames:
                current_text = self.file_list.toPlainText()
                new_files = "\n".join(filenames)
                if current_text:
                    self.file_list.setText(f"{current_text}\n{new_files}")
                else:
                    self.file_list.setText(new_files)
        except Exception as e:
            print(f"Error adding transfer files: {str(e)}")
    
    def _submit_job(self):
        """Submit job to the HPC system."""
        try:
            if not hasattr(self, 'hpc') or not self.hpc.connected:
                self.job_status.setText("Error: Not connected to HPC")
                return
            
            script = self.script_editor.toPlainText()
            if not script:
                self.job_status.setText("Error: Job script is empty")
                return
            
            remote_dir = self.workdir_input.text()
            if not remote_dir:
                remote_dir = None  # Use default
            
            # Submit the job
            self.job_status.setText("Submitting job...")
            
            # If file transfer is enabled, transfer files first
            if self.transfer_files_check.isChecked():
                files = self.file_list.toPlainText().split('\n')
                files = [f for f in files if f.strip()]  # Remove empty lines
                
                if files:
                    self.job_status.setText("Transferring files...")
                    for file_path in files:
                        remote_file = file_path.split('/')[-1]  # Just the filename
                        if remote_dir:
                            remote_path = f"{remote_dir}/{remote_file}"
                        else:
                            remote_path = remote_file
                            
                        success, message = self.hpc.transfer_file(file_path, remote_path)
                        if not success:
                            self.job_status.setText(f"Error transferring file: {message}")
                            return
            
            # Submit the job
            success, job_id = self.hpc.submit_job(script, remote_dir)
            
            if success:
                self.job_status.setText(f"Job submitted successfully. Job ID: {job_id}")
            else:
                self.job_status.setText(f"Job submission failed: {job_id}")
        
        except Exception as e:
            self.job_status.setText(f"Error: {str(e)}")
            print(f"Error submitting job: {str(e)}")