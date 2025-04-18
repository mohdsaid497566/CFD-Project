"""
Multi-objective optimization module for the Intake CFD Optimization Suite.

This module provides algorithms and utilities for multi-objective optimization,
including Pareto front analysis and visualization.
"""

import numpy as np
import matplotlib.pyplot as plt
import logging
import os
import json
from typing import List, Dict, Tuple, Callable, Union, Optional, Any
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("multi_objective")

class ParetoFront:
    """
    Class for managing and analyzing Pareto fronts in multi-objective optimization.
    """
    def __init__(self, tolerance: float = 1e-6):
        """
        Initialize a Pareto front container.
        
        Args:
            tolerance: Numerical tolerance for dominance comparison
        """
        self.tolerance = tolerance
        self.points = []  # List of tuples (objectives, variables)
        self.dominated_points = []  # Non-Pareto points for reference
        
    def add_point(self, objectives: np.ndarray, variables: Dict[str, float]) -> bool:
        """
        Add a point to the Pareto front if it's non-dominated.
        
        Args:
            objectives: Array of objective values (smaller is better)
            variables: Dictionary of design variable values
            
        Returns:
            True if the point was added to the Pareto front, False otherwise
        """
        point = (objectives, variables)
        
        # Check if this point is dominated by any existing Pareto point
        for i, (existing_obj, _) in enumerate(self.points):
            if self._dominates(existing_obj, objectives):
                # Point is dominated, add to dominated points list
                self.dominated_points.append(point)
                return False
        
        # If we get here, the point is not dominated by any existing point
        # Now check if this point dominates any existing Pareto points
        non_dominated = []
        newly_dominated = []
        
        for existing_point in self.points:
            existing_obj, _ = existing_point
            if self._dominates(objectives, existing_obj):
                # Existing point is dominated by new point
                newly_dominated.append(existing_point)
            else:
                # Existing point is not dominated
                non_dominated.append(existing_point)
        
        # Update Pareto front
        self.points = non_dominated + [point]
        self.dominated_points.extend(newly_dominated)
        
        return True
    
    def _dominates(self, obj1: np.ndarray, obj2: np.ndarray) -> bool:
        """
        Check if obj1 dominates obj2 (obj1 is better or equal in all dimensions,
        and strictly better in at least one dimension).
        
        Args:
            obj1: First objective vector
            obj2: Second objective vector
            
        Returns:
            True if obj1 dominates obj2, False otherwise
        """
        # Must be better or equal in all dimensions
        if not np.all(obj1 <= obj2 + self.tolerance):
            return False
        
        # Must be strictly better in at least one dimension
        return np.any(obj1 < obj2 - self.tolerance)
    
    def get_pareto_points(self) -> List[Tuple[np.ndarray, Dict[str, float]]]:
        """
        Get the current Pareto-optimal points.
        
        Returns:
            List of tuples (objectives, variables) for Pareto-optimal points
        """
        return self.points
    
    def get_dominated_points(self) -> List[Tuple[np.ndarray, Dict[str, float]]]:
        """
        Get the dominated (non-Pareto) points.
        
        Returns:
            List of tuples (objectives, variables) for dominated points
        """
        return self.dominated_points
    
    def get_all_points(self) -> List[Tuple[np.ndarray, Dict[str, float]]]:
        """
        Get all points (both Pareto and dominated).
        
        Returns:
            List of tuples (objectives, variables) for all points
        """
        return self.points + self.dominated_points
    
    def plot(self, obj_indices: List[int] = None, 
            obj_names: List[str] = None,
            show_dominated: bool = True,
            output_dir: Optional[str] = None,
            show_plot: bool = True) -> None:
        """
        Plot the Pareto front for visualization.
        
        Args:
            obj_indices: Indices of objectives to plot (default: first two)
            obj_names: Names of objectives for labeling
            show_dominated: Whether to show dominated points
            output_dir: Directory to save plot (if None, don't save)
            show_plot: Whether to display the plot
        """
        if not self.points:
            logger.warning("No Pareto points to plot")
            return
        
        # Get dimensionality of objectives
        obj_dim = len(self.points[0][0])
        
        # Default to first two objectives if not specified
        if obj_indices is None:
            if obj_dim >= 2:
                obj_indices = [0, 1]
            else:
                obj_indices = [0]
        
        # Validate indices
        for idx in obj_indices:
            if idx < 0 or idx >= obj_dim:
                raise ValueError(f"Objective index {idx} out of range (0-{obj_dim-1})")
        
        # Default objective names
        if obj_names is None:
            obj_names = [f"Objective {i+1}" for i in obj_indices]
        
        # Extract objective values for plotting
        pareto_objs = np.array([point[0] for point in self.points])
        
        if show_dominated and self.dominated_points:
            dominated_objs = np.array([point[0] for point in self.dominated_points])
        
        # Create figure
        plt.figure(figsize=(10, 6))
        
        if len(obj_indices) == 1:
            # 1D plot (rare, but possible)
            idx = obj_indices[0]
            y_vals = pareto_objs[:, idx]
            x_vals = np.arange(len(y_vals))
            
            plt.plot(x_vals, y_vals, 'bo-', label='Pareto Front')
            
            if show_dominated and self.dominated_points:
                y_vals_dom = dominated_objs[:, idx]
                x_vals_dom = np.arange(len(y_vals_dom)) + len(y_vals)
                plt.plot(x_vals_dom, y_vals_dom, 'rx', label='Dominated Points')
            
            plt.xlabel("Point Index")
            plt.ylabel(obj_names[0])
            
        elif len(obj_indices) == 2:
            # 2D plot
            idx1, idx2 = obj_indices
            
            # Plot Pareto front
            plt.plot(pareto_objs[:, idx1], pareto_objs[:, idx2], 'bo-', label='Pareto Front')
            
            # Plot dominated points if requested
            if show_dominated and self.dominated_points:
                plt.plot(dominated_objs[:, idx1], dominated_objs[:, idx2], 'rx', 
                        alpha=0.5, label='Dominated Points')
            
            plt.xlabel(obj_names[0])
            plt.ylabel(obj_names[1])
            
        elif len(obj_indices) == 3:
            # 3D plot
            ax = plt.figure().add_subplot(111, projection='3d')
            idx1, idx2, idx3 = obj_indices
            
            # Plot Pareto front
            ax.scatter(pareto_objs[:, idx1], pareto_objs[:, idx2], pareto_objs[:, idx3], 
                     c='b', marker='o', label='Pareto Front')
            
            # Connect points to make the front more visible
            for i in range(len(pareto_objs) - 1):
                ax.plot([pareto_objs[i, idx1], pareto_objs[i+1, idx1]],
                      [pareto_objs[i, idx2], pareto_objs[i+1, idx2]],
                      [pareto_objs[i, idx3], pareto_objs[i+1, idx3]], 'b-')
            
            # Plot dominated points if requested
            if show_dominated and self.dominated_points:
                ax.scatter(dominated_objs[:, idx1], dominated_objs[:, idx2], dominated_objs[:, idx3],
                         c='r', marker='x', alpha=0.5, label='Dominated Points')
            
            ax.set_xlabel(obj_names[0])
            ax.set_ylabel(obj_names[1])
            ax.set_zlabel(obj_names[2])
        
        else:
            logger.warning(f"Cannot visualize {len(obj_indices)}-dimensional Pareto front")
            return
        
        plt.title("Pareto Front")
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        
        # Save plot if requested
        if output_dir is not None:
            os.makedirs(output_dir, exist_ok=True)
            plt.savefig(os.path.join(output_dir, "pareto_front.png"), dpi=300)
            
        # Show plot if requested
        if show_plot:
            plt.show()
        else:
            plt.close()
    
    def export(self, filepath: str) -> None:
        """
        Export the Pareto front data to a file.
        
        Args:
            filepath: Path to save the data
        """
        # Prepare data for export
        export_data = {
            "pareto_points": [
                {
                    "objectives": point[0].tolist(),
                    "variables": point[1]
                }
                for point in self.points
            ],
            "dominated_points": [
                {
                    "objectives": point[0].tolist(),
                    "variables": point[1]
                }
                for point in self.dominated_points
            ],
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "n_pareto_points": len(self.points),
                "n_dominated_points": len(self.dominated_points)
            }
        }
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        
        # Save to file
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=4)
            
        logger.info(f"Pareto front data exported to {filepath}")
    
    @classmethod
    def load(cls, filepath: str) -> 'ParetoFront':
        """
        Load a previously exported Pareto front.
        
        Args:
            filepath: Path to the saved data
            
        Returns:
            Loaded ParetoFront object
        """
        # Load from file
        with open(filepath, 'r') as f:
            data = json.load(f)
            
        # Create new instance
        pareto_front = cls()
        
        # Load Pareto points
        for point_data in data["pareto_points"]:
            objectives = np.array(point_data["objectives"])
            variables = point_data["variables"]
            pareto_front.points.append((objectives, variables))
            
        # Load dominated points
        for point_data in data["dominated_points"]:
            objectives = np.array(point_data["objectives"])
            variables = point_data["variables"]
            pareto_front.dominated_points.append((objectives, variables))
            
        logger.info(f"Loaded Pareto front with {len(pareto_front.points)} points from {filepath}")
        
        return pareto_front

