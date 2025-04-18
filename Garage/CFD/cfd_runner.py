"""
CFD Runner module for the Intake CFD Optimization Suite.

This module provides the functionality to set up, run, and post-process
CFD simulations for intake system analysis using various solvers.
"""

import os
import sys
import logging
import subprocess
import enum
import json
import time
import shutil
from typing import Dict, List, Tuple, Union, Optional, Any, Callable
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("cfd_runner")

class CFDSolverType(enum.Enum):
    """Enum for supported CFD solver types."""
    OPENFOAM = "openfoam"
    FLUENT = "fluent"
    SU2 = "su2"
    CUSTOM = "custom"
    
    def __str__(self):
        return self.value

class CFDAnalysisType(enum.Enum):
    """Enum for supported CFD analysis types."""
    STEADY = "steady"
    TRANSIENT = "transient"
    
    def __str__(self):
        return self.value

class CFDCaseStatus(enum.Enum):
    """Status of a CFD case for GUI tracking."""
    NOT_STARTED = "not_started"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    UNKNOWN = "unknown"

    def __str__(self):
        return self.value

class CFDCaseManager:
    """
    Manager for CFD cases, useful for GUI to track, list, and manage cases.
    """
    def __init__(self):
        self.cases = {}  # case_id -> dict with info

    def add_case(self, case_id: str, case_dir: str, status: CFDCaseStatus = CFDCaseStatus.NOT_STARTED):
        self.cases[case_id] = {
            "case_dir": case_dir,
            "status": status,
            "start_time": None,
            "end_time": None,
            "result": None,
        }

    def update_status(self, case_id: str, status: CFDCaseStatus):
        if case_id in self.cases:
            self.cases[case_id]["status"] = status
            if status == CFDCaseStatus.RUNNING:
                self.cases[case_id]["start_time"] = time.time()
            elif status in (CFDCaseStatus.COMPLETED, CFDCaseStatus.FAILED, CFDCaseStatus.CANCELLED):
                self.cases[case_id]["end_time"] = time.time()

    def set_result(self, case_id: str, result: dict):
        if case_id in self.cases:
            self.cases[case_id]["result"] = result

    def get_case_info(self, case_id: str):
        return self.cases.get(case_id, None)

    def list_cases(self):
        return list(self.cases.keys())

    def remove_case(self, case_id: str):
        if case_id in self.cases:
            del self.cases[case_id]

class CFDCaseHistory:
    """
    Tracks the history of CFD case runs, useful for GUI history panels.
    """
    def __init__(self):
        self.history = []  # List of dicts: {case_id, status, start_time, end_time, summary}

    def add_entry(self, case_id, status, start_time, end_time, summary=None):
        self.history.append({
            "case_id": case_id,
            "status": status,
            "start_time": start_time,
            "end_time": end_time,
            "summary": summary or {},
        })

    def get_last(self):
        return self.history[-1] if self.history else None

    def get_all(self):
        return self.history

    def filter_by_status(self, status):
        return [h for h in self.history if h["status"] == status]

def find_latest_case_dir(base_dir: str, prefix: str = "cfd_model_") -> str:
    """
    Find the most recently modified CFD case directory.
    """
    if not os.path.isdir(base_dir):
        return ""
    dirs = [d for d in os.listdir(base_dir) if d.startswith(prefix)]
    if not dirs:
        return ""
    dirs = sorted(dirs, key=lambda d: os.path.getmtime(os.path.join(base_dir, d)), reverse=True)
    return os.path.join(base_dir, dirs[0])

def validate_cfd_model(model: CFDModel) -> Tuple[bool, str]:
    """
    Validate a CFDModel instance for completeness before running.
    Returns (True, "") if valid, else (False, reason).
    """
    if not model.name:
        return False, "Model name is missing"
    if not model.mesh_file or not os.path.exists(model.mesh_file):
        return False, "Mesh file is missing or does not exist"
    if not model.boundary_conditions:
        return False, "No boundary conditions defined"
    return True, ""

def export_case_to_zip(case_dir: str, zip_path: str) -> bool:
    """
    Export a CFD case directory to a zip file for sharing or archiving.
    """
    import zipfile
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(case_dir):
                for file in files:
                    abs_path = os.path.join(root, file)
                    rel_path = os.path.relpath(abs_path, case_dir)
                    zipf.write(abs_path, rel_path)
        return True
    except Exception as e:
        logger.error(f"Failed to export case to zip: {e}")
        return False

def import_case_from_zip(zip_path: str, extract_dir: str) -> bool:
    """
    Import a CFD case from a zip file.
    """
    import zipfile
    try:
        with zipfile.ZipFile(zip_path, 'r') as zipf:
            zipf.extractall(extract_dir)
        return True
    except Exception as e:
        logger.error(f"Failed to import case from zip: {e}")
        return False

def list_available_solvers() -> List[str]:
    """
    List available CFD solvers on the system (for GUI dropdowns).
    """
    solvers = []
    for solver in ["simpleFoam", "pimpleFoam", "fluent", "SU2_CFD"]:
        if shutil.which(solver):
            solvers.append(solver)
    return solvers

def get_case_disk_usage(case_dir: str) -> int:
    """
    Get disk usage of a CFD case directory in bytes.
    """
    total = 0
    for dirpath, _, filenames in os.walk(case_dir):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.isfile(fp):
                total += os.path.getsize(fp)
    return total

