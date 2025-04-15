#!/usr/bin/env python3
# filepath: /mnt/c/Users/Mohammed/Desktop/Intake-CFD-Project/nx/benchmark_tests.py

import os
import sys
import time
import argparse
import numpy as np
import subprocess
import json
import gmsh
from datetime import datetime
import multiprocessing
import matplotlib.pyplot as plt
import platform
from pathlib import Path
import shutil

class BenchmarkSuite:
    """
    Comprehensive benchmarking suite for Intake-CFD mesh generation and processing tools.
    """
    
    def __init__(self, output_dir="./benchmark_results"):
        """Initialize the benchmark suite."""
        self.output_dir = output_dir
        self.results = {}
        self.system_info = self._get_system_info()
        os.makedirs(output_dir, exist_ok=True)
    
    def _get_system_info(self):
        """Gather system information for benchmarking context."""
        info = {
            "platform": platform.platform(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "cpu_count": os.cpu_count(),
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        
        # Try to get GPU information if available
        try:
            if shutil.which("nvidia-smi"):
                gpu_info = subprocess.check_output(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv"]).decode("utf-8")
                info["gpu"] = gpu_info.strip()
        except:
            info["gpu"] = "Unknown or not available"
            
        return info
    
    def create_test_geometries(self):
        """Create test geometries of varying complexity for benchmarking."""
        print("Creating test geometries...")
        
        # Create directory for test data
        test_dir = os.path.join(self.output_dir, "test_geometries")
        os.makedirs(test_dir, exist_ok=True)
        
        # Initialize Gmsh
        gmsh.initialize()
        gmsh.option.setNumber("General.Terminal", 0)
        
        # Simple geometry: box
        simple_file = os.path.join(test_dir, "simple_box.stp")
        if not os.path.exists(simple_file):
            print("Creating simple box geometry...")
            gmsh.model.add("simple_box")
            box = gmsh.model.occ.addBox(0, 0, 0, 1, 1, 1)
            gmsh.model.occ.synchronize()
            gmsh.write(simple_file)
        
        # Medium complexity: intake-like tube with a bend
        medium_file = os.path.join(test_dir, "medium_intake.stp")
        if not os.path.exists(medium_file):
            print("Creating medium complexity intake geometry...")
            gmsh.model.add("medium_intake")
            
            # Create a tube with a bend
            cylinder1 = gmsh.model.occ.addCylinder(0, 0, 0, 5, 0, 0, 0.5)
            cylinder2 = gmsh.model.occ.addCylinder(5, 0, 0, 0, 3, 0, 0.5)
            fillet = gmsh.model.occ.fillet([cylinder1, cylinder2], [5], [0.2])
            
            gmsh.model.occ.synchronize()
            gmsh.write(medium_file)
        
        # Complex geometry: intake manifold with multiple branches
        complex_file = os.path.join(test_dir, "complex_manifold.stp")
        if not os.path.exists(complex_file):
            print("Creating complex manifold geometry...")
            gmsh.model.add("complex_manifold")
            
            # Main intake tube
            main_tube = gmsh.model.occ.addCylinder(0, 0, 0, 10, 0, 0, 0.8)
            
            # Branch tubes
            branch1 = gmsh.model.occ.addCylinder(3, 0, 0, 0, 4, 0, 0.4)
            branch2 = gmsh.model.occ.addCylinder(6, 0, 0, 0, 4, 0, 0.4)
            branch3 = gmsh.model.occ.addCylinder(9, 0, 0, 0, 4, 0, 0.4)
            
            # Fuse everything together
            gmsh.model.occ.fuse([(3, main_tube)], [(3, branch1), (3, branch2), (3, branch3)], removeTool=True)
            gmsh.model.occ.synchronize()
            gmsh.write(complex_file)
            
        # Very complex geometry: engine intake with plenum chamber and throttle body
        very_complex_file = os.path.join(test_dir, "engine_intake.stp")
        if not os.path.exists(very_complex_file):
            print("Creating very complex engine intake geometry...")
            gmsh.model.add("engine_intake")
            
            # Plenum chamber (ellipsoid)
            plenum = gmsh.model.occ.addSphere(5, 0, 0, 2)
            
            # Throttle body
            throttle_cylinder = gmsh.model.occ.addCylinder(5, 0, 0, 0, 0, 3, 0.7)
            
            # Intake runners
            runner1 = gmsh.model.occ.addCylinder(5, 1.5, 3, 3, 0, 0, 0.4)
            runner2 = gmsh.model.occ.addCylinder(5, 0.5, 3, 3, 0, 0, 0.4)
            runner3 = gmsh.model.occ.addCylinder(5, -0.5, 3, 3, 0, 0, 0.4)
            runner4 = gmsh.model.occ.addCylinder(5, -1.5, 3, 3, 0, 0, 0.4)
            
            # Intake trumpet
            trumpet = gmsh.model.occ.addCone(0, 0, 0, 5, 0, 0, 1.5, 0.8)
            
            # Fuse everything together
            gmsh.model.occ.fuse([(3, plenum)], 
                               [(3, throttle_cylinder), (3, runner1), (3, runner2), 
                                (3, runner3), (3, runner4), (3, trumpet)], 
                               removeTool=True)
                               
            gmsh.model.occ.synchronize()
            gmsh.write(very_complex_file)
            
        gmsh.finalize()
        print("Test geometries created successfully.")
        
        return {
            "simple": simple_file,
            "medium": medium_file,
            "complex": complex_file,
            "very_complex": very_complex_file
        }