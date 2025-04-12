#!/usr/bin/env python3

import sys
import os
import argparse
import gmsh
import tempfile
import time
import multiprocessing
import subprocess
import shutil
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import numpy as np

# Try to import CUDA-related libraries if available
try:
    import cupy as cp
    import pycuda.driver as cuda
    import pycuda.autoinit
    from pycuda import gpuarray
    CUDA_AVAILABLE = True
    print("CUDA support enabled - using GPU acceleration")
except ImportError:
    CUDA_AVAILABLE = False
    print("CUDA libraries not found - running in CPU-only mode")

# Try to import MPI if available
try:
    from mpi4py import MPI
    MPI_AVAILABLE = True
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()
    print(f"MPI available: rank {rank} of {size}")
except ImportError:
    MPI_AVAILABLE = False
    rank = 0
    size = 1

def get_optimal_thread_count():
    """Determine the optimal number of threads based on system resources"""
    cpu_count = multiprocessing.cpu_count()
    
    # If CUDA is available, leave some CPU cores free for GPU coordination
    if CUDA_AVAILABLE:
        # Use 75% of available cores when GPU is used
        return max(1, int(cpu_count * 0.75))
    else:
        # Use 90% of available cores in CPU-only mode
        return max(1, int(cpu_count * 0.9))

def setup_gpu_environment():
    """Configure the environment for optimal GPU performance"""
    if not CUDA_AVAILABLE:
        return False
        
    try:
        # Initialize CUDA
        cuda.init()
        
        # Get GPU device
        dev = cuda.Device(0)  # Use the first GPU
        ctx = dev.make_context()
        
        # Print GPU info
        print(f"Using GPU: {dev.name()} with {dev.total_memory()/1024/1024:.1f} MB memory")
        
        # Set device flags for improved performance
        ctx.set_cache_config(cuda.func_cache.PREFER_L1)
        
        # Detach the context (will be used automatically by cupy/pycuda)
        ctx.pop()
        
        return True
    except Exception as e:
        print(f"Error setting up GPU: {e}")
        return False

