#!/bin/bash

set -e  # Exit on error

# Check arguments
if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <input_file.stp>"
    exit 1
fi

INPUT_FILE="$1"
INPUT_BASE="${INPUT_FILE%.*}"

# Get absolute path
ABSOLUTE_INPUT=$(realpath "$INPUT_FILE")

# Create output file paths for different formats
BREP_OUTPUT="${INPUT_BASE}.brep"
STL_OUTPUT="${INPUT_BASE}.stl"
IGES_OUTPUT="${INPUT_BASE}.igs"
OBJ_OUTPUT="${INPUT_BASE}.obj"

echo "Converting $INPUT_FILE to multiple formats..."

# Create a temporary conversion script
TMP_SCRIPT=$(mktemp --suffix=.geo)

cat <<EOT > $TMP_SCRIPT
// Geometry conversion script

// Enhance import quality
Geometry.OCCFixDegenerated = 1;
Geometry.OCCFixSmallEdges = 1;
Geometry.OCCFixSmallFaces = 1;
Geometry.OCCSewFaces = 1;
Geometry.OCCMakeSolids = 1;
Geometry.Tolerance = 1e-2;
Geometry.ToleranceBoolean = 1e-2;
Geometry.AutoCoherence = 1;

// Import the geometry
Merge "$ABSOLUTE_INPUT";
CreateGeometry;
Coherence;

// Export to different formats
Save "$BREP_OUTPUT";
Save "$STL_OUTPUT";
Save "$IGES_OUTPUT";
Save "$OBJ_OUTPUT";

// Done
Exit;
EOT

echo "Running geometry conversions..."
gmsh "$TMP_SCRIPT" -

# Clean up temp file
rm "$TMP_SCRIPT"

# Check which files were created successfully
echo "Conversion results:"
for FILE in "$BREP_OUTPUT" "$STL_OUTPUT" "$IGES_OUTPUT" "$OBJ_OUTPUT"; do
    if [ -f "$FILE" ]; then
        echo "  ✓ Created: $FILE"
    else
        echo "  ✗ Failed:  $FILE"
    fi
done

# Suggest next steps
echo ""
echo "Try meshing with one of these formats:"
echo "  ./direct_mesh.sh $BREP_OUTPUT ${INPUT_BASE}_brep.msh"
echo "  ./direct_mesh.sh $STL_OUTPUT ${INPUT_BASE}_stl.msh"
echo "  ./direct_mesh.sh $IGES_OUTPUT ${INPUT_BASE}_iges.msh"
