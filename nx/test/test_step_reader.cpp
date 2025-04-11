#include <gmsh.h>
#include <iostream>
#include <cassert>

int main(int argc, char **argv) {
    try {
        gmsh::initialize();
        
        // Test 1: Basic STEP file reading
        std::cout << "Testing STEP file reading..." << std::endl;
        try {
            gmsh::merge("INTAKE3D.stp");
            std::vector<std::pair<int, int>> entities;
            gmsh::model::getEntities(entities);
            assert(!entities.empty() && "STEP file loaded but no entities found");
            std::cout << "Found " << entities.size() << " entities" << std::endl;
        } catch (const std::exception& e) {
            std::cerr << "STEP reading failed: " << e.what() << std::endl;
            throw;
        }

        // Test 2: Verify bounding box
        double xmin, ymin, zmin, xmax, ymax, zmax;
        gmsh::model::getBoundingBox(-1, -1, xmin, ymin, zmin, xmax, ymax, zmax);
        std::cout << "Bounding box: "
                  << "[" << xmin << ", " << xmax << "] x "
                  << "[" << ymin << ", " << ymax << "] x "
                  << "[" << zmin << ", " << zmax << "]" << std::endl;
        
        gmsh::finalize();
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "Fatal error: " << e.what() << std::endl;
        gmsh::finalize();
        return 1;
    }
}
