import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List

from .logger import logger
from .mesh_info import MeshInfo

def convert_mesh(input_file: str, output_file: str, **options) -> bool:
    """
    Convert mesh file formats using GMSH or other tools.
    
    Args:
        input_file: Path to input mesh file
        output_file: Path to output mesh file
        **options: Additional options for conversion
    
    Returns:
        True if conversion was successful
    """
    input_ext = os.path.splitext(input_file)[1].lower()
    output_ext = os.path.splitext(output_file)[1].lower()
    
    # GMSH to OpenFOAM
    if input_ext == '.msh' and output_ext == '.foam':
        try:
            # Convert using gmshToFoam
            process = subprocess.run(
                ['gmshToFoam', input_file],
                capture_output=True, text=True, check=True
            )
            
            # Move polyMesh directory to the correct location
            src = os.path.join(os.getcwd(), 'constant', 'polyMesh')
            dst = os.path.join(os.path.dirname(output_file), 'constant', 'polyMesh')
            
            if os.path.exists(src):
                if os.path.exists(dst):
                    shutil.rmtree(dst)
                shutil.move(src, dst)
            
            return True
            
        except Exception as e:
            logger.error(f"Error converting GMSH to OpenFOAM: {e}")
            return False
            
    # STL to GMSH
    elif input_ext == '.stl' and output_ext == '.msh':
        try:
            # Create a temporary geo file
            with tempfile.NamedTemporaryFile(suffix='.geo', delete=False) as geo_file:
                geo_path = geo_file.name
                geo_file.write(f"""
// Geo file for converting STL to GMSH
Merge "{os.path.abspath(input_file)}";
Surface Loop(1) = {1};
// Set mesh size
Mesh.CharacteristicLengthMin = {options.get('min_size', 0.1)};
Mesh.CharacteristicLengthMax = {options.get('max_size', 1.0)};
""".encode())
            
            try:
                # Run gmsh to generate mesh
                cmd = [
                    'gmsh', geo_path, '-3', '-format', 'msh', 
                    '-o', output_file, '-optimize_netgen'
                ]
                
                # Add verbosity level
                cmd.extend(['-v', str(options.get('verbosity', 1))])
                
                # Add other gmsh options
                for key, value in options.items():
                    if key.startswith('gmsh_'):
                        cmd.extend([f'-{key[5:]}', str(value)])
                
                process = subprocess.run(
                    cmd, capture_output=True, text=True, check=True
                )
                
                return os.path.exists(output_file)
                
            finally:
                # Clean up temporary file
                os.unlink(geo_path)
                
        except Exception as e:
            logger.error(f"Error converting STL to GMSH: {e}")
            return False
    
    logger.error(f"Unsupported conversion: {input_ext} to {output_ext}")
    return False

def check_mesh_quality(mesh_file: str) -> Dict[str, Any]:
    """
    Check mesh quality using OpenFOAM's checkMesh.
    
    Args:
        mesh_file: Path to mesh file (.foam file or polyMesh directory)
    
    Returns:
        Dictionary with quality metrics
    """
    # Determine case directory
    mesh_path = Path(mesh_file)
    case_dir = None
    
    if mesh_path.name == 'polyMesh' and mesh_path.is_dir():
        # If mesh_file is a polyMesh directory
        case_dir = str(mesh_path.parent.parent.parent)
    elif mesh_path.suffix == '.foam':
        # If mesh_file is a .foam file
        case_dir = str(mesh_path.parent)
    else:
        logger.error(f"Unsupported mesh file format for quality check: {mesh_file}")
        return {"error": "Unsupported mesh format"}
    
    try:
        # Run checkMesh to get quality metrics
        process = subprocess.run(
            ['checkMesh', '-case', case_dir],
            capture_output=True, text=True, check=False
        )
        
        # Parse output to get quality metrics
        metrics = {
            "mesh_check_passed": "Failed" not in process.stdout,
            "non_orthogonality": None,
            "skewness": None,
            "cell_aspect_ratio": None,
            "min_volume": None,
            "max_aspect_ratio": None
        }
        
        # Extract metrics from output
        for line in process.stdout.splitlines():
            line = line.strip()
            
            if "Max non-orthogonality" in line:
                try:
                    metrics["non_orthogonality"] = float(line.split('=')[1].strip().split()[0])
                except:
                    pass
                    
            elif "Max skewness" in line:
                try:
                    metrics["skewness"] = float(line.split('=')[1].strip().split()[0])
                except:
                    pass
                    
            elif "Max aspect ratio" in line:
                try:
                    metrics["max_aspect_ratio"] = float(line.split('=')[1].strip())
                except:
                    pass
                    
            elif "Min volume" in line:
                try:
                    metrics["min_volume"] = float(line.split('=')[1].strip().split()[0])
                except:
                    pass
        
        # Add raw output for reference
        metrics["raw_output"] = process.stdout
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error checking mesh quality: {e}")
        return {"error": str(e)}

