#!/bin/bash

# Create a simple CUDA test file
cat > test.cu << 'EOF'
#include <stdio.h>

__global__ void cuda_hello(){
    printf("Hello from CUDA!\n");
}

int main() {
    cuda_hello<<<1,1>>>();
    cudaDeviceSynchronize();
    return 0;
}
EOF

# Set up NVIDIA HPC SDK environment
NVIDIA_HPC_SDK="/opt/nvidia/hpc_sdk/Linux_x86_64/25.3"
export PATH="${NVIDIA_HPC_SDK}/cuda/bin:${NVIDIA_HPC_SDK}/compilers/bin:$PATH"

# Check if g++ is properly installed
echo "Checking C++ compiler installation..."
if ! dpkg -l | grep -q "g\+\+" || ! dpkg -l | grep -q "build-essential"; then
    echo "Installing build-essential package (includes g++)..."
    sudo apt update && sudo apt install -y build-essential
fi

# Verify g++ installation
G_PLUS_PLUS_PATH=$(which g++)
echo "G++ path: $G_PLUS_PLUS_PATH"
echo "G++ version:"
g++ --version

# Check for cc1plus
CC1PLUS_PATH=$(find /usr -name cc1plus 2>/dev/null | head -n 1)
if [ -z "$CC1PLUS_PATH" ]; then
    echo "Warning: cc1plus not found. This may cause nvcc compilation errors."
else
    echo "Found cc1plus at: $CC1PLUS_PATH"
    # Add the directory containing cc1plus to PATH
    CC1PLUS_DIR=$(dirname "$CC1PLUS_PATH")
    export PATH="$CC1PLUS_DIR:$PATH"
fi

# Try to use the HPC SDK's own C++ compiler if available
if [ -f "${NVIDIA_HPC_SDK}/compilers/bin/nvc++" ]; then
    echo "Found NVIDIA C++ compiler, using it as host compiler"
    export CUDAHOSTCXX="${NVIDIA_HPC_SDK}/compilers/bin/nvc++"
else
    export CUDAHOSTCXX="$G_PLUS_PLUS_PATH"
fi

echo "Using host C++ compiler: $CUDAHOSTCXX"

# Try to compile with explicit host compiler specification
echo "Compiling CUDA test program with explicit host compiler..."
nvcc -ccbin="$CUDAHOSTCXX" test.cu -o test_cuda

if [ $? -eq 0 ]; then
    echo "CUDA compilation successful!"
    echo "Running the program:"
    ./test_cuda
else
    echo "CUDA compilation failed."
    
    # Try installing nvidia-cuda-toolkit as a fallback
    echo "Installing NVIDIA CUDA toolkit from Ubuntu repositories..."
    sudo apt update && sudo apt install -y nvidia-cuda-toolkit
    
    echo "Trying compilation with system CUDA toolkit..."
    /usr/bin/nvcc -ccbin="$CUDAHOSTCXX" test.cu -o test_cuda
    
    if [ $? -eq 0 ]; then
        echo "CUDA compilation with system toolkit successful!"
        echo "Running the program:"
        ./test_cuda
    else
        echo "CUDA compilation with system toolkit also failed."
        echo "Displaying diagnostic information:"
        echo "Path: $PATH"
        echo "CUDA_HOME: $CUDA_HOME"
        echo "nvcc version:"
        nvcc --version || echo "nvcc not found in PATH"
        echo "CUDAHOSTCXX: $CUDAHOSTCXX"
        echo "GCC/G++ installation:"
        dpkg -l | grep -E 'gcc|g\+\+' || echo "GCC/G++ not found in package list"
    fi
fi

# Keep the test file for inspection
echo "Test file 'test.cu' has been kept for inspection."
