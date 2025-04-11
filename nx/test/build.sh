#!/bin/bash

# Exit on error
set -e

# Ensure we're in the script's directory
cd "$(dirname "$0")"

# Clean previous build
rm -rf build
mkdir build
cd build

# Ensure system paths are used
export PATH="/usr/bin:/usr/local/bin:$PATH"
export LD_LIBRARY_PATH="/usr/lib:/usr/local/lib:/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH"

# Configure and build
cmake ..
make -j$(nproc)

# Run tests if build succeeds
echo "Build successful! Running tests..."
cd bin
for test in test_*; do
    if [ -x "$test" ]; then
        echo "Running $test..."
        ./"$test"
        echo "----------------------------------------"
    fi
done
