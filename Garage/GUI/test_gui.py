import NXOpen
import NXOpen.UI

def show_simple_dialog():
    try:
        # Create a simple dialog
        dialog = NXOpen.UI.NXDialog()
        dialog.SetTitle("Test Dialog")
        
        # Add a label
        dialog.AddLabel(10, 10, "If you can see this dialog, GUI functionality is working!")
        
        # Add a button
        closeButton = dialog.AddButton(10, 50, "Close")
        
        # Add handler for the button
        def close_callback():
            dialog.Dispose()
        
        closeButton.AddHandler(close_callback)
        
        # Show the dialog
        dialog.Show()
        
        return True
    except Exception as ex:
        error_msg = str(ex)
        print(f"Error in test GUI: {error_msg}")
        
        # Try to show the error in an NX message box
        try:
            NXOpen.UI.GetUI().NXMessageBox.Show(
                "Error", 
                NXOpen.UI.MessageBoxType.Error, 
                f"Error in test GUI: {error_msg}")
        except:
            pass
        
        return False

# Run the test when this script is executed
if __name__ == "__main__":
    success = show_simple_dialog()
    if success:
        print("Test GUI displayed successfully")
    else:
        print("Failed to display test GUI")
#!/usr/bin/env python3
# test_gui.py - Unit tests for the GUI functionality of the Intake CFD Optimization Suite

import unittest
import tkinter as tk
from unittest.mock import patch, MagicMock
import sys
import os
import numpy as np
from tkinter import ttk
import threading
import tempfile
import json
import shutil

# Add the current directory to the Python path to import MDO modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the module to test
import MDO
from workflow_utils import DarkTheme, patch_workflow_gui

# Create a mock for the WorkflowGUI class
class MockWorkflowGUI:
    def __init__(self, root=None):
        self.root = root or tk.Tk()
        self.theme = MDO.ModernTheme()
        self.status_var = tk.StringVar(value="Ready")
        self.demo_var = tk.BooleanVar(value=True)
        self.theme_combo = tk.StringVar(value="Default (Blue)")
        self.workflow_tab = tk.Frame()
        self.visualization_tab = tk.Frame()
        self.optimization_tab = tk.Frame()
        self.settings_tab = tk.Frame()
        self.best_results = tk.ttk.Treeview(self.root)
        self.opt_algorithm = tk.StringVar()
        self.algo_description = tk.Label(self.root)
        
    def toggle_demo_mode(self):
        MDO.DEMO_MODE = self.demo_var.get()
        if MDO.DEMO_MODE:
            MDO.create_mock_executables()
    
    def change_theme(self):
        theme = self.theme_combo.get()
        if theme == "Dark":
            self.theme.bg_color = "#2C3E50"
            self.theme.text_color = "#ECF0F1"
        elif theme == "Light":
            self.theme.bg_color = "#F5F7FA"
            self.theme.text_color = "#2C3E50"
    
    def update_algorithm_description(self):
        algorithm = self.opt_algorithm.get()
        descriptions = {
            "SLSQP": "Sequential Least Squares Programming - Gradient-based optimizer",
            "COBYLA": "Constrained Optimization BY Linear Approximation - Non-gradient based",
            "NSGA2": "Non-dominated Sorting Genetic Algorithm - Multi-objective optimization",
            "GA": "Genetic Algorithm - Population-based evolutionary optimizer"
        }
        
        if algorithm in descriptions:
            self.algo_description.config(text=descriptions[algorithm])
    
    def run_diagnostics(self):
        pass
    
    def _show_diagnostics_result(self, results):
        pass
    
    def save_settings(self):
        pass
    
    def browse_file(self, entry):
        entry.delete(0, tk.END)
        entry.insert(0, "/mnt/c/path/to/test/file.txt")
    
    def browse_directory(self, entry):
        entry.delete(0, tk.END)
        entry.insert(0, "/mnt/c/path/to/test/directory")


