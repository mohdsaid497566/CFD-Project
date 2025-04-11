#!/bin/bash

# Exit on error
set -e

# Setup environment
export CUDA_HOME=/opt/nvidia/hpc_sdk/Linux_x86_64/25.3/cuda/12.8
export PATH=$CUDA_HOME/bin:$PATH
export LD_LIBRARY_PATH=$CUDA_HOME/lib64:/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH

# Ensure proper compiler setup
export CC=/usr/bin/gcc
export CXX=/usr/bin/g++
export CUDACXX=$CUDA_HOME/bin/nvcc
export CUDAHOSTCXX=/usr/bin/g++

# Build directory setup
rm -rf build
mkdir -p build
cd build

# Configure and build
cmake -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=ON ..
make -j$(nproc)

# Run tests
echo "Running tests..."
ctest --output-on-failure -V

# Show test summary
echo "Test Summary:"
ctest -N
