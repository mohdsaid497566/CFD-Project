#include <gmsh.h>
#include <iostream>

int main(int argc, char **argv) {
    try {
        // Initialize Gmsh
        gmsh::initialize(argc, argv);

        // Log a message
        gmsh::logger::write("This is a test log message.", "info");
        std::cout << "Log message written successfully." << std::endl;

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
