#!/bin/bash

# Fix permissions for all scripts
chmod +x ./mesh_validator.py
chmod +x ./mesh_refiner.py
chmod +x ./bc_manager.py
chmod +x ./benchmark_tests.py
chmod +x ./gmsh_process
chmod +x ./mesh_generator
chmod +x ./run_tests.sh
chmod +x ./fix_test_geometry.py
chmod +x ./run_benchmarks.sh
chmod +x ./view_benchmark_results.py

# Create test geometry with the fixed script
python3 ./fix_test_geometry.py














echo "See BENCHMARKING.md for detailed instructions."echo ""echo "  ./view_benchmark_results.py"echo "To view benchmark results:"echo ""echo "  ./benchmark_tests.py --help"echo "Or for more control:"echo ""echo "  ./run_benchmarks.sh"echo "To run benchmarks, use:"echo ""echo "All scripts now have correct permissions and test geometry has been created."# Add benchmarking instructions
cat > ./BENCHMARKING.md << 'EOF'
# Benchmarking Guide for Intake-CFD Project

This guide explains how to run benchmarks using the tools provided in this project.

## Quick Start

```bash
# Run all benchmarks with default settings
./benchmark_tests.py --output-dir ./benchmark_results

# Run only mesh generation benchmarks
./benchmark_tests.py --mesh-generation

# Run full benchmark suite (includes all tests, takes longer)
./benchmark_tests.py --full
```

## Benchmark Types

### 1. Mesh Generation Benchmarks

Tests the performance of mesh generation with different mesh sizes and geometries.

```bash
# Run mesh generation benchmarks
./benchmark_tests.py --mesh-generation

# Specify custom output directory
./benchmark_tests.py --mesh-generation --output-dir ./custom_results
```

### 2. Boundary Layer Benchmarks

Tests the performance of boundary layer generation with different configurations.

```bash
# Run boundary layer benchmarks
./benchmark_tests.py --boundary-layers
```

### 3. Export Format Benchmarks

Tests the performance of exporting meshes to various formats (SU2, OpenFOAM, CGNS, etc.)

```bash
# Run export format benchmarks
./benchmark_tests.py --export-formats
```

### 4. Mesh Quality Benchmarks

Tests mesh quality analysis and improvement algorithms.

```bash
# Run mesh quality benchmarks
./benchmark_tests.py --mesh-quality
```

### 5. Solver Compatibility Benchmarks

Tests compatibility checks with various CFD solvers.

```bash
# Run solver compatibility benchmarks
./benchmark_tests.py --solver-compat
```

## Customizing Benchmarks

You can customize benchmark parameters by editing the `benchmark_tests.py` file directly. 
Key parameters to adjust include:

- Mesh sizes for generation tests
- Boundary layer parameters
- Quality thresholds
- Test geometries

## Understanding Results

Benchmark results are saved to:
1. A JSON file (`benchmark_results.json`) with raw data
2. An HTML report (`benchmark_report.html`) with visualizations
3. A directory structure containing the generated meshes and exports

The HTML report includes:
- System information (CPU, memory, etc.)
- Performance charts for each benchmark category
- Timing measurements for all operations
- Quality metrics for generated meshes

## Advanced Usage

### Performance Profiling

For more detailed performance profiling, use:

```bash
# Run with full profiling information
./benchmark_tests.py --full --profile
```

### Comparing Results

To compare benchmark results between runs:

```bash
# Run comparison between two result directories
./compare_benchmarks.py ./benchmark_results_old ./benchmark_results_new
```

### Continuous Integration

The benchmarking system can be integrated into CI workflows using:

```bash
# Non-interactive mode for CI
./benchmark_tests.py --ci --quick --output-dir ./ci_results
```
EOF

echo "Created BENCHMARKING.md file with detailed benchmarking instructions"

# Create a simple benchmark runner script
cat > ./run_benchmarks.sh << 'EOF'
#!/bin/bash
# filepath: /mnt/c/Users/Mohammed/Desktop/Intake-CFD-Project/nx/run_benchmarks.sh

