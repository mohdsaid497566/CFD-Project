import gmsh
import sys

gmsh.initialize()
gmsh.model.add("test_intake")

# Create a simple intake-like geometry
gmsh.model.occ.addBox(0, 0, 0, 10, 1, 1, 1)  # Main intake duct
gmsh.model.occ.addCylinder(10, 0.5, 0.5, 3, 0, 0, 0.5, 2)  # Outlet cylinder

# Fuse the geometries (fixed the cut operation that was causing errors)
fused = gmsh.model.occ.fuse([(3,1)], [(3,2)], 3)[0]

# Create a side feature
box = gmsh.model.occ.addBox(2, -0.5, 0, 1, 2, 1, 4)  # Side feature
# Cut with a different tag (don't use tag 5 which was causing issues)
result = gmsh.model.occ.cut(fused, [(3,4)])

gmsh.model.occ.synchronize()
gmsh.write("./test_data/test_intake.stp")
gmsh.write("./test_data/test_intake.geo_unrolled")

# Create a reference mesh
gmsh.option.setNumber("Mesh.Algorithm", 6)
gmsh.option.setNumber("Mesh.Algorithm3D", 10)
gmsh.option.setNumber("Mesh.CharacteristicLengthFactor", 0.5)
gmsh.model.mesh.generate(3)
gmsh.write("./test_data/reference_mesh.msh")

gmsh.finalize()
