#include <gmsh.h>
#include <iostream>

int main(int argc, char **argv) {
    try {
        // Initialize Gmsh
        gmsh::initialize(argc, argv);

        // Add a model
        gmsh::model::add("test_model");
        std::cout << "Model 'test_model' added successfully." << std::endl;

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
