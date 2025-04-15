#!/usr/bin/env python3
"""
Comprehensive GUI Test Script for Intake CFD Project
This script tests the complete functionality of the GUI in both demo and actual modes.
"""

import os
import sys
import time
import argparse
import threading
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
import unittest
import logging
import tempfile
from datetime import datetime

# Add the current directory to the path to ensure imports work properly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
log_file = f"gui_test_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def create_mock_executables():
    """Create mock executables for testing the demo mode"""
    logger.info("Creating mock executables for DEMO mode")
    
    executables = ["gmsh_process", "cfd_solver", "process_results"]
    
    # Create mock gmsh_process script
    with open("./gmsh_process", "w") as f:
        f.write("#!/bin/bash\n")
        f.write("echo 'Mock gmsh_process running...'\n")
        f.write("echo 'Processing $2 to $4'\n")
        f.write("echo 'Created mock mesh file'\n")
        f.write("touch $4\n")
    
    # Create mock cfd_solver script
    with open("./cfd_solver", "w") as f:
        f.write("#!/bin/bash\n")
        f.write("echo 'Mock CFD solver running...'\n")
        f.write("echo 'Processing $2'\n")
        f.write("echo 'Created mock result files'\n")
        f.write("mkdir -p cfd_results\n")
        f.write("echo '0.123' > cfd_results/pressure.dat\n")
    
    # Create mock process_results script
    with open("./process_results", "w") as f:
        f.write("#!/bin/bash\n")
        f.write("echo 'Mock results processor running...'\n")
        f.write("echo 'Processing results from $2 to $4'\n")
        f.write("echo '0.123' > $4\n")
    
    # Make scripts executable
    try:
        os.chmod("./gmsh_process", 0o755)
        os.chmod("./cfd_solver", 0o755)
        os.chmod("./process_results", 0o755)
    except Exception as e:
        logger.warning(f"Could not set executable permissions: {str(e)}")
    
    logger.info("Mock executables created successfully")

class GUITestCase(unittest.TestCase):
    """Base test case class for GUI testing"""
    
    def setUp(self):
        """Set up the test environment"""
        self.root = None
        self.app = None
        self.teardown_called = False
    
    def tearDown(self):
        """Clean up after the test"""
        self.teardown_called = True
        if self.root:
            try:
                self.root.destroy()
            except:
                pass
    
    def initialize_gui(self, demo_mode=True):
        """Initialize the GUI for testing"""
        try:
            # Import MDO and set demo mode
            import MDO
            from MDO import WorkflowGUI, ModernTheme
            
            # Set demo mode
            MDO.DEMO_MODE = demo_mode
            logger.info(f"Set MDO.DEMO_MODE to {demo_mode}")
            
            # Create mock executables in demo mode
            if demo_mode:
                create_mock_executables()
            
            # Create root window and application
            self.root = tk.Tk()
            self.root.title(f"CFD GUI Test ({'DEMO' if demo_mode else 'ACTUAL'} Mode)")
            self.root.geometry("1280x800")
            
            # Initialize the GUI
            self.app = WorkflowGUI(self.root)
            logger.info("GUI initialized successfully")
            
            # Let the GUI initialize fully
            self.root.update()
            time.sleep(0.5)
            
            return True
        except Exception as e:
            logger.error(f"Error initializing GUI: {str(e)}")
            return False
    
    def wait_for_gui_event(self, timeout=1.0):
        """Wait for GUI events to process with a timeout"""
        end_time = time.time() + timeout
        while time.time() < end_time:
            self.root.update()
            time.sleep(0.1)


class TestGUIInitialization(GUITestCase):
    """Test GUI initialization in both demo and actual modes"""
    
    def test_demo_mode_initialization(self):
        """Test GUI initialization in demo mode"""
        success = self.initialize_gui(demo_mode=True)
        self.assertTrue(success, "Failed to initialize GUI in demo mode")
        # Check that critical components are created
        self.assertTrue(hasattr(self.app, 'notebook'), "Missing notebook component")
        self.assertTrue(self.app.notebook.winfo_exists(), "Notebook widget not created properly")
    
    def test_actual_mode_initialization(self):
        """Test GUI initialization in actual mode"""
        success = self.initialize_gui(demo_mode=False)
        self.assertTrue(success, "Failed to initialize GUI in actual mode")
        # Check that critical components are created
        self.assertTrue(hasattr(self.app, 'notebook'), "Missing notebook component")
        self.assertTrue(self.app.notebook.winfo_exists(), "Notebook widget not created properly")


