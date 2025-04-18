"""
MDO (Multidisciplinary Design Optimization) module for the Intake CFD Optimization Suite.

This package provides capabilities for design optimization of intake systems using
surrogate models and various optimization algorithms.
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("MDO")

# Import submodules
from . import optimizer
from . import surrogate_model
from .workflow_gui import WorkflowGUI

# Export main classes for easier importing
from .optimizer import (
    OptimizationProblem,
    DesignVariable,
    Constraint,
    Optimizer,
    GradientDescentOptimizer,
    GeneticAlgorithm
)

from .surrogate_model import (
    SurrogateModel,
    PolynomialSurrogate,
    RadialBasisSurrogate
)

# Try to import optional classes that require external dependencies
try:
    from .surrogate_model import GaussianProcessSurrogate
    __all__ = [
        'OptimizationProblem', 'DesignVariable', 'Constraint', 'Optimizer',
        'GradientDescentOptimizer', 'GeneticAlgorithm',
        'SurrogateModel', 'PolynomialSurrogate', 'RadialBasisSurrogate',
        'GaussianProcessSurrogate', 'WorkflowGUI'
    ]
except ImportError:
    logger.warning("scikit-learn not available. GaussianProcessSurrogate will not be available.")
    __all__ = [
        'OptimizationProblem', 'DesignVariable', 'Constraint', 'Optimizer',
        'GradientDescentOptimizer', 'GeneticAlgorithm',
        'SurrogateModel', 'PolynomialSurrogate', 'RadialBasisSurrogate',
        'WorkflowGUI'
    ]