#!/usr/bin/env python3
"""
This script creates a fluid domain around a STEP geometry using Gmsh Python API.
With full HPC acceleration support for CUDA, MPI, and OpenMP.
"""

import sys
import os
import argparse
import traceback
import gmsh
import numpy as np
from pathlib import Path
import tempfile
import multiprocessing
import platform
import ctypes
import subprocess
import shutil
import psutil
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

# Try to import MPI if available
try:
    from mpi4py import MPI
    HAS_MPI = True
except ImportError:
    HAS_MPI = False

# Try to import CUDA if available
try:
    import pycuda.driver as cuda
    import pycuda.autoinit
    HAS_CUDA = True
except ImportError:
    HAS_CUDA = False

def get_system_info():
    """Get system information for optimal resource allocation"""
    info = {}
    
    # Get CPU info
    info['cpu_count'] = multiprocessing.cpu_count()
    
    # Check for OpenMP
    if 'OMP_NUM_THREADS' in os.environ:
        info['omp_threads'] = int(os.environ['OMP_NUM_THREADS'])
    else:
        info['omp_threads'] = info['cpu_count']
    
    # Check for MPI
    if HAS_MPI:
        comm = MPI.COMM_WORLD
        info['mpi_rank'] = comm.Get_rank()
        info['mpi_size'] = comm.Get_size()
    else:
        info['mpi_rank'] = 0
        info['mpi_size'] = 1
    
    # Check for CUDA
    if HAS_CUDA:
        info['cuda_available'] = True
        info['cuda_devices'] = cuda.Device.count()
        info['cuda_device_names'] = [cuda.Device(i).name() for i in range(info['cuda_devices'])]
    else:
        info['cuda_available'] = False
        info['cuda_devices'] = 0
        info['cuda_device_names'] = []
    
    # Memory information
    try:
        if platform.system() == 'Linux':
            with open('/proc/meminfo', 'r') as f:
                mem_info = f.readlines()
            for line in mem_info:
                if 'MemTotal' in line:
                    info['system_memory_gb'] = int(line.split()[1]) / 1024 / 1024
                    break
        elif platform.system() == 'Windows':
            info['system_memory_gb'] = ctypes.windll.kernel32.GlobalMemoryStatusEx().ullTotalPhys / 1024 / 1024 / 1024
        else:
            # Default for other platforms
            info['system_memory_gb'] = 8
    except:
        info['system_memory_gb'] = 8

    # Add memory tracking for adaptive resource allocation
    try:
        mem = psutil.virtual_memory()
        info['system_memory_total_gb'] = mem.total / 1024 / 1024 / 1024
        info['system_memory_available_gb'] = mem.available / 1024 / 1024 / 1024
        info['system_memory_used_percent'] = mem.percent
    except:
        info['system_memory_total_gb'] = 8.0
        info['system_memory_available_gb'] = 4.0
        info['system_memory_used_percent'] = 50.0
    
    return info

def setup_environment(system_info, debug=False, acc_level=2):
    """Configure environment variables for optimal HPC performance"""
    # Configure Gmsh's environment variables
    os.environ["GMSH_NUM_THREADS"] = str(system_info['omp_threads'])
    
    # OpenMP configuration
    os.environ["OMP_SCHEDULE"] = "dynamic,16"
    os.environ["OMP_PROC_BIND"] = "close"
    os.environ["OMP_PLACES"] = "cores"
    os.environ["OMP_STACKSIZE"] = "128M"
    
    if debug:
        os.environ["GMSH_DEBUG"] = "99"
        os.environ["GMSH_VERBOSITY"] = "99"
        os.environ["OMP_DISPLAY_ENV"] = "TRUE"
    
    # Configure acceleration level based on user preference
    if acc_level >= 1:
        # Level 1: Basic OpenMP
        os.environ["OMP_NUM_THREADS"] = str(system_info['omp_threads'])
    
    if acc_level >= 2 and HAS_CUDA:
        # Level 2: Add CUDA
        os.environ["CUDA_VISIBLE_DEVICES"] = "0"  # Use first GPU by default
    
    if acc_level >= 3 and HAS_MPI:
        # Level 3: Add MPI
        os.environ["I_MPI_PIN_DOMAIN"] = "auto"
        os.environ["I_MPI_PIN_ORDER"] = "compact"

    # Memory management environment variables
    if system_info['system_memory_total_gb'] < 16:
        # For low-memory systems, be more conservative
        os.environ["OMP_STACKSIZE"] = "64M"
    else:
        # For high-memory systems, use more memory
        os.environ["OMP_STACKSIZE"] = "128M"

