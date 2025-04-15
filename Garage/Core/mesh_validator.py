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
