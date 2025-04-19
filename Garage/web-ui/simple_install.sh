#!/bin/bash

echo "Simple Install Script for CFD Intake Design Tool Web UI"
echo "======================================================"

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is required but not installed."
    echo "Please install Python 3 and try again."
    exit 1
fi

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies one by one with error handling
echo "Installing dependencies..."

dependencies=("flask" "numpy" "matplotlib" "requests")

for dep in "${dependencies[@]}"; do
    echo "Installing $dep..."
    pip install $dep
    
    if [ $? -ne 0 ]; then
        echo "WARNING: Failed to install $dep. Some features may not work."
    fi
done

echo ""
echo "Installation complete. Run the application with:"
echo "./run.sh"
echo ""
echo "If you encounter any issues, try running the diagnostics:"
echo "python optimize.py"
