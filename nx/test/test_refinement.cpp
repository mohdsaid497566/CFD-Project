#include <gmsh.h>
#include <iostream>
#include <vector>

int main(int argc, char **argv) {
    try {
        gmsh::initialize();
        gmsh::model::add("test_refinement");

        // Create geometry
        int boxTag = gmsh::model::occ::addBox(0, 0, 0, 1, 1, 1);
        gmsh::model::occ::synchronize();

        // Add size fields
        gmsh::model::mesh::field::add("Distance", 1);
        gmsh::model::mesh::field::setNumbers(1, "PointsList", {1});
        
        gmsh::model::mesh::field::add("Threshold", 2);
        gmsh::model::mesh::field::setNumber(2, "IField", 1);
        gmsh::model::mesh::field::setNumber(2, "LcMin", 0.01);
        gmsh::model::mesh::field::setNumber(2, "LcMax", 0.1);
        gmsh::model::mesh::field::setNumber(2, "DistMin", 0.1);
        gmsh::model::mesh::field::setNumber(2, "DistMax", 0.5);
        
        gmsh::model::mesh::field::setAsBackgroundMesh(2);

        // Generate and save mesh
        gmsh::model::mesh::generate(3);
        gmsh::write("refinement.msh");
        gmsh::finalize();
        return 0;
    }
    catch (const std::exception& e) {
        std::cerr << e.what() << std::endl;
        return 1;
    }
}
