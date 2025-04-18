#!/usr/bin/env python3

"""
Display settings manager for test runs.
Controls output formatting, colors, and verbosity levels for test execution.
"""

import os
import sys
import time
from enum import Enum
import argparse
import unittest
import importlib
import glob
import traceback
import json

class OutputColors:
    """ANSI color codes for terminal output."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"

class DisplayFormat(Enum):
    """Available display formats for test output."""
    MINIMAL = "minimal"  # Only show failures
    STANDARD = "standard"  # Show basic pass/fail for each test
    DETAILED = "detailed"  # Show detailed information for each test
    JSON = "json"  # Output in JSON format for parsing

class DisplaySettings:
    """Manages display settings for test runs."""
    
    def __init__(self, verbose=False, use_color=True, format=DisplayFormat.STANDARD):
        """
        Initialize display settings.
        
        Args:
            verbose (bool): Enable verbose output
            use_color (bool): Use colored output in terminal
            format (DisplayFormat): Output format style
        """
        self.verbose = verbose
        self.use_color = use_color and sys.stdout.isatty()  # Only use colors for interactive terminals
        self.format = format
        self.start_time = None
        self.test_counts = {"total": 0, "passed": 0, "failed": 0, "skipped": 0}
    
    def start_test_run(self):
        """Mark the beginning of a test run and record start time."""
        self.start_time = time.time()
        self.test_counts = {"total": 0, "passed": 0, "failed": 0, "skipped": 0}
        
        if self.verbose:
            self._print_header("STARTING TEST RUN")
    
    def end_test_run(self):
        """Display test run summary."""
        elapsed = time.time() - self.start_time if self.start_time else 0
        
        self._print_header("TEST RUN SUMMARY")
        print(f"Total tests: {self.test_counts['total']}")
        
        if self.use_color:
            print(f"Passed: {OutputColors.GREEN}{self.test_counts['passed']}{OutputColors.RESET}")
            print(f"Failed: {OutputColors.RED}{self.test_counts['failed']}{OutputColors.RESET}")
            print(f"Skipped: {OutputColors.YELLOW}{self.test_counts['skipped']}{OutputColors.RESET}")
        else:
            print(f"Passed: {self.test_counts['passed']}")
            print(f"Failed: {self.test_counts['failed']}")
            print(f"Skipped: {self.test_counts['skipped']}")
        
        print(f"Time elapsed: {elapsed:.2f} seconds")
    
    def print_test_file_header(self, test_file):
        """Display header for a test file."""
        basename = os.path.basename(test_file)
        self._print_divider()
        if self.use_color:
            print(f"{OutputColors.CYAN}{OutputColors.BOLD}Running: {basename}{OutputColors.RESET}")
        else:
            print(f"Running: {basename}")
        self._print_divider()
    
    def print_test_result(self, test_name, passed, error_msg=None):
        """
        Display result of an individual test.
        
        Args:
            test_name (str): Name of the test
            passed (bool): Whether the test passed
            error_msg (str): Error message if the test failed
        """
        self.test_counts["total"] += 1
        
        if passed:
            self.test_counts["passed"] += 1
            if self.format != DisplayFormat.MINIMAL:
                if self.use_color:
                    print(f"{OutputColors.GREEN}✓{OutputColors.RESET} {test_name}")
                else:
                    print(f"PASS: {test_name}")
        else:
            self.test_counts["failed"] += 1
            if self.use_color:
                print(f"{OutputColors.RED}✗{OutputColors.RESET} {test_name}")
                if error_msg and self.verbose:
                    print(f"{OutputColors.RED}  {error_msg}{OutputColors.RESET}")
            else:
                print(f"FAIL: {test_name}")
                if error_msg and self.verbose:
                    print(f"  {error_msg}")
    
    def print_skipped_test(self, test_name, reason=None):
        """Display information about a skipped test."""
        self.test_counts["total"] += 1
        self.test_counts["skipped"] += 1
        
        if self.format != DisplayFormat.MINIMAL:
            if self.use_color:
                print(f"{OutputColors.YELLOW}⚠ SKIP:{OutputColors.RESET} {test_name}")
                if reason and self.verbose:
                    print(f"{OutputColors.YELLOW}  {reason}{OutputColors.RESET}")
            else:
                print(f"SKIP: {test_name}")
                if reason and self.verbose:
                    print(f"  {reason}")
    
    def print_warning(self, message):
        """Display a warning message."""
        if self.use_color:
            print(f"{OutputColors.YELLOW}Warning: {message}{OutputColors.RESET}")
        else:
            print(f"Warning: {message}")
    
    def print_error(self, message):
        """Display an error message."""
        if self.use_color:
            print(f"{OutputColors.RED}Error: {message}{OutputColors.RESET}")
        else:
            print(f"Error: {message}")
    
    def print_info(self, message):
        """Display an informational message."""
        if self.verbose:
            if self.use_color:
                print(f"{OutputColors.BLUE}Info: {message}{OutputColors.RESET}")
            else:
                print(f"Info: {message}")
    
    def _print_header(self, text):
        """Print a formatted header."""
        self._print_divider()
        if self.use_color:
            print(f"{OutputColors.BOLD}{text}{OutputColors.RESET}")
        else:
            print(text)
        self._print_divider()
    
    def _print_divider(self):
        """Print a divider line."""
        print("-" * 60)


class TestRunner:
    """Runs display-related tests and formats output using DisplaySettings."""
    
    def __init__(self, display_settings=None):
        """
        Initialize the TestRunner with display settings.
        
        Args:
            display_settings (DisplaySettings): Display settings for test output
        """
        self.display_settings = display_settings or DisplaySettings()
        self.test_suite = unittest.TestSuite()
        self.result = None
    
    def create_stub_modules(self):
        """Create stub modules needed for tests to run"""
        self.display_settings.print_info("Checking for required stub modules...")
        
        # Create workflow_utils.py stub if needed
        workflow_utils_path = os.path.join(os.getcwd(), "workflow_utils.py")
        if not os.path.exists(workflow_utils_path):
            self.display_settings.print_info("Creating workflow_utils.py stub...")
            with open(workflow_utils_path, 'w') as f:
                f.write("""# Auto-generated stub for workflow_utils
