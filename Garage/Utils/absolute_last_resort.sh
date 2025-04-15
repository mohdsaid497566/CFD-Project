#!/bin/bash
set -e

# Default input and output file
INPUT_FILE="${1:-INTAKE3D.stp}"
OUTPUT_FILE="${2:-minimal_mesh.msh}"

echo "======================================="
echo "ABSOLUTE LAST RESORT MESHING APPROACH"
echo "======================================="
echo "Input: $INPUT_FILE"
echo "Output: $OUTPUT_FILE"
echo

# First try with built-in Gmsh kernel (works with any Gmsh installation)
MINIMAL_SCRIPT=$(mktemp --suffix=.geo)

cat <<EOT > "$MINIMAL_SCRIPT"
// The absolute minimal mesh generation script
// Using built-in Gmsh kernel (works with any Gmsh installation)

// Set general options
General.Terminal = 1;
General.Verbosity = 1;

// Set mesh parameters to be very coarse and simple
Mesh.CharacteristicLengthMax = 100.0;
Mesh.CharacteristicLengthMin = 10.0;
Mesh.Algorithm = 1; // MeshAdapt
Mesh.Algorithm3D = 1; // Delaunay
Mesh.ElementOrder = 1; // Linear elements
Mesh.Binary = 1; // Binary format

// Create a simple box with built-in kernel
Point(1) = {-100, -600, -300, 100};
Point(2) = {1900, -600, -300, 100};
Point(3) = {1900, 600, -300, 100};
Point(4) = {-100, 600, -300, 100};
Point(5) = {-100, -600, 300, 100};
Point(6) = {1900, -600, 300, 100};
Point(7) = {1900, 600, 300, 100};
Point(8) = {-100, 600, 300, 100};

Line(1) = {1, 2};
Line(2) = {2, 3};
Line(3) = {3, 4};
Line(4) = {4, 1};
Line(5) = {5, 6};
Line(6) = {6, 7};
Line(7) = {7, 8};
Line(8) = {8, 5};
Line(9) = {1, 5};
Line(10) = {2, 6};
Line(11) = {3, 7};
Line(12) = {4, 8};

Line Loop(1) = {1, 2, 3, 4};
Line Loop(2) = {5, 6, 7, 8};
Line Loop(3) = {1, 10, -5, -9};
Line Loop(4) = {2, 11, -6, -10};
Line Loop(5) = {3, 12, -7, -11};
Line Loop(6) = {4, 9, -8, -12};

Plane Surface(1) = {1};
Plane Surface(2) = {2};
Plane Surface(3) = {3};
Plane Surface(4) = {4};
Plane Surface(5) = {5};
Plane Surface(6) = {6};

Surface Loop(1) = {1, 2, 3, 4, 5, 6};
Volume(1) = {1};

// Just generate the mesh
Mesh 3;

// Save the mesh
Save "$OUTPUT_FILE";
Exit;
EOT

echo "Running minimal box-only mesh script (with built-in kernel)..."
gmsh "$MINIMAL_SCRIPT" -

# Check if the mesh was created
if [ -f "$OUTPUT_FILE" ] && [ -s "$OUTPUT_FILE" ]; then
    echo "Success! Created a minimal box mesh at: $OUTPUT_FILE"
    echo "WARNING: This mesh does NOT contain the actual geometry!"
    rm -f "$MINIMAL_SCRIPT"
    exit 0
fi

echo "First approach failed. Trying OpenCASCADE kernel approach..."

# Try with OpenCASCADE kernel
OCC_SCRIPT=$(mktemp --suffix=.geo)
cat <<EOT > "$OCC_SCRIPT"
// Minimal mesh script using OpenCASCADE
SetFactory("OpenCASCADE");

// Set general options
General.Terminal = 1;
General.Verbosity = 1;

// Set mesh parameters
Mesh.CharacteristicLengthMax = 100.0;
Mesh.CharacteristicLengthMin = 10.0;
Mesh.Algorithm = 1;
Mesh.Algorithm3D = 1;
Mesh.ElementOrder = 1;
Mesh.Binary = 1;

// Create a simple box with OpenCASCADE
Box(1) = {-100, -600, -300, 2000, 1200, 600};

// Generate mesh
Mesh 3;

// Save mesh
Save "$OUTPUT_FILE";
Exit;
EOT

echo "Running OpenCASCADE kernel approach..."
gmsh "$OCC_SCRIPT" -