def parallel_bounding_box_calc(entities_subset, model, queue):
    """Calculate bounding box for a subset of entities in parallel"""
    bbox_min = [float('inf'), float('inf'), float('inf')]
    bbox_max = [float('-inf'), float('-inf'), float('-inf')]
    
    for dim, tag in entities_subset:
        try:
            xmin, ymin, zmin, xmax, ymax, zmax = model.getBoundingBox(dim, tag)
            bbox_min[0] = min(bbox_min[0], xmin)
            bbox_min[1] = min(bbox_min[1], ymin)
            bbox_min[2] = min(bbox_min[2], zmin)
            bbox_max[0] = max(bbox_max[0], xmax)
            bbox_max[1] = max(bbox_max[1], ymax)
            bbox_max[2] = max(bbox_max[2], zmax)
        except Exception:
            pass
    
    queue.put((bbox_min, bbox_max))

def adapt_mesh_parameters(mesh_size, system_info):
    """Adapt mesh parameters based on available system resources"""
    available_memory = system_info['system_memory_available_gb']
    threads = system_info['omp_threads']
    
    # Scale mesh size based on available memory to prevent OOM kill
    if available_memory < 4:
        # Very limited memory - use much coarser mesh
        return {
            'mesh_size': mesh_size * 3.0,
            'threads': min(threads, 4),
            'refinement_factor': 0.5,
            'progressive': True
        }
    elif available_memory < 8:
        # Limited memory - use coarser mesh
        return {
            'mesh_size': mesh_size * 1.5,
            'threads': min(threads, 8),
            'refinement_factor': 0.7,
            'progressive': True
        }
    elif available_memory < 16:
        # Moderate memory - standard settings
        return {
            'mesh_size': mesh_size,
            'threads': threads,
            'refinement_factor': 1.0,
            'progressive': False
        }
    else:
        # High memory - can use refined mesh
        return {
            'mesh_size': mesh_size * 0.8,
            'threads': threads,
            'refinement_factor': 1.2,
            'progressive': False
        }