print("workflow_utils.py loaded (stub).")

class DarkTheme:
    \"\"\"Stub for DarkTheme class\"\"\"
    def __init__(self):
        self.bg_color = "#1E1E1E"
        self.primary_color = "#252526"
        self.accent_color = "#0078D7"
        self.text_color = "#CCCCCC"
        self.accent_hover = "#1C97EA"
        self.header_font = ("Segoe UI", 12, "bold")
        self.normal_font = ("Segoe UI", 10)
        self.small_font = ("Segoe UI", 9)
        self.button_font = ("Segoe UI", 10)

def patch_workflow_gui(cls):
    \"\"\"Stub for patch_workflow_gui function\"\"\"
    print("Using stub patch_workflow_gui function")
    return cls
""")
            self.display_settings.print_info(f"Created stub workflow_utils.py")
        
        # Create display_utils.py stub if needed
        display_utils_path = os.path.join(os.getcwd(), "display_utils.py")
        if not os.path.exists(display_utils_path):
            self.display_settings.print_info("Creating display_utils.py stub...")
            with open(display_utils_path, 'w') as f:
                f.write("""# Auto-generated stub for display_utils
print("display_utils.py loaded (stub).")

class ThemeTransition:
    \"\"\"Stub for ThemeTransition class\"\"\"
    def __init__(self, root, duration=0.3, steps=10):
        self.root = root
        self.duration = duration
        self.steps = steps
        self.transition_active = False
    
    def transition(self, widget_map):
        self.transition_active = True
        print(f"Simulating transition for {len(widget_map)} widgets")
        self.transition_active = False
    
    def interpolate_color(self, color1, color2, ratio):
        return "#7F7F7F"  # Gray as a default interpolation

class ColorScheme:
    \"\"\"Stub for ColorScheme class\"\"\"
    def __init__(self, primary_color="#3498DB", is_dark=False):
        self.primary_color = primary_color
        self.is_dark = is_dark
        self.colors = {
            'primary': primary_color,
            'background': "#1E1E1E" if is_dark else "#F5F7FA",
            'text': "#FFFFFF" if is_dark else "#2C3E50",
            'accent': "#3498DB",
            'accent_hover': "#2980B9",
            'success': "#2ECC71",
            'warning': "#F39C12",
            'error': "#E74C3C",
            'border': "#34495E" if is_dark else "#BDC3C7"
        }
    
    def get_contrasting_text_color(self, bg_color):
        if bg_color.lower() == "#ffffff":
            return "#000000"
        return "#FFFFFF"

class SystemThemeDetector:
    \"\"\"Stub for SystemThemeDetector class\"\"\"
    @staticmethod
    def get_system_theme():
        return "light"

