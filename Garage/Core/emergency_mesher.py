#!/usr/bin/env python3
"""
Emergency meshing script for problematic STEP files like INTAKE3D.stp.
Uses direct box meshing and minimal memory settings.
"""

import sys
import os
import argparse
import traceback
import psutil
import gmsh
import time

def get_available_memory_gb():
    """Get available system memory in GB"""
    try:
        mem = psutil.virtual_memory()
        return mem.available / 1024 / 1024 / 1024
    except:
        # Return a safe default if we can't determine memory
        return 4.0

def emergency_mesh(input_file, output_file, mesh_size=20.0, use_input_geometry=True):
    """
    Create a mesh with minimal memory requirements.
    
    Args:
        input_file: Path to input geometry file
        output_file: Path to output mesh file
        mesh_size: Base mesh size
        use_input_geometry: Whether to try loading the input geometry
    """
    print(f"Starting emergency meshing for {input_file}")
    print(f"Output will be saved to {output_file}")
    
    # Use available memory to determine thread count and mesh parameters
    avail_mem = get_available_memory_gb()
    print(f"Available system memory: {avail_mem:.2f} GB")
    
    # Scale back threads and increase mesh size for low memory systems
    if avail_mem < 4.0:
        threads = 2
        mesh_size = mesh_size * 1.5
        print("Low memory mode: Using 2 threads and increased mesh size")
    elif avail_mem < 8.0:
        threads = 4
        print("Medium memory mode: Using 4 threads")
    else:
        import multiprocessing
        threads = max(4, multiprocessing.cpu_count() - 2)
        print(f"High memory mode: Using {threads} threads")
    
    start_time = time.time()
    
    # Initialize Gmsh
    gmsh.initialize()
    
    try:
        # General options for robustness
        gmsh.option.setNumber("General.Terminal", 1)
        gmsh.option.setNumber("General.NumThreads", threads)
        gmsh.option.setNumber("General.ExpertMode", 1)
        
        # Create a new model
        model_name = os.path.splitext(os.path.basename(output_file))[0]
        gmsh.model.add(model_name)
        
        # Memory-friendly mesh options
        gmsh.option.setNumber("Mesh.Algorithm", 3)  # MeshAdapt is more memory efficient
        gmsh.option.setNumber("Mesh.Algorithm3D", 1)  # Delaunay is most memory efficient
        gmsh.option.setNumber("Mesh.CharacteristicLengthMax", mesh_size)
        gmsh.option.setNumber("Mesh.CharacteristicLengthMin", mesh_size / 10)
        gmsh.option.setNumber("Mesh.ElementOrder", 1)  # Linear elements use less memory
        gmsh.option.setNumber("Mesh.OptimizeNetgen", 0)  # Disable Netgen optimizer (memory intensive)
        gmsh.option.setNumber("Mesh.Optimize", 1)  # Basic optimization only
        gmsh.option.setNumber("Mesh.OptimizeThreshold", 0.3)  # Less aggressive optimization
        gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
        gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)
        gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)
        gmsh.option.setNumber("Mesh.SaveAll", 1)
        
        # Geometry healing options
        gmsh.option.setNumber("Geometry.OCCFixDegenerated", 1)
        gmsh.option.setNumber("Geometry.OCCFixSmallEdges", 1)
        gmsh.option.setNumber("Geometry.OCCFixSmallFaces", 1)
        gmsh.option.setNumber("Geometry.OCCSewFaces", 1)
        gmsh.option.setNumber("Geometry.OCCMakeSolids", 1)
        gmsh.option.setNumber("Geometry.Tolerance", 1e-2)
        gmsh.option.setNumber("Geometry.ToleranceBoolean", 1e-2)
        
        # Try to import the geometry if requested
        imported = False
        box_only = False
        
        if use_input_geometry:
            try:
                print("Attempting to import geometry...")
                try:
                    # Try OCC first
                    gmsh.model.occ.importShapes(input_file)
                    gmsh.model.occ.synchronize()
                    imported = True
                    print("Successfully imported with OCC")
                except Exception as e:
                    print(f"OCC import failed: {e}")
                    # Fall back to direct merge
                    gmsh.merge(input_file)
                    imported = True
                    print("Successfully imported with direct merge")
            except Exception as e:
                print(f"Import failed: {e}")
                print("Proceeding with box-only domain")
                box_only = True
        else:
            print("Skipping geometry import (box-only mode)")
            box_only = True
        
        # Calculate domain size
        if imported:
            # Get the bounding box of the imported geometry
            try:
                xmin, ymin, zmin, xmax, ymax, zmax = gmsh.model.getBoundingBox(-1, -1)
                print(f"Model bounding box: ({xmin:.2f}, {ymin:.2f}, {zmin:.2f}) - ({xmax:.2f}, {ymax:.2f}, {zmax:.2f})")
                
                # Calculate center and dimensions
                cx = (xmax + xmin) / 2
                cy = (ymax + ymin) / 2
                cz = (zmax + zmin) / 2
                dx = xmax - xmin
                dy = ymax - ymin
                dz = zmax - zmin
                
                # Ensure non-zero dimensions
                max_dim = max(dx, dy, dz)
                if dx < 0.01 * max_dim or dx <= 0:
                    dx = max_dim
                if dy < 0.01 * max_dim or dy <= 0:
                    dy = max_dim
                if dz < 0.01 * max_dim or dz <= 0:
                    dz = max_dim
                
                # Create domain as 5x larger than the geometry
                domain_scale = 5.0
                box = gmsh.model.occ.addBox(
                    cx - domain_scale * dx / 2,
                    cy - domain_scale * dy / 2,
                    cz - domain_scale * dz / 2,
                    domain_scale * dx,
                    domain_scale * dy,
                    domain_scale * dz
                )
                gmsh.model.occ.synchronize()
                print("Created domain box based on geometry bounding box")
            except Exception as e:
                print(f"Error calculating bounding box: {e}")
                box_only = True
        
        # Create a default box if needed
        if box_only:
            print("Creating default box domain")
            box = gmsh.model.occ.addBox(-900, -500, -200, 1800, 1000, 400)
            gmsh.model.occ.synchronize()
            print("Created default box domain")
            
        # Generate mesh
        print("Generating mesh - this may take a while...")
        
        # First generate 1D and 2D mesh
        print("Generating 1D mesh...")
        gmsh.model.mesh.generate(1)
        
        print("Generating 2D mesh...")
        try:
            gmsh.model.mesh.generate(2)
        except Exception as e:
            print(f"2D meshing failed with Algorithm 3: {e}")
            print("Trying with Algorithm 6 (Frontal-Delaunay)...")
            
            # Clear existing mesh
            gmsh.model.mesh.clear()
            
            # Try a different algorithm
            gmsh.option.setNumber("Mesh.Algorithm", 6)  # Frontal-Delaunay
            gmsh.model.mesh.generate(1)
            gmsh.model.mesh.generate(2)
        
        # Force garbage collection before 3D mesh
        try:
            import gc
            gc.collect()
            print("Memory cleaned up before 3D meshing")
        except:
            pass
        
        print("Generating 3D mesh...")
        try:
            gmsh.model.mesh.generate(3)
        except Exception as e:
            print(f"3D meshing failed with Delaunay: {e}")
            print("Trying with Algorithm 4 (Frontal)...")
            
            # Try a different algorithm
            gmsh.option.setNumber("Mesh.Algorithm3D", 4)  # Frontal
            
            # Increase mesh size if meshing failed
            gmsh.option.setNumber("Mesh.CharacteristicLengthMax", mesh_size * 2)
            gmsh.option.setNumber("Mesh.CharacteristicLengthMin", mesh_size / 5)
            
            try:
                gmsh.model.mesh.generate(3)
            except Exception as e2:
                print(f"Second 3D meshing attempt failed: {e2}")
                print("Trying with minimal options and larger mesh size...")
                
                # Last attempt with much larger mesh size
                gmsh.option.setNumber("Mesh.CharacteristicLengthMax", mesh_size * 5)
                gmsh.option.setNumber("Mesh.CharacteristicLengthMin", mesh_size)
                gmsh.option.setNumber("Mesh.Algorithm3D", 1)  # Back to Delaunay
                
                try:
                    gmsh.model.mesh.generate(3)
                except Exception as e3:
                    print(f"Final 3D meshing attempt failed: {e3}")
                    print("Saving 2D mesh only")
        
        # Save the mesh
        print("Saving mesh...")
        gmsh.option.setNumber("Mesh.Binary", 1)  # Binary format is more efficient
        gmsh.write(output_file)
        print(f"Mesh saved to {output_file}")
        print(f"Process completed in {time.time() - start_time:.2f} seconds")
        return True
        
    except Exception as e:
        print(f"Error during emergency meshing: {e}")
        traceback.print_exc()
        return False
        
    finally:
        if gmsh.isInitialized():
            gmsh.finalize()
            print("Gmsh finalized")

def main():
    parser = argparse.ArgumentParser(description="Emergency meshing for problematic STEP files")
    parser.add_argument("input_file", help="Input geometry file")
    parser.add_argument("output_file", nargs="?", help="Output mesh file")
    parser.add_argument("--size", type=float, default=20.0, help="Base mesh size")
    parser.add_argument("--box-only", action="store_true", help="Skip geometry import, create only a box domain")
    
    args = parser.parse_args()
    
    # Set default output file name if not specified
    if not args.output_file:
        input_base = os.path.splitext(args.input_file)[0]
        args.output_file = f"{input_base}_emergency.msh"
    
    result = emergency_mesh(
        args.input_file,
        args.output_file,
        mesh_size=args.size,
        use_input_geometry=not args.box_only
    )
    
    if result:
        print("Emergency meshing completed successfully!")
    else:
        print("Emergency meshing failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
