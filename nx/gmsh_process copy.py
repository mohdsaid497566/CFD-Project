import gmsh
import sys
import os
import math
import numpy as np
import multiprocessing # Import multiprocessing to get CPU count

def create_engine_intake_cfd_mesh_surfaces_v5( # Renamed function
    step_file,
    output_msh,
    domain_scale=5.0,
    base_mesh_size=1.0,
    boundary_layer_params=None,
    mesh_algorithm_3d=10, # e.g., 10=HXT, 1=Delaunay, 4=Frontal-Delaunay, 7=MMG3D
    mesh_algorithm_2d=6,  # e.g., 6=Frontal-Delaunay, 1=MeshAdapt, 5=Delaunay
    num_threads=0,        # 0 means use Gmsh default (often all cores)
    optimize_netgen=False # Netgen optimization can be slow, make optional
):
    """
    Create a CFD mesh around engine intake surfaces (v5 - Speed focus).
    Assumes the STEP file contains only the surfaces of the intake.
    Adds multi-threading and optional optimization adjustments for speed.
    """
    # Default boundary layer parameters
    if boundary_layer_params is None:
        boundary_layer_params = {
            'first_layer_thickness': 0.05,
            'num_layers': 5,
            'progression': 1.2,
            'thickness': 0.5
        }

    # Determine number of threads
    if num_threads <= 0:
        try:
            num_threads = multiprocessing.cpu_count()
        except NotImplementedError:
            num_threads = 4 # Fallback if cpu_count fails
            print("Warning: Could not detect CPU count, defaulting to 4 threads.")
    print(f"Using {num_threads} threads for meshing.")


    try:
        # Initialize Gmsh
        gmsh.initialize(sys.argv)
        gmsh.option.setNumber("General.Terminal", 1)
        # --- Speed Improvement: Multi-threading ---
        # Set number of threads for parallel mesh generation (if Gmsh is compiled with OpenMP)
        # See api/multi_thread.py
        gmsh.option.setNumber("General.NumThreads", num_threads)

        gmsh.model.add("engine_intake_cfd_surface_v5") # Renamed model

        # --- Geometry Import and Preparation ---
        ents_before = gmsh.model.getEntities()
        gmsh.merge(step_file)
        ents_after = gmsh.model.getEntities()
        intake_surfaces_dimtags = [e for e in ents_after if e not in ents_before and e[0] == 2]

        if not intake_surfaces_dimtags:
            raise ValueError("No 2D (Surface) entities found after merging STEP file.")
        print(f"Found {len(intake_surfaces_dimtags)} intake surfaces initially.")

        gmsh.option.setNumber("Geometry.OCCFixDegenerated", 1)
        gmsh.option.setNumber("Geometry.OCCFixSmallEdges", 1)
        gmsh.option.setNumber("Geometry.OCCFixSmallFaces", 1)
        gmsh.option.setNumber("Geometry.OCCSewFaces", 1)
        gmsh.model.occ.synchronize()

        # --- Domain Creation ---
        xmin, ymin, zmin, xmax, ymax, zmax = gmsh.model.getBoundingBox(-1, -1)
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
        out_vols, out_map = gmsh.model.occ.fragment(
            [(3, domain_vol)], intake_surfaces_dimtags
        )
        gmsh.model.occ.synchronize()
        print("Fragmentation complete.")

        # --- Identify Fluid Volume and Final Intake Surfaces/Edges ---
        all_vols_after_frag = gmsh.model.getEntities(3)
        fluid_volume_tag = -1
        if len(all_vols_after_frag) >= 1:
             fluid_volume_tag = all_vols_after_frag[0][1] # Assume first is fluid
             print(f"Selected fluid volume: Tag {fluid_volume_tag} (Check if correct)")
        else:
             raise ValueError("Fragmentation did not result in any volumes.")

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
             domain_box_surface_tags = [s[1] for s in domain_box_surfaces]
             final_intake_surface_tags = [s[1] for s in fluid_boundary_dimtags if s[1] not in domain_box_surface_tags]

        if not final_intake_surface_tags:
            print("Error: Could not identify final intake surfaces for Boundary Layer.")
        else:
             print(f"Identified {len(final_intake_surface_tags)} final intake surfaces for BL/Sizing.")

        final_intake_surfaces_dimtags = [(2, tag) for tag in final_intake_surface_tags]
        boundary_curves_dimtags = gmsh.model.getBoundary(final_intake_surfaces_dimtags, combined=True, oriented=False, recursive=False)
        final_intake_edge_tags = [c[1] for c in boundary_curves_dimtags]

        if not final_intake_edge_tags:
             print("Warning: Could not retrieve boundary edges for intake surfaces. Cannot apply Boundary Layer field by edges.")
        else:
            print(f"Identified {len(final_intake_edge_tags)} unique boundary edges for BL.")

        # --- Meshing ---
        # Mesh size field
        if final_intake_surface_tags:
            mesh_field_dist_tag = gmsh.model.mesh.field.add("Distance", 1)
            gmsh.model.mesh.field.setNumbers(mesh_field_dist_tag, "FacesList", [s[1] for s in final_intake_surfaces_dimtags])
            gmsh.model.mesh.field.setNumber(mesh_field_dist_tag, "Sampling", 100) # Lower sampling might speed up field evaluation slightly

            mesh_field_thres_tag = gmsh.model.mesh.field.add("Threshold", 2)
            gmsh.model.mesh.field.setNumber(mesh_field_thres_tag, "InField", mesh_field_dist_tag)
            gmsh.model.mesh.field.setNumber(mesh_field_thres_tag, "SizeMin", base_mesh_size / 5.0)
            gmsh.model.mesh.field.setNumber(mesh_field_thres_tag, "SizeMax", base_mesh_size)
            gmsh.model.mesh.field.setNumber(mesh_field_thres_tag, "DistMin", 0.1 * max_dim)
            gmsh.model.mesh.field.setNumber(mesh_field_thres_tag, "DistMax", 0.5 * max_dim)
            gmsh.model.mesh.field.setAsBackgroundMesh(mesh_field_thres_tag)
        else:
            print("Warning: Skipping mesh size field setup.")
            gmsh.option.setNumber("Mesh.CharacteristicLengthMin", base_mesh_size / 5.0) # Set a finer min size globally
            gmsh.option.setNumber("Mesh.CharacteristicLengthMax", base_mesh_size)

        # General Mesh options
        gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
        # --- Speed Improvement: Algorithm Choice ---
        gmsh.option.setNumber("Mesh.Algorithm", mesh_algorithm_2d) # Set 2D algorithm
        gmsh.option.setNumber("Mesh.Algorithm3D", mesh_algorithm_3d) # Set 3D algorithm
        gmsh.option.setNumber("Mesh.SubdivisionAlgorithm", 2)

        # --- Speed Improvement: Optimization ---
        gmsh.option.setNumber("Mesh.Optimize", 1) # Basic optimization
        # Netgen optimization is often slower but can improve quality
        gmsh.option.setNumber("Mesh.OptimizeNetgen", 1 if optimize_netgen else 0)
        # gmsh.option.setNumber("Mesh.Smoothing", 1) # Control Lloyd smoothing passes

        # --- Boundary Layers (Field Method using EdgesList) ---
        if final_intake_edge_tags:
            bl_field_tag = gmsh.model.mesh.field.add("BoundaryLayer")
            gmsh.model.mesh.field.setNumbers(bl_field_tag, "EdgesList", final_intake_edge_tags)
            gmsh.model.mesh.field.setNumber(bl_field_tag, "Size", boundary_layer_params['first_layer_thickness'])
            gmsh.model.mesh.field.setNumber(bl_field_tag, "Ratio", boundary_layer_params['progression'])
            gmsh.model.mesh.field.setNumber(bl_field_tag, "Thickness", boundary_layer_params['thickness'])
            gmsh.model.mesh.field.setAsBoundaryLayer(bl_field_tag)
            print("Boundary Layer Field configured using EdgesList.")
        else:
            print("Skipping Boundary Layer Field setup.")

        # --- Generate Mesh ---
        print("Generating 3D mesh...")
        gmsh.model.mesh.generate(3)
        print("Mesh generation completed.")

        # --- Export Mesh ---
        # --- Speed Improvement: Binary Output ---
        gmsh.option.setNumber("Mesh.Binary", 1) # Write MSH in binary format (faster I/O)
        gmsh.write(output_msh)
        print(f"Mesh successfully exported to {output_msh}")

    except Exception as e:
        print(f"Error in mesh generation: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
    finally:
        # Finalize Gmsh
        if gmsh.isInitialized():
            if '-nopopup' not in sys.argv and sys.stdout.isatty():
                 print("Showing GUI. Close window to exit.")
                 gmsh.fltk.run()
            gmsh.finalize()

# --- Example Usage ---
if __name__ == "__main__":
    step_file = "INTAKE3D.stp"
    output_msh = "INTAKE3D_surface_domain_v5.msh"

    if not os.path.exists(step_file):
         print(f"Error: Input STEP file not found at {step_file}", file=sys.stderr)
         if 'gmsh' in sys.modules and sys.modules['gmsh'].isInitialized():
              gmsh.finalize()
         sys.exit(1)

    bl_params = {
        'first_layer_thickness': 0.05,
        'progression': 1.2,
        'thickness': 0.5,
        'num_layers': 2
    }

    create_engine_intake_cfd_mesh_surfaces_v5( # Call the renamed function
        step_file,
        output_msh,
        domain_scale=2.0,
        base_mesh_size=0.5,
        boundary_layer_params=bl_params,
        # --- Parameters for Speed Tuning ---
        num_threads=8,          # Use 0 for auto-detect or set specific number
        mesh_algorithm_3d=1,   # Try 1 (Delaunay) or 4 if HXT (10) is slow and tets are OK
        mesh_algorithm_2d=1,    # Try 1 or 5 if 6 is slow
        optimize_netgen=False   # Set to True for better quality, False for potentially faster generation
    )