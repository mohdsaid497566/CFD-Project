#!/bin/bash

# Exit on error
set -e

# Create build directory if it doesn't exist
mkdir -p gmsh/build
cd gmsh/build

# NVIDIA HPC SDK base directory
NVIDIA_HPC_SDK="/opt/nvidia/hpc_sdk/Linux_x86_64/25.3"

# The problem is with gcc/g++ paths - nvcc needs to use the system g++, not miniconda's gcc
# First ensure PATH has system binaries before miniconda
export PATH="/usr/bin:${PATH}"

# Use system g++ compiler (not miniconda's) that has cc1plus available
export CUDAHOSTCXX="/usr/bin/g++"

# Set CUDA toolkit paths
export CUDA_HOME="/usr/local/cuda"  # Use the system CUDA installation that the diagnostics found
export CUDA_TOOLKIT_ROOT_DIR="/usr/local/cuda"
export PATH="${CUDA_HOME}/bin:${PATH}"

# Print compiler paths being used
echo "Using g++ compiler: $(which g++)"
echo "g++ version: $(g++ --version | head -n1)"
echo "cc1plus path: $(find /usr/libexec /usr/lib -name cc1plus | head -n1)"
echo "Using nvcc: $(which nvcc)"
echo "nvcc version: $(nvcc --version | grep "release")"

# Run CMake with specific compiler settings
cmake -DENABLE_MPI=ON \
      -DENABLE_OPENMP=ON \
      -DENABLE_CUDA=ON \
      -DCUDA_TOOLKIT_ROOT_DIR="${CUDA_TOOLKIT_ROOT_DIR}" \
      -DCMAKE_CUDA_COMPILER="${CUDA_HOME}/bin/nvcc" \
      -DCMAKE_CUDA_HOST_COMPILER="${CUDAHOSTCXX}" \
      -DCMAKE_CXX_COMPILER="/usr/bin/g++" \
      -DCMAKE_C_COMPILER="/usr/bin/gcc" \
      -DCUDA_HOST_COMPILER="${CUDAHOSTCXX}" \
      -DCMAKE_BUILD_TYPE=Release \
      ..

# Print success message
echo "Configuration completed successfully. Run 'make' to build."
