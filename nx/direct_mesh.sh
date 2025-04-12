#!/bin/bash

set -e  # Exit on error

# Check arguments
if [ "$#" -lt 2 ]; then
    echo "Usage: $0 <input_file.stp> <output_file.msh>"
    exit 1
fi

INPUT_FILE="$1"
OUTPUT_FILE="$2"

# Get absolute paths
ABSOLUTE_INPUT=$(realpath "$INPUT_FILE")
ABSOLUTE_OUTPUT=$(realpath "$OUTPUT_FILE")

# Create a temporary Gmsh script for importing and meshing directly
TMP_GEO=$(mktemp --suffix=.geo)

cat <<EOT > $TMP_GEO
// Direct geometry and meshing script - bypasses OCC fragmentation

// Meshing options
Mesh.Algorithm = 3;  // MeshAdapt algorithm is more robust for problematic geometries
Mesh.Algorithm3D = 4; // Frontal algorithm
Mesh.CharacteristicLengthMin = 0.1;
Mesh.CharacteristicLengthMax = 1.0;
Mesh.ElementOrder = 1;
Mesh.Binary = 1;
Mesh.MeshSizeFactor = 1.0;
Mesh.SaveAll = 1;
Mesh.SaveParametric = 0;
Mesh.ScalingFactor = 1.0;

// Better geometry import settings
Geometry.OCCFixDegenerated = 1;
Geometry.OCCFixSmallEdges = 1;
Geometry.OCCFixSmallFaces = 1;
Geometry.OCCSewFaces = 1;
Geometry.AutoCoherence = 1;
Geometry.Tolerance = 1e-2;

// Step 1: Import the geometry directly
Merge "$ABSOLUTE_INPUT";

// Step 2: Create a new model and synchronize
CreateGeometry;
Coherence;

// Step 3: Generate mesh directly without fragmentation
Mesh 3;

// Step 4: Save the mesh
Save "$ABSOLUTE_OUTPUT";
EOT

echo "Running Gmsh with direct geometric meshing approach..."
gmsh "$TMP_GEO" -

# Clean up temp files
rm "$TMP_GEO"

if [ -f "$OUTPUT_FILE" ]; then
    echo "Success! Created mesh: $OUTPUT_FILE"
else
    echo "Failed to create mesh. Trying alternative approach..."
    
    # Alternative approach - use gmsh command line with specific options
    echo "Running Gmsh command-line meshing..."
    gmsh "$INPUT_FILE" -3 -format msh -v 5 -algo meshadapt -o "$OUTPUT_FILE" -clmin 0.1 -clmax 1.0
    
    if [ -f "$OUTPUT_FILE" ]; then
        echo "Successfully created mesh with alternative approach!"
    else
        echo "All meshing attempts failed."
        exit 1
    fi
fi

echo "You can view the mesh with: gmsh $OUTPUT_FILE"
