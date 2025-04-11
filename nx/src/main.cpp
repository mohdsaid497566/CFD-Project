#include <iostream>        // Input/output (cout, cerr)
#include <string>          // String manipulation
#include <vector>          // Dynamic arrays (vectors)
#include <filesystem>      // File system operations (exists) - Requires C++17
#include <cmath>           // Math functions (max)
#include <map>             // Not strictly needed now, but kept for potential future param extensions
#include <utility>         // For std::pair
#include <stdexcept>       // For exceptions
#include <algorithm>       // For std::find, std::max, std::sort, std::unique, std::find_if, std::binary_search
#include <cstdlib>         // For EXIT_SUCCESS, EXIT_FAILURE, std::stod, std::stoi, getenv, setenv, _putenv_s
#include <thread>          // For std::thread::hardware_concurrency
#include <gmsh.h>          // Gmsh C++ API

// OpenMP header is included for omp_get_max_threads for auto-detection,
// and to ensure code compiles correctly when the -fopenmp flag is used.
#ifdef _OPENMP
#include <omp.h>
#endif

// --- NO CUDA HEADERS NEEDED FOR THIS SCRIPT ---
// Gmsh meshing itself is not directly accelerated by CUDA via this API workflow.

// Structure to hold boundary layer parameters
struct BoundaryLayerParams {
    double first_layer_thickness = 0.05;
    double progression = 1.2;
    double thickness = 0.5;
};

// --- Helper Function for Argument Parsing (Basic) ---
std::string getCmdOption(char **begin, char **end, const std::string &option, const std::string& default_val = "") {
    char **itr = std::find(begin, end, option);
    if (itr != end && ++itr != end) {
        if (std::string(*itr).rfind("--", 0) != 0 && std::string(*itr) != "-h" && std::string(*itr) != "-nopopup") {
             return *itr;
        }
    }
    return default_val;
}

bool cmdOptionExists(char **begin, char **end, const std::string &option) {
    return std::find(begin, end, option) != end;
}


