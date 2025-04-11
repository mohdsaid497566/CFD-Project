# Find NVIDIA HPC SDK
find_program(CMAKE_NVIDIA_COMPILER NAMES nvc++ PATHS
    /opt/nvidia/hpc_sdk/Linux_x86_64/23.7/compilers/bin
    /usr/local/nvidia/hpc_sdk/Linux_x86_64/23.7/compilers/bin
    ENV PATH
)

if(CMAKE_NVIDIA_COMPILER)
    set(NVHPC_ROOT_DIR "${CMAKE_NVIDIA_COMPILER}/../../.." CACHE PATH "NVIDIA HPC SDK root directory")
    set(NVHPC_FOUND TRUE)
endif()
