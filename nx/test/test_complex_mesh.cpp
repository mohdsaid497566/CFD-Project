#include <gmsh.h>
#include <iostream>
#include <vector>

int main(int argc, char **argv) {
    try {
        // Initialize Gmsh
        gmsh::initialize(argc, argv);

        // Add a model
        gmsh::model::add("complex_mesh_test");

        // Create a 3D box
        int boxTag = gmsh::model::occ::addBox(0, 0, 0, 1, 1, 1);
        gmsh::model::occ::synchronize();
        std::cout << "3D box created successfully." << std::endl;

        // Get the surfaces of the box
        std::vector<std::pair<int, int>> surfaces;
        gmsh::model::getEntities(surfaces, 2); // Dimension 2 for surfaces

        // Convert surface tags from int to double
        std::vector<double> surfaceTags;
        for (const auto &surface : surfaces) {
            surfaceTags.push_back(static_cast<double>(surface.second));
        }

        // Create distance field from surfaces
        gmsh::model::mesh::field::add("Distance", 1);
        gmsh::model::mesh::field::setNumbers(1, "SurfacesList", surfaceTags);

        // Create threshold field for boundary layer
        gmsh::model::mesh::field::add("MathEval", 2);
        gmsh::model::mesh::field::setString(2, "F", "0.05 + 0.1 * F1"); // F1 refers to Field 1

        // Set mesh size field
        gmsh::model::mesh::field::setAsBackgroundMesh(2);

        // Set mesh options with built-in optimization
        gmsh::option::setNumber("Mesh.MeshSizeFromPoints", 0);
        gmsh::option::setNumber("Mesh.MeshSizeFromCurvature", 0);
        gmsh::option::setNumber("Mesh.MeshSizeExtendFromBoundary", 0);
        gmsh::option::setNumber("Mesh.Algorithm3D", 1);      // Delaunay for 3D
        gmsh::option::setNumber("Mesh.Optimize", 1);         // Enable built-in optimizer
        gmsh::option::setNumber("Mesh.OptimizeThreshold", 0.3); // Quality threshold
        gmsh::option::setNumber("Mesh.OptimizeNetgen", 0);   // Disable Netgen
        gmsh::option::setNumber("Mesh.QualityType", 2);      // SICN quality measure
        gmsh::option::setNumber("Mesh.Smoothing", 100);      // Number of smoothing steps

        // Generate a 3D mesh
        gmsh::model::mesh::generate(3);
        std::cout << "3D mesh generated successfully." << std::endl;

        // Save the mesh to a file
        gmsh::write("complex_mesh.msh");
        std::cout << "Mesh saved to 'complex_mesh.msh'." << std::endl;

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