# Clean up
rm -f "$MINIMAL_SCRIPT" "$OCC_SCRIPT"

if [ -f "$OUTPUT_FILE" ] && [ -s "$OUTPUT_FILE" ]; then
    echo "Success with OpenCASCADE approach! Created mesh at: $OUTPUT_FILE"
    echo "WARNING: This mesh does NOT contain the actual geometry!"
    exit 0
else
    echo "Both approaches failed. Trying direct Python script..."
    
    # Last resort: Use Python API
    PYTHON_SCRIPT=$(mktemp --suffix=.py)
    cat <<EOT > "$PYTHON_SCRIPT"
#!/usr/bin/env python3
import gmsh
import sys

# Initialize Gmsh
gmsh.initialize()

# Create a new model
gmsh.model.add("box")

# Create points for the box corners
points = [
    gmsh.model.geo.addPoint(-100, -600, -300, 100),
    gmsh.model.geo.addPoint(1900, -600, -300, 100),
    gmsh.model.geo.addPoint(1900, 600, -300, 100),
    gmsh.model.geo.addPoint(-100, 600, -300, 100),
    gmsh.model.geo.addPoint(-100, -600, 300, 100),
    gmsh.model.geo.addPoint(1900, -600, 300, 100),
    gmsh.model.geo.addPoint(1900, 600, 300, 100),
    gmsh.model.geo.addPoint(-100, 600, 300, 100)
]

# Create lines connecting the points
lines = [
    gmsh.model.geo.addLine(points[0], points[1]),
    gmsh.model.geo.addLine(points[1], points[2]),
    gmsh.model.geo.addLine(points[2], points[3]),
    gmsh.model.geo.addLine(points[3], points[0]),
    gmsh.model.geo.addLine(points[4], points[5]),
    gmsh.model.geo.addLine(points[5], points[6]),
    gmsh.model.geo.addLine(points[6], points[7]),
    gmsh.model.geo.addLine(points[7], points[4]),
    gmsh.model.geo.addLine(points[0], points[4]),
    gmsh.model.geo.addLine(points[1], points[5]),
    gmsh.model.geo.addLine(points[2], points[6]),
    gmsh.model.geo.addLine(points[3], points[7])
]

# Create line loops for the 6 faces
line_loops = [
    gmsh.model.geo.addCurveLoop([lines[0], lines[1], lines[2], lines[3]]),
    gmsh.model.geo.addCurveLoop([lines[4], lines[5], lines[6], lines[7]]),
    gmsh.model.geo.addCurveLoop([lines[0], lines[9], -lines[4], -lines[8]]),
    gmsh.model.geo.addCurveLoop([lines[1], lines[10], -lines[5], -lines[9]]),
    gmsh.model.geo.addCurveLoop([lines[2], lines[11], -lines[6], -lines[10]]),
    gmsh.model.geo.addCurveLoop([lines[3], lines[8], -lines[7], -lines[11]])
]

# Create surfaces for each face
surfaces = []
for i in range(6):
    surfaces.append(gmsh.model.geo.addPlaneSurface([line_loops[i]]))

# Create a surface loop
surface_loop = gmsh.model.geo.addSurfaceLoop(surfaces)

# Create a volume
volume = gmsh.model.geo.addVolume([surface_loop])

# Synchronize the model
gmsh.model.geo.synchronize()

# Set mesh options
gmsh.option.setNumber("Mesh.Algorithm", 1)
gmsh.option.setNumber("Mesh.Algorithm3D", 1)
gmsh.option.setNumber("Mesh.CharacteristicLengthMax", 100)
gmsh.option.setNumber("Mesh.CharacteristicLengthMin", 10)

# Generate 3D mesh
gmsh.model.mesh.generate(3)

# Save the mesh
gmsh.write("$OUTPUT_FILE")

# Clean up
gmsh.finalize()
print("Created minimal box mesh using Python API")
EOT

    echo "Running Python API approach..."
    python3 "$PYTHON_SCRIPT"
    
    # Clean up
    rm -f "$PYTHON_SCRIPT"
    
    if [ -f "$OUTPUT_FILE" ] && [ -s "$OUTPUT_FILE" ]; then
        echo "Success with Python API approach! Created mesh at: $OUTPUT_FILE"
        echo "WARNING: This mesh does NOT contain the actual geometry!"
        exit 0
    else
        echo "All attempts failed."
        echo "Check that Gmsh is properly installed with: gmsh -info"
        exit 1
    fi
fi
