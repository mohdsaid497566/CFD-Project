"""
Utility functions and helper modules for the Intake CFD Optimization Suite.

This package contains various utility functions for file operations,
system commands, platform detection, and other helper functions.
"""

# Import key utilities to expose at the utils package level
from .workflow_utils import patch_workflow_gui

# Define what's available when importing *
__all__ = [
    'patch_workflow_gui'
]