#!/bin/bash
set -e

# Temporarily deactivate conda
CONDA_PREFIX_BACKUP=$CONDA_PREFIX
source deactivate 2>/dev/null || true

# Set system paths first
export PATH="/usr/bin:/usr/local/bin:$PATH"
export LD_LIBRARY_PATH="/usr/lib:/usr/local/lib:/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH"

# Clean and create build directory
rm -rf build
mkdir -p build
cd build

# Configure with system cmake
/usr/bin/cmake ..

# Build
make -j$(nproc)

# Restore conda environment
export CONDA_PREFIX=$CONDA_PREFIX_BACKUP