class TestIntakeCFDSuiteFunctions(unittest.TestCase):
    """Test suite for the Intake CFD Optimization Suite functions"""
    
    def setUp(self):
        """Set up test environment before each test"""
        # Ensure we're in DEMO_MODE for testing
        MDO.DEMO_MODE = True
    
    def tearDown(self):
        """Clean up after each test"""
        pass
    
    def test_is_wsl(self):
        """Test the WSL detection function"""
        # We can't easily test the actual implementation, but we can verify it returns a boolean
        result = MDO.is_wsl()
        self.assertIsInstance(result, bool)
    
    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data="Windows")
    @patch('os.path.exists')
    def test_is_wsl_detection(self, mock_exists, mock_open):
        """Test different WSL detection scenarios"""
        # Test detection via /proc/version
        mock_exists.return_value = False
        MDO.platform.system = MagicMock(return_value="Linux")
        MDO.platform.release = MagicMock(return_value="normal_release")
        mock_exists.return_value = True
        self.assertTrue(MDO.is_wsl())
        
        # Test detection via /proc/version when 'microsoft' is in the release
        MDO.platform.release = MagicMock(return_value="microsoft_WSL2")
        self.assertTrue(MDO.is_wsl())
    
    @patch('MDO.run_command')
    def test_run_nx_workflow_demo(self, mock_run_command):
        """Test NX workflow in demo mode"""
        MDO.DEMO_MODE = True
        result = MDO.run_nx_workflow()
        self.assertEqual(result, "INTAKE3D.step")
        # Verify run_command wasn't called since we're in demo mode
        mock_run_command.assert_not_called()
    
    @patch('MDO.run_command')
    def test_process_mesh_demo(self, mock_run_command):
        """Test mesh processing in demo mode"""
        MDO.DEMO_MODE = True
        step_file = "test.step"
        mesh_file = "test.msh"
        
        # Create a temporary file to capture writes
        with unittest.mock.patch('builtins.open', unittest.mock.mock_open()) as mock_file:
            MDO.process_mesh(step_file, mesh_file)
            mock_file.assert_called_once_with(mesh_file, 'w')
            # Verify run_command wasn't called since we're in demo mode
            mock_run_command.assert_not_called()
    
    @patch('MDO.os.makedirs')
    def test_run_cfd_demo(self, mock_makedirs):
        """Test CFD simulation in demo mode"""
        MDO.DEMO_MODE = True
        mesh_file = "test.msh"
        
        # Create a temporary file to capture writes
        with unittest.mock.patch('builtins.open', unittest.mock.mock_open()) as mock_file:
            MDO.run_cfd(mesh_file)
            mock_makedirs.assert_called_once_with("cfd_results", exist_ok=True)
            # Verify file writes occurred
            calls = mock_file.call_args_list
            self.assertEqual(len(calls), 2)  # Two files should be written
    
    def test_exp_function(self):
        """Test the expression generation function"""
        with patch('MDO.write_exp_file') as mock_write:
            MDO.exp(1.0, 2.0, 30.0, 45.0, 60.0)
            # Verify write_exp_file was called with 5 expressions
            args = mock_write.call_args[0]
            self.assertEqual(len(args[0]), 5)


class TestModernTheme(unittest.TestCase):
    """Test the ModernTheme class"""
    
    def setUp(self):
        """Set up test environment"""
        self.theme = MDO.ModernTheme()
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the window
    
    def tearDown(self):
        """Clean up after each test"""
        self.root.destroy()
    
    def test_theme_initialization(self):
        """Test that theme initializes with correct default values"""
        self.assertEqual(self.theme.bg_color, "#F5F7FA")  # Light background
        self.assertEqual(self.theme.primary_color, "#2C3E50")  # Dark blue header
        self.assertEqual(self.theme.accent_color, "#3498DB")  # Blue for buttons
        self.assertEqual(self.theme.accent_hover, "#2980B9")  # Darker blue for hover
    
    def test_theme_apply(self):
        """Test that the theme applies to widgets"""
        # This test requires mocking ttk.Style, which is complex
        # Instead, we'll just verify the method exists and doesn't crash
        try:
            self.theme.apply_theme(self.root)
        except Exception as e:
            self.fail(f"apply_theme raised {type(e).__name__} unexpectedly: {e}")