def create_simple_geometry(output_file: str, geometry_type: str, dimensions: Dict[str, float], **options) -> bool:
    """
    Create a simple geometry and mesh using GMSH.
    
    Args:
        output_file: Output mesh file (.msh)
        geometry_type: Type of geometry ('box', 'cylinder', 'sphere')
        dimensions: Dictionary with dimensions
        **options: Additional options
    
    Returns:
        True if creation was successful
    """
    try:
        # Create a geo file
        with tempfile.NamedTemporaryFile(suffix='.geo', delete=False) as geo_file:
            geo_path = geo_file.name
            
            if geometry_type == 'box':
                # Get dimensions
                lx = dimensions.get('length', 1.0)
                ly = dimensions.get('width', 1.0)
                lz = dimensions.get('height', 1.0)
                
                # Create box geometry
                geo_content = f"""
// Box geometry
lx = {lx};
ly = {ly};
lz = {lz};
mesh_size = {options.get('mesh_size', min(lx, ly, lz) / 10)};

Point(1) = {{0, 0, 0, mesh_size}};
Point(2) = {{lx, 0, 0, mesh_size}};
Point(3) = {{lx, ly, 0, mesh_size}};
Point(4) = {{0, ly, 0, mesh_size}};
Point(5) = {{0, 0, lz, mesh_size}};
Point(6) = {{lx, 0, lz, mesh_size}};
Point(7) = {{lx, ly, lz, mesh_size}};
Point(8) = {{0, ly, lz, mesh_size}};

Line(1) = {{1, 2}};
Line(2) = {{2, 3}};
Line(3) = {{3, 4}};
Line(4) = {{4, 1}};
Line(5) = {{5, 6}};
Line(6) = {{6, 7}};
Line(7) = {{7, 8}};
Line(8) = {{8, 5}};
Line(9) = {{1, 5}};
Line(10) = {{2, 6}};
Line(11) = {{3, 7}};
Line(12) = {{4, 8}};

Line Loop(1) = {{1, 2, 3, 4}};
Plane Surface(1) = {{1}};
Line Loop(2) = {{5, 6, 7, 8}};
Plane Surface(2) = {{2}};
Line Loop(3) = {{1, 10, -5, -9}};
Plane Surface(3) = {{3}};
Line Loop(4) = {{2, 11, -6, -10}};
Plane Surface(4) = {{4}};
Line Loop(5) = {{3, 12, -7, -11}};
Plane Surface(5) = {{5}};
Line Loop(6) = {{4, 9, -8, -12}};
Plane Surface(6) = {{6}};

Surface Loop(1) = {{1, 2, 3, 4, 5, 6}};
Volume(1) = {{1}};

// Define physical entities for boundary conditions
Physical Surface("inlet") = {{3}};
Physical Surface("outlet") = {{5}};
Physical Surface("walls") = {{1, 2, 4, 6}};
Physical Volume("fluid") = {{1}};

// Mesh options
Mesh.Algorithm = {options.get('algorithm', 6)};  // 6 = Frontal Delaunay
Mesh.CharacteristicLengthMin = {options.get('min_size', mesh_size/2)};
Mesh.CharacteristicLengthMax = {options.get('max_size', mesh_size*2)};
"""
            
            elif geometry_type == 'cylinder':
                # Get dimensions
                radius = dimensions.get('radius', 0.5)
                height = dimensions.get('height', 2.0)
                
                # Create cylinder geometry
                geo_content = f"""
// Cylinder geometry
radius = {radius};
height = {height};
mesh_size = {options.get('mesh_size', min(radius, height) / 5)};

Point(1) = {{0, 0, 0, mesh_size}};
Point(2) = {{radius, 0, 0, mesh_size}};
Point(3) = {{0, radius, 0, mesh_size}};
Point(4) = {{-radius, 0, 0, mesh_size}};
Point(5) = {{0, -radius, 0, mesh_size}};
Point(6) = {{0, 0, height, mesh_size}};
Point(7) = {{radius, 0, height, mesh_size}};
Point(8) = {{0, radius, height, mesh_size}};
Point(9) = {{-radius, 0, height, mesh_size}};
Point(10) = {{0, -radius, height, mesh_size}};

Circle(1) = {{2, 1, 3}};
Circle(2) = {{3, 1, 4}};
Circle(3) = {{4, 1, 5}};
Circle(4) = {{5, 1, 2}};
Circle(5) = {{7, 6, 8}};
Circle(6) = {{8, 6, 9}};
Circle(7) = {{9, 6, 10}};
Circle(8) = {{10, 6, 7}};
Line(9) = {{2, 7}};
Line(10) = {{3, 8}};
Line(11) = {{4, 9}};
Line(12) = {{5, 10}};

Line Loop(1) = {{1, 2, 3, 4}};
Plane Surface(1) = {{1}};
Line Loop(2) = {{5, 6, 7, 8}};
Plane Surface(2) = {{2}};
Line Loop(3) = {{1, 10, -5, -9}};
Ruled Surface(3) = {{3}};
Line Loop(4) = {{2, 11, -6, -10}};
Ruled Surface(4) = {{4}};
Line Loop(5) = {{3, 12, -7, -11}};
Ruled Surface(5) = {{5}};
Line Loop(6) = {{4, 9, -8, -12}};
Ruled Surface(6) = {{6}};

Surface Loop(1) = {{1, 2, 3, 4, 5, 6}};
Volume(1) = {{1}};

// Define physical entities for boundary conditions
Physical Surface("inlet") = {{1}};
Physical Surface("outlet") = {{2}};
Physical Surface("walls") = {{3, 4, 5, 6}};
Physical Volume("fluid") = {{1}};

// Mesh options
Mesh.Algorithm = {options.get('algorithm', 6)};
Mesh.CharacteristicLengthMin = {options.get('min_size', mesh_size/2)};
Mesh.CharacteristicLengthMax = {options.get('max_size', mesh_size*2)};
"""
                
            elif geometry_type == 'sphere':
                # Get dimensions
                radius = dimensions.get('radius', 1.0)
                
                # Create sphere geometry
                geo_content = f"""
// Sphere geometry
radius = {radius};
mesh_size = {options.get('mesh_size', radius / 5)};

Point(1) = {{0, 0, 0, mesh_size}};
Point(2) = {{radius, 0, 0, mesh_size}};
Point(3) = {{0, radius, 0, mesh_size}};
Point(4) = {{-radius, 0, 0, mesh_size}};
Point(5) = {{0, -radius, 0, mesh_size}};
Point(6) = {{0, 0, radius, mesh_size}};
Point(7) = {{0, 0, -radius, mesh_size}};

Circle(1) = {{2, 1, 3}};
Circle(2) = {{3, 1, 4}};
Circle(3) = {{4, 1, 5}};
Circle(4) = {{5, 1, 2}};
Circle(5) = {{2, 1, 6}};
Circle(6) = {{6, 1, 4}};
Circle(7) = {{4, 1, 7}};
Circle(8) = {{7, 1, 2}};
Circle(9) = {{3, 1, 6}};
Circle(10) = {{6, 1, 5}};
Circle(11) = {{5, 1, 7}};
Circle(12) = {{7, 1, 3}};

Line Loop(1) = {{1, 9, -5}};
Ruled Surface(1) = {{1}};
Line Loop(2) = {{2, 6, -9}};
Ruled Surface(2) = {{2}};
Line Loop(3) = {{3, 10, -6}};
Ruled Surface(3) = {{3}};
Line Loop(4) = {{4, 5, -10}};
Ruled Surface(4) = {{4}};
Line Loop(5) = {{1, 12, -8}};
Ruled Surface(5) = {{5}};
Line Loop(6) = {{2, 7, -12}};
Ruled Surface(6) = {{6}};
Line Loop(7) = {{3, 11, -7}};
Ruled Surface(7) = {{7}};
Line Loop(8) = {{4, 8, -11}};
Ruled Surface(8) = {{8}};

Surface Loop(1) = {{1, 2, 3, 4, 5, 6, 7, 8}};
Volume(1) = {{1}};

// Define physical entities for boundary conditions
Physical Surface("walls") = {{1, 2, 3, 4, 5, 6, 7, 8}};
Physical Volume("fluid") = {{1}};

// Mesh options
Mesh.Algorithm = {options.get('algorithm', 6)};
Mesh.CharacteristicLengthMin = {options.get('min_size', mesh_size/2)};
Mesh.CharacteristicLengthMax = {options.get('max_size', mesh_size*2)};
"""
            else:
                logger.error(f"Unsupported geometry type: {geometry_type}")
                return False
            
            # Write geo content to file
            geo_file.write(geo_content.encode())
        
        try:
            # Run gmsh to generate mesh
            cmd = [
                'gmsh', geo_path, '-3', '-format', 'msh2', 
                '-o', output_file, '-optimize'
            ]
            
            # Add other gmsh options
            for key, value in options.items():
                if key.startswith('gmsh_'):
                    cmd.extend([f'-{key[5:]}', str(value)])
            
            process = subprocess.run(
                cmd, capture_output=True, text=True, check=True
            )
            
            return os.path.exists(output_file)
            
        finally:
            # Clean up temporary file
            os.unlink(geo_path)
            
    except Exception as e:
        logger.error(f"Error creating simple geometry: {e}")
        return False

def extract_boundary_names(mesh_file: str) -> List[str]:
    """
    Extract boundary patch names from a mesh file.
    
    Args:
        mesh_file: Path to mesh file
    
    Returns:
        List of boundary patch names
    """
    mesh_info = MeshInfo(mesh_file)
    return list(mesh_info.boundaries.keys())