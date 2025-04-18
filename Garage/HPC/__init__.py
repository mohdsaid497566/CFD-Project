"""
HPC module initialization for the Intake CFD Project.
"""

# This file marks the HPC directory as a Python package

# Import classes, functions, or submodules you want to expose
from .hpc_connector import HPCJobStatus, HPCJob, HPCConnector, test_connection
from .hpc_integration import (
    initialize_hpc,
    create_hpc_tab,
    toggle_auth_type,
    select_key_file,
    test_hpc_connection,
    update_connection_result,
    connect_to_hpc,
    disconnect_from_hpc,
    get_hpc_config,
)
from .hpc_config_dialog import HPCConfigDialog
from .fix_hpc_structure import (
    fix_hpc_structure,
    ensure_directory,
    ensure_init_file,
    check_import,
    ensure_file_exists,
)
