cmake_minimum_required(VERSION 3.18)

# CUDA Configuration
set(CMAKE_CUDA_COMPILER "/opt/nvidia/hpc_sdk/Linux_x86_64/25.3/cuda/12.8/bin/nvcc")
set(CMAKE_CUDA_ARCHITECTURES 75)
set(CMAKE_CUDA_FLAGS "${CMAKE_CUDA_FLAGS} -std=c++17")

project(gmsh_nx_tests LANGUAGES CXX CUDA)

# Add path to custom find modules and includes
list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/../cmake")
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/../include)

# Find required packages
find_package(OpenMP REQUIRED)
find_package(GMSH REQUIRED)

# Enable testing and set directory
include(CTest)
enable_testing()
set(TEST_OUTPUT_DIR "${CMAKE_BINARY_DIR}/bin")
file(MAKE_DIRECTORY ${TEST_OUTPUT_DIR})

# Define test targets
set(TEST_TARGETS
    test_initialize
    test_logger
    test_model
    test_geometry
    test_mesh
    test_complex_mesh
    test_operations
    test_refinement
)

# Create test executables with common settings
foreach(target ${TEST_TARGETS})
    add_executable(${target} ${target}.cpp)
    target_link_libraries(${target} 
        PRIVATE 
            ${GMSH_LIBRARIES}
            gmsh_nx 
            OpenMP::OpenMP_CXX
    )
    target_include_directories(${target} 
        PRIVATE 
            ${GMSH_INCLUDE_DIRS}
            ${CMAKE_SOURCE_DIR}/include
    )
    set_target_properties(${target} PROPERTIES
        RUNTIME_OUTPUT_DIRECTORY "${TEST_OUTPUT_DIR}"
    )
    add_test(NAME ${target} 
             COMMAND ${target}
             WORKING_DIRECTORY "${TEST_OUTPUT_DIR}")
endforeach()

# OpenMP test configuration
add_executable(test_openmp test_openmp.cpp)
target_link_libraries(test_openmp 
    PRIVATE 
        ${GMSH_LIBRARIES}
        gmsh_nx
        OpenMP::OpenMP_CXX
)

add_test(
    NAME test_openmp
    COMMAND test_openmp
    WORKING_DIRECTORY ${TEST_OUTPUT_DIR}
)

# CUDA test configuration
add_executable(test_parallel test_parallel.cpp test_parallel.cu)

set_target_properties(test_parallel PROPERTIES
    CUDA_SEPARABLE_COMPILATION ON
    POSITION_INDEPENDENT_CODE ON
    RUNTIME_OUTPUT_DIRECTORY ${TEST_OUTPUT_DIR}
)

set(CUDA_TOOLKIT_ROOT "/opt/nvidia/hpc_sdk/Linux_x86_64/25.3/cuda/12.8")

target_compile_options(test_parallel PRIVATE
    $<$<COMPILE_LANGUAGE:CUDA>:
        --generate-code=arch=compute_75,code=sm_75
        -Xcompiler=-fPIC
        -Xcompiler=-fopenmp
        --extended-lambda
        --default-stream=per-thread
        --expt-relaxed-constexpr
    >
)

target_link_directories(test_parallel PRIVATE
    ${CUDA_TOOLKIT_ROOT}/lib64
    /usr/lib/x86_64-linux-gnu
)

target_link_libraries(test_parallel 
    PRIVATE 
        gmsh_nx
        OpenMP::OpenMP_CXX
        cudart
        cuda
)

target_include_directories(test_parallel PRIVATE 
    ${GMSH_INCLUDE_DIRS}
    ${CMAKE_CUDA_TOOLKIT_INCLUDE_DIRECTORIES}
)

add_test(
    NAME test_parallel
    COMMAND test_parallel
    WORKING_DIRECTORY ${TEST_OUTPUT_DIR}
)
