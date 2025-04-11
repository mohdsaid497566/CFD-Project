#!/bin/bash

# Test script for run_nx_commands.sh
echo "Starting test for run_nx_commands.sh..."

# Define test inputs
input_prt_path="test_input.prt"
expressions_py_path="test_expressions.py"
export_py_path="test_export.py"
output_prt_name="test_output"

# Run the script and capture output
output=$(../run_nx_commands.sh "$input_prt_path" "$expressions_py_path" "$export_py_path" "$output_prt_name" 2>&1)

# Display the output for debugging
echo "Script output:"
echo "$output"

# Check the output
if [ -f "../$output_prt_name.stp" ]; then
    echo "Test passed: STEP file created successfully."
else
    echo "Test failed: STEP file not created."
fi