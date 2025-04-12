#!/bin/bash

echo "Installing GPU acceleration dependencies for meshing..."

# Check if running in WSL
if grep -q Microsoft /proc/version; then
    echo "Running in Windows Subsystem for Linux (WSL)"
    CUDA_PACKAGE="cuda-11-7"
else
    echo "Running in native Linux"
    CUDA_PACKAGE="cuda"
fi

# Check for CUDA toolkit
if ! command -v nvcc &> /dev/null; then
    echo "CUDA toolkit not found. Installing CUDA..."
    
    # Add NVIDIA repository (Ubuntu-focused)
    if [ -f /etc/apt/sources.list.d/cuda.list ]; then
        sudo rm /etc/apt/sources.list.d/cuda.list
    fi
    
    # Use distro detection
    if [ -f /etc/lsb-release ]; then
        source /etc/lsb-release
        if [ "$DISTRIB_ID" = "Ubuntu" ]; then
            # Add CUDA repository for Ubuntu
            wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/cuda-ubuntu2004.pin
            sudo mv cuda-ubuntu2004.pin /etc/apt/preferences.d/cuda-repository-pin-600
            sudo apt-key adv --fetch-keys https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/3bf863cc.pub
            sudo add-apt-repository "deb https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/ /"
            sudo apt-get update
            sudo apt-get install -y $CUDA_PACKAGE
        else
            echo "Unsupported Linux distribution. Please install CUDA manually."
        fi
    else
        echo "Unable to detect Linux distribution. Please install CUDA manually."
    fi
fi

# Install python dependencies for GPU acceleration
echo "Installing Python GPU libraries..."
pip install --user cupy-cuda11x pycuda mpi4py

# Install MPI for parallel processing
echo "Installing MPI libraries..."
sudo apt-get update
sudo apt-get install -y libopenmpi-dev openmpi-bin

echo "Setting up environment variables..."
# Create environment setup script
cat > gpu_env_setup.sh << 'EOL'
#!/bin/bash

# CUDA environment setup
export PATH="/usr/local/cuda/bin:$PATH"
export LD_LIBRARY_PATH="/usr/local/cuda/lib64:$LD_LIBRARY_PATH"
export CUDA_HOME=/usr/local/cuda

# OpenMP settings for hybrid CPU/GPU computing
export OMP_NUM_THREADS=$(nproc)
export OMP_SCHEDULE="dynamic,1000"
export OMP_PROC_BIND=close
export OMP_PLACES=cores

# NVIDIA settings
export __GL_THREADED_OPTIMIZATIONS=1
export __GL_SYNC_TO_VBLANK=0
export CUDA_CACHE_MAXSIZE=2147483648  # 2GB cache
export CUDA_DEVICE_ORDER=PCI_BUS_ID

# Display configuration
echo "GPU acceleration environment configured:"
echo "  - CUDA_HOME: $CUDA_HOME"
echo "  - CPU threads: $OMP_NUM_THREADS"

# Check GPU device
if command -v nvidia-smi &> /dev/null; then
    echo "GPU information:"
    nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv
else
    echo "Warning: nvidia-smi not found. Is the NVIDIA driver installed?"
fi
EOL

chmod +x gpu_env_setup.sh

echo "Installation complete. Run 'source ./gpu_env_setup.sh' to set up the environment before meshing."
echo "Then use './mesh_intake.sh' with your STEP file to create an accelerated mesh."
