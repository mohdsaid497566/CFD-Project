#!/usr/bin/env python3
"""
Enhanced GMSH process script for handling problematic STEP files
with improved memory management and geometry healing options.

Usage: 
    ./gmsh_process.py --input <step_file> --output <mesh_file> [options]
"""

import os
import sys
import time
import argparse
import traceback
import gmsh
import numpy as np
import psutil

def get_available_memory_gb():
    """Get available system memory in GB"""
    return psutil.virtual_memory().available / (1024**3)

def process_step_file(
        step_file,
        output_msh,
        mesh_size=1.0,
        boundary_layers=True,
        bl_thickness=0.01, 
        bl_layers=5,
        domain_scale=2.0,
        num_threads=4,
        mesh_algorithm_3d=1,   # 1=Delaunay is most reliable (optionally try 4 or 10)
        mesh_algorithm_2d=6,   # 6=Frontal-Delaunay, 5=Delaunay as fallback
        optimize_netgen=True,  
        debug=False,
        validate_geometry=True,
        memory_limit=None
    ):
    """
    Process a STEP file to generate a mesh
    
    Args:
        step_file: Path to input STEP file
        output_msh: Path to output mesh file
        mesh_size: Base mesh size
        boundary_layers: Whether to add boundary layers
        bl_thickness: Boundary layer thickness
        bl_layers: Number of boundary layers
        domain_scale: Scale factor for domain size relative to geometry
        num_threads: Number of threads for meshing
        mesh_algorithm_3d: 3D meshing algorithm (1=Delaunay, 10=HXT)
        mesh_algorithm_2d: 2D meshing algorithm (6=Frontal-Delaunay, 5=Delaunay)
        optimize_netgen: Whether to use Netgen optimizer
        debug: Enable debug output
        validate_geometry: Enable geometry validation
    """
    # Memory monitoring
    start_mem = get_available_memory_gb()
    
    if memory_limit is None:
        memory_limit = max(2.0, 0.8 * psutil.virtual_memory().total / (1024**3))
    
    print(f"Available memory: {start_mem:.2f} GB, limit set to {memory_limit:.2f} GB")
    
    # Start timing
    start_time = time.time()
    
    # Initialize Gmsh
    gmsh.initialize()
    
    try:
        if debug:
            gmsh.option.setNumber("General.Terminal", 1)
            gmsh.option.setNumber("General.Verbosity", 99)
        # --- Speed Improvement: Multi-threading ---
        # Set number of threads for parallel mesh generation (if Gmsh is compiled with OpenMP)
        # See api/multi_thread.py
        gmsh.option.setNumber("General.NumThreads", num_threads)

        # Set memory limit
        gmsh.option.setNumber("Mesh.MemoryMax", memory_limit * 1024)  # Convert to MB
        
        # Create model
        model_name = os.path.basename(step_file).split('.')[0]
        gmsh.model.add(f"{model_name}_cfd")

        # Enable geometry healing options for robust STEP import
        if validate_geometry:
            gmsh.option.setNumber("Geometry.OCCFixDegenerated", 1)
            gmsh.option.setNumber("Geometry.OCCFixSmallEdges", 1)
            gmsh.option.setNumber("Geometry.OCCFixSmallFaces", 1)
            gmsh.option.setNumber("Geometry.OCCSewFaces", 1)
            gmsh.option.setNumber("Geometry.OCCMakeSolids", 1)
            gmsh.option.setNumber("Geometry.Tolerance", 1e-2)
            gmsh.option.setNumber("Geometry.ToleranceBoolean", 1e-2)

        # --- Geometry Import and Preparation ---
        print(f"Loading STEP file: {step_file}")
        ents_before = gmsh.model.getEntities()
        
        # Try three different import methods with increasing robustness
        try:
            # Method 1: OpenCASCADE importShapes (most accurate but can fail)
            print("Attempting OpenCASCADE importShapes...")
            gmsh.model.occ.importShapes(step_file)
            gmsh.model.occ.removeAllDuplicates()
            gmsh.model.occ.healShapes()
            gmsh.model.occ.synchronize()
            print("Successfully imported using OpenCASCADE")
        except Exception as e:
            print(f"OpenCASCADE importShapes failed: {e}")
            try:
                # Method 2: Direct merge (more forgiving)
                print("Attempting direct merge...")
                gmsh.merge(step_file)
                print("Successfully imported using direct merge")
            except Exception as e:
                print(f"Direct merge failed: {e}")
                # Method 3: Create simplified box domain (fallback)
                print("Creating simplified box domain as fallback...")
                # Create a 100x50x30 box as a fallback
                box = gmsh.model.occ.addBox(0, 0, 0, 100, 50, 30)
                gmsh.model.occ.synchronize()
                print("Created fallback box geometry")
                
        # Get all surfaces, representing intake geometry
        ents_after = gmsh.model.getEntities()
        intake_surfaces_dimtags = [e for e in ents_after if e not in ents_before and e[0] == 2]

        if not intake_surfaces_dimtags:
            print("Warning: No surface entities found directly. Checking for volumes...")
            volumes = gmsh.model.getEntities(3)
            if volumes:
                print(f"Found {len(volumes)} volumes, extracting their surfaces...")
                for volume_dim, volume_tag in volumes:
                    surfaces = gmsh.model.getBoundary([(volume_dim, volume_tag)], 
                                                    combined=False, oriented=False)
                    intake_surfaces_dimtags.extend([s for s in surfaces if s[0] == 2])
            
            if not intake_surfaces_dimtags:
                raise ValueError("No 2D (Surface) entities found after importing STEP file.")
                
        print(f"Found {len(intake_surfaces_dimtags)} intake surfaces initially.")

        # Validate bounding box
        xmin, ymin, zmin, xmax, ymax, zmax = gmsh.model.getBoundingBox(-1, -1)
        if debug:
            print(f"Model bounds: X[{xmin},{xmax}] Y[{ymin},{ymax}] Z[{zmin},{zmax}]")

        if abs(xmax-xmin) < 1e-6 or abs(ymax-ymin) < 1e-6 or abs(zmax-zmin) < 1e-6:
            print("Warning: Invalid model dimensions detected, adjusting...")
            if abs(xmax-xmin) < 1e-6: 
                xmax = xmin + 100.0
            if abs(ymax-ymin) < 1e-6:
                ymax = ymin + 50.0
            if abs(zmax-zmin) < 1e-6:
                zmax = zmin + 30.0
                
        gmsh.model.occ.synchronize()

        # --- Domain Creation ---
        print("Creating fluid domain...")
        domain_scale = max(domain_scale, 1.5)
        domain_center_x = (xmin + xmax) / 2
        domain_center_y = (ymin + ymax) / 2
        domain_center_z = (zmin + zmax) / 2
        max_dim = max(xmax - xmin, ymax - ymin, zmax - zmin)
        if max_dim <= 0:
             raise ValueError(f"Invalid bounding box dimensions calculated: max_dim = {max_dim}. Check input geometry.")
             
        dx = max_dim * domain_scale
        dy = max_dim * domain_scale
        dz = max_dim * domain_scale

        domain_vol = gmsh.model.occ.addBox(
            domain_center_x - dx / 2, domain_center_y - dy / 2, domain_center_z - dz / 2,
            dx, dy, dz
        )
        gmsh.model.occ.synchronize()

        # --- Boolean Operation (Fragment) ---
        print("Fragmenting domain with intake surfaces...")
        try:
            out_vols, out_map = gmsh.model.occ.fragment(
                [(3, domain_vol)], intake_surfaces_dimtags
            )
            gmsh.model.occ.synchronize()
        except Exception as e:
            print(f"Warning: Boolean fragmentation failed: {e}")
            print("Proceeding with just the outer box domain")
            out_vols = [(3, domain_vol)]
            out_map = []
        
        # Find fluid volume (the biggest one)
        fluid_volume_tag = domain_vol
        max_volume = 0.0
        for dim, tag in out_vols:
            if dim == 3:
                # Calculate volume
                mass = gmsh.model.occ.getMass(dim, tag)
                if mass > max_volume:
                    max_volume = mass
                    fluid_volume_tag = tag

        print(f"Using volume tag {fluid_volume_tag} as fluid domain (volume = {max_volume})")
        
        # --- Surface Identification ---
        print("Identifying surfaces for boundary conditions...")
        
        # Find the intake surfaces after fragmentation
        final_intake_surface_tags = []
        for i in range(len(intake_surfaces_dimtags)):
            if i < len(out_map):
                fragments = out_map[i]
                for dim, tag in fragments:
                    if dim == 2:
                        final_intake_surface_tags.append(tag)
            else:
                print(f"Warning: No map found for original surface index {i}.")

        if not final_intake_surface_tags:
            print("Warning: Could not map original intake surfaces. Boundary layers might be incorrect.")
            # Attempt fallback (less reliable)
            fluid_boundary_dimtags = gmsh.model.getBoundary([(3,fluid_volume_tag)], combined=False, oriented=False, recursive=False)
            domain_box_surfaces = gmsh.model.getBoundary([(3,domain_vol)], combined=False, oriented=False, recursive=False)
            domain_box_surface_tags = [s[1] for s in domain_box_surfaces if s[0] == 2]
            final_intake_surface_tags = [s[1] for s in fluid_boundary_dimtags if s[0] == 2 and s[1] not in domain_box_surface_tags]

        if not final_intake_surface_tags:
            print("Warning: Could not identify intake surfaces, using all boundary surfaces.")
            fluid_boundary_dimtags = gmsh.model.getBoundary([(3,fluid_volume_tag)], combined=False, oriented=False, recursive=False)
            final_intake_surface_tags = [s[1] for s in fluid_boundary_dimtags if s[0] == 2]
        
        # Create physical groups for boundary conditions
        inlet_group = gmsh.model.addPhysicalGroup(2, final_intake_surface_tags, name="intake_walls")
        
        # Find domain boundary surfaces (outlet, symmetry, etc.)
        fluid_boundary_dimtags = gmsh.model.getBoundary([(3,fluid_volume_tag)], combined=False, oriented=False, recursive=False)
        outlet_surface_tags = [s[1] for s in fluid_boundary_dimtags if s[0] == 2 and s[1] not in final_intake_surface_tags]
        
        if outlet_surface_tags:
            outlet_group = gmsh.model.addPhysicalGroup(2, outlet_surface_tags, name="outlet")
        
        # Create physical group for volume
        volume_group = gmsh.model.addPhysicalGroup(3, [fluid_volume_tag], name="fluid_volume")
        
        # --- Meshing Setup ---
        print("Setting up mesh parameters...")
        
        # Set mesh sizes
        gmsh.option.setNumber("Mesh.CharacteristicLengthMin", mesh_size / 2)
        gmsh.option.setNumber("Mesh.CharacteristicLengthMax", mesh_size)
        
        # Set mesh algorithms
        gmsh.option.setNumber("Mesh.Algorithm", mesh_algorithm_2d)
        gmsh.option.setNumber("Mesh.Algorithm3D", mesh_algorithm_3d)
        
        # Binary output for speed
        gmsh.option.setNumber("Mesh.Binary", 1)
        
        # Optimization
        if optimize_netgen:
            gmsh.option.setNumber("Mesh.OptimizeNetgen", 1)
            gmsh.option.setNumber("Mesh.Optimize", 1)
        else:
            gmsh.option.setNumber("Mesh.OptimizeNetgen", 0)
            gmsh.option.setNumber("Mesh.Optimize", 1)  # Basic optimization only
            
        # Recombination for quads/hexes
        gmsh.option.setNumber("Mesh.RecombineAll", 0)  # Set to 1 for hex mesh
        
        # --- Add boundary layers if requested ---
        if boundary_layers and final_intake_surface_tags:
            print("Setting up boundary layers...")
            
            try:
                # Fields for boundary layer
                dist_field = gmsh.model.mesh.field.add("Distance")
                gmsh.model.mesh.field.setNumbers(dist_field, "EdgesList", [])
                gmsh.model.mesh.field.setNumbers(dist_field, "FacesList", final_intake_surface_tags)
                
                # Threshold field
                threshold_field = gmsh.model.mesh.field.add("Threshold")
                gmsh.model.mesh.field.setNumber(threshold_field, "IField", dist_field)
                gmsh.model.mesh.field.setNumber(threshold_field, "LcMin", mesh_size / 5)
                gmsh.model.mesh.field.setNumber(threshold_field, "LcMax", mesh_size)
                gmsh.model.mesh.field.setNumber(threshold_field, "DistMin", 0.5 * bl_thickness)
                gmsh.model.mesh.field.setNumber(threshold_field, "DistMax", bl_thickness * 3)
                
                # Boundary layer field
                bl_field_tag = gmsh.model.mesh.field.add("BoundaryLayer")
                
                # Set boundary layer parameters
                gmsh.model.mesh.field.setNumbers(bl_field_tag, "FacesList", final_intake_surface_tags)
                gmsh.model.mesh.field.setNumber(bl_field_tag, "Quads", 0)  # 0 for triangles, 1 for quads
                gmsh.model.mesh.field.setNumber(bl_field_tag, "Ratio", 1.2)  # Growth ratio
                gmsh.model.mesh.field.setNumber(bl_field_tag, "Size", bl_thickness)
                gmsh.model.mesh.field.setNumber(bl_field_tag, "NLayers", bl_layers)
                gmsh.model.mesh.field.setAsBoundaryLayer(bl_field_tag)
                
                print("Boundary Layer Field configured.")
            except Exception as e:
                print(f"Error setting up boundary layers: {e}")
                print("Continuing without boundary layers.")
        
        # Set minimum mesh size field
        min_field = gmsh.model.mesh.field.add("Min")
        gmsh.model.mesh.field.setNumbers(min_field, "FieldsList", [threshold_field] if boundary_layers else [])
        gmsh.model.mesh.field.setAsBackgroundMesh(min_field)
        
        # --- Generate Mesh ---
        print("\n=== Starting mesh generation ===")
        print(f"Current memory usage: {psutil.Process().memory_info().rss / 1024**3:.2f} GB")
        
        # 1D mesh (edges)
        print("Generating 1D mesh...")
        gmsh.model.mesh.generate(1) 
        
        # 2D mesh (surfaces)
        print("Generating 2D mesh...")
        try:
            gmsh.model.mesh.generate(2)
        except Exception as e:
            print(f"Error with 2D mesh algorithm {mesh_algorithm_2d}: {e}")
            print("Trying with alternative algorithm (5=Delaunay)...")
            gmsh.option.setNumber("Mesh.Algorithm", 5) 
            
            # Try again with simplified algorithm
            try:
                # Clear mesh and regenerate
                gmsh.model.mesh.clear()
                gmsh.model.mesh.generate(1)
                gmsh.model.mesh.generate(2)
            except Exception as e:
                print(f"Second 2D meshing attempt failed: {e}")
                print("Final attempt with most reliable algorithm (1=MeshAdapt)...")
                gmsh.option.setNumber("Mesh.Algorithm", 1)
                
                # Last attempt
                gmsh.model.mesh.clear()
                gmsh.model.mesh.generate(1)
                gmsh.model.mesh.generate(2)
        
        # Memory usage checkpoint before 3D mesh
        print(f"After 2D meshing, memory usage: {psutil.Process().memory_info().rss / 1024**3:.2f} GB")
        
        # 3D mesh (volumes)
        print("Generating 3D mesh...")
        try:
            # Force garbage collection before heavy operation
            try:
                import gc
                gc.collect()
            except:
                pass
                
            gmsh.model.mesh.generate(3)
        except Exception as e:
            print(f"Error with 3D mesh algorithm {mesh_algorithm_3d}: {e}")
            print("Trying with most memory-efficient algorithm (1=Delaunay)...")
            
            gmsh.option.setNumber("Mesh.Algorithm3D", 1)
            gmsh.option.setNumber("Mesh.OptimizeNetgen", 0)  # Disable Netgen optimizer to save memory
            
            try:
                # Regenerate only 3D (keep 2D mesh)
                gmsh.model.mesh.generate(3)
            except Exception as e:
                print(f"Second 3D meshing attempt failed: {e}")
                print("Last attempt with simplified domain...")
                
                # Clear mesh
                gmsh.model.mesh.clear()
                
                # Coarsen mesh parameters for last resort attempt
                gmsh.option.setNumber("Mesh.CharacteristicLengthMin", mesh_size * 2)
                gmsh.option.setNumber("Mesh.CharacteristicLengthMax", mesh_size * 4)
                
                # Generate 3D mesh via 1,2,3
                gmsh.model.mesh.generate(1)
                gmsh.model.mesh.generate(2)
                gmsh.model.mesh.generate(3)
        
        # Check mesh statistics
        element_types, element_tags, node_tags = gmsh.model.mesh.getElements()
        num_elements = sum(len(tags) for tags in element_tags)
        print(f"Mesh generation completed with {num_elements} elements")
        
        # --- Export Mesh ---
        print(f"Writing output mesh to: {output_msh}")
        gmsh.write(output_msh)
        
        # Write SU2 format as well if requested
        if output_msh.endswith(".msh"):
            su2_file = output_msh.replace(".msh", ".su2")
            try:
                gmsh.write(su2_file)
                print(f"SU2 mesh also written to: {su2_file}")
            except Exception as e:
                print(f"Error writing SU2 format: {e}")
        
        # Print timing information
        end_time = time.time()
        elapsed = end_time - start_time
        print(f"Total execution time: {elapsed:.2f} seconds")
        
        # Return success
        return True
    
    except Exception as e:
        print(f"Error in mesh generation: {e}")
        traceback.print_exc()
        return False
    
    finally:
        # Check memory usage
        end_mem = get_available_memory_gb()
        print(f"Memory usage: {start_mem - end_mem:.2f} GB")
        
        if gmsh.isInitialized():
            # Finalize Gmsh
            gmsh.finalize()

