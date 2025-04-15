#!/bin/bash

# Check for input file
if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <input_file.stp> [output_file.msh]"
    exit 1
fi

# Use absolute paths to avoid issues with WSL
INPUT_FILE=$(realpath "$1")
OUTPUT_FILE="${2:-${INPUT_FILE%.*}.msh}"
OUTPUT_FILE=$(realpath "$OUTPUT_FILE")
MESH_SIZE=1.0

# Detect number of CPU cores
if command -v nproc &> /dev/null; then
    NUM_THREADS=$(nproc)
else
    NUM_THREADS=4
fi

# Set OpenMP environment variables for better performance
export OMP_NUM_THREADS=$NUM_THREADS
export OMP_SCHEDULE="dynamic,1000"
export OMP_PROC_BIND=close
export OMP_PLACES=cores

# GPU environment variables for CUDA and OpenGL
export __GL_THREADED_OPTIMIZATIONS=1
export __GL_SYNC_TO_VBLANK=0
export CUDA_CACHE_MAXSIZE=2147483648  # 2GB cache
export CUDA_CACHE_DISABLE=0
export CUDA_DEVICE_ORDER=PCI_BUS_ID
export CUDA_VISIBLE_DEVICES=0  # Use first GPU

echo "=== ACCELERATED INTAKE MESH WORKFLOW ==="
echo "Input: $INPUT_FILE"
echo "Output: $OUTPUT_FILE"
echo "Using $NUM_THREADS CPU threads and GPU acceleration"

# Check for required Python packages
if ! pip list | grep -q cupy || ! pip list | grep -q pycuda; then
    echo "Installing required Python GPU packages..."
    pip install --user cupy-cuda102 pycuda mpi4py
fi

# Step 1: Try GPU accelerated direct meshing
echo "Step 1: GPU accelerated meshing with Python API..."
./python_mesher.py "$INPUT_FILE" "$OUTPUT_FILE" --size $MESH_SIZE --alg2d 6 --alg3d 4 --gpu --threads $NUM_THREADS

# Check if successful
if [ $? -eq 0 ] && [ -f "$OUTPUT_FILE" ]; then
    echo "Mesh created successfully with GPU acceleration!"
    exit 0
fi

# Step 2: Try external Gmsh with GPU acceleration
echo "Step 2: Trying external Gmsh with GPU acceleration..."
./python_mesher.py "$INPUT_FILE" "$OUTPUT_FILE" --size $MESH_SIZE --external --gpu

# Check if successful
if [ $? -eq 0 ] && [ -f "$OUTPUT_FILE" ]; then
    echo "Mesh created successfully using external Gmsh with GPU!"
    exit 0
fi

# Step 3: Try STL conversion approach (often more GPU friendly)
echo "Step 3: Trying STL conversion approach with GPU acceleration..."
./python_mesher.py "$INPUT_FILE" "$OUTPUT_FILE" --size $MESH_SIZE --stl --gpu

# Check if successful
if [ $? -eq 0 ] && [ -f "$OUTPUT_FILE" ]; then
    echo "Mesh created successfully using GPU-accelerated STL approach!"
    exit 0
fi

# Step 4: Fall back to CPU-only meshing with robust options
echo "Step 4: Falling back to CPU-only meshing with simple_mesh.sh..."
./simple_mesh.sh "$INPUT_FILE" "$OUTPUT_FILE"

# Check if successful
if [ $? -eq 0 ] && [ -f "$OUTPUT_FILE" ]; then
    echo "Mesh created successfully using simple_mesh.sh!"
    exit 0
fi

echo "All meshing attempts failed. Check the input file or try with different parameters."
exit 1