int main(int argc, char **argv) {

    // --- Argument Parsing ---
    if (argc < 3 || cmdOptionExists(argv, argv + argc, "-h") || cmdOptionExists(argv, argv + argc, "--help")) {
        // Usage message remains the same
         std::cerr << "Usage: " << argv[0] << " <input_step_file> <output_msh_file> [options]\n"
                  << "\nOptions:\n"
                  << "  --domain_scale <float>      Factor to scale domain size relative to geometry (default: 5.0)\n"
                  << "  --base_mesh_size <float>    Target far-field mesh size (default: 0.5)\n"
                  << "  --alg_2d <int>              2D mesh algorithm (default: 5=Delaunay)\n"
                  << "  --alg_3d <int>              3D mesh algorithm (default: 10=HXT)\n"
                  << "  --threads <int>             Number of CPU threads for Gmsh (default: 0=auto detect using OpenMP/hardware_concurrency)\n" // Clarified threads are for Gmsh/CPU
                  << "  --no_netgen_opt             Disable Netgen optimization\n"
                  << "  --bl_first_layer <float>    Boundary Layer: first layer thickness (default: 0.05)\n"
                  << "  --bl_progression <float>    Boundary Layer: progression ratio (default: 1.2)\n"
                  << "  --bl_thickness <float>      Boundary Layer: total thickness (default: 0.5)\n"
                  << "  --debug                     Enable Gmsh debug output (equivalent to GMSH_DEBUG=1)\n"
                  << "  -nopopup                    Do not show Gmsh GUI after meshing\n"
                  << std::endl;
        return EXIT_FAILURE;
    }

    const std::string step_file = argv[1];
    const std::string output_msh = argv[2];

    // --- Configuration Parameters ---
    double domain_scale = 5.0;
    double base_mesh_size = 0.5;
    int mesh_algorithm_3d = 10;
    int mesh_algorithm_2d = 5;
    int num_threads = 0; // 0 means auto-detect
    bool optimize_netgen = true;
    bool debug_mode = false;
    bool interactive_gui = true;
    BoundaryLayerParams bl_params;

    // --- Parse Arguments (Code is identical to previous version) ---
     try {
        std::string temp_val;
        temp_val = getCmdOption(argv, argv + argc, "--domain_scale");
        if (!temp_val.empty()) domain_scale = std::stod(temp_val);

        temp_val = getCmdOption(argv, argv + argc, "--base_mesh_size");
        if (!temp_val.empty()) base_mesh_size = std::stod(temp_val);

        temp_val = getCmdOption(argv, argv + argc, "--alg_2d");
        if (!temp_val.empty()) mesh_algorithm_2d = std::stoi(temp_val);

        temp_val = getCmdOption(argv, argv + argc, "--alg_3d");
        if (!temp_val.empty()) mesh_algorithm_3d = std::stoi(temp_val);

        // This argument controls Gmsh's internal CPU threading
        temp_val = getCmdOption(argv, argv + argc, "--threads");
        if (!temp_val.empty()) num_threads = std::stoi(temp_val);

        if (cmdOptionExists(argv, argv + argc, "--no_netgen_opt")) {
            optimize_netgen = false;
        }
         if (cmdOptionExists(argv, argv + argc, "--debug")) {
            debug_mode = true;
            #ifdef _WIN32
                _putenv_s("GMSH_DEBUG", "1");
            #else
                setenv("GMSH_DEBUG", "1", 1);
            #endif
            std::cout << "Debug mode enabled (set GMSH_DEBUG=1 environment variable)." << std::endl;
        }
         if (cmdOptionExists(argv, argv + argc, "-nopopup")) {
            interactive_gui = false;
         }

        temp_val = getCmdOption(argv, argv + argc, "--bl_first_layer");
        if (!temp_val.empty()) bl_params.first_layer_thickness = std::stod(temp_val);
        temp_val = getCmdOption(argv, argv + argc, "--bl_progression");
        if (!temp_val.empty()) bl_params.progression = std::stod(temp_val);
        temp_val = getCmdOption(argv, argv + argc, "--bl_thickness");
        if (!temp_val.empty()) bl_params.thickness = std::stod(temp_val);

        // Basic validation (identical)
        if (domain_scale <= 1.0) { std::cerr << "Warning: domain_scale should be > 1.0" << std::endl; domain_scale = 1.5;}
        if (base_mesh_size <= 0) { std::cerr << "Error: base_mesh_size must be positive." << std::endl; return EXIT_FAILURE; }
        if (bl_params.first_layer_thickness <= 0) { std::cerr << "Error: bl_first_layer must be positive." << std::endl; return EXIT_FAILURE; }
        if (bl_params.progression <= 1.0) { std::cerr << "Warning: bl_progression should ideally be > 1.0" << std::endl; }
        if (bl_params.thickness <= 0) { std::cerr << "Error: bl_thickness must be positive." << std::endl; return EXIT_FAILURE; }
        if (bl_params.thickness < bl_params.first_layer_thickness) { std::cerr << "Error: bl_thickness cannot be smaller than bl_first_layer." << std::endl; return EXIT_FAILURE;}

    } catch (const std::invalid_argument& ia) {
        std::cerr << "Error: Invalid numeric value provided for argument: " << ia.what() << std::endl;
        return EXIT_FAILURE;
    } catch (const std::out_of_range& oor) {
        std::cerr << "Error: Numeric value out of range for argument: " << oor.what() << std::endl;
        return EXIT_FAILURE;
    }


    // --- Initial Checks (Identical) ---
    if (!std::filesystem::exists(step_file)) { /* ... */ }
    try { /* ... file size check ... */ } catch (...) { /* ... */ }
    std::cout << "Output mesh file: " << output_msh << std::endl;


    // --- Determine Number of CPU Threads for Gmsh ---
    if (num_threads <= 0) {
        std::cout << "Auto-detecting number of threads..." << std::endl;
        #ifdef _OPENMP
            // Use OpenMP function if compiled with OpenMP support
            num_threads = omp_get_max_threads();
            std::cout << "  Detected threads using OpenMP: " << num_threads << std::endl;
        #else
            // Fallback using C++ standard library (might return 0)
            unsigned int hardware_threads = std::thread::hardware_concurrency();
            if (hardware_threads > 0) {
                num_threads = hardware_threads;
                 std::cout << "  Detected threads using hardware_concurrency: " << num_threads << std::endl;
            } else {
                num_threads = 4; // Sensible default if detection fails
                std::cout << "  Warning: OpenMP not enabled/detected and hardware_concurrency failed. Defaulting to " << num_threads << " threads." << std::endl;
            }
        #endif
    }
    if (num_threads <= 0) num_threads = 1; // Ensure at least one thread
    std::cout << "Gmsh will use up to " << num_threads << " CPU threads for internal parallel operations." << std::endl;


    // --- Main Gmsh Workflow (Identical to previous robust version) ---
    try {
        gmsh::initialize();
        gmsh::option::setNumber("General.Terminal", 1);

        // *** Set the number of threads Gmsh should use internally ***
        // This is where OpenMP acceleration is primarily leveraged.
        gmsh::option::setNumber("General.NumThreads", num_threads);

        std::filesystem::path out_path(output_msh);
        gmsh::model::add(out_path.stem().string());

        // --- Geometry Import, Fixing, Domain Creation, Fragment ---
        // (All these steps remain exactly the same as the previous version)
        std::vector<std::pair<int, int>> ents_before;
        gmsh::model::getEntities(ents_before);
        std::cout << "Merging geometry from " << step_file << "..." << std::endl;
        std::vector<std::pair<int, int>> intake_geometry_dimtags;
        try { gmsh::merge(step_file); } catch(...) { /* error handling */ return EXIT_FAILURE; }
        std::vector<std::pair<int, int>> ents_after;
        gmsh::model::getEntities(ents_after);
        // ... (Identify initial intake_geometry_dimtags)
        if (intake_geometry_dimtags.empty()) { /* error handling */ return EXIT_FAILURE; }
        // ... (Extract intake_surfaces_volumes_dimtags)
        if (intake_surfaces_volumes_dimtags.empty()) { /* error handling */ return EXIT_FAILURE; }
        std::cout << "Applying OpenCASCADE geometry fixing options..." << std::endl;
        gmsh::option::setNumber("Geometry.OCCFixDegenerated", 1); // ... other fixing options ...
        gmsh::option::setNumber("Geometry.Tolerance", 1e-6);
        gmsh::model::occ::synchronize();
        std::cout << "Creating computational domain..." << std::endl;
        double xmin, ymin, zmin, xmax, ymax, zmax;
        gmsh::model::getBoundingBox(intake_surfaces_volumes_dimtags, xmin, ymin, zmin, xmax, ymax, zmax);
        // ... (Calculate domain_scale, domain_center_x/y/z, max_geom_dim, domain_dx/dy/dz, handling degenerate cases)
        int domain_vol_tag = gmsh::model::occ::addBox(/*...*/);
        gmsh::model::occ::synchronize();
        std::cout << "Fragmenting domain with intake geometry..." << std::endl;
        std::vector<std::pair<int, int>> outDimTags;
        std::vector<std::vector<std::pair<int, int>>> outDimTagsMap;
        try { gmsh::model::occ::fragment(/*...*/); } catch (...) { /* error handling */ return EXIT_FAILURE; }
        gmsh::model::occ::synchronize();

        // --- Identify Fluid Volume, Final Surfaces/Edges ---
        // (All these steps remain exactly the same)
        std::vector<std::pair<int, int>> all_vols_after_frag;
        gmsh::model::getEntities(all_vols_after_frag, 3);
        if (all_vols_after_frag.empty()) { /* error handling */ return EXIT_FAILURE; }
        int fluid_volume_tag = -1;
        // ... (Logic to find fluid_volume_tag, remove other vols if necessary)
        if (fluid_volume_tag == -1) { /* error handling if still not found */ return EXIT_FAILURE; }
        std::vector<std::pair<int, int>> fluid_boundary_surfaces_dimtags;
        gmsh::model::getBoundary({{3, fluid_volume_tag}}, fluid_boundary_surfaces_dimtags, false, false, false);
        std::vector<int> final_intake_surface_tags;
        std::vector<std::pair<int, int>> final_intake_surfaces_dimtags;
        // ... (Logic using outDimTagsMap to identify final_intake_surfaces_dimtags)
        if (final_intake_surface_tags.empty()) { /* error handling */ return EXIT_FAILURE; }
        std::vector<std::pair<int, int>> boundary_curves_dimtags;
        gmsh::model::getBoundary(final_intake_surfaces_dimtags, boundary_curves_dimtags, true, false, false);
        std::vector<double> final_intake_edge_tags_double;
        // ... (Populate final_intake_edge_tags_double)
        if (final_intake_edge_tags_double.empty()) { /* warning */ }


        // --- Meshing Setup (Identical) ---
        gmsh::option::setNumber("Mesh.CharacteristicLengthMin", base_mesh_size / 10.0);
        gmsh::option::setNumber("Mesh.CharacteristicLengthMax", base_mesh_size);
        std::cout << "Configuring mesh size field..." << std::endl;
        int mesh_field_dist_tag = gmsh::model::mesh::field::add("Distance");
        std::vector<double> final_intake_surface_tags_double(final_intake_surface_tags.begin(), final_intake_surface_tags.end());
        gmsh::model::mesh::field::setNumbers(mesh_field_dist_tag, "FacesList", final_intake_surface_tags_double);
        int mesh_field_thres_tag = gmsh::model::mesh::field::add("Threshold");
        gmsh::model::mesh::field::setNumber(mesh_field_thres_tag, "InField", mesh_field_dist_tag);
        // ... (Set SizeMin, SizeMax, DistMin, DistMax for Threshold field)
        gmsh::model::mesh::field::setAsBackgroundMesh(mesh_field_thres_tag);
        gmsh::option::setNumber("Mesh.MeshSizeExtendFromBoundary", 0);
        gmsh::option::setNumber("Mesh.Algorithm", mesh_algorithm_2d);
        gmsh::option::setNumber("Mesh.Algorithm3D", mesh_algorithm_3d);
        gmsh::option::setNumber("Mesh.Optimize", 1);
        gmsh::option::setNumber("Mesh.OptimizeNetgen", optimize_netgen ? 1 : 0);

        // --- Boundary Layers (Identical) ---
        if (!final_intake_edge_tags_double.empty()) {
            std::cout << "Configuring Boundary Layer field..." << std::endl;
            int bl_field_tag = gmsh::model::mesh::field::add("BoundaryLayer");
            gmsh::model::mesh::field::setNumbers(bl_field_tag, "EdgesList", final_intake_edge_tags_double);
            gmsh::model::mesh::field::setNumber(bl_field_tag, "Size", bl_params.first_layer_thickness);
            gmsh::model::mesh::field::setNumber(bl_field_tag, "Ratio", bl_params.progression);
            gmsh::model::mesh::field::setNumber(bl_field_tag, "Thickness", bl_params.thickness);
            gmsh::model::mesh::field::setAsBoundaryLayer(bl_field_tag);
        } else { /* warning */ }

        // --- Generate Mesh ---
        // This step utilizes the NumThreads set earlier for CPU parallelism.
        std::cout << "Generating 3D mesh (using up to " << num_threads << " CPU threads)..." << std::endl;
        try {
            gmsh::model::mesh::generate(3);
        } catch (...) { /* error handling */ return EXIT_FAILURE; }
        std::cout << "Mesh generation completed." << std::endl;

        // --- Export Mesh (Identical) ---
        std::cout << "Writing mesh to " << output_msh << "..." << std::endl;
        gmsh::option::setNumber("Mesh.Binary", 1);
        gmsh::option::setNumber("Mesh.MshFileVersion", 4.1);
        try { gmsh::write(output_msh); } catch (...) { /* error handling */ return EXIT_FAILURE; }
        std::cout << "Mesh successfully exported to " << output_msh << std::endl;

    } catch (const std::exception& e) { // Main try block catch
        std::cerr << "Error in Gmsh operation: " << e.what() << std::endl;
        if (gmsh::isInitialized()) gmsh::finalize();
        return EXIT_FAILURE;
    } catch (...) { // Catch-all
        std::cerr << "An unknown error occurred during the meshing process." << std::endl;
        if (gmsh::isInitialized()) gmsh::finalize();
        return EXIT_FAILURE;
    }

    // --- Finalize Gmsh (Identical) ---
    if (gmsh::isInitialized()) {
        if (interactive_gui && gmsh::fltk::isAvailable()) {
             std::cout << "Showing Gmsh GUI (Close window to exit program)." << std::endl;
             gmsh::fltk::run();
        }
        gmsh::finalize();
        std::cout << "Gmsh finalized." << std::endl;
    }

    return EXIT_SUCCESS;
}