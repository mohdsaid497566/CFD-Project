#include <gmsh.h>
#include <iostream>
#include <vector>

int main(int argc, char **argv) {
    try {
        gmsh::initialize();
        gmsh::model::add("test_operations");

        // Create two intersecting boxes
        int box1 = gmsh::model::occ::addBox(0, 0, 0, 1, 1, 1);
        int box2 = gmsh::model::occ::addBox(0.5, 0.5, 0.5, 1, 1, 1);
        gmsh::model::occ::synchronize();

        // Perform boolean operations
        std::vector<std::pair<int, int>> objects = {{3, box1}};
        std::vector<std::pair<int, int>> tools = {{3, box2}};
        std::vector<std::pair<int, int>> result;
        std::vector<std::vector<std::pair<int, int>>> map;
        
        // Cut operation with all required parameters
        gmsh::model::occ::cut(objects, tools, result, map, -1, true, true);
        gmsh::model::occ::synchronize();

        // Set mesh size and generate
        gmsh::option::setNumber("Mesh.CharacteristicLengthMin", 0.1);
        gmsh::option::setNumber("Mesh.CharacteristicLengthMax", 0.1);
        gmsh::model::mesh::generate(3);
        
        gmsh::write("operations.msh");
        gmsh::finalize();
        return 0;
    }
    catch (const std::exception& e) {
        std::cerr << e.what() << std::endl;
        gmsh::finalize();
        return 1;
    }
}