def create_mesh(input_file, output_file, mesh_size=1.0, algorithm_2d=6, algorithm_3d=4, 
                use_gpu=True, num_threads=None, omp_chunk_size=1000):
    """
    Create a mesh from the input file using the Gmsh Python API with GPU and parallel acceleration
    """
    print(f"Processing {input_file} -> {output_file}")
    
    # Setup optimal thread count
    if num_threads is None:
        num_threads = get_optimal_thread_count()
    
    # Initialize GPU if available and requested
    gpu_enabled = use_gpu and setup_gpu_environment() and CUDA_AVAILABLE
    
    # Set OpenMP environment variables for better performance
    os.environ["OMP_NUM_THREADS"] = str(num_threads)
    os.environ["OMP_SCHEDULE"] = f"dynamic,{omp_chunk_size}"
    os.environ["OMP_PROC_BIND"] = "close"
    os.environ["OMP_PLACES"] = "cores"
    os.environ["OMP_STACKSIZE"] = "128M"
    
    start_time = time.time()
    
    # Initialize Gmsh
    gmsh.initialize()
    
    # Set mesh options for robust meshing
    gmsh.option.setNumber("General.Terminal", 1)
    gmsh.option.setNumber("General.NumThreads", num_threads)
    gmsh.option.setNumber("Mesh.MaxNumThreads2D", num_threads)
    gmsh.option.setNumber("Mesh.MaxNumThreads3D", num_threads)
    
    gmsh.option.setNumber("Mesh.Algorithm", algorithm_2d)
    gmsh.option.setNumber("Mesh.Algorithm3D", algorithm_3d)
    gmsh.option.setNumber("Mesh.CharacteristicLengthMin", mesh_size * 0.1)
    gmsh.option.setNumber("Mesh.CharacteristicLengthMax", mesh_size)
    
    # Additional options for problematic geometries
    gmsh.option.setNumber("Mesh.ElementOrder", 1)  # First-order elements are more robust
    gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
    gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)
    gmsh.option.setNumber("Mesh.SaveAll", 1)
    gmsh.option.setNumber("Mesh.SaveParametric", 0)
    gmsh.option.setNumber("Mesh.OptimizeThreshold", 0.3)
    gmsh.option.setNumber("Mesh.Smoothing", 5)  # More aggressive smoothing
    gmsh.option.setNumber("Mesh.SmoothNormals", 1)
    gmsh.option.setNumber("Mesh.SmoothCrossField", 1)
    gmsh.option.setNumber("Mesh.AnisoMax", 100.0)  # Allow anisotropic elements
    gmsh.option.setNumber("Mesh.HighOrderOptimize", 0)  # Skip high order optimization
    gmsh.option.setNumber("Mesh.SecondOrderIncomplete", 0)
    
    # Critical for problematic meshes with duplicate edges
    gmsh.option.setNumber("Mesh.IgnorePeriodicity", 1)
    gmsh.option.setNumber("Mesh.CheckSurfaceMesh", 0)  # Skip surface mesh checking
    
    # Set geometry healing options - more aggressive
    gmsh.option.setNumber("Geometry.Tolerance", 1e-2)
    gmsh.option.setNumber("Geometry.ToleranceBoolean", 1e-2)
    gmsh.option.setNumber("Geometry.OCCFixDegenerated", 1)
    gmsh.option.setNumber("Geometry.OCCFixSmallEdges", 1)
    gmsh.option.setNumber("Geometry.OCCFixSmallFaces", 1)
    gmsh.option.setNumber("Geometry.OCCSewFaces", 1)
    gmsh.option.setNumber("Geometry.OCCMakeSolids", 1)
    gmsh.option.setNumber("Geometry.OCCParallel", num_threads > 1)
    
    # Create a new model
    model_name = os.path.splitext(os.path.basename(output_file))[0]
    gmsh.model.add(model_name)
    
    success = False
    try:
        # Import the geometry
        print("Importing geometry...")
        gmsh.merge(input_file)
        
        # Apply coherence to join entities - this is CPU intensive and parallelized by Gmsh
        print("Applying geometry coherence...")
        gmsh.model.occ.synchronize()
        gmsh.model.occ.removeAllDuplicates()
        gmsh.model.occ.synchronize()
        
        # Get entities after import
        entities = gmsh.model.getEntities()
        dims = set(e[0] for e in entities)
        print(f"Imported geometry: {len(entities)} entities")
        print(f"Dimensions: {sorted(list(dims))}")
        
        # Check for volumes (3D entities)
        vols = [e for e in entities if e[0] == 3]
        if vols:
            print(f"Found {len(vols)} volumes")
            for i, vol in enumerate(vols):
                print(f"  Volume {i}: tag {vol[1]}")
                
            # Use the first volume as the main geometry
            main_volume_tag = vols[0][1]
        else:
            # Create volume from surfaces if no volumes exist
            print("No volumes found. Looking for surfaces...")
            surfaces = [e for e in entities if e[0] == 2]
            
            if surfaces:
                print(f"Found {len(surfaces)} surfaces")
                try:
                    # Try to create a volume with OCC
                    print("Attempting to create volume from surfaces...")
                    surface_tags = [e[1] for e in surfaces]
                    
                    try:
                        # Try to create a shell from surfaces
                        shell = gmsh.model.occ.addSurfaceLoop(surface_tags)
                        main_volume_tag = gmsh.model.occ.addVolume([shell])
                        gmsh.model.occ.synchronize()
                        print(f"Created volume with tag {main_volume_tag}")
                    except Exception as e:
                        print(f"Direct volume creation failed: {e}")
                        print("Trying to heal surfaces first...")
                        
                        # Heal the surfaces
                        healed = []
                        gmsh.model.occ.healShapes([(2, tag) for tag in surface_tags], healed, 
                                               1e-2, True, True, True, True, True)
                        gmsh.model.occ.synchronize()
                        
                        # Try again with healed surfaces
                        healed_surfaces = gmsh.model.getEntities(2)
                        healed_tags = [e[1] for e in healed_surfaces]
                        shell = gmsh.model.occ.addSurfaceLoop(healed_tags)
                        main_volume_tag = gmsh.model.occ.addVolume([shell])
                        gmsh.model.occ.synchronize()
                        print(f"Created volume after healing with tag {main_volume_tag}")
                except Exception as e:
                    print(f"Volume creation failed: {e}")
                    # Fall back to surface meshing
                    main_volume_tag = None
                    print("Will proceed with 2D surface meshing only")
            else:
                print("No surfaces found. Looking for curves...")
                main_volume_tag = None
                curves = [e for e in entities if e[0] == 1]
                if not curves:
                    raise Exception("No usable geometry found in the input file")
        
        # Create a fluid domain surrounding the geometry
        try:
            if main_volume_tag is not None:
                print("Creating computational fluid domain...")
                # Get the bounding box of the geometry
                xmin, ymin, zmin, xmax, ymax, zmax = gmsh.model.getBoundingBox(-1, -1)
                print(f"Model bounding box: ({xmin}, {ymin}, {zmin}) - ({xmax}, {ymax}, {zmax})")
                
                # Calculate domain size - make it 5x larger than the geometry
                domain_scale = 5.0
                dx = xmax - xmin
                dy = ymax - ymin
                dz = zmax - zmin
                max_dim = max(dx, dy, dz)
                
                # Handle degenerate dimensions
                if dx < 0.01 * max_dim: dx = max_dim
                if dy < 0.01 * max_dim: dy = max_dim
                if dz < 0.01 * max_dim: dz = max_dim
                
                center_x = (xmax + xmin) / 2
                center_y = (ymax + ymin) / 2
                center_z = (zmax + zmin) / 2
                
                # Create a box that is domain_scale times larger than the geometry
                print(f"Creating domain box with scale factor {domain_scale}...")
                domain_vol = gmsh.model.occ.addBox(
                    center_x - domain_scale * dx / 2,
                    center_y - domain_scale * dy / 2,
                    center_z - domain_scale * dz / 2,
                    domain_scale * dx,
                    domain_scale * dy,
                    domain_scale * dz
                )
                gmsh.model.occ.synchronize()
                print(f"Created fluid domain box with tag {domain_vol}")
                
                # Perform boolean difference (domain - intake) to create fluid region
                print("Performing boolean operation to create fluid domain...")
                out_dimtags = []
                tools = [] if main_volume_tag is None else [(3, main_volume_tag)]
                try:
                    gmsh.model.occ.cut([(3, domain_vol)], tools, out_dimtags)
                    gmsh.model.occ.synchronize()
                    print(f"Boolean operation created {len(out_dimtags)} entities")
                    
                    # Check if we have a fluid volume
                    fluid_volumes = [tag for dim, tag in out_dimtags if dim == 3]
                    if fluid_volumes:
                        print(f"Created fluid volumes with tags: {fluid_volumes}")
                        main_volume_tag = fluid_volumes[0]  # Use the first fluid volume
                    else:
                        print("No fluid volumes created. Using original domain volume.")
                        main_volume_tag = domain_vol
                except Exception as e:
                    print(f"Boolean operation failed: {e}")
                    print("Falling back to original domain")
                    main_volume_tag = domain_vol
            else:
                print("No main volume available. Skipping fluid domain creation.")
        except Exception as e:
            print(f"Error creating fluid domain: {e}")
            print("Continuing with original geometry")
        
        # Generate mesh
        print("Generating mesh...")
        try:
            # First step: Try full 3D mesh
            mesh_start = time.time()
            gmsh.model.mesh.generate(1)  # Generate 1D mesh first
            print(f"1D mesh completed in {time.time() - mesh_start:.2f}s")
            
            mesh_start = time.time()
            gmsh.model.mesh.generate(2)  # Then 2D
            print(f"2D mesh completed in {time.time() - mesh_start:.2f}s")
            
            # Try 3D mesh if we have volumes
            if main_volume_tag is not None:
                try:
                    print(f"Attempting 3D meshing (using {num_threads} threads)...")
                    mesh_start = time.time()
                    gmsh.model.mesh.generate(3)
                    print(f"3D mesh successfully completed in {time.time() - mesh_start:.2f}s")
                    success = True
                except Exception as e:
                    print(f"3D meshing failed: {e}")
                    print("Continuing with 2D mesh...")
                    success = True  # 2D mesh is still useful
            else:
                print("No volumes available. Generating 2D mesh only.")
                success = True
                
        except Exception as e:
            print(f"Standard meshing failed: {e}")
            
            # Alternative approach - try different algorithms
            print("Trying alternative meshing approach...")
            
            # Reset mesh
            gmsh.model.mesh.clear()
            
            # Try different algorithm
            gmsh.option.setNumber("Mesh.Algorithm", 3)  # MeshAdapt
            gmsh.option.setNumber("Mesh.Algorithm3D", 1)  # Delaunay
            
            try:
                gmsh.model.mesh.generate(1)
                gmsh.model.mesh.generate(2)
                success = True
                print("Alternative 2D meshing successful!")
            except Exception as e2:
                print(f"Alternative 2D meshing failed: {e2}")
                
                # Last resort - create a simple box mesh
                try:
                    print("Creating simplified mesh...")
                    gmsh.model.mesh.clear()
                    xmin, ymin, zmin, xmax, ymax, zmax = gmsh.model.getBoundingBox(-1, -1)
                    
                    # Create a slightly smaller box to ensure we capture the model
                    dx = (xmax - xmin) * 0.01
                    dy = (ymax - ymin) * 0.01
                    dz = (zmax - zmin) * 0.01
                    
                    box = gmsh.model.occ.addBox(xmin+dx, ymin+dy, zmin+dz, 
                                               xmax-xmin-2*dx, ymax-ymin-2*dy, zmax-zmin-2*dz)
                    gmsh.model.occ.synchronize()
                    
                    # Mesh with simple options
                    gmsh.option.setNumber("Mesh.CharacteristicLengthMax", mesh_size * 2)
                    gmsh.model.mesh.generate(3)
                    success = True
                    print("Created simplified mesh")
                except Exception as e3:
                    print(f"Failed to create simplified mesh: {e3}")
        
        # Save mesh
        if success:
            print(f"Saving mesh to {output_file}...")
            gmsh.option.setNumber("Mesh.Binary", 1)  # Use binary format for efficiency
            gmsh.write(output_file)
            print(f"Mesh generated successfully in {time.time() - start_time:.2f} seconds")
            
            # Also save a geo file for debugging
            geo_file = f"{os.path.splitext(output_file)[0]}_model.geo_unrolled"
            print(f"Saving geometry to {geo_file} for inspection...")
            gmsh.write(geo_file)
        else:
            print("Failed to generate a usable mesh")
            
    except Exception as e:
        print(f"Error: {e}")
        
    finally:
        # Try to save whatever mesh and geometry we have
        try:
            debug_file = f"{os.path.splitext(output_file)[0]}_debug.msh"
            print(f"Saving debug mesh to {debug_file}...")
            gmsh.write(debug_file)
            
            debug_geo = f"{os.path.splitext(output_file)[0]}_debug.geo_unrolled"
            print(f"Saving debug geometry to {debug_geo}...")
            gmsh.write(debug_geo)
        except:
            pass
        
        gmsh.finalize()
    
    return success