# Set benchmark output directory
OUTPUT_DIR="./benchmark_results_$(date +%Y%m%d_%H%M)"
mkdir -p $OUTPUT_DIR

# Function to show progress
show_progress() {
  echo "====================================================="
  echo "$1"
  echo "====================================================="
}

# Ask which benchmarks to run
echo "Which benchmarks would you like to run?"
echo "1) Quick benchmarks (mesh generation only)"
echo "2) Standard benchmarks (mesh generation, export formats)"
echo "3) Full benchmarks (all tests - will take a while)"
echo "4) Custom benchmark selection"

read -p "Enter your choice [1-4]: " CHOICE

case $CHOICE in
  1)
    show_progress "Running quick benchmarks..."
    python3 ./benchmark_tests.py --mesh-generation --output-dir $OUTPUT_DIR
    ;;
  2)
    show_progress "Running standard benchmarks..."
    python3 ./benchmark_tests.py --mesh-generation --export-formats --output-dir $OUTPUT_DIR
    ;;
  3)
    show_progress "Running full benchmark suite..."
    python3 ./benchmark_tests.py --full --output-dir $OUTPUT_DIR
    ;;
  4)
    BENCHMARK_ARGS="--output-dir $OUTPUT_DIR"
    
    read -p "Include mesh generation benchmarks? (y/n): " INCLUDE_MESH
    if [[ $INCLUDE_MESH == "y" ]]; then
      BENCHMARK_ARGS="$BENCHMARK_ARGS --mesh-generation"
    fi
    
    read -p "Include boundary layer benchmarks? (y/n): " INCLUDE_BL
    if [[ $INCLUDE_BL == "y" ]]; then
      BENCHMARK_ARGS="$BENCHMARK_ARGS --boundary-layers"
    fi
    
    read -p "Include export format benchmarks? (y/n): " INCLUDE_EXPORT
    if [[ $INCLUDE_EXPORT == "y" ]]; then
      BENCHMARK_ARGS="$BENCHMARK_ARGS --export-formats"
    fi
    
    read -p "Include mesh quality benchmarks? (y/n): " INCLUDE_QUALITY
    if [[ $INCLUDE_QUALITY == "y" ]]; then
      BENCHMARK_ARGS="$BENCHMARK_ARGS --mesh-quality"
    fi
    
    read -p "Include solver compatibility benchmarks? (y/n): " INCLUDE_SOLVER
    if [[ $INCLUDE_SOLVER == "y" ]]; then
      BENCHMARK_ARGS="$BENCHMARK_ARGS --solver-compat"
    fi
    
    show_progress "Running custom benchmarks..."
    python3 ./benchmark_tests.py $BENCHMARK_ARGS
    ;;
  *)
    echo "Invalid choice. Exiting."
    exit 1
    ;;
esac

# Show results location
echo ""
echo "Benchmark completed. Results saved to: $OUTPUT_DIR"
echo "- Raw data: $OUTPUT_DIR/benchmark_results.json"
echo "- Report: $OUTPUT_DIR/benchmark_report.html"

# Open the report if possible
if command -v xdg-open &> /dev/null; then
  read -p "Open benchmark report? (y/n): " OPEN_REPORT
  if [[ $OPEN_REPORT == "y" ]]; then
    xdg-open "$OUTPUT_DIR/benchmark_report.html"
  fi
elif command -v open &> /dev/null; then
  read -p "Open benchmark report? (y/n): " OPEN_REPORT
  if [[ $OPEN_REPORT == "y" ]]; then
    open "$OUTPUT_DIR/benchmark_report.html"
  fi
fi
EOF

chmod +x ./run_benchmarks.sh

echo "Created run_benchmarks.sh script for easy benchmarking"

# Finish with the original message
echo "All scripts now have correct permissions and test geometry has been created."
echo ""
echo "To run benchmarks, use:"
echo "  ./run_benchmarks.sh"
echo ""
echo "Or for more control:"
echo "  ./benchmark_tests.py --help"
echo ""
echo "See BENCHMARKING.md for detailed instructions."