class TestGUIMethods(unittest.TestCase):
    """Test the GUI methods using our mock class"""
    
    def setUp(self):
        """Set up test environment"""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the window
        self.gui = MockWorkflowGUI(self.root)
        
        # Mock messagebox for tests
        self.patcher_messagebox = patch('tkinter.messagebox')
        self.mock_messagebox = self.patcher_messagebox.start()
        
        # Clear any test files if they exist
        if os.path.exists("settings.json"):
            try:
                os.remove("settings.json")
            except:
                pass
    
    def tearDown(self):
        """Clean up after each test"""
        self.patcher_messagebox.stop()
        self.root.destroy()
    
    @patch('MDO.create_mock_executables')
    def test_toggle_demo_mode(self, mock_create_mock_executables):
        """Test toggling the demo mode"""
        # Start in demo mode
        MDO.DEMO_MODE = True
        self.gui.demo_var.set(True)
        
        # Toggle off
        self.gui.demo_var.set(False)
        self.gui.toggle_demo_mode()
        self.assertFalse(MDO.DEMO_MODE)
        
        # Toggle back on
        self.gui.demo_var.set(True)
        self.gui.toggle_demo_mode()
        self.assertTrue(MDO.DEMO_MODE)
        mock_create_mock_executables.assert_called_once()
    
    def test_change_theme(self):
        """Test changing the theme"""
        # Check initial theme
        self.assertEqual(self.gui.theme.bg_color, "#F5F7FA")  # Light background
        
        # Change to dark theme
        self.gui.theme_combo.set("Dark")
        self.gui.change_theme()
        self.assertEqual(self.gui.theme.bg_color, "#2C3E50")  # Dark background
        self.assertEqual(self.gui.theme.text_color, "#ECF0F1")  # Light text
        
        # Change to light theme
        self.gui.theme_combo.set("Light")
        self.gui.change_theme()
        self.assertEqual(self.gui.theme.bg_color, "#F5F7FA")  # Light background
        self.assertEqual(self.gui.theme.text_color, "#2C3E50")  # Dark text
    
    def test_update_algorithm_description(self):
        """Test updating the algorithm description"""
        # Set up mock description label
        self.gui.algo_description = MagicMock()
        
        # Test SLSQP
        self.gui.opt_algorithm.set("SLSQP")
        self.gui.update_algorithm_description()
        self.gui.algo_description.config.assert_called_once()
        args = self.gui.algo_description.config.call_args[1]
        self.assertIn("Gradient-based optimizer", args["text"])
        
        # Reset mock and test COBYLA
        self.gui.algo_description.reset_mock()
        self.gui.opt_algorithm.set("COBYLA")
        self.gui.update_algorithm_description()
        self.gui.algo_description.config.assert_called_once()
        args = self.gui.algo_description.config.call_args[1]
        self.assertIn("Non-gradient based", args["text"])
    
    def test_browse_file(self):
        """Test browsing for a file"""
        # Create a test entry
        entry = tk.Entry(self.root)
        entry.insert(0, "original value")
        
        # Test the browse function
        self.gui.browse_file(entry)
        self.assertEqual(entry.get(), "/mnt/c/path/to/test/file.txt")
    
    def test_browse_directory(self):
        """Test browsing for a directory"""
        # Create a test entry
        entry = tk.Entry(self.root)
        entry.insert(0, "original directory")
        
        # Test the browse function
        self.gui.browse_directory(entry)
        self.assertEqual(entry.get(), "/mnt/c/path/to/test/directory")


class TestRunWithBypass(unittest.TestCase):
    """Test the run_with_bypass.bat script functionality"""
    
    def test_script_sets_demo_mode(self):
        """Test that the script sets DEMO_MODE environment variable"""
        # Read the batch file
        with open("/mnt/c/Users/Mohammed/Desktop/Intake-CFD-Project/nx/run_with_bypass.bat", "r") as f:
            batch_content = f.read()
        
        # Check that it sets DEMO_MODE
        self.assertIn("DEMO_MODE=1", batch_content)
        
        # Check that it runs MDO.py
        self.assertIn("python", batch_content)
        self.assertIn("MDO.py", batch_content)
    
    def test_script_handles_errors(self):
        """Test that the script has error handling"""
        # Read the batch file
        with open("/mnt/c/Users/Mohammed/Desktop/Intake-CFD-Project/nx/run_with_bypass.bat", "r") as f:
            batch_content = f.read()
        
        # Check for error handling
        self.assertIn("ERRORLEVEL", batch_content)
        self.assertIn("Application failed with error code", batch_content)


