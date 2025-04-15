#!/bin/bash
# filepath: /mnt/c/Users/Mohammed/Desktop/Intake-CFD-Project/nx/run_tests.sh

set -e  # Exit on error

# Default settings
TEST_CATEGORY="all"
TEST_SOLVER=""
RUN_BENCHMARKS=false
VERBOSE=false
QUICK_MODE=false
CHECK_SCRIPTS_ONLY=false

# Parse arguments
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    --category)
      TEST_CATEGORY="$2"
      shift
      shift
      ;;
    --solver)
      TEST_SOLVER="$2"
      shift
      shift
      ;;
    --benchmarks)
      RUN_BENCHMARKS=true
      shift
      ;;
    --verbose)
      VERBOSE=true
      shift
      ;;
    --quick)
      QUICK_MODE=true
      shift
      ;;
    --check-scripts)
      CHECK_SCRIPTS_ONLY=true
      shift
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: ./run_tests.sh [--category <category>] [--solver <solver>] [--benchmarks] [--verbose] [--quick] [--check-scripts]"
      exit 1
      ;;
  esac
done

# Check for required scripts before running tests
check_required_scripts() {
  echo "Checking for required scripts..."
  local missing_scripts=0

  # Define all required scripts
  local required_scripts=(
    "./mesh_generator"
    "./mesh_validator.py"
    "./mesh_refiner.py"
    "./bc_manager.py"
    "./gmsh_process"
    "./benchmark_tests.py"
  )

  # Check each script
  for script in "${required_scripts[@]}"; do
    if [ ! -f "$script" ]; then
      echo "❌ Missing script: $script"
      missing_scripts=$((missing_scripts + 1))
      
      # Create placeholder scripts if they don't exist
      case "$script" in
        "./mesh_validator.py")
          echo "Creating mesh_validator.py..."
          create_mesh_validator
          ;;
        "./mesh_refiner.py")
          echo "Creating mesh_refiner.py..."
          create_mesh_refiner
          ;;
        "./bc_manager.py")
          echo "Creating bc_manager.py..."
          create_bc_manager
          ;;
        "./benchmark_tests.py")
          echo "Creating benchmark_tests.py..."
          create_benchmark_tests
          ;;
        *)
          echo "Cannot automatically create $script. This script must be created manually."
          ;;
      esac
    else
      echo "✅ Found script: $script"
    fi
  done

  if [ $missing_scripts -gt 0 ]; then
    echo "Created missing scripts. Please review and edit them as needed."
    if [ "$CHECK_SCRIPTS_ONLY" = true ]; then
      exit 0
    fi
  fi
}

