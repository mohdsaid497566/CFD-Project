"""
Optimization module for the Intake CFD Optimization Suite.

This module provides classes for setting up and solving optimization problems,
including gradient-based and derivative-free algorithms.
"""

import numpy as np
import logging
import time
import os
import json
import matplotlib.pyplot as plt
from abc import ABC, abstractmethod
from typing import List, Dict, Tuple, Callable, Union, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("optimizer")

class DesignVariable:
    """
    Class representing a design variable in an optimization problem.
    """
    def __init__(self, name: str, lower_bound: float, upper_bound: float, 
                 initial_value: Optional[float] = None, 
                 units: Optional[str] = None, 
                 description: Optional[str] = None):
        """
        Initialize a design variable.
        
        Args:
            name: Name of the design variable
            lower_bound: Lower bound of the design variable
            upper_bound: Upper bound of the design variable
            initial_value: Initial value of the design variable (default: midpoint)
            units: Units of the design variable (optional)
            description: Description of the design variable (optional)
        """
        self.name = name
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound
        
        # Set initial value to midpoint if not provided
        if initial_value is None:
            self.initial_value = (lower_bound + upper_bound) / 2.0
        else:
            # Ensure initial value is within bounds
            self.initial_value = max(lower_bound, min(upper_bound, initial_value))
            
        self.units = units
        self.description = description
        
    def __str__(self):
        """String representation of the design variable."""
        if self.units:
            return f"{self.name} [{self.units}]: {self.initial_value} ({self.lower_bound}, {self.upper_bound})"
        else:
            return f"{self.name}: {self.initial_value} ({self.lower_bound}, {self.upper_bound})"
            
    def normalize(self, value: float) -> float:
        """
        Normalize a value of the design variable to [0, 1] range.
        
        Args:
            value: Value to normalize
            
        Returns:
            Normalized value in [0, 1] range
        """
        return (value - self.lower_bound) / (self.upper_bound - self.lower_bound)
        
    def denormalize(self, normalized_value: float) -> float:
        """
        Convert a normalized value [0, 1] to the original range.
        
        Args:
            normalized_value: Normalized value in [0, 1] range
            
        Returns:
            Denormalized value in original range
        """
        return self.lower_bound + normalized_value * (self.upper_bound - self.lower_bound)

class Constraint:
    """
    Class representing a constraint in an optimization problem.
    """
    def __init__(self, name: str, func: Callable, 
                 constraint_type: str = 'inequality', 
                 lower_bound: Optional[float] = None,
                 upper_bound: Optional[float] = None,
                 units: Optional[str] = None,
                 description: Optional[str] = None):
        """
        Initialize a constraint.
        
        Args:
            name: Name of the constraint
            func: Function that evaluates the constraint
            constraint_type: Type of constraint ('inequality' or 'equality')
            lower_bound: Lower bound for inequality constraint (if applicable)
            upper_bound: Upper bound for inequality constraint (if applicable)
            units: Units of the constraint (optional)
            description: Description of the constraint (optional)
        """
        self.name = name
        self.func = func
        self.constraint_type = constraint_type.lower()
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound
        self.units = units
        self.description = description
        
        # Validate constraint type
        if self.constraint_type not in ['inequality', 'equality']:
            raise ValueError("Constraint type must be 'inequality' or 'equality'")
            
        # Validate bounds for inequality constraint
        if self.constraint_type == 'inequality':
            if self.lower_bound is None and self.upper_bound is None:
                raise ValueError("Inequality constraint must have at least one bound")
        
    def evaluate(self, x: Dict[str, float]) -> float:
        """
        Evaluate the constraint at the given point.
        
        Args:
            x: Dictionary of design variable values
            
        Returns:
            Value of the constraint
        """
        return self.func(x)
        
    def is_satisfied(self, x: Dict[str, float], tolerance: float = 1e-6) -> bool:
        """
        Check if the constraint is satisfied at the given point.
        
        Args:
            x: Dictionary of design variable values
            tolerance: Tolerance for equality constraints
            
        Returns:
            True if the constraint is satisfied, False otherwise
        """
        value = self.evaluate(x)
        
        if self.constraint_type == 'equality':
            # For equality constraints, value should be close to 0
            return abs(value) <= tolerance
            
        else:  # Inequality constraint
            # Check lower bound if specified
            if self.lower_bound is not None and value < self.lower_bound - tolerance:
                return False
                
            # Check upper bound if specified
            if self.upper_bound is not None and value > self.upper_bound + tolerance:
                return False
                
            return True
            
    def constraint_violation(self, x: Dict[str, float]) -> float:
        """
        Calculate the constraint violation at the given point.
        
        Args:
            x: Dictionary of design variable values
            
        Returns:
            Amount of constraint violation (0 if constraint is satisfied)
        """
        value = self.evaluate(x)
        
        if self.constraint_type == 'equality':
            # For equality constraints, violation is absolute difference from 0
            return abs(value)
            
        else:  # Inequality constraint
            violation = 0.0
            
            # Check lower bound if specified
            if self.lower_bound is not None and value < self.lower_bound:
                violation = max(violation, self.lower_bound - value)
                
            # Check upper bound if specified
            if self.upper_bound is not None and value > self.upper_bound:
                violation = max(violation, value - self.upper_bound)
                
            return violation
            
    def __str__(self):
        """String representation of the constraint."""
        if self.constraint_type == 'equality':
            return f"{self.name} = 0"
        else:
            if self.lower_bound is not None and self.upper_bound is not None:
                return f"{self.lower_bound} <= {self.name} <= {self.upper_bound}"
            elif self.lower_bound is not None:
                return f"{self.lower_bound} <= {self.name}"
            else:
                return f"{self.name} <= {self.upper_bound}"

