"""
CFD (Computational Fluid Dynamics) module for the Intake CFD Optimization Suite.

This package provides capabilities for setting up, running, and post-processing
CFD simulations for intake system analysis.
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("CFD")

# Import submodules
from . import cfd_runner
from . import cfd_visualizer
from . import cfd_batch
from . import mesh_tools
from . import cfd_gui_helpers

# Export main classes and functions for easier importing
from .cfd_runner import (
    CFDRunner,
    CFDSolverType,
    CFDAnalysisType,
    CFDModel,
    CFDCaseStatus,
    CFDCaseManager,
    CFDCaseHistory,
    parse_openfoam_log,
    get_case_summary,
    find_latest_case_dir,
    validate_cfd_model,
    export_case_to_zip,
    import_case_from_zip,
    list_available_solvers,
    get_case_disk_usage,
)

from .cfd_visualizer import (
    CFDVisualizer,
    launch_paraview,
    extract_visualization_data,
)

from .cfd_batch import (
    CFDParametricStudy,
    CFDBatchRunner,
    create_structured_parameter_study,
)

from .mesh_tools import (
    MeshInfo,
    convert_mesh,
    check_mesh_quality,
    create_simple_geometry,
    extract_boundary_names,
)

from .cfd_gui_helpers import (
    CFDBackgroundTask,
    CFDSimulationController,
)

__all__ = [
    # cfd_runner
    'CFDRunner',
    'CFDSolverType',
    'CFDAnalysisType',
    'CFDModel',
    'CFDCaseStatus',
    'CFDCaseManager',
    'CFDCaseHistory',
    'parse_openfoam_log',
    'get_case_summary',
    'find_latest_case_dir',
    'validate_cfd_model',
    'export_case_to_zip',
    'import_case_from_zip',
    'list_available_solvers',
    'get_case_disk_usage',
    
    # cfd_visualizer
    'CFDVisualizer',
    'launch_paraview',
    'extract_visualization_data',
    
    # cfd_batch
    'CFDParametricStudy',
    'CFDBatchRunner',
    'create_structured_parameter_study',
    
    # mesh_tools
    'MeshInfo',
    'convert_mesh',
    'check_mesh_quality',
    'create_simple_geometry',
    'extract_boundary_names',
    
    # cfd_gui_helpers
    'CFDBackgroundTask',
    'CFDSimulationController',
]