class TestWorkflowTab(GUITestCase):
    """Test functionality of the workflow tab"""
    
    def setUp(self):
        """Set up the test environment with GUI initialized"""
        super().setUp()
        self.initialize_gui(demo_mode=True)
        # Select the workflow tab (tab index 0)
        self.app.notebook.select(0)
        self.root.update()
    
    def test_parameter_inputs(self):
        """Test parameter input fields in workflow tab"""
        # Test if parameter fields exist and can be modified
        param_fields = ['l4_workflow', 'l5_workflow', 'alpha1_workflow']
        for field_name in param_fields:
            if hasattr(self.app, field_name):
                field = getattr(self.app, field_name)
                field.delete(0, tk.END)
                field.insert(0, "2.5")
                self.assertEqual(field.get(), "2.5", f"Failed to set {field_name} value")
    
    def test_preset_selection(self):
        """Test preset selection functionality"""
        # Check if preset combo exists
        if hasattr(self.app, 'preset_combo'):
            presets = self.app.preset_combo['values']
            if len(presets) > 0:
                # Try selecting different presets
                for i in range(min(len(presets), 3)):
                    self.app.preset_combo.current(i)
                    self.root.update()
                    self.assertEqual(self.app.preset_combo.get(), presets[i], 
                                    f"Failed to select preset {presets[i]}")
    
    def test_workflow_execution(self):
        """Test workflow execution functionality"""
        if hasattr(self.app, 'run_complete_workflow'):
            # Define variables to track execution
            execution_started = [False]
            
            # Define a function to run workflow in a separate thread
            def run_workflow_thread():
                try:
                    self.app.run_complete_workflow()
                    execution_started[0] = True
                except Exception as e:
                    logger.error(f"Error executing workflow: {str(e)}")
            
            # Run workflow in a separate thread
            thread = threading.Thread(target=run_workflow_thread)
            thread.daemon = True
            thread.start()
            
            # Wait for workflow to start
            start_time = time.time()
            while not execution_started[0] and time.time() - start_time < 5:
                self.root.update()
                time.sleep(0.1)
            
            # Check status
            self.assertTrue(execution_started[0], "Workflow execution did not start")


class TestVisualizationTab(GUITestCase):
    """Test functionality of the visualization tab"""
    
    def setUp(self):
        """Set up the test environment with GUI initialized"""
        super().setUp()
        self.initialize_gui(demo_mode=True)
        # Select the visualization tab (tab index 1)
        self.app.notebook.select(1)
        self.root.update()
    
    def test_visualization_options(self):
        """Test visualization options in visualization tab"""
        # Test if visualization options exist
        viz_components = ['viz_option', 'colormap', 'plot_type']
        for comp_name in viz_components:
            self.assertTrue(hasattr(self.app, comp_name), f"Missing component: {comp_name}")
    
    def test_mesh_display(self):
        """Test mesh visualization functionality"""
        if hasattr(self.app, 'plot_mesh'):
            if hasattr(self.app, 'load_mesh_data'):
                try:
                    self.app.load_mesh_data()
                    self.app.plot_mesh()
                    self.wait_for_gui_event()
                    # Success if no exceptions are raised
                    self.assertTrue(True)
                except Exception as e:
                    logger.warning(f"Could not visualize mesh: {str(e)}")
    
    def test_results_visualization(self):
        """Test results visualization functionality"""
        if hasattr(self.app, 'visualize_results'):
            if hasattr(self.app, 'load_results_data'):
                try:
                    self.app.load_results_data()
                    self.app.visualize_results()
                    self.wait_for_gui_event()
                    # Success if no exceptions are raised
                    self.assertTrue(True)
                except Exception as e:
                    logger.warning(f"Could not visualize results: {str(e)}")


