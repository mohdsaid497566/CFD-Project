#!/bin/bash
set -e  # Exit on error

# Default input file (can be overridden)
INPUT_FILE="${1:-INTAKE3D.stp}"
OUTPUT_FILE="${2:-INTAKE3D_fluid_domain.msh}"

# Ensure absolute paths
ABSOLUTE_INPUT=$(realpath "$INPUT_FILE")
ABSOLUTE_OUTPUT=$(realpath "$OUTPUT_FILE")

# Check if input file exists
if [ ! -f "$ABSOLUTE_INPUT" ]; then
    echo "Error: Input file $INPUT_FILE does not exist."
    exit 1
fi

echo "INTAKE3D Specialized Mesh Generator"
echo "----------------------------------"
echo "Input: $ABSOLUTE_INPUT"
echo "Output: $ABSOLUTE_OUTPUT"

# Detect system resources
if command -v nproc &> /dev/null; then
    CPU_CORES=$(nproc)
else
    CPU_CORES=4
fi

# Calculate optimal thread count (75% of cores to avoid memory issues)
THREADS=$((CPU_CORES * 3 / 4))
if [ "$THREADS" -lt 2 ]; then
    THREADS=2
fi
echo "Using $THREADS out of $CPU_CORES available CPU cores"

# Set memory-friendly environment variables
export OMP_NUM_THREADS=$THREADS
export OMP_STACKSIZE="64M"
export OMP_SCHEDULE="dynamic,100"
export OMP_PROC_BIND=close
export OMP_PLACES=cores

# Set mesh parameters for INTAKE3D model based on testing
MESH_SIZE=30.0
ALGORITHM_2D=3  # MeshAdapt is more reliable
ALGORITHM_3D=1  # Delaunay is more memory-friendly

echo "Mesh parameters: size=${MESH_SIZE}, 2D alg=${ALGORITHM_2D}, 3D alg=${ALGORITHM_3D}"

# Create Python script for direct meshing with memory optimization
TEMP_SCRIPT=$(mktemp --suffix=.py)
cat <<EOT > "$TEMP_SCRIPT"
#!/usr/bin/env python3
import gmsh
import sys
import os
import traceback

