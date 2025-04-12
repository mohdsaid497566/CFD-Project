#!/bin/bash

echo "===== CUDA and Compiler Environment Diagnostic ====="
echo

echo "== System Information =="
uname -a
echo

echo "== WSL Information =="
if [ -f /proc/version ]; then
    grep -i "microsoft" /proc/version && echo "Running in WSL"
fi
echo

echo "== C/C++ Compiler Information =="
echo "gcc path: $(which gcc 2>/dev/null || echo 'Not found')"
echo "gcc version: $(gcc --version 2>/dev/null || echo 'Not available')"
echo
echo "g++ path: $(which g++ 2>/dev/null || echo 'Not found')"
echo "g++ version: $(g++ --version 2>/dev/null || echo 'Not available')"
echo

echo "== NVIDIA HPC SDK Information =="
NVIDIA_HPC_SDK="/opt/nvidia/hpc_sdk/Linux_x86_64/25.3"
if [ -d "$NVIDIA_HPC_SDK" ]; then
    echo "HPC SDK found at $NVIDIA_HPC_SDK"
    ls -la $NVIDIA_HPC_SDK
    echo
    echo "NVIDIA compilers:"
    find $NVIDIA_HPC_SDK -name "nvc++" -o -name "nvcc" | sort
    echo
else
    echo "NVIDIA HPC SDK not found at $NVIDIA_HPC_SDK"
fi
echo

echo "== CUDA Information =="
echo "nvcc path: $(which nvcc 2>/dev/null || echo 'Not found')"
if which nvcc &>/dev/null; then
    echo "nvcc version:"
    nvcc --version
fi
echo

echo "== CUDA Toolkit Locations =="
for loc in "/usr/local/cuda" "/usr/cuda" "$NVIDIA_HPC_SDK/cuda"; do
    if [ -d "$loc" ]; then
        echo "CUDA found at: $loc"
        ls -la $loc/bin 2>/dev/null || echo "No bin directory"
        echo "Include directory:"
        ls -la $loc/include 2>/dev/null | grep -E 'cuda|cu$' || echo "No CUDA headers found"
    fi
done
echo

echo "== Checking for cc1plus =="
CC1PLUS_PATHS=$(find /usr -name cc1plus 2>/dev/null)
if [ -z "$CC1PLUS_PATHS" ]; then
    echo "cc1plus not found - this will prevent CUDA compilation"
else
    echo "cc1plus found at:"
    echo "$CC1PLUS_PATHS"
fi
echo

echo "== Installed Packages =="
dpkg -l | grep -E 'cuda|nvidia|gcc|g\+\+|build-essential'
echo

echo "======= Diagnostic Complete ======="

# Make this info available for later reference
cp "$0.log" "cuda_diagnostic_$(date +%F_%H-%M-%S).log"
