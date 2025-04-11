#!/bin/bash
set -e

# Ensure NVIDIA HPC SDK is in path
export PATH="/opt/nvidia/hpc_sdk/Linux_x86_64/23.7/compilers/bin:$PATH"
export LD_LIBRARY_PATH="/opt/nvidia/hpc_sdk/Linux_x86_64/23.7/compilers/lib:/usr/lib:/usr/local/lib:/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH"

# Remove incorrect Gmsh environment variables
unset GMSH_TERMINAL

# Set Gmsh environment variables
export GMSH_NO_GUI=1
export GMSH_WARNING_LEVEL=0

# Add debug flags
export GMSH_DEBUG=1
export OMP_DISPLAY_ENV=TRUE
export OMP_NUM_THREADS=4
export GMSH_PRINT_ERRORS=1

# NVIDIA HPC SDK compiler flags
NVC_FLAGS="-std=c++17 -gpu=cc75 -gpu=mem:managed -O3 -fast -g -Minfo=all -mp"

# Clean and prepare build directory
rm -rf build_main
mkdir -p build_main
cd build_main

# Configure the project with CMake
cmake -DCMAKE_BUILD_TYPE=Debug \
      -DCMAKE_C_COMPILER=nvc \
      -DCMAKE_CXX_COMPILER=nvc++ \
      -DCMAKE_EXPORT_COMPILE_COMMANDS=ON \
      ..

# Build the main program with NVIDIA HPC compiler
make gmsh_processor -j$(nproc)

echo "Build complete. Run with:"
echo "./gmsh_processor"

# Print debug info
echo -e "\nBuilt with NVIDIA HPC compiler and OpenMP support. To debug:"
echo "gdb ./gmsh_processor"
