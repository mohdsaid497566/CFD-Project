#!/bin/bash
set -e

# Default input file
INPUT_FILE="${1:-INTAKE3D.stp}"
OUTPUT_FILE="${2:-${INPUT_FILE%.*}_mesh.msh}"

# Get system information
MEM_TOTAL_KB=$(grep MemTotal /proc/meminfo | awk '{print $2}')
MEM_TOTAL_GB=$(echo "scale=2; $MEM_TOTAL_KB / 1024 / 1024" | bc)
MEM_AVAIL_KB=$(grep MemAvailable /proc/meminfo | awk '{print $2}')
MEM_AVAIL_GB=$(echo "scale=2; $MEM_AVAIL_KB / 1024 / 1024" | bc)

# Determine optimal thread count based on available memory
if command -v nproc &> /dev/null; then
    MAX_THREADS=$(nproc)
else
    MAX_THREADS=4
fi

# Scale thread count based on available memory to avoid OOM
if (( $(echo "$MEM_AVAIL_GB < 4" | bc -l) )); then
    # Very limited memory
    THREADS=2
    MESH_SIZE=20.0
    COARSENING_FACTOR=3.0
    echo "Limited memory environment detected ($MEM_AVAIL_GB GB available). Using minimal settings."
elif (( $(echo "$MEM_AVAIL_GB < 8" | bc -l) )); then
    # Limited memory
    THREADS=$(( MAX_THREADS / 2 < 4 ? MAX_THREADS / 2 : 4 ))
    MESH_SIZE=20.0
    COARSENING_FACTOR=2.0
    echo "Low memory environment detected ($MEM_AVAIL_GB GB available). Reducing resource usage."
elif (( $(echo "$MEM_AVAIL_GB < 16" | bc -l) )); then
    # Moderate memory
    THREADS=$(( MAX_THREADS * 3 / 4 ))
    MESH_SIZE=15.0
    COARSENING_FACTOR=1.5
    echo "Moderate memory environment detected ($MEM_AVAIL_GB GB available)."
else
    # High memory
    THREADS=$MAX_THREADS
    MESH_SIZE=10.0
    COARSENING_FACTOR=1.0
    echo "High memory environment detected ($MEM_AVAIL_GB GB available)."
fi

# Set memory environment variables
export OMP_NUM_THREADS=$THREADS
export OMP_STACKSIZE="64M"

echo "Input: $INPUT_FILE"
echo "Output: $OUTPUT_FILE"
echo "Using $THREADS out of $MAX_THREADS available threads"
echo "Mesh size: ${MESH_SIZE} (coarsening factor: ${COARSENING_FACTOR}x)"

# Create a simple direct meshing script - this approach works better for problematic files
DIRECT_SCRIPT=$(mktemp --suffix=.geo)
cat <<EOT > "$DIRECT_SCRIPT"
// Direct meshing script for INTAKE3D.stp
// Set options for robust, low-memory meshing

// General options
General.NumThreads = $THREADS;
General.ExpertMode = 1;
General.Terminal = 1;

// Mesh options
Mesh.Algorithm = 3; // MeshAdapt
Mesh.Algorithm3D = 1; // Delaunay
Mesh.CharacteristicLengthMax = $MESH_SIZE;
Mesh.CharacteristicLengthMin = $(echo "$MESH_SIZE / 8.0" | bc);
Mesh.ElementOrder = 1; // Linear elements
Mesh.OptimizeNetgen = 0; // Disable Netgen to save memory
Mesh.Optimize = 1; // Basic optimization
Mesh.OptimizeThreshold = 0.3;
Mesh.Binary = 1;
Mesh.MeshSizeFromPoints = 0;
Mesh.MeshSizeFromCurvature = 0;
Mesh.MeshSizeExtendFromBoundary = 0;
Mesh.SaveAll = 1;

// Geometry healing
Geometry.OCCFixDegenerated = 1;
Geometry.OCCFixSmallEdges = 1;
Geometry.OCCFixSmallFaces = 1;
Geometry.OCCSewFaces = 1;
Geometry.OCCMakeSolids = 1;
Geometry.Tolerance = 1e-2;
Geometry.ToleranceBoolean = 1e-2;
Geometry.AutoCoherence = 1;

// Import file and create domain
Printf("Importing geometry...");
Merge "$INPUT_FILE";
Coherence;

// Get bounding box
bb() = BoundingBox;
xmin = bb(0); ymin = bb(1); zmin = bb(2);
xmax = bb(3); ymax = bb(4); zmax = bb(5);

// Center and size
cx = (xmax + xmin) / 2;
cy = (ymax + ymin) / 2;
cz = (zmax + zmin) / 2;
dx = xmax - xmin;
dy = ymax - ymin;
dz = zmax - zmin;

// Ensure non-zero dimensions
maxDim = Max(dx, Max(dy, dz));
If(dx < 0.01 * maxDim)
  dx = maxDim;
EndIf
If(dy < 0.01 * maxDim)
  dy = maxDim;
EndIf
If(dz < 0.01 * maxDim)
  dz = maxDim;
EndIf

// Create fluid domain box
Printf("Creating fluid domain...");
Box(100000) = {cx - 5*dx/2, cy - 5*dy/2, cz - 5*dz/2, 5*dx, 5*dy, 5*dz};

// Generate mesh
Printf("Generating mesh...");
Mesh.MeshSizeFromParametricPoints = 0;
Mesh 3;

// Save mesh
Save "$OUTPUT_FILE";
Exit;
EOT

echo "Running direct Gmsh script..."
gmsh "$DIRECT_SCRIPT" -

# Check if successful
if [ -f "$OUTPUT_FILE" ]; then
    echo "Success! Mesh created at $OUTPUT_FILE"
    rm "$DIRECT_SCRIPT"
    exit 0
fi

echo "Direct method failed. Trying simplified approach..."

# Create simplified script as fallback
SIMPLE_SCRIPT=$(mktemp --suffix=.geo)
cat <<EOT > "$SIMPLE_SCRIPT"
// Ultra-simplified meshing script - just create a box without importing the geometry
// This will at least provide a working mesh file

// Set minimal mesh size for speed
Mesh.CharacteristicLengthMin = $(echo "$MESH_SIZE * 0.5" | bc);
Mesh.CharacteristicLengthMax = $(echo "$MESH_SIZE * 2.0" | bc);
Mesh.Algorithm = 3; // MeshAdapt
Mesh.Algorithm3D = 1; // Delaunay
Mesh.OptimizeNetgen = 0;
Mesh.ElementOrder = 1;
Mesh.Binary = 1;

// Create simple box
Box(1) = {-900, -500, -200, 1800, 1000, 400};
Mesh 3;
Save "$OUTPUT_FILE";
Exit;
EOT

echo "Attempting fallback with simplified mesh..."
gmsh "$SIMPLE_SCRIPT" -

# Clean up
rm "$DIRECT_SCRIPT" "$SIMPLE_SCRIPT"

if [ -f "$OUTPUT_FILE" ]; then
    echo "Created a simplified mesh at $OUTPUT_FILE"
    echo "Warning: This mesh does NOT include the actual geometry"
    echo "It's just a placeholder box that can be used for testing"
    exit 0
else
    echo "All meshing attempts failed."
    exit 1
fi
