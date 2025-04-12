# Intake CFD Project

This repository contains tools for meshing STEP geometry files and preparing them for CFD simulations.

## Quick Start

### Basic Workflow
1. **Mesh the geometry**:
   ```bash
   ./simple_mesh.sh INTAKE3D.stp INTAKE3D_mesh.msh
   ```

2. **Prepare for CFD**:
   ```bash
   ./prepare_for_cfd.sh INTAKE3D_mesh.msh ../cfd_case openfoam
   ```

### Advanced Workflow
1. **Repair problematic geometry**:
   ```bash
   ./repair_step.sh INTAKE3D.stp
   ```

2. **Create a mesh with more options**:
   ```bash
   ./mesh_generator INTAKE3D_repaired.stp INTAKE3D_mesh.msh --base_mesh_size 0.5 --alg_2d 6 --alg_3d 1
   ```

3. **Create boundary layer mesh**:
   ```bash
   ./mesh_generator INTAKE3D_repaired.stp INTAKE3D_mesh.msh --bl_first_layer 0.02 --bl_progression 1.3
   ```

4. **Use Fortran interface with SU2 export**:
   ```bash
   ./compile_fortran.sh gmsh_process.f90
   ./gmsh_process --input INTAKE3D.stp --output mesh.msh --su2
   ```

## Script Descriptions

### Meshing Scripts

- **simple_mesh.sh**: Most robust meshing approach for problematic geometries. Uses optimized meshing parameters and error recovery mechanisms. Tries multiple algorithms if the first attempt fails, automatically adjusting mesh sizing for difficult regions.

- **mesh_intake.sh**: Specialized script for intake manifolds with GPU acceleration support. Implements a multi-stage approach specifically tuned for intake geometry. Uses progressive refinement near important features and can leverage CUDA for large models.

- **create_fluid_domain.sh**: Creates a fluid domain around a geometry by generating a bounding box and performing boolean subtraction. Includes automatic healing of geometry issues and ensures proper distance fields for meshing.

- **direct_mesh.sh**: Direct meshing approach that skips complex preprocessing steps. Useful for already repaired geometries or when boolean operations fail. Focuses on reliability over mesh quality for difficult cases.

- **python_mesher.py**: Python script with GPU acceleration for large models. Features include:
  - CUDA acceleration with pycuda/cupy for complex operations
  - MPI support for multi-node processing
  - Adaptive mesh sizing based on curvature
  - Memory optimization for handling very large models
  - Fall-back mechanisms when operations fail

- **python_domain_creator.py**: Creates a fluid domain with HPC acceleration. Optimized for high-performance computing environments with:
  - Multi-threading via OpenMP
  - CUDA acceleration for large boolean operations
  - Intelligent resource allocation based on model size
  - Advanced healing algorithms for problematic geometry

- **compile_fortran.sh**: Builds a Fortran interface to the Gmsh library. Creates a standalone executable with these capabilities:
  - Import STEP, BREP, STL geometry formats
  - Generate structured and unstructured meshes  
  - Export to multiple formats including MSH and SU2
  - Command-line parameters for mesh configuration
  - Interactive mode for guided mesh creation
  - Built-in mesh quality analysis
  - Usage: `./gmsh_process [options]`

- **absolute_last_resort.sh**: Emergency fallback for problematic files. Creates a simple box mesh when all other methods fail, ensuring you always get a working mesh file for simulation setup testing.

- **convert_geometry.sh**: Converts between geometry formats (STEP, BREP, STL, IGES) to overcome format-specific issues. Implements geometry healing during conversion and provides suggestions for further processing.

- **repair_step.sh**: Specialized tool for fixing common issues in STEP files:
  - Repairs degenerate edges and faces
  - Stitches disconnected surfaces
  - Creates proper solids from surface collections
  - Corrects orientation issues
  - Provides multiple repaired outputs for testing

### CFD Preparation

- **prepare_for_cfd.sh**: Comprehensive tool to prepare meshes for CFD simulation:
  - **OpenFOAM preparation**:
    - Creates complete case directory structure
    - Sets up boundary conditions (inlet, outlet, walls)
    - Configures turbulence models (k-epsilon by default)
    - Creates appropriate field files (U, p, k, epsilon, nut)
    - Generates controlDict, fvSchemes, fvSolution
    - Provides run scripts and Allrun automation
    - Adds ParaView visualization setup

  - **ANSYS Fluent preparation**:
    - Converts mesh to Fluent format
    - Creates journal file with automated setup
    - Sets up solver parameters and numerical schemes
    - Provides initialization settings

  - **Star-CCM+ preparation**:
    - Converts mesh to CGNS format
    - Creates detailed import instructions
    - Provides step-by-step physics model setup guide
    - Includes boundary condition configuration details
    
  - **SU2 preparation**:
    - Automatic export to SU2 format from Fortran interface
    - Direct export with `--su2` flag
    - Configures proper naming for boundary conditions
    - Sets up mesh format for SU2's CFD solver

- **extract_surfaces.py**: Advanced tool for identifying and extracting important features from the mesh:
  - Auto-detects inlets and outlets based on geometry
  - Creates named boundary patches
  - Separates walls into meaningful groups
  - Generates patch sets for specific simulation requirements
  - Supports custom feature extraction via Python API

## Debugging & Troubleshooting

### Command Line Debugging

1. **Enable Gmsh debug output**:
   ```bash
   GMSH_DEBUG=99 ./mesh_intake.sh INTAKE3D.stp
   ```

2. **Track mesh operations step-by-step**:
   ```bash
   GMSH_VERBOSITY=99 ./create_fluid_domain.sh INTAKE3D.stp
   ```

