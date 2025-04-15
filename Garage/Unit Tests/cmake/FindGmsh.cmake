# Try to find GMSH
# Once done this will define
# GMSH_FOUND - System has GMSH
# GMSH_INCLUDE_DIRS - The GMSH include directories
# GMSH_LIBRARIES - The libraries needed to use GMSH

find_path(GMSH_INCLUDE_DIR gmsh.h
    HINTS $ENV{GMSH_DIR}/include
    PATH_SUFFIXES gmsh
)

find_library(GMSH_LIBRARY
    NAMES gmsh
    HINTS $ENV{GMSH_DIR}/lib
)

include(FindPackageHandleStandardArgs)
find_package_handle_standard_args(GMSH DEFAULT_MSG
    GMSH_LIBRARY GMSH_INCLUDE_DIR)

mark_as_advanced(GMSH_INCLUDE_DIR GMSH_LIBRARY)

set(GMSH_LIBRARIES ${GMSH_LIBRARY})
set(GMSH_INCLUDE_DIRS ${GMSH_INCLUDE_DIR})
