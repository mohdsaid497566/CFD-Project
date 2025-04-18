"""
Neural Network-based surrogate models for MDO package.

This module extends the surrogate modeling capabilities with neural network models
that can handle complex, high-dimensional design spaces.
"""

import os
import sys
import logging
import numpy as np
from typing import Dict, List, Tuple, Union, Optional, Any, Callable
import time

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("neural_networks")

class NeuralNetworkSurrogate:
    """
    Base class for neural network-based surrogate models.
    Provides common functionality and interface for different NN implementations.
    """
    def __init__(self, input_dim: int, output_dim: int = 1, hidden_layers: List[int] = [20, 20],
                normalize_inputs: bool = True, normalize_outputs: bool = True):
        """
        Initialize neural network surrogate model.
        
        Args:
            input_dim: Dimension of input (number of design variables)
            output_dim: Dimension of output (number of objectives/constraints)
            hidden_layers: List of neurons in each hidden layer
            normalize_inputs: Whether to normalize input data
            normalize_outputs: Whether to normalize output data
        """
        self.input_dim = input_dim
        self.output_dim = output_dim
        self.hidden_layers = hidden_layers
        self.normalize_inputs = normalize_inputs
        self.normalize_outputs = normalize_outputs
        
        # Scaling parameters for normalization
        self.x_mean = None
        self.x_std = None
        self.y_mean = None
        self.y_std = None
        
        # Model instance
        self.model = None
        
        # Training history
        self.history = None
        
        # Check if required libraries are available
        self._check_dependencies()
    
    def _check_dependencies(self):
        """Check if required libraries are available"""
        try:
            # Try to import deep learning libraries
            # This will be overridden by subclasses
            pass
        except ImportError as e:
            logger.warning(f"Neural network dependencies not available: {str(e)}")
    
    def _normalize_inputs(self, X):
        """
        Normalize input data.
        
        Args:
            X: Input data of shape (n_samples, input_dim)
            
        Returns:
            Normalized input data
        """
        if not self.normalize_inputs or self.x_mean is None:
            return X
        
        return (X - self.x_mean) / self.x_std
    
    def _denormalize_inputs(self, X_norm):
        """
        Denormalize input data.
        
        Args:
            X_norm: Normalized input data
            
        Returns:
            Original input data
        """
        if not self.normalize_inputs or self.x_mean is None:
            return X_norm
        
        return X_norm * self.x_std + self.x_mean
    
    def _normalize_outputs(self, Y):
        """
        Normalize output data.
        
        Args:
            Y: Output data of shape (n_samples, output_dim)
            
        Returns:
            Normalized output data
        """
        if not self.normalize_outputs or self.y_mean is None:
            return Y
        
        return (Y - self.y_mean) / self.y_std
    
    def _denormalize_outputs(self, Y_norm):
        """
        Denormalize output data.
        
        Args:
            Y_norm: Normalized output data
            
        Returns:
            Original output data
        """
        if not self.normalize_outputs or self.y_mean is None:
            return Y_norm
        
        return Y_norm * self.y_std + self.y_mean
    
    def _compute_scaling_params(self, X, Y):
        """
        Compute scaling parameters for normalization.
        
        Args:
            X: Input data
            Y: Output data
        """
        if self.normalize_inputs:
            self.x_mean = np.mean(X, axis=0)
            self.x_std = np.std(X, axis=0)
            # Prevent division by zero
            self.x_std = np.where(self.x_std < 1e-10, 1.0, self.x_std)
        
        if self.normalize_outputs:
            self.y_mean = np.mean(Y, axis=0)
            self.y_std = np.std(Y, axis=0)
            # Prevent division by zero
            self.y_std = np.where(self.y_std < 1e-10, 1.0, self.y_std)
    
    def fit(self, X, Y, validation_split=0.2, epochs=100, batch_size=32, verbose=1):
        """
        Train the neural network surrogate model.
        
        Args:
            X: Input data of shape (n_samples, input_dim)
            Y: Output data of shape (n_samples, output_dim)
            validation_split: Fraction of data to use for validation
            epochs: Number of training epochs
            batch_size: Batch size for training
            verbose: Verbosity level (0=silent, 1=progress bar, 2=one line per epoch)
            
        Returns:
            Training history
        """
        # Will be implemented by subclasses
        raise NotImplementedError("Subclasses must implement this method")
    
    def predict(self, X):
        """
        Make predictions with the trained model.
        
        Args:
            X: Input data of shape (n_samples, input_dim)
            
        Returns:
            Predictions of shape (n_samples, output_dim)
        """
        # Will be implemented by subclasses
        raise NotImplementedError("Subclasses must implement this method")
    
    def evaluate(self, X, Y):
        """
        Evaluate model performance on test data.
        
        Args:
            X: Input data of shape (n_samples, input_dim)
            Y: Output data of shape (n_samples, output_dim)
            
        Returns:
            Dictionary of evaluation metrics
        """
        # Will be implemented by subclasses
        raise NotImplementedError("Subclasses must implement this method")
    
    def save(self, filepath):
        """
        Save model to file.
        
        Args:
            filepath: Path to save the model
        """
        # Will be implemented by subclasses
        raise NotImplementedError("Subclasses must implement this method")
    
    def load(self, filepath):
        """
        Load model from file.
        
        Args:
            filepath: Path to load the model from
        """
        # Will be implemented by subclasses
        raise NotImplementedError("Subclasses must implement this method")
    
    def plot_training_history(self, save_path=None, show=True):
        """
        Plot training history.
        
        Args:
            save_path: Path to save the plot
            show: Whether to display the plot
        """
        # Will be implemented by subclasses
        raise NotImplementedError("Subclasses must implement this method")
    
    def plot_prediction_error(self, X, Y, save_path=None, show=True):
        """
        Plot prediction error.
        
        Args:
            X: Input data
            Y: True output data
            save_path: Path to save the plot
            show: Whether to display the plot
        """
        # Will be implemented by subclasses
        raise NotImplementedError("Subclasses must implement this method")
    
    def get_gradient(self, X):
        """
        Compute gradient of model output with respect to inputs.
        
        Args:
            X: Input data of shape (n_samples, input_dim)
            
        Returns:
            Gradient of shape (n_samples, output_dim, input_dim)
        """
        # Will be implemented by subclasses
        raise NotImplementedError("Subclasses must implement this method")