class TestThemeSettings(unittest.TestCase):
    """Test the theme settings functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the window during tests
        # Create a patched WorkflowGUI instance
        self.original_class = MDO.WorkflowGUI
        MDO.WorkflowGUI = patch_workflow_gui(MDO.WorkflowGUI)
        self.app = MDO.WorkflowGUI(self.root)
        
    def tearDown(self):
        """Clean up after each test"""
        # Restore the original class
        MDO.WorkflowGUI = self.original_class
        self.root.destroy()
        
    def test_dark_theme_initialization(self):
        """Test that dark theme initializes with correct values"""
        dark_theme = DarkTheme()
        self.assertEqual(dark_theme.bg_color, "#1E1E1E")
        self.assertEqual(dark_theme.primary_color, "#252526")
        self.assertEqual(dark_theme.accent_color, "#0078D7")
        self.assertEqual(dark_theme.text_color, "#CCCCCC")
        
    def test_theme_switching(self):
        """Test that theme switching works correctly"""
        # Set up theme combo
        self.app.theme_combo = ttk.Combobox(self.root, values=["Light", "Dark", "System"])
        self.app.theme_combo.current(0)
        
        # Create a test variable to track theme changes
        self.app.theme_changed = False
        original_apply_dark_theme = self.app.apply_dark_theme
        
        def mock_apply_dark_theme():
            self.app.theme_changed = True
            # Don't actually apply the theme to avoid UI updates in test
        
        self.app.apply_dark_theme = mock_apply_dark_theme
        
        # Test switching to dark theme
        self.app.theme_combo.set("Dark")
        self.app._apply_theme_internal("Dark")
        self.assertTrue(self.app.theme_changed)
        self.assertIsInstance(self.app.theme, DarkTheme)
        
        # Restore original method
        self.app.apply_dark_theme = original_apply_dark_theme
        
    def test_refresh_light_theme(self):
        """Test that refresh_light_theme method exists and doesn't crash"""
        try:
            self.app.refresh_light_theme()
        except Exception as e:
            self.fail(f"refresh_light_theme raised {type(e).__name__} unexpectedly: {e}")


class TestDisplaySettings(unittest.TestCase):
    """Test the display settings functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the window during tests
        # Create a patched WorkflowGUI instance
        self.original_class = MDO.WorkflowGUI
        MDO.WorkflowGUI = patch_workflow_gui(MDO.WorkflowGUI)
        self.app = MDO.WorkflowGUI(self.root)
        
    def tearDown(self):
        """Clean up after each test"""
        # Restore the original class
        MDO.WorkflowGUI = self.original_class
        self.root.destroy()
    
    def test_font_size_changes(self):
        """Test that font size changes are applied correctly"""
        # Set up font size entry
        self.app.font_size = ttk.Entry(self.root)
        self.app.font_size.insert(0, "12")
        
        # Apply the font size
        self.app.apply_font_size()
        
        # Check that the font sizes were updated
        self.assertEqual(self.app.theme.normal_font[1], 12)
        self.assertEqual(self.app.theme.header_font[1], 14)  # header is +2
        self.assertEqual(self.app.theme.small_font[1], 11)   # small is -1
        
    def test_font_size_validation(self):
        """Test that font size validation works correctly"""
        # Set up font size entry
        self.app.font_size = ttk.Entry(self.root)
        
        # Test too small font size
        self.app.font_size.delete(0, tk.END)
        self.app.font_size.insert(0, "5")  # Too small
        self.app.apply_font_size()
        self.assertEqual(self.app.font_size.get(), "8")  # Should be adjusted to minimum
        
        # Test too large font size
        self.app.font_size.delete(0, tk.END)
        self.app.font_size.insert(0, "25")  # Too large
        self.app.apply_font_size()
        self.assertEqual(self.app.font_size.get(), "18")  # Should be adjusted to maximum
        
        # Test invalid input
        self.app.font_size.delete(0, tk.END)
        self.app.font_size.insert(0, "abc")  # Invalid
        self.app.apply_font_size()
        self.assertEqual(self.app.font_size.get(), "10")  # Should reset to default
    
    def test_integer_validation(self):
        """Test that integer validation works correctly"""
        # Test various inputs
        self.assertTrue(self.app._validate_integer("123"))   # Valid
        self.assertTrue(self.app._validate_integer("0"))     # Valid
        self.assertTrue(self.app._validate_integer(""))      # Empty is valid
        self.assertFalse(self.app._validate_integer("12.3")) # Invalid
        self.assertFalse(self.app._validate_integer("abc"))  # Invalid
        self.assertFalse(self.app._validate_integer("12a"))  # Invalid


class TestParallelizationSettings(unittest.TestCase):
    """Test the parallelization settings functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the window during tests
        # Create a patched WorkflowGUI instance
        self.original_class = MDO.WorkflowGUI
        MDO.WorkflowGUI = patch_workflow_gui(MDO.WorkflowGUI)
        self.app = MDO.WorkflowGUI(self.root)
        
        # Create temp directory for test settings
        self.test_dir = tempfile.mkdtemp()
        self.settings_file = os.path.join(self.test_dir, "settings.json")
        
    def tearDown(self):
        """Clean up after each test"""
        # Restore the original class
        MDO.WorkflowGUI = self.original_class
        self.root.destroy()
        
        # Clean up temp directory
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_parallel_processes_setting(self):
        """Test that parallel processes setting is saved and loaded correctly"""
        # Set up parallel processes spinbox
        self.app.parallel_processes = ttk.Spinbox(self.root, from_=1, to=64)
        self.app.parallel_processes.set(8)  # Set to 8 cores
        
        # Save settings
        settings = {
            "parallel_processes": "8",
            "memory_limit": 4.0,
            "theme": "Light"
        }
        
        with open(self.settings_file, "w") as f:
            json.dump(settings, f)
        
        # Load settings
        # Mock the path to our test file
        original_path_join = os.path.join
        def mock_path_join(*args):
            if args[-1] == "settings.json":
                return self.settings_file
            return original_path_join(*args)
        
        os.path.join = mock_path_join
        
        # Reset parallel processes to something else first
        self.app.parallel_processes.delete(0, tk.END)
        self.app.parallel_processes.insert(0, "4")
        
        # Test loading
        self.app.load_settings()
        
        # Verify the setting was loaded
        self.assertEqual(self.app.parallel_processes.get(), "8")
        
        # Restore original function
        os.path.join = original_path_join
    
    def test_memory_limit_setting(self):
        """Test that memory limit setting is saved and loaded correctly"""
        # Set up memory scale
        self.app.memory_scale = ttk.Scale(self.root, from_=1, to=64)
        self.app.memory_scale.set(4.0)  # Set to 4GB
        self.app.memory_label = ttk.Label(self.root)
        
        # Test memory display update
        self.app.update_memory_display()
        self.assertEqual(self.app.memory_label.cget("text"), "4.0 GB")
        
        # Change memory limit
        self.app.memory_scale.set(8.0)
        self.app.update_memory_display()
        self.assertEqual(self.app.memory_label.cget("text"), "8.0 GB")
    
    def test_run_diagnostics(self):
        """Test that run_diagnostics method exists and doesn't crash"""
        # Mock diagnostics result to avoid actual system checks
        def mock_diagnostics_thread():
            self.app._show_diagnostics_result({
                "NX": True,
                "GMSH": True,
                "CFD": True,
                "Memory": True,
                "Disk Space": True
            }, "8.0 GB available, 4.0 GB requested", "50 GB free")
        
        # Replace the diagnostics thread with our mock
        original_thread = self.app._run_diagnostics_thread
        self.app._run_diagnostics_thread = mock_diagnostics_thread
        
        try:
            self.app.run_diagnostics()
            # If we got here without exception, the test passed
        except Exception as e:
            self.fail(f"run_diagnostics raised {type(e).__name__} unexpectedly: {e}")
        finally:
            # Restore original method
            self.app._run_diagnostics_thread = original_thread


