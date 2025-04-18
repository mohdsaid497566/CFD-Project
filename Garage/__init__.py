"""
Garage - Intake CFD Optimization Suite

This package provides a complete workflow for intake CFD design optimization:
- NX CAD model parametrization
- GMSH-based meshing
- CFD simulation with OpenFOAM
- Results visualization and analysis
- Design optimization with OpenMDAO

Main components:
- core: Core CFD processing functionality
- gui: Graphical user interface components
- utils: Helper utilities and tools
- config: Configuration management
- models: Data models and schema definitions
- meshing: Mesh generation and manipulation
- optimization: Optimization algorithms and components
- io: Input/output operations for various file formats
"""

__version__ = '1.0.0'
__author__ = 'Mohammed'

# Import key modules for easier access
from .Core import python_mesher
from . import MDO

# Set default demo mode from environment variable or default to True
import os
DEMO_MODE = os.environ.get("GARAGE_DEMO_MODE", "1").lower() in ("true", "1", "yes")

# Define what's available when importing *
__all__ = [
    'python_mesher',
    'DEMO_MODE'
]