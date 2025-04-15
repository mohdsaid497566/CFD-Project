#!/bin/bash
# filepath: /mnt/c/Users/Mohammed/Desktop/Intake-CFD-Project/nx/make_scripts_executable.sh

# Make all required scripts executable
chmod +x ./mesh_validator.py
chmod +x ./mesh_refiner.py
chmod +x ./bc_manager.py
chmod +x ./benchmark_tests.py
chmod +x ./gmsh_process
chmod +x ./mesh_generator
chmod +x ./run_tests.sh

echo "All scripts are now executable."