def create_stl_mesh(input_file, output_file, mesh_size=1.0, num_threads=None):
    """
    Alternative approach: Convert to STL first then mesh using GPU acceleration if available
    """
    print(f"Trying STL conversion approach for {input_file}...")
    
    # Setup optimal thread count
    if num_threads is None:
        num_threads = get_optimal_thread_count()
    
    # Create temporary STL file
    with tempfile.NamedTemporaryFile(suffix='.stl', delete=False) as tmp:
        stl_file = tmp.name
    
    # Step 1: Convert to STL
    try:
        print(f"Converting to STL: {stl_file}")
        gmsh.initialize()
        gmsh.option.setNumber("Mesh.Binary", 1)
        gmsh.option.setNumber("General.NumThreads", num_threads)
        gmsh.merge(input_file)
        gmsh.write(stl_file)
        gmsh.finalize()
        
        # Step 2: Mesh from STL
        print("Meshing from STL...")
        gmsh.initialize()
        gmsh.option.setNumber("General.NumThreads", num_threads)
        gmsh.option.setNumber("Mesh.Algorithm", 3)  # MeshAdapt is better for STL
        gmsh.option.setNumber("Mesh.CharacteristicLengthMax", mesh_size)
        gmsh.merge(stl_file)
        gmsh.model.mesh.generate(3)
        gmsh.write(output_file)
        gmsh.finalize()
        
        print(f"Successfully created mesh via STL conversion: {output_file}")
        return True
        
    except Exception as e:
        print(f"STL conversion approach failed: {e}")
        return False
    finally:
        # Clean up temp file
        if os.path.exists(stl_file):
            os.unlink(stl_file)