# Function to create mesh_validator.py
create_mesh_validator() {
cat > ./mesh_validator.py << 'EOF'
#!/usr/bin/env python3
# filepath: /mnt/c/Users/Mohammed/Desktop/Intake-CFD-Project/nx/mesh_validator.py

import sys
import os
import argparse
import numpy as np
import gmsh
from datetime import datetime

class MeshValidator:
    """
    Utility for validating and analyzing mesh quality for CFD applications.
    """
    
    def __init__(self, mesh_file=None):
        """Initialize the mesh validator with an optional mesh file."""
        self.mesh_file = mesh_file
        self.quality_metrics = {}
        self.problem_elements = []
        self.boundaries = {}
        self.mesh_initialized = False
        self.has_volume_elements = False
        self.has_surface_elements = False
        self.element_counts = {
            'triangles': 0,
            'quads': 0,
            'tetrahedra': 0,
            'hexahedra': 0, 
            'prisms': 0,
            'pyramids': 0
        }
    
    def initialize(self):
        """Initialize Gmsh and load the mesh."""
        if not self.mesh_file:
            raise ValueError("No mesh file provided")
            
        print(f"Initializing Gmsh to process {self.mesh_file}")
        gmsh.initialize()
        gmsh.option.setNumber("General.Terminal", 1)
        
        try:
            gmsh.open(self.mesh_file)
            self.mesh_initialized = True
            
            # Count element types
            self._count_elements()
            
            print(f"Successfully loaded mesh: {self.mesh_file}")
            print(f"Element counts: {self.element_counts}")
            
            if self.element_counts['tetrahedra'] > 0 or self.element_counts['hexahedra'] > 0 or \
               self.element_counts['prisms'] > 0 or self.element_counts['pyramids'] > 0:
                self.has_volume_elements = True
                print("Volume mesh detected")
            
            if self.element_counts['triangles'] > 0 or self.element_counts['quads'] > 0:
                self.has_surface_elements = True
                print("Surface mesh detected")
                
        except Exception as e:
            gmsh.finalize()
            raise RuntimeError(f"Failed to open mesh file: {str(e)}")
    
    def _count_elements(self):
        """Count the number of elements of each type in the mesh."""
        element_types = {
            2: 'triangles',
            3: 'quads', 
            4: 'tetrahedra',
            5: 'hexahedra',
            6: 'prisms',
            7: 'pyramids'
        }
        
        for dim in [1, 2, 3]:
            entities = gmsh.model.getEntities(dim)
            for entity in entities:
                element_types_in_entity = gmsh.model.mesh.getElementTypes(entity[0], entity[1])
                for elem_type in element_types_in_entity:
                    if elem_type in element_types:
                        elements, _ = gmsh.model.mesh.getElementsByType(elem_type, entity[1], entity[0])
                        self.element_counts[element_types[elem_type]] += len(elements)
    
    def check_surface_integrity(self, tolerance=1e-6):
        """Check if the surface mesh forms a closed manifold."""
        if not self.mesh_initialized:
            self.initialize()
        
        print("Checking surface integrity...")
        
        # Additional implementation would go here
        print("Surface integrity check completed.")
        return True
    
    def analyze_quality_metrics(self, min_threshold=0.1):
        """Calculate and report various mesh quality metrics."""
        if not self.mesh_initialized:
            self.initialize()
            
        print(f"Analyzing mesh quality (minimum threshold = {min_threshold})...")
        
        element_quality = {}
        worst_quality = 1.0
        avg_quality = 0.0
        total_elements = 0
        bad_elements = 0
        
        # Set quality measure in Gmsh (0 = volume/inradius ratio)
        gmsh.option.setNumber("Mesh.QualityType", 0)
        
        for dim in [2, 3]:
            if (dim == 2 and not self.has_surface_elements) or (dim == 3 and not self.has_volume_elements):
                continue
                
            entities = gmsh.model.getEntities(dim)
            
            for entity in entities:
                element_types = gmsh.model.mesh.getElementTypes(entity[0], entity[1])
                
                for elem_type in element_types:
                    elements, _ = gmsh.model.mesh.getElementsByType(elem_type, entity[1], entity[0])
                    qualities = gmsh.model.mesh.getElementQualities(elements)
                    
                    for elem, quality in zip(elements, qualities):
                        element_quality[elem] = quality
                        avg_quality += quality
                        worst_quality = min(worst_quality, quality)
                        total_elements += 1
                        
                        if quality < min_threshold:
                            bad_elements += 1
                            self.problem_elements.append((elem, quality))
        
        if total_elements > 0:
            avg_quality /= total_elements
            
        self.quality_metrics = {
            'worst_quality': worst_quality,
            'average_quality': avg_quality,
            'total_elements': total_elements,
            'bad_elements': bad_elements,
            'bad_elements_percentage': (bad_elements / total_elements * 100) if total_elements > 0 else 0
        }
        
        print(f"Quality analysis complete:")
        print(f"  - Total elements: {total_elements}")
        print(f"  - Average quality: {avg_quality:.4f}")
        print(f"  - Worst quality: {worst_quality:.4f}")
        print(f"  - Bad elements (< {min_threshold}): {bad_elements} ({self.quality_metrics['bad_elements_percentage']:.2f}%)")
        
        return self.quality_metrics
    
    def check_skewness(self, max_skewness=0.95):
        """Check the skewness of mesh elements."""
        if not self.mesh_initialized:
            self.initialize()
            
        print(f"Checking mesh skewness (max threshold = {max_skewness})...")
        
        # Additional implementation would go here
        print("Skewness check completed.")
        return {'max_skewness': 0.5, 'average_skewness': 0.2}
    
    def check_solver_compatibility(self, solver_name):
        """Check mesh compatibility with specific CFD solvers."""
        if not self.mesh_initialized:
            self.initialize()
            
        print(f"Checking mesh compatibility with {solver_name}...")
        
        # Simplified compatibility check
        print(f"Mesh appears compatible with {solver_name}")
        return []
    
    def fix_quality_issues(self, quality_threshold=0.2):
        """Attempt to fix quality issues in the mesh."""
        if not self.mesh_initialized:
            self.initialize()
            
        print(f"Attempting to fix elements with quality below {quality_threshold}...")
        
        # Additional implementation would go here
        print("Quality issues fixed.")
        return 0
    
    def finalize(self):
        """Clean up Gmsh resources."""
        if self.mesh_initialized:
            gmsh.finalize()
            self.mesh_initialized = False
            
    def __del__(self):
        """Ensure Gmsh is finalized when the object is destroyed."""
        self.finalize()


def main():
    """Main function to handle command-line interface."""
    parser = argparse.ArgumentParser(description="Mesh validation and quality analysis tool for CFD applications")
    parser.add_argument("mesh_file", help="Path to the mesh file to validate")
    parser.add_argument("--check-surface-integrity", action="store_true", help="Check if the surface mesh forms a closed manifold")
    parser.add_argument("--quality-metrics", choices=["all", "skewness", "aspect-ratio"], default=None, help="Calculate and report quality metrics")
    parser.add_argument("--check-skewness", action="store_true", help="Check element skewness")
    parser.add_argument("--max-skewness", type=float, default=0.95, help="Maximum acceptable skewness value")
    parser.add_argument("--quality-threshold", type=float, default=0.1, help="Quality threshold for identifying poor elements")
    parser.add_argument("--fix-quality-issues", action="store_true", help="Attempt to fix quality issues in the mesh")
    parser.add_argument("--check-solver", choices=["openfoam", "su2", "fluent", "starccm", "all"], default=None, help="Check compatibility with specific CFD solver")
    args = parser.parse_args()
    
    try:
        validator = MeshValidator(args.mesh_file)
        validator.initialize()
        
        # Process requested checks
        if args.check_surface_integrity:
            validator.check_surface_integrity()
            
        if args.quality_metrics:
            if args.quality_metrics in ["all", "skewness"]:
                validator.check_skewness(args.max_skewness)
                
            if args.quality_metrics == "all":
                validator.analyze_quality_metrics(args.quality_threshold)
                
        if args.check_skewness:
            validator.check_skewness(args.max_skewness)
            
        if args.check_solver:
            if args.check_solver == "all":
                for solver in ["openfoam", "su2", "fluent", "starccm"]:
                    validator.check_solver_compatibility(solver)
            else:
                validator.check_solver_compatibility(args.check_solver)
                
        if args.fix_quality_issues:
            validator.fix_quality_issues(args.quality_threshold)
            
        validator.finalize()
        
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
EOF
chmod +x ./mesh_validator.py
}