def parse_openfoam_log(log_path: str) -> dict:
    """
    Parse an OpenFOAM log file for progress and errors (for GUI display).
    Returns a dict with keys: 'progress', 'errors', 'warnings', 'last_lines'.
    """
    result = {"progress": 0.0, "errors": [], "warnings": [], "last_lines": []}
    if not os.path.exists(log_path):
        return result
    try:
        with open(log_path, "r") as f:
            lines = f.readlines()
        result["last_lines"] = lines[-20:] if len(lines) > 20 else lines
        for line in lines:
            if "Time =" in line:
                try:
                    time_val = float(line.split("=")[-1].strip())
                    result["progress"] = max(result["progress"], time_val)
                except Exception:
                    pass
            if "FOAM FATAL ERROR" in line:
                result["errors"].append(line.strip())
            if "warning" in line.lower():
                result["warnings"].append(line.strip())
    except Exception as e:
        result["errors"].append(f"Failed to parse log: {e}")
    return result

def get_case_summary(case_dir: str) -> dict:
    """
    Summarize a CFD case for GUI display: status, last run, result files.
    """
    summary = {
        "case_dir": case_dir,
        "status": "UNKNOWN",
        "last_run": None,
        "result_files": [],
    }
    log_path = os.path.join(case_dir, "run.log")
    if os.path.exists(log_path):
        summary["last_run"] = datetime.fromtimestamp(os.path.getmtime(log_path)).isoformat()
        log_info = parse_openfoam_log(log_path)
        summary["status"] = "FAILED" if log_info["errors"] else "COMPLETED" if "End" in "".join(log_info["last_lines"]) else "RUNNING"
    # List result files (VTK, forceCoeffs, etc.)
    result_files = []
    for root, _, files in os.walk(case_dir):
        for fname in files:
            if fname.endswith((".vtk", ".dat", ".csv")):
                result_files.append(os.path.join(root, fname))
    summary["result_files"] = result_files
    return summary

