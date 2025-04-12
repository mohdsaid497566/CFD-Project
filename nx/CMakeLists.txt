cmake_minimum_required(VERSION 3.18)

# Set CUDA environment before project
set(CMAKE_CUDA_COMPILER "/opt/nvidia/hpc_sdk/Linux_x86_64/25.3/cuda/12.8/bin/nvcc")
set(CMAKE_CUDA_HOST_COMPILER "/usr/bin/g++")
set(CMAKE_C_COMPILER "/usr/bin/gcc")
set(CMAKE_CXX_COMPILER "/usr/bin/g++")
set(CMAKE_CUDA_ARCHITECTURES 75)
set(CMAKE_CUDA_FLAGS "${CMAKE_CUDA_FLAGS} -ccbin=/usr/bin/g++ -allow-unsupported-compiler")

project(intake_cfd_project LANGUAGES CXX CUDA)

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Enable testing at root level
include(CTest)
enable_testing()

# Add path to custom find modules and includes
list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/cmake")
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/include)

# Find required packages
find_package(GMSH REQUIRED)
if(NOT GMSH_FOUND)
    message(FATAL_ERROR "GMSH not found")
endif()

find_package(OpenMP)

# Verify GMSH has OpenCASCADE support
include(CheckCXXSourceCompiles)
set(CMAKE_REQUIRED_INCLUDES ${GMSH_INCLUDE_DIRS})
set(CMAKE_REQUIRED_LIBRARIES ${GMSH_LIBRARIES})
check_cxx_source_compiles("
    #include <gmsh.h>
    int main() {
        gmsh::initialize();
        gmsh::model::occ::synchronize();
        gmsh::finalize();
        return 0;
    }"
    GMSH_HAS_OPENCASCADE
)

if(NOT GMSH_HAS_OPENCASCADE)
    message(FATAL_ERROR 
        "GMSH was built without OpenCASCADE support.\n"
        "Please rebuild GMSH with: cmake -DENABLE_OCC=ON .."
    )
endif()

# Create gmsh_nx library
add_library(gmsh_nx SHARED src/gmsh_nx.cpp)
target_link_libraries(gmsh_nx 
    PRIVATE 
        ${GMSH_LIBRARIES}
        OpenMP::OpenMP_CXX
)
target_include_directories(gmsh_nx PRIVATE ${GMSH_INCLUDE_DIRS})

# Add executable for main
add_executable(mesh_generator src/main.cpp)
target_link_libraries(mesh_generator 
    PRIVATE
        gmsh_nx
        ${GMSH_LIBRARIES}
        OpenMP::OpenMP_CXX
        stdc++fs
)
target_include_directories(mesh_generator
    PRIVATE
        ${CMAKE_SOURCE_DIR}/include
        ${GMSH_INCLUDE_DIRS}
)

target_compile_options(mesh_generator
    PRIVATE
        $<$<CONFIG:Debug>:-g3 -O0 -Wall -Wextra -fno-omit-frame-pointer>
)

# Create a symlink from 'gmsh_processor' to 'mesh_generator' for compatibility
add_custom_command(
  TARGET mesh_generator POST_BUILD
  COMMAND ${CMAKE_COMMAND} -E create_symlink 
          $<TARGET_FILE:mesh_generator> 
          ${CMAKE_BINARY_DIR}/gmsh_processor
  COMMENT "Creating symlink from mesh_generator to gmsh_processor"
)

# Add tests
add_subdirectory(test)