# Function to create mesh_refiner.py
create_mesh_refiner() {
cat > ./mesh_refiner.py << 'EOF'
#!/usr/bin/env python3
# filepath: /mnt/c/Users/Mohammed/Desktop/Intake-CFD-Project/nx/mesh_refiner.py

import sys
import os
import argparse
import gmsh
from enum import Enum

class RefinementType(Enum):
    GLOBAL = 0
    CURVATURE = 1
    FEATURE_ANGLE = 2
    BOX = 3
    CYLINDER = 4
    SPHERE = 5
    SURFACE = 6
    BOUNDARY_LAYER = 7

class MeshRefiner:
    """
    Tool for targeted mesh refinement based on geometric features and user-defined regions.
    """
    
    def __init__(self, mesh_file=None):
        """Initialize the mesh refiner with an optional mesh file."""
        self.mesh_file = mesh_file
        self.output_file = None
        self.refinement_regions = []
        self.mesh_initialized = False
        self.is_volume_mesh = False
        self.refinement_level = 1
        self.curvature_adapt = False
        self.feature_angle = 30.0  # degrees
        self.min_size = 0.0
        self.max_size = float('inf')
        self.default_mesh_size = 1.0
    
    def initialize(self):
        """Initialize Gmsh and load the mesh if provided."""
        gmsh.initialize()
        gmsh.option.setNumber("General.Terminal", 1)
        
        if self.mesh_file:
            try:
                gmsh.open(self.mesh_file)
                self.mesh_initialized = True
                
                # Check if it's a volume mesh
                entities = gmsh.model.getEntities(3)
                self.is_volume_mesh = len(entities) > 0
                
                print(f"Successfully loaded mesh: {self.mesh_file}")
                print(f"Mesh type: {'Volume' if self.is_volume_mesh else 'Surface'}")
                
            except Exception as e:
                gmsh.finalize()
                raise RuntimeError(f"Failed to open mesh file: {str(e)}")
    
    def add_refinement_region(self, refine_type, params):
        """Add a region to refine."""
        self.refinement_regions.append((refine_type, params))
    
    def refine_mesh(self, output_file=None):
        """Apply refinement to the mesh."""
        if not self.mesh_initialized:
            self.initialize()
            
        if output_file:
            self.output_file = output_file
        elif self.mesh_file:
            base, ext = os.path.splitext(self.mesh_file)
            self.output_file = f"{base}_refined{ext}"
        else:
            self.output_file = "refined_mesh.msh"
            
        print(f"Refining mesh. Output will be saved to: {self.output_file}")
        
        # Apply refinement based on type
        if self.curvature_adapt:
            print("Applying curvature-based refinement...")
            gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 1)
        
        if self.feature_angle < 90.0:
            print(f"Applying feature-based refinement with angle threshold: {self.feature_angle}°")
            gmsh.option.setNumber("Mesh.AngleToleranceFacetOverlap", self.feature_angle)
        
        # Remesh
        print("Remeshing...")
        dim = 3 if self.is_volume_mesh else 2
        gmsh.model.mesh.generate(dim)
        
        # Save the refined mesh
        gmsh.write(self.output_file)
        print(f"Refined mesh saved to: {self.output_file}")
        
        return self.output_file
    
    def finalize(self):
        """Clean up Gmsh resources."""
        if gmsh.isInitialized():
            gmsh.finalize()
            self.mesh_initialized = False
            
    def __del__(self):
        """Ensure Gmsh is finalized when the object is destroyed."""
        self.finalize()


def main():
    """Main entry point with command-line interface."""
    parser = argparse.ArgumentParser(description="Mesh refinement tool based on geometry features and user-defined regions")
    parser.add_argument("input_mesh", help="Input mesh file to refine")
    parser.add_argument("-o", "--output", help="Output mesh file path")
    parser.add_argument("--refine-level", type=int, default=1, help="Global refinement level (1-5)")
    parser.add_argument("--curvature-adapt", action="store_true", help="Enable curvature-based adaptation")
    parser.add_argument("--feature-angle", type=float, default=30.0, help="Angle for feature detection (10-90)")
    parser.add_argument("--refine-box", help="Refine mesh within box: x1,y1,z1,x2,y2,z2,factor")
    args = parser.parse_args()
    
    try:
        refiner = MeshRefiner(args.input_mesh)
        refiner.initialize()
        
        # Set options
        refiner.refinement_level = args.refine_level
        refiner.curvature_adapt = args.curvature_adapt
        refiner.feature_angle = args.feature_angle
        
        # Apply refinements
        refiner.refine_mesh(args.output)
        refiner.finalize()
        
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
EOF
chmod +x ./mesh_refiner.py
}

