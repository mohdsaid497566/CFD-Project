#!/bin/bash

# Check if the correct number of arguments were passed
if [ "$#" -lt 2 ]; then
    echo "Usage: $0 <input_file> <output_file.msh> [options]"
    exit 1
fi

INPUT_FILE="$1"
OUTPUT_FILE="$2"
shift 2

# Get absolute paths
ABSOLUTE_INPUT=$(realpath "$INPUT_FILE")

# Check if input file exists
if [ ! -f "$ABSOLUTE_INPUT" ]; then
    echo "Error: Input file $INPUT_FILE does not exist."
    exit 1
fi

# Create a temporary Gmsh script
TEMP_SCRIPT=$(mktemp)
cat <<EOT > $TEMP_SCRIPT
// Simple meshing script for problematic geometries

// Set meshing options for extreme robustness
Mesh.Algorithm = 6;  // Frontal-Delaunay algorithm 
Mesh.Algorithm3D = 4; // Frontal algorithm
Mesh.CharacteristicLengthMin = 0.05;
Mesh.CharacteristicLengthMax = 0.8;
Mesh.CharacteristicLengthFromCurvature = 1;
Mesh.CharacteristicLengthFromPoints = 1;
Mesh.MinimumCirclePoints = 6;
Mesh.MinimumCurvePoints = 3;
Mesh.AngleToleranceFacetOverlap = 0.8;
Mesh.AnisoMax = 1000.0;
Mesh.SaveAll = 1;
Mesh.Binary = 1;

// Special options for difficult geometries
Mesh.HighOrderOptimize = 0;
Mesh.OptimizeNetgen = 0; // Skip Netgen optimizer which can fail
Mesh.ElementOrder = 1;  // Linear elements are more robust
Mesh.SecondOrderIncomplete = 0;
Mesh.SecondOrderLinear = 1;
Mesh.Smoothing = 3;
Mesh.SmoothNormals = 1;
Mesh.SmoothCrossField = 1;
Mesh.SmoothRatio = 1.8;
Mesh.MeshSizeExtendFromBoundary = 0;
Mesh.MeshSizeFactor = 1.0;

// Ignore faces without boundary
Mesh.CheckSurfaceMesh = 0;
Mesh.CheckVolumeMesh = 0;
Mesh.IgnorePeriodicity = 1;

// Geometry healing options
Geometry.Tolerance = 1e-2; // Use more relaxed tolerance
Geometry.OCCFixDegenerated = 1;
Geometry.OCCFixSmallEdges = 1;
Geometry.OCCFixSmallFaces = 1;
Geometry.OCCSewFaces = 1;
Geometry.OCCMakeSolids = 1;
Geometry.AutoCoherence = 1;
Geometry.ScalingFactor = 1.0;

// Load and synchronize the model
Merge "$ABSOLUTE_INPUT";
Coherence;

// Create geometry
CreateGeometry;
Coherence;

// Get all entities and check for volume
Printf("Checking for volumes...");
AllVolumes() = Volume{:};
If (!#AllVolumes())
  // Try to create a volume from all surfaces
  Printf("No volumes found, trying to create one...");
  AllSurfaces() = Surface{:};
  If (#AllSurfaces())
    surfLoop = newsl;
    Surface Loop(surfLoop) = AllSurfaces();
    newVol = newv;
    Volume(newVol) = {surfLoop};
    Printf("Created new volume with tag %g", newVol);
  EndIf
EndIf

// Generate mesh
Mesh.SaveAll = 1;
Mesh 1;
Mesh 2;
Mesh 3;

// Write mesh
Save "$OUTPUT_FILE";
Exit;
EOT

# Run the script with Gmsh
echo "Creating mesh with robust options..."
gmsh "$TEMP_SCRIPT" -

# Clean up
rm "$TEMP_SCRIPT"

# Check if the mesh was created
if [ -f "$OUTPUT_FILE" ]; then
    echo "Success! Mesh created as $OUTPUT_FILE"
    exit 0
else
    echo "Failed to create mesh. Trying alternative approach..."
    
    # Try an alternative approach with tetrahedral meshing directly
    ALT_SCRIPT=$(mktemp)
    cat <<EOT > $ALT_SCRIPT
// Alternative meshing approach with tetgen
Merge "$ABSOLUTE_INPUT";
Mesh.Algorithm3D = 1; // Delaunay (tetgen)
Mesh.MeshSizeMin = 0.1;
Mesh.MeshSizeMax = 1.0;
Mesh.CharacteristicLengthFactor = 1.0;
Mesh 3;
Save "$OUTPUT_FILE";
Exit;
EOT
    
    echo "Trying tetgen meshing algorithm..."
    gmsh "$ALT_SCRIPT" -
    
    rm "$ALT_SCRIPT"
    
    if [ -f "$OUTPUT_FILE" ]; then
        echo "Success with alternative approach! Mesh created as $OUTPUT_FILE"
        exit 0
    else
        echo "All meshing attempts failed."
        exit 1
    fi
fi