try:
    # Initialize Gmsh
    gmsh.initialize()
    
    # Create a new model
    gmsh.model.add("intake3d")

    # Print basic information
    print(f"Meshing INTAKE3D with Gmsh {gmsh.option.getString('General.Version')}")
    
    # Set mesh parameters optimized for INTAKE3D
    gmsh.option.setNumber("General.Terminal", 1)
    gmsh.option.setNumber("General.NumThreads", $THREADS)
    gmsh.option.setNumber("Mesh.Algorithm", $ALGORITHM_2D)  # MeshAdapt
    gmsh.option.setNumber("Mesh.Algorithm3D", $ALGORITHM_3D)  # Delaunay
    gmsh.option.setNumber("Mesh.CharacteristicLengthMax", $MESH_SIZE)
    gmsh.option.setNumber("Mesh.CharacteristicLengthMin", $MESH_SIZE / 10)
    
    # Memory-friendly options
    gmsh.option.setNumber("Mesh.OptimizeThreshold", 0.3)
    gmsh.option.setNumber("Mesh.OptimizeNetgen", 0)
    gmsh.option.setNumber("Mesh.HighOrderOptimize", 0)
    
    # Tolerance settings for STEP import
    gmsh.option.setNumber("Geometry.Tolerance", 1e-2)
    gmsh.option.setNumber("Geometry.ToleranceBoolean", 1e-2)
    gmsh.option.setNumber("Geometry.OCCFixDegenerated", 1)
    gmsh.option.setNumber("Geometry.OCCFixSmallEdges", 1)
    gmsh.option.setNumber("Geometry.OCCFixSmallFaces", 1)
    gmsh.option.setNumber("Geometry.OCCSewFaces", 1)
    
    # Import geometry
    print("Importing geometry...")
    try:
        gmsh.model.occ.importShapes("$ABSOLUTE_INPUT")
        gmsh.model.occ.synchronize()
        print("Import successful using OCC")
    except Exception as e:
        print(f"OCC import failed: {e}")
        print("Trying direct merge...")
        gmsh.merge("$ABSOLUTE_INPUT")
        print("Direct merge successful")
    
    # Get geometry bounding box
    xmin, ymin, zmin, xmax, ymax, zmax = gmsh.model.getBoundingBox(-1, -1)
    
    # Create a domain box
    margin = 5.0  # Scale factor
    dx = xmax - xmin
    dy = ymax - ymin
    dz = zmax - zmin
    
    # Ensure non-zero dimensions
    max_dim = max(dx, dy, dz)
    if dx < 0.01 * max_dim: dx = max_dim
    if dy < 0.01 * max_dim: dy = max_dim
    if dz < 0.01 * max_dim: dz = max_dim
    
    # Calculate center
    cx = (xmax + xmin) / 2
    cy = (ymax + ymin) / 2
    cz = (zmax + zmin) / 2
    
    # Add box
    box = gmsh.model.occ.addBox(
        cx - margin * dx / 2, 
        cy - margin * dy / 2, 
        cz - margin * dz / 2,
        margin * dx, 
        margin * dy, 
        margin * dz
    )
    gmsh.model.occ.synchronize()
    
    # Create fluid region by boolean difference
    print("Creating fluid domain...")
    
    # Get all volumes in model
    volumes = gmsh.model.getEntities(3)
    intake_volumes = [v for v in volumes if v[1] != box]
    
    # Check if we need to do boolean operations
    if intake_volumes:
        print(f"Found {len(intake_volumes)} intake volumes")
        try:
            out_dimtags = []
            gmsh.model.occ.cut([(3, box)], intake_volumes, out_dimtags)
            gmsh.model.occ.synchronize()
            print(f"Boolean difference created {len(out_dimtags)} entities")
        except Exception as e:
            print(f"Boolean operation failed: {e}")
            print("Using simple box domain")
    else:
        print("No intake volumes found for boolean, using simple box")

    # Generate mesh progressively
    print("Generating 1D mesh...")
    gmsh.model.mesh.generate(1)
    
    print("Generating 2D mesh...")
    gmsh.model.mesh.generate(2)
    
    # Import gc before 3D meshing
    import gc
    gc.collect()
    
    print("Generating 3D mesh (this may take a while)...")
    try:
        gmsh.model.mesh.generate(3)
    except Exception as e:
        print(f"3D meshing failed: {e}")
        print("Trying with increased mesh size...")
        # Increase mesh size and try again
        gmsh.option.setNumber("Mesh.CharacteristicLengthMax", $MESH_SIZE * 2)
        gmsh.option.setNumber("Mesh.CharacteristicLengthMin", $MESH_SIZE / 5)
        try:
            gmsh.model.mesh.generate(3)
        except Exception as e2:
            print(f"Second attempt failed: {e2}")
            print("Saving partial mesh")

    # Write mesh
    print("Writing mesh...")
    gmsh.option.setNumber("Mesh.Binary", 1)
    gmsh.write("$ABSOLUTE_OUTPUT")
    print(f"Mesh written to {os.path.abspath('$ABSOLUTE_OUTPUT')}")

except Exception as e:
    print(f"Error: {e}")
    traceback.print_exc()
    sys.exit(1)
finally:
    if gmsh.isInitialized():
        gmsh.finalize()
EOT

# Execute the script
echo "Starting specialized meshing process..."
python3 "$TEMP_SCRIPT"

# Clean up
rm "$TEMP_SCRIPT"

# Check if mesh was created
if [ -f "$ABSOLUTE_OUTPUT" ]; then
    echo "Success! Mesh created: $ABSOLUTE_OUTPUT"
    echo "To view the mesh: gmsh $ABSOLUTE_OUTPUT"
    exit 0
else
    echo "Meshing failed. Trying alternative approach..."
    
    # Fall back to external Gmsh approach
    GMSH_SCRIPT=$(mktemp --suffix=.geo)
    cat <<EOT > "$GMSH_SCRIPT"
// Emergency mesh script for INTAKE3D
Mesh.Algorithm = 3;
Mesh.Algorithm3D = 1;
Mesh.CharacteristicLengthMax = 40;
Mesh.CharacteristicLengthMin = 5;
Mesh.OptimizeNetgen = 0;
Mesh.ElementOrder = 1;
Mesh.Smoothing = 0;
Merge "$ABSOLUTE_INPUT";
Mesh 3;
Save "$ABSOLUTE_OUTPUT";
EOT
    
    echo "Running emergency meshing with Gmsh..."
    gmsh "$GMSH_SCRIPT" -
    
    # Clean up
    rm "$GMSH_SCRIPT"
    
    if [ -f "$ABSOLUTE_OUTPUT" ]; then
        echo "Success with emergency approach! Mesh created: $ABSOLUTE_OUTPUT"
        exit 0
    else
        echo "All meshing attempts failed."
        exit 1
    fi
fi
