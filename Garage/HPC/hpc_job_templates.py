#!/usr/bin/env python3
"""
HPC Job Templates for the Intake CFD Project.

This module provides functionality for creating, managing and using HPC job templates
for running CFD simulations on HPC systems.
"""

import os
import sys
import json
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("hpc_templates")

class JobTemplateManager:
    """Manager for HPC job templates"""
    
    def __init__(self, templates_dir=None):
        """
        Initialize the job template manager.
        
        Args:
            templates_dir: Directory where templates are stored
        """
        # Default templates directory is under the HPC config directory
        if templates_dir is None:
            templates_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "Config", "hpc_templates"
            )
        
        self.templates_dir = templates_dir
        
        # Ensure templates directory exists
        os.makedirs(self.templates_dir, exist_ok=True)
        
        # Template categories
        self.categories = ["OpenFOAM", "Parametric", "DoE", "Post-Processing", "Custom"]
        
        # Initialize empty template registry
        self.templates = {}
        
        # Load existing templates
        self.load_templates()
    
    def load_templates(self):
        """Load all templates from the templates directory"""
        self.templates = {}
        
        try:
            # Get all template files
            for file in Path(self.templates_dir).glob("*.json"):
                try:
                    with open(file, 'r') as f:
                        template = json.load(f)
                    
                    # Validate template
                    if self._validate_template(template):
                        self.templates[template["name"]] = template
                        logger.info(f"Loaded template: {template['name']}")
                    else:
                        logger.warning(f"Invalid template in file {file}")
                        
                except Exception as e:
                    logger.error(f"Error loading template {file}: {str(e)}")
                    
            logger.info(f"Loaded {len(self.templates)} job templates")
            
        except Exception as e:
            logger.error(f"Error loading templates: {str(e)}")
    
    def _validate_template(self, template):
        """
        Validate that a template has the required fields.
        
        Args:
            template: The template dictionary to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        required_fields = ["name", "description", "category", "scheduler", "script_template"]
        for field in required_fields:
            if field not in template:
                logger.warning(f"Template missing required field: {field}")
                return False
        
        return True
    
    def save_template(self, template):
        """
        Save a template to file.
        
        Args:
            template: Template dictionary
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self._validate_template(template):
            return False
        
        try:
            # Create safe filename from template name
            filename = template["name"].replace(" ", "_").replace("/", "_").lower() + ".json"
            file_path = os.path.join(self.templates_dir, filename)
            
            with open(file_path, 'w') as f:
                json.dump(template, f, indent=4)
                
            # Add to templates dictionary
            self.templates[template["name"]] = template
            
            logger.info(f"Saved template '{template['name']}' to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving template '{template.get('name', 'unknown')}': {str(e)}")
            return False
    
    def delete_template(self, template_name):
        """
        Delete a template.
        
        Args:
            template_name: Name of the template to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        if template_name not in self.templates:
            logger.warning(f"Template not found: {template_name}")
            return False
        
        try:
            # Generate filename
            filename = template_name.replace(" ", "_").replace("/", "_").lower() + ".json"
            file_path = os.path.join(self.templates_dir, filename)
            
            # Remove file if it exists
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Deleted template file {file_path}")
                
            # Remove from templates dictionary
            del self.templates[template_name]
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting template '{template_name}': {str(e)}")
            return False
    
    def get_template(self, template_name):
        """
        Get a template by name.
        
        Args:
            template_name: Name of the template
            
        Returns:
            dict: Template dictionary or None if not found
        """
        return self.templates.get(template_name)
    
    def get_template_names(self, category=None):
        """
        Get list of template names, optionally filtered by category.
        
        Args:
            category: Optional category filter
            
        Returns:
            list: List of template names
        """
        if category:
            return [name for name, template in self.templates.items() 
                  if template.get("category") == category]
        else:
            return list(self.templates.keys())
    
    def create_template(self, name, description, category, scheduler, script_template, 
                      parameters=None, environment=None):
        """
        Create a new job template.
        
        Args:
            name: Template name
            description: Template description
            category: Template category
            scheduler: Job scheduler type (slurm, pbs, etc.)
            script_template: The job script template text
            parameters: Dictionary of template parameters
            environment: Dictionary of environment settings
            
        Returns:
            dict: The created template
        """
        template = {
            "name": name,
            "description": description,
            "category": category,
            "scheduler": scheduler,
            "script_template": script_template,
            "parameters": parameters or {},
            "environment": environment or {},
            "created": True
        }
        
        return template
    
    def generate_script(self, template_name, parameters=None):
        """
        Generate a job script from a template with parameters.
        
        Args:
            template_name: Name of the template to use
            parameters: Dictionary of parameters to substitute
            
        Returns:
            tuple: (success, script_text or error message)
        """
        template = self.get_template(template_name)
        if not template:
            return False, f"Template not found: {template_name}"
        
        script_template = template["script_template"]
        param_dict = {}
        
        # Start with template default parameters
        param_dict.update(template.get("parameters", {}))
        
        # Override with provided parameters
        if parameters:
            param_dict.update(parameters)
        
        # Substitute parameters in template
        try:
            script_text = script_template
            
            # Replace all {{parameter}} placeholders
            for param_name, param_value in param_dict.items():
                placeholder = f"{{{{{param_name}}}}}"
                script_text = script_text.replace(placeholder, str(param_value))
            
            return True, script_text
            
        except Exception as e:
            logger.error(f"Error generating script from template '{template_name}': {str(e)}")
            return False, f"Error generating script: {str(e)}"
    
    def import_template_from_file(self, file_path):
        """
        Import a template from a file.
        
        Args:
            file_path: Path to the template file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with open(file_path, 'r') as f:
                template = json.load(f)
            
            # Validate and save template
            if self._validate_template(template):
                return self.save_template(template)
            else:
                logger.warning(f"Invalid template in file {file_path}")
                return False
                
        except Exception as e:
            logger.error(f"Error importing template from {file_path}: {str(e)}")
            return False
    
    def export_template_to_file(self, template_name, file_path):
        """
        Export a template to a file.
        
        Args:
            template_name: Name of the template to export
            file_path: Path where to save the template
            
        Returns:
            bool: True if successful, False otherwise
        """
        template = self.get_template(template_name)
        if not template:
            logger.warning(f"Template not found: {template_name}")
            return False
        
        try:
            with open(file_path, 'w') as f:
                json.dump(template, f, indent=4)
                
            logger.info(f"Exported template '{template_name}' to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting template '{template_name}' to {file_path}: {str(e)}")
            return False
    
    def create_default_templates(self):
        """
        Create a set of default templates for common HPC workflows.
        
        Returns:
            int: Number of templates created
        """
        count = 0
        
        # Create default OpenFOAM templates
        openfoam_templates = [
            self.create_template(
                name="OpenFOAM SimpleFoam",
                description="Standard OpenFOAM simpleFoam solver for steady-state incompressible flows",
                category="OpenFOAM",
                scheduler="slurm",
                script_template="""#!/bin/bash
#SBATCH --job-name={{job_name}}
#SBATCH --output={{job_name}}-%j.out
#SBATCH --error={{job_name}}-%j.err
#SBATCH --nodes={{nodes}}
#SBATCH --ntasks-per-node={{cores_per_node}}
#SBATCH --time={{wall_time}}
#SBATCH --mem={{memory}}
#SBATCH --partition={{partition}}

echo "Starting OpenFOAM simpleFoam job at $(date)"
echo "Running on $(hostname) with $(nproc) processors"

# Load required modules
module load {{openfoam_module}}
module load {{mpi_module}}

# Setup OpenFOAM environment
source $FOAM_ETC/bashrc

# Copy case files to scratch directory
SCRATCH_DIR="/scratch/$USER/$SLURM_JOB_ID"
mkdir -p $SCRATCH_DIR
cp -r {{case_dir}}/* $SCRATCH_DIR/
cd $SCRATCH_DIR

# Run OpenFOAM
echo "Running simpleFoam on {{case}} case with {{cores}} cores"

# Decompose the case for parallel running
decomposePar -force

# Run the solver
mpirun -np {{cores}} simpleFoam -parallel

# Reconstruct the case
reconstructPar

# Copy results back
mkdir -p {{results_dir}}
cp -r $SCRATCH_DIR/{{time_steps}} {{results_dir}}/
cp -r $SCRATCH_DIR/log.* {{results_dir}}/
cp -r $SCRATCH_DIR/postProcessing {{results_dir}}/ 2>/dev/null || true

echo "Job completed at $(date)"
""",
                parameters={
                    "job_name": "simpleFoam_run",
                    "nodes": 1,
                    "cores_per_node": 16,
                    "cores": 16,
                    "wall_time": "24:00:00",
                    "memory": "32G",
                    "partition": "compute",
                    "openfoam_module": "openfoam/v2006",
                    "mpi_module": "openmpi/4.0.3",
                    "case_dir": "openfoam_case",
                    "case": "intake",
                    "time_steps": "0 system constant processor* [1-9]*",
                    "results_dir": "openfoam_results"
                }
            ),
            self.create_template(
                name="OpenFOAM PimpleFoam",
                description="OpenFOAM pimpleFoam solver for transient incompressible flows",
                category="OpenFOAM",
                scheduler="slurm",
                script_template="""#!/bin/bash
#SBATCH --job-name={{job_name}}
#SBATCH --output={{job_name}}-%j.out
#SBATCH --error={{job_name}}-%j.err
#SBATCH --nodes={{nodes}}
#SBATCH --ntasks-per-node={{cores_per_node}}
#SBATCH --time={{wall_time}}
#SBATCH --mem={{memory}}
#SBATCH --partition={{partition}}

echo "Starting OpenFOAM pimpleFoam job at $(date)"
echo "Running on $(hostname) with $(nproc) processors"

# Load required modules
module load {{openfoam_module}}
module load {{mpi_module}}

# Setup OpenFOAM environment
source $FOAM_ETC/bashrc

# Copy case files to scratch directory
SCRATCH_DIR="/scratch/$USER/$SLURM_JOB_ID"
mkdir -p $SCRATCH_DIR
cp -r {{case_dir}}/* $SCRATCH_DIR/
cd $SCRATCH_DIR

# Run OpenFOAM
echo "Running pimpleFoam on {{case}} case with {{cores}} cores"

# Decompose the case for parallel running
decomposePar -force

# Run the solver
mpirun -np {{cores}} pimpleFoam -parallel

# Reconstruct the case
reconstructPar

# Copy results back
mkdir -p {{results_dir}}
cp -r $SCRATCH_DIR/{{time_steps}} {{results_dir}}/
cp -r $SCRATCH_DIR/log.* {{results_dir}}/
cp -r $SCRATCH_DIR/postProcessing {{results_dir}}/ 2>/dev/null || true

echo "Job completed at $(date)"
""",
                parameters={
                    "job_name": "pimpleFoam_run",
                    "nodes": 1,
                    "cores_per_node": 16,
                    "cores": 16,
                    "wall_time": "48:00:00",
                    "memory": "64G",
                    "partition": "compute",
                    "openfoam_module": "openfoam/v2006",
                    "mpi_module": "openmpi/4.0.3",
                    "case_dir": "openfoam_case",
                    "case": "intake_transient",
                    "time_steps": "0 system constant processor* [0-9]*",
                    "results_dir": "openfoam_results"
                }
            ),
        ]
        
        # Create default DoE templates
        doe_templates = [
            self.create_template(
                name="DoE Parameter Study",
                description="Run multiple CFD cases with different parameters",
                category="DoE",
                scheduler="slurm",
                script_template="""#!/bin/bash
#SBATCH --job-name={{job_name}}
#SBATCH --output={{job_name}}-%j.out
#SBATCH --error={{job_name}}-%j.err
#SBATCH --nodes={{nodes}}
#SBATCH --ntasks-per-node={{cores_per_node}}
#SBATCH --time={{wall_time}}
#SBATCH --mem={{memory}}
#SBATCH --partition={{partition}}

echo "Starting DoE Parameter Study job at $(date)"
echo "Running on $(hostname)"

# Load required modules
module load {{openfoam_module}}
module load {{python_module}}
module load {{mpi_module}}

# Setup OpenFOAM environment
source $FOAM_ETC/bashrc

# Create working directory
SCRATCH_DIR="/scratch/$USER/$SLURM_JOB_ID"
mkdir -p $SCRATCH_DIR
cd $SCRATCH_DIR

# Copy DoE definition and template case
cp {{doe_definition}} $SCRATCH_DIR/doe_definition.json
cp -r {{template_case_dir}} $SCRATCH_DIR/template

# Run DoE script
python3 <<EOF
import os
import sys
import json
import shutil
import subprocess
import time
from pathlib import Path

print("Processing DoE study with Python")

# Load DoE definition
with open('doe_definition.json', 'r') as f:
    doe_data = json.load(f)

samples = doe_data.get('samples', [])
print(f"Found {len(samples)} design points to evaluate")

# Process each sample
template_dir = Path('template')
for i, sample in enumerate(samples):
    sample_id = i + 1
    print(f"\\nProcessing design point {sample_id}/{len(samples)}")
    print(f"Parameters: {sample}")
    
    # Create sample directory
    sample_dir = Path(f"sample_{sample_id}")
    shutil.copytree(template_dir, sample_dir)
    
    # Generate case files with parameters
    os.chdir(sample_dir)
    
    # Update case parameters (modify this for your specific case)
    # Example: Update velocity in U file
    if "inlet_velocity" in sample:
        u_file = Path("0/U")
        if u_file.exists():
            with open(u_file, 'r') as f:
                content = f.read()
            
            # Replace velocity value in U file
            import re
            new_content = re.sub(
                r'(inlet\s*\{[^}]*value\s*uniform\s*)\(\s*[0-9.-]+\s+[0-9.-]+\s+[0-9.-]+\s*\)',
                f'\\\\1({sample["inlet_velocity"]} 0 0)',
                content
            )
            
            with open(u_file, 'w') as f:
                f.write(new_content)
    
    # Run OpenFOAM for this sample
    print(f"Running OpenFOAM for sample {sample_id}")
    subprocess.run("decomposePar -force", shell=True)
    subprocess.run(f"mpirun -np {{{{cores_per_case}}}} {{{{solver}}}} -parallel", shell=True)
    subprocess.run("reconstructPar", shell=True)
    
    # Extract and save results
    print(f"Processing results for sample {sample_id}")
    os.makedirs("results", exist_ok=True)
    
    # Extract forces (modify based on your postprocessing)
    if Path("postProcessing/forceCoeffs").exists():
        latest_time = sorted(os.listdir("postProcessing/forceCoeffs"))[-1]
        shutil.copy(f"postProcessing/forceCoeffs/{latest_time}/coefficient.dat", "results/forces.dat")
    
    # Save parameters with results
    with open("results/parameters.json", 'w') as f:
        json.dump(sample, f, indent=2)
    
    # Return to main directory
    os.chdir(Path(".."))

print("\\nDoE study completed successfully")
EOF

# Copy results back to original directory
mkdir -p {{results_dir}}
cp -r $SCRATCH_DIR/sample_* {{results_dir}}/
cp $SCRATCH_DIR/{{job_name}}* {{results_dir}}/ 2>/dev/null || true

echo "DoE Parameter Study completed at $(date)"
""",
                parameters={
                    "job_name": "doe_study",
                    "nodes": 1,
                    "cores_per_node": 36,
                    "cores_per_case": 4,
                    "wall_time": "48:00:00",
                    "memory": "64G",
                    "partition": "compute",
                    "openfoam_module": "openfoam/v2006",
                    "python_module": "python/3.8",
                    "mpi_module": "openmpi/4.0.3",
                    "doe_definition": "doe_definition.json",
                    "template_case_dir": "template_case",
                    "solver": "simpleFoam",
                    "results_dir": "doe_results"
                }
            )
        ]
        
        # Create default post-processing templates
        postproc_templates = [
            self.create_template(
                name="ParaView Batch Post-Processing",
                description="Process CFD results with ParaView in batch mode",
                category="Post-Processing",
                scheduler="slurm",
                script_template="""#!/bin/bash
#SBATCH --job-name={{job_name}}
#SBATCH --output={{job_name}}-%j.out
#SBATCH --error={{job_name}}-%j.err
#SBATCH --nodes=1
#SBATCH --ntasks-per-node={{cores}}
#SBATCH --time={{wall_time}}
#SBATCH --mem={{memory}}
#SBATCH --partition={{partition}}

echo "Starting ParaView batch post-processing job at $(date)"
echo "Running on $(hostname)"

# Load required modules
module load {{paraview_module}}
module load {{python_module}}

# Copy data to scratch directory
SCRATCH_DIR="/scratch/$USER/$SLURM_JOB_ID"
mkdir -p $SCRATCH_DIR
cp -r {{case_dir}} $SCRATCH_DIR/case
cp {{script_file}} $SCRATCH_DIR/
cd $SCRATCH_DIR

# Run ParaView in batch mode
pvbatch --force-offscreen-rendering {{script_file}} {{script_args}}

# Copy results back
mkdir -p {{results_dir}}
cp -r $SCRATCH_DIR/{{output_pattern}} {{results_dir}}/

echo "Post-processing completed at $(date)"
""",
                parameters={
                    "job_name": "paraview_post",
                    "cores": 8,
                    "wall_time": "8:00:00",
                    "memory": "32G",
                    "partition": "compute", 
                    "paraview_module": "paraview/5.9.0",
                    "python_module": "python/3.8",
                    "case_dir": "openfoam_results",
                    "script_file": "process_results.py",
                    "script_args": "",
                    "output_pattern": "images/*.png",
                    "results_dir": "processed_results"
                }
            )
        ]
        
        # Save all templates
        for template in openfoam_templates + doe_templates + postproc_templates:
            if self.save_template(template):
                count += 1
                
        return count


# Example usage
if __name__ == "__main__":
    template_manager = JobTemplateManager()
    
    # Check if any templates exist
    if not template_manager.templates:
        print("No templates found. Creating default templates...")
        count = template_manager.create_default_templates()
        print(f"Created {count} default templates")
    else:
        print(f"Found {len(template_manager.templates)} existing templates")
        
    # List available templates
    print("\nAvailable templates:")
    for category in template_manager.categories:
        templates = template_manager.get_template_names(category)
        if templates:
            print(f"\n{category}:")
            for name in templates:
                print(f"  - {name}")
    
    # Generate a script from a template
    if template_manager.templates:
        template_name = next(iter(template_manager.templates))
        print(f"\nGenerating script from template '{template_name}'")
        success, script = template_manager.generate_script(template_name)
        if success:
            print("Script generated successfully!")
        else:
            print(f"Error: {script}")