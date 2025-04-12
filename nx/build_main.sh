#!/bin/bash
set -e  # Exit on error

# Ensure NVIDIA HPC SDK is in path
export PATH="/opt/nvidia/hpc_sdk/Linux_x86_64/23.7/compilers/bin:$PATH"
export LD_LIBRARY_PATH="/opt/nvidia/hpc_sdk/Linux_x86_64/23.7/compilers/lib:/usr/lib:/usr/local/lib:/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH"

# Remove incorrect Gmsh environment variables
unset GMSH_TERMINAL

# Set Gmsh environment variables for better performance
export GMSH_NO_GUI=1
export GMSH_WARNING_LEVEL=1  # Show more warnings
export GMSH_VERBOSITY=5      # Increase verbosity 

# Determine number of threads safely
if command -v nproc &> /dev/null; then
    NUM_THREADS=$(nproc)
else
    NUM_THREADS=4  # Default if nproc not available
fi

# Set OpenMP variables for better performance with boundary layers
export OMP_PROC_BIND=close
export OMP_PLACES=cores
export OMP_SCHEDULE=dynamic,16
export OMP_NUM_THREADS=$NUM_THREADS
export OMP_STACKSIZE=128M    # Increase stack size for better recursion handling

# Add debug flags if needed (comment out for production runs)
#export GMSH_DEBUG=1
#export OMP_DISPLAY_ENV=TRUE
#export GMSH_PRINT_ERRORS=1

# NVIDIA HPC SDK compiler flags
NVC_FLAGS="-std=c++17 -gpu=cc75 -gpu=mem:managed -O3 -fast -g -Minfo=all -mp"

# Create build directory if it doesn't exist
mkdir -p build_main

# Configure and build
cd build_main
cmake ..
make -j$NUM_THREADS

# Copy the executable to the main directory for convenience
cp mesh_generator ..

echo "Build completed. Run ./mesh_generator <input_step_file> <output_msh_file> [options]"
echo "Try these options for faster boundary layers:"
echo "  --bl_first_layer 0.02 --bl_progression 1.3 --bl_num_layers 5 --bl_intersect_method 1"
echo "  --bl_angle_tolerance 45 --bl_smooth_normals 1"
echo ""
echo "For difficult geometry with non-closed loops, try:"
echo "  --alg_2d 3 --base_mesh_size 1.0"
