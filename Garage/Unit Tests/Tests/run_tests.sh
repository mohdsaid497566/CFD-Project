#!/bin/bash
set -e

# Clean conda environment
unset CONDA_PREFIX
unset CONDA_PYTHON_EXE
export PATH=/usr/local/bin:/usr/bin:$PATH

# Install dependencies once
echo "=== Installing Dependencies ==="
sudo apt-get update
sudo apt-get install -y \
    libomp-dev \
    libocct-dev \
    libglu1-mesa-dev \
    build-essential \
    cmake

# Fix library paths
sudo ln -sf /usr/lib/x86_64-linux-gnu/libgomp.so.1 /usr/lib/x86_64-linux-gnu/libgomp.so
export LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu:/usr/local/lib:$LD_LIBRARY_PATH
sudo ldconfig

# Configure compiler flags
export CC=/usr/bin/gcc
export CXX=/usr/bin/g++
export CUDACXX=/opt/nvidia/hpc_sdk/Linux_x86_64/25.3/cuda/12.8/bin/nvcc
export LDFLAGS="-L/usr/lib/x86_64-linux-gnu"

# Build GMSH
echo "=== Building GMSH with OpenCASCADE support ==="
cd /tmp
rm -rf gmsh
git clone https://gitlab.onelab.info/gmsh/gmsh.git
cd gmsh
mkdir -p build && cd build

# Configure with explicit OpenMP flags
cmake .. \
    -DENABLE_OPENMP=ON \
    -DENABLE_OPENCASCADE=ON \
    -DCMAKE_C_FLAGS="${CFLAGS}" \
    -DCMAKE_CXX_FLAGS="${CXXFLAGS}" \
    -DCMAKE_EXE_LINKER_FLAGS="${LDFLAGS}"

make -j$(nproc)
sudo make install
sudo ldconfig

echo "=== Building and Testing Project ==="
# Return to project directory
cd /mnt/c/users/mohammed/Desktop/nx

# Clean and create build directory
rm -rf build
mkdir -p build && cd build

# Configure and build project
echo "Configuring project..."
cmake -DBUILD_TESTING=ON ..

echo "Building project..."
make -j$(nproc)

# Run tests with detailed output
echo "=== Running Tests ==="
echo "Discovered tests:"
ctest -N

echo "Executing tests..."
ctest --output-on-failure -V

# Check results
failed_tests=$(ctest --output-on-failure -N -F | grep -c "Failed" || true)
if [ "$failed_tests" -gt 0 ]; then
    echo "ERROR: $failed_tests tests failed!"
    exit 1
else
    echo "SUCCESS: All tests passed!"
    exit 0
fi