class CFDModel:
    """
    Class representing a CFD model with its geometry, boundary conditions,
    and solver parameters.
    """
    def __init__(self, name: str, 
                mesh_file: str, 
                boundary_conditions: Dict[str, Dict[str, Any]],
                solver_settings: Dict[str, Any] = None,
                working_dir: Optional[str] = None):
        """
        Initialize a CFD model.
        
        Args:
            name: Name of the CFD model
            mesh_file: Path to the mesh file
            boundary_conditions: Dictionary of boundary conditions
            solver_settings: Dictionary of solver-specific settings
            working_dir: Working directory for the simulation
        """
        self.name = name
        self.mesh_file = mesh_file
        self.boundary_conditions = boundary_conditions
        self.solver_settings = solver_settings or {}
        
        # Set working directory
        if working_dir:
            self.working_dir = working_dir
        else:
            self.working_dir = os.path.join(os.getcwd(), f"cfd_model_{name}")
            
        # Create working directory if it doesn't exist
        os.makedirs(self.working_dir, exist_ok=True)
        
        # Results storage
        self.results = {}
        
    def add_boundary_condition(self, name: str, bc_type: str, values: Dict[str, Any]) -> None:
        """
        Add a boundary condition to the model.
        
        Args:
            name: Name of the boundary
            bc_type: Type of boundary condition (e.g., 'inlet', 'outlet', 'wall')
            values: Dictionary of values for the boundary condition
        """
        self.boundary_conditions[name] = {
            'type': bc_type,
            'values': values
        }
        
    def update_solver_settings(self, settings: Dict[str, Any]) -> None:
        """
        Update solver settings.
        
        Args:
            settings: Dictionary of solver settings to update
        """
        self.solver_settings.update(settings)
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert model to dictionary for serialization.
        
        Returns:
            Dictionary representation of the model
        """
        return {
            'name': self.name,
            'mesh_file': self.mesh_file,
            'boundary_conditions': self.boundary_conditions,
            'solver_settings': self.solver_settings,
            'working_dir': self.working_dir
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CFDModel':
        """
        Create a model from a dictionary.
        
        Args:
            data: Dictionary representation of the model
            
        Returns:
            CFDModel instance
        """
        model = cls(
            name=data['name'],
            mesh_file=data['mesh_file'],
            boundary_conditions=data['boundary_conditions'],
            solver_settings=data['solver_settings'],
            working_dir=data.get('working_dir')
        )
        return model
        
    def save_to_file(self, filepath: str) -> None:
        """
        Save model to a JSON file.
        
        Args:
            filepath: Path to save the model
        """
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=4)
            
        logger.info(f"Model saved to {filepath}")
        
    @classmethod
    def load_from_file(cls, filepath: str) -> 'CFDModel':
        """
        Load model from a JSON file.
        
        Args:
            filepath: Path to the model file
            
        Returns:
            CFDModel instance
        """
        with open(filepath, 'r') as f:
            data = json.load(f)
            
        model = cls.from_dict(data)
        logger.info(f"Model loaded from {filepath}")
        
        return model
        
    def __str__(self) -> str:
        """String representation of the model."""
        return f"CFDModel(name={self.name}, mesh_file={self.mesh_file})"

class CFDRunner:
    """
    Class for running CFD simulations using various solvers.
    """
    def __init__(self, solver_type: Union[CFDSolverType, str] = CFDSolverType.OPENFOAM,
                analysis_type: Union[CFDAnalysisType, str] = CFDAnalysisType.STEADY,
                num_processors: int = 1,
                solver_binary: Optional[str] = None,
                solver_env_setup: Optional[str] = None):
        """
        Initialize a CFD runner.
        
        Args:
            solver_type: Type of CFD solver to use
            analysis_type: Type of analysis (steady or transient)
            num_processors: Number of processors for parallel runs
            solver_binary: Path to the solver binary (if not in PATH)
            solver_env_setup: Optional script to set up the solver environment
        """
        # Convert string to enum if needed
        if isinstance(solver_type, str):
            self.solver_type = CFDSolverType(solver_type.lower())
        else:
            self.solver_type = solver_type
            
        # Convert string to enum if needed
        if isinstance(analysis_type, str):
            self.analysis_type = CFDAnalysisType(analysis_type.lower())
        else:
            self.analysis_type = analysis_type
            
        self.num_processors = num_processors
        self.solver_binary = solver_binary
        self.solver_env_setup = solver_env_setup
        
        # Track active simulations
        self.active_simulations = {}
        
        # Set solver-specific parameters
        self._set_solver_specific_parameters()
        
    def _set_solver_specific_parameters(self) -> None:
        """Set solver-specific parameters and commands."""
        if self.solver_type == CFDSolverType.OPENFOAM:
            # Set default OpenFOAM binary if not specified
            if not self.solver_binary:
                if self.analysis_type == CFDAnalysisType.STEADY:
                    self.solver_binary = "simpleFoam"
                else:
                    self.solver_binary = "pimpleFoam"
                    
            # Set environment setup script
            if not self.solver_env_setup:
                # Look for standard OpenFOAM environment setup scripts
                for setup_script in ["/opt/openfoam/etc/bashrc", "/usr/lib/openfoam/openfoam/etc/bashrc"]:
                    if os.path.exists(setup_script):
                        self.solver_env_setup = f"source {setup_script}"
                        break
                        
        elif self.solver_type == CFDSolverType.FLUENT:
            # Set default Fluent binary if not specified
            if not self.solver_binary:
                self.solver_binary = "fluent"
                
        elif self.solver_type == CFDSolverType.SU2:
            # Set default SU2 binary if not specified
            if not self.solver_binary:
                self.solver_binary = "SU2_CFD"
                
    def _create_case_directory(self, model: CFDModel, case_dir: Optional[str] = None) -> str:
        """
        Create a directory for the CFD case.
        
        Args:
            model: CFD model
            case_dir: Directory for the case (if None, use model's working_dir)
            
        Returns:
            Path to the case directory
        """
        # Use provided case directory or create one in the model's working directory
        if case_dir:
            case_path = case_dir
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            case_path = os.path.join(model.working_dir, f"{model.name}_{timestamp}")
            
        # Create the directory
        os.makedirs(case_path, exist_ok=True)
        
        logger.info(f"Created case directory: {case_path}")
        
        return case_path
        
    def _prepare_openfoam_case(self, model: CFDModel, case_dir: str) -> str:
        """
        Prepare an OpenFOAM case directory.
        
        Args:
            model: CFD model
            case_dir: Directory for the case
            
        Returns:
            Path to the prepared case
        """
        logger.info("Preparing OpenFOAM case")
        
        # Create standard OpenFOAM directory structure
        os.makedirs(os.path.join(case_dir, "0"), exist_ok=True)
        os.makedirs(os.path.join(case_dir, "constant"), exist_ok=True)
        os.makedirs(os.path.join(case_dir, "constant", "polyMesh"), exist_ok=True)
        os.makedirs(os.path.join(case_dir, "system"), exist_ok=True)
        
        # Check if we need to convert the mesh
        mesh_ext = os.path.splitext(model.mesh_file)[1].lower()
        if mesh_ext == ".msh":
            # Copy mesh file to case directory
            mesh_target = os.path.join(case_dir, "constant", "polyMesh", "mesh.msh")
            shutil.copy(model.mesh_file, mesh_target)
            
            # Create script to run gmshToFoam for mesh conversion
            with open(os.path.join(case_dir, "convert_mesh.sh"), "w") as f:
                f.write("#!/bin/bash\n")
                if self.solver_env_setup:
                    f.write(f"{self.solver_env_setup}\n")
                f.write(f"cd {case_dir}\n")
                f.write("gmshToFoam constant/polyMesh/mesh.msh\n")
                
            # Make script executable
            os.chmod(os.path.join(case_dir, "convert_mesh.sh"), 0o755)
            
            # Run mesh conversion
            subprocess.run(["/bin/bash", os.path.join(case_dir, "convert_mesh.sh")])
            logger.info("Converted GMSH mesh to OpenFOAM format")
            
        elif mesh_ext == ".unv":
            # Copy mesh file to case directory
            mesh_target = os.path.join(case_dir, "constant", "polyMesh", "mesh.unv")
            shutil.copy(model.mesh_file, mesh_target)
            
            # Create script to run ideasToFoam for mesh conversion
            with open(os.path.join(case_dir, "convert_mesh.sh"), "w") as f:
                f.write("#!/bin/bash\n")
                if self.solver_env_setup:
                    f.write(f"{self.solver_env_setup}\n")
                f.write(f"cd {case_dir}\n")
                f.write("ideasUnvToFoam constant/polyMesh/mesh.unv\n")
                
            # Make script executable
            os.chmod(os.path.join(case_dir, "convert_mesh.sh"), 0o755)
            
            # Run mesh conversion
            subprocess.run(["/bin/bash", os.path.join(case_dir, "convert_mesh.sh")])
            logger.info("Converted UNV mesh to OpenFOAM format")
            
        # Create default OpenFOAM case files
        self._create_openfoam_system_files(model, case_dir)
        self._create_openfoam_boundary_conditions(model, case_dir)
        
        # Create run script
        with open(os.path.join(case_dir, "Allrun"), "w") as f:
            f.write("#!/bin/bash\n")
            if self.solver_env_setup:
                f.write(f"{self.solver_env_setup}\n")
            f.write(f"cd {case_dir}\n")
            
            # Add pre-processing steps
            f.write("# Pre-processing\n")
            f.write("echo 'Running pre-processing...'\n")
            f.write("checkMesh\n\n")
            
            # Add solver command
            f.write("# Solving\n")
            f.write("echo 'Running solver...'\n")
            if self.num_processors > 1:
                f.write(f"decomposePar\n")
                f.write(f"mpirun -np {self.num_processors} {self.solver_binary} -parallel\n")
                f.write("reconstructPar\n")
            else:
                f.write(f"{self.solver_binary}\n")
                
            # Add post-processing steps
            f.write("\n# Post-processing\n")
            f.write("echo 'Running post-processing...'\n")
            f.write("foamToVTK\n")
            
        # Make script executable
        os.chmod(os.path.join(case_dir, "Allrun"), 0o755)
        
        return case_dir
        
    def _create_openfoam_system_files(self, model: CFDModel, case_dir: str) -> None:
        """
        Create OpenFOAM system directory files.
        
        Args:
            model: CFD model
            case_dir: Case directory
        """
        # Create controlDict
        steady = self.analysis_type == CFDAnalysisType.STEADY
        
        with open(os.path.join(case_dir, "system", "controlDict"), "w") as f:
            f.write(f"""/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\\\    /   O peration     | Version:  v2012                                 |
|   \\\\  /    A nd           | Website:  www.openfoam.com                      |
|    \\\\/     M anipulation  |                                                 |
\\*---------------------------------------------------------------------------*/
FoamFile
{{
    version     2.0;
    format      ascii;
    class       dictionary;
    location    "system";
    object      controlDict;
}}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

application     {self.solver_binary};

startFrom       startTime;

startTime       0;

stopAt          {"endTime" if steady else "nextWrite"};

endTime         {model.solver_settings.get('end_time', 1000)};

deltaT          {model.solver_settings.get('time_step', 1)};

writeControl    {"runTime" if steady else "adjustableRunTime"};

writeInterval   {model.solver_settings.get('write_interval', 100)};

purgeWrite      0;

writeFormat     ascii;

writePrecision  6;

writeCompression off;

timeFormat      general;

timePrecision   6;

runTimeModifiable true;

// Custom functions
functions
{{
    #includeFunc  residuals
    
    forceCoeffs
    {{
        type            forceCoeffs;
        libs            (forces);
        writeControl    timeStep;
        writeInterval   1;
        patches         (inlet-wall outlet-wall);
        rho             rhoInf;
        rhoInf          1.0;
        liftDir         (0 1 0);
        dragDir         (1 0 0);
        CofR            (0 0 0);
        pitchAxis       (0 0 1);
        magUInf         {model.solver_settings.get('velocity', 10)};
        lRef            {model.solver_settings.get('reference_length', 1)};
        Aref            {model.solver_settings.get('reference_area', 1)};
    }}
}}

// ************************************************************************* //
""")

        # Create fvSchemes
        with open(os.path.join(case_dir, "system", "fvSchemes"), "w") as f:
            f.write(f"""/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\\\    /   O peration     | Version:  v2012                                 |
|   \\\\  /    A nd           | Website:  www.openfoam.com                      |
|    \\\\/     M anipulation  |                                                 |
\\*---------------------------------------------------------------------------*/
FoamFile
{{
    version     2.0;
    format      ascii;
    class       dictionary;
    location    "system";
    object      fvSchemes;
}}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

ddtSchemes
{{
    default         {"steadyState" if steady else "Euler"};
}}

gradSchemes
{{
    default         Gauss linear;
}}

divSchemes
{{
    default         none;
    div(phi,U)      bounded Gauss limitedLinearV 1;
    div(phi,k)      bounded Gauss limitedLinear 1;
    div(phi,epsilon) bounded Gauss limitedLinear 1;
    div(phi,omega)  bounded Gauss limitedLinear 1;
    div(phi,nuTilda) bounded Gauss limitedLinear 1;
    div((nuEff*dev2(T(grad(U))))) Gauss linear;
}}

laplacianSchemes
{{
    default         Gauss linear corrected;
}}

interpolationSchemes
{{
    default         linear;
}}

snGradSchemes
{{
    default         corrected;
}}

wallDist
{{
    method meshWave;
}}

// ************************************************************************* //
""")

        # Create fvSolution
        with open(os.path.join(case_dir, "system", "fvSolution"), "w") as f:
            f.write(f"""/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\\\    /   O peration     | Version:  v2012                                 |
|   \\\\  /    A nd           | Website:  www.openfoam.com                      |
|    \\\\/     M anipulation  |                                                 |
\\*---------------------------------------------------------------------------*/
FoamFile
{{
    version     2.0;
    format      ascii;
    class       dictionary;
    location    "system";
    object      fvSolution;
}}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

solvers
{{
    p
    {{
        solver          GAMG;
        tolerance       1e-7;
        relTol          0.01;
        smoother        GaussSeidel;
    }}

    pFinal
    {{
        $p;
        smoother        DICGaussSeidel;
        tolerance       1e-7;
        relTol          0;
    }}

    "(U|k|epsilon|omega|nuTilda)"
    {{
        solver          smoothSolver;
        smoother        symGaussSeidel;
        tolerance       1e-8;
        relTol          0.1;
    }}
    
    "(U|k|epsilon|omega|nuTilda)Final"
    {{
        $U;
        tolerance       1e-8;
        relTol          0;
    }}
}}

{"SIMPLE" if steady else "PIMPLE"}
{{
    nNonOrthogonalCorrectors 0;
    
    residualControl
    {{
        p               1e-4;
        U               1e-4;
        "(k|epsilon|omega|nuTilda)" 1e-4;
    }}
}}

relaxationFactors
{{
    fields
    {{
        p               0.3;
    }}
    equations
    {{
        U               0.7;
        "(k|epsilon|omega|nuTilda)" 0.7;
    }}
}}

// ************************************************************************* //
""")

        # Create decomposeParDict if using parallel
        if self.num_processors > 1:
            with open(os.path.join(case_dir, "system", "decomposeParDict"), "w") as f:
                f.write(f"""/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\\\    /   O peration     | Version:  v2012                                 |
|   \\\\  /    A nd           | Website:  www.openfoam.com                      |
|    \\\\/     M anipulation  |                                                 |
\\*---------------------------------------------------------------------------*/
FoamFile
{{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      decomposeParDict;
}}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

numberOfSubdomains {self.num_processors};

method          scotch;

// ************************************************************************* //
""")

    def _create_openfoam_boundary_conditions(self, model: CFDModel, case_dir: str) -> None:
        """
        Create OpenFOAM boundary condition files in the 0 directory.
        
        Args:
            model: CFD model
            case_dir: Case directory
        """
        # Create U (velocity) file
        with open(os.path.join(case_dir, "0", "U"), "w") as f:
            f.write(f"""/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\\\    /   O peration     | Version:  v2012                                 |
|   \\\\  /    A nd           | Website:  www.openfoam.com                      |
|    \\\\/     M anipulation  |                                                 |
\\*---------------------------------------------------------------------------*/
FoamFile
{{
    version     2.0;
    format      ascii;
    class       volVectorField;
    location    "0";
    object      U;
}}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

dimensions      [0 1 -1 0 0 0 0];

internalField   uniform (0 0 0);

boundaryField
{{
""")
            
            # Add boundary conditions from model
            for name, bc in model.boundary_conditions.items():
                if bc['type'] == 'inlet':
                    velocity = bc['values'].get('velocity', (10, 0, 0))
                    if isinstance(velocity, (int, float)):
                        velocity = (velocity, 0, 0)
                    f.write(f"    {name}\n")
                    f.write(f"    {{\n")
                    f.write(f"        type            fixedValue;\n")
                    f.write(f"        value           uniform ({velocity[0]} {velocity[1]} {velocity[2]});\n")
                    f.write(f"    }}\n\n")
                elif bc['type'] == 'outlet':
                    f.write(f"    {name}\n")
                    f.write(f"    {{\n")
                    f.write(f"        type            zeroGradient;\n")
                    f.write(f"    }}\n\n")
                elif bc['type'] == 'wall':
                    f.write(f"    {name}\n")
                    f.write(f"    {{\n")
                    f.write(f"        type            noSlip;\n")
                    f.write(f"    }}\n\n")
                elif bc['type'] == 'symmetry':
                    f.write(f"    {name}\n")
                    f.write(f"    {{\n")
                    f.write(f"        type            symmetry;\n")
                    f.write(f"    }}\n\n")
                else:
                    f.write(f"    {name}\n")
                    f.write(f"    {{\n")
                    f.write(f"        type            zeroGradient;\n")
                    f.write(f"    }}\n\n")
                    
            f.write("}\n\n")
            f.write("// ************************************************************************* //\n")
            
        # Create p (pressure) file
        with open(os.path.join(case_dir, "0", "p"), "w") as f:
            f.write(f"""/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\\\    /   O peration     | Version:  v2012                                 |
|   \\\\  /    A nd           | Website:  www.openfoam.com                      |
|    \\\\/     M anipulation  |                                                 |
\\*---------------------------------------------------------------------------*/
FoamFile
{{
    version     2.0;
    format      ascii;
    class       volScalarField;
    location    "0";
    object      p;
}}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

dimensions      [0 2 -2 0 0 0 0];

internalField   uniform 0;

boundaryField
{{
""")
            
            # Add boundary conditions from model
            for name, bc in model.boundary_conditions.items():
                if bc['type'] == 'inlet':
                    f.write(f"    {name}\n")
                    f.write(f"    {{\n")
                    f.write(f"        type            zeroGradient;\n")
                    f.write(f"    }}\n\n")
                elif bc['type'] == 'outlet':
                    pressure = bc['values'].get('pressure', 0)
                    f.write(f"    {name}\n")
                    f.write(f"    {{\n")
                    f.write(f"        type            fixedValue;\n")
                    f.write(f"        value           uniform {pressure};\n")
                    f.write(f"    }}\n\n")
                elif bc['type'] == 'wall':
                    f.write(f"    {name}\n")
                    f.write(f"    {{\n")
                    f.write(f"        type            zeroGradient;\n")
                    f.write(f"    }}\n\n")
                elif bc['type'] == 'symmetry':
                    f.write(f"    {name}\n")
                    f.write(f"    {{\n")
                    f.write(f"        type            symmetry;\n")
                    f.write(f"    }}\n\n")
                else:
                    f.write(f"    {name}\n")
                    f.write(f"    {{\n")
                    f.write(f"        type            zeroGradient;\n")
                    f.write(f"    }}\n\n")
                    
            f.write("}\n\n")
            f.write("// ************************************************************************* //\n")
            
        # Create turbulence model files (k, epsilon, omega, etc.) if needed
        turbulence_model = model.solver_settings.get('turbulence_model', 'kEpsilon')
        
        if turbulence_model in ['kEpsilon', 'RAS']:
            # Create k file
            with open(os.path.join(case_dir, "0", "k"), "w") as f:
                f.write(f"""/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\\\    /   O peration     | Version:  v2012                                 |
|   \\\\  /    A nd           | Website:  www.openfoam.com                      |
|    \\\\/     M anipulation  |                                                 |
\\*---------------------------------------------------------------------------*/
FoamFile
{{
    version     2.0;
    format      ascii;
    class       volScalarField;
    location    "0";
    object      k;
}}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

dimensions      [0 2 -2 0 0 0 0];

internalField   uniform 0.1;

boundaryField
{{
""")
                
                # Add boundary conditions from model
                for name, bc in model.boundary_conditions.items():
                    if bc['type'] == 'inlet':
                        k_value = bc['values'].get('k', 0.1)
                        f.write(f"    {name}\n")
                        f.write(f"    {{\n")
                        f.write(f"        type            fixedValue;\n")
                        f.write(f"        value           uniform {k_value};\n")
                        f.write(f"    }}\n\n")
                    elif bc['type'] == 'outlet':
                        f.write(f"    {name}\n")
                        f.write(f"    {{\n")
                        f.write(f"        type            zeroGradient;\n")
                        f.write(f"    }}\n\n")
                    elif bc['type'] == 'wall':
                        f.write(f"    {name}\n")
                        f.write(f"    {{\n")
                        f.write(f"        type            kqRWallFunction;\n")
                        f.write(f"        value           uniform 0.1;\n")
                        f.write(f"    }}\n\n")
                    elif bc['type'] == 'symmetry':
                        f.write(f"    {name}\n")
                        f.write(f"    {{\n")
                        f.write(f"        type            symmetry;\n")
                        f.write(f"    }}\n\n")
                    else:
                        f.write(f"    {name}\n")
                        f.write(f"    {{\n")
                        f.write(f"        type            zeroGradient;\n")
                        f.write(f"    }}\n\n")
                        
                f.write("}\n\n")
                f.write("// ************************************************************************* //\n")
                
            # Create epsilon file
            with open(os.path.join(case_dir, "0", "epsilon"), "w") as f:
                f.write(f"""/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\\\    /   O peration     | Version:  v2012                                 |
|   \\\\  /    A nd           | Website:  www.openfoam.com                      |
|    \\\\/     M anipulation  |                                                 |
\\*---------------------------------------------------------------------------*/
FoamFile
{{
    version     2.0;
    format      ascii;
    class       volScalarField;
    location    "0";
    object      epsilon;
}}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

dimensions      [0 2 -3 0 0 0 0];

internalField   uniform 0.1;

boundaryField
{{
""")
                
                # Add boundary conditions from model
                for name, bc in model.boundary_conditions.items():
                    if bc['type'] == 'inlet':
                        eps_value = bc['values'].get('epsilon', 0.1)
                        f.write(f"    {name}\n")
                        f.write(f"    {{\n")
                        f.write(f"        type            fixedValue;\n")
                        f.write(f"        value           uniform {eps_value};\n")
                        f.write(f"    }}\n\n")
                    elif bc['type'] == 'outlet':
                        f.write(f"    {name}\n")
                        f.write(f"    {{\n")
                        f.write(f"        type            zeroGradient;\n")
                        f.write(f"    }}\n\n")
                    elif bc['type'] == 'wall':
                        f.write(f"    {name}\n")
                        f.write(f"    {{\n")
                        f.write(f"        type            epsilonWallFunction;\n")
                        f.write(f"        value           uniform 0.1;\n")
                        f.write(f"    }}\n\n")
                    elif bc['type'] == 'symmetry':
                        f.write(f"    {name}\n")
                        f.write(f"    {{\n")
                        f.write(f"        type            symmetry;\n")
                        f.write(f"    }}\n\n")
                    else:
                        f.write(f"    {name}\n")
                        f.write(f"    {{\n")
                        f.write(f"        type            zeroGradient;\n")
                        f.write(f"    }}\n\n")
                        
                f.write("}\n\n")
                f.write("// ************************************************************************* //\n")

        # Create turbulence properties file
        os.makedirs(os.path.join(case_dir, "constant"), exist_ok=True)
        with open(os.path.join(case_dir, "constant", "turbulenceProperties"), "w") as f:
            f.write(f"""/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\\\    /   O peration     | Version:  v2012                                 |
|   \\\\  /    A nd           | Website:  www.openfoam.com                      |
|    \\\\/     M anipulation  |                                                 |
\\*---------------------------------------------------------------------------*/
FoamFile
{{
    version     2.0;
    format      ascii;
    class       dictionary;
    location    "constant";
    object      turbulenceProperties;
}}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

simulationType  RAS;

RAS
{{
    RASModel        {model.solver_settings.get('turbulence_model', 'kEpsilon')};

    turbulence      on;

    printCoeffs     on;
}}

// ************************************************************************* //
""")

    def setup_case(self, model: CFDModel, case_dir: Optional[str] = None) -> str:
        """
        Set up a CFD case for the given model.
        
        Args:
            model: CFD model to simulate
            case_dir: Directory to set up the case (if None, create one)
            
        Returns:
            Path to the prepared case directory
        """
        # Create case directory
        case_dir = self._create_case_directory(model, case_dir)
        
        # Prepare case based on solver type
        if self.solver_type == CFDSolverType.OPENFOAM:
            return self._prepare_openfoam_case(model, case_dir)
        elif self.solver_type == CFDSolverType.FLUENT:
            # Not implemented yet
            raise NotImplementedError(f"Fluent setup not implemented yet")
        elif self.solver_type == CFDSolverType.SU2:
            # Not implemented yet
            raise NotImplementedError(f"SU2 setup not implemented yet")
        elif self.solver_type == CFDSolverType.CUSTOM:
            # User will provide their own setup
            return case_dir
        else:
            raise ValueError(f"Unknown solver type: {self.solver_type}")
            
    def run_case(self, case_dir: str, 
                background: bool = False, 
                timeout: Optional[int] = None) -> Union[Dict[str, Any], str]:
        """
        Run a prepared CFD case.
        
        Args:
            case_dir: Directory containing the prepared case
            background: Whether to run in the background
            timeout: Timeout in seconds (None for no timeout)
            
        Returns:
            If background is True, returns the job ID.
            Otherwise, returns a dictionary of results.
        """
        # Determine the run script
        if self.solver_type == CFDSolverType.OPENFOAM:
            run_script = os.path.join(case_dir, "Allrun")
        else:
            raise ValueError(f"Unknown solver type: {self.solver_type}")
            
        # Check if the run script exists
        if not os.path.exists(run_script):
            raise FileNotFoundError(f"Run script not found: {run_script}")
            
        # Run the case
        if background:
            # Generate a unique job ID
            job_id = f"cfd_{int(time.time())}_{os.path.basename(case_dir)}"
            
            # Create a log file
            log_file = os.path.join(case_dir, "run.log")
            
            # Run the command in the background
            command = f"cd {case_dir} && {run_script} > {log_file} 2>&1 &"
            subprocess.Popen(command, shell=True, executable="/bin/bash")
            
            # Track the active simulation
            self.active_simulations[job_id] = {
                'case_dir': case_dir,
                'log_file': log_file,
                'start_time': time.time()
            }
            
            logger.info(f"Started CFD simulation in background: {job_id}")
            
            return job_id
        else:
            # Run the command and wait for completion
            logger.info(f"Running CFD simulation in {case_dir}")
            
            try:
                result = subprocess.run(
                    run_script, 
                    shell=True, 
                    executable="/bin/bash",
                    check=True, 
                    timeout=timeout,
                    capture_output=True,
                    text=True
                )
                
                # Process the results
                return self._process_results(case_dir)
                
            except subprocess.CalledProcessError as e:
                logger.error(f"CFD simulation failed: {str(e)}")
                logger.error(f"Stderr: {e.stderr}")
                raise RuntimeError(f"CFD simulation failed: {str(e)}")
                
            except subprocess.TimeoutExpired:
                logger.error(f"CFD simulation timed out after {timeout} seconds")
                raise TimeoutError(f"CFD simulation timed out after {timeout} seconds")
                
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get the status of a background job.
        
        Args:
            job_id: Job ID returned by run_case
            
        Returns:
            Dictionary with job status information
        """
        if job_id not in self.active_simulations:
            raise ValueError(f"Unknown job ID: {job_id}")
            
        job_info = self.active_simulations[job_id]
        case_dir = job_info['case_dir']
        log_file = job_info['log_file']
        
        # Check if the log file exists
        if not os.path.exists(log_file):
            return {
                'job_id': job_id,
                'status': 'UNKNOWN',
                'message': 'Log file not found',
                'elapsed_time': time.time() - job_info['start_time']
            }
            
        # Check if the job is still running
        try:
            with open(log_file, 'r') as f:
                log_content = f.read()
                
            # Check for completion indicators
            if "FOAM FATAL ERROR" in log_content:
                status = 'FAILED'
                message = 'CFD simulation failed with error'
            elif "End" in log_content:
                status = 'COMPLETED'
                message = 'CFD simulation completed successfully'
            else:
                status = 'RUNNING'
                message = 'CFD simulation is still running'
                
            return {
                'job_id': job_id,
                'status': status,
                'message': message,
                'elapsed_time': time.time() - job_info['start_time'],
                'log_tail': log_content[-1000:] if len(log_content) > 1000 else log_content
            }
            
        except Exception as e:
            logger.error(f"Error checking job status: {str(e)}")
            return {
                'job_id': job_id,
                'status': 'ERROR',
                'message': f'Error checking job status: {str(e)}',
                'elapsed_time': time.time() - job_info['start_time']
            }
            
    def get_job_results(self, job_id: str) -> Dict[str, Any]:
        """
        Get the results of a completed background job.
        
        Args:
            job_id: Job ID returned by run_case
            
        Returns:
            Dictionary of results
        """
        if job_id not in self.active_simulations:
            raise ValueError(f"Unknown job ID: {job_id}")
            
        job_info = self.active_simulations[job_id]
        case_dir = job_info['case_dir']
        
        # Check job status first
        status = self.get_job_status(job_id)
        
        if status['status'] != 'COMPLETED':
            raise RuntimeError(f"Job is not completed: {status['status']} - {status['message']}")
            
        # Process the results
        results = self._process_results(case_dir)
        
        # Clean up the job
        del self.active_simulations[job_id]
        
        return results
        
    def _process_results(self, case_dir: str) -> Dict[str, Any]:
        """
        Process the results of a CFD simulation.
        
        Args:
            case_dir: Directory containing the results
            
        Returns:
            Dictionary of results
        """
        results = {
            'case_dir': case_dir,
            'success': True,
            'force_coefficients': {},
            'residuals': {},
            'fields': {}
        }
        
        if self.solver_type == CFDSolverType.OPENFOAM:
            # Look for force coefficients
            force_file = os.path.join(case_dir, 'postProcessing', 'forceCoeffs', '0', 'coefficient.dat')
            if os.path.exists(force_file):
                try:
                    # Read the last line for final values
                    with open(force_file, 'r') as f:
                        lines = f.readlines()
                        
                    if len(lines) > 1:
                        # Parse header
                        header = lines[0].strip().split()
                        
                        # Parse last line
                        values = lines[-1].strip().split()
                        
                        # Create dictionary of values
                        for i, key in enumerate(header):
                            if i < len(values):
                                try:
                                    results['force_coefficients'][key] = float(values[i])
                                except ValueError:
                                    results['force_coefficients'][key] = values[i]
                except Exception as e:
                    logger.error(f"Error parsing force coefficients: {str(e)}")
                    
            # Look for residuals
            residuals_file = os.path.join(case_dir, 'postProcessing', 'residuals', '0', 'residuals.dat')
            if os.path.exists(residuals_file):
                try:
                    # Read the file
                    with open(residuals_file, 'r') as f:
                        lines = f.readlines()
                        
                    if len(lines) > 1:
                        # Parse header
                        header = lines[0].strip().split()
                        
                        # Parse final residuals
                        final_values = lines[-1].strip().split()
                        
                        # Create dictionary of residuals
                        for i, key in enumerate(header):
                            if i < len(final_values):
                                try:
                                    results['residuals'][key] = float(final_values[i])
                                except ValueError:
                                    results['residuals'][key] = final_values[i]
                except Exception as e:
                    logger.error(f"Error parsing residuals: {str(e)}")
                    
            # Check for solution fields
            last_time_dir = None
            for d in sorted([d for d in os.listdir(case_dir) if d.replace('.', '', 1).isdigit()], reverse=True):
                if os.path.isdir(os.path.join(case_dir, d)):
                    last_time_dir = d
                    break
                    
            if last_time_dir:
                # Look for field files
                for field_file in ['U', 'p', 'k', 'epsilon']:
                    field_path = os.path.join(case_dir, last_time_dir, field_file)
                    if os.path.exists(field_path):
                        results['fields'][field_file] = {
                            'path': field_path,
                            'time': last_time_dir
                        }
                        
            # Look for VTK files (for visualization)
            vtk_dir = os.path.join(case_dir, 'VTK')
            if os.path.exists(vtk_dir):
                results['vtk_dir'] = vtk_dir
                
        return results
        
    def cleanup_case(self, case_dir: str, remove_large_files: bool = False) -> None:
        """
        Clean up a CFD case directory to save disk space.
        
        Args:
            case_dir: Directory to clean up
            remove_large_files: Whether to remove large result files
        """
        if not os.path.isdir(case_dir):
            logger.warning(f"Case directory not found: {case_dir}")
            return
            
        if self.solver_type == CFDSolverType.OPENFOAM:
            # Remove processor directories
            for d in os.listdir(case_dir):
                if d.startswith('processor') and os.path.isdir(os.path.join(case_dir, d)):
                    shutil.rmtree(os.path.join(case_dir, d))
                    
            # Remove time directories if requested
            if remove_large_files:
                for d in os.listdir(case_dir):
                    if d.replace('.', '', 1).isdigit() and os.path.isdir(os.path.join(case_dir, d)):
                        # Keep the last time directory
                        if d != 'constant' and d != 'system' and d != '0':
                            shutil.rmtree(os.path.join(case_dir, d))
                            
            logger.info(f"Cleaned up case directory: {case_dir}")
            
# Example usage if this module is run directly
if __name__ == "__main__":
    # Create a simple CFD model
    model = CFDModel(
        name="simple_channel",
        mesh_file="/path/to/channel.msh",
        boundary_conditions={
            "inlet": {
                "type": "inlet",
                "values": {"velocity": 10.0}
            },
            "outlet": {
                "type": "outlet",
                "values": {"pressure": 0.0}
            },
            "walls": {
                "type": "wall",
                "values": {}
            }
        },
        solver_settings={
            "turbulence_model": "kEpsilon",
            "end_time": 500,
            "write_interval": 100
        }
    )
    
    # Create a CFD runner for OpenFOAM
    runner = CFDRunner(
        solver_type=CFDSolverType.OPENFOAM,
        analysis_type=CFDAnalysisType.STEADY,
        num_processors=4
    )
    
    # Set up the case (no actual execution since mesh file doesn't exist)
    try:
        case_dir = runner.setup_case(model)
        print(f"Case set up in: {case_dir}")
    except FileNotFoundError:
        print("Skipping case setup due to missing mesh file")