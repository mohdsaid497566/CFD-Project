#!/bin/bash
set -e

# Install OpenCASCADE and dependencies
sudo apt-get update
sudo apt-get install -y \
    libocct-foundation-dev \
    libocct-modeling-algorithms-dev \
    libocct-ocaf-dev \
    libocct-data-exchange-dev \
    libglu1-mesa-dev \
    libx11-dev \
    build-essential \
    cmake \
    git

# Rebuild GMSH with OpenCASCADE
cd /tmp
rm -rf gmsh
git clone https://gitlab.onelab.info/gmsh/gmsh.git
cd gmsh
mkdir build && cd build

# Configure with explicit OpenCASCADE paths
cmake .. \
    -DENABLE_OPENMP=ON \
    -DENABLE_OCC=ON \
    -DENABLE_OPENCASCADE=ON \
    -DENABLE_BUILD_SHARED=ON \
    -DCMAKE_BUILD_TYPE=Release \
    -DOPENCASCADE_ROOT=/usr \
    -DOPENCASCADE_INCLUDE_DIR=/usr/include/opencascade

make -j$(nproc)
sudo make install
sudo ldconfig

# Verify OpenCASCADE support
echo "Verifying GMSH OpenCASCADE support..."
if ! ldd /usr/local/lib/libgmsh.so | grep -q "libTK"; then
    echo "Error: GMSH was not linked against OpenCASCADE"
    exit 1
fi