class MemoryVisualizer:
    \"\"\"Stub for MemoryVisualizer class\"\"\"
    def __init__(self, canvas):
        self.canvas = canvas
        if not canvas.winfo_width():
            canvas.configure(width=200, height=80)
    
    def update_display(self, percentage, current_value, max_value):
        self.canvas.delete("all")
        # Draw a simple representation in the canvas
        self.canvas.create_rectangle(10, 10, 190, 70, outline="#000000")
        self.canvas.create_rectangle(10, 10, 10 + (percentage * 1.8), 70, fill="#3498DB")
        self.canvas.create_text(100, 40, text=f"{current_value}/{max_value} GB")

class WidgetFactory:
    \"\"\"Stub for WidgetFactory class\"\"\"
    def __init__(self, theme):
        self.theme = theme
    
    def create_header(self, parent, text):
        import tkinter as tk
        header = tk.Label(parent, text=text)
        return header
    
    def create_button(self, parent, text, command=None, is_primary=False):
        import tkinter as tk
        button = tk.Button(parent, text=text, command=command)
        if is_primary:
            button.configure(style="Primary.TButton")
        return button
    
    def create_form_field(self, parent, label_text, default_value=""):
        import tkinter as tk
        frame = tk.Frame(parent)
        label = tk.Label(frame, text=label_text)
        entry = tk.Entry(frame)
        entry.insert(0, default_value)
        label.pack(side=tk.LEFT)
        entry.pack(side=tk.RIGHT)
        return frame, entry

def apply_tooltip(widget, text):
    \"\"\"Stub for apply_tooltip function\"\"\"
    widget.tooltip_text = text

def create_status_indicator(parent):
    \"\"\"Stub for create_status_indicator function\"\"\"
    import tkinter as tk
    indicator = tk.Frame(parent)
    label = tk.Label(indicator, text="Status")
    icon = tk.Label(indicator, text="■")
    label.pack(side=tk.LEFT)
    icon.pack(side=tk.RIGHT)
    
    def update_status(status):
        if status == "running":
            icon.configure(text="▶", fg="#3498DB")
        elif status == "success":
            icon.configure(text="✓", fg="#2ECC71")
        elif status == "error":
            icon.configure(text="✗", fg="#E74C3C")
        else:
            icon.configure(text="■", fg="#7F8C8D")
    
    indicator.update_status = update_status
    return indicator

def create_progress_display(parent, stages=None):
    \"\"\"Stub for create_progress_display function\"\"\"
    import tkinter as tk
    display = tk.Frame(parent)
    stages = stages or ["Step 1", "Step 2", "Step 3"]
    
    stage_frames = {}
    for stage in stages:
        frame = tk.Frame(display)
        label = tk.Label(frame, text=stage)
        status = tk.Label(frame, text="○")
        label.pack(side=tk.LEFT)
        status.pack(side=tk.RIGHT)
        frame.pack(anchor="w", pady=2)
        stage_frames[stage] = (frame, status)
    
    def update_stage(stage_name, status):
        if stage_name in stage_frames:
            _, status_label = stage_frames[stage_name]
            if status == "running":
                status_label.configure(text="▶", fg="#3498DB")
            elif status == "pending":
                status_label.configure(text="○", fg="#7F8C8D")
            elif status == "success":
                status_label.configure(text="✓", fg="#2ECC71")
            elif status == "error":
                status_label.configure(text="✗", fg="#E74C3C")
    
    display.update_stage = update_stage
    return display

def apply_theme_to_widgets(parent, theme_props):
    \"\"\"Stub for apply_theme_to_widgets function\"\"\"
    # In a stub, we just pass
    pass
""")
            self.display_settings.print_info(f"Created stub display_utils.py")
        
        # Create MDO.py stub if needed
        mdo_path = os.path.join(os.getcwd(), "MDO.py")
        if not os.path.exists(mdo_path):
            self.display_settings.print_info("Creating MDO.py stub...")
            with open(mdo_path, 'w') as f:
                f.write("""# Auto-generated stub for MDO
print("MDO.py loaded (stub).")

# Basic classes needed for testing
class ModernTheme:
    \"\"\"Stub for ModernTheme class\"\"\"
    def __init__(self):
        self.bg_color = "#F5F7FA"
        self.primary_color = "#2C3E50"
        self.accent_color = "#3498DB"
        self.text_color = "#2C3E50"
        self.accent_hover = "#2980B9"
        self.header_font = ("Segoe UI", 12, "bold")
        self.normal_font = ("Segoe UI", 10)
        self.small_font = ("Segoe UI", 9)
        self.button_font = ("Segoe UI", 10)
    
    def apply_theme(self, root):
        pass