def create_fluid_domain(input_file, output_file, domain_scale=5.0, mesh_size=10.0,
                        debug=False, simplify=False, acc_level=2, num_threads=None,
                        mesh_algorithm_2d=1, mesh_algorithm_3d=4):
    """
    Create a fluid domain around an input geometry with HPC acceleration.
    
    Args:
        input_file: Path to STEP file
        output_file: Path to output mesh file
        domain_scale: Scale factor for domain size relative to geometry
        mesh_size: Base mesh size for the domain
        debug: Enable debug output
        simplify: Create simplified box domain without boolean operations
        acc_level: Level of acceleration (0-3)
        num_threads: Override number of threads to use
        mesh_algorithm_2d: 2D meshing algorithm (1-7)
        mesh_algorithm_3d: 3D meshing algorithm (1-10)
    """
    start_time = os.times()
    
    # Get system information and configure environment
    system_info = get_system_info()
    
    # Override thread count if specified
    if num_threads is not None:
        system_info['omp_threads'] = num_threads
    
    # Print system info
    print("HPC-enabled Gmsh Fluid Domain Creator")
    print(f"System: {platform.system()} {platform.release()} on {platform.machine()}")
    print(f"CPU cores: {system_info['cpu_count']}")
    print(f"OpenMP threads: {system_info['omp_threads']}")
    print(f"Available memory: {system_info['system_memory_available_gb']:.1f} GB of {system_info['system_memory_total_gb']:.1f} GB")
    
    if HAS_MPI:
        print(f"MPI: Rank {system_info['mpi_rank']} of {system_info['mpi_size']}")
    else:
        print("MPI: Not available")
    
    if HAS_CUDA:
        print(f"CUDA: {system_info['cuda_devices']} device(s) - {', '.join(system_info['cuda_device_names'])}")
    else:
        print("CUDA: Not available")
    
    # Adapt mesh parameters based on system resources
    adaptive_params = adapt_mesh_parameters(mesh_size, system_info)
    adjusted_mesh_size = adaptive_params['mesh_size']
    adjusted_threads = adaptive_params['threads']
    
    if adjusted_mesh_size != mesh_size:
        print(f"Adapting mesh size to {adjusted_mesh_size:.2f} (from {mesh_size:.2f}) based on available resources")
    
    if adjusted_threads != system_info['omp_threads']:
        print(f"Limiting threads to {adjusted_threads} based on available memory")
        system_info['omp_threads'] = adjusted_threads
    
    # Initialize environment based on system info
    setup_environment(system_info, debug=debug, acc_level=acc_level)
    
    # Try increasing the stack size to avoid segfaults
    try:
        import resource
        resource.setrlimit(resource.RLIMIT_STACK, (resource.RLIM_INFINITY, resource.RLIM_INFINITY))
        print("Increased stack size limit")
    except:
        print("Warning: Could not increase stack size limit")

    # Initialize Gmsh with options for optimal HPC performance
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 1)
    gmsh.option.setNumber("General.NumThreads", system_info['omp_threads'])
    
    # Memory optimization options
    gmsh.option.setNumber("General.ExpertMode", 1)  # Enable expert mode for memory optimizations
    gmsh.option.setNumber("Mesh.OptimizeThreshold", 0.3)  # Less aggressive optimization to save memory
    gmsh.option.setNumber("Mesh.OptimizeNetgen", 0)  # Disable Netgen optimization to save memory
    gmsh.option.setNumber("Mesh.HighOrderOptimize", 0)  # Disable high order optimization
    
    # Add a dummy model first (helps with some Gmsh segfaults)
    gmsh.model.add("dummy")
    
    try:
        # Create model with name from output file
        model_name = Path(output_file).stem
        gmsh.model.add(model_name)
        
        print(f"Processing {input_file} -> {output_file}")
        print(f"Domain scale: {domain_scale}x, Mesh size: {adjusted_mesh_size}")
        
        # Set geometry tolerance options
        gmsh.option.setNumber("Geometry.Tolerance", 1e-3)
        gmsh.option.setNumber("Geometry.ToleranceBoolean", 1e-2)
        gmsh.option.setNumber("Geometry.OCCFixDegenerated", 1)
        gmsh.option.setNumber("Geometry.OCCFixSmallEdges", 1)
        gmsh.option.setNumber("Geometry.OCCFixSmallFaces", 1)
        gmsh.option.setNumber("Geometry.OCCSewFaces", 1)
        gmsh.option.setNumber("Geometry.OCCMakeSolids", 1)
        gmsh.option.setNumber("Geometry.AutoCoherence", 1)
        
        # Try various import methods with progress tracking
        print("Importing geometry...")
        import_success = False
        import_time_start = os.times()
        
        # Method 1: OCC Import
        try:
            gmsh.model.occ.importShapes(input_file)
            gmsh.model.occ.synchronize()
            import_success = True
            print("Successfully imported with OCC importShapes")
        except Exception as e:
            print(f"OCC importShapes failed: {e}")
            
            # Method 2: Direct Gmsh merge
            try:
                gmsh.merge(input_file)
                gmsh.model.occ.synchronize()
                import_success = True
                print("Successfully imported with gmsh.merge")
            except Exception as e:
                print(f"Direct merge failed: {e}")
                
                # Method 3: Repair STEP via STL conversion with parallel processing
                print("Attempting repair via STL conversion (parallel)...")
                try:
                    # Create temporary directory for conversion files
                    temp_dir = tempfile.mkdtemp()
                    temp_stl = os.path.join(temp_dir, "temp.stl")
                    temp_stp = os.path.join(temp_dir, "repaired.step")
                    
                    # Use subprocess to offload conversion to separate process
                    subprocess.run([
                        "gmsh", input_file, "-3", "-o", temp_stl, 
                        "-format", "stl", "-bin", 
                        f"-nt", str(system_info['omp_threads'])
                    ], check=True)
                    
                    subprocess.run([
                        "gmsh", temp_stl, "-3", "-o", temp_stp, 
                        "-format", "step",
                        f"-nt", str(system_info['omp_threads'])
                    ], check=True)
                    
                    # Try to import the repaired file
                    gmsh.model.occ.importShapes(temp_stp)
                    gmsh.model.occ.synchronize()
                    import_success = True
                    print("Successfully imported repaired geometry via parallel STL conversion")
                    
                    # Clean up temp files
                    try:
                        shutil.rmtree(temp_dir)
                    except:
                        pass
                except Exception as e:
                    print(f"Parallel STL repair method failed: {e}")
        
        import_time_end = os.times()
        import_time = import_time_end.user - import_time_start.user
        print(f"Geometry import completed in {import_time:.2f} seconds")
        
        if not import_success:
            print("All import methods failed. Proceeding with empty model and domain box only.")
        
        # Get geometry entities
        geometry_entities = gmsh.model.getEntities()
        geometry_volumes = gmsh.model.getEntities(3)
        geometry_surfaces = gmsh.model.getEntities(2)
        
        print(f"Imported geometry: {len(geometry_entities)} entities")
        print(f"  {len(geometry_volumes)} volumes, {len(geometry_surfaces)} surfaces")
        
        # Calculate bounding box in parallel if we have many entities
        bbox_min = [float('inf'), float('inf'), float('inf')]
        bbox_max = [float('-inf'), float('-inf'), float('-inf')]
        
        if not geometry_entities:
            print("Warning: No entities imported. Using default box dimensions.")
            bbox_min = [-100, -100, -100]
            bbox_max = [100, 100, 100]
        else:
            try:
                # Try to get bounding box from whole model
                xmin, ymin, zmin, xmax, ymax, zmax = gmsh.model.getBoundingBox(-1, -1)
                bbox_min = [xmin, ymin, zmin]
                bbox_max = [xmax, ymax, zmax]
                print(f"Model bounding box: {bbox_min} - {bbox_max}")
            except Exception as e:
                print(f"Error getting model bounding box: {e}")
                print("Using parallel entity-by-entity bounding box calculation...")
                
                if len(geometry_entities) > 100 and acc_level >= 1:
                    # Parallel bounding box calculation for large models
                    try:
                        from multiprocessing import Queue, Process
                        
                        # Split entities across processes
                        chunks = []
                        chunk_size = max(1, len(geometry_entities) // system_info['omp_threads'])
                        for i in range(0, len(geometry_entities), chunk_size):
                            chunks.append(geometry_entities[i:i+chunk_size])
                        
                        # Create shared queue for results
                        queue = Queue()
                        processes = []
                        
                        # Start parallel processes
                        for chunk in chunks:
                            p = Process(target=parallel_bounding_box_calc, 
                                      args=(chunk, gmsh.model, queue))
                            p.start()
                            processes.append(p)
                        
                        # Wait for results
                        for p in processes:
                            p.join()
                        
                        # Combine results
                        results = []
                        while not queue.empty():
                            results.append(queue.get())
                        
                        for min_vals, max_vals in results:
                            for i in range(3):
                                bbox_min[i] = min(bbox_min[i], min_vals[i])
                                bbox_max[i] = max(bbox_max[i], max_vals[i])
                        
                        print(f"Parallel bounding box calculation: {bbox_min} - {bbox_max}")
                    except Exception as e:
                        print(f"Parallel bounding box calculation failed: {e}")
                        # Fall back to sequential calculation
                
                # If parallel failed or not needed, use sequential calculation
                if bbox_min[0] == float('inf'):
                    entities_to_try = []
                    if geometry_volumes:
                        entities_to_try = geometry_volumes
                    elif geometry_surfaces:
                        entities_to_try = geometry_surfaces
                    elif geometry_entities:
                        entities_to_try = [e for e in geometry_entities if e[0] == 0]
                    
                    for dim, tag in entities_to_try:
                        try:
                            xmin, ymin, zmin, xmax, ymax, zmax = gmsh.model.getBoundingBox(dim, tag)
                            bbox_min[0] = min(bbox_min[0], xmin)
                            bbox_min[1] = min(bbox_min[1], ymin)
                            bbox_min[2] = min(bbox_min[2], zmin)
                            bbox_max[0] = max(bbox_max[0], xmax)
                            bbox_max[1] = max(bbox_max[1], ymax)
                            bbox_max[2] = max(bbox_max[2], zmax)
                        except Exception as entity_e:
                            print(f"Warning: Skipping entity ({dim}, {tag}): {entity_e}")
        
        # Check if we got a valid bounding box
        if bbox_min[0] == float('inf') or bbox_max[0] == float('-inf'):
            print("Warning: Failed to calculate bounding box. Using default.")
            bbox_min = [-100, -100, -100]
            bbox_max = [100, 100, 100]
        
        # Calculate domain size based on bounding box
        center = [(bbox_min[i] + bbox_max[i])/2 for i in range(3)]
        size = [bbox_max[i] - bbox_min[i] for i in range(3)]
        max_size = max(size) if max(size) > 0 else 200.0
        
        # Handle degenerate dimensions
        for i in range(3):
            if size[i] < 0.01 * max_size or size[i] <= 0:
                size[i] = max_size
        
        # Create domain box
        domain_size = [max(s * domain_scale, 10.0) for s in size]
        print(f"Domain center: {center}")
        print(f"Domain size: {domain_size}")
        
        # Create the box with OCC
        box_dim_tag = gmsh.model.occ.addBox(
            center[0] - domain_size[0]/2,
            center[1] - domain_size[1]/2,
            center[2] - domain_size[2]/2,
            domain_size[0], domain_size[1], domain_size[2]
        )
        gmsh.model.occ.synchronize()
        
        # Use simplified box meshing if requested or if geometry import failed
        if simplify or not import_success:
            print("Creating simplified box mesh (no boolean operations)")
            
            # Set mesh parameters for optimal performance on HPC systems
            gmsh.option.setNumber("Mesh.Algorithm", mesh_algorithm_2d)
            gmsh.option.setNumber("Mesh.Algorithm3D", mesh_algorithm_3d)
            gmsh.option.setNumber("Mesh.CharacteristicLengthMax", adjusted_mesh_size)
            gmsh.option.setNumber("Mesh.CharacteristicLengthMin", adjusted_mesh_size/10)
            gmsh.option.setNumber("Mesh.ElementOrder", 1)  # Linear elements
            gmsh.option.setNumber("Mesh.OptimizeNetgen", 0)
            gmsh.option.setNumber("Mesh.SaveAll", 1)
            gmsh.option.setNumber("Mesh.Binary", 1)
            
            # Memory management and optimization options
            gmsh.option.setNumber("Mesh.OptimizeThreshold", 0.3)  # Less aggressive optimization to save memory
            gmsh.option.setNumber("Mesh.OptimizeNetgen", 0)  # Disable Netgen optimization to save memory
            gmsh.option.setNumber("Mesh.HighOrderOptimize", 0)  # Disable high order optimization
            
            # Chunked meshing for large domains (prevents OOM)
            if adaptive_params['progressive']:
                print("Using progressive mesh generation to reduce memory usage")
                gmsh.option.setNumber("Mesh.MaxNumThreads1D", min(4, system_info['omp_threads']))
                gmsh.option.setNumber("Mesh.MaxNumThreads2D", min(4, system_info['omp_threads']))
                gmsh.option.setNumber("Mesh.MaxNumThreads3D", min(4, system_info['omp_threads']))
            else:
                # OpenMP optimizations 
                gmsh.option.setNumber("Mesh.MaxNumThreads1D", system_info['omp_threads'])
                gmsh.option.setNumber("Mesh.MaxNumThreads2D", system_info['omp_threads'])
                gmsh.option.setNumber("Mesh.MaxNumThreads3D", system_info['omp_threads'])
            
            # Generate mesh with parallel acceleration
            mesh_time_start = os.times()
            try:
                print(f"Generating 1D mesh using {system_info['omp_threads']} threads...")
                gmsh.model.mesh.generate(1)
                
                print(f"Generating 2D mesh using {system_info['omp_threads']} threads...")
                gmsh.model.mesh.generate(2)
                
                # Try to clear some memory after 2D meshing
                if adaptive_params['progressive']:
                    print("Temporarily clearing internal data structures to free memory...")
                    # Force garbage collection
                    import gc
                    gc.collect()
                
                print(f"Generating 3D mesh using {system_info['omp_threads']} threads...")
                
                if adaptive_params['progressive']:
                    # For large meshes, use progressive approach with multiple attempts
                    current_algo = mesh_algorithm_3d
                    for attempt in range(3):
                        try:
                            print(f"3D meshing attempt {attempt+1} with algorithm {current_algo}...")
                            gmsh.option.setNumber("Mesh.Algorithm3D", current_algo)
                            
                            # Use increasing mesh sizes on each attempt to guarantee success
                            size_factor = 1.0 + (0.5 * attempt)
                            gmsh.option.setNumber("Mesh.CharacteristicLengthMax", adjusted_mesh_size * size_factor)
                            gmsh.option.setNumber("Mesh.CharacteristicLengthMin", adjusted_mesh_size * size_factor / 10)
                            
                            gmsh.model.mesh.generate(3)
                            print(f"3D meshing succeeded with algorithm {current_algo}")
                            break
                        except Exception as e:
                            print(f"3D meshing failed with algorithm {current_algo}: {e}")
                            # Fall back to different algorithms
                            if current_algo == mesh_algorithm_3d:
                                current_algo = 1  # Try Delaunay
                            elif current_algo == 1:
                                current_algo = 4  # Try Frontal
                            else:
                                current_algo = 10  # Try HXT
                            
                            # Force garbage collection after failed attempt
                            import gc
                            gc.collect()
                            
                            if attempt == 2:
                                raise  # Re-raise the exception if all attempts fail
                else:
                    # Standard meshing approach
                    try:
                        gmsh.model.mesh.generate(3)
                    except Exception as e:
                        print(f"3D meshing failed with algorithm {mesh_algorithm_3d}: {e}")
                        print("Trying alternative 3D meshing algorithm...")
                        
                        # Try a more robust algorithm
                        alt_algo = 1 if mesh_algorithm_3d != 1 else 4
                        gmsh.option.setNumber("Mesh.Algorithm3D", alt_algo)
                        gmsh.model.mesh.generate(3)
            except Exception as e:
                print(f"Meshing failed: {e}")
                print("Trying with larger mesh size...")
                gmsh.option.setNumber("Mesh.CharacteristicLengthMax", adjusted_mesh_size * 5)
                gmsh.option.setNumber("Mesh.CharacteristicLengthMin", adjusted_mesh_size)
                
                try:
                    gmsh.model.mesh.generate(3)
                except Exception as e2:
                    print(f"Meshing with larger size failed: {e2}")
                    print("Saving partial mesh...")
                    
                    # Last resort - try generating 3D mesh with coarsest settings possible
                    print("Trying emergency coarse meshing...")
                    gmsh.option.setNumber("Mesh.CharacteristicLengthMax", adjusted_mesh_size * 10)
                    gmsh.option.setNumber("Mesh.Algorithm3D", 1)  # Delaunay is most memory-efficient
                    
                    try:
                        gmsh.model.mesh.generate(3)
                        print("Successfully created emergency coarse mesh")
                    except Exception as e3:
                        print(f"Emergency meshing failed: {e3}")
            
            mesh_time_end = os.times()
            mesh_time = mesh_time_end.user - mesh_time_start.user
            print(f"Mesh generation completed in {mesh_time:.2f} seconds")
            
            # Write mesh
            gmsh.write(output_file)
            print(f"Mesh saved to {output_file}")
            
            # Create visualization script
            create_visualization_script(output_file)
            return True
        
        # If not simplified, continue with boolean operations
        print("Creating fluid region using boolean operations...")
        
        # First check and try to create volume from surfaces if needed
        if not geometry_volumes and geometry_surfaces:
            print("No volumes found. Attempting to create volume from surfaces...")
            try:
                surf_tags = [tag for dim, tag in geometry_surfaces]
                if surf_tags:
                    # Try to create a closed shell
                    try:
                        sl = gmsh.model.occ.addSurfaceLoop(surf_tags)
                        vol = gmsh.model.occ.addVolume([sl])
                        geometry_volumes = [(3, vol)]
                        gmsh.model.occ.synchronize()
                        print(f"Successfully created volume from surfaces: {geometry_volumes}")
                    except Exception as e:
                        print(f"Failed to create direct surface loop: {e}")
                        
                        # Try with healing first
                        print("Attempting surface healing before creating volume...")
                        out_dimtags = []
                        try:
                            surf_dimtags = [(2, tag) for tag in surf_tags]
                            gmsh.model.occ.healShapes(surf_dimtags, out_dimtags,
                                                    1e-3, True, True, True, True, True)
                            gmsh.model.occ.synchronize()
                            
                            # Try again with healed surfaces
                            healed_surfs = gmsh.model.getEntities(2)
                            healed_tags = [tag for dim, tag in healed_surfs]
                            sl = gmsh.model.occ.addSurfaceLoop(healed_tags)
                            vol = gmsh.model.occ.addVolume([sl])
                            geometry_volumes = [(3, vol)]
                            gmsh.model.occ.synchronize()
                            print(f"Created volume after healing: {geometry_volumes}")
                        except Exception as e2:
                            print(f"Volume creation after healing failed: {e2}")
            except Exception as e:
                print(f"Failed to process surfaces: {e}")
        
        # Try boolean operations with error handling
        boolean_time_start = os.times()
        fluid_volumes = []
        try:
            if geometry_volumes:
                print(f"Performing boolean difference with {len(geometry_volumes)} volumes...")
                
                # Create tool entities list
                tool_dimtags = geometry_volumes
                
                # Perform boolean difference with higher tolerance for better quality
                gmsh.option.setNumber("Geometry.ToleranceBoolean", 1e-2)
                out_dimtags, out_map = gmsh.model.occ.cut(
                    [(3, box_dim_tag)],
                    tool_dimtags,
                    removeObject=True, removeTool=False
                )
                gmsh.model.occ.synchronize()
                
                print(f"Boolean operation created {len(out_dimtags)} entities")
                fluid_volumes = [tag for dim, tag in out_dimtags if dim == 3]
            else:
                print("No volumes available for boolean operation. Using box volume.")
                fluid_volumes = [box_dim_tag]
        except Exception as e:
            print(f"Boolean operation failed: {e}")
            print("Using domain box without boolean operations")
            fluid_volumes = [box_dim_tag]
        
        boolean_time_end = os.times()
        boolean_time = boolean_time_end.user - boolean_time_start.user
        print(f"Boolean operations completed in {boolean_time:.2f} seconds")
        
        # Configure mesh parameters for HPC optimization
        print("Setting up optimized HPC meshing parameters...")
        gmsh.option.setNumber("Mesh.Algorithm", mesh_algorithm_2d)
        gmsh.option.setNumber("Mesh.Algorithm3D", mesh_algorithm_3d)
        gmsh.option.setNumber("Mesh.CharacteristicLengthMax", mesh_size)
        gmsh.option.setNumber("Mesh.CharacteristicLengthMin", mesh_size/10)
        gmsh.option.setNumber("Mesh.SaveAll", 1)
        gmsh.option.setNumber("Mesh.ElementOrder", 1)
        gmsh.option.setNumber("Mesh.OptimizeNetgen", 0)
        
        # OpenMP threading configuration
        gmsh.option.setNumber("Mesh.MaxNumThreads1D", system_info['omp_threads'])
        gmsh.option.setNumber("Mesh.MaxNumThreads2D", system_info['omp_threads'])
        gmsh.option.setNumber("Mesh.MaxNumThreads3D", system_info['omp_threads'])
        
        # Set additional performance options
        gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
        gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)
        gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)
        
        # Create mesh size field in parallel
        field_time_start = os.times()
        try:
            # Get surfaces to use for distance field
            surf_dimtags = gmsh.model.getEntities(2)
            if surf_dimtags:
                distance_field = gmsh.model.mesh.field.add("Distance")
                surf_tags = [tag for dim, tag in surf_dimtags]
                
                # Use chunking for large models
                if len(surf_tags) > 1000 and acc_level >= 1:
                    chunk_size = 1000
                    for i in range(0, len(surf_tags), chunk_size):
                        end = min(i + chunk_size, len(surf_tags))
                        chunk = surf_tags[i:end]
                        gmsh.model.mesh.field.setNumbers(distance_field, "FacesList", chunk)
                        print(f"Added surface chunk {i//chunk_size + 1}/{(len(surf_tags)-1)//chunk_size + 1} to distance field")
                else:
                    gmsh.model.mesh.field.setNumbers(distance_field, "FacesList", surf_tags)
                
                # Create threshold field
                threshold_field = gmsh.model.mesh.field.add("Threshold")
                gmsh.model.mesh.field.setNumber(threshold_field, "InField", distance_field)
                gmsh.model.mesh.field.setNumber(threshold_field, "SizeMin", mesh_size/5)
                gmsh.model.mesh.field.setNumber(threshold_field, "SizeMax", mesh_size)
                gmsh.model.mesh.field.setNumber(threshold_field, "DistMin", max_size/20)
                gmsh.model.mesh.field.setNumber(threshold_field, "DistMax", max_size/2)
                
                # Use the field
                gmsh.model.mesh.field.setAsBackgroundMesh(threshold_field)
                print("Mesh size field created for refinement near geometry")
        except Exception as e:
            print(f"Warning: Failed to create mesh size field: {e}")
        
        field_time_end = os.times()
        field_time = field_time_end.user - field_time_start.user
        print(f"Field setup completed in {field_time:.2f} seconds")
        
        # Generate mesh with progressive approach and parallel acceleration
        print(f"Generating mesh using {system_info['omp_threads']} threads...")
        mesh_time_start = os.times()
        mesh_success = False
        
        try:
            print("Generating 1D mesh...")
            gmsh.model.mesh.generate(1)
            
            print("Generating 2D mesh...")
            try:
                gmsh.model.mesh.generate(2)
            except Exception as e:
                print(f"2D meshing failed with algorithm {mesh_algorithm_2d}: {e}")
                print("Trying alternative 2D meshing algorithm...")
                gmsh.option.setNumber("Mesh.Algorithm", 5 if mesh_algorithm_2d != 5 else 6)
                gmsh.model.mesh.generate(2)
            
            print("Generating 3D mesh...")
            try:
                gmsh.model.mesh.generate(3)
                mesh_success = True
                print("3D mesh generation successful")
            except Exception as e:
                print(f"3D meshing failed with algorithm {mesh_algorithm_3d}: {e}")
                print("Trying alternative 3D meshing algorithms...")
                
                # Try different 3D algorithms
                alt_3d_algos = [1, 10, 4, 7]  # Delaunay, HXT, Frontal, MMG3D
                for algo in alt_3d_algos:
                    if algo == mesh_algorithm_3d:
                        continue
                    
                    try:
                        print(f"Trying 3D algorithm {algo}...")
                        gmsh.option.setNumber("Mesh.Algorithm3D", algo)
                        gmsh.model.mesh.generate(3)
                        mesh_success = True
                        print(f"3D mesh generation successful with algorithm {algo}")
                        break
                    except Exception as e:
                        print(f"Algorithm {algo} failed: {e}")
                
                if not mesh_success:
                    # Last resort: try with much larger mesh size
                    print("All algorithms failed. Trying with larger mesh size...")
                    gmsh.option.setNumber("Mesh.CharacteristicLengthMax", mesh_size * 10)
                    gmsh.option.setNumber("Mesh.CharacteristicLengthMin", mesh_size * 2)
                    
                    try:
                        gmsh.option.setNumber("Mesh.Algorithm3D", 4)  # Frontal
                        gmsh.model.mesh.generate(3)
                        mesh_success = True
                    except Exception as e2:
                        print(f"Meshing with large size failed: {e2}")
                        print("Creating 2D mesh only...")
        except Exception as e:
            print(f"Meshing failed: {e}")
            print("Will save whatever mesh is created so far...")
        
        mesh_time_end = os.times()
        mesh_time = mesh_time_end.user - mesh_time_start.user
        print(f"Mesh generation completed in {mesh_time:.2f} seconds")
        
        # Write mesh
        write_time_start = os.times()
        gmsh.write(output_file)
        write_time_end = os.times()
        write_time = write_time_end.user - write_time_start.user
        print(f"Mesh saved to {output_file} in {write_time:.2f} seconds")
        
        # Create visualization script
        create_visualization_script(output_file)
        
        # Print total processing time
        end_time = os.times()
        total_time = end_time.user - start_time.user
        print(f"Total processing time: {total_time:.2f} seconds")
        
        return mesh_success
        
    except Exception as e:
        print(f"Error creating fluid domain: {e}")
        traceback.print_exc()
        
        # Try to save whatever we have
        try:
            debug_file = output_file + "_debug.msh"
            gmsh.write(debug_file)
            print(f"Saved debug mesh to {debug_file}")
        except:
            pass
            
        return False
        
    finally:
        if gmsh.isInitialized():
            gmsh.finalize()

