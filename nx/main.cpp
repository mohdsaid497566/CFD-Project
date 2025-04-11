#include "gmsh_process.cpp"
#include <iostream>

int main(int argc, char **argv) {
    int ierr = 0;
    
    try {
        // Initialize Gmsh with minimal options
        const char* args[] = {
            "gmsh",
            "-nopopup",    // Don't popup dialog windows
            "-v", "2"      // Set verbosity level
        };
        int argc_ = sizeof(args) / sizeof(args[0]);
        gmsh::initialize(argc_, const_cast<char**>(args));
        
        std::cout << "Gmsh initialized successfully." << std::endl;
        
        std::string stepFile = "INTAKE3D.stp";
        std::string outputMsh = "output.msh";
        double domainScale = 1.5;
        double baseMeshSize = 0.5;
        BoundaryLayer blParams = {0.01, 1.2, 0.1, 2};
        int meshAlgorithm3D = 1;
        int meshAlgorithm2D = 2;
        int numThreads = 4;
        bool optimizeNetgen = true;

        createEngineIntakeCFDMeshSurfacesV5(
            stepFile, outputMsh, domainScale, baseMeshSize,
            blParams, meshAlgorithm3D, meshAlgorithm2D,
            numThreads, optimizeNetgen, ierr
        );

        // Cleanup Gmsh
        gmsh::finalize();
        return ierr;
    }
    catch (const std::exception& e) {
        std::cerr << "Fatal error: " << e.what() << std::endl;
        if (gmsh::isInitialized()) {
            gmsh::finalize();
        }
        return 1;
    }
}