class TensorFlowNeuralNetwork(NeuralNetworkSurrogate):
    """
    Neural network surrogate model implemented using TensorFlow/Keras.
    """
    def __init__(self, input_dim, output_dim=1, hidden_layers=[20, 20],
                activation='relu', learning_rate=0.001, l2_reg=0.0,
                dropout_rate=0.0, normalize_inputs=True, normalize_outputs=True):
        """
        Initialize TensorFlow neural network surrogate model.
        
        Args:
            input_dim: Dimension of input (number of design variables)
            output_dim: Dimension of output (number of objectives/constraints)
            hidden_layers: List of neurons in each hidden layer
            activation: Activation function for hidden layers
            learning_rate: Learning rate for optimizer
            l2_reg: L2 regularization coefficient
            dropout_rate: Dropout rate (0-1)
            normalize_inputs: Whether to normalize input data
            normalize_outputs: Whether to normalize output data
        """
        super().__init__(input_dim, output_dim, hidden_layers, normalize_inputs, normalize_outputs)
        
        self.activation = activation
        self.learning_rate = learning_rate
        self.l2_reg = l2_reg
        self.dropout_rate = dropout_rate
    
    def _check_dependencies(self):
        """Check if TensorFlow is available"""
        try:
            import tensorflow as tf
            from tensorflow.keras import models, layers, optimizers, regularizers, callbacks
            
            # Check TensorFlow version
            logger.info(f"TensorFlow version: {tf.__version__}")
            
            # Store module references
            self.tf = tf
            self.models = models
            self.layers = layers
            self.optimizers = optimizers
            self.regularizers = regularizers
            self.callbacks = callbacks
            
            # Check GPU availability
            if len(tf.config.list_physical_devices('GPU')) > 0:
                logger.info("GPU is available for TensorFlow")
            else:
                logger.info("No GPU found. Using CPU for TensorFlow")
            
        except ImportError as e:
            logger.warning(f"TensorFlow not available: {str(e)}")
            raise ImportError("TensorFlow is required for TensorFlowNeuralNetwork")
    
    def _build_model(self):
        """Build the TensorFlow model"""
        # Create sequential model
        model = self.models.Sequential()
        
        # Add input layer
        model.add(self.layers.Input(shape=(self.input_dim,)))
        
        # Add hidden layers
        regularizer = self.regularizers.l2(self.l2_reg) if self.l2_reg > 0 else None
        
        for i, neurons in enumerate(self.hidden_layers):
            model.add(self.layers.Dense(
                neurons,
                activation=self.activation,
                kernel_regularizer=regularizer,
                name=f'hidden_{i+1}'
            ))
            
            # Add dropout if specified
            if self.dropout_rate > 0:
                model.add(self.layers.Dropout(self.dropout_rate))
        
        # Add output layer
        model.add(self.layers.Dense(self.output_dim, name='output'))
        
        # Compile model
        model.compile(
            optimizer=self.optimizers.Adam(learning_rate=self.learning_rate),
            loss='mse',
            metrics=['mae']
        )
        
        return model
    
    def fit(self, X, Y, validation_split=0.2, epochs=100, batch_size=32, verbose=1,
           early_stopping=True, patience=20, save_best_model=True, model_path=None):
        """
        Train the neural network surrogate model.
        
        Args:
            X: Input data of shape (n_samples, input_dim)
            Y: Output data of shape (n_samples, output_dim)
            validation_split: Fraction of data to use for validation
            epochs: Number of training epochs
            batch_size: Batch size for training
            verbose: Verbosity level (0=silent, 1=progress bar, 2=one line per epoch)
            early_stopping: Whether to use early stopping
            patience: Patience for early stopping
            save_best_model: Whether to save the best model during training
            model_path: Path to save the best model
            
        Returns:
            Training history
        """
        # Ensure X and Y have correct shape
        if len(X.shape) == 1:
            X = X.reshape(-1, 1)
        
        if len(Y.shape) == 1:
            Y = Y.reshape(-1, 1)
        
        # Compute scaling parameters
        self._compute_scaling_params(X, Y)
        
        # Normalize data
        X_norm = self._normalize_inputs(X)
        Y_norm = self._normalize_outputs(Y)
        
        # Build model if not already built
        if self.model is None:
            self.model = self._build_model()
            
            # Print model summary
            self.model.summary()
        
        # Prepare callbacks
        callbacks_list = []
        
        if early_stopping:
            es_callback = self.callbacks.EarlyStopping(
                monitor='val_loss',
                patience=patience,
                restore_best_weights=True,
                verbose=1 if verbose > 0 else 0
            )
            callbacks_list.append(es_callback)
        
        if save_best_model:
            if model_path is None:
                model_path = 'best_nn_model.h5'
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(os.path.abspath(model_path)), exist_ok=True)
            
            mc_callback = self.callbacks.ModelCheckpoint(
                model_path,
                monitor='val_loss',
                save_best_only=True,
                verbose=0
            )
            callbacks_list.append(mc_callback)
        
        # Train model
        start_time = time.time()
        
        self.history = self.model.fit(
            X_norm, Y_norm,
            validation_split=validation_split,
            epochs=epochs,
            batch_size=batch_size,
            verbose=verbose,
            callbacks=callbacks_list
        )
        
        training_time = time.time() - start_time
        logger.info(f"Model training completed in {training_time:.2f} seconds")
        
        return self.history
    
    def predict(self, X):
        """
        Make predictions with the trained model.
        
        Args:
            X: Input data of shape (n_samples, input_dim)
            
        Returns:
            Predictions of shape (n_samples, output_dim)
        """
        if self.model is None:
            raise ValueError("Model not trained. Call fit() first.")
        
        # Ensure X has correct shape
        if len(X.shape) == 1:
            X = X.reshape(-1, 1)
        
        # Normalize inputs
        X_norm = self._normalize_inputs(X)
        
        # Make prediction
        Y_norm_pred = self.model.predict(X_norm)
        
        # Denormalize outputs
        Y_pred = self._denormalize_outputs(Y_norm_pred)
        
        return Y_pred
    
    def evaluate(self, X, Y):
        """
        Evaluate model performance on test data.
        
        Args:
            X: Input data of shape (n_samples, input_dim)
            Y: Output data of shape (n_samples, output_dim)
            
        Returns:
            Dictionary of evaluation metrics
        """
        if self.model is None:
            raise ValueError("Model not trained. Call fit() first.")
        
        # Ensure X and Y have correct shape
        if len(X.shape) == 1:
            X = X.reshape(-1, 1)
        
        if len(Y.shape) == 1:
            Y = Y.reshape(-1, 1)
        
        # Normalize data
        X_norm = self._normalize_inputs(X)
        Y_norm = self._normalize_outputs(Y)
        
        # Evaluate model
        scores = self.model.evaluate(X_norm, Y_norm, verbose=0)
        
        # Make predictions for additional metrics
        Y_pred = self.predict(X)
        
        # Calculate additional metrics
        from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
        
        metrics = {
            'loss': scores[0],
            'mae': scores[1],
            'mse': mean_squared_error(Y, Y_pred),
            'rmse': np.sqrt(mean_squared_error(Y, Y_pred)),
            'r2': r2_score(Y, Y_pred)
        }
        
        # For multi-output models, calculate per-output metrics
        if self.output_dim > 1:
            for i in range(self.output_dim):
                metrics[f'mae_output_{i}'] = mean_absolute_error(Y[:, i], Y_pred[:, i])
                metrics[f'rmse_output_{i}'] = np.sqrt(mean_squared_error(Y[:, i], Y_pred[:, i]))
                metrics[f'r2_output_{i}'] = r2_score(Y[:, i], Y_pred[:, i])
        
        return metrics
    
    def save(self, filepath):
        """
        Save model to file.
        
        Args:
            filepath: Path to save the model
        """
        if self.model is None:
            raise ValueError("Model not trained. Call fit() first.")
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        
        # Save model
        self.model.save(filepath)
        
        # Save scaling parameters
        import pickle
        
        scaling_params = {
            'x_mean': self.x_mean,
            'x_std': self.x_std,
            'y_mean': self.y_mean,
            'y_std': self.y_std,
            'input_dim': self.input_dim,
            'output_dim': self.output_dim,
            'hidden_layers': self.hidden_layers,
            'normalize_inputs': self.normalize_inputs,
            'normalize_outputs': self.normalize_outputs,
            'activation': self.activation,
            'learning_rate': self.learning_rate,
            'l2_reg': self.l2_reg,
            'dropout_rate': self.dropout_rate
        }
        
        scaling_filepath = filepath + '.params'
        with open(scaling_filepath, 'wb') as f:
            pickle.dump(scaling_params, f)
        
        logger.info(f"Model saved to {filepath}")
    
    def load(self, filepath):
        """
        Load model from file.
        
        Args:
            filepath: Path to load the model from
        """
        # Load model
        self.model = self.models.load_model(filepath)
        
        # Load scaling parameters
        import pickle
        
        scaling_filepath = filepath + '.params'
        with open(scaling_filepath, 'rb') as f:
            params = pickle.load(f)
        
        self.x_mean = params['x_mean']
        self.x_std = params['x_std']
        self.y_mean = params['y_mean']
        self.y_std = params['y_std']
        self.input_dim = params['input_dim']
        self.output_dim = params['output_dim']
        self.hidden_layers = params['hidden_layers']
        self.normalize_inputs = params['normalize_inputs']
        self.normalize_outputs = params['normalize_outputs']
        self.activation = params['activation']
        self.learning_rate = params['learning_rate']
        self.l2_reg = params['l2_reg']
        self.dropout_rate = params['dropout_rate']
        
        logger.info(f"Model loaded from {filepath}")
    
    def plot_training_history(self, save_path=None, show=True):
        """
        Plot training history.
        
        Args:
            save_path: Path to save the plot
            show: Whether to display the plot
        """
        if self.history is None:
            raise ValueError("No training history available. Train the model first.")
        
        try:
            import matplotlib.pyplot as plt
            
            # Create figure with 2 subplots
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
            
            # Plot training & validation loss
            ax1.plot(self.history.history['loss'], label='Train')
            ax1.plot(self.history.history['val_loss'], label='Validation')
            ax1.set_title('Model Loss')
            ax1.set_xlabel('Epoch')
            ax1.set_ylabel('Loss (MSE)')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # Plot training & validation MAE
            ax2.plot(self.history.history['mae'], label='Train')
            ax2.plot(self.history.history['val_mae'], label='Validation')
            ax2.set_title('Model Mean Absolute Error')
            ax2.set_xlabel('Epoch')
            ax2.set_ylabel('MAE')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # Save figure if path provided
            if save_path is not None:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                logger.info(f"Training history plot saved to {save_path}")
            
            # Show figure if requested
            if show:
                plt.show()
            else:
                plt.close()
                
        except ImportError:
            logger.warning("Matplotlib not available. Skipping plot generation.")
    
    def plot_prediction_error(self, X, Y, save_path=None, show=True):
        """
        Plot prediction error.
        
        Args:
            X: Input data
            Y: True output data
            save_path: Path to save the plot
            show: Whether to display the plot
        """
        if self.model is None:
            raise ValueError("Model not trained. Call fit() first.")
        
        try:
            import matplotlib.pyplot as plt
            
            # Ensure data has correct shape
            if len(X.shape) == 1:
                X = X.reshape(-1, 1)
            
            if len(Y.shape) == 1:
                Y = Y.reshape(-1, 1)
            
            # Make predictions
            Y_pred = self.predict(X)
            
            # Create figure with subplots
            n_plots = min(self.output_dim, 4)  # Limit number of output plots
            fig, axes = plt.subplots(1, n_plots, figsize=(5*n_plots, 5))
            
            if n_plots == 1:
                axes = [axes]  # Make it iterable
            
            for i in range(n_plots):
                ax = axes[i]
                
                # Plot true vs predicted
                ax.scatter(Y[:, i], Y_pred[:, i], alpha=0.7)
                
                # Plot perfect prediction line
                min_val = min(np.min(Y[:, i]), np.min(Y_pred[:, i]))
                max_val = max(np.max(Y[:, i]), np.max(Y_pred[:, i]))
                ax.plot([min_val, max_val], [min_val, max_val], 'r--')
                
                # Calculate metrics for this output
                from sklearn.metrics import r2_score, mean_squared_error
                r2 = r2_score(Y[:, i], Y_pred[:, i])
                rmse = np.sqrt(mean_squared_error(Y[:, i], Y_pred[:, i]))
                
                # Add metrics to plot
                ax.text(0.05, 0.95, f'R² = {r2:.4f}\nRMSE = {rmse:.4f}',
                       transform=ax.transAxes, verticalalignment='top',
                       bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
                
                ax.set_title(f'Output {i+1}')
                ax.set_xlabel('True Value')
                ax.set_ylabel('Predicted Value')
                ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # Save figure if path provided
            if save_path is not None:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                logger.info(f"Prediction error plot saved to {save_path}")
            
            # Show figure if requested
            if show:
                plt.show()
            else:
                plt.close()
                
        except ImportError:
            logger.warning("Matplotlib not available. Skipping plot generation.")
    
    def get_gradient(self, X):
        """
        Compute gradient of model output with respect to inputs.
        
        Args:
            X: Input data of shape (n_samples, input_dim)
            
        Returns:
            Gradient of shape (n_samples, output_dim, input_dim)
        """
        if self.model is None:
            raise ValueError("Model not trained. Call fit() first.")
        
        # Ensure X has correct shape
        if len(X.shape) == 1:
            X = X.reshape(-1, 1)
        
        # Normalize inputs
        X_norm = self._normalize_inputs(X)
        
        # Create tensor for input data
        X_tensor = self.tf.convert_to_tensor(X_norm, dtype=self.tf.float32)
        
        # Compute gradient
        with self.tf.GradientTape(persistent=True) as tape:
            tape.watch(X_tensor)
            Y_pred = self.model(X_tensor)
        
        # Get gradients
        gradients = []
        for i in range(self.output_dim):
            grad = tape.gradient(Y_pred[:, i], X_tensor)
            gradients.append(grad)
        
        # Stack gradients along new axis
        grad_tensor = self.tf.stack(gradients, axis=1)
        
        # Convert to numpy array
        grad_np = grad_tensor.numpy()
        
        # Apply scaling if inputs/outputs were normalized
        if self.normalize_inputs and self.normalize_outputs:
            for i in range(self.output_dim):
                grad_np[:, i, :] = grad_np[:, i, :] * (self.y_std[i] / self.x_std)
        
        return grad_np


class PyTorchNeuralNetwork(NeuralNetworkSurrogate):
    """
    Neural network surrogate model implemented using PyTorch.
    """
    def __init__(self, input_dim, output_dim=1, hidden_layers=[20, 20],
                activation='relu', learning_rate=0.001, l2_reg=0.0,
                dropout_rate=0.0, normalize_inputs=True, normalize_outputs=True):
        """
        Initialize PyTorch neural network surrogate model.
        
        Args:
            input_dim: Dimension of input (number of design variables)
            output_dim: Dimension of output (number of objectives/constraints)
            hidden_layers: List of neurons in each hidden layer
            activation: Activation function for hidden layers ('relu', 'tanh', 'sigmoid')
            learning_rate: Learning rate for optimizer
            l2_reg: L2 regularization coefficient
            dropout_rate: Dropout rate (0-1)
            normalize_inputs: Whether to normalize input data
            normalize_outputs: Whether to normalize output data
        """
        super().__init__(input_dim, output_dim, hidden_layers, normalize_inputs, normalize_outputs)
        
        self.activation = activation
        self.learning_rate = learning_rate
        self.l2_reg = l2_reg
        self.dropout_rate = dropout_rate
    
    def _check_dependencies(self):
        """Check if PyTorch is available"""
        try:
            import torch
            import torch.nn as nn
            import torch.optim as optim
            from torch.utils.data import DataLoader, TensorDataset
            
            # Check PyTorch version
            logger.info(f"PyTorch version: {torch.__version__}")
            
            # Store module references
            self.torch = torch
            self.nn = nn
            self.optim = optim
            self.DataLoader = DataLoader
            self.TensorDataset = TensorDataset
            
            # Check CUDA availability
            self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
            logger.info(f"Using device: {self.device}")
            
        except ImportError as e:
            logger.warning(f"PyTorch not available: {str(e)}")
            raise ImportError("PyTorch is required for PyTorchNeuralNetwork")
    
    def _get_activation(self):
        """Get activation function based on name"""
        if self.activation.lower() == 'relu':
            return self.nn.ReLU()
        elif self.activation.lower() == 'tanh':
            return self.nn.Tanh()
        elif self.activation.lower() == 'sigmoid':
            return self.nn.Sigmoid()
        else:
            logger.warning(f"Unknown activation function: {self.activation}. Using ReLU.")
            return self.nn.ReLU()
    
    def _build_model(self):
        """Build PyTorch model"""
        # Define model architecture
        class NeuralNet(self.nn.Module):
            def __init__(self, input_dim, hidden_layers, output_dim, 
                       activation, dropout_rate):
                super(NeuralNet, self).__init__()
                
                # Input layer
                layers = []
                
                # First hidden layer
                layers.append(self.nn.Linear(input_dim, hidden_layers[0]))
                layers.append(activation)
                
                if dropout_rate > 0:
                    layers.append(self.nn.Dropout(dropout_rate))
                
                # Additional hidden layers
                for i in range(len(hidden_layers) - 1):
                    layers.append(self.nn.Linear(hidden_layers[i], hidden_layers[i+1]))
                    layers.append(activation)
                    
                    if dropout_rate > 0:
                        layers.append(self.nn.Dropout(dropout_rate))
                
                # Output layer
                layers.append(self.nn.Linear(hidden_layers[-1], output_dim))
                
                # Create sequential model
                self.model = self.nn.Sequential(*layers)
            
            def forward(self, x):
                return self.model(x)
        
        # Create model instance
        model = NeuralNet(
            self.input_dim,
            self.hidden_layers,
            self.output_dim,
            self._get_activation(),
            self.dropout_rate
        )
        
        # Move model to device (CPU/GPU)
        model.to(self.device)
        
        return model
    
    def fit(self, X, Y, validation_split=0.2, epochs=100, batch_size=32, verbose=1,
           early_stopping=True, patience=20, save_best_model=True, model_path=None):
        """
        Train the PyTorch neural network surrogate model.
        
        Args:
            X: Input data of shape (n_samples, input_dim)
            Y: Output data of shape (n_samples, output_dim)
            validation_split: Fraction of data to use for validation
            epochs: Number of training epochs
            batch_size: Batch size for training
            verbose: Verbosity level (0=silent, 1=progress bar, 2=one line per epoch)
            early_stopping: Whether to use early stopping
            patience: Patience for early stopping
            save_best_model: Whether to save the best model during training
            model_path: Path to save the best model
            
        Returns:
            Training history
        """
        # Ensure X and Y have correct shape
        if len(X.shape) == 1:
            X = X.reshape(-1, 1)
        
        if len(Y.shape) == 1:
            Y = Y.reshape(-1, 1)
        
        # Compute scaling parameters
        self._compute_scaling_params(X, Y)
        
        # Normalize data
        X_norm = self._normalize_inputs(X)
        Y_norm = self._normalize_outputs(Y)
        
        # Convert to PyTorch tensors
        X_tensor = self.torch.tensor(X_norm, dtype=self.torch.float32)
        Y_tensor = self.torch.tensor(Y_norm, dtype=self.torch.float32)
        
        # Split data into train and validation sets
        n_samples = len(X_norm)
        n_train = int(n_samples * (1 - validation_split))
        
        indices = np.random.permutation(n_samples)
        train_indices = indices[:n_train]
        val_indices = indices[n_train:]
        
        X_train = X_tensor[train_indices]
        Y_train = Y_tensor[train_indices]
        X_val = X_tensor[val_indices]
        Y_val = Y_tensor[val_indices]
        
        # Create data loaders
        train_dataset = self.TensorDataset(X_train, Y_train)
        val_dataset = self.TensorDataset(X_val, Y_val)
        
        train_loader = self.DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        val_loader = self.DataLoader(val_dataset, batch_size=batch_size)
        
        # Build model if not already built
        if self.model is None:
            self.model = self._build_model()
            
            # Print model summary
            if verbose > 0:
                print(self.model)
                print(f"Number of parameters: {sum(p.numel() for p in self.model.parameters())}")
        
        # Define loss function and optimizer
        criterion = self.nn.MSELoss()
        optimizer = self.optim.Adam(
            self.model.parameters(),
            lr=self.learning_rate,
            weight_decay=self.l2_reg
        )
        
        # Initialize variables for early stopping
        best_val_loss = float('inf')
        patience_counter = 0
        best_model_state = None
        
        # Initialize history
        history = {
            'train_loss': [],
            'val_loss': [],
            'train_mae': [],
            'val_mae': []
        }
        
        # Training loop
        start_time = time.time()
        
        for epoch in range(epochs):
            # Training phase
            self.model.train()
            train_loss = 0.0
            train_mae = 0.0
            
            for inputs, targets in train_loader:
                # Move data to device
                inputs = inputs.to(self.device)
                targets = targets.to(self.device)
                
                # Forward pass
                outputs = self.model(inputs)
                loss = criterion(outputs, targets)
                
                # Backward and optimize
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                
                # Accumulate metrics
                train_loss += loss.item() * inputs.size(0)
                train_mae += self.torch.mean(self.torch.abs(outputs - targets)).item() * inputs.size(0)
            
            # Compute epoch metrics
            train_loss /= len(train_dataset)
            train_mae /= len(train_dataset)
            
            # Validation phase
            self.model.eval()
            val_loss = 0.0
            val_mae = 0.0
            
            with self.torch.no_grad():
                for inputs, targets in val_loader:
                    # Move data to device
                    inputs = inputs.to(self.device)
                    targets = targets.to(self.device)
                    
                    # Forward pass
                    outputs = self.model(inputs)
                    loss = criterion(outputs, targets)
                    
                    # Accumulate metrics
                    val_loss += loss.item() * inputs.size(0)
                    val_mae += self.torch.mean(self.torch.abs(outputs - targets)).item() * inputs.size(0)
                
                # Compute epoch metrics
                val_loss /= len(val_dataset)
                val_mae /= len(val_dataset)
            
            # Store metrics in history
            history['train_loss'].append(train_loss)
            history['val_loss'].append(val_loss)
            history['train_mae'].append(train_mae)
            history['val_mae'].append(val_mae)
            
            # Print progress
            if verbose == 1:
                print(f"Epoch {epoch+1}/{epochs} - "
                    f"train_loss: {train_loss:.4f} - "
                    f"val_loss: {val_loss:.4f} - "
                    f"train_mae: {train_mae:.4f} - "
                    f"val_mae: {val_mae:.4f}")
            elif verbose == 2 and (epoch == 0 or (epoch + 1) % 10 == 0 or epoch == epochs - 1):
                print(f"Epoch {epoch+1}/{epochs} - "
                    f"train_loss: {train_loss:.4f} - "
                    f"val_loss: {val_loss:.4f}")
            
            # Check for early stopping
            if early_stopping:
                if val_loss < best_val_loss:
                    best_val_loss = val_loss
                    patience_counter = 0
                    
                    # Save best model state
                    best_model_state = {
                        'model_state_dict': self.model.state_dict(),
                        'optimizer_state_dict': optimizer.state_dict(),
                        'epoch': epoch,
                        'train_loss': train_loss,
                        'val_loss': val_loss
                    }
                    
                    # Save best model if requested
                    if save_best_model and model_path is not None:
                        # Ensure directory exists
                        os.makedirs(os.path.dirname(os.path.abspath(model_path)), exist_ok=True)
                        self.torch.save(best_model_state, model_path)
                else:
                    patience_counter += 1
                    
                    if patience_counter >= patience:
                        if verbose > 0:
                            print(f"Early stopping at epoch {epoch+1}")
                        break
        
        # Restore best model if early stopping was used
        if early_stopping and best_model_state is not None:
            self.model.load_state_dict(best_model_state['model_state_dict'])
            
            if verbose > 0:
                print(f"Restored best model from epoch {best_model_state['epoch']+1} "
                    f"with validation loss {best_model_state['val_loss']:.4f}")
        
        training_time = time.time() - start_time
        logger.info(f"Model training completed in {training_time:.2f} seconds")
        
        # Store history
        self.history = history
        
        return history
    
    def predict(self, X):
        """
        Make predictions with the trained model.
        
        Args:
            X: Input data of shape (n_samples, input_dim)
            
        Returns:
            Predictions of shape (n_samples, output_dim)
        """
        if self.model is None:
            raise ValueError("Model not trained. Call fit() first.")
        
        # Ensure X has correct shape
        if len(X.shape) == 1:
            X = X.reshape(-1, 1)
        
        # Normalize inputs
        X_norm = self._normalize_inputs(X)
        
        # Convert to PyTorch tensor
        X_tensor = self.torch.tensor(X_norm, dtype=self.torch.float32)
        X_tensor = X_tensor.to(self.device)
        
        # Set model to evaluation mode
        self.model.eval()
        
        # Make prediction
        with self.torch.no_grad():
            Y_norm_pred = self.model(X_tensor).cpu().numpy()
        
        # Denormalize outputs
        Y_pred = self._denormalize_outputs(Y_norm_pred)
        
        return Y_pred
    
    def evaluate(self, X, Y):
        """
        Evaluate model performance on test data.
        
        Args:
            X: Input data of shape (n_samples, input_dim)
            Y: Output data of shape (n_samples, output_dim)
            
        Returns:
            Dictionary of evaluation metrics
        """
        if self.model is None:
            raise ValueError("Model not trained. Call fit() first.")
        
        # Ensure X and Y have correct shape
        if len(X.shape) == 1:
            X = X.reshape(-1, 1)
        
        if len(Y.shape) == 1:
            Y = Y.reshape(-1, 1)
        
        # Make predictions
        Y_pred = self.predict(X)
        
        # Calculate metrics
        from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
        
        metrics = {
            'mse': mean_squared_error(Y, Y_pred),
            'rmse': np.sqrt(mean_squared_error(Y, Y_pred)),
            'mae': mean_absolute_error(Y, Y_pred),
            'r2': r2_score(Y, Y_pred)
        }
        
        # For multi-output models, calculate per-output metrics
        if self.output_dim > 1:
            for i in range(self.output_dim):
                metrics[f'mae_output_{i}'] = mean_absolute_error(Y[:, i], Y_pred[:, i])
                metrics[f'rmse_output_{i}'] = np.sqrt(mean_squared_error(Y[:, i], Y_pred[:, i]))
                metrics[f'r2_output_{i}'] = r2_score(Y[:, i], Y_pred[:, i])
        
        return metrics
    
    def save(self, filepath):
        """
        Save model to file.
        
        Args:
            filepath: Path to save the model
        """
        if self.model is None:
            raise ValueError("Model not trained. Call fit() first.")
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        
        # Save model
        model_state = {
            'model_state_dict': self.model.state_dict(),
            'input_dim': self.input_dim,
            'output_dim': self.output_dim,
            'hidden_layers': self.hidden_layers,
            'activation': self.activation,
            'dropout_rate': self.dropout_rate
        }
        
        self.torch.save(model_state, filepath)
        
        # Save scaling parameters
        import pickle
        
        scaling_params = {
            'x_mean': self.x_mean,
            'x_std': self.x_std,
            'y_mean': self.y_mean,
            'y_std': self.y_std,
            'normalize_inputs': self.normalize_inputs,
            'normalize_outputs': self.normalize_outputs,
            'learning_rate': self.learning_rate,
            'l2_reg': self.l2_reg
        }
        
        scaling_filepath = filepath + '.params'
        with open(scaling_filepath, 'wb') as f:
            pickle.dump(scaling_params, f)
        
        logger.info(f"Model saved to {filepath}")
    
    def load(self, filepath):
        """
        Load model from file.
        
        Args:
            filepath: Path to load the model from
        """
        # Load model state
        model_state = self.torch.load(filepath, map_location=self.device)
        
        # Set model parameters
        self.input_dim = model_state['input_dim']
        self.output_dim = model_state['output_dim']
        self.hidden_layers = model_state['hidden_layers']
        self.activation = model_state['activation']
        self.dropout_rate = model_state['dropout_rate']
        
        # Build model
        self.model = self._build_model()
        
        # Load state dict
        self.model.load_state_dict(model_state['model_state_dict'])
        
        # Load scaling parameters
        import pickle
        
        scaling_filepath = filepath + '.params'
        with open(scaling_filepath, 'rb') as f:
            params = pickle.load(f)
        
        self.x_mean = params['x_mean']
        self.x_std = params['x_std']
        self.y_mean = params['y_mean']
        self.y_std = params['y_std']
        self.normalize_inputs = params['normalize_inputs']
        self.normalize_outputs = params['normalize_outputs']
        self.learning_rate = params['learning_rate']
        self.l2_reg = params['l2_reg']
        
        logger.info(f"Model loaded from {filepath}")
    
    def plot_training_history(self, save_path=None, show=True):
        """
        Plot training history.
        
        Args:
            save_path: Path to save the plot
            show: Whether to display the plot
        """
        if self.history is None:
            raise ValueError("No training history available. Train the model first.")
        
        try:
            import matplotlib.pyplot as plt
            
            # Create figure with 2 subplots
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
            
            # Plot training & validation loss
            ax1.plot(self.history['train_loss'], label='Train')
            ax1.plot(self.history['val_loss'], label='Validation')
            ax1.set_title('Model Loss')
            ax1.set_xlabel('Epoch')
            ax1.set_ylabel('Loss (MSE)')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # Plot training & validation MAE
            ax2.plot(self.history['train_mae'], label='Train')
            ax2.plot(self.history['val_mae'], label='Validation')
            ax2.set_title('Model Mean Absolute Error')
            ax2.set_xlabel('Epoch')
            ax2.set_ylabel('MAE')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # Save figure if path provided
            if save_path is not None:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                logger.info(f"Training history plot saved to {save_path}")
            
            # Show figure if requested
            if show:
                plt.show()
            else:
                plt.close()
                
        except ImportError:
            logger.warning("Matplotlib not available. Skipping plot generation.")
    
    def plot_prediction_error(self, X, Y, save_path=None, show=True):
        """
        Plot prediction error.
        
        Args:
            X: Input data
            Y: True output data
            save_path: Path to save the plot
            show: Whether to display the plot
        """
        if self.model is None:
            raise ValueError("Model not trained. Call fit() first.")
        
        try:
            import matplotlib.pyplot as plt
            
            # Ensure data has correct shape
            if len(X.shape) == 1:
                X = X.reshape(-1, 1)
            
            if len(Y.shape) == 1:
                Y = Y.reshape(-1, 1)
            
            # Make predictions
            Y_pred = self.predict(X)
            
            # Create figure with subplots
            n_plots = min(self.output_dim, 4)  # Limit number of output plots
            fig, axes = plt.subplots(1, n_plots, figsize=(5*n_plots, 5))
            
            if n_plots == 1:
                axes = [axes]  # Make it iterable
            
            for i in range(n_plots):
                ax = axes[i]
                
                # Plot true vs predicted
                ax.scatter(Y[:, i], Y_pred[:, i], alpha=0.7)
                
                # Plot perfect prediction line
                min_val = min(np.min(Y[:, i]), np.min(Y_pred[:, i]))
                max_val = max(np.max(Y[:, i]), np.max(Y_pred[:, i]))
                ax.plot([min_val, max_val], [min_val, max_val], 'r--')
                
                # Calculate metrics for this output
                from sklearn.metrics import r2_score, mean_squared_error
                r2 = r2_score(Y[:, i], Y_pred[:, i])
                rmse = np.sqrt(mean_squared_error(Y[:, i], Y_pred[:, i]))
                
                # Add metrics to plot
                ax.text(0.05, 0.95, f'R² = {r2:.4f}\nRMSE = {rmse:.4f}',
                       transform=ax.transAxes, verticalalignment='top',
                       bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
                
                ax.set_title(f'Output {i+1}')
                ax.set_xlabel('True Value')
                ax.set_ylabel('Predicted Value')
                ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # Save figure if path provided
            if save_path is not None:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                logger.info(f"Prediction error plot saved to {save_path}")
            
            # Show figure if requested
            if show:
                plt.show()
            else:
                plt.close()
                
        except ImportError:
            logger.warning("Matplotlib not available. Skipping plot generation.")
    
    def get_gradient(self, X):
        """
        Compute gradient of model output with respect to inputs.
        
        Args:
            X: Input data of shape (n_samples, input_dim)
            
        Returns:
            Gradient of shape (n_samples, output_dim, input_dim)
        """
        if self.model is None:
            raise ValueError("Model not trained. Call fit() first.")
        
        # Ensure X has correct shape
        if len(X.shape) == 1:
            X = X.reshape(-1, 1)
        
        # Normalize inputs
        X_norm = self._normalize_inputs(X)
        
        # Compute gradient for each sample and output
        n_samples = len(X_norm)
        gradients = np.zeros((n_samples, self.output_dim, self.input_dim))
        
        for i in range(n_samples):
            x_i = X_norm[i:i+1]
            x_tensor = self.torch.tensor(x_i, dtype=self.torch.float32, requires_grad=True)
            x_tensor = x_tensor.to(self.device)
            
            # Set model to evaluation mode
            self.model.eval()
            
            # Forward pass
            y_pred = self.model(x_tensor)
            
            # Compute gradient for each output dimension
            for j in range(self.output_dim):
                # Zero out previous gradients
                if x_tensor.grad is not None:
                    x_tensor.grad.zero_()
                
                # Backward pass for this output
                y_pred[0, j].backward(retain_graph=(j < self.output_dim - 1))
                
                # Get gradient
                grad_j = x_tensor.grad.cpu().numpy()[0]
                gradients[i, j, :] = grad_j
        
        # Apply scaling if inputs/outputs were normalized
        if self.normalize_inputs and self.normalize_outputs:
            for i in range(self.output_dim):
                gradients[:, i, :] = gradients[:, i, :] * (self.y_std[i] / self.x_std)
        
        return gradients


# Factory function to create neural network surrogate models
def create_neural_network(framework='tensorflow', **kwargs):
    """
    Create a neural network surrogate model using the specified framework.
    
    Args:
        framework: Deep learning framework to use ('tensorflow' or 'pytorch')
        **kwargs: Additional arguments for the neural network model
        
    Returns:
        Neural network surrogate model instance
    """
    if framework.lower() == 'tensorflow':
        try:
            return TensorFlowNeuralNetwork(**kwargs)
        except ImportError:
            logger.warning("TensorFlow not available. Trying PyTorch instead.")
            framework = 'pytorch'
    
    if framework.lower() == 'pytorch':
        try:
            return PyTorchNeuralNetwork(**kwargs)
        except ImportError:
            logger.error("Neither TensorFlow nor PyTorch available. Cannot create neural network surrogate.")
            raise ImportError("Either TensorFlow or PyTorch is required for neural network surrogate models.")
    
    raise ValueError(f"Unknown framework: {framework}. Supported frameworks: 'tensorflow', 'pytorch'")


# Example usage
if __name__ == "__main__":
    # Generate some test data
    np.random.seed(42)
    
    # Example: 2D input, 1D output
    X = np.random.rand(1000, 2) * 10 - 5  # Range: [-5, 5]
    Y = np.sin(X[:, 0]) * np.cos(X[:, 1]) + 0.1 * np.random.randn(1000, 1)
    
    # Split data
    n_train = 800
    X_train, X_test = X[:n_train], X[n_train:]
    Y_train, Y_test = Y[:n_train], Y[n_train:]
    
    try:
        # Try to create TensorFlow model
        print("Creating TensorFlow neural network...")
        nn_tf = create_neural_network(
            framework='tensorflow',
            input_dim=2,
            output_dim=1,
            hidden_layers=[32, 32],
            activation='relu',
            learning_rate=0.001
        )
        
        # Train model
        nn_tf.fit(
            X_train, Y_train,
            validation_split=0.2,
            epochs=50,
            batch_size=32,
            verbose=1
        )
        
        # Evaluate model
        metrics_tf = nn_tf.evaluate(X_test, Y_test)
        print(f"TensorFlow model metrics: {metrics_tf}")
        
        # Plot training history
        nn_tf.plot_training_history()
        
        # Plot prediction error
        nn_tf.plot_prediction_error(X_test, Y_test)
        
        # Get gradients
        grads_tf = nn_tf.get_gradient(X_test[:5])
        print(f"TensorFlow gradients shape: {grads_tf.shape}")
        
    except ImportError:
        print("TensorFlow not available. Skipping TensorFlow example.")
    
    try:
        # Try to create PyTorch model
        print("\nCreating PyTorch neural network...")
        nn_pt = create_neural_network(
            framework='pytorch',
            input_dim=2,
            output_dim=1,
            hidden_layers=[32, 32],
            activation='relu',
            learning_rate=0.001
        )
        
        # Train model
        nn_pt.fit(
            X_train, Y_train,
            validation_split=0.2,
            epochs=50,
            batch_size=32,
            verbose=1
        )
        
        # Evaluate model
        metrics_pt = nn_pt.evaluate(X_test, Y_test)
        print(f"PyTorch model metrics: {metrics_pt}")
        
        # Plot training history
        nn_pt.plot_training_history()
        
        # Plot prediction error
        nn_pt.plot_prediction_error(X_test, Y_test)
        
        # Get gradients
        grads_pt = nn_pt.get_gradient(X_test[:5])
        print(f"PyTorch gradients shape: {grads_pt.shape}")
        
    except ImportError:
        print("PyTorch not available. Skipping PyTorch example.")