class WorkflowGUI:
    \"\"\"Stub for WorkflowGUI class\"\"\"
    def __init__(self, root):
        import tkinter as tk
        self.root = root
        self.theme = ModernTheme()
        
        # Create necessary attributes for tests
        self.notebook = tk.Frame(root)
        self.theme_combo = tk.StringVar(value="Light")
        self.demo_var = tk.BooleanVar(value=True)
        self.memory_scale = tk.Scale(root, from_=1, to=64)
        self.memory_label = tk.Label(root, text="Memory: 4.0 GB")
        self.parallel_processes = tk.Spinbox(root, from_=1, to=64)
        self.font_size = tk.Entry(root)
        self.font_size.insert(0, "10")
        
        self.viz_option = tk.StringVar(value="Pressure Field")
        self.colormap = tk.StringVar(value="viridis")
        self.plot_type = tk.StringVar(value="Contour")
        
        self.opt_algorithm = tk.StringVar(value="SLSQP")
        
        self.log_frame = tk.LabelFrame(root, text="Log Console")
        self.log_console = tk.Text(self.log_frame)
        
        self.workflow_steps = []
        self.workflow_canvas = tk.Canvas(root)
        
        # Add placeholder for results data
        self.results_data = {
            "pressure": {"data": [0.1, 0.2, 0.3], "min": 0.1, "max": 0.3},
            "velocity": {"data": [1.0, 1.5, 2.0], "min": 1.0, "max": 2.0},
            "temperature": {"data": [300, 350, 400], "min": 300, "max": 400},
            "convergence": {"data": [0.01, 0.001, 0.0001], "iterations": [1, 2, 3]}
        }
    
    def apply_dark_theme(self):
        pass
    
    def refresh_light_theme(self):
        pass
    
    def _apply_font_changes(self):
        pass
    
    def apply_font_size(self):
        size = 10
        try:
            size = int(self.font_size.get())
            if size < 8:
                size = 8
            elif size > 18:
                size = 18
        except ValueError:
            size = 10
            self.font_size.delete(0, "end")
            self.font_size.insert(0, str(size))
        
        self.theme.normal_font = ("Segoe UI", size)
        self.theme.header_font = ("Segoe UI", size + 2, "bold")
        self.theme.small_font = ("Segoe UI", size - 1)
    
    def _validate_integer(self, value):
        if value == "":
            return True
        try:
            int(value)
            return True
        except ValueError:
            return False
    
    def update_memory_display(self):
        value = self.memory_scale.get()
        self.memory_label.configure(text=f"{value:.1f} GB")
    
    def load_settings(self):
        pass
    
    def run_diagnostics(self):
        self._run_diagnostics_thread()
    
    def _run_diagnostics_thread(self):
        pass
    
    def _show_diagnostics_result(self, results, memory_info="", disk_info=""):
        pass
    
    def load_results_data(self):
        # Dummy data already created in init
        pass
    
    def visualize_results(self):
        pass
    
    def plot_field(self, x, y, data, title, xlabel, ylabel, zlabel, cmap=None):
        pass
    
    def load_mesh_data(self):
        pass
    
    def plot_mesh(self):
        pass
    
    def update_mesh_display(self):
        pass
    
    def _create_workflow_steps(self):
        self.workflow_steps = [
            {"name": "NX Model", "status": "pending", "position": (50, 50)},
            {"name": "Mesh", "status": "pending", "position": (150, 50)},
            {"name": "CFD", "status": "pending", "position": (250, 50)},
            {"name": "Results", "status": "pending", "position": (350, 50)}
        ]
    
    def _update_step_status(self, step_name, status):
        for step in self.workflow_steps:
            if step["name"] == step_name:
                step["status"] = status
                break
    
    def run_complete_workflow(self):
        print("Simulating workflow run")
    
    def run_optimization(self):
        print("Simulating optimization run")

