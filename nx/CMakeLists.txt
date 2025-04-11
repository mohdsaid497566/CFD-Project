cmake_minimum_required(VERSION 3.18)

# Set CUDA environment before project
set(CMAKE_CUDA_COMPILER "/opt/nvidia/hpc_sdk/Linux_x86_64/25.3/cuda/12.8/bin/nvcc")
set(CMAKE_CUDA_HOST_COMPILER "/usr/bin/g++")
set(CMAKE_C_COMPILER "/usr/bin/gcc")
set(CMAKE_CXX_COMPILER "/usr/bin/g++")
set(CMAKE_CUDA_ARCHITECTURES 75)
set(CMAKE_CUDA_FLAGS "${CMAKE_CUDA_FLAGS} -ccbin=/usr/bin/g++ -allow-unsupported-compiler")

project(gmsh_nx LANGUAGES CXX CUDA)

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

# Verify GMSH has OpenCASCADE support
include(CheckCXXSourceCompiles)
set(CMAKE_REQUIRED_INCLUDES ${GMSH_INCLUDE_DIRS})
set(CMAKE_REQUIRED_LIBRARIES ${GMSH_LIBRARIES})
check_cxx_source_compiles("
    #include <gmsh.h>
    int main() {
        gmsh::initialize();
        bool hasOCC = gmsh::model::occ::addBox(0,0,0, 1,1,1) > 0;
        gmsh::finalize();
        return !hasOCC;
    }"
    GMSH_HAS_OPENCASCADE
)

if(NOT GMSH_HAS_OPENCASCADE)
    message(FATAL_ERROR 
        "GMSH was built without OpenCASCADE support.\n"
        "Please rebuild GMSH with: cmake -DENABLE_OCC=ON .."
    )
endif()

find_package(OpenMP REQUIRED)

# Create gmsh_nx library
add_library(gmsh_nx SHARED src/gmsh_nx.cpp)
target_link_libraries(gmsh_nx 
    PRIVATE 
        ${GMSH_LIBRARIES}
        OpenMP::OpenMP_CXX
)
target_include_directories(gmsh_nx PRIVATE ${GMSH_INCLUDE_DIRS})

# Create main executable if not building tests
if(NOT BUILD_TESTING)
    add_executable(gmsh_processor src/main.cpp)
    target_compile_options(gmsh_processor
        PRIVATE
            $<$<CONFIG:Debug>:-g3 -O0 -Wall -Wextra -fno-omit-frame-pointer>
    )
    target_link_libraries(gmsh_processor
        PRIVATE
            gmsh_nx
            ${GMSH_LIBRARIES}
            OpenMP::OpenMP_CXX
            stdc++fs
    )
    target_include_directories(gmsh_processor
        PRIVATE
            ${CMAKE_SOURCE_DIR}/include
            ${GMSH_INCLUDE_DIRS}
    )
endif()

# Add tests
add_subdirectory(test)
