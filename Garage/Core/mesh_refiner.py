#!/usr/bin/env python3
# filepath: /mnt/c/Users/Mohammed/Desktop/Intake-CFD-Project/nx/mesh_refiner.py

import sys
import os
import argparse
import numpy as np
import gmsh
import time
from enum import Enum
from typing import List, Tuple, Dict, Optional, Union

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
        
        # Options for progressive refinement
        self.progressive = False
        self.iterations = 3
        self.target_quality = 0.3
        
    def initialize(self, verbose=True):
        """Initialize Gmsh and load the mesh if provided."""
        gmsh.initialize()
        gmsh.option.setNumber("General.Terminal", 1 if verbose else 0)
        
        if self.mesh_file:
            try:
                gmsh.open(self.mesh_file)
                self.mesh_initialized = True
                
                # Check if it's a volume mesh
                entities = gmsh.model.getEntities(3)
                self.is_volume_mesh = len(entities) > 0
                
                if verbose:
                    print(f"Successfully loaded mesh: {self.mesh_file}")
                    print(f"Mesh type: {'Volume' if self.is_volume_mesh else 'Surface'}")
                
                # Get default mesh size from the model
                self.default_mesh_size = self._get_default_mesh_size()
                
            except Exception as e:
                gmsh.finalize()
                raise RuntimeError(f"Failed to open mesh file: {str(e)}")
    
    def _get_default_mesh_size(self):
        """Get an average mesh size from the existing elements."""
        try:
            # Calculate characteristic length from existing mesh
            size = 0.0
            count = 0
            
            # Check mesh elements based on mesh type
            dim = 3 if self.is_volume_mesh else 2
            entities = gmsh.model.getEntities(dim)
            
            for entity in entities:
                element_types = gmsh.model.mesh.getElementTypes(entity[0], entity[1])
                
                for elem_type in element_types:
                    # Get elements of this type
                    elements, _ = gmsh.model.mesh.getElementsByType(elem_type, entity[1], entity[0])
                    count += len(elements)
                    
                    # Sample some elements to get average size
                    if len(elements) > 0:
                        sample_count = min(len(elements), 100)
                        for i in range(sample_count):
                            elem_idx = elements[i * len(elements) // sample_count]
                            # Get node coordinates
                            node_tags = gmsh.model.mesh.getElement(elem_idx)[1]
                            node_coords = [gmsh.model.mesh.getNode(tag)[0] for tag in node_tags]
                            
                            # Compute rough element size as max distance between nodes
                            max_dist = 0.0
                            for i in range(len(node_coords)):
                                for j in range(i+1, len(node_coords)):
                                    dist = np.linalg.norm(np.array(node_coords[i]) - np.array(node_coords[j]))
                                    max_dist = max(max_dist, dist)
                            
                            size += max_dist
                            
            return size / count if count > 0 else 1.0
            
        except Exception as e:
            print(f"Warning: Could not determine default mesh size: {str(e)}")
            return 1.0
    
    def add_refinement_region(self, refine_type, params):
        """Add a region to refine."""
        self.refinement_regions.append((refine_type, params))
        
    def add_box_refinement(self, x_min, y_min, z_min, x_max, y_max, z_max, size_factor=0.5):
        """Add a box region to refine."""
        self.add_refinement_region(
            RefinementType.BOX, 
            {
                'x_min': x_min, 'y_min': y_min, 'z_min': z_min, 
                'x_max': x_max, 'y_max': y_max, 'z_max': z_max,
                'size_factor': size_factor
            }
        )
        
    def add_cylinder_refinement(self, x, y, z, dx, dy, dz, r, size_factor=0.5):
        """Add a cylindrical region to refine."""
        self.add_refinement_region(
            RefinementType.CYLINDER, 
            {
                'x': x, 'y': y, 'z': z,  # base point
                'dx': dx, 'dy': dy, 'dz': dz,  # axis direction
                'r': r,  # radius
                'size_factor': size_factor
            }
        )
        
    def add_sphere_refinement(self, x, y, z, r, size_factor=0.5):
        """Add a spherical region to refine."""
        self.add_refinement_region(
            RefinementType.SPHERE, 
            {
                'x': x, 'y': y, 'z': z,  # center
                'r': r,  # radius
                'size_factor': size_factor
            }
        )
        
    def add_surface_refinement(self, surface_id, size_factor=0.5):
        """Add a surface to refine."""
        self.add_refinement_region(
            RefinementType.SURFACE, 
            {
                'surface_id': surface_id,
                'size_factor': size_factor
            }
        )
        
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

        # Set global meshing parameters
        gmsh.option.setNumber("Mesh.CharacteristicLengthMin", self.min_size if self.min_size > 0 else self.default_mesh_size * 0.1)
        gmsh.option.setNumber("Mesh.CharacteristicLengthMax", self.max_size if self.max_size < float('inf') else self.default_mesh_size * 2.0)
        
        # Global refinement
        if self.refinement_level > 1:
            print(f"Applying global refinement (level {self.refinement_level})...")
            gmsh.option.setNumber("Mesh.CharacteristicLengthFactor", 1.0 / self.refinement_level)
        
        # Curvature-based refinement
        if self.curvature_adapt:
            print("Enabling curvature-based mesh adaptation...")
            gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 1)
            gmsh.option.setNumber("Mesh.MeshSizeFromCurvatureIsotropic", 1)
            # Adjust the number of points per 2π circle
            min_points = 10 + self.refinement_level * 5
            gmsh.option.setNumber("Mesh.MinimumCirclePoints", min_points)
            gmsh.option.setNumber("Mesh.MinimumCurvePoints", min_points // 2)
            
        # Feature angle detection
        if self.feature_angle < 90.0:
            print(f"Detecting features with angle threshold: {self.feature_angle}°...")
            gmsh.option.setNumber("Mesh.AngleToleranceFacetOverlap", self.feature_angle)
            gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 1)
            
            # Create a Threshold field to refine at detected features
            feature_field = gmsh.model.mesh.field.add("MathEval")
            gmsh.model.mesh.field.setString(feature_field, "F", f"0.3 * F")
            gmsh.model.mesh.field.setAsBackgroundMesh(feature_field)
            
        # Apply specific refinement regions
        fields = []
        
        for i, (refine_type, params) in enumerate(self.refinement_regions):
            if refine_type == RefinementType.BOX:
                field_id = self._create_box_field(params)
                fields.append(field_id)
                
            elif refine_type == RefinementType.SPHERE:
                field_id = self._create_sphere_field(params)
                fields.append(field_id)
                
            elif refine_type == RefinementType.CYLINDER:
                field_id = self._create_cylinder_field(params)
                fields.append(field_id)
                
            elif refine_type == RefinementType.SURFACE:
                field_id = self._create_surface_field(params)
                fields.append(field_id)
                
        # Combine fields if there are more than one
        if len(fields) > 1:
            print(f"Combining {len(fields)} refinement regions...")
            min_field = gmsh.model.mesh.field.add("Min")
            gmsh.model.mesh.field.setNumbers(min_field, "FieldsList", fields)
            gmsh.model.mesh.field.setAsBackgroundMesh(min_field)
        elif len(fields) == 1:
            gmsh.model.mesh.field.setAsBackgroundMesh(fields[0])
            
        # Remesh
        print("Remeshing...")
        dim = 3 if self.is_volume_mesh else 2
        gmsh.model.mesh.generate(dim)
        
        # Apply smoothing
        print("Applying mesh smoothing...")
        gmsh.option.setNumber("Mesh.Smoothing", 5)  # Number of smoothing steps
        gmsh.model.mesh.optimize("Netgen")
        
        # Save the refined mesh
        gmsh.write(self.output_file)
        print(f"Refined mesh saved to: {self.output_file}")
        
        return self.output_file
        
    def _create_box_field(self, params):
        """Create a box field for refinement."""
        field = gmsh.model.mesh.field.add("Box")
        gmsh.model.mesh.field.setNumber(field, "VIn", self.default_mesh_size * params['size_factor'])
        gmsh.model.mesh.field.setNumber(field, "VOut", self.default_mesh_size)
        gmsh.model.mesh.field.setNumber(field, "XMin", params['x_min'])
        gmsh.model.mesh.field.setNumber(field, "YMin", params['y_min'])
        gmsh.model.mesh.field.setNumber(field, "ZMin", params['z_min'])
        gmsh.model.mesh.field.setNumber(field, "XMax", params['x_max'])
        gmsh.model.mesh.field.setNumber(field, "YMax", params['y_max'])
        gmsh.model.mesh.field.setNumber(field, "ZMax", params['z_max'])
        return field
        
    def _create_sphere_field(self, params):
        """Create a sphere field for refinement."""
        field = gmsh.model.mesh.field.add("Ball")
        gmsh.model.mesh.field.setNumber(field, "VIn", self.default_mesh_size * params['size_factor'])
        gmsh.model.mesh.field.setNumber(field, "VOut", self.default_mesh_size)
        gmsh.model.mesh.field.setNumber(field, "XCenter", params['x'])
        gmsh.model.mesh.field.setNumber(field, "YCenter", params['y'])
        gmsh.model.mesh.field.setNumber(field, "ZCenter", params['z'])
        gmsh.model.mesh.field.setNumber(field, "Radius", params['r'])
        return field
        
    def _create_cylinder_field(self, params):
        """Create a cylinder field for refinement."""
        # For a cylinder, we'll use a Cylinder field
        field = gmsh.model.mesh.field.add("Cylinder")
        gmsh.model.mesh.field.setNumber(field, "VIn", self.default_mesh_size * params['size_factor'])
        gmsh.model.mesh.field.setNumber(field, "VOut", self.default_mesh_size)
        gmsh.model.mesh.field.setNumber(field, "XCenter", params['x'])
        gmsh.model.mesh.field.setNumber(field, "YCenter", params['y'])
        gmsh.model.mesh.field.setNumber(field, "ZCenter", params['z'])
        gmsh.model.mesh.field.setNumber(field, "XAxis", params['dx'])
        gmsh.model.mesh.field.setNumber(field, "YAxis", params['dy'])
        gmsh.model.mesh.field.setNumber(field, "ZAxis", params['dz'])
        gmsh.model.mesh.field.setNumber(field, "Radius", params['r'])
        return field
        
    def _create_surface_field(self, params):
        """Create a distance field for surface refinement."""
        # First create a distance field from the surface
        distance_field = gmsh.model.mesh.field.add("Distance")
        gmsh.model.mesh.field.setNumbers(distance_field, "FacesList", [params['surface_id']])
        
        # Then create a threshold field based on the distance
        threshold_field = gmsh.model.mesh.field.add("Threshold")
        gmsh.model.mesh.field.setNumber(threshold_field, "IField", distance_field)
        gmsh.model.mesh.field.setNumber(threshold_field, "LcMin", self.default_mesh_size * params['size_factor'])
        gmsh.model.mesh.field.setNumber(threshold_field, "LcMax", self.default_mesh_size)
        gmsh.model.mesh.field.setNumber(threshold_field, "DistMin", 0)
        gmsh.model.mesh.field.setNumber(threshold_field, "DistMax", self.default_mesh_size * 2)
        
        return threshold_field
    
    def refine_boundary_layers(self, first_layer_thickness=None, growth_rate=1.2, num_layers=5):
        """Refine boundary layers post-generation."""
        if not self.mesh_initialized:
            self.initialize()
            
        print("Refining boundary layers...")
        
        if first_layer_thickness is None:
            # Estimate a good first layer thickness based on mesh size
            first_layer_thickness = self.default_mesh_size * 0.1
        
        # Get boundary surfaces
        boundary_surfaces = []
        all_surfaces = gmsh.model.getEntities(2)
        
        # If it's a volume mesh, get surfaces that are on the boundary
        if self.is_volume_mesh:
            for surface in all_surfaces:
                adj_volumes = gmsh.model.getAdjacencies(2, surface[1])
                if len(adj_volumes[0]) == 1:  # Only one adjacent volume = boundary
                    boundary_surfaces.append(surface)
        else:
            # For surface mesh, use all surfaces
            boundary_surfaces = all_surfaces
            
        print(f"Found {len(boundary_surfaces)} boundary surfaces")
        
        if not boundary_surfaces:
            print("No boundary surfaces found for boundary layer refinement")
            return
        
        # Get the boundary edges
        boundary_edges = []
        for surface in boundary_surfaces:
            edges = gmsh.model.getBoundary([surface], combined=False, oriented=False)
            boundary_edges.extend(edges)
        
        # Remove duplicates (edges might belong to multiple surfaces)
        boundary_edge_tags = list(set(edge[1] for edge in boundary_edges))
        print(f"Found {len(boundary_edge_tags)} unique boundary edges")
        
        # Create boundary layer field
        bl_field = gmsh.model.mesh.field.add("BoundaryLayer")
        gmsh.model.mesh.field.setNumbers(bl_field, "EdgesList", boundary_edge_tags)
        gmsh.model.mesh.field.setNumber(bl_field, "Size", first_layer_thickness)
        gmsh.model.mesh.field.setNumber(bl_field, "Ratio", growth_rate)
        gmsh.model.mesh.field.setNumber(bl_field, "Quads", 1)  # Try to generate quads/prisms/hexas
        gmsh.model.mesh.field.setNumber(bl_field, "Thickness", first_layer_thickness * growth_rate ** (num_layers - 1) * 1.5)  # Estimate total thickness
        
        # Apply the field
        gmsh.model.mesh.field.setAsBackgroundMesh(bl_field)
        
        # Remesh with boundary layers
        print("Remeshing with boundary layers...")
        dim = 3 if self.is_volume_mesh else 2
        gmsh.model.mesh.generate(dim)
        
        if self.output_file:
            gmsh.write(self.output_file)
            print(f"Mesh with refined boundary layers saved to: {self.output_file}")
        else:
            base, ext = os.path.splitext(self.mesh_file)
            output = f"{base}_with_bl{ext}"
            gmsh.write(output)
            print(f"Mesh with refined boundary layers saved to: {output}")
            
    def smooth_mesh(self, iterations=5, quality_threshold=0.1):
        """Apply mesh smoothing to improve quality."""
        if not self.mesh_initialized:
            self.initialize()
            
        print(f"Applying mesh smoothing ({iterations} iterations)...")
        
        # Set quality threshold
        gmsh.option.setNumber("Mesh.OptimizeThreshold", quality_threshold)
        
        # Apply smoothing
        for i in range(iterations):
            print(f"Smoothing iteration {i+1}/{iterations}...")
            gmsh.model.mesh.optimize("Relocate2D")
            if self.is_volume_mesh:
                gmsh.model.mesh.optimize("Relocate3D")
        
        # Final Netgen optimization
        print("Applying final Netgen optimization...")
        gmsh.model.mesh.optimize("Netgen")
        
        if self.output_file:
            gmsh.write(self.output_file)
            print(f"Smoothed mesh saved to: {self.output_file}")
        else:
            base, ext = os.path.splitext(self.mesh_file)
            output = f"{base}_smoothed{ext}"
            gmsh.write(output)
            print(f"Smoothed mesh saved to: {output}")
    
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
    
    # Global refinement options
    parser.add_argument("--refine-level", type=int, default=1, help="Global refinement level (1-5)")
    parser.add_argument("--curvature-adapt", action="store_true", help="Enable curvature-based adaptation")
    parser.add_argument("--feature-angle", type=float, default=30.0, help="Angle for feature detection (10-90)")
    parser.add_argument("--min-size", type=float, default=0, help="Minimum element size")
    parser.add_argument("--max-size", type=float, default=float('inf'), help="Maximum element size")
    
    # Specific refinement regions
    parser.add_argument("--refine-box", help="Refine mesh within box: x1,y1,z1,x2,y2,z2,factor")
    parser.add_argument("--refine-sphere", help="Refine mesh within sphere: x,y,z,r,factor")
    parser.add_argument("--refine-cylinder", help="Refine mesh within cylinder: x,y,z,dx,dy,dz,r,factor")
    parser.add_argument("--refine-surface", help="Refine mesh near surface: surface_id,factor")
    
    # Boundary layer refinement
    parser.add_argument("--refine-bl", action="store_true", help="Refine boundary layers")
    parser.add_argument("--bl-first-layer", type=float, help="First boundary layer thickness")
    parser.add_argument("--bl-growth-rate", type=float, default=1.2, help="Boundary layer growth rate")
    parser.add_argument("--bl-layers", type=int, default=5, help="Number of boundary layers")
    
    # Mesh smoothing
    parser.add_argument("--smooth", action="store_true", help="Apply mesh smoothing")
    parser.add_argument("--smooth-iterations", type=int, default=5, help="Number of smoothing iterations")
    parser.add_argument("--quality-threshold", type=float, default=0.1, help="Quality threshold for smoothing")
    
    args = parser.parse_args()
    
    try:
        refiner = MeshRefiner(args.input_mesh)
        refiner.initialize()
        
        # Set global options
        refiner.refinement_level = args.refine_level
        refiner.curvature_adapt = args.curvature_adapt
        refiner.feature_angle = args.feature_angle
        refiner.min_size = args.min_size
        refiner.max_size = args.max_size
        
        # Add specific refinement regions
        if args.refine_box:
            parts = list(map(float, args.refine_box.split(',')))
            if len(parts) == 7:
                refiner.add_box_refinement(parts[0], parts[1], parts[2], parts[3], parts[4], parts[5], parts[6])
            else:
                print("Error: Box refinement requires 7 values: x1,y1,z1,x2,y2,z2,factor")
                
        if args.refine_sphere:
            parts = list(map(float, args.refine_sphere.split(',')))
            if len(parts) == 5:
                refiner.add_sphere_refinement(parts[0], parts[1], parts[2], parts[3], parts[4])
            else:
                print("Error: Sphere refinement requires 5 values: x,y,z,r,factor")
                
        if args.refine_cylinder:
            parts = list(map(float, args.refine_cylinder.split(',')))
            if len(parts) == 8:
                refiner.add_cylinder_refinement(parts[0], parts[1], parts[2], parts[3], parts[4], parts[5], parts[6], parts[7])
            else:
                print("Error: Cylinder refinement requires 8 values: x,y,z,dx,dy,dz,r,factor")
                
        if args.refine_surface:
            parts = args.refine_surface.split(',')
            if len(parts) == 2:
                refiner.add_surface_refinement(int(parts[0]), float(parts[1]))
            else:
                print("Error: Surface refinement requires 2 values: surface_id,factor")
        
        # Apply refinements
        if args.output:
            refiner.output_file = args.output
            
        # Basic refinement
        if (args.refine_level > 1 or args.curvature_adapt or args.feature_angle < 90.0 or 
            args.refine_box or args.refine_sphere or args.refine_cylinder or args.refine_surface):
            refiner.refine_mesh()
            
        # Boundary layer refinement
        if args.refine_bl:
            refiner.refine_boundary_layers(
                first_layer_thickness=args.bl_first_layer,
                growth_rate=args.bl_growth_rate,
                num_layers=args.bl_layers
            )
            
        # Smoothing
        if args.smooth:
            refiner.smooth_mesh(
                iterations=args.smooth_iterations,
                quality_threshold=args.quality_threshold
            )
            
        refiner.finalize()
        
    except Exception as e:
        print(f"Error: {str(e)}")
        if refiner:
            refiner.finalize()
        sys.exit(1)


if __name__ == "__main__":
    main()