#include <gmsh.h>
#include <iostream>
#include <string>
#include <vector>
#include <omp.h>

struct BoundaryLayer {
    double firstLayerThickness;
    double progression;
    double thickness;
    int numLayers;
};

void createEngineIntakeCFDMeshSurfacesV5(
    const std::string &stepFile, const std::string &outputMsh,
    double domainScale, double baseMeshSize, const BoundaryLayer &blParams,
    int meshAlgorithm3D, int meshAlgorithm2D, int numThreads,
    bool optimizeNetgen, int &ierr) {

    ierr = 0;

    try {
        if (!gmsh::isInitialized()) {
            throw std::runtime_error("Gmsh must be initialized before calling this function");
        }

        std::cout << "DEBUG: Starting function with parameters:" << std::endl;
        std::cout << "  stepFile: " << stepFile << std::endl;
        std::cout << "  outputMsh: " << outputMsh << std::endl;
        std::cout << "  domainScale: " << domainScale << std::endl;
        std::cout << "  baseMeshSize: " << baseMeshSize << std::endl;
        std::cout << "  numThreads: " << numThreads << std::endl;

        // Set thread count for OpenMP
        omp_set_num_threads(numThreads);

        // Add a new model
        gmsh::model::add("engine_intake_cfd_surface_v5");

        // Merge the STEP file
        gmsh::merge(stepFile);

        // Fix geometry
        gmsh::option::setNumber("Geometry.OCCFixDegenerated", 1);
        gmsh::option::setNumber("Geometry.OCCFixSmallEdges", 1);
        gmsh::option::setNumber("Geometry.OCCFixSmallFaces", 1);
        gmsh::option::setNumber("Geometry.OCCSewFaces", 1);
        gmsh::model::occ::synchronize();

        // Get bounding box
        double xmin, ymin, zmin, xmax, ymax, zmax;
        gmsh::model::getBoundingBox(-1, -1, xmin, ymin, zmin, xmax, ymax, zmax);
        std::cout << "Bounding box: xmin=" << xmin << ", ymin=" << ymin
                  << ", zmin=" << zmin << ", xmax=" << xmax
                  << ", ymax=" << ymax << ", zmax=" << zmax << std::endl;

        // Create domain box
        double domainCenterX = (xmin + xmax) / 2.0;
        double domainCenterY = (ymin + ymax) / 2.0;
        double domainCenterZ = (zmin + zmax) / 2.0;
        double maxDim = std::max(xmax - xmin, std::max(ymax - ymin, zmax - zmin));
        double dx = maxDim * domainScale;
        double dy = maxDim * domainScale;
        double dz = maxDim * domainScale;

        gmsh::model::occ::addBox(domainCenterX - dx / 2.0, domainCenterY - dy / 2.0,
                                 domainCenterZ - dz / 2.0, dx, dy, dz);
        gmsh::model::occ::synchronize();

        // Set mesh options with built-in optimization
        gmsh::option::setNumber("Mesh.Algorithm", meshAlgorithm2D);
        gmsh::option::setNumber("Mesh.Algorithm3D", meshAlgorithm3D);
        gmsh::option::setNumber("Mesh.OptimizeNetgen", 0);  // Disable Netgen
        gmsh::option::setNumber("Mesh.Optimize", 1);        // Enable built-in optimizer
        gmsh::option::setNumber("Mesh.OptimizeThreshold", 0.3);
        gmsh::option::setNumber("Mesh.QualityType", 2);     // SICN quality measure
        gmsh::option::setNumber("Mesh.Smoothing", 100);     // Smoothing steps

        // Create physical group for boundary layer surfaces
        std::vector<std::pair<int, int>> surfaces;
        gmsh::model::getEntities(surfaces, 2);
        std::vector<double> surfaceTags(surfaces.size());

        // Parallelize surface tag extraction with OpenMP
        #pragma omp parallel for
        for (size_t i = 0; i < surfaces.size(); ++i) {
            surfaceTags[i] = static_cast<double>(surfaces[i].second);
        }

        // Apply boundary layer using fields
        gmsh::model::mesh::field::add("Distance", 1);
        gmsh::model::mesh::field::setNumbers(1, "SurfacesList", surfaceTags);

        gmsh::model::mesh::field::add("Threshold", 2);
        gmsh::model::mesh::field::setNumber(2, "IField", 1);
        gmsh::model::mesh::field::setNumber(2, "LcMin", blParams.firstLayerThickness);
        gmsh::model::mesh::field::setNumber(2, "LcMax", baseMeshSize);
        gmsh::model::mesh::field::setNumber(2, "DistMin", blParams.thickness);
        gmsh::model::mesh::field::setNumber(2, "DistMax", blParams.thickness * blParams.progression);
        gmsh::model::mesh::field::setAsBackgroundMesh(2);

        // Generate the mesh
        gmsh::model::mesh::generate(3);

        // Write the mesh to a file
        gmsh::write(outputMsh);

        std::cout << "Mesh generation completed successfully." << std::endl;
    } catch (const std::exception &e) {
        std::cerr << "Error: " << e.what() << std::endl;
        ierr = -1;
    }
}
