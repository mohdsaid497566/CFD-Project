#!/bin/bash#!/bin/bash

























echo "lldb ./gmsh_processor"echo "Build complete. To debug run:"make gmsh_processor -j$(nproc)# Build main program      ..      -DCMAKE_EXE_LINKER_FLAGS="${LDFLAGS}" \      -DCMAKE_CXX_FLAGS_DEBUG="${CXXFLAGS}" \      -DCMAKE_EXPORT_COMPILE_COMMANDS=ON \      -DBUILD_TESTING=OFF \cmake -DCMAKE_BUILD_TYPE=Debug \# Configure with debug optionscd buildmkdir -p build# Build directory setupsource /opt/intel/oneapi/setvars.sh# Setup environmentsudo apt-get update && sudo apt-get install -y lldb# Install LLDB debuggerset -eset -e

# Install LLDB debugger
sudo apt-get update && sudo apt-get install -y lldb

# Setup environment
export CUDA_HOME=/opt/nvidia/hpc_sdk/Linux_x86_64/25.3/cuda/12.8
export PATH=$CUDA_HOME/bin:$PATH
export LD_LIBRARY_PATH=/usr/local/lib:/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH

# Compiler setup with enhanced debug flags
export CC=/usr/bin/gcc
export CXX=/usr/bin/g++
export CFLAGS="-g3 -O0 -Wall -Wextra -fno-omit-frame-pointer -fsanitize=address"
export CXXFLAGS="-g3 -O0 -Wall -Wextra -fno-omit-frame-pointer -fsanitize=address"
export LDFLAGS="-fsanitize=address"

# Build directory setup
rm -rf build_main
mkdir -p build_main
cd build_main

# Configure with debug options
cmake -DCMAKE_BUILD_TYPE=Debug \
      -DBUILD_TESTING=OFF \
      -DCMAKE_EXPORT_COMPILE_COMMANDS=ON \
      -DCMAKE_CXX_FLAGS_DEBUG="${CXXFLAGS}" \
      -DCMAKE_EXE_LINKER_FLAGS="${LDFLAGS}" \
      ..

# Build main program
make gmsh_processor -j$(nproc)

echo "Build complete. To debug run:"
echo "lldb ./gmsh_processor"
#!/bin/bash
set -e

# Setup environment
export CUDA_HOME=/opt/nvidia/hpc_sdk/Linux_x86_64/25.3/cuda/12.8
export PATH=$CUDA_HOME/bin:$PATH
export LD_LIBRARY_PATH=/usr/local/lib:/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH

# Compiler setup with debug flags
export CC=/usr/bin/gcc
export CXX=/usr/bin/g++
export CFLAGS="-g3 -O0 -Wall -Wextra -fno-omit-frame-pointer"
export CXXFLAGS="-g3 -O0 -Wall -Wextra -fno-omit-frame-pointer"

# Build directory setup
rm -rf build_main
mkdir -p build_main
cd build_main

# Configure and build main program only
cmake -DCMAKE_BUILD_TYPE=Debug \
      -DBUILD_TESTING=OFF \
      -DCMAKE_EXPORT_COMPILE_COMMANDS=ON \
      ..

# Build only the main program
make gmsh_processor -j$(nproc)

echo "Build complete. Run with:"
echo "./gmsh_processor"

# Print debug info
echo -e "\nBuilt with debug symbols. To debug:"
echo "gdb ./gmsh_processor"