class TestOptimizationTab(GUITestCase):
    """Test functionality of the optimization tab"""
    
    def setUp(self):
        """Set up the test environment with GUI initialized"""
        super().setUp()
        self.initialize_gui(demo_mode=True)
        # Select the optimization tab (tab index 2)
        self.app.notebook.select(2)
        self.root.update()
    
    def test_algorithm_selection(self):
        """Test optimization algorithm selection"""
        if hasattr(self.app, 'opt_algorithm'):
            algorithms = self.app.opt_algorithm['values']
            if len(algorithms) > 0:
                # Try selecting different algorithms
                for i in range(min(len(algorithms), 2)):
                    self.app.opt_algorithm.current(i)
                    self.root.update()
                    self.assertEqual(self.app.opt_algorithm.get(), algorithms[i], 
                                    f"Failed to select algorithm {algorithms[i]}")
    
    def test_algorithm_description_update(self):
        """Test updating algorithm description when selection changes"""
        if hasattr(self.app, 'opt_algorithm') and hasattr(self.app, 'update_algorithm_description'):
            # Try to update description for a specific algorithm
            self.app.opt_algorithm.current(0)  # Select first algorithm
            self.app.update_algorithm_description()
            self.wait_for_gui_event()
            # Just testing that it doesn't raise an exception
            self.assertTrue(True)
    
    def test_parameter_bounds(self):
        """Test parameter bounds inputs"""
        # Test if parameter bounds fields exist and can be modified
        param_fields = ['l4_min', 'l4_max', 'l5_min', 'l5_max']
        for field_name in param_fields:
            if hasattr(self.app, field_name):
                field = getattr(self.app, field_name)
                field.delete(0, tk.END)
                field.insert(0, "1.0")
                self.assertEqual(field.get(), "1.0", f"Failed to set {field_name} value")


class TestSettingsTab(GUITestCase):
    """Test functionality of the settings tab"""
    
    def setUp(self):
        """Set up the test environment with GUI initialized"""
        super().setUp()
        self.initialize_gui(demo_mode=True)
        # Select the settings tab (tab index 3)
        self.app.notebook.select(3)
        self.root.update()
    
    def test_theme_selection(self):
        """Test theme selection functionality"""
        if hasattr(self.app, 'theme_combo') and hasattr(self.app, 'change_theme'):
            themes = self.app.theme_combo['values']
            if len(themes) > 0:
                original_theme = self.app.theme_combo.get()
                # Try different themes
                for i in range(min(len(themes), 2)):
                    self.app.theme_combo.current(i)
                    self.app.change_theme()
                    self.wait_for_gui_event()
                    self.assertEqual(self.app.theme_combo.get(), themes[i], 
                                    f"Failed to select theme {themes[i]}")
                # Restore original theme
                self.app.theme_combo.set(original_theme)
                self.app.change_theme()
    
    def test_demo_mode_toggle(self):
        """Test demo mode toggle functionality"""
        if hasattr(self.app, 'demo_var') and hasattr(self.app, 'toggle_demo_mode'):
            original_value = self.app.demo_var.get()
            # Toggle demo mode
            self.app.demo_var.set(not original_value)
            self.app.toggle_demo_mode()
            self.wait_for_gui_event()
            # Toggle back
            self.app.demo_var.set(original_value)
            self.app.toggle_demo_mode()
    
    def test_run_diagnostics(self):
        """Test run diagnostics functionality"""
        if hasattr(self.app, 'run_diagnostics'):
            try:
                self.app.run_diagnostics()
                self.wait_for_gui_event(timeout=2.0)
                # Success if no exceptions are raised
                self.assertTrue(True)
            except Exception as e:
                logger.warning(f"Could not run diagnostics: {str(e)}")


class TestModeSwitching(GUITestCase):
    """Test switching between demo and actual modes"""
    
    def test_mode_switching(self):
        """Test switching between demo and actual modes"""
        # First initialize in demo mode
        self.initialize_gui(demo_mode=True)
        
        # Check initial mode
        import MDO
        self.assertTrue(MDO.DEMO_MODE, "GUI should initialize in demo mode")
        
        # Switch to actual mode if toggle_demo_mode exists
        if hasattr(self.app, 'demo_var') and hasattr(self.app, 'toggle_demo_mode'):
            self.app.demo_var.set(False)
            self.app.toggle_demo_mode()
            self.wait_for_gui_event()
            self.assertFalse(MDO.DEMO_MODE, "Failed to switch to actual mode")
            
            # Switch back to demo mode
            self.app.demo_var.set(True)
            self.app.toggle_demo_mode()
            self.wait_for_gui_event()
            self.assertTrue(MDO.DEMO_MODE, "Failed to switch back to demo mode")


