# Locate CUDA installation
if(NOT DEFINED CUDA_TOOLKIT_ROOT_DIR)
    set(CUDA_TOOLKIT_ROOT_DIR "/opt/nvidia/hpc_sdk/Linux_x86_64/25.3/cuda/12.8")
endif()

find_path(CUDA_INCLUDE_DIR cuda.h
    HINTS ${CUDA_TOOLKIT_ROOT_DIR}
    PATH_SUFFIXES include
)

find_library(CUDA_CUDART_LIBRARY cudart
    HINTS ${CUDA_TOOLKIT_ROOT_DIR}
    PATH_SUFFIXES lib64 lib
)

include(FindPackageHandleStandardArgs)
find_package_handle_standard_args(CUDA
    REQUIRED_VARS
        CUDA_INCLUDE_DIR
        CUDA_CUDART_LIBRARY
)

if(CUDA_FOUND AND NOT TARGET CUDA::cudart)
    add_library(CUDA::cudart UNKNOWN IMPORTED)
    set_target_properties(CUDA::cudart PROPERTIES
        IMPORTED_LOCATION "${CUDA_CUDART_LIBRARY}"
        INTERFACE_INCLUDE_DIRECTORIES "${CUDA_INCLUDE_DIR}"
    )
endif()
