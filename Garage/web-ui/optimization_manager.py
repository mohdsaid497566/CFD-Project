import reactpy as rp
import numpy as np
import math
import time
import random

class Optimization_Manager:
    """Manages optimization workflows for the web interface"""
    
    def __init__(self):
        self.parameters = {
            'L4': 3.0,
            'L5': 3.0,
            'alpha1': 15.0,
            'alpha2': 15.0,
            'alpha3': 15.0
        }
        self.bounds = {
            'L4': [1.0, 5.0],
            'L5': [1.0, 5.0],
            'alpha1': [5.0, 30.0],
            'alpha2': [5.0, 30.0],
            'alpha3': [5.0, 30.0]
        }
        self.algorithm = "genetic"
        self.population_size = 30
        self.generations = 20
        self.objective = "pressure_drop"
        self.optimization_running = False
        self.convergence_data = {
            'generations': [],
            'best_fitness': [],
            'avg_fitness': []
        }
        
    def render(self):
        """Render the optimization manager UI"""
        # Parameters section
        parameters_section = rp.html.div(
            {"className": "optimization-section"},
            [
                rp.html.h3("Optimization Parameters"),
                self._create_parameter_inputs(),
                self._create_bounds_inputs()
            ]
        )
        
        # Algorithm settings
        algorithm_section = rp.html.div(
            {"className": "optimization-section"},
            [
                rp.html.h3("Algorithm Settings"),
                self._create_algorithm_settings()
            ]
        )
        
        # Objective function
        objective_section = rp.html.div(
            {"className": "optimization-section"},
            [
                rp.html.h3("Objective Function"),
                self._create_objective_settings()
            ]
        )
        
        # Control buttons
        controls_section = rp.html.div(
            {"className": "optimization-section"},
            [
                rp.html.h3("Controls"),
                self._create_control_buttons()
            ]
        )
        
        # Status and results
        results_section = rp.html.div(
            {"className": "optimization-section"},
            [
                rp.html.h3("Results"),
                self._create_results_display()
            ]
        )
        
        return rp.html.div(
            {"className": "optimization-manager"},
            [
                parameters_section,
                algorithm_section,
                objective_section,
                controls_section,
                results_section
            ]
        )
    
    def _create_parameter_inputs(self):
        """Create inputs for parameter values"""
        parameter_inputs = []
        
        for param_name, value in self.parameters.items():
            parameter_inputs.append(
                rp.html.div(
                    {"className": "parameter-input"},
                    [
                        rp.html.label({"htmlFor": f"opt-param-{param_name}"}, f"{param_name}:"),
                        rp.html.input({
                            "id": f"opt-param-{param_name}",
                            "type": "number",
                            "value": str(value),
                            "step": "0.1",
                            "disabled": self.optimization_running
                        })
                    ]
                )
            )
        
        return rp.html.div(
            {"className": "parameter-inputs"},
            parameter_inputs
        )
    
    def _create_bounds_inputs(self):
        """Create inputs for parameter bounds"""
        bounds_inputs = []
        
        for param_name, bound in self.bounds.items():
            bounds_inputs.append(
                rp.html.div(
                    {"className": "bounds-input"},
                    [
                        rp.html.span({"className": "param-name"}, f"{param_name} bounds:"),
                        rp.html.div(
                            {"className": "bound-range"},
                            [
                                rp.html.input({
                                    "type": "number",
                                    "value": str(bound[0]),
                                    "className": "min-bound",
                                    "step": "0.1",
                                    "disabled": self.optimization_running
                                }),
                                rp.html.span(" to "),
                                rp.html.input({
                                    "type": "number",
                                    "value": str(bound[1]),
                                    "className": "max-bound",
                                    "step": "0.1",
                                    "disabled": self.optimization_running
                                })
                            ]
                        )
                    ]
                )
            )
        
        return rp.html.div(
            {"className": "bounds-inputs"},
            bounds_inputs
        )
    
    def _create_algorithm_settings(self):
        """Create algorithm settings controls"""
        return rp.html.div(
            {"className": "algorithm-settings"},
            [
                rp.html.div(
                    {"className": "setting-row"},
                    [
                        rp.html.label({"htmlFor": "algorithm-type"}, "Algorithm:"),
                        rp.html.select(
                            {
                                "id": "algorithm-type",
                                "value": self.algorithm,
                                "disabled": self.optimization_running
                            },
                            [
                                rp.html.option({"value": "genetic"}, "Genetic Algorithm"),
                                rp.html.option({"value": "pso"}, "Particle Swarm"),
                                rp.html.option({"value": "bayesian"}, "Bayesian Optimization")
                            ]
                        )
                    ]
                ),
                rp.html.div(
                    {"className": "setting-row"},
                    [
                        rp.html.label({"htmlFor": "population-size"}, "Population Size:"),
                        rp.html.input({
                            "id": "population-size",
                            "type": "number",
                            "value": str(self.population_size),
                            "min": "10",
                            "disabled": self.optimization_running
                        })
                    ]
                ),
                rp.html.div(
                    {"className": "setting-row"},
                    [
                        rp.html.label({"htmlFor": "generations"}, "Generations:"),
                        rp.html.input({
                            "id": "generations",
                            "type": "number",
                            "value": str(self.generations),
                            "min": "5",
                            "disabled": self.optimization_running
                        })
                    ]
                )
            ]
        )
    
    def _create_objective_settings(self):
        """Create objective function settings"""
        return rp.html.div(
            {"className": "objective-settings"},
            [
                rp.html.div(
                    {"className": "setting-row"},
                    [
                        rp.html.label({"htmlFor": "objective-function"}, "Objective:"),
                        rp.html.select(
                            {
                                "id": "objective-function",
                                "value": self.objective,
                                "disabled": self.optimization_running
                            },
                            [
                                rp.html.option({"value": "pressure_drop"}, "Minimize Pressure Drop"),
                                rp.html.option({"value": "flow_rate"}, "Maximize Flow Rate"),
                                rp.html.option({"value": "flow_uniformity"}, "Maximize Flow Uniformity")
                            ]
                        )
                    ]
                ),
                rp.html.div(
                    {"className": "radio-options"},
                    [
                        rp.html.div(
                            {"className": "radio-option"},
                            [
                                rp.html.input({
                                    "type": "radio",
                                    "id": "minimize",
                                    "name": "opt-direction",
                                    "value": "minimize",
                                    "checked": True,
                                    "disabled": self.optimization_running
                                }),
                                rp.html.label({"htmlFor": "minimize"}, "Minimize")
                            ]
                        ),
                        rp.html.div(
                            {"className": "radio-option"},
                            [
                                rp.html.input({
                                    "type": "radio",
                                    "id": "maximize",
                                    "name": "opt-direction",
                                    "value": "maximize",
                                    "disabled": self.optimization_running
                                }),
                                rp.html.label({"htmlFor": "maximize"}, "Maximize")
                            ]
                        )
                    ]
                )
            ]
        )
    
    def _create_control_buttons(self):
        """Create optimization control buttons"""
        return rp.html.div(
            {"className": "control-buttons"},
            [
                rp.html.button(
                    {
                        "className": "start-button",
                        "disabled": self.optimization_running
                    },
                    "Start Optimization"
                ),
                rp.html.button(
                    {
                        "className": "stop-button",
                        "disabled": not self.optimization_running
                    },
                    "Stop"
                ),
                rp.html.button(
                    {
                        "className": "export-button",
                        "disabled": self.optimization_running
                    },
                    "Export Results"
                )
            ]
        )
    
    def _create_results_display(self):
        """Create the results display section"""
        if not self.convergence_data['generations']:
            # No data yet
            return rp.html.div(
                {"className": "results-placeholder"},
                "Run optimization to see results here"
            )
        
        # In a real app, this would render a chart
        return rp.html.div(
            {"className": "results-display"},
            [
                rp.html.div(
                    {"className": "chart-placeholder"},
                    "Convergence chart would be displayed here"
                ),
                rp.html.div(
                    {"className": "best-solution"},
                    [
                        rp.html.h4("Best Solution:"),
                        rp.html.div("Parameter values and performance metrics would be shown here")
                    ]
                )
            ]
        )