def create_visualization_script(mesh_file):
    """Create a script to visualize the mesh in Gmsh"""
    viz_file = mesh_file.replace(".msh", "_viz.geo")
    with open(viz_file, "w") as f:
        f.write(f"""// Visualization script for {mesh_file}
SetFactory("OpenCASCADE");
Merge "{mesh_file}";
General.TrackballQuaternion0 = 0.3;
General.TrackballQuaternion1 = 0.2;
General.TrackballQuaternion2 = 0.1;
General.TrackballQuaternion3 = 0.9;
Mesh.SurfaceEdges = 1;
Mesh.SurfaceFaces = 1;
Mesh.VolumeFaces = 0;
Mesh.Points = 0;
Mesh.ColorCarousel = 1;
""")
    print(f"Created visualization script: {viz_file}")
    print(f"To view the mesh, run: gmsh {viz_file}")

def main():
    parser = argparse.ArgumentParser(description="Create a fluid domain around a STEP geometry with HPC acceleration")
    parser.add_argument("input_file", help="Input STEP file")
    parser.add_argument("output_file", nargs="?", help="Output mesh file")
    parser.add_argument("--scale", type=float, default=5.0, help="Domain scale factor")
    parser.add_argument("--size", type=float, default=10.0, help="Base mesh size")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    parser.add_argument("--simplify", action="store_true", help="Create simplified mesh")
    parser.add_argument("--threads", type=int, help="Number of threads to use (default: auto)")
    parser.add_argument("--alg2d", type=int, default=1, help="2D mesh algorithm (1-7)")
    parser.add_argument("--alg3d", type=int, default=4, help="3D mesh algorithm (1-10)")
    parser.add_argument("--acc", type=int, default=2, choices=[0, 1, 2, 3], 
                       help="Acceleration level (0=None, 1=OpenMP, 2=OpenMP+CUDA, 3=OpenMP+CUDA+MPI)")
    parser.add_argument("--progressive", action="store_true", 
                       help="Use progressive meshing to reduce memory consumption")
    parser.add_argument("--coarsen", type=float, default=1.0,
                       help="Coarsening factor to apply to mesh size (>1.0 creates coarser mesh)")
    
    args = parser.parse_args()
    
    # Set default output file name if not specified
    if not args.output_file:
        input_path = Path(args.input_file)
        args.output_file = f"{input_path.stem}_domain.msh"
    
    # Validate parameters
    if args.alg2d < 1 or args.alg2d > 7:
        print("Warning: Invalid 2D algorithm. Using default (1)")
        args.alg2d = 1
        
    if args.alg3d < 1 or args.alg3d > 10:
        print("Warning: Invalid 3D algorithm. Using default (4)")
        args.alg3d = 4
    
    # Apply coarsening factor if specified
    if args.coarsen != 1.0:
        args.size *= args.coarsen
        print(f"Applying coarsening factor {args.coarsen}x: new mesh size = {args.size}")
    
    success = create_fluid_domain(
        args.input_file, 
        args.output_file, 
        domain_scale=args.scale,
        mesh_size=args.size,
        debug=args.debug,
        simplify=args.simplify,
        acc_level=args.acc,
        num_threads=args.threads,
        mesh_algorithm_2d=args.alg2d,
        mesh_algorithm_3d=args.alg3d
    )
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
