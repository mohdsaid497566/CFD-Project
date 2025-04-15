#!/bin/bash
set -e

# Install dependencies
sudo apt-get update
sudo apt-get install -y \
    libocct-dev \
    libglu1-mesa-dev \
    libxft-dev \
    libxcursor-dev \
    libxinerama-dev

# Clone and build GMSH
cd /tmp
git clone https://gitlab.onelab.info/gmsh/gmsh.git
cd gmsh
mkdir build && cd build

# Configure with required options
cmake .. \
    -DENABLE_OPENMP=ON \
    -DENABLE_OPENCASCADE=ON \
    -DENABLE_BUILD_SHARED=ON \
    -DENABLE_BUILD_LIB=ON

# Build and install
make -j$(nproc)
sudo make install
sudo ldconfig