class OptimizationProblem:
    """
    Class representing an optimization problem with objectives and constraints.
    """
    def __init__(self, name: str = "Optimization Problem"):
        """
        Initialize an optimization problem.
        
        Args:
            name: Name of the optimization problem
        """
        self.name = name
        self.design_variables: Dict[str, DesignVariable] = {}
        self.objectives: Dict[str, Callable] = {}
        self.constraints: Dict[str, Constraint] = {}
        self.analysis_function = None
        
    def add_design_variable(self, variable: DesignVariable) -> None:
        """
        Add a design variable to the problem.
        
        Args:
            variable: The design variable to add
        """
        self.design_variables[variable.name] = variable
        
    def add_objective(self, name: str, func: Callable, minimize: bool = True) -> None:
        """
        Add an objective function to the problem.
        
        Args:
            name: Name of the objective
            func: Function that evaluates the objective
            minimize: Whether to minimize (True) or maximize (False) the objective
        """
        # Store a modified function that negates the value if maximizing
        if minimize:
            self.objectives[name] = func
        else:
            self.objectives[name] = lambda x: -func(x)
            
    def add_constraint(self, constraint: Constraint) -> None:
        """
        Add a constraint to the problem.
        
        Args:
            constraint: The constraint to add
        """
        self.constraints[constraint.name] = constraint
        
    def set_analysis_function(self, func: Callable) -> None:
        """
        Set the analysis function that evaluates all objectives and constraints.
        
        Args:
            func: Function that takes design variables and returns results dictionary
        """
        self.analysis_function = func
        
    def evaluate(self, x: Union[Dict[str, float], np.ndarray]) -> Dict[str, float]:
        """
        Evaluate all objectives and constraints at the given point.
        
        Args:
            x: Dictionary of design variable values or array of normalized values
            
        Returns:
            Dictionary containing objective and constraint values
        """
        # If x is a numpy array, convert to dictionary
        if isinstance(x, np.ndarray):
            x_dict = {}
            for i, (name, var) in enumerate(self.design_variables.items()):
                x_dict[name] = var.denormalize(x[i])
        else:
            x_dict = x
            
        results = {}
        
        # If analysis function is provided, use it to compute all outputs at once
        if self.analysis_function is not None:
            analysis_results = self.analysis_function(x_dict)
            
            # Extract objectives and constraints from analysis results
            for name in self.objectives.keys():
                if name in analysis_results:
                    results[f"obj_{name}"] = analysis_results[name]
                else:
                    results[f"obj_{name}"] = self.objectives[name](x_dict)
                    
            for name, constraint in self.constraints.items():
                if name in analysis_results:
                    results[f"con_{name}"] = analysis_results[name]
                else:
                    results[f"con_{name}"] = constraint.evaluate(x_dict)
        else:
            # Evaluate each objective and constraint separately
            for name, func in self.objectives.items():
                results[f"obj_{name}"] = func(x_dict)
                
            for name, constraint in self.constraints.items():
                results[f"con_{name}"] = constraint.evaluate(x_dict)
                
        return results
        
    def get_initial_point(self) -> np.ndarray:
        """
        Get the initial point for optimization.
        
        Returns:
            Array of normalized initial values for all design variables
        """
        x0 = np.zeros(len(self.design_variables))
        
        for i, var in enumerate(self.design_variables.values()):
            x0[i] = var.normalize(var.initial_value)
            
        return x0
        
    def get_bounds(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Get the normalized bounds for all design variables.
        
        Returns:
            Tuple of (lower_bounds, upper_bounds) arrays
        """
        n = len(self.design_variables)
        lb = np.zeros(n)
        ub = np.ones(n)
        
        return lb, ub
        
    def get_constraint_bounds(self) -> Tuple[List[float], List[float]]:
        """
        Get the bounds for all constraints.
        
        Returns:
            Tuple of (lower_bounds, upper_bounds) lists
        """
        lb = []
        ub = []
        
        for constraint in self.constraints.values():
            if constraint.constraint_type == 'equality':
                lb.append(0.0)
                ub.append(0.0)
            else:  # Inequality constraint
                if constraint.lower_bound is not None:
                    lb.append(constraint.lower_bound)
                else:
                    lb.append(-np.inf)
                    
                if constraint.upper_bound is not None:
                    ub.append(constraint.upper_bound)
                else:
                    ub.append(np.inf)
                    
        return lb, ub
        
    def __str__(self):
        """String representation of the optimization problem."""
        s = [f"Optimization Problem: {self.name}"]
        
        s.append("\nDesign Variables:")
        for var in self.design_variables.values():
            s.append(f"  {var}")
            
        s.append("\nObjectives:")
        for name in self.objectives.keys():
            s.append(f"  {name}")
            
        s.append("\nConstraints:")
        for constraint in self.constraints.values():
            s.append(f"  {constraint}")
            
        return "\n".join(s)

class OptimizerAlgorithm(ABC):
    """
    Abstract base class for optimization algorithms.
    """
    @abstractmethod
    def minimize(self, problem: OptimizationProblem, 
                x0: np.ndarray = None, 
                max_iterations: int = 100, 
                tolerance: float = 1e-6) -> Dict:
        """
        Minimize the objective function(s) of the optimization problem.
        
        Args:
            problem: The optimization problem to solve
            x0: Initial point (if None, use problem's initial point)
            max_iterations: Maximum number of iterations
            tolerance: Convergence tolerance
            
        Returns:
            Dictionary with optimization results
        """
        pass

class GradientDescentOptimizer(OptimizerAlgorithm):
    """
    Simple gradient descent optimizer with finite difference gradient estimation.
    """
    def __init__(self, learning_rate: float = 0.1, 
                 momentum: float = 0.0,
                 finite_diff_step: float = 1e-6):
        """
        Initialize the gradient descent optimizer.
        
        Args:
            learning_rate: Learning rate / step size
            momentum: Momentum coefficient (0.0 for no momentum)
            finite_diff_step: Step size for finite difference gradient calculation
        """
        self.learning_rate = learning_rate
        self.momentum = momentum
        self.finite_diff_step = finite_diff_step
        
    def estimate_gradient(self, problem: OptimizationProblem, 
                         x: np.ndarray, 
                         obj_name: str) -> np.ndarray:
        """
        Estimate the gradient using finite differences.
        
        Args:
            problem: The optimization problem
            x: Current point
            obj_name: Name of the objective to compute the gradient for
            
        Returns:
            Gradient vector
        """
        n = len(x)
        grad = np.zeros(n)
        
        # Evaluate the base point
        base_results = problem.evaluate(x)
        base_obj = base_results[f"obj_{obj_name}"]
        
        # Compute forward differences
        for i in range(n):
            x_step = x.copy()
            x_step[i] += self.finite_diff_step
            
            # Evaluate the perturbed point
            step_results = problem.evaluate(x_step)
            step_obj = step_results[f"obj_{obj_name}"]
            
            # Compute gradient
            grad[i] = (step_obj - base_obj) / self.finite_diff_step
            
        return grad
        
    def minimize(self, problem: OptimizationProblem, 
                x0: np.ndarray = None, 
                max_iterations: int = 100, 
                tolerance: float = 1e-6) -> Dict:
        """
        Minimize the objective function using gradient descent.
        
        Args:
            problem: The optimization problem to solve
            x0: Initial point (if None, use problem's initial point)
            max_iterations: Maximum number of iterations
            tolerance: Convergence tolerance
            
        Returns:
            Dictionary with optimization results
        """
        # Use default initial point if none provided
        if x0 is None:
            x0 = problem.get_initial_point()
            
        # Get problem bounds
        lb, ub = problem.get_bounds()
        
        # Initialize
        x = x0.copy()
        velocity = np.zeros_like(x)
        
        # Check if multi-objective
        if len(problem.objectives) > 1:
            logger.warning("Gradient descent with multiple objectives not supported. Using first objective.")
            
        # Get first objective name
        obj_name = list(problem.objectives.keys())[0]
        
        # Initialize history
        history = {
            'iterations': [],
            'x': [],
            'obj': [],
            'grad_norm': [],
            'step': [],
            'constraint_violation': []
        }
        
        # Start timer
        start_time = time.time()
        
        for iteration in range(max_iterations):
            # Evaluate objective and constraints
            results = problem.evaluate(x)
            obj_value = results[f"obj_{obj_name}"]
            
            # Compute constraint violation
            constraint_violation = 0.0
            for name, constraint in problem.constraints.items():
                constraint_value = results[f"con_{name}"]
                
                if constraint.constraint_type == 'equality':
                    constraint_violation += abs(constraint_value)
                else:  # Inequality constraint
                    if constraint.lower_bound is not None and constraint_value < constraint.lower_bound:
                        constraint_violation += constraint.lower_bound - constraint_value
                    if constraint.upper_bound is not None and constraint_value > constraint.upper_bound:
                        constraint_violation += constraint_value - constraint.upper_bound
            
            # Estimate gradient
            grad = self.estimate_gradient(problem, x, obj_name)
            grad_norm = np.linalg.norm(grad)
            
            # Update history
            history['iterations'].append(iteration)
            history['x'].append(x.copy())
            history['obj'].append(obj_value)
            history['grad_norm'].append(grad_norm)
            history['constraint_violation'].append(constraint_violation)
            
            # Check convergence
            if grad_norm < tolerance:
                logger.info(f"Converged after {iteration} iterations (gradient norm = {grad_norm:.6e})")
                break
                
            # Update velocity with momentum
            velocity = self.momentum * velocity - self.learning_rate * grad
            
            # Update position
            x_new = x + velocity
            
            # Project onto bounds
            x_new = np.maximum(np.minimum(x_new, ub), lb)
            
            # Compute step size
            step = np.linalg.norm(x_new - x)
            history['step'].append(step)
            
            # Update position
            x = x_new
            
            # Log progress
            if iteration % 10 == 0:
                logger.info(f"Iteration {iteration}: obj = {obj_value:.6e}, "
                          f"grad_norm = {grad_norm:.6e}, step = {step:.6e}, "
                          f"constraint_violation = {constraint_violation:.6e}")
                
        # End timer
        end_time = time.time()
        
        # Final evaluation
        final_results = problem.evaluate(x)
        obj_value = final_results[f"obj_{obj_name}"]
        
        # Convert normalized x to original values
        x_dict = {}
        for i, (name, var) in enumerate(problem.design_variables.items()):
            x_dict[name] = var.denormalize(x[i])
            
        # Package results
        results = {
            'x': x,
            'x_dict': x_dict,
            'obj_value': obj_value,
            'n_iterations': len(history['iterations']),
            'n_function_evals': len(history['iterations']) * (len(problem.design_variables) + 1),
            'success': np.linalg.norm(grad) < tolerance,
            'time': end_time - start_time,
            'history': history
        }
        
        return results

class GeneticAlgorithm(OptimizerAlgorithm):
    """
    Genetic algorithm optimizer.
    """
    def __init__(self, population_size: int = 50, 
                 elite_ratio: float = 0.1,
                 crossover_prob: float = 0.8,
                 mutation_prob: float = 0.2,
                 mutation_scale: float = 0.1):
        """
        Initialize the genetic algorithm optimizer.
        
        Args:
            population_size: Size of the population
            elite_ratio: Ratio of elite individuals to keep unchanged
            crossover_prob: Probability of crossover
            mutation_prob: Probability of mutation
            mutation_scale: Scale of mutation relative to bounds
        """
        self.population_size = population_size
        self.elite_ratio = elite_ratio
        self.crossover_prob = crossover_prob
        self.mutation_prob = mutation_prob
        self.mutation_scale = mutation_scale
        
    def initialize_population(self, n_vars: int, lb: np.ndarray, ub: np.ndarray) -> np.ndarray:
        """
        Initialize a random population.
        
        Args:
            n_vars: Number of design variables
            lb: Lower bounds
            ub: Upper bounds
            
        Returns:
            Initial population array of shape (population_size, n_vars)
        """
        return lb + np.random.random((self.population_size, n_vars)) * (ub - lb)
        
    def evaluate_population(self, problem: OptimizationProblem, 
                           population: np.ndarray, 
                           obj_name: str) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Evaluate the objective and constraint violation for the entire population.
        
        Args:
            problem: The optimization problem
            population: Population array of shape (population_size, n_vars)
            obj_name: Name of the objective to evaluate
            
        Returns:
            Tuple of (objective values, constraint violations, evaluation results)
        """
        n_pop = population.shape[0]
        obj_values = np.zeros(n_pop)
        constraint_violations = np.zeros(n_pop)
        eval_results = []
        
        for i in range(n_pop):
            # Evaluate individual
            results = problem.evaluate(population[i])
            eval_results.append(results)
            
            # Get objective value
            obj_values[i] = results[f"obj_{obj_name}"]
            
            # Compute constraint violation
            constraint_violation = 0.0
            for name, constraint in problem.constraints.items():
                constraint_value = results[f"con_{name}"]
                
                if constraint.constraint_type == 'equality':
                    constraint_violation += abs(constraint_value)
                else:  # Inequality constraint
                    if constraint.lower_bound is not None and constraint_value < constraint.lower_bound:
                        constraint_violation += constraint.lower_bound - constraint_value
                    if constraint.upper_bound is not None and constraint_value > constraint.upper_bound:
                        constraint_violation += constraint_value - constraint.upper_bound
                        
            constraint_violations[i] = constraint_violation
            
        return obj_values, constraint_violations, eval_results
        
    def compute_fitness(self, obj_values: np.ndarray, 
                       constraint_violations: np.ndarray, 
                       constraint_penalty: float = 1000.0) -> np.ndarray:
        """
        Compute fitness values from objective values and constraint violations.
        
        Args:
            obj_values: Objective values
            constraint_violations: Constraint violations
            constraint_penalty: Penalty coefficient for constraint violations
            
        Returns:
            Fitness values
        """
        # Penalize objective with constraint violations
        return obj_values + constraint_penalty * constraint_violations
        
    def selection(self, population: np.ndarray, fitness: np.ndarray) -> np.ndarray:
        """
        Select parents using tournament selection.
        
        Args:
            population: Population array
            fitness: Fitness values (lower is better)
            
        Returns:
            Selected parents
        """
        n_pop, n_vars = population.shape
        selected = np.zeros_like(population)
        
        for i in range(n_pop):
            # Select two random individuals
            idx1 = np.random.randint(n_pop)
            idx2 = np.random.randint(n_pop)
            
            # Select the one with better fitness (lower value)
            if fitness[idx1] < fitness[idx2]:
                selected[i] = population[idx1].copy()
            else:
                selected[i] = population[idx2].copy()
                
        return selected
        
    def crossover(self, parents: np.ndarray) -> np.ndarray:
        """
        Perform crossover to create offspring.
        
        Args:
            parents: Parent population
            
        Returns:
            Offspring population
        """
        n_pop, n_vars = parents.shape
        offspring = np.zeros_like(parents)
        
        for i in range(0, n_pop, 2):
            if i + 1 < n_pop:  # Ensure we have a pair
                if np.random.random() < self.crossover_prob:
                    # Single-point crossover
                    crossover_point = np.random.randint(1, n_vars)
                    
                    # First offspring
                    offspring[i, :crossover_point] = parents[i, :crossover_point]
                    offspring[i, crossover_point:] = parents[i+1, crossover_point:]
                    
                    # Second offspring
                    offspring[i+1, :crossover_point] = parents[i+1, :crossover_point]
                    offspring[i+1, crossover_point:] = parents[i, crossover_point:]
                else:
                    # No crossover
                    offspring[i] = parents[i].copy()
                    offspring[i+1] = parents[i+1].copy()
            else:
                # Odd population size, just copy the last parent
                offspring[i] = parents[i].copy()
                
        return offspring
        
    def mutation(self, population: np.ndarray, lb: np.ndarray, ub: np.ndarray) -> np.ndarray:
        """
        Perform mutation on the population.
        
        Args:
            population: Population array
            lb: Lower bounds
            ub: Upper bounds
            
        Returns:
            Mutated population
        """
        n_pop, n_vars = population.shape
        
        # Determine which individuals and variables to mutate
        mutation_mask = np.random.random((n_pop, n_vars)) < self.mutation_prob
        
        # Generate random mutations
        mutations = np.random.normal(loc=0.0, scale=self.mutation_scale, 
                                    size=(n_pop, n_vars))
        mutations = mutations * (ub - lb)  # Scale by variable range
        
        # Apply mutations
        mutated = population.copy()
        mutated[mutation_mask] += mutations[mutation_mask]
        
        # Ensure bounds are respected
        mutated = np.maximum(np.minimum(mutated, ub), lb)
        
        return mutated
        
    def minimize(self, problem: OptimizationProblem, 
                x0: np.ndarray = None, 
                max_iterations: int = 100, 
                tolerance: float = 1e-6) -> Dict:
        """
        Minimize the objective function using a genetic algorithm.
        
        Args:
            problem: The optimization problem to solve
            x0: Initial point (if provided, included in initial population)
            max_iterations: Maximum number of iterations (generations)
            tolerance: Convergence tolerance (not used directly in GA)
            
        Returns:
            Dictionary with optimization results
        """
        # Get problem dimensions
        n_vars = len(problem.design_variables)
        lb, ub = problem.get_bounds()
        
        # Check if multi-objective
        if len(problem.objectives) > 1:
            logger.warning("Genetic algorithm with multiple objectives not supported. Using first objective.")
            
        # Get first objective name
        obj_name = list(problem.objectives.keys())[0]
        
        # Initialize population
        population = self.initialize_population(n_vars, lb, ub)
        
        # Include initial guess if provided
        if x0 is not None:
            population[0] = x0.copy()
            
        # Initialize history
        history = {
            'generations': [],
            'min_obj': [],
            'mean_obj': [],
            'best_x': [],
            'best_fitness': [],
            'mean_constraint_violation': []
        }
        
        # Start timer
        start_time = time.time()
        
        best_obj = float('inf')
        best_x = None
        best_results = None
        n_elite = int(self.elite_ratio * self.population_size)
        
        for generation in range(max_iterations):
            # Evaluate population
            obj_values, constraint_violations, eval_results = self.evaluate_population(
                problem, population, obj_name)
                
            # Compute fitness
            fitness = self.compute_fitness(obj_values, constraint_violations)
            
            # Find best individual
            best_idx = np.argmin(fitness)
            generation_best_obj = obj_values[best_idx]
            generation_best_x = population[best_idx].copy()
            
            # Update global best
            if generation_best_obj < best_obj and constraint_violations[best_idx] < tolerance:
                best_obj = generation_best_obj
                best_x = generation_best_x.copy()
                best_results = eval_results[best_idx]
                
            # Update history
            history['generations'].append(generation)
            history['min_obj'].append(np.min(obj_values))
            history['mean_obj'].append(np.mean(obj_values))
            history['best_x'].append(generation_best_x.copy())
            history['best_fitness'].append(np.min(fitness))
            history['mean_constraint_violation'].append(np.mean(constraint_violations))
            
            # Log progress
            if generation % 10 == 0:
                logger.info(f"Generation {generation}: best obj = {generation_best_obj:.6e}, "
                          f"mean obj = {np.mean(obj_values):.6e}, "
                          f"mean constraint violation = {np.mean(constraint_violations):.6e}")
                
            # Check for convergence - not typically used in GA but can stop early if we're close enough
            if np.min(constraint_violations) < tolerance and generation > 20:
                # Check if population has converged (low diversity)
                if np.max(np.std(population, axis=0)) < tolerance:
                    logger.info(f"Converged after {generation} generations (low diversity)")
                    break
                    
            # Create next generation
            # Sort by fitness
            sorted_indices = np.argsort(fitness)
            sorted_population = population[sorted_indices]
            
            # Keep elite individuals
            next_population = np.zeros_like(population)
            next_population[:n_elite] = sorted_population[:n_elite]
            
            # Selection
            selected = self.selection(population, fitness)
            
            # Crossover
            offspring = self.crossover(selected)
            
            # Mutation
            mutated_offspring = self.mutation(offspring, lb, ub)
            
            # Combine elite with new individuals
            next_population[n_elite:] = mutated_offspring[:(self.population_size - n_elite)]
            
            # Update population
            population = next_population
            
        # End timer
        end_time = time.time()
        
        # If no solution found that satisfies constraints, use the best from the last generation
        if best_x is None:
            best_idx = np.argmin(fitness)
            best_x = population[best_idx].copy()
            best_obj = obj_values[best_idx]
            best_results = eval_results[best_idx]
            
        # Convert normalized x to original values
        x_dict = {}
        for i, (name, var) in enumerate(problem.design_variables.items()):
            x_dict[name] = var.denormalize(best_x[i])
            
        # Package results
        results = {
            'x': best_x,
            'x_dict': x_dict,
            'obj_value': best_obj,
            'n_generations': len(history['generations']),
            'n_function_evals': len(history['generations']) * self.population_size,
            'success': True,  # GA always returns a solution, even if constraints not satisfied
            'time': end_time - start_time,
            'history': history
        }
        
        # Add final evaluation results
        for key, value in best_results.items():
            results[key] = value
        
        return results

class Optimizer:
    """
    Main optimizer class that provides a unified interface to different optimization algorithms.
    """
    def __init__(self, 
                algorithm: str = 'genetic', 
                options: Dict = None,
                output_dir: Optional[str] = None,
                save_history: bool = True):
        """
        Initialize the optimizer.
        
        Args:
            algorithm: Optimization algorithm to use ('gradient', 'genetic', 'bfgs')
            options: Algorithm-specific options
            output_dir: Directory to save results (default: 'optimization_results')
            save_history: Whether to save optimization history
        """
        self.algorithm = algorithm.lower()
        self.options = options or {}
        
        if output_dir is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.output_dir = f"optimization_results_{timestamp}"
        else:
            self.output_dir = output_dir
            
        self.save_history = save_history
        
        # Create output directory if needed
        if self.save_history:
            os.makedirs(self.output_dir, exist_ok=True)
        
    def get_algorithm(self) -> OptimizerAlgorithm:
        """
        Get the optimization algorithm instance based on selected algorithm.
        
        Returns:
            OptimizerAlgorithm instance
        """
        if self.algorithm == 'gradient':
            return GradientDescentOptimizer(
                learning_rate=self.options.get('learning_rate', 0.1),
                momentum=self.options.get('momentum', 0.0),
                finite_diff_step=self.options.get('finite_diff_step', 1e-6)
            )
        elif self.algorithm == 'genetic':
            return GeneticAlgorithm(
                population_size=self.options.get('population_size', 50),
                elite_ratio=self.options.get('elite_ratio', 0.1),
                crossover_prob=self.options.get('crossover_prob', 0.8),
                mutation_prob=self.options.get('mutation_prob', 0.2),
                mutation_scale=self.options.get('mutation_scale', 0.1)
            )
        elif self.algorithm == 'bfgs':
            # We'll use scipy's implementation
            try:
                from scipy.optimize import minimize as scipy_minimize
                
                def bfgs_algo(problem, x0, max_iterations, tolerance):
                    obj_name = list(problem.objectives.keys())[0]
                    
                    def obj_func(x):
                        results = problem.evaluate(x)
                        return results[f"obj_{obj_name}"]
                        
                    bounds = [(0, 1) for _ in range(len(problem.design_variables))]
                    
                    result = scipy_minimize(
                        obj_func, 
                        x0 if x0 is not None else problem.get_initial_point(),
                        method='L-BFGS-B',
                        bounds=bounds,
                        options={
                            'maxiter': max_iterations,
                            'ftol': tolerance,
                            'gtol': tolerance
                        }
                    )
                    
                    # Evaluate at solution point
                    final_results = problem.evaluate(result.x)
                    
                    # Convert normalized x to original values
                    x_dict = {}
                    for i, (name, var) in enumerate(problem.design_variables.items()):
                        x_dict[name] = var.denormalize(result.x[i])
                        
                    # Package results
                    opt_results = {
                        'x': result.x,
                        'x_dict': x_dict,
                        'obj_value': result.fun,
                        'n_iterations': result.nit,
                        'n_function_evals': result.nfev,
                        'success': result.success,
                        'time': None,  # Not provided by scipy
                        'message': result.message
                    }
                    
                    # Add final evaluation results
                    for key, value in final_results.items():
                        opt_results[key] = value
                    
                    return opt_results
                    
                # Return a wrapper since we're not using the OptimizerAlgorithm class
                class BfgsWrapper(OptimizerAlgorithm):
                    def minimize(self, problem, x0=None, max_iterations=100, tolerance=1e-6):
                        return bfgs_algo(problem, x0, max_iterations, tolerance)
                        
                return BfgsWrapper()
                
            except ImportError:
                logger.warning("SciPy not available, falling back to genetic algorithm")
                return GeneticAlgorithm()
        else:
            logger.warning(f"Unknown algorithm '{self.algorithm}', using genetic algorithm")
            return GeneticAlgorithm()
            
    def optimize(self, problem: OptimizationProblem, 
                x0: np.ndarray = None, 
                max_iterations: int = 100, 
                tolerance: float = 1e-6) -> Dict:
        """
        Optimize the problem.
        
        Args:
            problem: The optimization problem to solve
            x0: Initial point (if None, use problem's initial point)
            max_iterations: Maximum number of iterations
            tolerance: Convergence tolerance
            
        Returns:
            Dictionary with optimization results
        """
        logger.info(f"Starting optimization with {self.algorithm} algorithm")
        logger.info(f"Problem: {problem.name}")
        logger.info(f"  {len(problem.design_variables)} design variables")
        logger.info(f"  {len(problem.objectives)} objectives")
        logger.info(f"  {len(problem.constraints)} constraints")
        
        # Get algorithm
        algorithm = self.get_algorithm()
        
        # Optimize
        results = algorithm.minimize(problem, x0, max_iterations, tolerance)
        
        # Log results
        logger.info(f"Optimization complete:")
        logger.info(f"  Objective value: {results['obj_value']:.6e}")
        logger.info(f"  Iterations: {results['n_iterations']}")
        logger.info(f"  Function evaluations: {results['n_function_evals']}")
        logger.info(f"  Time: {results['time']:.2f} seconds" if results['time'] is not None else "  Time: unknown")
        
        # Log design variable values
        logger.info("  Design variable values:")
        for name, value in results['x_dict'].items():
            logger.info(f"    {name}: {value}")
            
        # Save results if requested
        if self.save_history:
            self._save_results(problem, results)
            
        return results
        
    def _save_results(self, problem: OptimizationProblem, results: Dict) -> None:
        """
        Save optimization results to files.
        
        Args:
            problem: The optimization problem
            results: Optimization results
        """
        # Save final design variables
        with open(os.path.join(self.output_dir, 'optimal_design.json'), 'w') as f:
            json.dump(results['x_dict'], f, indent=4)
            
        # Save summary
        summary = {
            'problem_name': problem.name,
            'algorithm': self.algorithm,
            'options': self.options,
            'obj_value': float(results['obj_value']),  # Convert numpy types to Python types
            'n_iterations': results['n_iterations'],
            'n_function_evals': results['n_function_evals'],
            'time': float(results['time']) if results['time'] is not None else None,
            'success': bool(results['success']),
            'timestamp': datetime.now().isoformat()
        }
        
        with open(os.path.join(self.output_dir, 'summary.json'), 'w') as f:
            json.dump(summary, f, indent=4)
            
        # Save convergence history plot
        if 'history' in results:
            history = results['history']
            
            # Plot objective vs. iteration
            plt.figure(figsize=(10, 6))
            
            if self.algorithm == 'genetic':
                plt.plot(history['generations'], history['min_obj'], 'b-', label='Best')
                plt.plot(history['generations'], history['mean_obj'], 'r--', label='Mean')
                plt.xlabel('Generation')
            else:
                plt.plot(history['iterations'], history['obj'], 'b-')
                plt.xlabel('Iteration')
                
            plt.ylabel('Objective Value')
            plt.title('Convergence History')
            plt.grid(True)
            plt.legend()
            plt.tight_layout()
            plt.savefig(os.path.join(self.output_dir, 'convergence_history.png'), dpi=300)
            plt.close()
            
            # Plot constraint violation
            if 'constraint_violation' in history:
                plt.figure(figsize=(10, 6))
                
                if self.algorithm == 'genetic':
                    plt.semilogy(history['generations'], 
                               np.maximum(history['mean_constraint_violation'], 1e-10), 
                               'r-')
                    plt.xlabel('Generation')
                else:
                    plt.semilogy(history['iterations'], 
                               np.maximum(history['constraint_violation'], 1e-10), 
                               'r-')
                    plt.xlabel('Iteration')
                    
                plt.ylabel('Constraint Violation')
                plt.title('Constraint Violation History')
                plt.grid(True)
                plt.tight_layout()
                plt.savefig(os.path.join(self.output_dir, 'constraint_violation.png'), dpi=300)
                plt.close()
                
            # Save raw history data
            with open(os.path.join(self.output_dir, 'history.json'), 'w') as f:
                # Convert numpy arrays to lists
                history_json = {}
                for key, value in history.items():
                    if isinstance(value, list) and len(value) > 0 and isinstance(value[0], np.ndarray):
                        history_json[key] = [arr.tolist() for arr in value]
                    elif isinstance(value, np.ndarray):
                        history_json[key] = value.tolist()
                    else:
                        history_json[key] = value
                        
                json.dump(history_json, f, indent=4)

# Example usage if this module is run directly
if __name__ == "__main__":
    # Define a simple optimization problem
    problem = OptimizationProblem("Simple Quadratic Problem")
    
    # Add design variables
    problem.add_design_variable(DesignVariable("x1", -5, 5, 0))
    problem.add_design_variable(DesignVariable("x2", -5, 5, 0))
    
    # Define objective function
    def objective(x):
        return x["x1"]**2 + x["x2"]**2
        
    # Add objective
    problem.add_objective("f", objective, minimize=True)
    
    # Define constraint
    def constraint(x):
        return x["x1"] + x["x2"]  # x1 + x2 >= 1
        
    # Add constraint
    problem.add_constraint(Constraint("g1", constraint, "inequality", lower_bound=1))
    
    # Create optimizer
    optimizer = Optimizer(algorithm="genetic", 
                         options={"population_size": 50, "elite_ratio": 0.1}, 
                         output_dir="simple_opt_results")
    
    # Optimize
    results = optimizer.optimize(problem, max_iterations=50)
    
    # Print results
    print("\nOptimization Results:")
    print(f"x1 = {results['x_dict']['x1']:.6f}")
    print(f"x2 = {results['x_dict']['x2']:.6f}")
    print(f"f(x) = {results['obj_value']:.6f}")
    print(f"g1(x) = {results['con_g1']:.6f} (>= 1)")
    print(f"Iterations: {results['n_iterations']}")
    print(f"Function evaluations: {results['n_function_evals']}")