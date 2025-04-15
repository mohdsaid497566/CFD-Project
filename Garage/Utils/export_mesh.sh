#!/bin/bash
# This script handles exporting a mesh to a specific format in an isolated process.

if [ $# -lt 2 ]; then
    echo "Usage: $0 mesh_file format"
    echo "Exports the given mesh file to the specified format."
    exit 1
fi

MESH_FILE="$1"
FORMAT="$2"

# Validate that the mesh file exists
if [ ! -f "$MESH_FILE" ]; then
    echo "Error: Mesh file '$MESH_FILE' not found."
    exit 1
fi

echo "Starting export to $FORMAT format"

# Enable verbose debugging
export GMSH_VERBOSITY=99

# Validate the mesh file before exporting
echo "Validating mesh file..."
python3 ./mesh_validator.py "$MESH_FILE" --quality-metrics all
VALIDATION_EXIT_CODE=$?
if [ $VALIDATION_EXIT_CODE -ne 0 ]; then
    echo "Error: Mesh validation failed with exit code $VALIDATION_EXIT_CODE."
    echo "Please check the mesh file for issues and try again."
    exit 1
fi

# Perform the export
echo "Exporting mesh to $FORMAT format..."
./gmsh_process --input "$MESH_FILE" --output "$MESH_FILE" "$FORMAT"
EXPORT_EXIT_CODE=$?

if [ $EXPORT_EXIT_CODE -eq 0 ]; then
    echo "Export to $FORMAT format completed successfully."
    exit 0
elif [ $EXPORT_EXIT_CODE -eq 139 ]; then
    echo "Error: Segmentation fault occurred during export."
    echo "Possible causes: invalid mesh, insufficient memory, or a bug in GMSH."
    echo "Suggestions:"
    echo "  - Validate the mesh using './mesh_validator.py'."
    echo "  - Simplify the mesh or reduce its complexity."    echo "  - Check system resources and ensure sufficient memory is available."    echo "  - Update to the latest version of GMSH."    exit 139else    echo "Error: Export to $FORMAT format failed with exit code $EXPORT_EXIT_CODE."    echo "Check the GMSH logs for more details."    exit $EXPORT_EXIT_CODEfi