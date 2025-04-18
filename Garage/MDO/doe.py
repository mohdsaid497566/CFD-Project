"""
Design of Experiments (DOE) module for MDO package.

This module provides capabilities for creating and analyzing design of experiments,
which are crucial for sensitivity analysis and surrogate model building.
"""

import numpy as np
import matplotlib.pyplot as plt
import logging
import os
from typing import Dict, List, Tuple, Union, Optional, Any, Callable
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("doe")

class DesignOfExperiments:
    """
    Class for generating and analyzing design of experiments.
    """
    def __init__(self, problem, doe_type: str = "latin_hypercube", seed: Optional[int] = None):
        """
        Initialize the DOE object.
        
        Args:
            problem: Optimization problem defining the design space
            doe_type: Type of DOE (latin_hypercube, full_factorial, random, etc.)
            seed: Random seed for reproducibility
        """
        self.problem = problem
        self.doe_type = doe_type.lower()
        
        # Set random seed if provided
        if seed is not None:
            np.random.seed(seed)
        
        # Supported DOE types
        self.supported_doe_types = [
            "latin_hypercube", 
            "full_factorial", 
            "random", 
            "central_composite", 
            "box_behnken",
            "halton",
            "sobol"
        ]
        
        if self.doe_type not in self.supported_doe_types:
            raise ValueError(f"Unsupported DOE type: {self.doe_type}. "
                           f"Supported types: {', '.join(self.supported_doe_types)}")
        
        # Cache for generated samples
        self.samples = None
        self.results = None
        
    def generate_samples(self, n_samples: int) -> np.ndarray:
        """
        Generate DOE samples.
        
        Args:
            n_samples: Number of samples to generate
            
        Returns:
            Array of sample points in design space
        """
        # Get problem dimensions
        n_vars = len(self.problem.design_variables)
        
        # Check for full factorial special case
        if self.doe_type == "full_factorial":
            # Calculate points per dimension
            points_per_dim = max(2, int(np.power(n_samples, 1.0 / n_vars)))
            logger.info(f"Using {points_per_dim} points per dimension for full factorial design")
            
            # Generate full factorial design
            self.samples = self._generate_full_factorial(points_per_dim)
        elif self.doe_type == "central_composite":
            self.samples = self._generate_central_composite()
        elif self.doe_type == "box_behnken":
            self.samples = self._generate_box_behnken()
        elif self.doe_type == "halton":
            self.samples = self._generate_halton_sequence(n_samples)
        elif self.doe_type == "sobol":
            self.samples = self._generate_sobol_sequence(n_samples)
        elif self.doe_type == "latin_hypercube":
            self.samples = self._generate_latin_hypercube(n_samples)
        elif self.doe_type == "random":
            self.samples = self._generate_random(n_samples)
        else:
            # This should never happen due to earlier check
            raise ValueError(f"Unsupported DOE type: {self.doe_type}")
        
        logger.info(f"Generated {len(self.samples)} samples using {self.doe_type} design")
        return self.samples
    
    def _generate_latin_hypercube(self, n_samples: int) -> np.ndarray:
        """
        Generate Latin Hypercube samples.
        
        Args:
            n_samples: Number of samples
            
        Returns:
            Array of sample points
        """
        n_vars = len(self.problem.design_variables)
        lb, ub = self.problem.get_bounds()
        
        # Generate Latin Hypercube samples in [0, 1]
        cut = np.linspace(0, 1, n_samples + 1)
        u = np.random.rand(n_samples, n_vars)
        
        a = cut[0:-1]
        b = cut[1::]
        
        # Scale samples to [0, 1]^n_vars
        rdpoints = np.zeros_like(u)
        for j in range(n_vars):
            rdpoints[:, j] = u[:, j] * (b - a) + a
        
        # Shuffle each column to get Latin Hypercube property
        for j in range(n_vars):
            np.random.shuffle(rdpoints[:, j])
        
        # Scale to actual bounds
        scaled_points = lb + rdpoints * (ub - lb)
        
        return scaled_points
    
    def _generate_random(self, n_samples: int) -> np.ndarray:
        """
        Generate random samples.
        
        Args:
            n_samples: Number of samples
            
        Returns:
            Array of sample points
        """
        n_vars = len(self.problem.design_variables)
        lb, ub = self.problem.get_bounds()
        
        # Generate random samples in [0, 1]^n_vars
        u = np.random.rand(n_samples, n_vars)
        
        # Scale to actual bounds
        scaled_points = lb + u * (ub - lb)
        
        return scaled_points
    
    def _generate_full_factorial(self, points_per_dim: int) -> np.ndarray:
        """
        Generate full factorial design.
        
        Args:
            points_per_dim: Number of points per dimension
            
        Returns:
            Array of sample points
        """
        n_vars = len(self.problem.design_variables)
        lb, ub = self.problem.get_bounds()
        
        # Create grid points for each dimension
        grids = []
        for i in range(n_vars):
            grids.append(np.linspace(lb[i], ub[i], points_per_dim))
        
        # Create meshgrid
        mesh = np.meshgrid(*grids)
        
        # Reshape to get design matrix
        design_matrix = np.column_stack([x.flatten() for x in mesh])
        
        return design_matrix
    
    def _generate_central_composite(self) -> np.ndarray:
        """
        Generate Central Composite Design (CCD).
        
        Returns:
            Array of sample points
        """
        n_vars = len(self.problem.design_variables)
        lb, ub = self.problem.get_bounds()
        
        # Center point
        center = (lb + ub) / 2
        
        # Factorial points (2^n)
        factorial_points = []
        for i in range(2**n_vars):
            point = np.zeros(n_vars)
            for j in range(n_vars):
                # Convert i to binary and use as factorial design
                if (i >> j) & 1:
                    point[j] = ub[j]
                else:
                    point[j] = lb[j]
            factorial_points.append(point)
        
        # Axial points (2*n)
        axial_points = []
        alpha = 1.0  # Can be modified based on design requirements
        
        for i in range(n_vars):
            # Low axial point
            point_low = center.copy()
            point_low[i] = max(lb[i], center[i] - alpha * (center[i] - lb[i]))
            axial_points.append(point_low)
            
            # High axial point
            point_high = center.copy()
            point_high[i] = min(ub[i], center[i] + alpha * (ub[i] - center[i]))
            axial_points.append(point_high)
        
        # Combine all points
        all_points = [center]  # Start with center point
        all_points.extend(factorial_points)
        all_points.extend(axial_points)
        
        return np.array(all_points)
    
    def _generate_box_behnken(self) -> np.ndarray:
        """
        Generate Box-Behnken Design.
        
        Returns:
            Array of sample points
        """
        n_vars = len(self.problem.design_variables)
        
        if n_vars < 3:
            raise ValueError("Box-Behnken design requires at least 3 variables")
        
        lb, ub = self.problem.get_bounds()
        
        # Center point
        center = (lb + ub) / 2
        
        # Box-Behnken design points
        design_points = []
        
        # Center point (repeated for better properties)
        for _ in range(1):
            design_points.append(center.copy())
        
        # Box-Behnken exploration points
        for i in range(n_vars):
            for j in range(i+1, n_vars):
                # Create 2^2 factorial design for variables i and j
                for a in [-1, 1]:
                    for b in [-1, 1]:
                        point = center.copy()
                        point[i] = center[i] + a * (ub[i] - center[i])
                        point[j] = center[j] + b * (ub[j] - center[j])
                        design_points.append(point)
        
        return np.array(design_points)
    
    def _generate_halton_sequence(self, n_samples: int) -> np.ndarray:
        """
        Generate Halton sequence for quasi-random sampling.
        
        Args:
            n_samples: Number of samples
            
        Returns:
            Array of sample points
        """
        n_vars = len(self.problem.design_variables)
        lb, ub = self.problem.get_bounds()
        
        # First n_vars prime numbers for Halton sequence
        primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71]
        
        if n_vars > len(primes):
            raise ValueError(f"Halton sequence limited to {len(primes)} dimensions")
        
        # Generate Halton sequence
        samples = np.zeros((n_samples, n_vars))
        
        for i in range(n_vars):
            base = primes[i]
            samples[:, i] = self._halton_sequence(n_samples, base)
        
        # Scale to bounds
        scaled_points = lb + samples * (ub - lb)
        
        return scaled_points
    
    def _halton_sequence(self, n_samples: int, base: int) -> np.ndarray:
        """
        Generate one-dimensional Halton sequence.
        
        Args:
            n_samples: Number of samples
            base: Prime base for the sequence
            
        Returns:
            One-dimensional Halton sequence
        """
        sequence = np.zeros(n_samples)
        
        for i in range(n_samples):
            n = i + 1
            f = 1
            r = 0
            
            while n > 0:
                f = f / base
                r = r + f * (n % base)
                n = int(n / base)
            
            sequence[i] = r
        
        return sequence
    
    def _generate_sobol_sequence(self, n_samples: int) -> np.ndarray:
        """
        Generate Sobol sequence for quasi-random sampling.
        
        Args:
            n_samples: Number of samples
            
        Returns:
            Array of sample points
        """
        try:
            from scipy.stats import qmc
            
            n_vars = len(self.problem.design_variables)
            lb, ub = self.problem.get_bounds()
            
            # Initialize Sobol sequence generator
            sampler = qmc.Sobol(d=n_vars, scramble=True)
            
            # Generate samples
            samples = sampler.random(n=n_samples)
            
            # Scale to bounds
            scaled_points = qmc.scale(samples, lb, ub)
            
            return scaled_points
            
        except ImportError:
            logger.warning("scipy.stats.qmc not available. Falling back to Latin Hypercube sampling.")
            return self._generate_latin_hypercube(n_samples)
    
    def evaluate(self, parallel: bool = False, n_jobs: int = -1) -> List[Dict]:
        """
        Evaluate all samples using the problem's objective and constraint functions.
        
        Args:
            parallel: Whether to use parallel processing
            n_jobs: Number of parallel jobs (-1 for all available cores)
            
        Returns:
            List of dictionaries with evaluation results
        """
        if self.samples is None:
            raise ValueError("No samples generated. Call generate_samples first.")
        
        n_samples = len(self.samples)
        
        try:
            if parallel:
                # Try to use joblib for parallel processing
                from joblib import Parallel, delayed
                import multiprocessing
                
                if n_jobs == -1:
                    n_jobs = multiprocessing.cpu_count()
                
                logger.info(f"Evaluating {n_samples} samples in parallel using {n_jobs} cores")
                
                self.results = Parallel(n_jobs=n_jobs)(
                    delayed(self.problem.evaluate)(self.samples[i]) 
                    for i in range(n_samples)
                )
            else:
                raise ImportError("Fallback to sequential processing")
                
        except ImportError:
            # Fallback to sequential processing
            logger.info(f"Evaluating {n_samples} samples sequentially")
            
            self.results = []
            for i, sample in enumerate(self.samples):
                if i % 10 == 0:
                    logger.info(f"Progress: {i}/{n_samples}")
                
                result = self.problem.evaluate(sample)
                self.results.append(result)
        
        logger.info(f"Completed evaluation of {n_samples} samples")
        return self.results
    
    def analyze(self, output_dir: Optional[str] = None, 
               show_plots: bool = True) -> Dict[str, Any]:
        """
        Analyze DOE results and generate visualizations.
        
        Args:
            output_dir: Directory to save analysis results and plots
            show_plots: Whether to display plots
            
        Returns:
            Dictionary with analysis results
        """
        if self.samples is None or self.results is None:
            raise ValueError("Samples or results not available. Call generate_samples and evaluate first.")
        
        # Create output directory if specified
        if output_dir is not None:
            os.makedirs(output_dir, exist_ok=True)
        
        n_samples = len(self.samples)
        n_vars = len(self.problem.design_variables)
        
        # Get variable and objective names
        var_names = list(self.problem.design_variables.keys())
        obj_names = list(self.problem.objectives.keys())
        
        # Extract data for analysis
        X = self.samples
        Y = {}
        
        for obj_name in obj_names:
            Y[obj_name] = np.array([result[f"obj_{obj_name}"] for result in self.results])
        
        # Basic statistical analysis
        statistics = {}
        for obj_name in obj_names:
            y = Y[obj_name]
            statistics[obj_name] = {
                'min': float(np.min(y)),
                'max': float(np.max(y)),
                'mean': float(np.mean(y)),
                'std': float(np.std(y)),
                'q25': float(np.percentile(y, 25)),
                'median': float(np.percentile(y, 50)),
                'q75': float(np.percentile(y, 75))
            }
        
        # Correlation analysis
        correlations = {}
        for obj_name in obj_names:
            y = Y[obj_name]
            var_correlations = {}
            
            for i, var_name in enumerate(var_names):
                x = X[:, i]
                corr = float(np.corrcoef(x, y)[0, 1])
                var_correlations[var_name] = corr
            
            correlations[obj_name] = var_correlations
        
        # Save results if output directory is specified
        if output_dir is not None:
            import json
            
            analysis_results = {
                'doe_type': self.doe_type,
                'n_samples': n_samples,
                'n_variables': n_vars,
                'variable_names': var_names,
                'objective_names': obj_names,
                'statistics': statistics,
                'correlations': correlations
            }
            
            with open(os.path.join(output_dir, 'doe_analysis.json'), 'w') as f:
                json.dump(analysis_results, f, indent=4)
        
        # Generate visualizations
        if output_dir is not None or show_plots:
            self._generate_visualizations(var_names, obj_names, X, Y, 
                                         output_dir=output_dir, 
                                         show_plots=show_plots)
        
        # Return analysis results
        return {
            'statistics': statistics,
            'correlations': correlations
        }
    
    def _generate_visualizations(self, var_names, obj_names, X, Y, 
                               output_dir=None, show_plots=True):
        """
        Generate visualizations of DOE results.
        
        Args:
            var_names: List of variable names
            obj_names: List of objective names
            X: Sample points
            Y: Objective values
            output_dir: Directory to save plots
            show_plots: Whether to display plots
        """
        n_vars = len(var_names)
        
        # Plot sampling points
        if n_vars >= 2:
            plt.figure(figsize=(10, 8))
            
            # Create scatter matrix of sampling points
            n_plots = min(4, n_vars)  # Limit to first 4 variables for clarity
            
            for i in range(n_plots):
                for j in range(n_plots):
                    if i != j:
                        plt.subplot(n_plots, n_plots, i * n_plots + j + 1)
                        plt.scatter(X[:, j], X[:, i], alpha=0.7, s=30)
                        plt.xlabel(var_names[j])
                        plt.ylabel(var_names[i])
            
            plt.tight_layout()
            
            if output_dir is not None:
                plt.savefig(os.path.join(output_dir, 'doe_sampling_points.png'), dpi=300)
            
            if show_plots:
                plt.show()
            else:
                plt.close()
        
        # Plot correlation heatmap
        for obj_name in obj_names:
            y = Y[obj_name]
            
            # Calculate correlations with variables
            correlations = np.zeros(n_vars)
            for i in range(n_vars):
                correlations[i] = np.corrcoef(X[:, i], y)[0, 1]
            
            # Sort by absolute correlation
            sorted_indices = np.argsort(np.abs(correlations))[::-1]
            sorted_var_names = [var_names[i] for i in sorted_indices]
            sorted_correlations = correlations[sorted_indices]
            
            # Plot correlations
            plt.figure(figsize=(12, 6))
            colors = ['r' if c < 0 else 'b' for c in sorted_correlations]
            plt.bar(range(n_vars), sorted_correlations, color=colors)
            plt.axhline(y=0, color='k', linestyle='-', alpha=0.3)
            plt.xticks(range(n_vars), sorted_var_names, rotation=90)
            plt.ylabel('Correlation Coefficient')
            plt.title(f'Variable Correlations with {obj_name}')
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            
            if output_dir is not None:
                plt.savefig(os.path.join(output_dir, f'correlation_{obj_name}.png'), dpi=300)
            
            if show_plots:
                plt.show()
            else:
                plt.close()
        
        # Plot response surfaces for top correlations
        for obj_name in obj_names:
            y = Y[obj_name]
            
            # Calculate correlations with variables
            correlations = np.zeros(n_vars)
            for i in range(n_vars):
                correlations[i] = np.corrcoef(X[:, i], y)[0, 1]
            
            # Get indices of top 2 variables by absolute correlation
            top_indices = np.argsort(np.abs(correlations))[-2:]
            
            if len(top_indices) >= 2:
                # Plot response surface
                x1_idx, x2_idx = top_indices[1], top_indices[0]
                x1, x2 = X[:, x1_idx], X[:, x2_idx]
                
                plt.figure(figsize=(10, 8))
                
                # 3D surface plot
                from mpl_toolkits.mplot3d import Axes3D
                
                ax = plt.subplot(111, projection='3d')
                ax.scatter(x1, x2, y, c=y, cmap='viridis', s=50, alpha=0.7)
                ax.set_xlabel(var_names[x1_idx])
                ax.set_ylabel(var_names[x2_idx])
                ax.set_zlabel(obj_name)
                ax.set_title(f'Response Surface: {obj_name} vs. {var_names[x1_idx]} and {var_names[x2_idx]}')
                
                if output_dir is not None:
                    plt.savefig(os.path.join(output_dir, f'response_surface_{obj_name}.png'), dpi=300)
                
                if show_plots:
                    plt.show()
                else:
                    plt.close()
    
    def get_best_point(self, objective_name: Optional[str] = None, minimize: bool = True) -> Tuple[np.ndarray, float]:
        """
        Get the best point from the DOE based on a specific objective.
        
        Args:
            objective_name: Name of the objective to use (if None, uses first objective)
            minimize: Whether to minimize (True) or maximize (False) the objective
            
        Returns:
            Tuple of (best_point, best_value)
        """
        if self.samples is None or self.results is None:
            raise ValueError("Samples or results not available. Call generate_samples and evaluate first.")
        
        # Get objective name
        if objective_name is None:
            objective_name = list(self.problem.objectives.keys())[0]
        else:
            if objective_name not in self.problem.objectives:
                raise ValueError(f"Objective '{objective_name}' not found in problem definition")
        
        # Extract objective values
        obj_values = np.array([result[f"obj_{objective_name}"] for result in self.results])
        
        # Find best index
        if minimize:
            best_idx = np.argmin(obj_values)
        else:
            best_idx = np.argmax(obj_values)
        
        # Get best point and value
        best_point = self.samples[best_idx]
        best_value = obj_values[best_idx]
        
        return best_point, best_value
    
    def get_pareto_points(self, objective_names: Optional[List[str]] = None) -> List[Tuple[np.ndarray, Dict[str, float]]]:
        """
        Get Pareto-optimal points from DOE samples.
        
        Args:
            objective_names: List of objective names to consider (if None, uses all objectives)
            
        Returns:
            List of tuples (point, objective_values) for Pareto-optimal points
        """
        if self.samples is None or self.results is None:
            raise ValueError("Samples or results not available. Call generate_samples and evaluate first.")
        
        # Get objective names
        if objective_names is None:
            objective_names = list(self.problem.objectives.keys())
        else:
            for name in objective_names:
                if name not in self.problem.objectives:
                    raise ValueError(f"Objective '{name}' not found in problem definition")
        
        # Need at least 2 objectives for Pareto analysis
        if len(objective_names) < 2:
            logger.warning("At least 2 objectives needed for Pareto analysis. Returning best point.")
            best_point, best_value = self.get_best_point(objective_names[0])
            
            objective_values = {objective_names[0]: best_value}
            return [(best_point, objective_values)]
        
        # Extract objective values
        objective_values = np.zeros((len(self.samples), len(objective_names)))
        
        for j, name in enumerate(objective_names):
            objective_values[:, j] = [result[f"obj_{name}"] for result in self.results]
        
        # Find Pareto-optimal points
        pareto_indices = []
        
        for i in range(len(self.samples)):
            dominated = False
            
            for j in range(len(self.samples)):
                if i != j:
                    if np.all(objective_values[j] <= objective_values[i]) and np.any(objective_values[j] < objective_values[i]):
                        dominated = True
                        break
            
            if not dominated:
                pareto_indices.append(i)
        
        # Collect Pareto-optimal points
        pareto_points = []
        
        for idx in pareto_indices:
            point = self.samples[idx]
            values = {name: float(objective_values[idx, j]) for j, name in enumerate(objective_names)}
            pareto_points.append((point, values))
        
        return pareto_points
    
    def plot_pareto_front(self, objective_names: Optional[List[str]] = None,
                         output_dir: Optional[str] = None,
                         show_plot: bool = True) -> None:
        """
        Plot the Pareto front from DOE samples.
        
        Args:
            objective_names: List of objective names to consider (if None, uses first 2 objectives)
            output_dir: Directory to save plot (if None, don't save)
            show_plot: Whether to display the plot
        """
        if self.samples is None or self.results is None:
            raise ValueError("Samples or results not available. Call generate_samples and evaluate first.")
        
        # Get objective names
        all_objectives = list(self.problem.objectives.keys())
        
        if objective_names is None:
            if len(all_objectives) >= 2:
                objective_names = all_objectives[:2]  # Use first 2 objectives
            else:
                raise ValueError("At least 2 objectives required for Pareto front plot")
        else:
            for name in objective_names:
                if name not in all_objectives:
                    raise ValueError(f"Objective '{name}' not found in problem definition")
            
            if len(objective_names) < 2:
                raise ValueError("At least 2 objectives required for Pareto front plot")
        
        # Get Pareto points
        pareto_points = self.get_pareto_points(objective_names)
        
        # Extract objective values for all points and Pareto points
        all_x = np.array([result[f"obj_{objective_names[0]}"] for result in self.results])
        all_y = np.array([result[f"obj_{objective_names[1]}"] for result in self.results])
        
        pareto_x = np.array([p[1][objective_names[0]] for p in pareto_points])
        pareto_y = np.array([p[1][objective_names[1]] for p in pareto_points])
        
        # Sort Pareto points for line plotting
        pareto_sorted_indices = np.argsort(pareto_x)
        pareto_x_sorted = pareto_x[pareto_sorted_indices]
        pareto_y_sorted = pareto_y[pareto_sorted_indices]
        
        # Plot Pareto front
        plt.figure(figsize=(10, 8))
        
        # Plot all points
        plt.scatter(all_x, all_y, c='silver', alpha=0.5, label='All points')
        
        # Plot Pareto points
        plt.scatter(pareto_x, pareto_y, c='red', s=100, label='Pareto points')
        
        # Connect Pareto points
        plt.plot(pareto_x_sorted, pareto_y_sorted, 'r--', alpha=0.7)
        
        plt.xlabel(objective_names[0])
        plt.ylabel(objective_names[1])
        plt.title('Pareto Front')
        plt.grid(True, alpha=0.3)
        plt.legend()
        
        if output_dir is not None:
            os.makedirs(output_dir, exist_ok=True)
            plt.savefig(os.path.join(output_dir, 'pareto_front.png'), dpi=300)
        
        if show_plot:
            plt.show()
        else:
            plt.close()
    
    def export_samples(self, filename: str) -> None:
        """
        Export DOE samples to a file.
        
        Args:
            filename: Path to save the data
        """
        if self.samples is None:
            raise ValueError("No samples generated. Call generate_samples first.")
        
        var_names = list(self.problem.design_variables.keys())
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)
        
        # Determine file type from extension
        if filename.endswith('.csv'):
            # Export as CSV
            with open(filename, 'w') as f:
                # Write header
                f.write(','.join(var_names) + '\n')
                
                # Write data
                for sample in self.samples:
                    f.write(','.join(f"{x:.6e}" for x in sample) + '\n')
                    
            logger.info(f"Exported {len(self.samples)} samples to {filename}")
            
        elif filename.endswith('.json'):
            # Export as JSON
            import json
            
            # Prepare data
            data = {
                'doe_type': self.doe_type,
                'n_samples': len(self.samples),
                'variables': var_names,
                'samples': self.samples.tolist()
            }
            
            # Write to file
            with open(filename, 'w') as f:
                json.dump(data, f, indent=4)
                
            logger.info(f"Exported {len(self.samples)} samples to {filename}")
            
        elif filename.endswith('.npy'):
            # Export as NumPy array
            np.save(filename, self.samples)
            logger.info(f"Exported {len(self.samples)} samples to {filename}")
            
        else:
            raise ValueError("Unsupported file format. Use .csv, .json, or .npy")
    
    def export_results(self, filename: str) -> None:
        """
        Export DOE results to a file.
        
        Args:
            filename: Path to save the data
        """
        if self.samples is None or self.results is None:
            raise ValueError("Samples or results not available. Call generate_samples and evaluate first.")
        
        var_names = list(self.problem.design_variables.keys())
        obj_names = list(self.problem.objectives.keys())
        con_names = list(self.problem.constraints.keys())
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)
        
        # Determine file type from extension
        if filename.endswith('.csv'):
            # Export as CSV
            with open(filename, 'w') as f:
                # Write header
                header = var_names.copy()
                
                # Add objective and constraint names
                for name in obj_names:
                    header.append(f"obj_{name}")
                
                for name in con_names:
                    header.append(f"con_{name}")
                
                f.write(','.join(header) + '\n')
                
                # Write data
                for i, sample in enumerate(self.samples):
                    row = [f"{x:.6e}" for x in sample]
                    
                    # Add objective and constraint values
                    for name in obj_names:
                        row.append(f"{self.results[i][f'obj_{name}']:.6e}")
                    
                    for name in con_names:
                        row.append(f"{self.results[i][f'con_{name}']:.6e}")
                    
                    f.write(','.join(row) + '\n')
                    
            logger.info(f"Exported {len(self.samples)} results to {filename}")
            
        elif filename.endswith('.json'):
            # Export as JSON
            import json
            
            # Prepare data
            data = {
                'doe_type': self.doe_type,
                'n_samples': len(self.samples),
                'variables': var_names,
                'objectives': obj_names,
                'constraints': con_names,
                'samples': self.samples.tolist(),
                'results': self.results
            }
            
            # Write to file
            with open(filename, 'w') as f:
                json.dump(data, f, indent=4)
                
            logger.info(f"Exported {len(self.samples)} results to {filename}")
            
        elif filename.endswith('.pkl'):
            # Export as pickle
            import pickle
            
            # Prepare data
            data = {
                'doe_type': self.doe_type,
                'n_samples': len(self.samples),
                'variables': var_names,
                'objectives': obj_names,
                'constraints': con_names,
                'samples': self.samples,
                'results': self.results
            }
            
            # Write to file
            with open(filename, 'wb') as f:
                pickle.dump(data, f)
                
            logger.info(f"Exported {len(self.samples)} results to {filename}")
            
        else:
            raise ValueError("Unsupported file format. Use .csv, .json, or .pkl")
    
    @classmethod
    def import_samples(cls, filename: str, problem):
        """
        Import DOE samples from a file.
        
        Args:
            filename: Path to the data file
            problem: Optimization problem
            
        Returns:
            DesignOfExperiments object with imported samples
        """
        doe = cls(problem, doe_type="imported")
        
        # Determine file type from extension
        if filename.endswith('.csv'):
            # Import from CSV
            samples = []
            
            with open(filename, 'r') as f:
                # Read header
                header = f.readline().strip().split(',')
                
                # Read data
                for line in f:
                    values = [float(x) for x in line.strip().split(',')]
                    samples.append(values)
                    
            doe.samples = np.array(samples)
            
        elif filename.endswith('.json'):
            # Import from JSON
            import json
            
            with open(filename, 'r') as f:
                data = json.load(f)
                
            doe.samples = np.array(data['samples'])
            doe.doe_type = data.get('doe_type', 'imported')
            
        elif filename.endswith('.npy'):
            # Import from NumPy array
            doe.samples = np.load(filename)
            
        else:
            raise ValueError("Unsupported file format. Use .csv, .json, or .npy")
        
        logger.info(f"Imported {len(doe.samples)} samples from {filename}")
        return doe
    
    @classmethod
    def import_results(cls, filename: str, problem):
        """
        Import DOE results from a file.
        
        Args:
            filename: Path to the data file
            problem: Optimization problem
            
        Returns:
            DesignOfExperiments object with imported samples and results
        """
        doe = cls(problem, doe_type="imported")
        
        # Determine file type from extension
        if filename.endswith('.json'):
            # Import from JSON
            import json
            
            with open(filename, 'r') as f:
                data = json.load(f)
                
            doe.samples = np.array(data['samples'])
            doe.results = data['results']
            doe.doe_type = data.get('doe_type', 'imported')
            
        elif filename.endswith('.pkl'):
            # Import from pickle
            import pickle
            
            with open(filename, 'rb') as f:
                data = pickle.load(f)
                
            doe.samples = data['samples']
            doe.results = data['results']
            doe.doe_type = data.get('doe_type', 'imported')
            
        else:
            raise ValueError("Unsupported file format for results. Use .json or .pkl")
        
        logger.info(f"Imported {len(doe.samples)} results from {filename}")
        return doe

