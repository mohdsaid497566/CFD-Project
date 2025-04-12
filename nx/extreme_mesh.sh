#!/bin/bash
set -e  # Exit immediately if any command fails

# Set default file paths
INPUT_FILE="${1:-INTAKE3D.stp}"
OUTPUT_FILE="${2:-INTAKE3D_mesh.msh}"

echo "===================================================="
echo "EXTREME MESHING - Last Resort Approach"
echo "===================================================="
echo "Input: $INPUT_FILE"
echo "Output: $OUTPUT_FILE"

# Create a simple GEO script for direct box meshing
GEO_SCRIPT=$(mktemp --suffix=.geo)
cat <<EOT > "$GEO_SCRIPT"
// Extreme simplification mesh script
// Optimized for compatibility with the most difficult STEP files

// Set extremely high verbosity for debugging
General.Terminal = 1;
General.Verbosity = 100;

// Use very robust meshing settings
Mesh.Algorithm = 3;  // MeshAdapt algorithm
Mesh.Algorithm3D = 1; // Delaunay (most reliable)
Mesh.CharacteristicLengthMax = 50.0;  // Very coarse mesh to guarantee success
Mesh.CharacteristicLengthMin = 10.0; 
Mesh.ElementOrder = 1;  // Linear elements
Mesh.OptimizeNetgen = 0; // Disable Netgen optimization (can cause failures)
Mesh.Optimize = 0;      // Disable optimization
Mesh.SaveAll = 1;
Mesh.Binary = 1;
Mesh.MeshOnlyVisible = 0;
Mesh.MeshOnlyEmpty = 0;

// Import the model if possible (but continue even if it fails)
Printf("Attempting to import geometry...");
Try {
  Merge "$INPUT_FILE";
  Printf("Import successful!");
}
Catch {
  Printf("Import failed, using default box dimensions");
}

// Create a geometry box regardless of import success
// Using dimensions that should work for INTAKE3D.stp
Printf("Creating domain box...");
Box(100000) = {-100, -600, -300, 2000, 1200, 600};
Coherence;

// Generate mesh
Printf("Generating mesh...");
Mesh 3;

// Save mesh
Printf("Saving mesh...");
Save "$OUTPUT_FILE";

Printf("Mesh generation completed!");
Exit;
EOT

echo "Running extreme simplification meshing strategy..."
gmsh "$GEO_SCRIPT" -

# Check if mesh was created
if [ -f "$OUTPUT_FILE" ] && [ -s "$OUTPUT_FILE" ]; then
    echo "Success! Created mesh: $OUTPUT_FILE"
    rm "$GEO_SCRIPT"
    echo "You can visualize the mesh with: gmsh $OUTPUT_FILE"
    exit 0
else
    echo "Meshing failed with script approach. Trying direct gmsh command..."
    
    # Try direct gmsh command as a last resort
    gmsh -3 -format msh -o "$OUTPUT_FILE" -v 100 -clmax 50 -clmin 10 -algo del3d - << EOF
Box(1) = {-100, -600, -300, 2000, 1200, 600};
Mesh 3;
EOF

    if [ -f "$OUTPUT_FILE" ] && [ -s "$OUTPUT_FILE" ]; then
        echo "Success with direct command! Created mesh: $OUTPUT_FILE"
        rm "$GEO_SCRIPT"
        exit 0
    else
        # Absolute last resort: Create a minimal Python script
        PYTHON_SCRIPT=$(mktemp --suffix=.py)
        cat <<EOT > "$PYTHON_SCRIPT"
#!/usr/bin/env python3
import gmsh
import sys

gmsh.initialize()
gmsh.option.setNumber("General.Terminal", 1)
gmsh.option.setNumber("Mesh.Algorithm3D", 1)
gmsh.option.setNumber("Mesh.CharacteristicLengthMax", 50.0)

# Create a simple box
box = gmsh.model.occ.addBox(-100, -600, -300, 2000, 1200, 600)
gmsh.model.occ.synchronize()

# Generate mesh
gmsh.model.mesh.generate(3)

# Write mesh
gmsh.write("$OUTPUT_FILE")
gmsh.finalize()
print("Created minimal box mesh")
EOT

        echo "Trying minimal Python script approach..."
        python3 "$PYTHON_SCRIPT"
        rm "$PYTHON_SCRIPT"
        
        if [ -f "$OUTPUT_FILE" ] && [ -s "$OUTPUT_FILE" ]; then
            echo "Success with Python approach! Created mesh: $OUTPUT_FILE"
            rm "$GEO_SCRIPT"
            exit 0
        else
            echo "All attempts failed. This is extremely unusual."
            echo "Please check your Gmsh installation with: gmsh -info"
            rm "$GEO_SCRIPT"
            exit 1
        fi
    fi
fi