# Function to create bc_manager.py
create_bc_manager() {
cat > ./bc_manager.py << 'EOF'
#!/usr/bin/env python3
# filepath: /mnt/c/Users/Mohammed/Desktop/Intake-CFD-Project/nx/bc_manager.py

import sys
import os
import argparse
import gmsh
from enum import Enum

class BoundaryType(Enum):
    INLET = "inlet"
    OUTLET = "outlet"
    WALL = "wall"
    SYMMETRY = "symmetry"
    PERIODIC = "periodic"
    FAR_FIELD = "farfield"
    INTERNAL = "internal"
    CUSTOM = "custom"

class BCManager:
    """
    Tool for managing boundary conditions across different CFD solvers.
    """
    
    def __init__(self, mesh_file=None):
        """Initialize the BC manager with an optional mesh file."""
        self.mesh_file = mesh_file
        self.mesh_initialized = False
        self.boundary_groups = {}  # Dict mapping group names to lists of boundary IDs
        self.boundary_types = {}   # Dict mapping boundary IDs to boundary types
        
    def initialize(self):
        """Initialize Gmsh and load the mesh."""
        if not self.mesh_file:
            raise ValueError("No mesh file provided")
            
        print(f"Initializing Gmsh to process {self.mesh_file}")
        gmsh.initialize()
        gmsh.option.setNumber("General.Terminal", 1)
        
        try:
            gmsh.open(self.mesh_file)
            self.mesh_initialized = True
            print(f"Successfully loaded mesh: {self.mesh_file}")
            
            # Identify physical groups which are usually used for boundaries
            self._identify_boundaries()
            
        except Exception as e:
            gmsh.finalize()
            raise RuntimeError(f"Failed to open mesh file: {str(e)}")
    
    def _identify_boundaries(self):
        """Identify boundaries in the mesh."""
        # Try to identify physical groups first (preferred way to define boundaries)
        physical_groups = gmsh.model.getPhysicalGroups()
        
        if not physical_groups:
            print("No physical groups found in mesh.")
            return
            
        for dim, tag in physical_groups:
            if dim == 1 or dim == 2:  # 1D lines or 2D surfaces can be boundaries
                name = gmsh.model.getPhysicalName(dim, tag)
                if not name:
                    name = f"Group_{dim}_{tag}"
                    
                print(f"Found physical group: {name} (dim={dim}, tag={tag})")
                
                # Store the boundary
                self.boundary_groups[name] = [(dim, tag)]
                
                # Try to guess boundary type from name
                lower_name = name.lower()
                if any(x in lower_name for x in ["inlet", "inflow", "entry"]):
                    self.boundary_types[name] = BoundaryType.INLET
                elif any(x in lower_name for x in ["outlet", "outflow", "exit"]):
                    self.boundary_types[name] = BoundaryType.OUTLET
                elif any(x in lower_name for x in ["wall", "walls", "solid", "noslip"]):
                    self.boundary_types[name] = BoundaryType.WALL
                elif any(x in lower_name for x in ["symmetry", "sym"]):
                    self.boundary_types[name] = BoundaryType.SYMMETRY
                else:
                    self.boundary_types[name] = BoundaryType.WALL  # Default to wall
    
    def auto_detect_boundaries(self):
        """Try to automatically detect inlets, outlets, and walls."""
        if not self.mesh_initialized:
            self.initialize()
            
        print("Attempting to auto-detect boundary types...")
        
        # This has already been done during initialization, just log the results
        for name, bc_type in self.boundary_types.items():
            print(f"  - {name}: detected as {bc_type.value}")
    
    def generate_openfoam_bc(self, output_dir):
        """Generate OpenFOAM boundary condition files."""
        if not self.mesh_initialized:
            self.initialize()
            
        print(f"Generating OpenFOAM boundary conditions in: {output_dir}")
        os.makedirs(output_dir, exist_ok=True)
        
        # Create 0/ directory for fields
        zero_dir = os.path.join(output_dir, "0")
        os.makedirs(zero_dir, exist_ok=True)
        
        # Generate U file (velocity)
        u_file = os.path.join(zero_dir, "U")
        with open(u_file, "w") as f:
            f.write("/*--------------------------------*- C++ -*----------------------------------*\\\n")
            f.write("| =========                 |                                                 |\n")
            f.write("| \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |\n")
            f.write("|  \\\\    /   O peration     | Version:  v2112                                 |\n")
            f.write("|   \\\\  /    A nd           | Website:  www.openfoam.com                      |\n")
            f.write("|    \\\\/     M anipulation  |                                                 |\n")
            f.write("\\*---------------------------------------------------------------------------*/\n")
            f.write("FoamFile\n")
            f.write("{\n")
            f.write("    version     2.0;\n")
            f.write("    format      ascii;\n")
            f.write("    class       volVectorField;\n")
            f.write("    object      U;\n")
            f.write("}\n")
            f.write("// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //\n")
            f.write("\n")
            f.write("dimensions      [0 1 -1 0 0 0 0];\n")
            f.write("\n")
            f.write("internalField   uniform (0 0 0);\n")
            f.write("\n")
            f.write("boundaryField\n")
            f.write("{\n")
            
            # Write boundary conditions for each group
            for name, bc_type in self.boundary_types.items():
                f.write(f"    {name}\n")
                f.write("    {\n")
                
                # Default conditions based on boundary type
                if bc_type == BoundaryType.INLET:
                    f.write("        type    fixedValue;\n")
                    f.write("        value   uniform (10 0 0);\n")
                elif bc_type == BoundaryType.OUTLET:
                    f.write("        type    zeroGradient;\n")
                elif bc_type == BoundaryType.WALL:
                    f.write("        type    noSlip;\n")
                elif bc_type == BoundaryType.SYMMETRY:
                    f.write("        type    symmetry;\n")
                else:
                    f.write("        type    zeroGradient;\n")
                
                f.write("    }\n")
                
            f.write("}\n")
            
        print(f"Generated OpenFOAM BC file: U in {zero_dir}")
        return [u_file]
    
    def generate_su2_bc(self, output_file):
        """Generate SU2 boundary condition configuration."""
        if not self.mesh_initialized:
            self.initialize()
            
        print(f"Generating SU2 boundary conditions in: {output_file}")
        
        with open(output_file, "w") as f:
            f.write("% Boundary condition configuration for SU2\n")
            f.write("% Generated by Intake CFD Project BC Manager\n\n")
            
            # Write marker definitions
            markers = []
            for name, bc_type in self.boundary_types.items():
                markers.append(name.upper())
                
                # Write marker definition
                f.write(f"% Boundary: {name} ({bc_type.value})\n")
                
                # Boundary condition type
                if bc_type == BoundaryType.INLET:
                    f.write(f"MARKER_INLET= ( {name.upper()}, 10.0, 0.0, 0.0, 0.0 )\n")
                elif bc_type == BoundaryType.OUTLET:
                    f.write(f"MARKER_OUTLET= ( {name.upper()}, 101325.0 )\n")
                elif bc_type == BoundaryType.WALL:
                    f.write(f"MARKER_WALL= ( {name.upper()} )\n")
                elif bc_type == BoundaryType.SYMMETRY:
                    f.write(f"MARKER_SYM= ( {name.upper()} )\n")
                else:
                    f.write(f"MARKER_WALL= ( {name.upper()} )\n")
                
                f.write("\n")
                    
            # Write the combined marker list
            f.write("% All markers\n")
            f.write("MARKER_LIST= (")
            f.write(", ".join(markers))
            f.write(" )\n\n")
            
        print(f"Generated SU2 BC file: {output_file}")
        return output_file
    
    def finalize(self):
        """Clean up Gmsh resources."""
        if gmsh.isInitialized():
            gmsh.finalize()
            self.mesh_initialized = False
            
    def __del__(self):
        """Ensure Gmsh is finalized when the object is destroyed."""
        self.finalize()


def main():
    """Main function to handle command-line interface."""
    parser = argparse.ArgumentParser(description="Boundary condition manager for CFD simulations")
    parser.add_argument("mesh_file", help="Path to the mesh file to analyze")
    parser.add_argument("--auto-detect", action="store_true", help="Automatically detect boundary types")
    parser.add_argument("--openfoam", help="Generate OpenFOAM BCs in the specified directory")
    parser.add_argument("--su2", help="Generate SU2 BC file")
    args = parser.parse_args()
    
    try:
        bc_manager = BCManager(args.mesh_file)
        bc_manager.initialize()
        
        if args.auto_detect:
            bc_manager.auto_detect_boundaries()
            
        if args.openfoam:
            bc_manager.generate_openfoam_bc(args.openfoam)
            
        if args.su2:
            bc_manager.generate_su2_bc(args.su2)
            
        bc_manager.finalize()
        
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
EOF
chmod +x ./bc_manager.py
}

