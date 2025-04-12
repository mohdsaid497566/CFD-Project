#!/bin/bash
set -e

# Check if OpenFOAM environment is sourced
if [ -z "$WM_PROJECT" ]; then
    echo "Error: OpenFOAM environment not found!"
    echo "Please source the OpenFOAM environment file first. For example:"
    echo "  source /usr/lib/openfoam/openfoam2212/etc/bashrc"
    exit 1
fi

# Convert the mesh
if [ ! -d "constant/polyMesh" ]; then
    echo "Converting mesh from GMSH to OpenFOAM format..."
    gmshToFoam "box_mesh.msh"
    
    # Fix boundary conditions
    createPatch -overwrite
    
    # Check mesh quality
    checkMesh
fi

# Initialize fields
echo "Initializing fields..."
setFields

# Run the simulation
echo "Starting simulation with simpleFoam..."
simpleFoam

echo "Simulation completed!"
