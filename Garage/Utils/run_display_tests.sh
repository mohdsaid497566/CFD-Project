#!/bin/bash

# Run the display settings tests
echo "Running display settings tests..."
echo "=================================="

# Run the general GUI tests
python3 test_gui.py -v

# Run the detailed display settings tests
python3 test_display_settings.py -v

# Summarize results
echo ""
echo "Test Summary"
echo "============"

# Check if tests passed
if [ $? -eq 0 ]; then
    echo "✅ All display and parallelization tests passed!"
else
    echo "❌ Some tests failed. Please check the output above for details."
    exit 1
fi
