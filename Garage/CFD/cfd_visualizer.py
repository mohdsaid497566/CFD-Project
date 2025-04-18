"""
CFD Visualizer module for the Intake CFD Optimization Suite.

This module provides utilities for visualizing CFD results, including
plotting residuals, force coefficients, and exporting to various formats.
"""

import os
import sys
import logging
import tempfile
import subprocess
from typing import Dict, List, Tuple, Optional, Any, Union
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("cfd_visualizer")

class CFDVisualizer:
    """Class for visualizing CFD results."""
    
    def __init__(self, case_dir: str, output_dir: Optional[str] = None):
        """
        Initialize a CFD visualizer.
        
        Args:
            case_dir: Directory containing the CFD case
            output_dir: Directory for saving visualization results (default: case_dir/visualizations)
        """
        self.case_dir = case_dir
        self.output_dir = output_dir or os.path.join(case_dir, "visualizations")
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Check if case directory exists
        if not os.path.isdir(case_dir):
            raise FileNotFoundError(f"Case directory not found: {case_dir}")
    
    def plot_residuals(self, save_path: Optional[str] = None) -> str:
        """
        Plot residual history from OpenFOAM run.
        
        Args:
            save_path: Path to save the plot (default: output_dir/residuals.png)
            
        Returns:
            Path to the saved plot
        """
        residuals_file = os.path.join(self.case_dir, 'postProcessing', 'residuals', '0', 'residuals.dat')
        
        if not os.path.exists(residuals_file):
            logger.warning(f"Residuals file not found: {residuals_file}")
            return ""
        
        # Load residuals data
        try:
            data = np.loadtxt(residuals_file, skiprows=1)
            
            # Create plot
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Read header to get variable names
            with open(residuals_file, 'r') as f:
                header = f.readline().strip().split()
            
            # Plot each residual on log scale
            for i, var in enumerate(header[1:], 1):  # Skip first column (time/iteration)
                if i < data.shape[1]:
                    ax.semilogy(data[:, 0], data[:, i], label=var)
            
            ax.set_xlabel('Iteration')
            ax.set_ylabel('Residual')
            ax.set_title('Residual History')
            ax.grid(True, which="both", ls="-")
            ax.legend()
            
            # Save plot
            save_path = save_path or os.path.join(self.output_dir, 'residuals.png')
            fig.savefig(save_path, dpi=300, bbox_inches='tight')
            plt.close(fig)
            
            logger.info(f"Residual plot saved to {save_path}")
            return save_path
        
        except Exception as e:
            logger.error(f"Error plotting residuals: {e}")
            return ""

    def plot_force_coefficients(self, save_path: Optional[str] = None) -> str:
        """
        Plot force coefficients from OpenFOAM run.
        
        Args:
            save_path: Path to save the plot (default: output_dir/force_coefficients.png)
            
        Returns:
            Path to the saved plot
        """
        force_file = os.path.join(self.case_dir, 'postProcessing', 'forceCoeffs', '0', 'coefficient.dat')
        
        if not os.path.exists(force_file):
            logger.warning(f"Force coefficients file not found: {force_file}")
            return ""
        
        # Load force data
        try:
            data = np.loadtxt(force_file, skiprows=1)
            
            # Create plot
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Read header to get variable names
            with open(force_file, 'r') as f:
                header = f.readline().strip().split()
            
            # Plot each coefficient
            for i, var in enumerate(header[1:], 1):  # Skip first column (time/iteration)
                if i < data.shape[1] and ('Cd' in var or 'Cl' in var or 'Cm' in var):
                    ax.plot(data[:, 0], data[:, i], label=var)
            
            ax.set_xlabel('Time/Iteration')
            ax.set_ylabel('Coefficient Value')
            ax.set_title('Force Coefficients')
            ax.grid(True)
            ax.legend()
            
            # Save plot
            save_path = save_path or os.path.join(self.output_dir, 'force_coefficients.png')
            fig.savefig(save_path, dpi=300, bbox_inches='tight')
            plt.close(fig)
            
            logger.info(f"Force coefficients plot saved to {save_path}")
            return save_path
        
        except Exception as e:
            logger.error(f"Error plotting force coefficients: {e}")
            return ""
    
    def create_paraview_state(self, vtk_dir: Optional[str] = None, save_path: Optional[str] = None) -> str:
        """
        Create a ParaView state file for visualizing the CFD case.
        
        Args:
            vtk_dir: Directory containing VTK files (default: case_dir/VTK)
            save_path: Path to save the state file (default: output_dir/paraview_state.pvsm)
            
        Returns:
            Path to the saved state file
        """
        vtk_dir = vtk_dir or os.path.join(self.case_dir, 'VTK')
        if not os.path.exists(vtk_dir):
            logger.warning(f"VTK directory not found: {vtk_dir}")
            return ""
        
        # Find VTK files
        vtk_files = []
        for root, _, files in os.walk(vtk_dir):
            for file in files:
                if file.endswith('.vtk'):
                    vtk_files.append(os.path.join(root, file))
        
        if not vtk_files:
            logger.warning(f"No VTK files found in {vtk_dir}")
            return ""
        
        try:
            # Create a basic Python script for ParaView
            pvpy_script = f"""
from paraview.simple import *

# Create a new 'Render View'
renderView = GetRenderView()
renderView.ViewSize = [1200, 800]
renderView.CenterOfRotation = [0.0, 0.0, 0.0]
renderView.CameraPosition = [1.0, 1.0, 1.0]
renderView.CameraFocalPoint = [0.0, 0.0, 0.0]
renderView.CameraViewUp = [0.0, 0.0, 1.0]
renderView.Background = [0.32, 0.34, 0.43]

# Load data
reader = LegacyVTKReader(FileNames=['{vtk_files[0]}'])
Show(reader, renderView)

# Apply a better color map for velocity
velocity = ['U_X', 'U_Y', 'U_Z']
if velocity[0] in reader.PointArrayStatus:
    ColorBy(reader, ('POINTS', velocity[0]))
    velocityLUT = GetColorTransferFunction(velocity[0])
    velocityLUT.ApplyPreset('Blue to Red Rainbow', True)
    velocityLUT.RescaleTransferFunction(-10.0, 10.0)
    
    # Show color bar
    velocityLUTColorBar = GetScalarBar(velocityLUT, renderView)
    velocityLUTColorBar.Title = 'Velocity X'
    velocityLUTColorBar.ComponentTitle = 'm/s'
    velocityLUTColorBar.Visibility = 1

# Add a plane for slicing
slice1 = Slice(Input=reader)
slice1.SliceType = 'Plane'
slice1.SliceOffsetValues = [0.0]
slice1.SliceType.Origin = [0.0, 0.0, 0.0]
slice1.SliceType.Normal = [0.0, 1.0, 0.0]
Show(slice1, renderView)

# Add streamlines if velocity field available
if all(v in reader.PointArrayStatus for v in velocity):
    # Create a merged U vector for streamlines
    calc = Calculator(Input=reader)
    calc.Function = 'U_X*iHat+U_Y*jHat+U_Z*kHat'
    calc.ResultArrayName = 'U'
    
    # Create streamlines
    stream = StreamTracer(Input=calc, SeedType='Point Source')
    stream.Vectors = ['POINTS', 'U']
    stream.MaximumStreamlineLength = 10.0
    stream.SeedType.Center = [0.0, 0.0, 0.0]
    stream.SeedType.NumberOfPoints = 100
    stream.SeedType.Radius = 0.5
    Show(stream, renderView)
    
    # Color streamlines by velocity magnitude
    ColorBy(stream, ('POINTS', 'U', 'Magnitude'))
    streamLUT = GetColorTransferFunction('U')
    streamLUT.ApplyPreset('Blue to Red Rainbow', True)

# Set view to fit data
ResetCamera()

# Save state
SaveState('{save_path}')
"""
            
            # Create a temporary script file
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.py') as tmp:
                tmp.write(pvpy_script)
                script_path = tmp.name
            
            try:
                # Check if pvpython is available
                if shutil.which('pvpython'):
                    # Run the script with pvpython
                    save_path = save_path or os.path.join(self.output_dir, 'paraview_state.pvsm')
                    subprocess.run(['pvpython', script_path, save_path], check=True)
                    logger.info(f"ParaView state saved to {save_path}")
                    return save_path
                else:
                    # Just save the script if pvpython is not available
                    save_path = save_path or os.path.join(self.output_dir, 'paraview_setup.py')
                    shutil.copy(script_path, save_path)
                    logger.info(f"ParaView script saved to {save_path} (pvpython not found to generate state file)")
                    return save_path
            finally:
                # Clean up temp file
                os.unlink(script_path)
                
        except Exception as e:
            logger.error(f"Error creating ParaView state: {e}")
            return ""

    def get_case_summary_plots(self) -> Dict[str, str]:
        """
        Generate standard plots for case summary.
        
        Returns:
            Dictionary mapping plot types to file paths
        """
        plots = {}
        
        # Generate residual plot
        residuals_path = self.plot_residuals()
        if residuals_path:
            plots['residuals'] = residuals_path
        
        # Generate force coefficients plot
        forces_path = self.plot_force_coefficients()
        if forces_path:
            plots['force_coefficients'] = forces_path
        
        # Try to create ParaView state
        paraview_path = self.create_paraview_state()
        if paraview_path:
            plots['paraview_state'] = paraview_path
        
        return plots

    @staticmethod
    def generate_report(case_dir: str, output_path: Optional[str] = None) -> str:
        """
        Generate an HTML report for a CFD case.
        
        Args:
            case_dir: Directory containing the CFD case
            output_path: Path to save the report (default: case_dir/report.html)
            
        Returns:
            Path to the generated report
        """
        try:
            # Create visualizer and generate plots
            visualizer = CFDVisualizer(case_dir)
            plots = visualizer.get_case_summary_plots()
            
            # Get case summary
            from .cfd_runner import get_case_summary
            summary = get_case_summary(case_dir)
            
            # Create HTML report
            output_path = output_path or os.path.join(case_dir, 'report.html')
            
            with open(output_path, 'w') as f:
                f.write(f"""<!DOCTYPE html>
<html>
<head>
    <title>CFD Case Report: {os.path.basename(case_dir)}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333366; }}
        h2 {{ color: #333366; margin-top: 20px; }}
        .section {{ margin-bottom: 30px; }}
        .plot {{ margin: 20px 0; text-align: center; }}
        .plot img {{ max-width: 100%; border: 1px solid #ddd; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ text-align: left; padding: 8px; border-bottom: 1px solid #ddd; }}
        tr:nth-child(even) {{ background-color: #f2f2f2; }}
        th {{ background-color: #333366; color: white; }}
    </style>
</head>
<body>
    <h1>CFD Case Report: {os.path.basename(case_dir)}</h1>
    
    <div class="section">
        <h2>Case Summary</h2>
        <table>
            <tr><th>Property</th><th>Value</th></tr>
            <tr><td>Case Directory</td><td>{case_dir}</td></tr>
            <tr><td>Status</td><td>{summary.get('status', 'Unknown')}</td></tr>
            <tr><td>Last Run</td><td>{summary.get('last_run', 'Unknown')}</td></tr>
        </table>
    </div>
""")

                # Add plots to report
                if plots:
                    f.write("""    <div class="section">
        <h2>Plots</h2>
""")
                    
                    # Copy plots to relative paths and include in HTML
                    for plot_type, plot_path in plots.items():
                        if os.path.exists(plot_path):
                            plot_basename = os.path.basename(plot_path)
                            # Copy to same directory as report
                            report_dir = os.path.dirname(output_path)
                            dest_path = os.path.join(report_dir, plot_basename)
                            if plot_path != dest_path:
                                shutil.copy(plot_path, dest_path)
                            
                            if plot_path.endswith(('.png', '.jpg', '.jpeg', '.gif')):
                                f.write(f"""        <div class="plot">
            <h3>{plot_type.replace('_', ' ').title()}</h3>
            <img src="{plot_basename}" alt="{plot_type}" />
        </div>
""")
                            elif plot_path.endswith('.pvsm'):
                                f.write(f"""        <div class="plot">
            <h3>ParaView State</h3>
            <p>ParaView state file: <a href="{plot_basename}">{plot_basename}</a></p>
        </div>
""")
                    
                    f.write("    </div>\n")
                
                # Add result files section
                if 'result_files' in summary and summary['result_files']:
                    f.write("""    <div class="section">
        <h2>Result Files</h2>
        <table>
            <tr><th>File</th><th>Size</th></tr>
""")
                    
                    for file_path in summary['result_files']:
                        try:
                            file_size = os.path.getsize(file_path)
                            if file_size < 1024:
                                size_str = f"{file_size} B"
                            elif file_size < 1024 * 1024:
                                size_str = f"{file_size / 1024:.1f} KB"
                            else:
                                size_str = f"{file_size / (1024 * 1024):.1f} MB"
                        except:
                            size_str = "Unknown"
                            
                        f.write(f"""            <tr><td>{os.path.basename(file_path)}</td><td>{size_str}</td></tr>
""")
                    
                    f.write("""        </table>
    </div>
""")
                
                # Close HTML
                f.write("""</body>
</html>
""")
            
            logger.info(f"Report generated at {output_path}")
            return output_path
        
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return ""

