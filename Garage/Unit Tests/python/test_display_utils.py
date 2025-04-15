"""
Unit tests for the enhanced display utilities
"""
import unittest
import tkinter as tk
from tkinter import ttk
import os
import sys
import platform
import threading
import time

# Add parent directory to path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import display utilities to test
from display_utils import (
    ThemeTransition,
    ColorScheme,
    SystemThemeDetector,
    MemoryVisualizer,
    WidgetFactory,
    apply_tooltip,
    create_status_indicator,
    create_progress_display,
    apply_theme_to_widgets
)


class TestColorScheme(unittest.TestCase):
    """Test the ColorScheme class"""
    
    def test_light_theme_generation(self):
        """Test that light theme colors are generated correctly"""
        scheme = ColorScheme("#3498DB", is_dark=False)
        colors = scheme.colors
        
        # Check that all expected colors are present
        self.assertIn('primary', colors)
        self.assertIn('background', colors)
        self.assertIn('text', colors)
        self.assertIn('accent', colors)
        self.assertIn('accent_hover', colors)
        self.assertIn('success', colors)
        self.assertIn('warning', colors)
        self.assertIn('error', colors)
        self.assertIn('border', colors)
        
        # Verify primary color is set correctly
        self.assertEqual(colors['primary'], "#3498DB")
        
        # For a light theme, the background should be light
        bg_color = colors['background']
        r, g, b = int(bg_color[1:3], 16), int(bg_color[3:5], 16), int(bg_color[5:7], 16)
        brightness = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        self.assertGreater(brightness, 0.5, "Light theme background should be bright")
    
    def test_dark_theme_generation(self):
        """Test that dark theme colors are generated correctly"""
        scheme = ColorScheme("#3498DB", is_dark=True)
        colors = scheme.colors
        
        # For a dark theme, the background should be dark
        bg_color = colors['background']
        r, g, b = int(bg_color[1:3], 16), int(bg_color[3:5], 16), int(bg_color[5:7], 16)
        brightness = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        self.assertLess(brightness, 0.5, "Dark theme background should be dark")
        
    def test_contrasting_text_color(self):
        """Test that the contrasting text color function works correctly"""
        scheme = ColorScheme("#3498DB", is_dark=False)
        
        # Dark background should get white text
        text_color = scheme.get_contrasting_text_color("#000000")
        self.assertEqual(text_color, "#FFFFFF")
        
        # Light background should get black text
        text_color = scheme.get_contrasting_text_color("#FFFFFF")
        self.assertEqual(text_color, "#000000")


class TestMemoryVisualizer(unittest.TestCase):
    """Test the MemoryVisualizer class"""
    
    def setUp(self):
        """Set up test environment"""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the window
        self.canvas = tk.Canvas(self.root)
        
    def tearDown(self):
        """Clean up after each test"""
        self.root.destroy()
    
    def test_memory_visualizer_creation(self):
        """Test that the memory visualizer can be created"""
        visualizer = MemoryVisualizer(self.canvas)
        self.assertEqual(self.canvas.winfo_width(), 200)
        self.assertEqual(self.canvas.winfo_height(), 80)
    
    def test_memory_display_update(self):
        """Test that the memory display can be updated"""
        visualizer = MemoryVisualizer(self.canvas)
        visualizer.update_display(75, 6.0, 8.0)
        
        # Check that the canvas has some items now
        self.assertGreater(len(self.canvas.find_all()), 0)


class TestStatusIndicator(unittest.TestCase):
    """Test the status indicator utility"""
    
    def setUp(self):
        """Set up test environment"""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the window
        
    def tearDown(self):
        """Clean up after each test"""
        self.root.destroy()
    
    def test_status_indicator_creation(self):
        """Test that the status indicator can be created"""
        indicator = create_status_indicator(self.root)
        self.assertIsNotNone(indicator)
        
        # Check the update method exists and can be called
        indicator.update_status("running")
        indicator.update_status("success")
        indicator.update_status("error")
        
        # Interface checks passed if no exceptions


class TestProgressDisplay(unittest.TestCase):
    """Test the progress display utility"""
    
    def setUp(self):
        """Set up test environment"""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the window
        
    def tearDown(self):
        """Clean up after each test"""
        self.root.destroy()
    
    def test_progress_display_creation(self):
        """Test that the progress display can be created"""
        stages = ["Step 1", "Step 2", "Step 3", "Step 4"]
        display = create_progress_display(self.root, stages=stages)
        self.assertIsNotNone(display)
        
        # Check the update method exists and can be called
        display.update_stage("Step 1", "running")
        display.update_stage("Step 2", "pending")
        display.update_stage("Step 3", "success")
        display.update_stage("Step 4", "error")
        
        # Interface checks passed if no exceptions


