#!/bin/bash

# Run comprehensive HPC workflow tests
echo "Running HPC workflow tests..."
echo "============================="

# Make sure the script is executable
chmod +x test_hpc_workflow.py
chmod +x test_hpc_advanced.py

# Run the basic HPC workflow tests
echo "Running basic HPC workflow tests..."
python3 test_hpc_workflow.py -v

# Store result of the first test
BASIC_TESTS_RESULT=$?

# Run advanced HPC workflow tests
echo -e "\nRunning advanced HPC workflow tests..."
python3 test_hpc_advanced.py -v

# Store result of the second test
ADVANCED_TESTS_RESULT=$?

# Summarize results
echo ""
echo "Test Summary"
echo "============"

if [ $BASIC_TESTS_RESULT -eq 0 ] && [ $ADVANCED_TESTS_RESULT -eq 0 ]; then
    echo "✅ All HPC workflow tests passed!"
    exit 0
else
    echo "❌ Some tests failed. Please check the output above for details."
    exit 1
fi
