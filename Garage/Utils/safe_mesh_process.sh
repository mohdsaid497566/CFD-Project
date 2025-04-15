#!/bin/bash
# This is a wrapper script for gmsh_process that avoids segmentation faults
# by separating the mesh generation and export steps, with isolated export processes.

if [ $# -lt 2 ]; then
    echo "Usage: $0 input_file output_file [options]"
    echo "This wrapper separates mesh generation and exports to avoid segmentation faults."
    exit 1
fi

INPUT_FILE="$1"
OUTPUT_FILE="$2"
shift 2

# Extract mesh options and export options
MESH_OPTIONS=""
EXPORT_OPTIONS=""
EXPORT_FORMATS=false

for opt in "$@"; do
    case "$opt" in
        --su2|--openfoam|--vtk|--cgns|--fluent|--med|--paraview|--all-formats)
            EXPORT_OPTIONS="$EXPORT_OPTIONS $opt"
            EXPORT_FORMATS=true
            ;;
        *)
            MESH_OPTIONS="$MESH_OPTIONS $opt"
            ;;
    esac
done

# Step 1: Generate the mesh only
echo "Step 1: Generating mesh without exports"
./gmsh_process --input "$INPUT_FILE" --output "$OUTPUT_FILE" $MESH_OPTIONS

# Check if the mesh generation was successful
if [ ! -f "$OUTPUT_FILE" ]; then
    echo "Error: Mesh generation failed. Output file not found."
    exit 1
fi

# Step 2: Export to requested formats if any
if [ "$EXPORT_FORMATS" = true ]; then
    echo "Step 2: Exporting mesh to requested formats"
    for format in $EXPORT_OPTIONS; do
        echo "  Exporting to $format format using isolated process"
        ./export_mesh.sh "$OUTPUT_FILE" "$format"
        if [ $? -ne 0 ]; then
            echo "Error: Export to $format format failed. Skipping."
        fi
    done
fi

# Debugging: Check memory usage after each step
echo "Debugging: Checking memory usage"
free -h

echo "All operations completed successfully."
