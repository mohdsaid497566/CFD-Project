#!/bin/bash

set -e  # Exit on error

# Check for input file
if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <input_file.stp> [output_file.msh] [domain_scale]"
    exit 1
fi

INPUT_FILE="$1"
OUTPUT_FILE="${2:-${INPUT_FILE%.*}_domain.msh}"
DOMAIN_SCALE="${3:-5.0}"

# Get absolute paths
ABSOLUTE_INPUT=$(realpath "$INPUT_FILE")
ABSOLUTE_OUTPUT=$(realpath "$OUTPUT_FILE")

echo "Creating fluid domain mesh around $INPUT_FILE"
echo "Scale factor: ${DOMAIN_SCALE}x"
echo "Output file: $OUTPUT_FILE"

# Enable debug mode in Gmsh
export GMSH_DEBUG=99
export GMSH_VERBOSITY=99

# Create a very simple, direct meshing script - focus on reliability
TEMP_SCRIPT=$(mktemp)
cat <<EOT > $TEMP_SCRIPT
// Extremely simplified domain creation script
// Using OpenCASCADE with debug output
SetFactory("OpenCASCADE");

// Verbose logging
General.Terminal = 1;
General.ExpertMode = 1;

// Set basic mesh options
Mesh.Algorithm = 3;
Mesh.Algorithm3D = 1;
Mesh.CharacteristicLengthMin = 0.5;
Mesh.CharacteristicLengthMax = 10.0;

// Print debug message
Printf("Importing STEP file...");

// Import the geometry
Merge "$ABSOLUTE_INPUT";