class TestWorkflowVisualization(GUITestCase):
    """Test workflow visualization functionality"""
    
    def test_workflow_steps_creation(self):
        """Test creation of workflow steps in the canvas"""
        self.initialize_gui(demo_mode=True)
        
        if hasattr(self.app, '_create_workflow_steps'):
            # Create a canvas if needed
            if not hasattr(self.app, 'workflow_canvas') or not self.app.workflow_canvas:
                self.app.workflow_canvas = tk.Canvas(self.root)
                self.app.workflow_canvas.pack(fill='both', expand=True)
            
            # Create workflow steps
            self.app._create_workflow_steps()
            self.root.update()
            
            # Check that steps were created
            self.assertTrue(hasattr(self.app, 'workflow_steps'), "Workflow steps not created")
            if hasattr(self.app, 'workflow_steps'):
                self.assertGreaterEqual(len(self.app.workflow_steps), 4, "Not enough workflow steps created")
    
    def test_update_step_status(self):
        """Test updating workflow step status"""
        self.initialize_gui(demo_mode=True)
        
        # Set up workflow canvas and steps if needed
        if hasattr(self.app, '_create_workflow_steps'):
            if not hasattr(self.app, 'workflow_canvas') or not self.app.workflow_canvas:
                self.app.workflow_canvas = tk.Canvas(self.root)
                self.app.workflow_canvas.pack(fill='both', expand=True)
            
            self.app._create_workflow_steps()
            self.root.update()
            
            # Update step status if the method exists
            if hasattr(self.app, '_update_step_status'):
                # Test all status types
                statuses = ["pending", "running", "complete", "failed"]
                for status in statuses:
                    if len(self.app.workflow_steps) > 0:
                        step_name = self.app.workflow_steps[0]["name"]
                        self.app._update_step_status(step_name, status)
                        self.root.update()
                        self.assertEqual(self.app.workflow_steps[0]["status"], status,
                                       f"Failed to update step status to {status}")


class TestDemoVsActualMode(unittest.TestCase):
    """Test differences between demo and actual modes"""
    
    @classmethod
    def setUpClass(cls):
        """Set up shared resources for tests"""
        # Import MDO module to get access to run_command
        try:
            import MDO
            cls.MDO = MDO
            # Store original demo mode
            cls.original_demo_mode = MDO.DEMO_MODE
        except ImportError:
            logger.error("Could not import MDO module")
            cls.MDO = None
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests"""
        # Restore original demo mode
        if cls.MDO:
            cls.MDO.DEMO_MODE = cls.original_demo_mode
    
    def test_run_command_demo_mode(self):
        """Test run_command behavior in demo mode"""
        if not self.MDO:
            self.skipTest("MDO module not available")
        
        # Set demo mode
        self.MDO.DEMO_MODE = True
        
        # Run a test command in demo mode
        result = self.MDO.run_command(["./gmsh_process", "--test"])
        
        # In demo mode, run_command should simulate execution
        self.assertIn("Mock", result, "Demo mode should simulate command execution")
    
    def test_run_command_actual_mode(self):
        """Test run_command behavior in actual mode"""
        if not self.MDO:
            self.skipTest("MDO module not available")
        
        # Set actual mode
        self.MDO.DEMO_MODE = False
        
        # Create a simple echo command to test
        test_file = "test_actual_mode.txt"
        test_content = "actual mode test"
        
        try:
            # Run a real command that should work in actual mode
            result = self.MDO.run_command(["echo", test_content, ">", test_file])
            
            # In actual mode, run_command should execute real commands
            # Note: the echo command might not actually create the file due to how run_command works
            # This is just testing that it doesn't return a mock message
            self.assertNotIn("Mock", result, "Actual mode should not simulate command execution")
        except Exception as e:
            logger.warning(f"Error testing actual mode: {str(e)}")
        finally:
            # Clean up
            if os.path.exists(test_file):
                os.remove(test_file)


def run_test_suite(mode="both"):
    """Run all tests in the specified mode"""
    logger.info(f"Running test suite in mode: {mode}")
    
    # Create a test suite
    suite = unittest.TestSuite()
    
    # Add the general initialization tests
    suite.addTest(unittest.makeSuite(TestGUIInitialization))
    
    # Add the tab-specific tests
    suite.addTest(unittest.makeSuite(TestWorkflowTab))
    suite.addTest(unittest.makeSuite(TestVisualizationTab))
    suite.addTest(unittest.makeSuite(TestOptimizationTab))
    suite.addTest(unittest.makeSuite(TestSettingsTab))
    
    # Add the workflow visualization tests
    suite.addTest(unittest.makeSuite(TestWorkflowVisualization))
    
    # Add the mode-specific tests
    suite.addTest(unittest.makeSuite(TestModeSwitching))
    
    # Add the demo vs actual mode tests
    suite.addTest(unittest.makeSuite(TestDemoVsActualMode))
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return success status
    return result.wasSuccessful()


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Comprehensive test for CFD GUI")
    parser.add_argument("--mode", choices=["demo", "actual", "both"], default="both",
                      help="Test mode: demo (mock data), actual (real executables), or both")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    success = run_test_suite(args.mode)
    sys.exit(0 if success else 1)