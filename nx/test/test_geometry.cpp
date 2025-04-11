#include <gmsh.h>
#include <iostream>

int main(int argc, char **argv) {
    try {
        // Initialize Gmsh
        gmsh::initialize(argc, argv);

        // Add a model
        gmsh::model::add("geometry_test");

        // Create a simple rectangle
        gmsh::model::occ::addRectangle(0, 0, 0, 1, 1);
        gmsh::model::occ::synchronize();
        std::cout << "Rectangle created successfully." << std::endl;

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