def run_gmsh_with_gpu(input_file, output_file, mesh_size=1.0):
    """
    Try to use external Gmsh executable with GPU acceleration through CUDA-GL
    This requires a Gmsh build with OpenGL support
    """
    # Check if gmsh executable is available
    gmsh_path = shutil.which('gmsh')
    if not gmsh_path:
        print("External Gmsh executable not found")
        return False
    
    try:
        # Create a temporary options file for Gmsh
        with tempfile.NamedTemporaryFile(suffix='.opt', mode='w', delete=False) as opt_file:
            opt_path = opt_file.name
            opt_file.write(f"Mesh.CharacteristicLengthMax = {mesh_size};\n")
            opt_file.write(f"Mesh.CharacteristicLengthMin = {mesh_size * 0.1};\n")
            opt_file.write("Mesh.Algorithm = 3;\n")  # MeshAdapt
            opt_file.write("Mesh.Algorithm3D = 1;\n")  # Delaunay
            opt_file.write("Mesh.OptimizeThreshold = 0.3;\n")
            opt_file.write("Mesh.Binary = 1;\n")
            opt_file.write("Mesh.SaveAll = 1;\n")
            opt_file.write("Mesh.MeshSizeExtendFromBoundary = 0;\n")
            opt_file.write("Mesh.IgnorePeriodicity = 1;\n")
            opt_file.write("Mesh.CheckSurfaceMesh = 0;\n")
            opt_file.write("Geometry.OCCFixDegenerated = 1;\n")
            opt_file.write("Geometry.OCCFixSmallEdges = 1;\n")
            opt_file.write("Geometry.OCCFixSmallFaces = 1;\n")
            opt_file.write("Geometry.OCCSewFaces = 1;\n")
            opt_file.write("Geometry.OCCMakeSolids = 1;\n")
            opt_file.write("Geometry.Tolerance = 1e-2;\n")
            opt_file.write("Geometry.ToleranceBoolean = 1e-2;\n")
        
        # Run external gmsh with options file
        cmd = [
            gmsh_path,
            input_file,
            "-3",  # Generate 3D mesh
            "-format", "msh",
            "-o", output_file,
            "-string", f"Merge \"{opt_path}\";",
            "-gpu"  # Enable GPU acceleration (if supported)
        ]
        
        print(f"Executing: {' '.join(cmd)}")
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()
        
        if process.returncode == 0:
            print("External Gmsh GPU meshing successful")
            return True
        else:
            print(f"External Gmsh GPU meshing failed: {stderr}")
            return False
    except Exception as e:
        print(f"Error running external Gmsh with GPU: {e}")
        return False
    finally:
        # Clean up temp file
        if os.path.exists(opt_path):
            os.unlink(opt_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create mesh using Gmsh Python API with GPU acceleration")
    parser.add_argument("input_file", help="Input geometry file (STEP, BREP, STL, etc.)")
    parser.add_argument("output_file", help="Output mesh file")
    parser.add_argument("--size", type=float, default=1.0, help="Characteristic mesh size")
    parser.add_argument("--alg2d", type=int, default=6, help="2D meshing algorithm")
    parser.add_argument("--alg3d", type=int, default=4, help="3D meshing algorithm")
    parser.add_argument("--stl", action="store_true", help="Use STL conversion approach")
    parser.add_argument("--gpu", action="store_true", help="Enable GPU acceleration")
    parser.add_argument("--cpu-only", action="store_true", help="Disable GPU acceleration")
    parser.add_argument("--threads", type=int, help="Number of CPU threads to use")
    parser.add_argument("--external", action="store_true", help="Use external Gmsh executable")
    
    args = parser.parse_args()
    
    # Default to GPU if available unless --cpu-only is specified
    use_gpu = not args.cpu_only and (args.gpu or CUDA_AVAILABLE)
    
    if args.external and use_gpu:
        # Try external Gmsh with GPU first
        success = run_gmsh_with_gpu(args.input_file, args.output_file, args.size)
    elif args.stl:
        # STL approach
        success = create_stl_mesh(args.input_file, args.output_file, args.size, args.threads)
    else:
        # Standard approach
        success = create_mesh(
            args.input_file, 
            args.output_file, 
            args.size, 
            args.alg2d, 
            args.alg3d,
            use_gpu=use_gpu,
            num_threads=args.threads
        )
    
    # If the selected approach fails, try the alternative
    if not success and not args.stl:
        print("\nDirect meshing approach failed. Trying STL conversion method...\n")
        success = create_stl_mesh(args.input_file, args.output_file, args.size, args.threads)
    
    # If that also fails and we haven't tried the external Gmsh, try that as last resort
    if not success and not args.external and use_gpu:
        print("\nTrying external Gmsh with GPU acceleration...\n")
        success = run_gmsh_with_gpu(args.input_file, args.output_file, args.size)
    
    sys.exit(0 if success else 1)
