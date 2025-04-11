#include <gmsh.h>
#include <iostream>

int main(int argc, char **argv) {
    try {
        // Initialize Gmsh
        gmsh::initialize();

        // Log Gmsh version
        std::cout << "Gmsh initialized successfully." << std::endl;
        gmsh::logger::write("Gmsh version logged successfully.", "info");

        // Create a simple model using namespace
        gmsh::model::add("test");

        // Clean up
        gmsh::finalize();

        std::cout << "Test completed successfully" << std::endl;
        return 0;
    }
    catch (const std::exception &e) {
        std::cerr << "Exception caught: " << e.what() << std::endl;
        gmsh::finalize();
        return 1;
    }
}
