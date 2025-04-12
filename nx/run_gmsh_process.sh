#!/bin/bash
# Set library path and run the executable
export LD_LIBRARY_PATH="/usr/local/lib:$LD_LIBRARY_PATH"
# Execute with proper path
./gmsh_process