def launch_paraview(vtk_dir: str) -> bool:
    """
    Launch ParaView for visualizing VTK files.
    
    Args:
        vtk_dir: Directory containing VTK files
    
    Returns:
        True if ParaView was launched successfully
    """
    if not os.path.isdir(vtk_dir):
        logger.error(f"VTK directory not found: {vtk_dir}")
        return False
    
    try:
        # Find a VTK file
        vtk_file = None
        for root, _, files in os.walk(vtk_dir):
            for file in files:
                if file.endswith('.vtk'):
                    vtk_file = os.path.join(root, file)
                    break
            if vtk_file:
                break
        
        if not vtk_file:
            logger.error(f"No VTK files found in {vtk_dir}")
            return False
        
        # Try to launch ParaView
        paraview_cmd = 'paraview'
        if not shutil.which(paraview_cmd):
            logger.error("ParaView executable not found in PATH")
            return False
        
        subprocess.Popen([paraview_cmd, vtk_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logger.info(f"Launched ParaView with {vtk_file}")
        return True
        
    except Exception as e:
        logger.error(f"Error launching ParaView: {e}")
        return False

def extract_visualization_data(case_dir: str) -> Dict[str, Any]:
    """
    Extract visualization data from CFD case into a format suitable for GUI plotting.
    
    Args:
        case_dir: Directory containing the CFD case
    
    Returns:
        Dictionary with visualization data
    """
    data = {
        "residuals": None,
        "forces": None,
        "field_summary": {}
    }
    
    try:
        # Extract residuals
        residuals_file = os.path.join(case_dir, 'postProcessing', 'residuals', '0', 'residuals.dat')
        if os.path.exists(residuals_file):
            with open(residuals_file, 'r') as f:
                header = f.readline().strip().split()
                lines = f.readlines()
            
            residuals = {key: [] for key in header}
            for line in lines:
                values = line.strip().split()
                for i, key in enumerate(header):
                    if i < len(values):
                        try:
                            residuals[key].append(float(values[i]))
                        except ValueError:
                            residuals[key].append(None)
            
            data["residuals"] = residuals
        
        # Extract forces
        force_file = os.path.join(case_dir, 'postProcessing', 'forceCoeffs', '0', 'coefficient.dat')
        if os.path.exists(force_file):
            with open(force_file, 'r') as f:
                header = f.readline().strip().split()
                lines = f.readlines()
            
            forces = {key: [] for key in header}
            for line in lines:
                values = line.strip().split()
                for i, key in enumerate(header):
                    if i < len(values):
                        try:
                            forces[key].append(float(values[i]))
                        except ValueError:
                            forces[key].append(None)
            
            data["forces"] = forces
            
        # Get field summary (min/max values)
        # Look for the last time directory
        time_dirs = []
        for d in os.listdir(case_dir):
            if d.replace('.', '', 1).isdigit() and os.path.isdir(os.path.join(case_dir, d)):
                time_dirs.append(d)
        
        if time_dirs:
            # Find the directory with highest time value
            last_time_dir = max(time_dirs, key=lambda x: float(x))
            time_path = os.path.join(case_dir, last_time_dir)
            
            # Check for field files
            for field in ['U', 'p', 'k', 'epsilon']:
                field_path = os.path.join(time_path, field)
                if os.path.exists(field_path):
                    # Try to extract min/max values with foamDictionary
                    try:
                        process = subprocess.run(
                            ['foamDictionary', field_path, '-entry', 'internalField'],
                            capture_output=True, text=True, check=False
                        )
                        if process.returncode == 0:
                            output = process.stdout.strip()
                            
                            # Simple parsing for uniform fields
                            if "uniform" in output:
                                data["field_summary"][field] = {
                                    "type": "uniform",
                                    "value": output.split("uniform")[1].strip().strip(";")
                                }
                            # For non-uniform fields, indicate data is available but too large to include
                            else:
                                data["field_summary"][field] = {
                                    "type": "nonuniform",
                                    "available": True,
                                    "size": os.path.getsize(field_path)
                                }
                    except Exception as e:
                        logger.warning(f"Error extracting field data for {field}: {e}")
                        data["field_summary"][field] = {
                            "type": "unknown",
                            "error": str(e)
                        }
    
    except Exception as e:
        logger.error(f"Error extracting visualization data: {e}")
    
    return data
