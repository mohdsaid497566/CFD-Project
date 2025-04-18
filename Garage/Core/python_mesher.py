"""
Mesh processing module for the Intake CFD Optimization Suite.

This module provides functions for processing meshes, including importing
geometry files and generating meshes using Gmsh.
"""

import os
import sys
import gmsh
import numpy as np
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("python_mesher")

def process_mesh(step_file, mesh_file, mesh_size=20.0, auto_refine=True, curvature_adapt=True):
    """
    Process a STEP file to generate a mesh file using Gmsh.
    
    Args:
        step_file: Path to the input STEP geometry file
        mesh_file: Path to the output mesh file
        mesh_size: Base mesh size
        auto_refine: Whether to automatically refine the mesh based on geometry
        curvature_adapt: Whether to adapt the mesh to curvature
        
    Returns:
        bool: True if successful, False otherwise
    """
    logger.info(f"Processing {step_file} to generate {mesh_file}")
    logger.info(f"Parameters: mesh_size={mesh_size}, auto_refine={auto_refine}, curvature_adapt={curvature_adapt}")
    
    try:
        # Initialize Gmsh
        gmsh.initialize()
        gmsh.option.setNumber("General.Terminal", 1)
        gmsh.option.setNumber("General.Verbosity", 3)
        
        # Add a model
        model_name = os.path.basename(step_file).split('.')[0]
        gmsh.model.add(model_name)
        
        # Configure safer/more tolerant geometry healing options
        gmsh.option.setNumber("Geometry.Tolerance", 1e-2)
        gmsh.option.setNumber("Geometry.ToleranceBoolean", 1e-2)
        gmsh.option.setNumber("Geometry.OCCFixDegenerated", 1)
        gmsh.option.setNumber("Geometry.OCCFixSmallEdges", 1)
        gmsh.option.setNumber("Geometry.OCCFixSmallFaces", 1)
        gmsh.option.setNumber("Geometry.OCCSewFaces", 1)
        gmsh.option.setNumber("Geometry.OCCMakeSolids", 1)
        
        # Set memory options to prevent segfaults
        gmsh.option.setNumber("Mesh.MemoryMax", 2048)  # Limit memory usage
        gmsh.option.setNumber("General.NumThreads", 2)  # Limit threads
        
        # Import the geometry
        logger.info(f"Importing geometry from {step_file}")
        try:
            gmsh.merge(step_file)
        except Exception as e:
            logger.error(f"Error merging STEP file: {str(e)}")
            return False
        
        # Get the model dimensions
        logger.info("Getting model dimensions")
        xmin, ymin, zmin, xmax, ymax, zmax = get_model_bounds()
        logger.info(f"Model dimensions: {xmax-xmin} x {ymax-ymin} x {zmax-zmin}")
        
        # Set mesh size
        if auto_refine:
            # Calculate adaptive mesh size based on model dimensions
            max_dim = max(xmax-xmin, ymax-ymin, zmax-zmin)
            char_length_min = mesh_size / 10
            char_length_max = mesh_size
            
            gmsh.option.setNumber("Mesh.CharacteristicLengthMin", char_length_min)
            gmsh.option.setNumber("Mesh.CharacteristicLengthMax", char_length_max)
            
            if curvature_adapt:
                # Enable curvature-based mesh adaptation
                gmsh.option.setNumber("Mesh.CharacteristicLengthFromCurvature", 1)
                gmsh.option.setNumber("Mesh.MinimumElementsPerTwoPi", 20)
        else:
            # Use uniform mesh size
            gmsh.option.setNumber("Mesh.CharacteristicLengthMin", mesh_size / 2)
            gmsh.option.setNumber("Mesh.CharacteristicLengthMax", mesh_size)
        
        # Generate mesh
        logger.info("Generating mesh")
        try:
            # Generate 1D mesh
            logger.info("Generating 1D mesh")
            gmsh.model.mesh.generate(1)
            
            # Generate 2D mesh
            logger.info("Generating 2D mesh")
            gmsh.model.mesh.generate(2)
            
            # Generate 3D mesh
            logger.info("Generating 3D mesh")
            gmsh.model.mesh.generate(3)
        except Exception as e:
            logger.error(f"Error during mesh generation: {str(e)}")
            # Try alternative meshing approach
            try:
                logger.info("Trying alternative meshing approach")
                gmsh.option.setNumber("Mesh.Algorithm", 3)  # MeshAdapt algorithm
                gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
                gmsh.option.setNumber("Mesh.OptimizeNetgen", 1)
                
                # Retry mesh generation
                gmsh.model.mesh.clear()
                gmsh.model.mesh.generate(1)
                gmsh.model.mesh.generate(2)
                gmsh.model.mesh.generate(3)
            except Exception as e2:
                logger.error(f"Alternative meshing approach failed: {str(e2)}")
                return False
        
        # Save the mesh
        logger.info(f"Saving mesh to {mesh_file}")
        gmsh.write(mesh_file)
        
        # Get mesh statistics
        node_count = gmsh.model.mesh.getNodeCount()
        element_count = gmsh.model.mesh.getElementCount()
        logger.info(f"Mesh generated with {node_count} nodes and {element_count} elements")
        
        # Finalize Gmsh
        gmsh.finalize()
        
        return True
        
    except Exception as e:
        logger.error(f"Error in process_mesh: {str(e)}")
        # Ensure Gmsh is finalized in case of error
        try:
            gmsh.finalize()
        except:
            pass
        return False

