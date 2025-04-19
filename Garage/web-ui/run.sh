#!/bin/bash

echo "Starting CFD Intake Design Tool Web UI"
echo "======================================="

# Check if the virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    
    # Install minimal dependencies for basic functionality
    echo "Installing minimal dependencies..."
    pip install flask
else
    source venv/bin/activate
fi

# Create a simplified requirements file if it doesn't exist
if [ ! -f "requirements.txt" ]; then
    echo "Creating requirements.txt..."
    cat > requirements.txt << EOF
flask==2.0.1
numpy==1.21.0
matplotlib==3.4.2
requests==2.25.1
gunicorn==20.1.0
EOF
fi

echo "NOTICE: For full functionality, run:"
echo "pip install -r requirements.txt"
echo ""

# Run the performance optimizer
echo "Running performance diagnostics..."
python optimize.py

# Choose server based on what's available
if command -v gunicorn &> /dev/null; then
    echo "Starting with gunicorn (production server)..."
    gunicorn -w 4 -b 0.0.0.0:5000 app:app
else
    echo "Starting with Flask development server..."
    # Add threaded=True for better performance
    python app.py
fi
