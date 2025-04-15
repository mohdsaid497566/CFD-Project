#include <gmsh.h>
#include <iostream>

int main(int argc, char **argv) {
    try {
        // Initialize Gmsh
        gmsh::initialize(argc, argv);

        // Add a model
        gmsh::model::add("mesh_test");

        // Create a simple rectangle
        gmsh::model::occ::addRectangle(0, 0, 0, 1, 1);
        gmsh::model::occ::synchronize();

        // Generate a 2D mesh
        gmsh::model::mesh::generate(2);
        std::cout << "2D mesh generated successfully." << std::endl;

        // Finalize Gmsh
        gmsh::finalize();
        return 0;
    }
    catch (const std::exception &e) {
        std::cerr << "Exception caught: " << e.what() << std::endl;
        gmsh::finalize();
        return 1;
    }
}
