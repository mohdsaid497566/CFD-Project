#!/bin/bash
# filepath: /mnt/c/Users/Mohammed/Desktop/Intake-CFD-Project/nx/setup_environment.sh

# This script sets up the Python environment for Intake CFD Optimization Suite

echo "Setting up environment for Intake CFD Optimization Suite"
echo "========================================================"

# Detect environment
IS_WSL=false
if grep -q Microsoft /proc/version || grep -q microsoft /proc/version; then
    echo "WSL environment detected"
    IS_WSL=true
fi

# Create a virtual environment if it doesn't exist
if [ ! -d "./venv" ]; then
    echo "Creating Python virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Update pip and setuptools
echo "Updating pip and setuptools..."
pip install --upgrade pip setuptools wheel

# Install core dependencies first
echo "Installing core Python packages..."
pip install numpy pandas matplotlib scipy openmdao

# Install GUI-related packages
echo "Installing GUI and visualization packages..."
pip install pillow tk

# Install specialized viz packages, handling errors gracefully
echo "Installing visualization packages..."
pip install vtk pyvista --no-dependencies || echo "Warning: Some visualization packages failed to install"

# Install additional dependencies
echo "Installing additional packages..."
pip install scikit-learn plotly tqdm

# Install all requirements (as a fallback)
echo "Installing remaining dependencies from requirements.txt..."
pip install -r requirements.txt || echo "Some packages from requirements.txt could not be installed"

# For WSL users, provide system dependencies instructions
if [ "$IS_WSL" = true ]; then
    echo -e "\n=============================================\n"
    echo "WSL environment detected. You may need to install these system dependencies:"
    echo "sudo apt-get update"
    echo "sudo apt-get install -y python3-tk libxft-dev libffi-dev"
    echo "sudo apt-get install -y libgl1-mesa-dev xvfb"
    echo -e "\n=============================================\n"
fi

# Create mock executables for demo mode if they don't exist
if [ ! -f "./gmsh_process" ]; then
    echo "Creating mock executables for demonstration mode..."
    
    echo "#!/bin/bash
echo 'Mock gmsh_process running...'
echo 'Processing \$2 to \$4'
echo 'Created mock mesh file'
touch \$4" > ./gmsh_process
    
    echo "#!/bin/bash
echo 'Mock CFD solver running...'
echo 'Processing \$2'
echo 'Created mock result files'
mkdir -p cfd_results
echo '0.123' > cfd_results/pressure.dat" > ./cfd_solver
    
    echo "#!/bin/bash
echo 'Mock results processor running...'
echo 'Processing results from \$2 to \$4'
echo '0.123' > \$4" > ./process_results
    
    chmod +x ./gmsh_process ./cfd_solver ./process_results
    
    echo "Mock executables created successfully."
fi

echo -e "\n=============================================\n"
echo "Environment setup complete!"
echo "To activate this environment in the future, run:"
echo "source venv/bin/activate"
echo -e "\n"
echo "To run the application:"
echo "python MDO.py"
echo -e "\n=============================================\n"