"""
Core functionality for the Intake CFD Optimization Suite.

This package contains the core computational modules for CFD processing,
including mesh generation, CFD simulation, and results processing.
"""

# Import key modules for easier access
from .python_mesher import process_mesh, validate_mesh

# Define what's available when importing *
__all__ = [
    'process_mesh',
    'validate_mesh'
]