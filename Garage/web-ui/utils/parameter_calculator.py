import math

class ParameterCalculator:
    """
    Class to calculate various parameters for the intake system
    """
    def __init__(self):
        # Constants
        self.sound_speed = 343.0  # m/s (speed of sound in air at 20°C)
        self.air_density = 1.2  # kg/m³
    
    def calculate(self, data):
        """
        Calculate derived parameters from input data
        
        Args:
            data: Dictionary with intake parameters
        
        Returns:
            Dictionary with calculated results
        """
        results = {}
        
        # Extract parameters
        runner_length = data.get('runner_length', 150.0) / 1000.0  # convert mm to m
        runner_diameter = data.get('runner_diameter', 35.0) / 1000.0  # convert mm to m
        plenum_volume = data.get('plenum_volume', 2000.0) / 1000000.0  # convert cc to m³
        engine_rpm = data.get('engine_rpm', 6000)
        
        # Calculate runner cross-sectional area
        runner_area = math.pi * (runner_diameter/2)**2
        
        # Calculate Helmholtz resonator frequency
        # f = c/(2π) * √(A/(V*L))
        # where c is sound speed, A is runner area, V is plenum volume, L is runner length
        helmholtz_freq = self.sound_speed/(2*math.pi) * math.sqrt(runner_area / (plenum_volume * runner_length))
        
        # Calculate resonant RPM (assuming 2 cycles per rotation for 4-stroke engine)
        # RPM = 60 * f / 2
        resonant_rpm = 60 * helmholtz_freq / 2
        
        # Calculate velocity at given RPM
        # Use basic rule of thumb: engine displacement * RPM / (number of cylinders * 2 * 60)
        # This is a simplified approximation
        displacement_per_cylinder = 0.0005  # m³ (500cc example)
        flow_rate = displacement_per_cylinder * engine_rpm / (2 * 60)  # m³/s
        velocity = flow_rate / runner_area  # m/s
        
        # Store results
        results['resonant_rpm'] = resonant_rpm
        results['helmholtz_freq'] = helmholtz_freq
        results['velocity'] = velocity
        
        return results
