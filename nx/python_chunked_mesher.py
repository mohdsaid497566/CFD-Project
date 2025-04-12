#!/usr/bin/env python3
"""
A specialized mesher for extremely large models that uses a chunked approach
to minimize memory usage. Splits the domain into subdomains and meshes each separately.
"""

import sys
import os
import argparse
import gmsh
import numpy as np
import time
import psutil
import multiprocessing
import tempfile
from pathlib import Path

def get_memory_status():
    """Get current memory usage and availability"""
    mem = psutil.virtual_memory()
    return {
        'total_gb': mem.total / 1024**3,
        'available_gb': mem.available / 1024**3,
        'used_percent': mem.percent
    }

def print_memory_status(prefix="Memory Status"):
    """Print current memory status"""
    mem = get_memory_status()
    print(f"{prefix}: {mem['available_gb']:.2f} GB available, {mem['used_percent']}% used")

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Mesh large models with chunked approach")
    parser.add_argument("input_file", help="Input geometry file (STEP, BREP, etc.)")
    parser.add_argument("output_file", nargs="?", help="Output mesh file")
    parser.add_argument("--mesh-size", type=float, default=10.0, help="Base mesh size")
    parser.add_argument("--chunks", type=int, default=4, help="Number of chunks to divide domain into")
    parser.add_argument("--threads", type=int, default=0, help="Number of threads to use (0=auto)")
    parser.add_argument("--2d-algorithm", type=int, default=3, help="2D meshing algorithm")
    parser.add_argument("--3d-algorithm", type=int, default=1, help="3D meshing algorithm")
    args = parser.parse_args()
    
    # Set output file if not provided
    if not args.output_file:
        input_path = Path(args.input_file)
        args.output_file = f"{input_path.stem}_chunked.msh"
    
    # Set threads if auto
    if args.threads <= 0:
        args.threads = max(1, multiprocessing.cpu_count() // 2)
    
    print(f"Using {args.threads} threads")
    print_memory_status("Initial memory")
    
    # Initialize Gmsh
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 1)
    gmsh.option.setNumber("General.Verbosity", 3)
    gmsh.option.setNumber("General.NumThreads", args.threads)
    
    start_time = time.time()
    
    # Add a model
    gmsh.model.add("chunked_model")
    
    try:
        # Step 1: Import the geometry and get bounding box
        print(f"Importing geometry from {args.input_file}...")
        try:
            gmsh.model.occ.importShapes(args.input_file)
            gmsh.model.occ.synchronize()
            print("Successfully imported using OCC")
        except Exception as e:
            print(f"OCC import failed: {e}")
            print("Trying direct merge...")
            gmsh.merge(args.input_file)
            print("Direct merge successful")
        
        # Get the bounding box
        xmin, ymin, zmin, xmax, ymax, zmax = gmsh.model.getBoundingBox(-1, -1)
        print(f"Model bounding box: ({xmin:.2f}, {ymin:.2f}, {zmin:.2f}) - ({xmax:.2f}, {ymax:.2f}, {zmax:.2f})")
        
        # Create a slightly larger domain box
        margin = 0.01 * max(xmax - xmin, ymax - ymin, zmax - zmin)
        
        # Step 2: Create subdomain chunks
        chunks = args.chunks
        chunk_tags = []
        
        # Decide which dimension to split based on the largest extent
        dims = [xmax - xmin, ymax - ymin, zmax - zmin]
        split_dim = dims.index(max(dims))
        
        if split_dim == 0:  # Split along X
            dx = (xmax - xmin) / chunks
            for i in range(chunks):
                x_start = xmin - margin + i * dx
                x_end = xmin - margin + (i + 1) * dx
                if i == chunks - 1:
                    x_end = xmax + margin  # Ensure we cover the entire domain
                
                box = gmsh.model.occ.addBox(
                    x_start, ymin - margin, zmin - margin,
                    x_end - x_start, ymax - ymin + 2*margin, zmax - zmin + 2*margin
                )
                chunk_tags.append(box)
                print(f"Created X-chunk {i+1}/{chunks}: ({x_start:.2f}, {ymin-margin:.2f}, {zmin-margin:.2f}) - "
                      f"({x_end:.2f}, {ymax+margin:.2f}, {zmax+margin:.2f})")
        
        elif split_dim == 1:  # Split along Y
            dy = (ymax - ymin) / chunks
            for i in range(chunks):
                y_start = ymin - margin + i * dy
                y_end = ymin - margin + (i + 1) * dy
                if i == chunks - 1:
                    y_end = ymax + margin  # Ensure we cover the entire domain
                
                box = gmsh.model.occ.addBox(
                    xmin - margin, y_start, zmin - margin,
                    xmax - xmin + 2*margin, y_end - y_start, zmax - zmin + 2*margin
                )
                chunk_tags.append(box)
                print(f"Created Y-chunk {i+1}/{chunks}: ({xmin-margin:.2f}, {y_start:.2f}, {zmin-margin:.2f}) - "
                      f"({xmax+margin:.2f}, {y_end:.2f}, {zmax+margin:.2f})")
        
        else:  # Split along Z
            dz = (zmax - zmin) / chunks
            for i in range(chunks):
                z_start = zmin - margin + i * dz
                z_end = zmin - margin + (i + 1) * dz
                if i == chunks - 1:
                    z_end = zmax + margin  # Ensure we cover the entire domain
                
                box = gmsh.model.occ.addBox(
                    xmin - margin, ymin - margin, z_start,
                    xmax - xmin + 2*margin, ymax - ymin + 2*margin, z_end - z_start
                )
                chunk_tags.append(box)
                print(f"Created Z-chunk {i+1}/{chunks}: ({xmin-margin:.2f}, {ymin-margin:.2f}, {z_start:.2f}) - "
                      f"({xmax+margin:.2f}, {ymax+margin:.2f}, {z_end:.2f})")
        
        gmsh.model.occ.synchronize()
        
        # Step 3: Process each chunk separately to create fragment
        chunk_meshes = []
        
        for i, chunk_tag in enumerate(chunk_tags):
            # Save current model state
            temp_model_file = tempfile.mktemp(suffix='.brep')
            gmsh.write(temp_model_file)
            
            # Create a new model for the chunk
            gmsh.model.add(f"chunk_{i}")
            
            # Load the saved model state
            gmsh.merge(temp_model_file)
            
            # Get the chunk volume
            chunk_vol_dimtag = (3, chunk_tag)
            
            print(f"\nProcessing chunk {i+1}/{chunks}...")
            print_memory_status(f"Before meshing chunk {i+1}")
            
            # Set meshing parameters for this chunk - fix the attribute access
            gmsh.option.setNumber("Mesh.Algorithm", getattr(args, '2d_algorithm'))
            gmsh.option.setNumber("Mesh.Algorithm3D", getattr(args, '3d_algorithm'))
            gmsh.option.setNumber("Mesh.CharacteristicLengthMax", args.mesh_size)
            gmsh.option.setNumber("Mesh.CharacteristicLengthMin", args.mesh_size * 0.1)
            gmsh.option.setNumber("Mesh.ElementOrder", 1)
            gmsh.option.setNumber("Mesh.OptimizeNetgen", 0)
            
            # Try boolean intersection to get just the geometry inside the chunk
            try:
                # Get all entities in the model
                all_entities = gmsh.model.getEntities(3)  # Get all volumes
                
                # If no volumes, get surfaces
                if not all_entities:
                    all_entities = gmsh.model.getEntities(2)  # Get all surfaces
                
                # Exclude the chunk itself from boolean operation targets
                target_entities = [e for e in all_entities if e[1] != chunk_tag]
                
                if target_entities:
                    # Perform boolean intersection
                    out_dimtags = []
                    gmsh.model.occ.intersect([chunk_vol_dimtag], target_entities, out_dimtags)
                    gmsh.model.occ.synchronize()
                    print(f"Created intersection with {len(out_dimtags)} entities")
                else:
                    # If no target entities, just use the chunk
                    out_dimtags = [chunk_vol_dimtag]
                    print("No entities found for intersection, using chunk as is")
            except Exception as e:
                print(f"Boolean operation failed: {e}")
                out_dimtags = [chunk_vol_dimtag]  # Use chunk as is
            
            # Generate mesh for the chunk
            try:
                print(f"Generating mesh for chunk {i+1}...")
                chunk_start_time = time.time()
                
                # Use progressive approach to minimize memory usage
                gmsh.model.mesh.generate(1)
                print(f"1D mesh for chunk {i+1} completed")
                
                gmsh.model.mesh.generate(2)
                print(f"2D mesh for chunk {i+1} completed")
                
                gmsh.model.mesh.generate(3)
                print(f"3D mesh for chunk {i+1} completed")
                
                # Save the chunk mesh to a temporary file
                chunk_mesh_file = f"chunk_{i+1}_mesh.msh"
                gmsh.write(chunk_mesh_file)
                chunk_meshes.append(chunk_mesh_file)
                
                print(f"Chunk {i+1} mesh saved to {chunk_mesh_file}")
                print(f"Chunk {i+1} meshed in {time.time() - chunk_start_time:.2f} seconds")
                
                # Clean up to free memory
                gmsh.model.mesh.clear()
                print_memory_status(f"After meshing chunk {i+1}")
                
                # Clean up temporary model file
                os.remove(temp_model_file)
                
            except Exception as e:
                print(f"Failed to mesh chunk {i+1}: {e}")
                # Continue with next chunk
                
            # Reset for next chunk
            gmsh.model.remove()
            
            # Force garbage collection
            import gc
            gc.collect()
        
        print("\nAll chunks processed")
        
        # Step 4: Merge chunk meshes into final mesh
        if chunk_meshes:
            print(f"Merging {len(chunk_meshes)} chunk meshes...")
            
            # Initialize a new model for the merged mesh
            gmsh.model.add("merged_model")
            
            # Merge all chunk meshes
            for i, chunk_file in enumerate(chunk_meshes):
                print(f"Merging chunk {i+1}...")
                gmsh.merge(chunk_file)
            
            # Save the final mesh
            gmsh.write(args.output_file)
            print(f"Final mesh saved to {args.output_file}")
            
            # Clean up temporary chunk files
            for chunk_file in chunk_meshes:
                try:
                    os.remove(chunk_file)
                except:
                    pass
        else:
            print("No chunk meshes were created successfully")
            return False
        
        print(f"\nTotal processing time: {time.time() - start_time:.2f} seconds")
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        gmsh.finalize()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