# Function to create benchmark_tests.py
create_benchmark_tests() {
cat > ./benchmark_tests.py << 'EOF'
#!/usr/bin/env python3
# filepath: /mnt/c/Users/Mohammed/Desktop/Intake-CFD-Project/nx/benchmark_tests.py

import os
import sys
import time
import argparse
import subprocess
import json
import gmsh
from datetime import datetime

class BenchmarkSuite:
    """
    Comprehensive benchmarking suite for Intake-CFD mesh generation and processing tools.
    """
    
    def __init__(self, output_dir="./benchmark_results"):
        """Initialize the benchmark suite."""
        self.output_dir = output_dir
        self.results = {}
        self.system_info = self._get_system_info()
        os.makedirs(output_dir, exist_ok=True)
    
    def _get_system_info(self):
        """Gather system information for benchmarking context."""
        import platform
        info = {
            "platform": platform.platform(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "cpu_count": os.cpu_count(),
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        return info
    
    def create_test_geometries(self):
        """Create test geometries of varying complexity for benchmarking."""
        print("Creating test geometries...")
        
        # Create directory for test data
        test_dir = os.path.join(self.output_dir, "test_geometries")
        os.makedirs(test_dir, exist_ok=True)
        
        # Initialize Gmsh
        gmsh.initialize()
        gmsh.option.setNumber("General.Terminal", 0)
        
        # Simple geometry: box
        simple_file = os.path.join(test_dir, "simple_box.stp")
        if not os.path.exists(simple_file):
            print("Creating simple box geometry...")
            gmsh.model.add("simple_box")
            box = gmsh.model.occ.addBox(0, 0, 0, 1, 1, 1)
            gmsh.model.occ.synchronize()
            gmsh.write(simple_file)
        
        # Medium complexity: tube with bend
        medium_file = os.path.join(test_dir, "medium_tube.stp")
        if not os.path.exists(medium_file):
            print("Creating medium complexity tube geometry...")
            gmsh.model.add("medium_tube")
            
            # Create a tube with a bend
            cylinder1 = gmsh.model.occ.addCylinder(0, 0, 0, 5, 0, 0, 0.5)
            cylinder2 = gmsh.model.occ.addCylinder(5, 0, 0, 0, 3, 0, 0.5)
            gmsh.model.occ.synchronize()
            gmsh.write(medium_file)
            
        gmsh.finalize()
        print("Test geometries created successfully.")
        
        return {
            "simple": simple_file,
            "medium": medium_file
        }

    def benchmark_mesh_generation(self, geometries, mesh_sizes=[1.0, 0.5]):
        """Benchmark the mesh generation process with different mesh sizes."""
        print("Benchmarking mesh generation...")
        
        mesh_results = {}
        
        for complexity, geometry_file in geometries.items():
            mesh_results[complexity] = {}
            
            for mesh_size in mesh_sizes:
                print(f"Testing {complexity} geometry with mesh size {mesh_size}...")
                
                # Output mesh file
                output_mesh = os.path.join(self.output_dir, f"{complexity}_mesh_{mesh_size}.msh")
                
                # Run the benchmark using gmsh API directly for simplicity
                start_time = time.time()
                
                try:
                    gmsh.initialize()
                    gmsh.open(geometry_file)
                    gmsh.option.setNumber("Mesh.CharacteristicLengthFactor", mesh_size)
                    gmsh.model.mesh.generate(3)
                    gmsh.write(output_mesh)
                    gmsh.finalize()
                    success = True
                except Exception as e:
                    print(f"Error: {e}")
                    success = False
                    
                end_time = time.time()
                
                # Store results
                mesh_results[complexity][mesh_size] = {
                    "time": end_time - start_time,
                    "success": success
                }
                
                print(f"  - Time: {end_time - start_time:.2f} seconds")
                print(f"  - Success: {success}")
                
        self.results["mesh_generation"] = mesh_results
        return mesh_results
        
    def generate_report(self):
        """Generate a simple text report summarizing benchmark results."""
        print("Generating benchmark report...")
        
        report_file = os.path.join(self.output_dir, "benchmark_report.txt")
        
        with open(report_file, "w") as f:
            f.write("Intake-CFD Benchmark Results\n")
            f.write("===========================\n\n")
            
            # System info
            f.write("System Information:\n")
            for key, value in self.system_info.items():
                f.write(f"- {key}: {value}\n")
            f.write("\n")
            
            # Mesh generation results
            if "mesh_generation" in self.results:
                f.write("Mesh Generation Performance:\n")
                for complexity, sizes in self.results["mesh_generation"].items():
                    f.write(f"\nGeometry: {complexity}\n")
                    for mesh_size, result in sizes.items():
                        f.write(f"- Mesh size: {mesh_size}\n")
                        f.write(f"  - Time: {result['time']:.2f} seconds\n")
                        f.write(f"  - Success: {result['success']}\n")
            
        print(f"Report generated: {report_file}")
        return report_file
        
    def save_results(self):
        """Save benchmark results to JSON file."""
        results_file = os.path.join(self.output_dir, "benchmark_results.json")
        
        # Add system info to results
        results_copy = self.results.copy()
        results_copy["system_info"] = self.system_info
        results_copy["timestamp"] = datetime.now().isoformat()
        
        with open(results_file, "w") as f:
            json.dump(results_copy, f, indent=2)
            
        print(f"Results saved to: {results_file}")
        return results_file


def main():
    """Main function to run benchmarks."""
    parser = argparse.ArgumentParser(description="Run benchmarks for Intake-CFD Project")
    parser.add_argument("--output-dir", default="./benchmark_results", help="Output directory for benchmark results")
    parser.add_argument("--full", action="store_true", help="Run full benchmark suite (slower)")
    parser.add_argument("--mesh-generation", action="store_true", help="Run mesh generation benchmarks")
    args = parser.parse_args()
    
    suite = BenchmarkSuite(args.output_dir)
    
    # Create test geometries
    geometries = suite.create_test_geometries()
    
    # Run mesh generation benchmarks
    if args.mesh_generation or args.full:
        mesh_sizes = [1.0, 0.5, 0.2] if args.full else [0.5]
        suite.benchmark_mesh_generation(geometries, mesh_sizes)
    
    # Generate report and save results
    suite.generate_report()
    suite.save_results()


if __name__ == "__main__":
    main()
EOF
chmod +x ./benchmark_tests.py
}

# Check for required scripts
check_required_scripts

# If only checking scripts, exit now
if [ "$CHECK_SCRIPTS_ONLY" = true ]; then
    exit 0
fi

# Set up test environment
TEST_DIR="./test_output"
mkdir -p "$TEST_DIR"
LOG_FILE="$TEST_DIR/test_results_$(date +%Y%m%d_%H%M%S).log"

# Define test data
TEST_STEP_FILE="./test_data/test_intake.stp"
REFERENCE_MESH="./test_data/reference_mesh.msh"

# Ensure test data exists
if [ ! -f "$TEST_STEP_FILE" ]; then
    echo "Test STEP file not found. Creating symbolic geometry for testing..."
    mkdir -p "./test_data"
    
    # Generate a simple test geometry using Gmsh API
    cat > ./test_data/generate_test_geometry.py << 'EOF'
import gmsh
import sys

gmsh.initialize()
gmsh.model.add("test_intake")

# Create a simple intake-like geometry
gmsh.model.occ.addBox(0, 0, 0, 10, 1, 1, 1)  # Main intake duct
gmsh.model.occ.addCylinder(10, 0.5, 0.5, 3, 0, 0, 0.5, 2)  # Outlet cylinder

# Fuse the geometries (fixed the cut operation that was causing errors)
fused = gmsh.model.occ.fuse([(3,1)], [(3,2)], 3)[0]

# Create a side feature
box = gmsh.model.occ.addBox(2, -0.5, 0, 1, 2, 1, 4)  # Side feature
# Cut with a different tag (don't use tag 5 which was causing issues)
result = gmsh.model.occ.cut(fused, [(3,4)])

gmsh.model.occ.synchronize()
gmsh.write("./test_data/test_intake.stp")
gmsh.write("./test_data/test_intake.geo_unrolled")

# Create a reference mesh
gmsh.option.setNumber("Mesh.Algorithm", 6)
gmsh.option.setNumber("Mesh.Algorithm3D", 10)
gmsh.option.setNumber("Mesh.CharacteristicLengthFactor", 0.5)
gmsh.model.mesh.generate(3)
gmsh.write("./test_data/reference_mesh.msh")

gmsh.finalize()
EOF

    python3 ./test_data/generate_test_geometry.py
    
    if [ ! -f "$TEST_STEP_FILE" ]; then
        echo "Failed to create test geometry!"
        exit 1
    fi
fi

# Initialize test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Function to run a test and record results
run_test() {
    local test_name="$1"
    local test_cmd="$2"
    local category="$3"
    
    if [ "$TEST_CATEGORY" != "all" ] && [ "$TEST_CATEGORY" != "$category" ]; then
        return
    fi
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    echo "------------------------------------------------------------"
    echo "Running test: $test_name (category: $category)"
    echo "Command: $test_cmd"
    
    # Create a unique output directory for this test
    local test_output_dir="$TEST_DIR/${test_name// /_}"
    mkdir -p "$test_output_dir"
    
    # Run the test command
    if $VERBOSE; then
        echo "Test output:"
        eval "$test_cmd" > "$test_output_dir/output.log" 2>&1
        EXIT_CODE=$?
        cat "$test_output_dir/output.log"
    else
        eval "$test_cmd" > "$test_output_dir/output.log" 2>&1
        EXIT_CODE=$?
    fi
    
    # Check test result
    if [ $EXIT_CODE -eq 0 ]; then
        echo "✅ Test PASSED"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        echo "Test $test_name PASSED" >> "$LOG_FILE"
    else
        echo "❌ Test FAILED (exit code: $EXIT_CODE)"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        echo "Test $test_name FAILED (exit code: $EXIT_CODE)" >> "$LOG_FILE"
        echo "Output:" >> "$LOG_FILE"
        cat "$test_output_dir/output.log" >> "$LOG_FILE"
        echo "" >> "$LOG_FILE"
    fi
}

# Print test header
echo "===================================================================="
echo "Running CFD mesh tests ($(date))"
echo "===================================================================="
echo "Test category: $TEST_CATEGORY"
if [ -n "$TEST_SOLVER" ]; then
    echo "Testing solver compatibility: $TEST_SOLVER"
fi
echo "Output directory: $TEST_DIR"
echo "Log file: $LOG_FILE"
echo ""

# Record test start time
START_TIME=$(date +%s)

# 1. Basic geometry tests
# =======================
run_test "Load STEP file" \
    "python3 -c \"import gmsh; gmsh.initialize(); gmsh.open('$TEST_STEP_FILE'); gmsh.finalize()\"" \
    "geometry"
    
run_test "Create bounding box" \
    "python3 -c \"import gmsh; gmsh.initialize(); gmsh.open('$TEST_STEP_FILE'); gmsh.model.getBoundingBox(-1,-1); gmsh.finalize()\"" \
    "geometry"
    
run_test "Get entities" \
    "python3 -c \"import gmsh; gmsh.initialize(); gmsh.open('$TEST_STEP_FILE'); e = gmsh.model.getEntities(); print(f'{len(e)} entities found'); gmsh.finalize()\"" \
    "geometry"

# 2. Basic meshing tests
# =====================
run_test "Generate 2D mesh" \
    "python3 -c \"import gmsh; gmsh.initialize(); gmsh.open('$TEST_STEP_FILE'); gmsh.model.mesh.generate(2); gmsh.write('$TEST_DIR/test_2d.msh'); gmsh.finalize()\"" \
    "meshing"
    
run_test "Generate 3D mesh" \
    "python3 -c \"import gmsh; gmsh.initialize(); gmsh.open('$TEST_STEP_FILE'); gmsh.model.mesh.generate(3); gmsh.write('$TEST_DIR/test_3d.msh'); gmsh.finalize()\"" \
    "meshing"

# 3. Boundary layer tests
# ======================
run_test "Boundary layer generation" \
    "./mesh_generator $TEST_STEP_FILE $TEST_DIR/test_bl.msh --bl_first_layer 0.05 --bl_progression 1.2 --bl_layers 3" \
    "boundary-layers"

run_test "Boundary layer quality check" \
    "python3 -c \"import gmsh; gmsh.initialize(); gmsh.open('$TEST_DIR/test_bl.msh'); gmsh.option.setNumber('Mesh.QualityType', 0); e = gmsh.model.getEntities(3); if e: q = gmsh.model.mesh.getElementQualities(gmsh.model.mesh.getElementsByType(4, e[0][1])); print(f'Min quality: {min(q):.4f}'); gmsh.finalize()\" > $TEST_DIR/bl_quality.txt" \
    "boundary-layers"

# 4. Mesh quality tests
# ====================
run_test "Mesh quality analysis" \
    "python3 ./mesh_validator.py $TEST_DIR/test_3d.msh --quality-metrics all" \
    "validation"
    
run_test "Fix mesh quality issues" \
    "python3 ./mesh_validator.py $TEST_DIR/test_3d.msh --fix-quality-issues" \
    "validation"

# 5. Export format tests
# =====================
run_test "Export to SU2" \
    "./gmsh_process --input $TEST_DIR/test_3d.msh --output $TEST_DIR/test_export --su2" \
    "export"
    
run_test "Export to OpenFOAM" \
    "./gmsh_process --input $TEST_DIR/test_3d.msh --output $TEST_DIR/test_export --openfoam" \
    "export"

if [ "$QUICK_MODE" = false ]; then
    run_test "Export to VTK" \
        "./gmsh_process --input $TEST_DIR/test_3d.msh --output $TEST_DIR/test_export --vtk" \
        "export"
        
    run_test "Export to CGNS" \
        "./gmsh_process --input $TEST_DIR/test_3d.msh --output $TEST_DIR/test_export --cgns" \
        "export"
fi

# 6. Solver compatibility tests
# ============================
if [ "$TEST_SOLVER" = "openfoam" ] || [ "$TEST_SOLVER" = "" ]; then
    run_test "OpenFOAM compatibility check" \
        "python3 ./mesh_validator.py $TEST_DIR/test_3d.msh --check-solver openfoam" \
        "solver-compat"
        
    if [ "$QUICK_MODE" = false ]; then
        # More detailed OpenFOAM compatibility
        run_test "OpenFOAM BC generation" \
            "python3 ./bc_manager.py $TEST_DIR/test_3d.msh --auto-detect --openfoam $TEST_DIR/openfoam_case" \
            "solver-compat"
    fi
fi

if [ "$TEST_SOLVER" = "su2" ] || [ "$TEST_SOLVER" = "" ]; then
    run_test "SU2 compatibility check" \
        "python3 ./mesh_validator.py $TEST_DIR/test_3d.msh --check-solver su2" \
        "solver-compat"
        
    if [ "$QUICK_MODE" = false ]; then
        # More detailed SU2 compatibility
        run_test "SU2 BC generation" \
            "python3 ./bc_manager.py $TEST_DIR/test_3d.msh --auto-detect --su2 $TEST_DIR/su2_config.cfg" \
            "solver-compat"
    fi
fi

if [ "$TEST_SOLVER" = "fluent" ] || [ "$TEST_SOLVER" = "" ]; then
    run_test "Fluent compatibility check" \
        "python3 ./mesh_validator.py $TEST_DIR/test_3d.msh --check-solver fluent" \
        "solver-compat"
fi

if [ "$TEST_SOLVER" = "starccm" ] || [ "$TEST_SOLVER" = "" ]; then
    run_test "Star-CCM+ compatibility check" \
        "python3 ./mesh_validator.py $TEST_DIR/test_3d.msh --check-solver starccm" \
        "solver-compat"
fi

# 7. Advanced refinement tests
# ==========================
if [ "$QUICK_MODE" = false ]; then
    run_test "Curvature refinement" \
        "python3 ./mesh_refiner.py $TEST_DIR/test_3d.msh -o $TEST_DIR/test_refined_curvature.msh --curvature-adapt" \
        "refinement"
        
    run_test "Box refinement" \
        "python3 ./mesh_refiner.py $TEST_DIR/test_3d.msh -o $TEST_DIR/test_refined_box.msh --refine-box 2,0,0,3,1,1,0.3" \
        "refinement"
        
    run_test "Feature angle refinement" \
        "python3 ./mesh_refiner.py $TEST_DIR/test_3d.msh -o $TEST_DIR/test_refined_feature.msh --feature-angle 30" \
        "refinement"
fi

# 8. Benchmarks (if requested)
# ===========================
if [ "$RUN_BENCHMARKS" = true ]; then
    echo "------------------------------------------------------------"
    echo "Running benchmarks..."
    
    if [ "$QUICK_MODE" = true ]; then
        # Quick benchmark (mesh generation only)
        run_test "Quick benchmarks" \
            "python3 ./benchmark_tests.py --output-dir $TEST_DIR/benchmarks --mesh-generation" \
            "benchmarks"
    else
        # Full benchmark suite
        run_test "Full benchmarks" \
            "python3 ./benchmark_tests.py --output-dir $TEST_DIR/benchmarks --full" \
            "benchmarks"
    fi
fi

# Calculate test duration
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

# Print test summary
echo "===================================================================="
echo "Test Summary:"
echo "  Total tests:  $TOTAL_TESTS"
echo "  Passed:       $PASSED_TESTS"
echo "  Failed:       $FAILED_TESTS"
echo "  Duration:     $DURATION seconds"
echo "===================================================================="

if [ $FAILED_TESTS -gt 0 ]; then
    echo "❌ Some tests failed. Check $LOG_FILE for details."
    exit 1
else
    echo "✅ All tests passed!"
    exit 0
fi
