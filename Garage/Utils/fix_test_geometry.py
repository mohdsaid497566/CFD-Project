#!/usr/bin/env python3

import os
import gmsh
import sys

def create_test_geometry():
    """Create a simple test geometry for testing"""
    print("Creating test geometry...")
    
    # Initialize Gmsh
    gmsh.initialize()
    gmsh.model.add("test_intake")
    
    # Create a simple intake-like geometry
    # Main intake duct
    box = gmsh.model.occ.addBox(0, 0, 0, 10, 1, 1)
    
    # Outlet cylinder
    cyl = gmsh.model.occ.addCylinder(10, 0.5, 0.5, 3, 0, 0, 0.5)
    
    # Fuse the box and cylinder
    fused_entities, fused_map = gmsh.model.occ.fuse([(3, box)], [(3, cyl)])
    
    # Synchronize to update the model
    gmsh.model.occ.synchronize()
    
    # Ensure the test_data directory exists
    test_dir = "./test_data"
    os.makedirs(test_dir, exist_ok=True)
    
    # Save the geometry
    stp_file = os.path.join(test_dir, "test_intake.stp")
    gmsh.write(stp_file)
    print(f"Wrote geometry to {stp_file}")
    
    # Create a mesh
    gmsh.option.setNumber("Mesh.Algorithm", 6)
    gmsh.option.setNumber("Mesh.Algorithm3D", 1)  # Use more reliable algorithm
    gmsh.option.setNumber("Mesh.CharacteristicLengthFactor", 0.5)
    
    try:
        gmsh.model.mesh.generate(3)
        print("Generated 3D mesh")
        
        # Save the mesh
        mesh_file = os.path.join(test_dir, "reference_mesh.msh")
        gmsh.write(mesh_file)
        print(f"Wrote mesh to {mesh_file}")
    except Exception as e:
        print(f"Error generating mesh: {e}")
    
    gmsh.finalize()
    return True

if __name__ == "__main__":
    create_test_geometry()
    print("Test geometry creation completed.")