def get_model_bounds():
    """
    Get the bounding box of the current Gmsh model.
    
    Returns:
        tuple: (xmin, ymin, zmin, xmax, ymax, zmax)
    """
    entities = []
    try:
        entities = gmsh.model.getEntities()
    except:
        return 0, 0, 0, 1, 1, 1  # Default bounds if no entities
    
    if not entities:
        return 0, 0, 0, 1, 1, 1  # Default bounds if no entities
    
    xmin, ymin, zmin = float('inf'), float('inf'), float('inf')
    xmax, ymax, zmax = float('-inf'), float('-inf'), float('-inf')
    
    for entity in entities:
        dim, tag = entity
        try:
            bounds = gmsh.model.getBoundingBox(dim, tag)
            ex_min, ey_min, ez_min, ex_max, ey_max, ez_max = bounds
            
            xmin = min(xmin, ex_min)
            ymin = min(ymin, ey_min)
            zmin = min(zmin, ez_min)
            xmax = max(xmax, ex_max)
            ymax = max(ymax, ey_max)
            zmax = max(zmax, ez_max)
        except:
            continue
    
    if xmin == float('inf'):
        return 0, 0, 0, 1, 1, 1  # Default bounds if no valid bounds found
    
    return xmin, ymin, zmin, xmax, ymax, zmax

def validate_mesh(mesh_file):
    """
    Validate a mesh file to ensure it's suitable for CFD simulation.
    
    Args:
        mesh_file: Path to the mesh file to validate
        
    Returns:
        tuple: (valid, message) where valid is a boolean and message is a string
    """
    if not os.path.exists(mesh_file):
        return False, f"Mesh file not found: {mesh_file}"
    
    try:
        # Initialize Gmsh
        gmsh.initialize()
        gmsh.option.setNumber("General.Terminal", 0)
        
        # Try to open the mesh file
        gmsh.open(mesh_file)
        
        # Get mesh statistics
        node_count = gmsh.model.mesh.getNodeCount()
        element_count = gmsh.model.mesh.getElementCount()
        
        # Check if the mesh has nodes and elements
        if node_count == 0:
            gmsh.finalize()
            return False, "Mesh has no nodes"
        
        if element_count == 0:
            gmsh.finalize()
            return False, "Mesh has no elements"
        
        # Check for 3D elements (tetrahedral, hexahedral, etc.)
        entities = gmsh.model.getEntities(3)
        if not entities:
            gmsh.finalize()
            return False, "Mesh has no 3D elements"
        
        # Finalize Gmsh
        gmsh.finalize()
        
        return True, f"Valid mesh with {node_count} nodes and {element_count} elements"
        
    except Exception as e:
        try:
            gmsh.finalize()
        except:
            pass
        return False, f"Error validating mesh: {str(e)}"

if __name__ == "__main__":
    # Simple command-line interface for testing
    import argparse
    
    parser = argparse.ArgumentParser(description="Process STEP geometry files to mesh files")
    parser.add_argument("--input", required=True, help="Input STEP file")
    parser.add_argument("--output", required=True, help="Output mesh file")
    parser.add_argument("--size", type=float, default=20.0, help="Base mesh size")
    parser.add_argument("--auto-refine", action="store_true", help="Enable automatic mesh refinement")
    parser.add_argument("--curvature-adapt", action="store_true", help="Enable curvature adaptation")
    
    args = parser.parse_args()
    
    success = process_mesh(
        args.input,
        args.output,
        mesh_size=args.size,
        auto_refine=args.auto_refine,
        curvature_adapt=args.curvature_adapt
    )
    
    if success:
        print("Mesh processing completed successfully")
        sys.exit(0)
    else:
        print("Mesh processing failed")
        sys.exit(1)
