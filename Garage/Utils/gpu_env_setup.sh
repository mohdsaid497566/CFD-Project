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