# Example usage
if __name__ == "__main__":
    # This is just an example, normally would be imported and used elsewhere
    
    # Example problem definition
    class ExampleProblem:
        def __init__(self):
            self.design_variables = {
                'x1': {'lb': -5.0, 'ub': 5.0},
                'x2': {'lb': -5.0, 'ub': 5.0}
            }
            
            self.objectives = {
                'f1': 'minimize',
                'f2': 'minimize'
            }
            
            self.constraints = {}
            
        def get_bounds(self):
            lb = np.array([var['lb'] for var in self.design_variables.values()])
            ub = np.array([var['ub'] for var in self.design_variables.values()])
            return lb, ub
        
        def evaluate(self, x):
            # Rosenbrock function
            f1 = 100 * (x[1] - x[0]**2)**2 + (1 - x[0])**2
            # Sphere function
            f2 = x[0]**2 + x[1]**2
            
            return {'obj_f1': f1, 'obj_f2': f2}
    
    # Create problem and DOE
    problem = ExampleProblem()
    doe = DesignOfExperiments(problem, doe_type="latin_hypercube", seed=42)
    
    # Generate and evaluate samples
    samples = doe.generate_samples(100)
    results = doe.evaluate()
    
    # Analyze results
    analysis = doe.analyze(output_dir="doe_results", show_plots=True)
    
    # Get best point for first objective
    best_point, best_value = doe.get_best_point('f1')
    print(f"Best point for f1: {best_point}, value: {best_value}")
    
    # Get Pareto points
    pareto_points = doe.get_pareto_points(['f1', 'f2'])
    print(f"Found {len(pareto_points)} Pareto-optimal points")
    
    # Plot Pareto front
    doe.plot_pareto_front(['f1', 'f2'], output_dir="doe_results")
    
    # Export results
    doe.export_results("doe_results/results.json")