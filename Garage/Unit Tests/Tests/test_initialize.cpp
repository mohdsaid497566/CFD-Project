#include <gmsh.h>
#include <iostream>

int main(int argc, char **argv) {
    try {
        // Initialize Gmsh
        gmsh::initialize(argc, argv);
        std::cout << "Gmsh initialized successfully." << std::endl;

        // Finalize Gmsh
        gmsh::finalize();
        std::cout << "Gmsh finalized successfully." << std::endl;

        return 0;
    }
    catch (const std::exception &e) {
        std::cerr << "Exception caught: " << e.what() << std::endl;
        gmsh::finalize();
        return 1;
    }
}
