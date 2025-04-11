#!/bin/bash

# Install required compilers
sudo apt-get update
sudo apt-get install -y gcc g++ build-essential

# Set up CUDA environment
export PATH=/opt/nvidia/hpc_sdk/Linux_x86_64/25.3/cuda/12.8/bin:$PATH
export LD_LIBRARY_PATH=/opt/nvidia/hpc_sdk/Linux_x86_64/25.3/cuda/12.8/lib64:$LD_LIBRARY_PATH

# Ensure system compiler is used
export CC=/usr/bin/gcc
export CXX=/usr/bin/g++
export CUDACXX=/opt/nvidia/hpc_sdk/Linux_x86_64/25.3/cuda/12.8/bin/nvcc
export CUDAHOSTCXX=/usr/bin/g++
