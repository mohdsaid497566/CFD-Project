"""
GUI components for the Intake CFD Optimization Suite.

This package contains the graphical user interface components for the
Intake CFD Optimization Suite, including visualization, parameter settings,
and workflow control.
"""

# Import key components for easier access
from .gui_helper import setup_theme, create_header
from .display_utils import visualize_geometry, visualize_mesh, visualize_results

# Define what's available when importing *
__all__ = [
    'setup_theme',
    'create_header',
    'visualize_geometry',
    'visualize_mesh',
    'visualize_results'
]