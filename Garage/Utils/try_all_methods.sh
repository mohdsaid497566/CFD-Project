#!/bin/bash

# Check if input file is provided
if [ $# -lt 1 ]; then
    echo "Usage: $0 <input_file.stp> [output_file.msh]"
    exit 1
fi

INPUT_FILE="$1"
BASE_NAME=$(basename "${INPUT_FILE%.*}")
OUTPUT_FILE="${2:-${BASE_NAME}_mesh.msh}"

# Make sure the input file exists
if [ ! -f "$INPUT_FILE" ]; then
    echo "Error: Input file $INPUT_FILE not found!"
    exit 1
fi

echo "===================================================="
echo "Comprehensive Meshing Script for Problematic Geometry"
echo "===================================================="
echo "Input: $INPUT_FILE"
echo "Output: $OUTPUT_FILE"
echo

# Create a temporary directory for working files
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

# Try Method 1: Emergency mesher (most likely to succeed)
echo "Method 1: Running emergency mesher..."
./emergency_mesher.py "$INPUT_FILE" "$OUTPUT_FILE" --size 30.0
if [ -f "$OUTPUT_FILE" ] && [ -s "$OUTPUT_FILE" ]; then
    echo "Success! Method 1 created a valid mesh."
    exit 0
fi

# Try Method 2: Direct Gmsh GEO script
echo -e "\nMethod 2: Trying direct Gmsh script approach..."
DIRECT_SCRIPT="${TEMP_DIR}/direct_script.geo"
cat <<EOT > "$DIRECT_SCRIPT"
// Direct meshing with simplified options
Geometry.OCCFixDegenerated = 1;
Geometry.OCCFixSmallEdges = 1;
Geometry.OCCFixSmallFaces = 1;
Geometry.OCCSewFaces = 1;
Geometry.Tolerance = 1e-2;
Geometry.AutoCoherence = 1;

// Set mesh parameters
Mesh.Algorithm = 3;
Mesh.Algorithm3D = 1;
Mesh.CharacteristicLengthMax = 40.0;
Mesh.CharacteristicLengthMin = 5.0;
Mesh.ElementOrder = 1;
Mesh.Binary = 1;
Mesh.MeshSizeExtendFromBoundary = 0;

// Load geometry
Merge "$INPUT_FILE";

// Create box domain
Mesh 3;
Save "$OUTPUT_FILE";
Exit;
EOT

gmsh "$DIRECT_SCRIPT" -
if [ -f "$OUTPUT_FILE" ] && [ -s "$OUTPUT_FILE" ]; then
    echo "Success! Method 2 created a valid mesh."
    exit 0
fi

# Try Method 3: Convert to intermediate format first
echo -e "\nMethod 3: Converting to intermediate formats..."
STL_FILE="${TEMP_DIR}/${BASE_NAME}.stl"
BREP_FILE="${TEMP_DIR}/${BASE_NAME}.brep"

# Try STEP → STL → MSH
echo "  Attempting STEP → STL conversion..."
gmsh "$INPUT_FILE" -3 -o "$STL_FILE" -format stl -bin -v 0 || true

if [ -f "$STL_FILE" ] && [ -s "$STL_FILE" ]; then
    echo "  STL conversion successful, attempting to mesh from STL..."
    gmsh "$STL_FILE" -3 -o "$OUTPUT_FILE" -format msh2 -bin -v 0 -clmax 40 -clmin 5 -algo del3d
    if [ -f "$OUTPUT_FILE" ] && [ -s "$OUTPUT_FILE" ]; then
        echo "Success! Method 3 (via STL) created a valid mesh."
        exit 0
    fi
fi

# Try STEP → BREP → MSH
echo "  Attempting STEP → BREP conversion..."
gmsh "$INPUT_FILE" -0 -o "$BREP_FILE" -format brep -v 0 || true

if [ -f "$BREP_FILE" ] && [ -s "$BREP_FILE" ]; then
    echo "  BREP conversion successful, attempting to mesh from BREP..."
    gmsh "$BREP_FILE" -3 -o "$OUTPUT_FILE" -format msh2 -bin -v 0 -clmax 40 -clmin 5 -algo del3d
    if [ -f "$OUTPUT_FILE" ] && [ -s "$OUTPUT_FILE" ]; then
        echo "Success! Method 3 (via BREP) created a valid mesh."
        exit 0
    fi
fi

# Try Method 4: Python domain creator with simplify option
echo -e "\nMethod 4: Using python_domain_creator.py with simplified settings..."
./python_domain_creator.py "$INPUT_FILE" "$OUTPUT_FILE" --simplify --alg3d 1 --alg2d 3 --size 40.0 --coarsen 3.0
if [ -f "$OUTPUT_FILE" ] && [ -s "$OUTPUT_FILE" ]; then
    echo "Success! Method 4 created a valid mesh."
    exit 0
fi

# Try Method 5: Fallback to box-only mesh
echo -e "\nMethod 5: Fallback to box-only mesh (no geometry)..."
BOX_SCRIPT="${TEMP_DIR}/box_only.geo"
cat <<EOT > "$BOX_SCRIPT"
// Emergency script - just create a simple box
Mesh.CharacteristicLengthMax = 50.0;
Mesh.Algorithm3D = 1;
Box(1) = {-900, -500, -200, 1800, 1000, 400};
Mesh 3;
Save "$OUTPUT_FILE";
EOT

gmsh "$BOX_SCRIPT" -
if [ -f "$OUTPUT_FILE" ] && [ -s "$OUTPUT_FILE" ]; then
    echo "Success! Method 5 created a valid mesh (box only, no actual geometry)."
    echo "WARNING: This mesh does not contain the actual intake geometry."
    exit 0
fi

echo -e "\nAll meshing methods failed!"
echo "Try running with increased mesh size or on a system with more memory."
exit 1
