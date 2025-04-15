#include <iostream>        // Input/output (cout, cerr)
#include <string>          // String manipulation
#include <vector>          // Dynamic arrays (vectors)
#include <filesystem>      // File system operations (exists) - Requires C++17
#include <cmath>           // Math functions (max)
#include <map>             // Not strictly needed now, but kept for potential future param extensions
#include <set>             // For std::set used in surface filtering
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
    int num_layers = 0;     // Auto-calculate number of layers if 0, otherwise use this value
    bool smooth_normals = true; // Smooth boundary layer normals
    bool optimize_quality = true; // Optimize boundary layer element quality
    double angle_tolerance = 30.0; // Angle tolerance in degrees for boundary layer
    int intersect_method = 2; // Method for handling intersections: 0=None, 1=Restrict, 2=Split
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
                  << "  --bl_num_layers <int>       Boundary Layer: number of layers (default: 0=auto)\n"
                  << "  --bl_smooth_normals <0|1>   Boundary Layer: smooth normals (default: 1=true)\n"
                  << "  --bl_angle_tolerance <float> Boundary Layer: angle tolerance in degrees (default: 30.0)\n"
                  << "  --bl_intersect_method <0|1|2> Boundary Layer: intersection handling (default: 2=Split)\n"
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
        temp_val = getCmdOption(argv, argv + argc, "--bl_num_layers");
        if (!temp_val.empty()) bl_params.num_layers = std::stoi(temp_val);
        temp_val = getCmdOption(argv, argv + argc, "--bl_smooth_normals");
        if (!temp_val.empty()) bl_params.smooth_normals = (std::stoi(temp_val) != 0);
        temp_val = getCmdOption(argv, argv + argc, "--bl_angle_tolerance");
        if (!temp_val.empty()) bl_params.angle_tolerance = std::stod(temp_val);
        temp_val = getCmdOption(argv, argv + argc, "--bl_intersect_method");
        if (!temp_val.empty()) bl_params.intersect_method = std::stoi(temp_val);

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
    if (!std::filesystem::exists(step_file)) { 
        std::cerr << "Error: Input STEP file " << step_file << " does not exist." << std::endl;
        return EXIT_FAILURE;
    }

    try { 
        std::uintmax_t file_size = std::filesystem::file_size(step_file);
        if (file_size == 0) {
            std::cerr << "Error: Input STEP file " << step_file << " is empty." << std::endl;
            return EXIT_FAILURE;
        }
        std::cout << "Input file size: " << file_size << " bytes" << std::endl;
    } catch (std::filesystem::filesystem_error& e) {
        std::cerr << "Error accessing input file: " << e.what() << std::endl;
        return EXIT_FAILURE;
    }
    
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


    // --- Main Gmsh Workflow ---
    try {
        gmsh::initialize();
        gmsh::option::setNumber("General.Terminal", 1);

        // *** Set the number of threads Gmsh should use internally ***
        gmsh::option::setNumber("General.NumThreads", num_threads);

        std::filesystem::path out_path(output_msh);
        gmsh::model::add(out_path.stem().string());

        // --- Geometry Import, Fixing, Domain Creation, Fragment ---
        std::vector<std::pair<int, int>> ents_before;
        gmsh::model::getEntities(ents_before);
        std::cout << "Merging geometry from " << step_file << "..." << std::endl;
        std::vector<std::pair<int, int>> intake_geometry_dimtags;
        
        try { 
            gmsh::merge(step_file); 
        } catch(const std::exception& e) {
            std::cerr << "Error merging STEP file: " << e.what() << std::endl;
            return EXIT_FAILURE;
        } catch(...) {
            std::cerr << "Unknown error merging STEP file" << std::endl;
            return EXIT_FAILURE;
        }
        
        std::vector<std::pair<int, int>> ents_after;
        gmsh::model::getEntities(ents_after);
        
        // Identify intake geometry dimensions and tags
        for (const auto& ent : ents_after) {
            if (std::find(ents_before.begin(), ents_before.end(), ent) == ents_before.end()) {
                intake_geometry_dimtags.push_back(ent);
            }
        }
        
        if (intake_geometry_dimtags.empty()) {
            std::cerr << "Error: No geometry was imported from the STEP file." << std::endl;
            return EXIT_FAILURE;
        }
        
        // Extract surfaces and volumes for intake geometry
        std::vector<std::pair<int, int>> intake_surfaces_volumes_dimtags;
        for (const auto& dimtag : intake_geometry_dimtags) {
            if (dimtag.first >= 2) { // Dimensions 2 (surfaces) and 3 (volumes)
                intake_surfaces_volumes_dimtags.push_back(dimtag);
            }
        }
        
        if (intake_surfaces_volumes_dimtags.empty()) {
            std::cerr << "Error: No surfaces or volumes found in the imported geometry." << std::endl;
            return EXIT_FAILURE;
        }
        
        std::cout << "Applying OpenCASCADE geometry fixing options..." << std::endl;
        // Increase tolerance for better surface healing
        gmsh::option::setNumber("Geometry.Tolerance", 1e-5);
        gmsh::option::setNumber("Geometry.ToleranceBoolean", 1e-4);
        gmsh::option::setNumber("Geometry.OCCFixDegenerated", 1);
        gmsh::option::setNumber("Geometry.OCCFixSmallEdges", 1);
        gmsh::option::setNumber("Geometry.OCCFixSmallFaces", 1);
        gmsh::option::setNumber("Geometry.OCCSewFaces", 1);
        gmsh::option::setNumber("Geometry.OCCMakeSolids", 1);
        
        // Improve surface joining algorithms
        gmsh::option::setNumber("Geometry.AutoCoherence", 1);
        gmsh::model::occ::synchronize();
        
        std::cout << "Creating computational domain..." << std::endl;
        double xmin = 0, ymin = 0, zmin = 0, xmax = 0, ymax = 0, zmax = 0;
        
        // Get the bounding box of all entities
        for (const auto& dimtag : intake_surfaces_volumes_dimtags) {
            double ent_xmin, ent_ymin, ent_zmin, ent_xmax, ent_ymax, ent_zmax;
            gmsh::model::getBoundingBox(dimtag.first, dimtag.second, 
                                      ent_xmin, ent_ymin, ent_zmin, 
                                      ent_xmax, ent_ymax, ent_zmax);
            
            // Initialize bounding box with first entity
            if (xmin == 0 && xmax == 0) {
                xmin = ent_xmin; ymin = ent_ymin; zmin = ent_zmin;
                xmax = ent_xmax; ymax = ent_ymax; zmax = ent_zmax;
            } else {
                // Expand bounding box with each entity
                xmin = std::min(xmin, ent_xmin);
                ymin = std::min(ymin, ent_ymin);
                zmin = std::min(zmin, ent_zmin);
                xmax = std::max(xmax, ent_xmax);
                ymax = std::max(ymax, ent_ymax);
                zmax = std::max(zmax, ent_zmax);
            }
        }
        
        // Calculate domain size based on geometry bounding box
        double domain_center_x = (xmax + xmin) / 2.0;
        double domain_center_y = (ymax + ymin) / 2.0;
        double domain_center_z = (zmax + zmin) / 2.0;
        
        double max_geom_dim = std::max({xmax - xmin, ymax - ymin, zmax - zmin});
        double domain_dx = domain_scale * (xmax - xmin);
        double domain_dy = domain_scale * (ymax - ymin);
        double domain_dz = domain_scale * (zmax - zmin);
        
        // Handle degenerate cases (flat/linear geometry)
        if (domain_dx < 0.01 * max_geom_dim) domain_dx = max_geom_dim;
        if (domain_dy < 0.01 * max_geom_dim) domain_dy = max_geom_dim;
        if (domain_dz < 0.01 * max_geom_dim) domain_dz = max_geom_dim;
        
        int domain_vol_tag = gmsh::model::occ::addBox(
            domain_center_x - domain_dx / 2,
            domain_center_y - domain_dy / 2,
            domain_center_z - domain_dz / 2,
            domain_dx, domain_dy, domain_dz
        );
        
        gmsh::model::occ::synchronize();
        
        std::cout << "Fragmenting domain with intake geometry..." << std::endl;
        std::vector<std::pair<int, int>> outDimTags;
        std::vector<std::vector<std::pair<int, int>>> outDimTagsMap;
        
        try {
            gmsh::model::occ::fragment(
                {{3, domain_vol_tag}}, 
                intake_surfaces_volumes_dimtags, 
                outDimTags, 
                outDimTagsMap
            );
        } catch (const std::exception& e) {
            std::cerr << "Error during fragmentation: " << e.what() << std::endl;
            return EXIT_FAILURE;
        } catch(...) {
            std::cerr << "Unknown error during fragmentation" << std::endl;
            return EXIT_FAILURE;
        }
        
        gmsh::model::occ::synchronize();

        // --- Identify Fluid Volume, Final Surfaces/Edges ---
        std::vector<std::pair<int, int>> all_vols_after_frag;
        gmsh::model::getEntities(all_vols_after_frag, 3);
        
        // Debug output of all entities
        std::cout << "Entities after fragmentation:" << std::endl;
        std::vector<std::pair<int, int>> all_entities;
        gmsh::model::getEntities(all_entities);
        std::cout << "  Found " << all_entities.size() << " total entities" << std::endl;
        
        // Count by dimension
        int dim0_count = 0, dim1_count = 0, dim2_count = 0, dim3_count = 0;
        for (const auto& entity : all_entities) {
            if (entity.first == 0) dim0_count++;
            else if (entity.first == 1) dim1_count++;
            else if (entity.first == 2) dim2_count++;
            else if (entity.first == 3) dim3_count++;
        }
        std::cout << "  Points: " << dim0_count << ", Curves: " << dim1_count 
                  << ", Surfaces: " << dim2_count << ", Volumes: " << dim3_count << std::endl;
        
        if (all_vols_after_frag.empty()) {
            std::cout << "Warning: No volumes found. Attempting to create volume from surfaces..." << std::endl;
            
            // Get all surfaces
            std::vector<std::pair<int, int>> all_surfaces;
            gmsh::model::getEntities(all_surfaces, 2);
            
            if (!all_surfaces.empty()) {
                try {
                    // Create a surface loop
                    std::vector<int> surface_tags;
                    for (const auto& surface : all_surfaces) {
                        surface_tags.push_back(surface.second);
                    }
                    
                    // Add a surface loop
                    int surface_loop_tag = gmsh::model::occ::addSurfaceLoop(surface_tags);
                    
                    // Create a volume from the surface loop
                    int new_vol_tag = gmsh::model::occ::addVolume({surface_loop_tag});
                    gmsh::model::occ::synchronize();
                    
                    // Requery for volumes
                    all_vols_after_frag.clear();
                    gmsh::model::getEntities(all_vols_after_frag, 3);
                    
                    std::cout << "Created new volume with tag " << new_vol_tag << std::endl;
                } catch (const std::exception& e) {
                    std::cout << "Warning: Failed to create volume: " << e.what() << std::endl;
                }
            }
            
            if (all_vols_after_frag.empty()) {
                // Last resort: Create a box that contains all surfaces
                std::cout << "Attempting to create a bounding box volume..." << std::endl;
                
                // Get model bounding box
                double xmin = 0, ymin = 0, zmin = 0, xmax = 0, ymax = 0, zmax = 0;
                gmsh::model::getBoundingBox(-1, -1, xmin, ymin, zmin, xmax, ymax, zmax);
                
                // Create a box slightly larger than the model
                double margin = 0.01 * std::max({xmax-xmin, ymax-ymin, zmax-zmin});
                int box_tag = gmsh::model::occ::addBox(
                    xmin - margin, ymin - margin, zmin - margin,
                    (xmax-xmin) + 2*margin, (ymax-ymin) + 2*margin, (zmax-zmin) + 2*margin
                );
                gmsh::model::occ::synchronize();
                
                // Add the box to our volumes list
                all_vols_after_frag.push_back({3, box_tag});
                std::cout << "Created bounding box volume with tag " << box_tag << std::endl;
            }
        }

        // After fragment and before meshing, try to heal the model further
        std::cout << "Healing model after fragmentation..." << std::endl;
        try {
            std::vector<std::pair<int, int>> outDimTagsHealed;
            if (!all_vols_after_frag.empty()) {
                // Try to heal the fragmented volumes
                gmsh::model::occ::healShapes(all_vols_after_frag, outDimTagsHealed, 
                                            1e-4,  // tolerance
                                            true,  // fixDegenerated
                                            true,  // fixSmallEdges
                                            true,  // fixSmallFaces
                                            true,  // sewFaces
                                            true); // makeSolids
                gmsh::model::occ::synchronize();
                std::cout << "Healed " << outDimTagsHealed.size() << " entities" << std::endl;
                
                // Re-query volumes after healing as they might have changed
                all_vols_after_frag.clear();
                gmsh::model::getEntities(all_vols_after_frag, 3);
            }
        } catch (const std::exception& e) {
            std::cout << "Warning during healing: " << e.what() << std::endl;
            // Continue with original volumes if healing fails
        }
        
        // Debug output of all volumes
        std::cout << "Volumes after healing: " << all_vols_after_frag.size() << std::endl;
        for (size_t i = 0; i < all_vols_after_frag.size(); i++) {
            std::cout << "  Volume " << i << ": tag " << all_vols_after_frag[i].second << std::endl;
        }
        
        int fluid_volume_tag = -1;
        if (!all_vols_after_frag.empty()) {
            // Use the first volume as the fluid domain (simplification)
            fluid_volume_tag = all_vols_after_frag[0].second;
            std::cout << "Selected fluid volume: Tag " << fluid_volume_tag << std::endl;
        } else {
            std::cerr << "Error: No volumes available after healing." << std::endl;
            
            // Last resort: Use all surfaces directly for meshing without a volume
            std::cout << "Attempting to continue with surface meshing only..." << std::endl;
            std::vector<std::pair<int, int>> all_surfaces;
            gmsh::model::getEntities(all_surfaces, 2);
            
            if (all_surfaces.empty()) {
                std::cerr << "Error: No surfaces available either. Cannot continue." << std::endl;
                return EXIT_FAILURE;
            }
            
            // Continue without fluid volume
            std::cout << "Using " << all_surfaces.size() << " surfaces for meshing without volume." << std::endl;
        }

        // Alternative approach to identify surfaces if getBoundary fails
        std::vector<std::pair<int, int>> fluid_boundary_surfaces_dimtags;
        try {
            gmsh::model::getBoundary({{3, fluid_volume_tag}}, fluid_boundary_surfaces_dimtags, false, false, false);
        } catch (const std::exception& e) {
            std::cout << "Warning during boundary extraction: " << e.what() << std::endl;
            // Get all surfaces as a fallback
            gmsh::model::getEntities(fluid_boundary_surfaces_dimtags, 2);
        }
        
        if (fluid_boundary_surfaces_dimtags.empty()) {
            std::cout << "Warning: No surfaces found in fluid boundary. Getting all surfaces..." << std::endl;
            gmsh::model::getEntities(fluid_boundary_surfaces_dimtags, 2);
        }
        
        std::vector<int> final_intake_surface_tags;
        std::vector<std::pair<int, int>> final_intake_surfaces_dimtags;
        
        // First attempt: Extract intake surface tags from the fragmentation mapping
        if (!outDimTagsMap.empty() && outDimTagsMap[0].size() > 0) {
            for (const auto& dimtag : outDimTagsMap[0]) {
                if (dimtag.first == 2) { // Surface dimension
                    final_intake_surface_tags.push_back(dimtag.second);
                    final_intake_surfaces_dimtags.push_back(dimtag);
                }
            }
        }
        
        // If not found through fragmentation map, use alternative approach
        if (final_intake_surface_tags.empty()) {
            std::cout << "Warning: Could not identify intake surfaces through fragmentation map. Trying alternative approach..." << std::endl;
            
            // Get all surfaces from the domain boundaries
            std::vector<std::pair<int, int>> domain_box_surfaces;
            gmsh::model::getBoundary({{3, domain_vol_tag}}, domain_box_surfaces, false, false, false);
            
            // Convert to a set of surface tags for easy lookup
            std::set<int> domain_box_surface_tags;
            for (const auto& surface : domain_box_surfaces) {
                domain_box_surface_tags.insert(surface.second);
            }
            
            // Include all boundary surfaces of fluid volume that aren't part of the domain box
            for (const auto& surface : fluid_boundary_surfaces_dimtags) {
                if (domain_box_surface_tags.find(surface.second) == domain_box_surface_tags.end()) {
                    final_intake_surface_tags.push_back(surface.second);
                    final_intake_surfaces_dimtags.push_back(surface);
                }
            }
            
            std::cout << "Found " << final_intake_surface_tags.size() << " intake surfaces using alternative approach." << std::endl;
        }
        
        // Last resort: If still empty, take all boundary surfaces
        if (final_intake_surface_tags.empty()) {
            std::cout << "Warning: Alternative approach failed. Using all fluid boundary surfaces..." << std::endl;
            
            for (const auto& surface : fluid_boundary_surfaces_dimtags) {
                final_intake_surface_tags.push_back(surface.second);
                final_intake_surfaces_dimtags.push_back(surface);
            }
            
            std::cout << "Using " << final_intake_surface_tags.size() << " boundary surfaces as intake surfaces." << std::endl;
        }
        
        if (final_intake_surface_tags.empty()) {
            std::cerr << "Error: Could not identify intake surfaces." << std::endl;
            return EXIT_FAILURE;
        }
        
        std::vector<std::pair<int, int>> boundary_curves_dimtags;
        gmsh::model::getBoundary(final_intake_surfaces_dimtags, boundary_curves_dimtags, true, false, false);
        
        std::vector<double> final_intake_edge_tags_double;
        for (const auto& curve : boundary_curves_dimtags) {
            if (curve.first == 1) { // Edges/curves are dimension 1
                final_intake_edge_tags_double.push_back(curve.second);
            }
        }
        
        if (final_intake_edge_tags_double.empty()) {
            std::cout << "Warning: No boundary edges identified for intake surfaces." << std::endl;
        }

        // Find all unique edges that form the boundary
        std::cout << "Extracting model edges for boundary layer creation..." << std::endl;
        std::vector<std::pair<int, int>> all_edges;
        try {
            // Create edges explicitly to ensure connectivity
            gmsh::model::mesh::createEdges();
            
            // Get all edges from all surfaces, not just boundary curves
            for (const auto& surface : final_intake_surfaces_dimtags) {
                std::vector<std::pair<int, int>> surface_edges;
                gmsh::model::getBoundary({surface}, surface_edges, false, false, true);
                for (const auto& edge : surface_edges) {
                    if (edge.first == 1) { // Only consider edges (dim=1)
                        all_edges.push_back(edge);
                    }
                }
            }
            
            // If we get edges, use them directly
            if (!all_edges.empty()) {
                final_intake_edge_tags_double.clear();
                for (const auto& edge : all_edges) {
                    final_intake_edge_tags_double.push_back(edge.second);
                }
            }
            
            if (!final_intake_edge_tags_double.empty()) {
                std::cout << "Found " << final_intake_edge_tags_double.size() << " edges for boundary layer mesh" << std::endl;
            }
        } catch (const std::exception& e) {
            std::cout << "Warning during edge extraction: " << e.what() << std::endl;
        }

        // --- Meshing Setup ---
        gmsh::option::setNumber("Mesh.CharacteristicLengthMin", base_mesh_size / 10.0);
        gmsh::option::setNumber("Mesh.CharacteristicLengthMax", base_mesh_size);
        
        // Improve mesh generation settings for problem geometries
        gmsh::option::setNumber("Mesh.SaveAll", 1);  // Save all elements
        gmsh::option::setNumber("Mesh.MeshOnlyVisible", 0);  // Mesh everything
        gmsh::option::setNumber("Mesh.MeshOnlyEmpty", 0);  // Mesh all entities
        gmsh::option::setNumber("Mesh.Algorithm", mesh_algorithm_2d); // Default to Delaunay
        gmsh::option::setNumber("Mesh.Algorithm3D", mesh_algorithm_3d);
        
        // Use compound meshing for curved surfaces
        gmsh::option::setNumber("Mesh.CompoundClassify", 1);
        
        // Set better quality settings
        gmsh::option::setNumber("Mesh.LcIntegrationPrecision", 1e-5);
        gmsh::option::setNumber("Mesh.ElementOrder", 1);  // Use first order elements first
        
        std::cout << "Configuring mesh size field..." << std::endl;
        int mesh_field_dist_tag = gmsh::model::mesh::field::add("Distance");
        std::vector<double> final_intake_surface_tags_double(final_intake_surface_tags.begin(), final_intake_surface_tags.end());
        gmsh::model::mesh::field::setNumbers(mesh_field_dist_tag, "FacesList", final_intake_surface_tags_double);
        int mesh_field_thres_tag = gmsh::model::mesh::field::add("Threshold");
        gmsh::model::mesh::field::setNumber(mesh_field_thres_tag, "InField", mesh_field_dist_tag);
        
        gmsh::model::mesh::field::setNumber(mesh_field_thres_tag, "SizeMin", base_mesh_size / 5.0);
        gmsh::model::mesh::field::setNumber(mesh_field_thres_tag, "SizeMax", base_mesh_size);
        gmsh::model::mesh::field::setNumber(mesh_field_thres_tag, "DistMin", 0.1 * max_geom_dim);
        gmsh::model::mesh::field::setNumber(mesh_field_thres_tag, "DistMax", 0.5 * max_geom_dim);
        gmsh::model::mesh::field::setAsBackgroundMesh(mesh_field_thres_tag);
        gmsh::option::setNumber("Mesh.MeshSizeExtendFromBoundary", 0);
        gmsh::option::setNumber("Mesh.Algorithm", mesh_algorithm_2d);
        gmsh::option::setNumber("Mesh.Algorithm3D", mesh_algorithm_3d);
        gmsh::option::setNumber("Mesh.Optimize", 1);
        gmsh::option::setNumber("Mesh.OptimizeNetgen", optimize_netgen ? 1 : 0);

        // --- Boundary Layers ---
        if (!final_intake_edge_tags_double.empty()) {
            std::cout << "Configuring Boundary Layer field..." << std::endl;
            
            // Set some global meshing options to improve performance with boundary layers
            gmsh::option::setNumber("Mesh.BoundaryLayerFanPoints", 3); // Fewer fan points at corners
            gmsh::option::setNumber("Mesh.Optimize", 1);
            gmsh::option::setNumber("Mesh.OptimizeThreshold", 0.3); // Less aggressive optimization
            
            // Create the boundary layer field
            int bl_field_tag = gmsh::model::mesh::field::add("BoundaryLayer");
            gmsh::model::mesh::field::setNumbers(bl_field_tag, "EdgesList", final_intake_edge_tags_double);
            gmsh::model::mesh::field::setNumber(bl_field_tag, "Size", bl_params.first_layer_thickness);
            gmsh::model::mesh::field::setNumber(bl_field_tag, "Ratio", bl_params.progression);
            gmsh::model::mesh::field::setNumber(bl_field_tag, "Thickness", bl_params.thickness);
            
            // Additional boundary layer settings for better performance
            if (bl_params.num_layers > 0) {
                gmsh::model::mesh::field::setNumber(bl_field_tag, "NbLayers", bl_params.num_layers);
            }
            
            gmsh::model::mesh::field::setNumber(bl_field_tag, "SmoothNormals", bl_params.smooth_normals ? 1 : 0);
            gmsh::model::mesh::field::setNumber(bl_field_tag, "AngleTol", bl_params.angle_tolerance);
            gmsh::model::mesh::field::setNumber(bl_field_tag, "IntersectMetrics", bl_params.intersect_method);
            
            // Use growth rate instead of absolute thickness if possible
            gmsh::model::mesh::field::setNumber(bl_field_tag, "BetaLaw", 1); // Use beta law for layer distribution
            
            // Set the field as boundary layer
            gmsh::model::mesh::field::setAsBoundaryLayer(bl_field_tag);
        } else { 
            std::cout << "Warning: No edges available for boundary layer mesh." << std::endl;
        }

        // --- Generate Mesh ---
        std::cout << "Generating 3D mesh (using up to " << num_threads << " CPU threads)..." << std::endl;
        
        // Additional performance options for meshing - safely setting options with error checking
        try {
            gmsh::option::setNumber("Mesh.MaxNumThreads2D", num_threads);
            gmsh::option::setNumber("Mesh.MaxNumThreads3D", num_threads);
            
            // Improve robustness for difficult geometries
            gmsh::option::setNumber("Mesh.AngleToleranceFacetOverlap", 0.5);
            gmsh::option::setNumber("Mesh.AnisoMax", 100.0); // Allow more anisotropic elements
            
            // Set more options to handle non-closed loops
            gmsh::option::setNumber("Mesh.IgnorePeriodicity", 1);
            gmsh::option::setNumber("Mesh.ScalingFactor", 1.0);
            
            // Set reliable standard options
            gmsh::option::setNumber("Mesh.OptimizeThreshold", 0.3);
        } catch (const std::exception& e) {
            std::cerr << "Warning: Some mesh options could not be set: " << e.what() << std::endl;
            // Continue execution - non-fatal error
        }
        
        // Generate mesh with more robust approach
        try {
            std::cout << "  Generating 1D mesh..." << std::endl;
            gmsh::model::mesh::generate(1);
            
            std::cout << "  Generating 2D mesh..." << std::endl;
            // Try different meshing algorithm if first one fails
            try {
                gmsh::model::mesh::generate(2);
            }
            catch (const std::exception& e) {
                std::cout << "  Warning: First attempt at 2D meshing failed: " << e.what() << std::endl;
                std::cout << "  Trying alternative 2D algorithm..." << std::endl;
                gmsh::option::setNumber("Mesh.Algorithm", 3); // Try MeshAdapt algorithm instead
                gmsh::model::mesh::generate(2);
            }
            
            std::cout << "  Generating 3D mesh..." << std::endl;
            gmsh::model::mesh::generate(3);
        } catch (const std::exception& e) {
            std::cerr << "Error during mesh generation: " << e.what() << std::endl;
            
            // If mesh generation fails, save what we have so far
            try {
                std::string debug_mesh_file = output_msh + "_debug.msh";
                std::cout << "Saving partial mesh to " << debug_mesh_file << " for debugging..." << std::endl;
                gmsh::write(debug_mesh_file);
            } catch (...) {}
            
            return EXIT_FAILURE;
        } catch(...) {
            std::cerr << "Unknown error during mesh generation" << std::endl;
            return EXIT_FAILURE;
        }
        std::cout << "Mesh generation completed." << std::endl;

        // --- Export Mesh ---
        std::cout << "Writing mesh to " << output_msh << "..." << std::endl;
        gmsh::option::setNumber("Mesh.Binary", 1);
        gmsh::option::setNumber("Mesh.MshFileVersion", 4.1);
        try { 
            gmsh::write(output_msh); 
        } catch (const std::exception& e) {
            std::cerr << "Error writing mesh file: " << e.what() << std::endl;
            return EXIT_FAILURE;
        } catch(...) {
            std::cerr << "Unknown error writing mesh file" << std::endl;
            return EXIT_FAILURE;
        }
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

    // --- Finalize Gmsh ---
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