class NSGA2:
    """
    Implementation of the Non-dominated Sorting Genetic Algorithm II (NSGA-II) 
    for multi-objective optimization.
    """
    def __init__(self, population_size: int = 100,
                 crossover_prob: float = 0.8,
                 mutation_prob: float = 0.2,
                 mutation_scale: float = 0.1,
                 tournament_size: int = 2):
        """
        Initialize the NSGA-II optimizer.
        
        Args:
            population_size: Size of the population
            crossover_prob: Probability of crossover
            mutation_prob: Probability of mutation
            mutation_scale: Scale of mutation relative to bounds
            tournament_size: Size of tournament for selection
        """
        self.population_size = population_size
        self.crossover_prob = crossover_prob
        self.mutation_prob = mutation_prob
        self.mutation_scale = mutation_scale
        self.tournament_size = tournament_size
        
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
    
    def _fast_non_dominated_sort(self, objectives: np.ndarray) -> List[List[int]]:
        """
        Fast non-dominated sorting algorithm from NSGA-II.
        
        Args:
            objectives: Array of objective values for each individual
            
        Returns:
            List of fronts, where each front is a list of indices
        """
        n_pop = objectives.shape[0]
        n_objectives = objectives.shape[1]
        
        # Initialize domination counts and dominated sets
        domination_count = np.zeros(n_pop, dtype=int)
        dominated_sets = [[] for _ in range(n_pop)]
        fronts = [[]]
        
        # Compute domination counts and dominated sets
        for i in range(n_pop):
            for j in range(n_pop):
                if i == j:
                    continue
                
                # Check if i dominates j
                if np.all(objectives[i] <= objectives[j]) and np.any(objectives[i] < objectives[j]):
                    dominated_sets[i].append(j)
                # Check if j dominates i
                elif np.all(objectives[j] <= objectives[i]) and np.any(objectives[j] < objectives[i]):
                    domination_count[i] += 1
            
            # If i is not dominated by anyone, add to first front
            if domination_count[i] == 0:
                fronts[0].append(i)
        
        # Compute subsequent fronts
        front_index = 0
        
        while fronts[front_index]:
            next_front = []
            
            for i in fronts[front_index]:
                for j in dominated_sets[i]:
                    domination_count[j] -= 1
                    
                    if domination_count[j] == 0:
                        next_front.append(j)
            
            front_index += 1
            fronts.append(next_front)
        
        # Remove last empty front
        fronts.pop()
        
        return fronts
    
    def _crowding_distance(self, objectives: np.ndarray, front: List[int]) -> np.ndarray:
        """
        Compute crowding distance for points in a front.
        
        Args:
            objectives: Array of objective values for each individual
            front: List of indices in the front
            
        Returns:
            Array of crowding distances for individuals in the front
        """
        n_points = len(front)
        n_objectives = objectives.shape[1]
        
        if n_points <= 2:
            # If only 1 or 2 points, assign infinite distance
            return np.full(n_points, np.inf)
        
        # Extract objectives for points in the front
        front_obj = objectives[front]
        
        # Initialize crowding distances
        distances = np.zeros(n_points)
        
        # Compute crowding distance for each objective
        for obj_idx in range(n_objectives):
            # Sort by this objective
            sorted_indices = np.argsort(front_obj[:, obj_idx])
            
            # Set boundary points to infinity
            distances[sorted_indices[0]] = np.inf
            distances[sorted_indices[-1]] = np.inf
            
            # Normalize objective range
            obj_range = front_obj[sorted_indices[-1], obj_idx] - front_obj[sorted_indices[0], obj_idx]
            
            if obj_range > 0:
                # Compute distances for intermediate points
                for i in range(1, n_points - 1):
                    idx = sorted_indices[i]
                    prev_idx = sorted_indices[i - 1]
                    next_idx = sorted_indices[i + 1]
                    
                    # Accumulate normalized distance
                    distances[idx] += (front_obj[next_idx, obj_idx] - front_obj[prev_idx, obj_idx]) / obj_range
        
        return distances
    
    def _crowded_comparison(self, i: int, j: int, ranks: np.ndarray, distances: np.ndarray) -> int:
        """
        Crowded comparison operator for selection.
        
        Args:
            i: Index of first individual
            j: Index of second individual
            ranks: Array of front ranks for each individual
            distances: Array of crowding distances for each individual
            
        Returns:
            -1 if i is better, 1 if j is better, 0 if equal
        """
        if ranks[i] < ranks[j]:  # i has better rank
            return -1
        elif ranks[i] > ranks[j]:  # j has better rank
            return 1
        else:  # Same rank, compare crowding distance
            if distances[i] > distances[j]:  # i is less crowded
                return -1
            elif distances[i] < distances[j]:  # j is less crowded
                return 1
            else:  # Equal crowding
                return 0
    
    def tournament_selection(self, ranks: np.ndarray, distances: np.ndarray) -> List[int]:
        """
        Perform tournament selection based on ranks and crowding distances.
        
        Args:
            ranks: Array of front ranks for each individual
            distances: Array of crowding distances for each individual
            
        Returns:
            List of selected parent indices
        """
        n_pop = len(ranks)
        selected = []
        
        for _ in range(n_pop):
            # Randomly select tournament candidates
            candidates = np.random.choice(n_pop, self.tournament_size, replace=False)
            
            # Initialize winner as first candidate
            winner = candidates[0]
            
            # Compare with other candidates
            for candidate in candidates[1:]:
                comparison = self._crowded_comparison(candidate, winner, ranks, distances)
                if comparison < 0:  # Candidate is better
                    winner = candidate
            
            selected.append(winner)
        
        return selected
    
    def crossover(self, population: np.ndarray, parents: List[int]) -> np.ndarray:
        """
        Perform crossover to create offspring.
        
        Args:
            population: Current population
            parents: Indices of selected parents
            
        Returns:
            Offspring population
        """
        n_pop, n_vars = population.shape
        offspring = np.zeros_like(population)
        
        for i in range(0, n_pop, 2):
            parent1_idx = parents[i % len(parents)]
            parent2_idx = parents[(i + 1) % len(parents)]
            
            parent1 = population[parent1_idx]
            parent2 = population[parent2_idx]
            
            if np.random.random() < self.crossover_prob:
                # Simulated Binary Crossover (SBX)
                u = np.random.random(n_vars)
                
                # Spread factor parameter
                eta_c = 20.0
                beta = np.zeros(n_vars)
                
                # Calculate beta for each variable
                for j in range(n_vars):
                    if u[j] <= 0.5:
                        beta[j] = (2 * u[j]) ** (1 / (eta_c + 1))
                    else:
                        beta[j] = (1 / (2 * (1 - u[j]))) ** (1 / (eta_c + 1))
                
                # Generate children
                offspring[i] = 0.5 * ((1 + beta) * parent1 + (1 - beta) * parent2)
                offspring[i+1] = 0.5 * ((1 - beta) * parent1 + (1 + beta) * parent2)
            else:
                # No crossover
                offspring[i] = parent1.copy()
                offspring[i+1] = parent2.copy()
        
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
        
        # Polynomial mutation
        eta_m = 20.0
        
        for i in range(n_pop):
            for j in range(n_vars):
                if np.random.random() < self.mutation_prob:
                    # Calculate delta based on polynomial mutation
                    u = np.random.random()
                    
                    if u <= 0.5:
                        delta = (2 * u) ** (1 / (eta_m + 1)) - 1
                    else:
                        delta = 1 - (2 * (1 - u)) ** (1 / (eta_m + 1))
                    
                    # Apply mutation
                    range_j = ub[j] - lb[j]
                    population[i, j] += delta * self.mutation_scale * range_j
                    
                    # Ensure bounds are respected
                    population[i, j] = max(lb[j], min(ub[j], population[i, j]))
        
        return population
    
    def optimize(self, problem, max_generations: int = 100, 
                x0: np.ndarray = None, 
                callback: Callable = None) -> Dict:
        """
        Run the NSGA-II optimization algorithm.
        
        Args:
            problem: The optimization problem (must have multiple objectives)
            max_generations: Maximum number of generations
            x0: Initial point (if provided, included in initial population)
            callback: Callback function called after each generation
            
        Returns:
            Dictionary with optimization results
        """
        from .optimizer import OptimizationProblem
        
        if not isinstance(problem, OptimizationProblem):
            raise TypeError("Problem must be an OptimizationProblem instance")
        
        if len(problem.objectives) < 2:
            raise ValueError("NSGA-II requires at least two objectives")
        
        # Get problem dimensions
        n_vars = len(problem.design_variables)
        n_objectives = len(problem.objectives)
        lb, ub = problem.get_bounds()
        
        # Initialize population
        population = self.initialize_population(n_vars, lb, ub)
        
        # Include initial guess if provided
        if x0 is not None:
            population[0] = x0.copy()
        
        # Initialize history and Pareto front
        history = {
            'generations': [],
            'pareto_front': []
        }
        
        pareto_front = ParetoFront()
        
        # Start timer
        start_time = datetime.now()
        
        # Evaluate initial population
        objectives = np.zeros((self.population_size, n_objectives))
        constraint_violations = np.zeros(self.population_size)
        
        obj_names = list(problem.objectives.keys())
        
        for i in range(self.population_size):
            # Evaluate individual
            results = problem.evaluate(population[i])
            
            # Extract objective values
            for j, name in enumerate(obj_names):
                objectives[i, j] = results[f"obj_{name}"]
            
            # Compute constraint violation
            for name, constraint in problem.constraints.items():
                constraint_value = results[f"con_{name}"]
                
                if constraint.constraint_type == 'equality':
                    constraint_violations[i] += abs(constraint_value)
                else:  # Inequality constraint
                    if constraint.lower_bound is not None and constraint_value < constraint.lower_bound:
                        constraint_violations[i] += constraint.lower_bound - constraint_value
                    if constraint.upper_bound is not None and constraint_value > constraint.upper_bound:
                        constraint_violations[i] += constraint_value - constraint.upper_bound
        
        # Main optimization loop
        for generation in range(max_generations):
            # Perform non-dominated sorting
            fronts = self._fast_non_dominated_sort(objectives)
            
            # Compute crowding distances for each front
            distances = np.zeros(self.population_size)
            ranks = np.zeros(self.population_size, dtype=int)
            
            for i, front in enumerate(fronts):
                # Assign rank to individuals in this front
                for idx in front:
                    ranks[idx] = i
                
                # Compute crowding distances
                front_distances = self._crowding_distance(objectives, front)
                
                for j, idx in enumerate(front):
                    distances[idx] = front_distances[j]
            
            # Update history
            history['generations'].append(generation)
            
            # Update Pareto front
            for i in range(self.population_size):
                if ranks[i] == 0:  # First front (non-dominated)
                    # Convert to original variable values
                    x_dict = {}
                    for j, (name, var) in enumerate(problem.design_variables.items()):
                        x_dict[name] = var.denormalize(population[i, j])
                    
                    pareto_front.add_point(objectives[i], x_dict)
            
            # Store current Pareto front
            history['pareto_front'].append(pareto_front.get_pareto_points())
            
            # Call callback if provided
            if callback is not None:
                callback(generation, pareto_front)
            
            # Log progress
            if generation % 10 == 0:
                logger.info(f"Generation {generation}: {len(fronts[0])} points on Pareto front")
            
            # Check termination
            if generation == max_generations - 1:
                break
            
            # Selection, crossover, and mutation to create new population
            # 1. Select parents using tournament selection
            parents = self.tournament_selection(ranks, distances)
            
            # 2. Crossover
            offspring = self.crossover(population, parents)
            
            # 3. Mutation
            offspring = self.mutation(offspring, lb, ub)
            
            # 4. Evaluate offspring
            offspring_objectives = np.zeros((self.population_size, n_objectives))
            offspring_violations = np.zeros(self.population_size)
            
            for i in range(self.population_size):
                # Evaluate individual
                results = problem.evaluate(offspring[i])
                
                # Extract objective values
                for j, name in enumerate(obj_names):
                    offspring_objectives[i, j] = results[f"obj_{name}"]
                
                # Compute constraint violation
                for name, constraint in problem.constraints.items():
                    constraint_value = results[f"con_{name}"]
                    
                    if constraint.constraint_type == 'equality':
                        offspring_violations[i] += abs(constraint_value)
                    else:  # Inequality constraint
                        if constraint.lower_bound is not None and constraint_value < constraint.lower_bound:
                            offspring_violations[i] += constraint.lower_bound - constraint_value
                        if constraint.upper_bound is not None and constraint_value > constraint.upper_bound:
                            offspring_violations[i] += constraint_value - constraint.upper_bound
            
            # 5. Combine parent and offspring populations
            combined_pop = np.vstack((population, offspring))
            combined_obj = np.vstack((objectives, offspring_objectives))
            combined_violations = np.hstack((constraint_violations, offspring_violations))
            
            # 6. Perform non-dominated sorting on combined population
            combined_fronts = self._fast_non_dominated_sort(combined_obj)
            
            # 7. Select next generation based on fronts and crowding distance
            new_population = np.zeros_like(population)
            new_objectives = np.zeros_like(objectives)
            new_violations = np.zeros_like(constraint_violations)
            
            # Fill new population front by front
            next_gen_size = 0
            front_idx = 0
            
            while next_gen_size + len(combined_fronts[front_idx]) <= self.population_size:
                # Add entire front
                for idx in combined_fronts[front_idx]:
                    new_population[next_gen_size] = combined_pop[idx]
                    new_objectives[next_gen_size] = combined_obj[idx]
                    new_violations[next_gen_size] = combined_violations[idx]
                    next_gen_size += 1
                
                front_idx += 1
                
                if front_idx >= len(combined_fronts):
                    break
            
            # If we need more individuals to fill the population
            if next_gen_size < self.population_size and front_idx < len(combined_fronts):
                # Compute crowding distance for the last considered front
                last_front = combined_fronts[front_idx]
                last_front_distances = self._crowding_distance(combined_obj, last_front)
                
                # Sort the front by crowding distance (descending)
                sorted_indices = np.argsort(-last_front_distances)
                
                # Add individuals from the front until the population is filled
                for i in range(self.population_size - next_gen_size):
                    idx = last_front[sorted_indices[i]]
                    new_population[next_gen_size] = combined_pop[idx]
                    new_objectives[next_gen_size] = combined_obj[idx]
                    new_violations[next_gen_size] = combined_violations[idx]
                    next_gen_size += 1
            
            # Update population for next generation
            population = new_population
            objectives = new_objectives
            constraint_violations = new_violations
        
        # End time
        end_time = datetime.now()
        
        # Package results
        results = {
            'pareto_front': pareto_front,
            'history': history,
            'n_generations': max_generations,
            'n_function_evals': max_generations * self.population_size * 2,  # Parent + offspring
            'time': (end_time - start_time).total_seconds(),
        }
        
        return results