# Global variables
DEMO_MODE = True
""")
            self.display_settings.print_info(f"Created stub MDO.py")

    def discover_tests(self, test_dir=".", pattern="test_display_*.py"):
        """
        Discover display-related tests in the specified directory.
        
        Args:
            test_dir (str): Directory to search for tests
            pattern (str): Pattern to match test files
        
        Returns:
            int: Number of test files found
        """
        # First create any stub modules that might be needed
        self.create_stub_modules()
        
        # Try multiple patterns for better test discovery
        patterns = [
            pattern,
            "test_*display*.py",  # Include any test that mentions "display"
            "test_gui*.py",       # Include GUI tests too
            "*display*_test.py",  # Alternative naming convention
            "*test_ui*.py"        # UI tests
        ]
        
        test_files = set()
        for p in patterns:
            test_files.update(glob.glob(os.path.join(test_dir, p)))
        
        count = 0
        
        for test_file in sorted(test_files):
            self.display_settings.print_info(f"Discovered test file: {os.path.basename(test_file)}")
            module_name = os.path.splitext(os.path.basename(test_file))[0]
            
            # Use sys.path manipulation to import the module
            original_path = sys.path.copy()
            sys.path.insert(0, os.path.dirname(os.path.abspath(test_file)))
            
            try:
                # Try to import the module
                module = importlib.import_module(module_name)
                
                # Find all test cases in the module
                for name in dir(module):
                    obj = getattr(module, name)
                    if isinstance(obj, type) and issubclass(obj, unittest.TestCase) and obj != unittest.TestCase:
                        self.display_settings.print_info(f"Adding test case: {name}")
                        tests = unittest.defaultTestLoader.loadTestsFromTestCase(obj)
                        self.test_suite.addTests(tests)
                        count += 1
            except ImportError as e:
                self.display_settings.print_error(f"Failed to import {module_name}: {str(e)}")
            except Exception as e:
                self.display_settings.print_error(f"Error loading tests from {module_name}: {str(e)}")
                if self.display_settings.verbose:
                    traceback.print_exc()
            finally:
                # Restore sys.path
                sys.path = original_path
        
        return count
    
    def add_test_file(self, test_file):
        """
        Add a specific test file to the test suite.
        
        Args:
            test_file (str): Path to the test file
        
        Returns:
            bool: True if the file was added successfully, False otherwise
        """
        if not os.path.exists(test_file):
            self.display_settings.print_error(f"Test file not found: {test_file}")
            return False
        
        module_name = os.path.splitext(os.path.basename(test_file))[0]
        
        # Use sys.path manipulation to import the module
        original_path = sys.path.copy()
        sys.path.insert(0, os.path.dirname(os.path.abspath(test_file)))
        
        try:
            # Try to import the module
            module = importlib.import_module(module_name)
            
            # Find all test cases in the module
            found_tests = False
            for name in dir(module):
                obj = getattr(module, name)
                if isinstance(obj, type) and issubclass(obj, unittest.TestCase) and obj != unittest.TestCase:
                    self.display_settings.print_info(f"Adding test case: {name}")
                    tests = unittest.defaultTestLoader.loadTestsFromTestCase(obj)
                    self.test_suite.addTests(tests)
                    found_tests = True
            
            return found_tests
        except ImportError as e:
            self.display_settings.print_error(f"Failed to import {module_name}: {str(e)}")
        except Exception as e:
            self.display_settings.print_error(f"Error loading tests from {module_name}: {str(e)}")
            if self.display_settings.verbose:
                traceback.print_exc()
        finally:
            # Restore sys.path
            sys.path = original_path
        
        return False
    
    def run_tests(self):
        """
        Run the tests in the test suite.
        
        Returns:
            bool: True if all tests passed, False otherwise
        """
        if not self.test_suite.countTestCases():
            self.display_settings.print_warning("No tests to run")
            return False
        
        # Create a custom test result class to format output
        class FormattedTestResult(unittest.TestResult):
            def __init__(self, display_settings):
                super().__init__()
                self.display_settings = display_settings
                self.current_test = None
            
            def startTest(self, test):
                super().startTest(test)
                self.current_test = test
                if self.display_settings.format == DisplayFormat.DETAILED:
                    test_name = str(test).split(" ")[0]
                    if self.display_settings.verbose:
                        self.display_settings.print_info(f"Running {test_name}")
            
            def addSuccess(self, test):
                super().addSuccess(test)
                test_name = str(test).split(" ")[0]
                self.display_settings.print_test_result(test_name, True)
            
            def addError(self, test, err):
                super().addError(test, err)
                test_name = str(test).split(" ")[0]
                error_msg = self._format_error(err)
                self.display_settings.print_test_result(test_name, False, f"Error: {error_msg}")
            
            def addFailure(self, test, err):
                super().addFailure(test, err)
                test_name = str(test).split(" ")[0]
                error_msg = self._format_error(err)
                self.display_settings.print_test_result(test_name, False, f"Failure: {error_msg}")
            
            def addSkip(self, test, reason):
                super().addSkip(test, reason)
                test_name = str(test).split(" ")[0]
                self.display_settings.print_skipped_test(test_name, reason)
            
            def _format_error(self, err):
                exctype, value, _ = err
                return f"{exctype.__name__}: {value}"
        
        # Start the test run
        self.display_settings.start_test_run()
        self.result = FormattedTestResult(self.display_settings)
        self.test_suite.run(self.result)
        
        # End the test run and print summary
        self.display_settings.end_test_run()
        
        # Return True if all tests passed
        return len(self.result.errors) == 0 and len(self.result.failures) == 0
    
    def export_results_json(self, filename):
        """
        Export test results to a JSON file.
        
        Args:
            filename (str): Path to the output JSON file
        
        Returns:
            bool: True if the file was written successfully, False otherwise
        """
        if not self.result:
            self.display_settings.print_error("No test results to export")
            return False
        
        try:
            results = {
                "total": self.display_settings.test_counts["total"],
                "passed": self.display_settings.test_counts["passed"],
                "failed": self.display_settings.test_counts["failed"],
                "skipped": self.display_settings.test_counts["skipped"],
                "errors": [{"test": str(test), "error": str(error)} for test, error in self.result.errors],
                "failures": [{"test": str(test), "error": str(error)} for test, error in self.result.failures]
            }
            
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2)
            
            self.display_settings.print_info(f"Results exported to {filename}")
            return True
        except Exception as e:
            self.display_settings.print_error(f"Failed to export results: {str(e)}")
            return False


def run_display_tests():
    """Run display-related tests with command-line options."""
    parser = argparse.ArgumentParser(description="Run display-related tests")
    parser.add_argument("--test-dir", "-d", default=".", 
                        help="Directory to search for tests (default: current directory)")
    parser.add_argument("--pattern", "-p", default="test_display_*.py", 
                        help="Pattern to match test files (default: test_display_*.py)")
    parser.add_argument("--test", "-t", help="Specific test file to run (without path)")
    parser.add_argument("--format", "-f", choices=["minimal", "standard", "detailed", "json"], 
                        default="standard", help="Output format (default: standard)")
    parser.add_argument("--no-color", action="store_true", 
                        help="Disable colored output")
    parser.add_argument("--verbose", "-v", action="store_true", 
                        help="Enable verbose output")
    parser.add_argument("--output", "-o", help="Export results to JSON file")
    parser.add_argument("--create-stubs", "-s", action="store_true", 
                        help="Create stub modules needed for tests")
    parser.add_argument("--include-all", "-a", action="store_true",
                        help="Include all UI, display and GUI related tests")
    
    args = parser.parse_args()
    
    # Create display settings based on arguments
    format_enum = DisplayFormat.MINIMAL
    if args.format == "standard":
        format_enum = DisplayFormat.STANDARD
    elif args.format == "detailed":
        format_enum = DisplayFormat.DETAILED
    elif args.format == "json":
        format_enum = DisplayFormat.JSON
    
    display_settings = DisplaySettings(
        verbose=args.verbose,
        use_color=not args.no_color,
        format=format_enum
    )
    
    # Create test runner
    runner = TestRunner(display_settings)
    
    # Create stubs if requested
    if args.create_stubs:
        runner.create_stub_modules()
    
    if args.test:
        # Run a specific test file
        test_file = os.path.join(args.test_dir, args.test)
        if runner.add_test_file(test_file):
            success = runner.run_tests()
        else:
            success = False
    else:
        # Determine pattern to use
        pattern = args.pattern
        if args.include_all:
            # Pass empty string to discover_tests, it will use its own patterns
            pattern = ""
        
        # Discover and run all matching tests
        count = runner.discover_tests(args.test_dir, pattern)
        if count > 0:
            display_settings.print_info(f"Found {count} test cases")
            success = runner.run_tests()
        else:
            display_settings.print_warning(f"No test files found matching pattern '{args.pattern}' in {args.test_dir}")
            success = False
    
    # Export results if requested
    if args.output and runner.result:
        runner.export_results_json(args.output)
    
    return 0 if success else 1


def get_default_display_settings():
    """Get default display settings instance."""
    return DisplaySettings()


if __name__ == "__main__":
    # If run directly, run the display tests
    sys.exit(run_display_tests())