def main():
    parser = argparse.ArgumentParser(description="Process STEP files to generate CFD meshes")
    parser.add_argument("--input", required=True, help="Input STEP file")
    parser.add_argument("--output", required=True, help="Output mesh file")
    parser.add_argument("--size", type=float, default=1.0, help="Base mesh size")
    parser.add_argument("--threads", type=int, default=4, help="Number of threads")
    parser.add_argument("--domain-scale", type=float, default=2.0, help="Domain size scale factor")
    parser.add_argument("--bl", action="store_true", help="Add boundary layers")
    parser.add_argument("--bl-thickness", type=float, default=0.01, help="Boundary layer thickness")
    parser.add_argument("--bl-layers", type=int, default=5, help="Number of boundary layers")
    parser.add_argument("--algo3d", type=int, default=1, help="3D meshing algorithm (1=Delaunay recommended)")
    parser.add_argument("--algo2d", type=int, default=6, help="2D meshing algorithm (6=Frontal-Delaunay recommended)")
    parser.add_argument("--optimize", action="store_true", help="Enable Netgen optimizer")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    parser.add_argument("--validate", action="store_true", help="Validate geometry")
    parser.add_argument("--memory-limit", type=float, help="Memory limit in GB")
    
    args = parser.parse_args()
    
    # Check if input file exists
    if not os.path.isfile(args.input):
        print(f"Error: Input file '{args.input}' does not exist")
        return 1
    
    # Process the file
    success = process_step_file(
        args.input, 
        args.output,
        mesh_size=args.size,
        boundary_layers=args.bl,
        bl_thickness=args.bl_thickness,
        bl_layers=args.bl_layers,
        domain_scale=args.domain_scale,
        num_threads=args.threads,
        mesh_algorithm_3d=args.algo3d,
        mesh_algorithm_2d=args.algo2d,
        optimize_netgen=args.optimize,
        debug=args.debug,
        validate_geometry=args.validate,
        memory_limit=args.memory_limit
    )
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())