"""
Surrogate modeling module for the Intake CFD Optimization Suite.

This module provides classes for creating and using surrogate models to
approximate expensive CFD simulations during optimization.
"""

import numpy as np
import logging
import os
import json
import pickle
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple, Union, Optional, Any, Callable
from abc import ABC, abstractmethod
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("surrogate_model")

class SurrogateModel(ABC):
    """
    Abstract base class for surrogate models.
    """
    def __init__(self, name: str = "Surrogate Model"):
        """
        Initialize the surrogate model.
        
        Args:
            name: Name of the surrogate model
        """
        self.name = name
        self.trained = False
        self.input_dim = None
        self.output_dim = None
        self.input_names = None
        self.output_names = None
        self.input_bounds = None
        
        # Training data
        self.X_train = None
        self.y_train = None
        
    def set_input_bounds(self, bounds: Dict[str, Tuple[float, float]]) -> None:
        """
        Set the bounds for the input variables.
        
        Args:
            bounds: Dictionary mapping input names to (lower, upper) bound tuples
        """
        self.input_bounds = bounds
        
    def set_input_output_names(self, input_names: List[str], output_names: List[str]) -> None:
        """
        Set names for input and output variables.
        
        Args:
            input_names: List of input variable names
            output_names: List of output variable names
        """
        self.input_names = input_names
        self.output_names = output_names
        self.input_dim = len(input_names)
        self.output_dim = len(output_names)
        
    def _normalize_inputs(self, X: np.ndarray) -> np.ndarray:
        """
        Normalize input data to [0, 1] range based on bounds.
        
        Args:
            X: Input data array of shape (n_samples, input_dim)
            
        Returns:
            Normalized input data
        """
        if self.input_bounds is None:
            logger.warning("Input bounds not set, using raw inputs")
            return X
            
        X_norm = np.zeros_like(X)
        
        for i, name in enumerate(self.input_names):
            if name in self.input_bounds:
                lb, ub = self.input_bounds[name]
                # Avoid division by zero if bounds are the same
                if ub == lb:
                    X_norm[:, i] = 0.5
                else:
                    X_norm[:, i] = (X[:, i] - lb) / (ub - lb)
            else:
                logger.warning(f"Bounds not found for input {name}, using raw values")
                X_norm[:, i] = X[:, i]
                
        return X_norm
        
    def _denormalize_inputs(self, X_norm: np.ndarray) -> np.ndarray:
        """
        Denormalize input data from [0, 1] range to original range.
        
        Args:
            X_norm: Normalized input data
            
        Returns:
            Denormalized input data
        """
        if self.input_bounds is None:
            logger.warning("Input bounds not set, using raw inputs")
            return X_norm
            
        X = np.zeros_like(X_norm)
        
        for i, name in enumerate(self.input_names):
            if name in self.input_bounds:
                lb, ub = self.input_bounds[name]
                X[:, i] = lb + X_norm[:, i] * (ub - lb)
            else:
                X[:, i] = X_norm[:, i]
                
        return X
        
    def _prepare_training_data(self, X: Union[np.ndarray, Dict[str, np.ndarray]], 
                              y: Union[np.ndarray, Dict[str, np.ndarray]]) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare training data for the surrogate model.
        
        Args:
            X: Input data as array or dictionary
            y: Output data as array or dictionary
            
        Returns:
            Tuple of (X_array, y_array)
        """
        # Convert dictionary input to array if needed
        if isinstance(X, dict):
            if self.input_names is None:
                self.input_names = list(X.keys())
                self.input_dim = len(self.input_names)
                
            X_array = np.column_stack([X[name] for name in self.input_names])
        else:
            X_array = X
            
        # Convert dictionary output to array if needed
        if isinstance(y, dict):
            if self.output_names is None:
                self.output_names = list(y.keys())
                self.output_dim = len(self.output_names)
                
            y_array = np.column_stack([y[name] for name in self.output_names])
        else:
            y_array = y
            
        # Check dimensions
        if X_array.ndim == 1:
            X_array = X_array.reshape(-1, 1)
            
        if y_array.ndim == 1:
            y_array = y_array.reshape(-1, 1)
            
        # Set dimensions if not already set
        if self.input_dim is None:
            self.input_dim = X_array.shape[1]
            
        if self.output_dim is None:
            self.output_dim = y_array.shape[1]
            
        # Check that dimensions match expected values
        if X_array.shape[1] != self.input_dim:
            raise ValueError(f"Input data has {X_array.shape[1]} dimensions, expected {self.input_dim}")
            
        if y_array.shape[1] != self.output_dim:
            raise ValueError(f"Output data has {y_array.shape[1]} dimensions, expected {self.output_dim}")
            
        return X_array, y_array
        
    @abstractmethod
    def train(self, X: Union[np.ndarray, Dict[str, np.ndarray]], 
              y: Union[np.ndarray, Dict[str, np.ndarray]], **kwargs) -> None:
        """
        Train the surrogate model on the given data.
        
        Args:
            X: Input data as array or dictionary
            y: Output data as array or dictionary
            **kwargs: Additional model-specific training parameters
        """
        pass
        
    @abstractmethod
    def predict(self, X: Union[np.ndarray, Dict[str, np.ndarray]]) -> Union[np.ndarray, Dict[str, np.ndarray]]:
        """
        Make predictions using the surrogate model.
        
        Args:
            X: Input data as array or dictionary
            
        Returns:
            Predictions as array or dictionary
        """
        pass
        
    def score(self, X: Union[np.ndarray, Dict[str, np.ndarray]], 
             y: Union[np.ndarray, Dict[str, np.ndarray]]) -> Dict[str, float]:
        """
        Compute the coefficient of determination R^2 for the model.
        
        Args:
            X: Input data
            y: True output data
            
        Returns:
            Dictionary of R^2 scores for each output
        """
        if not self.trained:
            raise ValueError("Model must be trained before calculating score")
            
        # Prepare data
        X_array, y_array = self._prepare_training_data(X, y)
        
        # Make predictions
        y_pred = self.predict(X_array)
        
        # Calculate R^2 for each output dimension
        r2_scores = {}
        
        for i in range(self.output_dim):
            y_true_i = y_array[:, i]
            y_pred_i = y_pred[:, i]
            
            # Calculate R^2
            ss_total = np.sum((y_true_i - np.mean(y_true_i)) ** 2)
            ss_residual = np.sum((y_true_i - y_pred_i) ** 2)
            
            if ss_total < 1e-10:  # Avoid division by zero
                r2 = 1.0
            else:
                r2 = 1 - (ss_residual / ss_total)
                
            # Store in dictionary
            if self.output_names is not None:
                r2_scores[self.output_names[i]] = r2
            else:
                r2_scores[f"output_{i}"] = r2
                
        # Overall R^2
        r2_scores["overall"] = np.mean(list(r2_scores.values()))
        
        return r2_scores
        
    def cross_validate(self, X: Union[np.ndarray, Dict[str, np.ndarray]], 
                      y: Union[np.ndarray, Dict[str, np.ndarray]], 
                      n_folds: int = 5, **kwargs) -> Dict[str, List[float]]:
        """
        Perform k-fold cross-validation on the model.
        
        Args:
            X: Input data
            y: Output data
            n_folds: Number of folds for cross-validation
            **kwargs: Additional model-specific training parameters
            
        Returns:
            Dictionary of cross-validation scores
        """
        # Prepare data
        X_array, y_array = self._prepare_training_data(X, y)
        
        # Number of samples
        n_samples = X_array.shape[0]
        
        # Generate random indices
        indices = np.random.permutation(n_samples)
        fold_size = n_samples // n_folds
        
        # Initialize scores
        cv_scores = {f"fold_{i+1}": [] for i in range(n_folds)}
        cv_scores["average"] = []
        
        # Perform k-fold cross-validation
        for i in range(n_folds):
            # Test indices for this fold
            test_indices = indices[i*fold_size:(i+1)*fold_size]
            
            # Training indices (all except test)
            train_indices = np.concatenate([
                indices[:i*fold_size],
                indices[(i+1)*fold_size:]
            ])
            
            # Split data
            X_train = X_array[train_indices]
            y_train = y_array[train_indices]
            X_test = X_array[test_indices]
            y_test = y_array[test_indices]
            
            # Train model on training data
            self.train(X_train, y_train, **kwargs)
            
            # Score on test data
            fold_scores = self.score(X_test, y_test)
            
            # Store scores
            cv_scores[f"fold_{i+1}"] = fold_scores
            
        # Calculate average scores
        output_names = list(cv_scores["fold_1"].keys())
        avg_scores = {name: np.mean([cv_scores[f"fold_{i+1}"][name] for i in range(n_folds)]) 
                    for name in output_names}
        cv_scores["average"] = avg_scores
        
        return cv_scores
        
    def plot_prediction(self, X: Union[np.ndarray, Dict[str, np.ndarray]], 
                       y: Union[np.ndarray, Dict[str, np.ndarray]], 
                       output_dir: Optional[str] = None,
                       show_plot: bool = True) -> None:
        """
        Plot predictions against true values.
        
        Args:
            X: Input data
            y: True output data
            output_dir: Directory to save plots (if None, don't save)
            show_plot: Whether to display the plot
        """
        if not self.trained:
            raise ValueError("Model must be trained before plotting predictions")
            
        # Prepare data
        X_array, y_array = self._prepare_training_data(X, y)
        
        # Make predictions
        y_pred = self.predict(X_array)
        
        # Create output directory if needed
        if output_dir is not None:
            os.makedirs(output_dir, exist_ok=True)
            
        # Plot each output dimension
        for i in range(self.output_dim):
            y_true_i = y_array[:, i]
            y_pred_i = y_pred[:, i]
            
            # Get output name
            if self.output_names is not None:
                output_name = self.output_names[i]
            else:
                output_name = f"output_{i}"
                
            # Calculate R^2
            ss_total = np.sum((y_true_i - np.mean(y_true_i)) ** 2)
            ss_residual = np.sum((y_true_i - y_pred_i) ** 2)
            
            if ss_total < 1e-10:  # Avoid division by zero
                r2 = 1.0
            else:
                r2 = 1 - (ss_residual / ss_total)
                
            # Plot true vs. predicted
            plt.figure(figsize=(8, 6))
            plt.scatter(y_true_i, y_pred_i, alpha=0.7)
            
            # Add diagonal line (perfect predictions)
            min_val = min(np.min(y_true_i), np.min(y_pred_i))
            max_val = max(np.max(y_true_i), np.max(y_pred_i))
            plt.plot([min_val, max_val], [min_val, max_val], 'r--')
            
            plt.xlabel(f"True {output_name}")
            plt.ylabel(f"Predicted {output_name}")
            plt.title(f"{self.name}: True vs. Predicted {output_name} (R² = {r2:.4f})")
            plt.grid(True)
            plt.tight_layout()
            
            # Save plot if requested
            if output_dir is not None:
                plt.savefig(os.path.join(output_dir, f"prediction_{output_name}.png"), dpi=300)
                
            # Show plot if requested
            if show_plot:
                plt.show()
            else:
                plt.close()
                
        # Plot error histogram
        for i in range(self.output_dim):
            y_true_i = y_array[:, i]
            y_pred_i = y_pred[:, i]
            
            # Get output name
            if self.output_names is not None:
                output_name = self.output_names[i]
            else:
                output_name = f"output_{i}"
                
            # Calculate error
            error = y_true_i - y_pred_i
            
            # Plot error histogram
            plt.figure(figsize=(8, 6))
            plt.hist(error, bins=20, alpha=0.7)
            plt.xlabel(f"Error in {output_name}")
            plt.ylabel("Frequency")
            plt.title(f"{self.name}: Error Distribution for {output_name}")
            plt.grid(True)
            plt.tight_layout()
            
            # Save plot if requested
            if output_dir is not None:
                plt.savefig(os.path.join(output_dir, f"error_hist_{output_name}.png"), dpi=300)
                
            # Show plot if requested
            if show_plot:
                plt.show()
            else:
                plt.close()
                
    def save(self, filepath: str) -> None:
        """
        Save the surrogate model to a file.
        
        Args:
            filepath: Path to save the model
        """
        # Create model metadata
        metadata = {
            "name": self.name,
            "type": type(self).__name__,
            "input_dim": self.input_dim,
            "output_dim": self.output_dim,
            "input_names": self.input_names,
            "output_names": self.output_names,
            "input_bounds": self.input_bounds,
            "trained": self.trained,
            "timestamp": datetime.now().isoformat()
        }
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        
        # Save model-specific attributes
        model_data = self._get_save_data()
        
        # Combine metadata and model data
        save_data = {
            "metadata": metadata,
            "model_data": model_data
        }
        
        # Save to file
        with open(filepath, 'wb') as f:
            pickle.dump(save_data, f)
            
        logger.info(f"Model saved to {filepath}")
        
    @abstractmethod
    def _get_save_data(self) -> Dict[str, Any]:
        """
        Get model-specific data to save.
        
        Returns:
            Dictionary of model-specific data
        """
        pass
        
    @classmethod
    def load(cls, filepath: str) -> 'SurrogateModel':
        """
        Load a surrogate model from a file.
        
        Args:
            filepath: Path to the saved model
            
        Returns:
            Loaded surrogate model
        """
        # Load data from file
        with open(filepath, 'rb') as f:
            save_data = pickle.load(f)
            
        # Extract metadata and model data
        metadata = save_data["metadata"]
        model_data = save_data["model_data"]
        
        # Check if the model type matches
        if metadata["type"] != cls.__name__:
            logger.warning(f"Loaded model type ({metadata['type']}) doesn't match "
                         f"current class ({cls.__name__}). This may cause issues.")
            
        # Create new instance
        model = cls(name=metadata["name"])
        
        # Set common attributes
        model.input_dim = metadata["input_dim"]
        model.output_dim = metadata["output_dim"]
        model.input_names = metadata["input_names"]
        model.output_names = metadata["output_names"]
        model.input_bounds = metadata["input_bounds"]
        model.trained = metadata["trained"]
        
        # Load model-specific data
        model._set_load_data(model_data)
        
        logger.info(f"Model loaded from {filepath}")
        
        return model
        
    @abstractmethod
    def _set_load_data(self, model_data: Dict[str, Any]) -> None:
        """
        Set model-specific data when loading.
        
        Args:
            model_data: Dictionary of model-specific data
        """
        pass

class PolynomialSurrogate(SurrogateModel):
    """
    Polynomial regression surrogate model.
    """
    def __init__(self, degree: int = 2, name: str = "Polynomial Surrogate"):
        """
        Initialize the polynomial surrogate model.
        
        Args:
            degree: Polynomial degree
            name: Model name
        """
        super().__init__(name=name)
        self.degree = degree
        self.coefficients = None
        
    def _compute_polynomial_features(self, X: np.ndarray) -> np.ndarray:
        """
        Compute polynomial features from input data.
        
        Args:
            X: Input data of shape (n_samples, input_dim)
            
        Returns:
            Polynomial features of shape (n_samples, n_features)
        """
        n_samples, n_features = X.shape
        
        # For degree 1, just return the original features
        if self.degree == 1:
            return X
            
        # For higher degrees, compute polynomial features
        # Start with original features and bias term
        poly_features = [np.ones((n_samples, 1)), X]
        
        # Add higher-degree terms
        for d in range(2, self.degree + 1):
            # Add terms x_i^d
            for i in range(n_features):
                term = X[:, i:i+1] ** d
                poly_features.append(term)
                
            # Add interaction terms x_i^a * x_j^b where a+b=d
            if n_features > 1:
                for i in range(n_features):
                    for j in range(i+1, n_features):
                        for a in range(1, d):
                            b = d - a
                            term = (X[:, i:i+1] ** a) * (X[:, j:j+1] ** b)
                            poly_features.append(term)
                            
        # Concatenate all features
        return np.hstack(poly_features)
        
    def train(self, X: Union[np.ndarray, Dict[str, np.ndarray]], 
              y: Union[np.ndarray, Dict[str, np.ndarray]], **kwargs) -> None:
        """
        Train the polynomial surrogate model.
        
        Args:
            X: Input data as array or dictionary
            y: Output data as array or dictionary
            **kwargs: Additional training parameters (ignored)
        """
        # Prepare training data
        X_array, y_array = self._prepare_training_data(X, y)
        
        # Store training data
        self.X_train = X_array.copy()
        self.y_train = y_array.copy()
        
        # Normalize inputs
        X_norm = self._normalize_inputs(X_array)
        
        # Compute polynomial features
        X_poly = self._compute_polynomial_features(X_norm)
        
        # Initialize coefficients
        self.coefficients = np.zeros((X_poly.shape[1], self.output_dim))
        
        # Fit model using least squares for each output dimension
        for i in range(self.output_dim):
            # Get output data for this dimension
            y_i = y_array[:, i]
            
            # Solve normal equations using pseudo-inverse
            self.coefficients[:, i] = np.linalg.pinv(X_poly) @ y_i
            
        self.trained = True
        logger.info(f"Trained polynomial surrogate model of degree {self.degree}")
        
    def predict(self, X: Union[np.ndarray, Dict[str, np.ndarray]]) -> Union[np.ndarray, Dict[str, np.ndarray]]:
        """
        Make predictions using the polynomial surrogate model.
        
        Args:
            X: Input data as array or dictionary
            
        Returns:
            Predictions as array or dictionary
        """
        if not self.trained:
            raise ValueError("Model must be trained before making predictions")
            
        # Convert input to array if needed
        if isinstance(X, dict):
            X_array = np.column_stack([X[name] for name in self.input_names])
        else:
            X_array = X
            
        # Ensure 2D array
        if X_array.ndim == 1:
            X_array = X_array.reshape(1, -1)
            
        # Normalize inputs
        X_norm = self._normalize_inputs(X_array)
        
        # Compute polynomial features
        X_poly = self._compute_polynomial_features(X_norm)
        
        # Make predictions
        y_pred = X_poly @ self.coefficients
        
        # Convert to dictionary if input was dictionary
        if isinstance(X, dict) and self.output_names is not None:
            y_pred_dict = {name: y_pred[:, i] for i, name in enumerate(self.output_names)}
            return y_pred_dict
            
        return y_pred
        
    def _get_save_data(self) -> Dict[str, Any]:
        """
        Get model-specific data to save.
        
        Returns:
            Dictionary of model-specific data
        """
        return {
            "degree": self.degree,
            "coefficients": self.coefficients,
            "X_train": self.X_train,
            "y_train": self.y_train
        }
        
    def _set_load_data(self, model_data: Dict[str, Any]) -> None:
        """
        Set model-specific data when loading.
        
        Args:
            model_data: Dictionary of model-specific data
        """
        self.degree = model_data["degree"]
        self.coefficients = model_data["coefficients"]
        self.X_train = model_data["X_train"]
        self.y_train = model_data["y_train"]

class RadialBasisSurrogate(SurrogateModel):
    """
    Radial Basis Function (RBF) surrogate model.
    """
    def __init__(self, kernel: str = 'gaussian', epsilon: float = 1.0, 
                 regularization: float = 1e-10, name: str = "RBF Surrogate"):
        """
        Initialize the RBF surrogate model.
        
        Args:
            kernel: Kernel function type ('gaussian', 'multiquadric', 'inverse_multiquadric', 'linear')
            epsilon: Kernel width parameter
            regularization: Regularization parameter
            name: Model name
        """
        super().__init__(name=name)
        self.kernel = kernel.lower()
        self.epsilon = epsilon
        self.regularization = regularization
        self.centers = None
        self.weights = None
        
        # Set kernel function
        self._set_kernel_function()
        
    def _set_kernel_function(self) -> None:
        """Set the kernel function based on the selected kernel type."""
        if self.kernel == 'gaussian':
            self.kernel_func = lambda r: np.exp(-(self.epsilon * r) ** 2)
        elif self.kernel == 'multiquadric':
            self.kernel_func = lambda r: np.sqrt(1 + (self.epsilon * r) ** 2)
        elif self.kernel == 'inverse_multiquadric':
            self.kernel_func = lambda r: 1.0 / np.sqrt(1 + (self.epsilon * r) ** 2)
        elif self.kernel == 'linear':
            self.kernel_func = lambda r: r
        else:
            raise ValueError(f"Unknown kernel type: {self.kernel}")
            
    def _compute_distances(self, X1: np.ndarray, X2: np.ndarray) -> np.ndarray:
        """
        Compute pairwise Euclidean distances between points.
        
        Args:
            X1: First set of points of shape (n1, d)
            X2: Second set of points of shape (n2, d)
            
        Returns:
            Distance matrix of shape (n1, n2)
        """
        # Compute squared Euclidean distance using the identity ||x-y||^2 = ||x||^2 + ||y||^2 - 2*x.y
        X1_norm = np.sum(X1 ** 2, axis=1)[:, np.newaxis]  # Shape (n1, 1)
        X2_norm = np.sum(X2 ** 2, axis=1)[np.newaxis, :]  # Shape (1, n2)
        X1_X2 = X1 @ X2.T  # Shape (n1, n2)
        
        distances = np.sqrt(np.maximum(X1_norm + X2_norm - 2 * X1_X2, 0))  # Ensure non-negative
        
        return distances
        
    def _compute_kernel_matrix(self, X1: np.ndarray, X2: np.ndarray) -> np.ndarray:
        """
        Compute the kernel matrix between two sets of points.
        
        Args:
            X1: First set of points of shape (n1, d)
            X2: Second set of points of shape (n2, d)
            
        Returns:
            Kernel matrix of shape (n1, n2)
        """
        # Compute pairwise distances
        distances = self._compute_distances(X1, X2)
        
        # Apply kernel function
        K = self.kernel_func(distances)
        
        return K
        
    def train(self, X: Union[np.ndarray, Dict[str, np.ndarray]], 
              y: Union[np.ndarray, Dict[str, np.ndarray]], **kwargs) -> None:
        """
        Train the RBF surrogate model.
        
        Args:
            X: Input data as array or dictionary
            y: Output data as array or dictionary
            **kwargs: Additional training parameters
        """
        # Update kernel parameters if provided
        if 'epsilon' in kwargs:
            self.epsilon = kwargs['epsilon']
            self._set_kernel_function()
            
        if 'regularization' in kwargs:
            self.regularization = kwargs['regularization']
            
        # Prepare training data
        X_array, y_array = self._prepare_training_data(X, y)
        
        # Store training data
        self.X_train = X_array.copy()
        self.y_train = y_array.copy()
        
        # Normalize inputs
        X_norm = self._normalize_inputs(X_array)
        
        # Set centers to training points
        self.centers = X_norm
        
        # Compute kernel matrix
        K = self._compute_kernel_matrix(X_norm, X_norm)
        
        # Add regularization to diagonal to improve numerical stability
        K = K + np.eye(K.shape[0]) * self.regularization
        
        # Compute weights using linear solve for each output dimension
        self.weights = np.zeros((K.shape[0], self.output_dim))
        
        for i in range(self.output_dim):
            # Get output data for this dimension
            y_i = y_array[:, i]
            
            # Solve linear system
            self.weights[:, i] = np.linalg.solve(K, y_i)
            
        self.trained = True
        logger.info(f"Trained RBF surrogate model with kernel={self.kernel}, epsilon={self.epsilon}")
        
    def predict(self, X: Union[np.ndarray, Dict[str, np.ndarray]]) -> Union[np.ndarray, Dict[str, np.ndarray]]:
        """
        Make predictions using the RBF surrogate model.
        
        Args:
            X: Input data as array or dictionary
            
        Returns:
            Predictions as array or dictionary
        """
        if not self.trained:
            raise ValueError("Model must be trained before making predictions")
            
        # Convert input to array if needed
        if isinstance(X, dict):
            X_array = np.column_stack([X[name] for name in self.input_names])
        else:
            X_array = X
            
        # Ensure 2D array
        if X_array.ndim == 1:
            X_array = X_array.reshape(1, -1)
            
        # Normalize inputs
        X_norm = self._normalize_inputs(X_array)
        
        # Compute kernel matrix between inputs and centers
        K = self._compute_kernel_matrix(X_norm, self.centers)
        
        # Make predictions
        y_pred = K @ self.weights
        
        # Convert to dictionary if input was dictionary
        if isinstance(X, dict) and self.output_names is not None:
            y_pred_dict = {name: y_pred[:, i] for i, name in enumerate(self.output_names)}
            return y_pred_dict
            
        return y_pred
        
    def _get_save_data(self) -> Dict[str, Any]:
        """
        Get model-specific data to save.
        
        Returns:
            Dictionary of model-specific data
        """
        return {
            "kernel": self.kernel,
            "epsilon": self.epsilon,
            "regularization": self.regularization,
            "centers": self.centers,
            "weights": self.weights,
            "X_train": self.X_train,
            "y_train": self.y_train
        }
        
    def _set_load_data(self, model_data: Dict[str, Any]) -> None:
        """
        Set model-specific data when loading.
        
        Args:
            model_data: Dictionary of model-specific data
        """
        self.kernel = model_data["kernel"]
        self.epsilon = model_data["epsilon"]
        self.regularization = model_data["regularization"]
        self.centers = model_data["centers"]
        self.weights = model_data["weights"]
        self.X_train = model_data["X_train"]
        self.y_train = model_data["y_train"]
        
        # Set kernel function
        self._set_kernel_function()

# Try to import scikit-learn
try:
    from sklearn.gaussian_process import GaussianProcessRegressor
    from sklearn.gaussian_process.kernels import RBF, ConstantKernel, Matern, WhiteKernel
    
    class GaussianProcessSurrogate(SurrogateModel):
        """
        Gaussian Process surrogate model using scikit-learn.
        """
        def __init__(self, kernel_type: str = 'rbf', 
                    length_scale: Union[float, List[float]] = 1.0,
                    noise_level: float = 1e-10,
                    name: str = "Gaussian Process Surrogate"):
            """
            Initialize the Gaussian Process surrogate model.
            
            Args:
                kernel_type: Kernel type ('rbf', 'matern', 'constant', 'white')
                length_scale: Length scale parameter for RBF kernel
                noise_level: Noise level
                name: Model name
            """
            super().__init__(name=name)
            self.kernel_type = kernel_type.lower()
            self.length_scale = length_scale
            self.noise_level = noise_level
            self.gp_models = None
            
            # Set kernel
            self._set_kernel()
            
        def _set_kernel(self) -> None:
            """Set the kernel based on the selected kernel type."""
            if self.kernel_type == 'rbf':
                # RBF kernel with constant scale
                self.kernel = ConstantKernel(1.0) * RBF(length_scale=self.length_scale)
            elif self.kernel_type == 'matern':
                # Matern kernel
                self.kernel = ConstantKernel(1.0) * Matern(length_scale=self.length_scale, nu=1.5)
            elif self.kernel_type == 'constant':
                # Constant kernel
                self.kernel = ConstantKernel(1.0)
            elif self.kernel_type == 'white':
                # White noise kernel
                self.kernel = WhiteKernel(noise_level=self.noise_level)
            else:
                raise ValueError(f"Unknown kernel type: {self.kernel_type}")
                
        def train(self, X: Union[np.ndarray, Dict[str, np.ndarray]], 
                y: Union[np.ndarray, Dict[str, np.ndarray]], **kwargs) -> None:
            """
            Train the Gaussian Process surrogate model.
            
            Args:
                X: Input data as array or dictionary
                y: Output data as array or dictionary
                **kwargs: Additional training parameters
            """
            # Update kernel parameters if provided
            if 'length_scale' in kwargs:
                self.length_scale = kwargs['length_scale']
                self._set_kernel()
                
            if 'noise_level' in kwargs:
                self.noise_level = kwargs['noise_level']
                
            # Prepare training data
            X_array, y_array = self._prepare_training_data(X, y)
            
            # Store training data
            self.X_train = X_array.copy()
            self.y_train = y_array.copy()
            
            # Normalize inputs
            X_norm = self._normalize_inputs(X_array)
            
            # Initialize GP models for each output dimension
            self.gp_models = []
            
            for i in range(self.output_dim):
                # Get output data for this dimension
                y_i = y_array[:, i]
                
                # Create and fit GP model
                gp = GaussianProcessRegressor(
                    kernel=self.kernel,
                    alpha=self.noise_level,
                    n_restarts_optimizer=5,
                    normalize_y=True
                )
                
                gp.fit(X_norm, y_i)
                self.gp_models.append(gp)
                
            self.trained = True
            logger.info(f"Trained Gaussian Process model with kernel={self.kernel_type}")
            
        def predict(self, X: Union[np.ndarray, Dict[str, np.ndarray]], 
                   return_std: bool = False) -> Union[np.ndarray, Dict[str, np.ndarray]]:
            """
            Make predictions using the Gaussian Process surrogate model.
            
            Args:
                X: Input data as array or dictionary
                return_std: Whether to return standard deviations
                
            Returns:
                Predictions as array or dictionary
            """
            if not self.trained:
                raise ValueError("Model must be trained before making predictions")
                
            # Convert input to array if needed
            if isinstance(X, dict):
                X_array = np.column_stack([X[name] for name in self.input_names])
            else:
                X_array = X
                
            # Ensure 2D array
            if X_array.ndim == 1:
                X_array = X_array.reshape(1, -1)
                
            # Normalize inputs
            X_norm = self._normalize_inputs(X_array)
            
            # Make predictions for each output dimension
            y_preds = []
            y_stds = []
            
            for i in range(self.output_dim):
                if return_std:
                    y_pred_i, y_std_i = self.gp_models[i].predict(X_norm, return_std=True)
                    y_stds.append(y_std_i)
                else:
                    y_pred_i = self.gp_models[i].predict(X_norm)
                    
                y_preds.append(y_pred_i)
                
            # Stack predictions
            y_pred = np.column_stack(y_preds)
            
            # Convert to dictionary if input was dictionary
            if isinstance(X, dict) and self.output_names is not None:
                if return_std:
                    y_pred_dict = {name: y_pred[:, i] for i, name in enumerate(self.output_names)}
                    y_std_dict = {f"{name}_std": y_stds[i] for i, name in enumerate(self.output_names)}
                    return {**y_pred_dict, **y_std_dict}
                else:
                    y_pred_dict = {name: y_pred[:, i] for i, name in enumerate(self.output_names)}
                    return y_pred_dict
                    
            if return_std:
                y_std = np.column_stack(y_stds)
                return y_pred, y_std
                
            return y_pred
            
        def _get_save_data(self) -> Dict[str, Any]:
            """
            Get model-specific data to save.
            
            Returns:
                Dictionary of model-specific data
            """
            return {
                "kernel_type": self.kernel_type,
                "length_scale": self.length_scale,
                "noise_level": self.noise_level,
                "gp_models": self.gp_models,
                "X_train": self.X_train,
                "y_train": self.y_train
            }
            
        def _set_load_data(self, model_data: Dict[str, Any]) -> None:
            """
            Set model-specific data when loading.
            
            Args:
                model_data: Dictionary of model-specific data
            """
            self.kernel_type = model_data["kernel_type"]
            self.length_scale = model_data["length_scale"]
            self.noise_level = model_data["noise_level"]
            self.gp_models = model_data["gp_models"]
            self.X_train = model_data["X_train"]
            self.y_train = model_data["y_train"]
            
            # Set kernel
            self._set_kernel()
            
except ImportError:
    logger.warning("scikit-learn not available. GaussianProcessSurrogate will not be available.")

# Example usage if this module is run directly
if __name__ == "__main__":
    # Create some test data
    np.random.seed(42)
    X = np.random.uniform(-1, 1, (20, 2))
    y = np.sin(X[:, 0]) * np.cos(X[:, 1]) + 0.1 * np.random.randn(20)
    
    # Create test points for prediction
    X_test = np.random.uniform(-1, 1, (100, 2))
    y_test = np.sin(X_test[:, 0]) * np.cos(X_test[:, 1])
    
    # Test polynomial surrogate model
    print("Testing Polynomial Surrogate Model")
    poly_model = PolynomialSurrogate(degree=3)
    poly_model.train(X, y.reshape(-1, 1))
    
    y_pred_poly = poly_model.predict(X_test).flatten()
    r2_poly = poly_model.score(X_test, y_test.reshape(-1, 1))
    print(f"Polynomial R^2: {r2_poly['overall']}")
    
    # Test RBF surrogate model
    print("\nTesting RBF Surrogate Model")
    rbf_model = RadialBasisSurrogate(kernel='gaussian', epsilon=2.0)
    rbf_model.train(X, y.reshape(-1, 1))
    
    y_pred_rbf = rbf_model.predict(X_test).flatten()
    r2_rbf = rbf_model.score(X_test, y_test.reshape(-1, 1))
    print(f"RBF R^2: {r2_rbf['overall']}")
    
    # Plot predictions
    plt.figure(figsize=(10, 6))
    plt.scatter(y_test, y_pred_poly, alpha=0.7, label=f"Polynomial (R^2={r2_poly['overall']:.3f})")
    plt.scatter(y_test, y_pred_rbf, alpha=0.7, label=f"RBF (R^2={r2_rbf['overall']:.3f})")
    
    # Add diagonal line
    min_val = min(np.min(y_test), np.min(y_pred_poly), np.min(y_pred_rbf))
    max_val = max(np.max(y_test), np.max(y_pred_poly), np.max(y_pred_rbf))
    plt.plot([min_val, max_val], [min_val, max_val], 'k--')
    
    plt.xlabel("True Value")
    plt.ylabel("Predicted Value")
    plt.title("Surrogate Model Predictions")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()
    
    # Try saving and loading a model
    print("\nTesting model save/load")
    save_path = "rbf_surrogate.pkl"
    rbf_model.save(save_path)
    
    loaded_model = RadialBasisSurrogate.load(save_path)
    y_pred_loaded = loaded_model.predict(X_test).flatten()
    r2_loaded = loaded_model.score(X_test, y_test.reshape(-1, 1))
    print(f"Loaded RBF R^2: {r2_loaded['overall']}")
    
    # Verify predictions are the same
    assert np.allclose(y_pred_rbf, y_pred_loaded)
    
    # Clean up
    import os
    os.remove(save_path)