#!/bin/bash

# Check if a file was provided
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 input.stp"
    exit 1
fi

# Get absolute paths for input file
INPUT_FILE="$1"
ABSOLUTE_INPUT=$(realpath "$INPUT_FILE")
OUTPUT_FILE="${ABSOLUTE_INPUT%.*}_repaired.stp"

# Check if input file exists
if [ ! -f "$ABSOLUTE_INPUT" ]; then
    echo "Error: Input file $INPUT_FILE does not exist."
    exit 1
fi

echo "Input: $ABSOLUTE_INPUT"
echo "Output: $OUTPUT_FILE"

# Create a temporary Gmsh script for initial repair
TEMP_SCRIPT=$(mktemp)
cat <<EOT > $TEMP_SCRIPT
// Gmsh script to repair STEP files

// Load the STEP file
Merge "$ABSOLUTE_INPUT";

// Set healing options
Geometry.OCCFixDegenerated = 1;
Geometry.OCCFixSmallEdges = 1;
Geometry.OCCFixSmallFaces = 1;
Geometry.OCCSewFaces = 1;
Geometry.OCCMakeSolids = 1;
Geometry.Tolerance = 1e-3;
Geometry.ToleranceBoolean = 1e-2;
Geometry.MatchMeshTolerance = 1e-2;
Geometry.AutoCoherence = 1;

// This is the key - synchronize before healing
Coherence;

// Export to a new STEP file
Save "$OUTPUT_FILE";
Exit;
EOT

echo "Attempting to repair STEP file using Gmsh..."
gmsh "$TEMP_SCRIPT" -

# Create a script that manually creates a volume from all surfaces in the model
# This approach helps when automatic volume creation fails
VOLUME_SCRIPT=$(mktemp)
cat <<EOT > $VOLUME_SCRIPT
// Gmsh script to manually create a volume from all surfaces

// Load the previously repaired file
Merge "$OUTPUT_FILE";

// Get all surfaces
Printf("Finding all surfaces...");
Geometry.AutoCoherence = 1;
Coherence;

// Create a surface loop from all surfaces
surfLoop = newsl;
AllSurfaces() = Boundary{ Volume{:}; };
If (!#AllSurfaces())
  AllSurfaces() = Surface{:};
EndIf
Printf("Found %g surfaces", #AllSurfaces());

// Create a new volume using all available surfaces
If (#AllSurfaces())
  Surface Loop(surfLoop) = AllSurfaces();
  newVol = newv;
  Volume(newVol) = {surfLoop};
  Printf("Created new volume with tag %g", newVol);
EndIf

// Save manually constructed model
Save "$OUTPUT_FILE";
Exit;
EOT

echo "Creating explicit volume from surfaces..."
gmsh "$VOLUME_SCRIPT" -

# If the file wasn't created or if we want to try STL conversion as well
echo "Trying STL conversion method for extra repair..."
# Create a temporary STL file
TMP_STL=$(mktemp --suffix=.stl)
STL_OUTPUT_FILE="${ABSOLUTE_INPUT%.*}_stl_repaired.stp"

# Try using gmsh to convert to STL (with absolute paths)
echo "Converting to STL..."
gmsh "$OUTPUT_FILE" -3 -o "$TMP_STL" -format stl -bin -v 1

if [ -f "$TMP_STL" ] && [ -s "$TMP_STL" ]; then
    echo "Successfully converted to STL. Converting back to STEP..."
    gmsh "$TMP_STL" -3 -o "$STL_OUTPUT_FILE" -format step -v 1
    
    if [ -f "$STL_OUTPUT_FILE" ]; then
        echo "STL repair successful! Try using both repaired files:"
        echo "  ./mesh_generator \"$OUTPUT_FILE\" \"${OUTPUT_FILE%.*}.msh\" --alg_2d 3 --alg_3d 4"
        echo "  ./mesh_generator \"$STL_OUTPUT_FILE\" \"${STL_OUTPUT_FILE%.*}.msh\" --alg_2d 3 --alg_3d 4"
    else
        echo "Failed to convert back to STEP."
    fi
fi

# Clean up
rm "$TEMP_SCRIPT" "$VOLUME_SCRIPT"
[ -f "$TMP_STL" ] && rm "$TMP_STL"

# Add success suggestions
echo ""
echo "If the repaired files still have issues, try:"
echo "  ./simple_mesh.sh \"$OUTPUT_FILE\" \"${OUTPUT_FILE%.*}.msh\""
echo ""
echo "Or these mesh generator options:"
echo "  --alg_2d 6 --alg_3d 1 --base_mesh_size 1.0"
echo "  --alg_2d 3 --alg_3d 4 --base_mesh_size 0.8"
