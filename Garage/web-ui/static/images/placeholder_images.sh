#!/bin/bash

# Create placeholder images for the web UI
# Requires ImageMagick to be installed (convert command)

# Check if ImageMagick is installed
if ! command -v convert &> /dev/null; then
    echo "ImageMagick is not installed. Please install it to generate placeholder images."
    exit 1
fi

# Create model placeholder
convert -size 400x300 gradient:blue-white \
    -gravity center -pointsize 20 -annotate 0 "Model Preview" \
    model_placeholder.png

# Create convergence placeholder
convert -size 400x300 gradient:green-yellow \
    -gravity center -pointsize 20 -annotate 0 "Convergence Plot" \
    convergence_placeholder.png

# Create result placeholder
convert -size 600x400 gradient:red-yellow \
    -gravity center -pointsize 20 -annotate 0 "CFD Visualization" \
    result_placeholder.png

# Create flow chart placeholder
convert -size 400x300 gradient:purple-white \
    -gravity center -pointsize 20 -annotate 0 "Flow Rate Chart" \
    flow_chart_placeholder.png

echo "Placeholder images created successfully!"
