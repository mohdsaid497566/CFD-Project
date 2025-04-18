#!/bin/bash

# Check if Doxygen is installed
if ! command -v doxygen &> /dev/null; then
    echo "Error: Doxygen is not installed"
    echo "Please install Doxygen first"
    exit 1
fi

# Create output directory if it doesn't exist
mkdir -p docs_output

# Generate documentation
doxygen Doxyfile

echo "Documentation generated successfully!"
echo "Open docs_output/html/index.html in your web browser to view it."
