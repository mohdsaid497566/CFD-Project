#!/usr/bin/env python3
# filepath: /mnt/c/Users/Mohammed/Desktop/Intake-CFD-Project/nx/bc_manager.py

import sys
import os
import argparse
import json
import gmsh
import numpy as np
from enum import Enum
from typing import List, Dict, Tuple, Any

class BoundaryType(Enum):
    INLET = "inlet"
    OUTLET = "outlet"
    WALL = "wall"
    SYMMETRY = "symmetry"
    PERIODIC = "periodic"
    FAR_FIELD = "farfield"
    INTERNAL = "internal"
    CUSTOM = "custom"

class SolverType(Enum):
    OPENFOAM = "openfoam"
    FLUENT = "fluent"
    SU2 = "su2"
    STARCCM = "starccm"
    CODE_SATURNE = "code_saturne"
    CONVERGE = "converge"

class BCManager:
    """
    Tool for managing boundary conditions across different CFD solvers.
    """
    
    def __init__(self, mesh_file=None):
        """Initialize the BC manager with an optional mesh file."""
        self.mesh_file = mesh_file
        self.mesh_initialized = False
        self.boundary_groups = {}  # Dict mapping group names to lists of boundary IDs
        self.boundary_types = {}   # Dict mapping boundary IDs to boundary types
        self.boundary_data = {}    # Dict mapping boundary IDs to additional data
        self.bc_templates = self._load_bc_templates()
        
    def initialize(self):
        """Initialize Gmsh and load the mesh."""
        if not self.mesh_file:
            raise ValueError("No mesh file provided")
            
        print(f"Initializing Gmsh to process {self.mesh_file}")
        gmsh.initialize()
        gmsh.option.setNumber("General.Terminal", 1)
        
        try:
            gmsh.open(self.mesh_file)
            self.mesh_initialized = True
            print(f"Successfully loaded mesh: {self.mesh_file}")
            
            # Identify physical groups which are usually used for boundaries
            self._identify_boundaries()
            
        except Exception as e:
            gmsh.finalize()
            raise RuntimeError(f"Failed to open mesh file: {str(e)}")
    
    def _identify_boundaries(self):
        """Identify boundaries in the mesh."""
        # Try to identify physical groups first (preferred way to define boundaries)
        physical_groups = gmsh.model.getPhysicalGroups()
        
        if not physical_groups:
            print("No physical groups found in mesh. Trying to identify boundary surfaces...")
            self._identify_boundaries_from_topology()
            return
            
        for dim, tag in physical_groups:
            if dim == 1 or dim == 2:  # 1D lines or 2D surfaces can be boundaries
                name = gmsh.model.getPhysicalName(dim, tag)
                if not name:
                    name = f"Group_{dim}_{tag}"
                    
                print(f"Found physical group: {name} (dim={dim}, tag={tag})")
                
                # Store the boundary
                self.boundary_groups[name] = [(dim, tag)]
                
                # Try to guess boundary type from name
                lower_name = name.lower()
                if any(x in lower_name for x in ["inlet", "inflow", "entry"]):
                    self.boundary_types[name] = BoundaryType.INLET
                elif any(x in lower_name for x in ["outlet", "outflow", "exit"]):
                    self.boundary_types[name] = BoundaryType.OUTLET
                elif any(x in lower_name for x in ["wall", "walls", "solid", "noslip"]):
                    self.boundary_types[name] = BoundaryType.WALL
                elif any(x in lower_name for x in ["symmetry", "sym"]):
                    self.boundary_types[name] = BoundaryType.SYMMETRY
                elif any(x in lower_name for x in ["periodic"]):
                    self.boundary_types[name] = BoundaryType.PERIODIC
                elif any(x in lower_name for x in ["farfield", "far", "infinity"]):
                    self.boundary_types[name] = BoundaryType.FAR_FIELD
                else:
                    self.boundary_types[name] = BoundaryType.WALL  # Default to wall
    
    def _identify_boundaries_from_topology(self):
        """Identify boundaries based on model topology (if no physical groups)."""
        # For 3D models, look for surface entities with only one adjacent volume
        # For 2D models, look for curve entities with only one adjacent surface
        
        dim = 3  # Start assuming it's a 3D model
        entities = gmsh.model.getEntities(dim)
        
        if not entities:
            dim = 2  # Try 2D model
            entities = gmsh.model.getEntities(dim)
            
        if not entities:
            print("No 2D or 3D entities found in mesh.")
            return
            
        # Get boundary entities
        boundary_entities = []
        if dim == 3:
            all_surfaces = gmsh.model.getEntities(2)
            for surface in all_surfaces:
                adj_volumes = gmsh.model.getAdjacencies(2, surface[1])[0]
                if len(adj_volumes) == 1:  # Boundary surface
                    boundary_entities.append(surface)
                    
        else:  # dim == 2
            all_curves = gmsh.model.getEntities(1)
            for curve in all_curves:
                adj_surfaces = gmsh.model.getAdjacencies(1, curve[1])[0]
                if len(adj_surfaces) == 1:  # Boundary curve
                    boundary_entities.append(curve)
        
        print(f"Found {len(boundary_entities)} boundary entities")
        
        # Try to identify specific boundaries based on geometry
        if boundary_entities:
            # Group boundaries by orientation to identify inlets/outlets/etc.
            self._group_by_orientation(boundary_entities)
    
    def _group_by_orientation(self, boundary_entities):
        """Group boundary entities by orientation to identify inlets/outlets/etc."""
        # Calculate normals for each boundary entity
        normals = {}
        
        for entity in boundary_entities:
            # Get center point of entity
            dim, tag = entity
            center = [0, 0, 0]
            
            # Get all nodes on this entity
            node_tags = set()
            types = gmsh.model.mesh.getElementTypes(dim, tag)
            
            for t in types:
                elem_tags, node_tags_per_elem = gmsh.model.mesh.getElementsByType(t, tag)
                for nodes in node_tags_per_elem:
                    node_tags.update(nodes)
            
            # Calculate center
            if node_tags:
                for node_tag in node_tags:
                    node_coord = gmsh.model.mesh.getNode(node_tag)[0]
                    center = [center[i] + node_coord[i] / len(node_tags) for i in range(3)]
            
            # Assume that normal points away from the origin
            # This is a simplistic approach but works for many simple geometries
            normal = np.array(center)
            norm = np.linalg.norm(normal)
            if norm > 1e-10:
                normal = normal / norm
            else:
                normal = np.array([0, 0, 1])  # Default if center is at origin
                
            normals[entity] = normal
        
        # Group by major axis direction
        pos_x = []
        neg_x = []
        pos_y = []
        neg_y = []
        pos_z = []
        neg_z = []
        
        for entity, normal in normals.items():
            # Find dominant direction
            abs_normal = np.abs(normal)
            max_idx = np.argmax(abs_normal)
            
            if max_idx == 0:  # X-axis dominant
                if normal[0] > 0:
                    pos_x.append(entity)
                else:
                    neg_x.append(entity)
            elif max_idx == 1:  # Y-axis dominant
                if normal[1] > 0:
                    pos_y.append(entity)
                else:
                    neg_y.append(entity)
            else:  # Z-axis dominant
                if normal[2] > 0:
                    pos_z.append(entity)
                else:
                    neg_z.append(entity)
        
        # Create boundary groups
        # Guess: negative X might be inlet, positive X might be outlet
        if neg_x:
            self.boundary_groups["inlet"] = neg_x
            self.boundary_types["inlet"] = BoundaryType.INLET
            
        if pos_x:
            self.boundary_groups["outlet"] = pos_x
            self.boundary_types["outlet"] = BoundaryType.OUTLET
            
        # Group remaining as walls
        walls = []
        if pos_y:
            walls.extend(pos_y)
        if neg_y:
            walls.extend(neg_y)
        if pos_z:
            walls.extend(pos_z)
        if neg_z:
            walls.extend(neg_z)
            
        if walls:
            self.boundary_groups["walls"] = walls
            self.boundary_types["walls"] = BoundaryType.WALL
            
        print(f"Automatically identified: {len(self.boundary_groups)} boundary groups")
        for name, entities in self.boundary_groups.items():
            print(f"  - {name}: {len(entities)} entities")
    
    def _load_bc_templates(self):
        """Load boundary condition templates from file or use defaults."""
        templates_file = os.path.join(os.path.dirname(__file__), "bc_templates.json")
        
        if os.path.exists(templates_file):
            try:
                with open(templates_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load templates file: {str(e)}")
        
        # Default templates if file not found
        return {
            "openfoam": {
                "inlet": {
                    "velocity": {
                        "type": "fixedValue",
                        "value": "uniform (0 0 10)"
                    },
                    "pressure": {
                        "type": "zeroGradient"
                    }
                },
                "outlet": {
                    "velocity": {
                        "type": "zeroGradient"
                    },
                    "pressure": {
                        "type": "fixedValue",
                        "value": "uniform 0"
                    }
                },
                "wall": {
                    "velocity": {
                        "type": "noSlip"
                    },
                    "pressure": {
                        "type": "zeroGradient"
                    }
                },
                "symmetry": {
                    "type": "symmetry"
                }
            },
            "su2": {
                "inlet": {
                    "marker": "MARKER_INLET",
                    "type": "INLET_VELOCITY",
                    "params": "( 10.0, 0.0, 0.0, 0.0, 0.0 )"
                },
                "outlet": {
                    "marker": "MARKER_OUTLET",
                    "type": "OUTLET_PRESSURE",
                    "params": "( 101325.0 )"
                },
                "wall": {
                    "marker": "MARKER_WALL",
                    "type": "WALL",
                    "params": "( NO_SLIP )"
                },
                "symmetry": {
                    "marker": "MARKER_SYM",
                    "type": "SYMMETRY"
                },
                "farfield": {
                    "marker": "MARKER_FARFIELD",
                    "type": "FAR_FIELD",
                    "params": "( 101325.0, 300.0, 1.0, 0.0, 0.0 )"
                }
            },
            "fluent": {
                "inlet": "velocity-inlet",
                "outlet": "pressure-outlet",
                "wall": "wall",
                "symmetry": "symmetry",
                "periodic": "periodic",
                "farfield": "pressure-far-field"
            },
            "starccm": {
                "inlet": "Velocity Inlet",
                "outlet": "Pressure Outlet",
                "wall": "Wall",
                "symmetry": "Symmetry Plane"
            }
        }
    
    def assign_boundary_type(self, boundary_name, boundary_type):
        """Assign a boundary condition type to a boundary."""
        if boundary_name not in self.boundary_groups:
            raise ValueError(f"Boundary '{boundary_name}' not found")
            
        if isinstance(boundary_type, str):
            try:
                boundary_type = BoundaryType(boundary_type)
            except ValueError:
                print(f"Warning: Unknown boundary type '{boundary_type}'. Using CUSTOM.")
                boundary_type = BoundaryType.CUSTOM
                
        self.boundary_types[boundary_name] = boundary_type
        print(f"Assigned boundary '{boundary_name}' as {boundary_type.value}")
    
    def rename_boundary(self, old_name, new_name):
        """Rename a boundary group."""
        if old_name not in self.boundary_groups:
            raise ValueError(f"Boundary '{old_name}' not found")
            
        self.boundary_groups[new_name] = self.boundary_groups.pop(old_name)
        if old_name in self.boundary_types:
            self.boundary_types[new_name] = self.boundary_types.pop(old_name)
        if old_name in self.boundary_data:
            self.boundary_data[new_name] = self.boundary_data.pop(old_name)
            
        print(f"Renamed boundary from '{old_name}' to '{new_name}'")
    
    def merge_boundaries(self, names, new_name):
        """Merge multiple boundaries into one."""
        entities = []
        for name in names:
            if name not in self.boundary_groups:
                print(f"Warning: Boundary '{name}' not found, skipping")
                continue
                
            entities.extend(self.boundary_groups[name])
            
        if not entities:
            raise ValueError("No valid boundaries to merge")
            
        self.boundary_groups[new_name] = entities
        
        # Inherit boundary type from the first valid group
        for name in names:
            if name in self.boundary_types:
                self.boundary_types[new_name] = self.boundary_types[name]
                break
                
        print(f"Merged {len(names)} boundaries into '{new_name}'")
    
    def set_boundary_data(self, boundary_name, data):
        """Set additional data for a boundary."""
        if boundary_name not in self.boundary_groups:
            raise ValueError(f"Boundary '{boundary_name}' not found")
            
        self.boundary_data[boundary_name] = data
        print(f"Set data for boundary '{boundary_name}'")
    
    def auto_detect_boundaries(self):
        """Try to automatically detect inlets, outlets, and walls."""
        if not self.mesh_initialized:
            self.initialize()
            
        print("Attempting to auto-detect boundary types...")
        
        # This has already been done during initialization, just log the results
        for name, bc_type in self.boundary_types.items():
            print(f"  - {name}: detected as {bc_type.value}")
    
    def generate_openfoam_bc(self, output_dir):
        """Generate OpenFOAM boundary condition files."""
        if not self.mesh_initialized:
            self.initialize()
            
        print(f"Generating OpenFOAM boundary conditions in: {output_dir}")
        os.makedirs(output_dir, exist_ok=True)
        
        # Create 0/ directory for fields
        zero_dir = os.path.join(output_dir, "0")
        os.makedirs(zero_dir, exist_ok=True)
        
        # Generate U file (velocity)
        u_file = os.path.join(zero_dir, "U")
        with open(u_file, "w") as f:
            f.write("/*--------------------------------*- C++ -*----------------------------------*\\\n")
            f.write("| =========                 |                                                 |\n")
            f.write("| \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |\n")
            f.write("|  \\\\    /   O peration     | Version:  v2112                                 |\n")
            f.write("|   \\\\  /    A nd           | Website:  www.openfoam.com                      |\n")
            f.write("|    \\\\/     M anipulation  |                                                 |\n")
            f.write("\\*---------------------------------------------------------------------------*/\n")
            f.write("FoamFile\n")
            f.write("{\n")
            f.write("    version     2.0;\n")
            f.write("    format      ascii;\n")
            f.write("    class       volVectorField;\n")
            f.write("    object      U;\n")
            f.write("}\n")
            f.write("// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //\n")
            f.write("\n")
            f.write("dimensions      [0 1 -1 0 0 0 0];\n")
            f.write("\n")
            f.write("internalField   uniform (0 0 0);\n")
            f.write("\n")
            f.write("boundaryField\n")
            f.write("{\n")
            
            # Write boundary conditions for each group
            for name, bc_type in self.boundary_types.items():
                f.write(f"    {name}\n")
                f.write("    {\n")
                
                # Get appropriate BC for this type
                templates = self.bc_templates.get("openfoam", {})
                bc_template = templates.get(bc_type.value, {}).get("velocity", {})
                
                if bc_template:
                    for key, value in bc_template.items():
                        f.write(f"        {key}    {value};\n")
                else:
                    # Default
                    if bc_type == BoundaryType.INLET:
                        f.write("        type    fixedValue;\n")
                        f.write("        value   uniform (10 0 0);\n")
                    elif bc_type == BoundaryType.OUTLET:
                        f.write("        type    zeroGradient;\n")
                    elif bc_type == BoundaryType.WALL:
                        f.write("        type    noSlip;\n")
                    elif bc_type == BoundaryType.SYMMETRY:
                        f.write("        type    symmetry;\n")
                    else:
                        f.write("        type    zeroGradient;\n")
                
                f.write("    }\n")
                
            f.write("}\n")
            f.write("\n")
            f.write("// ************************************************************************* //\n")
            
        # Generate p file (pressure)
        p_file = os.path.join(zero_dir, "p")
        with open(p_file, "w") as f:
            f.write("/*--------------------------------*- C++ -*----------------------------------*\\\n")
            f.write("| =========                 |                                                 |\n")
            f.write("| \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |\n")
            f.write("|  \\\\    /   O peration     | Version:  v2112                                 |\n")
            f.write("|   \\\\  /    A nd           | Website:  www.openfoam.com                      |\n")
            f.write("|    \\\\/     M anipulation  |                                                 |\n")
            f.write("\\*---------------------------------------------------------------------------*/\n")
            f.write("FoamFile\n")
            f.write("{\n")
            f.write("    version     2.0;\n")
            f.write("    format      ascii;\n")
            f.write("    class       volScalarField;\n")
            f.write("    object      p;\n")
            f.write("}\n")
            f.write("// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //\n")
            f.write("\n")
            f.write("dimensions      [0 2 -2 0 0 0 0];\n")
            f.write("\n")
            f.write("internalField   uniform 0;\n")
            f.write("\n")
            f.write("boundaryField\n")
            f.write("{\n")
            
            # Write boundary conditions for each group
            for name, bc_type in self.boundary_types.items():
                f.write(f"    {name}\n")
                f.write("    {\n")
                
                # Get appropriate BC for this type
                templates = self.bc_templates.get("openfoam", {})
                bc_template = templates.get(bc_type.value, {}).get("pressure", {})
                
                if bc_template:
                    for key, value in bc_template.items():
                        f.write(f"        {key}    {value};\n")
                else:
                    # Default
                    if bc_type == BoundaryType.INLET:
                        f.write("        type    zeroGradient;\n")
                    elif bc_type == BoundaryType.OUTLET:
                        f.write("        type    fixedValue;\n")
                        f.write("        value   uniform 0;\n")
                    elif bc_type == BoundaryType.WALL:
                        f.write("        type    zeroGradient;\n")
                    elif bc_type == BoundaryType.SYMMETRY:
                        f.write("        type    symmetry;\n")
                    else:
                        f.write("        type    zeroGradient;\n")
                
                f.write("    }\n")
                
            f.write("}\n")
            f.write("\n")
            f.write("// ************************************************************************* //\n")
            
        print(f"Generated OpenFOAM BC files: U and p in {zero_dir}")
        return [u_file, p_file]
    
    def generate_su2_bc(self, output_file):
        """Generate SU2 boundary condition configuration."""
        if not self.mesh_initialized:
            self.initialize()
            
        print(f"Generating SU2 boundary conditions in: {output_file}")
        
        with open(output_file, "w") as f:
            f.write("% Boundary condition configuration for SU2\n")
            f.write("% Generated by Intake CFD Project BC Manager\n\n")
            
            # Write marker definitions
            markers = []
            for name, bc_type in self.boundary_types.items():
                # Get appropriate marker for this type
                templates = self.bc_templates.get("su2", {})
                bc_template = templates.get(bc_type.value, {})
                
                if bc_template:
                    marker = bc_template.get("marker", name.upper())
                    markers.append(marker)
                    
                    # Write marker definition
                    f.write(f"% Boundary: {name} ({bc_type.value})\n")
                    
                    # Marker name
                    f.write(f"MARKER_NAME= {name}\n")
                    
                    # Boundary condition type
                    bc_su2_type = bc_template.get("type", "WALL")
                    f.write(f"MARKER_{bc_su2_type}= ( {marker}")
                    
                    # Parameters if any
                    params = bc_template.get("params", "")
                    if params:
                        f.write(f", {params}")
                        
                    f.write(" )\n\n")
                    
            # Write the combined marker list
            f.write("% All markers\n")
            f.write("MARKER_LIST= (")
            f.write(", ".join(markers))
            f.write(" )\n\n")
            
            # Write some common settings based on the boundaries we have
            f.write("% Common settings based on boundary types\n")
            
            # If we have walls, enable wall functions
            if any(bc_type == BoundaryType.WALL for bc_type in self.boundary_types.values()):
                f.write("WALL_FUNCTION= YES\n")
                
            # If we have inlets/outlets, suggest incompressible flow
            if any(bc_type in [BoundaryType.INLET, BoundaryType.OUTLET] for bc_type in self.boundary_types.values()):
                f.write("SOLVER= NAVIER_STOKES\n")
                f.write("KIND_TURB_MODEL= SST\n")
                
            # If we have far field, suggest compressible flow
            if any(bc_type == BoundaryType.FAR_FIELD for bc_type in self.boundary_types.values()):
                f.write("SOLVER= EULER\n")
                f.write("MACH_NUMBER= 0.8\n")
                
            print(f"Generated SU2 BC file: {output_file}")
            return output_file
    
    def generate_fluent_bc(self, output_file):
        """Generate ANSYS Fluent journal file for boundary conditions."""
        if not self.mesh_initialized:
            self.initialize()
            
        print(f"Generating Fluent boundary conditions in: {output_file}")
        
        with open(output_file, "w") as f:
            f.write(";; Fluent Journal File for Boundary Conditions\n")
            f.write(";; Generated by Intake CFD Project BC Manager\n\n")
            
            # Define boundary types
            for name, bc_type in self.boundary_types.items():
                # Get appropriate BC for this type
                templates = self.bc_templates.get("fluent", {})
                fluent_type = templates.get(bc_type.value, "wall")
                
                f.write(f";; Setting boundary {name} as {fluent_type}\n")
                f.write(f"define/boundary-conditions/modify-zones/zone-type {name} {fluent_type} ;\n\n")
                
                # Set specific parameters based on boundary type
                if bc_type == BoundaryType.INLET:
                    f.write(f";; Setting velocity inlet parameters for {name}\n")
                    f.write(f"define/boundary-conditions/velocity-inlet {name} no yes no 10 no 0 no 0 no 0 no 0 no 1 no no yes 5 10 ;\n\n")
                    
                elif bc_type == BoundaryType.OUTLET:
                    f.write(f";; Setting pressure outlet parameters for {name}\n")
                    f.write(f"define/boundary-conditions/pressure-outlet {name} no 0 no 0 no no yes 5 10 ;\n\n")
                    
            print(f"Generated Fluent BC journal file: {output_file}")
            return output_file
    
    def save_boundary_definitions(self, output_file):
        """Save boundary definitions to a JSON file."""
        data = {
            "boundary_groups": {name: [list(entity) for entity in entities] 
                               for name, entities in self.boundary_groups.items()},
            "boundary_types": {name: bc_type.value for name, bc_type in self.boundary_types.items()},
            "boundary_data": self.boundary_data
        }
        
        with open(output_file, "w") as f:
            json.dump(data, f, indent=2)
            
        print(f"Saved boundary definitions to: {output_file}")
        return output_file
    
    def load_boundary_definitions(self, input_file):
        """Load boundary definitions from a JSON file."""
        with open(input_file, "r") as f:
            data = json.load(f)
            
        # Load boundary groups
        self.boundary_groups = {name: [tuple(entity) for entity in entities]
                               for name, entities in data.get("boundary_groups", {}).items()}
        
        # Load boundary types
        self.boundary_types = {name: BoundaryType(bc_type) 
                              for name, bc_type in data.get("boundary_types", {}).items()}
        
        # Load boundary data
        self.boundary_data = data.get("boundary_data", {})
        
        print(f"Loaded boundary definitions from: {input_file}")
        print(f"  - {len(self.boundary_groups)} boundary groups")
        print(f"  - {len(self.boundary_types)} boundary types")
    
    def finalize(self):
        """Clean up Gmsh resources."""
        if gmsh.isInitialized():
            gmsh.finalize()
            self.mesh_initialized = False
            
    def __del__(self):
        """Ensure Gmsh is finalized when the object is destroyed."""
        self.finalize()


def main():
    """Main function to handle command-line interface."""
    parser = argparse.ArgumentParser(description="Boundary condition manager for CFD simulations")
    parser.add_argument("mesh_file", help="Path to the mesh file to analyze")
    
    # General options
    parser.add_argument("--auto-detect", action="store_true", help="Automatically detect boundary types")
    parser.add_argument("--rename", nargs=2, metavar=('OLD_NAME', 'NEW_NAME'), help="Rename a boundary")
    parser.add_argument("--merge", nargs='+', help="Merge boundaries: --merge name1 name2 ... nameN new_name")
    parser.add_argument("--assign", nargs=2, metavar=('NAME', 'TYPE'), help="Assign boundary type: NAME TYPE")
    
    # Export options
    parser.add_argument("--openfoam", help="Generate OpenFOAM BCs in the specified directory")
    parser.add_argument("--su2", help="Generate SU2 BC file")
    parser.add_argument("--fluent", help="Generate Fluent journal file for BCs")
    
    # Save/load definitions
    parser.add_argument("--save", help="Save boundary definitions to file")
    parser.add_argument("--load", help="Load boundary definitions from file")
    
    args = parser.parse_args()
    
    try:
        bc_manager = BCManager(args.mesh_file)
        bc_manager.initialize()
        
        # Process operations in order
        if args.load:
            bc_manager.load_boundary_definitions(args.load)
            
        if args.auto_detect:
            bc_manager.auto_detect_boundaries()
            
        if args.rename:
            bc_manager.rename_boundary(args.rename[0], args.rename[1])
            
        if args.merge:
            if len(args.merge) < 3:
                print("Error: --merge requires at least 2 source boundaries and 1 target name")
            else:
                source_names = args.merge[:-1]
                new_name = args.merge[-1]
                bc_manager.merge_boundaries(source_names, new_name)
                
        if args.assign:
            bc_manager.assign_boundary_type(args.assign[0], args.assign[1])
            
        # Generate output
        if args.openfoam:
            bc_manager.generate_openfoam_bc(args.openfoam)
            
        if args.su2:
            bc_manager.generate_su2_bc(args.su2)
            
        if args.fluent:
            bc_manager.generate_fluent_bc(args.fluent)
            
        if args.save:
            bc_manager.save_boundary_definitions(args.save)
            
        bc_manager.finalize()
        
    except Exception as e:
        print(f"Error: {str(e)}")
        if 'bc_manager' in locals():
            bc_manager.finalize()
        sys.exit(1)


if __name__ == "__main__":
    main()