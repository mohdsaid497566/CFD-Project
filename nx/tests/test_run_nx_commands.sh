#!/bin/bash

set -e

echo "Running test for run_nx_commands.sh"

output=$(./run_nx_commands.sh)
echo "Output: $output"

if [[ -z "$output" ]]; then
  echo "Error: No output from run_nx_commands.sh"
  exit 1
fi

if [[ ! -f "step_file.txt" ]]; then
  echo "Error: step_file.txt not found"
  exit 1
fi

echo "Test completed successfully"