3. **Visualize intermediate results**:
   ```bash
   # Save intermediate steps
   ./simple_mesh.sh INTAKE3D.stp INTAKE3D_mesh.msh --debug
   
   # View intermediate geometry
   gmsh INTAKE3D_temp_*.geo
   ```

### Diagnosing Specific Issues

1. **Broken geometry/topology**:
   ```bash
   # Generate explicit report of geometric issues
   ./repair_step.sh INTAKE3D.stp --diagnose
   
   # Fix common issues and generate report
   ./repair_step.sh INTAKE3D.stp --fix-all --report
   ```

2. **Memory usage tracking**:
   ```bash
   # For low-memory systems
   ./python_domain_creator.py INTAKE3D.stp mesh.msh --track-memory
   
   # Memory-optimized execution
   ./absolute_last_resort.sh INTAKE3D.stp mesh.msh --low-memory
   ```

3. **Boundary layer problems**:
   ```bash
   # Visualize boundary layer setup
   ./mesh_generator INTAKE3D.stp mesh.msh --bl_debug --bl_first_layer 0.02
   
   # Fix common boundary layer issues
   ./mesh_generator INTAKE3D.stp mesh.msh --fix-bl-intersections --bl_first_layer 0.05
   ```

### Common Error Messages

1. **"Boolean operation failed"**:
   - Indicates geometry has self-intersections or gaps
   - Try: `./repair_step.sh INTAKE3D.stp --heal-tolerance 0.01`
   - Or: `./direct_mesh.sh INTAKE3D.stp mesh.msh` (skips boolean operations)

2. **"Out of memory"**:
   - Mesh is too complex for available RAM
   - Try: `./python_domain_creator.py INTAKE3D.stp mesh.msh --coarsen 2.0`
   - Or: `./absolute_last_resort.sh INTAKE3D.stp mesh.msh` (minimal memory usage)

3. **"No surfaces/volumes found"**:
   - Geometry has structural issues
   - Try: `./convert_geometry.sh INTAKE3D.stp` then use the .brep or .stl output
   - Or: `./simple_mesh.sh INTAKE3D.stp mesh.msh --force-2d` (surface mesh only)

### Analyzing Log Files

1. **Extract critical errors from log**:
   ```bash
   ./mesh_intake.sh INTAKE3D.stp mesh.msh 2>&1 | grep -E "Error|Warning|Failed"
   ```

2. **Generate detailed timing report**:
   ```bash
   ./python_mesher.py INTAKE3D.stp mesh.msh --timing-report
   ```

3. **Profile resource usage** (requires GNU time):
   ```bash
   /usr/bin/time -v ./mesh_generator INTAKE3D.stp mesh.msh
   ```

### Recommended Core Workflow

If you encounter persistent issues, use this simplified pipeline that avoids most common problems:

```bash
# 1. Repair and convert geometry
./repair_step.sh INTAKE3D.stp

# 2. Mesh with reliable direct approach
./direct_mesh.sh INTAKE3D_repaired.stp prepped.msh

# 3. Prepare for CFD with standard settings
./prepare_for_cfd.sh prepped.msh ../cfd_case
```

## Build & Installation
- **install_gpu_deps.sh**: Installs GPU acceleration dependencies
- **build_main.sh**: Builds the C++ tools from source
- **compile_fortran.sh**: Builds the Fortran interface and wrapper:
  ```bash
  # Basic usage
  ./compile_fortran.sh gmsh_process.f90
  
  # Run the compiled program
  ./run_gmsh_process.sh
  
  # Command line options for the Fortran interface
  ./gmsh_process --help
  ```

## Common Issues and Solutions

### Meshing Failures
1. **If importing fails**: Use `convert_geometry.sh` to convert to another format
   ```bash 
   ./convert_geometry.sh INTAKE3D.stp
   ./direct_mesh.sh INTAKE3D.brep INTAKE3D_mesh.msh
   ```

2. **If mesh is too large**: Increase the mesh size
   ```bash
   ./mesh_generator INTAKE3D.stp INTAKE3D_mesh.msh --base_mesh_size 1.0
   ```

3. **If boolean operations fail**: Try simplified mesh
   ```bash
   ./absolute_last_resort.sh INTAKE3D.stp box_mesh.msh
   ```

### Memory Issues
- Use progressive meshing approach for large models
- Try different algorithms with `--alg_3d 1` (lowest memory usage)
- For very large models, enable GPU acceleration with `./python_mesher.py --gpu`

## Mesh Quality Optimization
- Use Netgen optimizer (default): `--no_netgen_opt` to disable
- Adjust boundary layers with `--bl_progression` and `--bl_first_layer`
- Try alternative meshing algorithms: `--alg_2d 3 --alg_3d 4` for better quality

## Export Formats
- **MSH format**: Default Gmsh format for all tools
- **SU2 format**: For SU2 CFD solver
  ```bash
  # Using Fortran interface
  ./gmsh_process --input INTAKE3D.stp --output mesh.msh --su2
  
  # Using Python interface
  ./python_mesher.py INTAKE3D.stp mesh.msh --export-su2
  ```
- **OpenFOAM format**: Through prepare_for_cfd.sh
- **Fluent format**: Through prepare_for_cfd.sh with fluent option
- **CGNS format**: For Star-CCM+ and other solvers

## Requirements
- Gmsh with OpenCASCADE support
- Python 3.6+
- OpenMPI (optional, for parallel meshing)
- CUDA toolkit (optional, for GPU acceleration)
- gfortran (optional, for Fortran interface)