class TestWidgetFactory(unittest.TestCase):
    """Test the widget factory utility"""
    
    def setUp(self):
        """Set up test environment"""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the window
        
        # Create a theme dictionary
        theme = {
            "bg_color": "#FFFFFF",
            "text_color": "#000000",
            "accent_color": "#3498DB",
            "header_font": ("Arial", 12, "bold"),
            "normal_font": ("Arial", 10)
        }
        self.factory = WidgetFactory(theme)
        
    def tearDown(self):
        """Clean up after each test"""
        self.root.destroy()
    
    def test_create_header(self):
        """Test that a header can be created"""
        header = self.factory.create_header(self.root, "Test Header")
        self.assertIsNotNone(header)
        self.assertEqual(header.cget("text"), "Test Header")
    
    def test_create_button(self):
        """Test that a button can be created"""
        def dummy_command():
            pass
        
        button = self.factory.create_button(self.root, "Test Button", dummy_command)
        self.assertIsNotNone(button)
        self.assertEqual(button.cget("text"), "Test Button")
        
        # Test primary button
        primary_button = self.factory.create_button(self.root, "Primary", dummy_command, is_primary=True)
        self.assertIsNotNone(primary_button)
        self.assertEqual(primary_button.cget("style"), "Primary.TButton")
    
    def test_create_form_field(self):
        """Test that a form field can be created"""
        frame, entry = self.factory.create_form_field(self.root, "Test Field", "Default Value")
        self.assertIsNotNone(frame)
        self.assertIsNotNone(entry)
        self.assertEqual(entry.get(), "Default Value")


class TestThemeTransition(unittest.TestCase):
    """Test the theme transition utility"""
    
    def setUp(self):
        """Set up test environment"""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the window
        
    def tearDown(self):
        """Clean up after each test"""
        self.root.destroy()
    
    def test_color_interpolation(self):
        """Test that colors can be interpolated correctly"""
        transition = ThemeTransition(self.root)
        
        # Test 50% interpolation
        midpoint = transition.interpolate_color("#000000", "#FFFFFF", 0.5)
        self.assertEqual(midpoint.lower(), "#7f7f7f")
        
        # Test 25% interpolation
        quarter = transition.interpolate_color("#000000", "#FFFFFF", 0.25)
        self.assertEqual(quarter.lower(), "#3f3f3f")
        
        # Test interpolation with colors
        blue_to_red = transition.interpolate_color("#0000FF", "#FF0000", 0.5)
        self.assertEqual(blue_to_red.lower(), "#7f007f")


class TestSystemThemeDetector(unittest.TestCase):
    """Test the system theme detector utility"""
    
    def test_system_theme_detection(self):
        """Test that system theme can be detected"""
        theme = SystemThemeDetector.get_system_theme()
        self.assertIn(theme, ["light", "dark"])


class TestAccessibilityUtils(unittest.TestCase):
    """Test the accessibility utilities"""
    
    def setUp(self):
        """Set up test environment"""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the window
        
    def tearDown(self):
        """Clean up after each test"""
        self.root.destroy()
    
    @unittest.skipIf(platform.system() not in ["Windows", "Darwin", "Linux"], "OS not supported")
    def test_apply_theme_to_widgets(self):
        """Test that a theme can be applied to widgets"""
        # Create a hierarchy of widgets
        frame = ttk.Frame(self.root)
        label = ttk.Label(frame, text="Test Label")
        button = ttk.Button(frame, text="Test Button")
        entry = ttk.Entry(frame)
        
        # Pack widgets
        label.pack()
        button.pack()
        entry.pack()
        frame.pack()
        
        # Define theme properties
        theme_props = {
            "TFrame": {"background": "#FFFFFF"},
            "TLabel": {"foreground": "#000000", "background": "#FFFFFF"},
            "TButton": {"foreground": "#FFFFFF", "background": "#0078D7"}
        }
        
        # Apply theme to widgets
        apply_theme_to_widgets(frame, theme_props)
        
        # No assertions needed, just checking that the function runs without errors


class TestLiveThemeTransition(unittest.TestCase):
    """Test live theme transitions"""
    
    def setUp(self):
        """Set up test environment"""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the window
        
    def tearDown(self):
        """Clean up after each test"""
        self.root.destroy()
    
    def test_theme_transition_interface(self):
        """Test the theme transition interface - not a visual test"""
        transition = ThemeTransition(self.root, duration=0.1, steps=3)
        
        # Create a label to test with
        label = ttk.Label(self.root, text="Test")
        
        # Define a simple transition
        widget_map = {
            label: {
                "foreground": ("#000000", "#FFFFFF"),
                "background": ("#FFFFFF", "#000000")
            }
        }
        
        # Start transition
        transition.transition(widget_map)
        
        # Wait for transition to complete
        start_time = time.time()
        while transition.transition_active and time.time() - start_time < 2:
            self.root.update_idletasks()
            time.sleep(0.05)
        
        # Verify transition completed
        self.assertFalse(transition.transition_active)


if __name__ == "__main__":
    unittest.main()
