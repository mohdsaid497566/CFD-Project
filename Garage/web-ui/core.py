"""
Core functionality module extracted from main.py
This provides the actual intake design and CFD calculations
"""
import numpy as np
import logging
import os
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import io
import base64

# Setup logging
def setup_logger():
    logger = logging.getLogger('IntakeCFD')
    logger.setLevel(logging.INFO)
    
    # Create console handler and set level
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(ch)
    
    return logger

class IntakeDesignTool:
    def __init__(self):
        self.logger = setup_logger()
        self.results = None
        self.intake_params = None
        self.intake_geometry = None
        self.cfd_results = None
        
    def design_intake(self, intake_height, intake_width, contraction_ratio, inlet_outlet_distance):
        """
        Design the intake based on given parameters
        """
        self.logger.info(f"Designing intake with parameters: height={intake_height}, width={intake_width}, "
                         f"contraction_ratio={contraction_ratio}, inlet_outlet_distance={inlet_outlet_distance}")
        
        self.intake_params = {
            'intake_height': intake_height,
            'intake_width': intake_width,
            'contraction_ratio': contraction_ratio,
            'inlet_outlet_distance': inlet_outlet_distance,
        }
        
        # Calculate outlet dimensions
        outlet_height = intake_height / contraction_ratio
        outlet_width = intake_width / contraction_ratio
        
        # Generate points for the intake profile (using Bezier curve)
        num_points = 50
        x_points = np.linspace(0, inlet_outlet_distance, num_points)
        
        # Create profile curves for height and width
        profile_height = self._generate_bezier_profile(intake_height, outlet_height, num_points)
        profile_width = self._generate_bezier_profile(intake_width, outlet_width, num_points)
        
        # Calculate area at each point
        areas = profile_height * profile_width
        
        # Calculate pressure and velocity (using Bernoulli's equation)
        # Assuming inlet velocity = 15 m/s and fluid density = 1.225 kg/m³
        inlet_velocity = 15
        fluid_density = 1.225
        inlet_area = intake_height * intake_width
        
        velocities = []
        pressures = []
        
        for area in areas:
            # From continuity equation: A1*V1 = A2*V2
            velocity = inlet_velocity * (inlet_area / area)
            velocities.append(velocity)
            
            # From Bernoulli's equation: P1 + 0.5*rho*V1² = P2 + 0.5*rho*V2²
            # Assuming P1 = 0 (gauge pressure), we can find P2
            pressure = 0.5 * fluid_density * (inlet_velocity**2 - velocity**2)
            pressures.append(pressure)
        
        # Store geometry
        self.intake_geometry = {
            'x_points': x_points,
            'profile_height': profile_height,
            'profile_width': profile_width,
            'areas': areas,
            'velocities': velocities,
            'pressures': pressures,
            'outlet_height': outlet_height,
            'outlet_width': outlet_width,
            'total_length': inlet_outlet_distance
        }
        
        # Calculate derived results
        self.results = {
            **self.intake_params,
            'outlet_height': outlet_height,
            'outlet_width': outlet_width,
            'total_length': inlet_outlet_distance,
            'pressure_drop': max(pressures) - min(pressures)
        }
        
        return True
    
    def _generate_bezier_profile(self, start_value, end_value, num_points):
        """
        Generate a Bezier curve profile from start_value to end_value
        """
        # Bezier curve with control points to create a smooth contraction
        t = np.linspace(0, 1, num_points)
        
        # Control points for a cubic Bezier curve
        # P0 = (0, start_value), P1 = (1/3, start_value), 
        # P2 = (2/3, end_value), P3 = (1, end_value)
        profile = (1-t)**3 * start_value + 3*(1-t)**2*t * start_value + \
                  3*(1-t)*t**2 * end_value + t**3 * end_value
                  
        return profile
    
    def run_cfd(self, inlet_velocity=15, fluid_density=1.225):
        """
        Run CFD simulation on the designed intake
        """
        if not self.intake_geometry:
            self.logger.error("Cannot run CFD without designing intake first")
            return False
            
        self.logger.info(f"Running CFD simulation with inlet velocity={inlet_velocity} m/s")
        
        # Get contraction ratio
        contraction_ratio = self.intake_params['contraction_ratio']
        
        # Calculate CFD results
        self.cfd_results = {
            'inlet_velocity': inlet_velocity,
            'outlet_velocity': inlet_velocity * contraction_ratio,
            'velocity_ratio': contraction_ratio,
            'efficiency': 100 - (5 / contraction_ratio),  # Simple efficiency model
            'pressure_recovery': 0.8 * (1 - 1/(contraction_ratio**2)),
            'max_pressure': max(self.intake_geometry['pressures']),
            'min_pressure': min(self.intake_geometry['pressures'])
        }
        
        # Update results with CFD data
        self.results.update(self.cfd_results)
        
        return True
    
    def get_results(self):
        """
        Get the combined design and CFD results
        """
        return self.results
    
    def generate_plots(self):
        """
        Generate plots of the intake design and CFD results
        """
        if not self.intake_geometry:
            return None
            
        plots = {}
        
        # Generate profile plot
        fig_profile = Figure(figsize=(10, 4))
        ax_profile = fig_profile.add_subplot(111)
        ax_profile.plot(self.intake_geometry['x_points'], self.intake_geometry['profile_height'], 
                        label='Height Profile')
        ax_profile.plot(self.intake_geometry['x_points'], self.intake_geometry['profile_width'], 
                        label='Width Profile')
        ax_profile.set_xlabel('Length (mm)')
        ax_profile.set_ylabel('Dimension (mm)')
        ax_profile.set_title('Intake Profiles')
        ax_profile.legend()
        ax_profile.grid(True)
        
        # Convert figure to base64 for embedding in HTML
        buffer = io.BytesIO()
        FigureCanvas(fig_profile).print_png(buffer)
        plot_data = base64.b64encode(buffer.getvalue()).decode('utf8')
        plots['profile'] = plot_data
        
        # Generate velocity plot
        fig_velocity = Figure(figsize=(10, 4))
        ax_velocity = fig_velocity.add_subplot(111)
        ax_velocity.plot(self.intake_geometry['x_points'], self.intake_geometry['velocities'])
        ax_velocity.set_xlabel('Length (mm)')
        ax_velocity.set_ylabel('Velocity (m/s)')
        ax_velocity.set_title('Velocity Profile')
        ax_velocity.grid(True)
        
        buffer = io.BytesIO()
        FigureCanvas(fig_velocity).print_png(buffer)
        plot_data = base64.b64encode(buffer.getvalue()).decode('utf8')
        plots['velocity'] = plot_data
        
        # Generate pressure plot
        fig_pressure = Figure(figsize=(10, 4))
        ax_pressure = fig_pressure.add_subplot(111)
        ax_pressure.plot(self.intake_geometry['x_points'], self.intake_geometry['pressures'])
        ax_pressure.set_xlabel('Length (mm)')
        ax_pressure.set_ylabel('Pressure (Pa)')
        ax_pressure.set_title('Pressure Profile')
        ax_pressure.grid(True)
        
        buffer = io.BytesIO()
        FigureCanvas(fig_pressure).print_png(buffer)
        plot_data = base64.b64encode(buffer.getvalue()).decode('utf8')
        plots['pressure'] = plot_data
        
        return plots
    
    def generate_3d_data(self):
        """
        Generate data for 3D visualization
        """
        if not self.intake_geometry:
            return None
            
        # Extract geometry data for 3D modeling
        x_points = self.intake_geometry['x_points'].tolist()
        height_profile = self.intake_geometry['profile_height'].tolist()
        width_profile = self.intake_geometry['profile_width'].tolist()
        
        # Create a structured data format for THREE.js
        visualization_data = {
            'x_points': x_points,
            'height_profile': height_profile,
            'width_profile': width_profile,
            'inlet_dims': [self.intake_params['intake_width'], self.intake_params['intake_height']],
            'outlet_dims': [self.results['outlet_width'], self.results['outlet_height']]
        }
        
        return visualization_data