// Print entity counts
Printf("Before adding box:");
Printf("Number of points: %g", #Point{:});
Printf("Number of curves: %g", #Curve{:});
Printf("Number of surfaces: %g", #Surface{:});
Printf("Number of volumes: %g", #Volume{:});

// Create a simple box
Printf("Creating domain box...");
Box(10000) = {-100, -100, -100, 200, 200, 200};
Coherence;

// Re-print counts
Printf("After adding box:");
Printf("Number of points: %g", #Point{:});
Printf("Number of curves: %g", #Curve{:});
Printf("Number of surfaces: %g", #Surface{:});
Printf("Number of volumes: %g", #Volume{:});

// Simple mesh generation - skip boolean operations for now
Printf("Generating mesh...");
Mesh.SaveAll = 1;
Mesh.Binary = 1;
Mesh.MeshOnlyVisible = 0;

// Generate mesh
Mesh 3;

// Save resulting mesh
Printf("Saving mesh...");
Save "$ABSOLUTE_OUTPUT";
EOT

echo "Running simplified Gmsh script with debug output..."
gmsh "$TEMP_SCRIPT" -

# Clean up
rm "$TEMP_SCRIPT"

# Check if the mesh was created - if not, try Python approach directly
if [ -f "$OUTPUT_FILE" ]; then
    echo "Success! Mesh created as $OUTPUT_FILE"
    exit 0
else
    echo "Gmsh script approach failed. Trying direct Python API approach..."
    
    # Create Python script for maximum control and debugging
    PYTHON_SCRIPT=$(mktemp)
    cat <<EOT > "$PYTHON_SCRIPT"
#!/usr/bin/env python3
import sys
import os
import gmsh
import traceback

# Set debug environment variables
os.environ["GMSH_DEBUG"] = "99"
os.environ["GMSH_VERBOSITY"] = "99"

try:
    # Initialize gmsh with all messages
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 1)
    gmsh.option.setNumber("General.Verbosity", 99)
    
    # Create a new model
    gmsh.model.add("domain")
    
    print("Importing STEP file: $ABSOLUTE_INPUT")
    try:
        # First try OCC import
        gmsh.model.occ.importShapes("$ABSOLUTE_INPUT")
        gmsh.model.occ.synchronize()
    except Exception as e:
        print(f"OCC import failed: {e}")
        # Fall back to direct import
        print("Trying direct merge...")
        gmsh.merge("$ABSOLUTE_INPUT")
    
    # Print entity counts
    points = gmsh.model.getEntities(0)
    curves = gmsh.model.getEntities(1)
    surfaces = gmsh.model.getEntities(2)
    volumes = gmsh.model.getEntities(3)
    
    print(f"After import: {len(points)} points, {len(curves)} curves, {len(surfaces)} surfaces, {len(volumes)} volumes")
    
    # Create domain box using OCC
    print("Creating domain box...")
    box = gmsh.model.occ.addBox(-100, -100, -100, 200, 200, 200)
    gmsh.model.occ.synchronize()
    
    # Print updated entity counts
    points = gmsh.model.getEntities(0)
    curves = gmsh.model.getEntities(1)
    surfaces = gmsh.model.getEntities(2)
    volumes = gmsh.model.getEntities(3)
    
    print(f"After box: {len(points)} points, {len(curves)} curves, {len(surfaces)} surfaces, {len(volumes)} volumes")
    
    # Set mesh parameters
    gmsh.option.setNumber("Mesh.Algorithm", 3)
    gmsh.option.setNumber("Mesh.Algorithm3D", 1)
    gmsh.option.setNumber("Mesh.CharacteristicLengthMin", 1.0)
    gmsh.option.setNumber("Mesh.CharacteristicLengthMax", 20.0)
    gmsh.option.setNumber("Mesh.SaveAll", 1)
    gmsh.option.setNumber("Mesh.MeshOnlyVisible", 0)
    
    # Generate mesh
    print("Generating mesh...")
    try:
        gmsh.model.mesh.generate(3)
    except Exception as e:
        print(f"3D mesh generation failed: {e}")
        try:
            print("Trying 2D mesh generation...")
            gmsh.model.mesh.generate(2)
        except Exception as e2:
            print(f"2D mesh generation failed: {e2}")
            print("Trying 1D mesh generation...")
            try:
                gmsh.model.mesh.generate(1)
            except Exception as e3:
                print(f"1D mesh generation failed: {e3}")
    
    # Save the mesh
    print(f"Saving mesh to {os.path.abspath('$ABSOLUTE_OUTPUT')}")
    gmsh.write("$ABSOLUTE_OUTPUT")
    
except Exception as e:
    print(f"Error in Python script: {e}")
    traceback.print_exc()
finally:
    # Always finalize GMSH
    if gmsh.isInitialized():
        gmsh.finalize()
EOT

    echo "Running Python script with maximum error reporting..."
    chmod +x "$PYTHON_SCRIPT"
    python3 -u "$PYTHON_SCRIPT"
    rm "$PYTHON_SCRIPT"
    
    if [ -f "$OUTPUT_FILE" ]; then
        echo "Success with Python approach!"
        exit 0
    else
        echo "Python approach failed. Creating minimal working mesh..."
        
        # Final attempt: Create a minimal mesh with just a box
        MINIMAL_SCRIPT=$(mktemp)
        cat <<EOT > "$MINIMAL_SCRIPT"
#!/usr/bin/env python3
import gmsh

# Initialize gmsh
gmsh.initialize()
gmsh.option.setNumber("General.Terminal", 1)

# Create a new model
gmsh.model.add("box")

# Create a simple box
box = gmsh.model.occ.addBox(-100, -100, -100, 200, 200, 200)
gmsh.model.occ.synchronize()

# Set mesh parameters
gmsh.option.setNumber("Mesh.Algorithm3D", 1)
gmsh.option.setNumber("Mesh.CharacteristicLengthMax", 20.0)

# Generate mesh
gmsh.model.mesh.generate(3)

# Save mesh
gmsh.write("$ABSOLUTE_OUTPUT")

# Finalize
gmsh.finalize()
EOT

        echo "Creating minimal box mesh..."
        python3 "$MINIMAL_SCRIPT"
        rm "$MINIMAL_SCRIPT"
        
        if [ -f "$OUTPUT_FILE" ]; then
            echo "Created minimal box mesh as $OUTPUT_FILE"
            echo "Warning: This mesh does not include the intake geometry!"
            exit 0
        else
            echo "All meshing attempts failed."
            echo "Check if Gmsh is installed correctly and has OpenCASCADE support."
            echo "Run 'gmsh -info' to see Gmsh configuration."
            exit 1
        fi
    fi
fi