class MOEADDE:
    """
    Multi-Objective Evolutionary Algorithm with Decomposition (MOEA/D) using
    Differential Evolution. This algorithm decomposes a multi-objective problem
    into multiple scalar subproblems and optimizes them simultaneously.
    """
    def __init__(self, 
                 n_neighbors: int = 20,
                 de_f: float = 0.5,
                 de_cr: float = 0.8,
                 decomposition: str = 'tchebycheff',
                 weight_generation: str = 'uniform'):
        """
        Initialize the MOEA/D-DE optimizer.
        
        Args:
            n_neighbors: Number of neighbors for each subproblem
            de_f: Differential evolution scaling factor
            de_cr: Differential evolution crossover rate
            decomposition: Decomposition method ('tchebycheff', 'weighted_sum', 'pbi')
            weight_generation: Method to generate weight vectors ('uniform', 'systematic')
        """
        self.n_neighbors = n_neighbors
        self.de_f = de_f
        self.de_cr = de_cr
        self.decomposition = decomposition
        self.weight_generation = weight_generation
    
    def _generate_weights(self, n_objectives: int, n_weights: int) -> np.ndarray:
        """
        Generate weight vectors for decomposition.
        
        Args:
            n_objectives: Number of objectives
            n_weights: Number of weight vectors to generate
            
        Returns:
            Array of weight vectors of shape (n_weights, n_objectives)
        """
        if self.weight_generation == 'uniform':
            # Simple uniform sampling
            weights = np.random.random((n_weights, n_objectives))
            # Normalize to sum to 1
            return weights / np.sum(weights, axis=1, keepdims=True)
        
        elif self.weight_generation == 'systematic':
            # For two objectives, evenly distribute weights
            if n_objectives == 2:
                weights = np.zeros((n_weights, n_objectives))
                for i in range(n_weights):
                    weights[i, 0] = i / (n_weights - 1)
                    weights[i, 1] = 1 - weights[i, 0]
                return weights
            
            # For three objectives, use Das and Dennis's method
            elif n_objectives == 3:
                h = int(np.floor(np.power(n_weights * (n_objectives - 1) * np.math.factorial(n_objectives - 1), 1/(n_objectives - 1))))
                weights = []
                for i in range(h + 1):
                    for j in range(h + 1 - i):
                        k = h - i - j
                        weight = np.array([i, j, k]) / h
                        weights.append(weight)
                
                # If we have too many weights, sample randomly
                if len(weights) > n_weights:
                    indices = np.random.choice(len(weights), n_weights, replace=False)
                    weights = [weights[i] for i in indices]
                
                return np.array(weights)
            
            # For more objectives, use random generation as a fallback
            else:
                logger.warning(f"Systematic weight generation not implemented for {n_objectives} objectives. Using uniform sampling.")
                return self._generate_weights(n_objectives, n_weights)
        
        else:
            raise ValueError(f"Unknown weight generation method: {self.weight_generation}")
    
    def _compute_neighborhoods(self, weights: np.ndarray) -> List[List[int]]:
        """
        Compute neighborhoods for each subproblem based on weight vector distances.
        
        Args:
            weights: Array of weight vectors
            
        Returns:
            List of lists, where each list contains indices of neighbors
        """
        n_weights = weights.shape[0]
        distances = np.zeros((n_weights, n_weights))
        
        # Compute distances between weight vectors
        for i in range(n_weights):
            for j in range(i, n_weights):
                d = np.linalg.norm(weights[i] - weights[j])
                distances[i, j] = d
                distances[j, i] = d
        
        # Find n_neighbors closest weights for each weight vector
        neighborhoods = []
        for i in range(n_weights):
            # Get indices of neighbors sorted by distance
            neighbor_indices = np.argsort(distances[i])[:self.n_neighbors]
            neighborhoods.append(neighbor_indices.tolist())
        
        return neighborhoods
    
    def _decompose(self, f: np.ndarray, weights: np.ndarray, z_ideal: np.ndarray) -> float:
        """
        Apply decomposition method to convert vector objective to scalar.
        
        Args:
            f: Objective function values
            weights: Weight vector
            z_ideal: Ideal point (best values for each objective)
            
        Returns:
            Scalar value representing aggregate objective
        """
        if self.decomposition == 'weighted_sum':
            # Simple weighted sum of objectives
            return np.sum(weights * f)
        
        elif self.decomposition == 'tchebycheff':
            # Tchebycheff approach (minimize maximum weighted deviation)
            # Add small epsilon to avoid division by zero
            epsilon = 1e-6
            weighted_deviations = weights * np.abs(f - z_ideal + epsilon)
            return np.max(weighted_deviations)
        
        elif self.decomposition == 'pbi':
            # Penalty-based Boundary Intersection
            # Projection of vector onto weight direction and perpendicular distance
            theta = 5.0  # Penalty parameter
            
            # Normalize weights
            norm_weights = weights / np.linalg.norm(weights) if np.linalg.norm(weights) > 0 else weights
            
            # Calculate d1 (distance along weight vector)
            d1 = np.dot(f - z_ideal, norm_weights)
            
            # Calculate d2 (perpendicular distance)
            d2 = np.linalg.norm((f - z_ideal) - d1 * norm_weights)
            
            # Aggregate with penalty
            return d1 + theta * d2
        
        else:
            raise ValueError(f"Unknown decomposition method: {self.decomposition}")
    
    def differential_evolution(self, 
                               x: np.ndarray, 
                               population: np.ndarray, 
                               lb: np.ndarray, 
                               ub: np.ndarray) -> np.ndarray:
        """
        Apply differential evolution operator to create a new solution.
        
        Args:
            x: Current solution
            population: Current population
            lb: Lower bounds
            ub: Upper bounds
            
        Returns:
            New solution
        """
        n_pop, n_vars = population.shape
        
        # Randomly select three distinct individuals, different from current x
        indices = np.random.choice(n_pop, 3, replace=False)
        
        # DE/rand/1 mutation
        y = population[indices[0]] + self.de_f * (population[indices[1]] - population[indices[2]])
        
        # Binomial crossover
        mask = np.random.random(n_vars) < self.de_cr
        # Ensure at least one component is inherited from the mutant
        if not np.any(mask):
            mask[np.random.randint(0, n_vars)] = True
        
        # Create offspring
        y_new = np.copy(x)
        y_new[mask] = y[mask]
        
        # Ensure bounds are respected
        y_new = np.clip(y_new, lb, ub)
        
        return y_new
    
    def optimize(self, problem, n_iterations: int = 100, 
                population_size: int = None,
                x0: np.ndarray = None,
                callback: Callable = None) -> Dict:
        """
        Run the MOEA/D-DE optimization algorithm.
        
        Args:
            problem: The optimization problem (must have multiple objectives)
            n_iterations: Maximum number of iterations
            population_size: Population size (if None, set to 100 or 10x number of variables)
            x0: Initial point (if provided, included in initial population)
            callback: Callback function called after each iteration
            
        Returns:
            Dictionary with optimization results
        """
        from .optimizer import OptimizationProblem
        
        if not isinstance(problem, OptimizationProblem):
            raise TypeError("Problem must be an OptimizationProblem instance")
        
        if len(problem.objectives) < 2:
            raise ValueError("MOEA/D requires at least two objectives")
        
        # Get problem dimensions
        n_vars = len(problem.design_variables)
        n_objectives = len(problem.objectives)
        lb, ub = problem.get_bounds()
        
        # Set population size if not provided
        if population_size is None:
            population_size = max(100, 10 * n_vars)
        
        # Generate weight vectors
        weights = self._generate_weights(n_objectives, population_size)
        
        # Compute neighborhoods
        neighborhoods = self._compute_neighborhoods(weights)
        
        # Initialize population
        population = np.random.random((population_size, n_vars)) * (ub - lb) + lb
        
        # Include initial guess if provided
        if x0 is not None:
            population[0] = x0.copy()
        
        # Evaluate initial population
        objectives = np.zeros((population_size, n_objectives))
        obj_names = list(problem.objectives.keys())
        
        for i in range(population_size):
            # Evaluate individual
            results = problem.evaluate(population[i])
            
            # Extract objective values
            for j, name in enumerate(obj_names):
                objectives[i, j] = results[f"obj_{name}"]
        
        # Compute ideal point
        z_ideal = np.min(objectives, axis=0)
        
        # Compute initial fitness values for each subproblem
        fitness = np.zeros(population_size)
        for i in range(population_size):
            fitness[i] = self._decompose(objectives[i], weights[i], z_ideal)
        
        # Initialize Pareto front tracker
        pareto_front = ParetoFront()
        for i in range(population_size):
            # Convert to original variable values
            x_dict = {}
            for j, (name, var) in enumerate(problem.design_variables.items()):
                x_dict[name] = var.denormalize(population[i, j])
            
            pareto_front.add_point(objectives[i], x_dict)
        
        # Initialize history
        history = {
            'iterations': [],
            'ideal_point': [],
            'pareto_front': []
        }
        
        # Start timer
        start_time = datetime.now()
        
        # Main optimization loop
        for iteration in range(n_iterations):
            # Update each subproblem
            for i in range(population_size):
                # Select neighborhood indices
                if np.random.random() < 0.9:  # 90% chance to use neighborhood
                    neighbor_indices = neighborhoods[i]
                else:
                    # Use global population
                    neighbor_indices = list(range(population_size))
                
                # Generate new solution using DE
                y = self.differential_evolution(
                    population[i],
                    population[neighbor_indices],
                    lb, ub
                )
                
                # Evaluate new solution
                y_results = problem.evaluate(y)
                y_objectives = np.array([y_results[f"obj_{name}"] for name in obj_names])
                
                # Update ideal point
                if np.any(y_objectives < z_ideal):
                    z_ideal = np.minimum(z_ideal, y_objectives)
                    # Update history when ideal point changes
                    history['ideal_point'].append(z_ideal.copy())
                
                # Update neighboring subproblems
                for j in neighbor_indices:
                    # Calculate new aggregation function value
                    new_fitness = self._decompose(y_objectives, weights[j], z_ideal)
                    current_fitness = self._decompose(objectives[j], weights[j], z_ideal)
                    
                    # If new solution is better for this subproblem, update it
                    if new_fitness < current_fitness:
                        population[j] = y.copy()
                        objectives[j] = y_objectives.copy()
                        fitness[j] = new_fitness
                
                # Add new solution to Pareto front if non-dominated
                x_dict = {}
                for j, (name, var) in enumerate(problem.design_variables.items()):
                    x_dict[name] = var.denormalize(y[j])
                
                pareto_front.add_point(y_objectives, x_dict)
            
            # Update history
            history['iterations'].append(iteration)
            history['pareto_front'].append(pareto_front.get_pareto_points())
            
            # Call callback if provided
            if callback:
                callback(iteration, pareto_front, history)
            
            # Log progress
            if (iteration + 1) % 10 == 0 or iteration == 0 or iteration == n_iterations - 1:
                elapsed_time = (datetime.now() - start_time).total_seconds()
                logger.info(f"Iteration {iteration + 1}/{n_iterations} - "
                          f"Time: {elapsed_time:.2f}s - "
                          f"Pareto front size: {len(pareto_front.get_pareto_points())}")
        
        # Prepare final results
        results = {
            'pareto_front': pareto_front,
            'history': history,
            'population': population,
            'objectives': objectives,
            'weights': weights,
            'ideal_point': z_ideal,
            'runtime': (datetime.now() - start_time).total_seconds()
        }
        
        return results

# Example usage if this module is run directly
if __name__ == "__main__":
    # Create a test Pareto front
    pf = ParetoFront()
    
    # Add some points (objectives, variables)
    pf.add_point(np.array([1.0, 5.0]), {"x": 0.5, "y": 0.5})
    pf.add_point(np.array([2.0, 3.0]), {"x": 0.7, "y": 0.3})
    pf.add_point(np.array([3.0, 2.0]), {"x": 0.3, "y": 0.7})
    pf.add_point(np.array([5.0, 1.0]), {"x": 0.1, "y": 0.9})
    
    # Add a dominated point
    pf.add_point(np.array([2.5, 3.5]), {"x": 0.6, "y": 0.4})
    
    # Plot the Pareto front
    pf.plot(obj_names=["Cost", "Time"], show_dominated=True)
    
    # Export to file
    pf.export("test_pareto_front.json")
    
    # Load from file
    loaded_pf = ParetoFront.load("test_pareto_front.json")
    
    # Clean up test file
    import os
    os.remove("test_pareto_front.json")