class TestWorkflowVisualization(unittest.TestCase):
    """Test the workflow visualization functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the window during tests
        # Create a patched WorkflowGUI instance
        self.original_class = MDO.WorkflowGUI
        MDO.WorkflowGUI = patch_workflow_gui(MDO.WorkflowGUI)
        self.app = MDO.WorkflowGUI(self.root)
        
    def tearDown(self):
        """Clean up after each test"""
        # Restore the original class
        MDO.WorkflowGUI = self.original_class
        self.root.destroy()
    
    def test_workflow_steps_creation(self):
        """Test that workflow steps are created correctly"""
        # Set up workflow canvas
        self.app.workflow_canvas = tk.Canvas(self.root)
        
        # Create workflow steps
        self.app._create_workflow_steps()
        
        # Verify steps were created
        self.assertEqual(len(self.app.workflow_steps), 4)
        self.assertEqual(self.app.workflow_steps[0]["name"], "NX Model")
        self.assertEqual(self.app.workflow_steps[1]["name"], "Mesh")
        self.assertEqual(self.app.workflow_steps[2]["name"], "CFD")
        self.assertEqual(self.app.workflow_steps[3]["name"], "Results")
        
        # Verify status
        for step in self.app.workflow_steps:
            self.assertEqual(step["status"], "pending")
    
    def test_update_step_status(self):
        """Test updating step status"""
        # Set up workflow canvas and steps
        self.app.workflow_canvas = tk.Canvas(self.root)
        self.app._create_workflow_steps()
        
        # Update status of a step
        self.app._update_step_status("Mesh", "running")
        
        # Verify status was updated
        self.assertEqual(self.app.workflow_steps[0]["status"], "pending")
        self.assertEqual(self.app.workflow_steps[1]["status"], "running")
        self.assertEqual(self.app.workflow_steps[2]["status"], "pending")
        
        # Update another step
        self.app._update_step_status("CFD", "complete")
        self.assertEqual(self.app.workflow_steps[2]["status"], "complete")
        
        # Update to failed
        self.app._update_step_status("Results", "failed")
        self.assertEqual(self.app.workflow_steps[3]["status"], "failed")


if __name__ == "__main__":
    unittest.main()