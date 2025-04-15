#include "gmsh_nx/gmsh_nx.hpp"

namespace gmsh_nx {
    void initialize() {
        gmsh::initialize();
    }

    void finalize() {
        gmsh::finalize();
    }
}
