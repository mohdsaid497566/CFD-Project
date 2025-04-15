find_path(GMSH_INCLUDE_DIR gmsh.h
    HINTS
    /usr/include
    /usr/local/include
)

find_library(GMSH_LIBRARY
    NAMES gmsh
    HINTS
    /usr/lib
    /usr/lib/x86_64-linux-gnu
    /usr/local/lib
)

include(FindPackageHandleStandardArgs)
find_package_handle_standard_args(Gmsh DEFAULT_MSG GMSH_LIBRARY GMSH_INCLUDE_DIR)

if(GMSH_FOUND)
    set(GMSH_LIBRARIES ${GMSH_LIBRARY})
    set(GMSH_INCLUDE_DIRS ${GMSH_INCLUDE_DIR})
endif()

mark_as_advanced(GMSH_INCLUDE_DIR GMSH_LIBRARY)
