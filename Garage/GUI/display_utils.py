"""
Enhanced display utilities for the Intake CFD application.
Provides advanced theme control, UI transitions, and display helpers.
"""

import tkinter as tk
from tkinter import ttk
import platform
import os
import time
import threading
import colorsys
from typing import Dict, Any, Tuple, List, Union, Optional
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import matplotlib.colors as colors
import matplotlib.cm as cm
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("display_utils")


class ThemeTransition:
    """
    Handles smooth transitions between themes by gradually changing colors.
    """
    def __init__(self, root, duration=0.5, steps=10):
        self.root = root
        self.duration = duration
        self.steps = steps
        self.transition_active = False
        self.transition_thread = None
    
    def interpolate_color(self, start_color: str, end_color: str, fraction: float) -> str:
        """Interpolate between two hex colors."""
        # Convert hex to RGB
        start_rgb = tuple(int(start_color[i:i+2], 16) for i in (1, 3, 5))
        end_rgb = tuple(int(end_color[i:i+2], 16) for i in (1, 3, 5))
        
        # Interpolate
        current_rgb = tuple(int(start_rgb[i] + fraction * (end_rgb[i] - start_rgb[i])) for i in range(3))
        
        # Convert back to hex
        return f"#{current_rgb[0]:02x}{current_rgb[1]:02x}{current_rgb[2]:02x}"
    
    def transition(self, widget_map: Dict[Any, Dict[str, Tuple[str, str]]]):
        """
        Perform a smooth transition between theme colors.
        
        Args:
            widget_map: A mapping of widgets to their property transitions
                Format: {widget: {"property": (start_color, end_color)}}
        """
        if self.transition_active:
            return
            
        self.transition_active = True
        delay = self.duration / self.steps
        
        def run_transition():
            try:
                for step in range(self.steps + 1):
                    fraction = step / self.steps
                    
                    for widget, properties in widget_map.items():
                        for prop, (start, end) in properties.items():
                            if start.startswith('#') and end.startswith('#'):
                                # Color interpolation
                                try:
                                    current = self.interpolate_color(start, end, fraction)
                                    widget[prop] = current
                                except (ValueError, IndexError):
                                    # Fall back to direct assignment if color interpolation fails
                                    widget[prop] = end if fraction > 0.5 else start
                            else:
                                # Non-color property - just switch at midpoint
                                widget[prop] = end if fraction > 0.5 else start
                                
                    # Update the UI
                    self.root.update_idletasks()
                    time.sleep(delay)
            finally:
                self.transition_active = False
        
        # Run in a separate thread to avoid blocking the UI
        self.transition_thread = threading.Thread(target=run_transition)
        self.transition_thread.daemon = True
        self.transition_thread.start()


class ColorScheme:
    """
    Advanced color scheme generator with support for light/dark themes
    and automatic contrast calculations.
    """
    def __init__(self, primary_color: str, is_dark: bool = False):
        self.primary_color = primary_color
        self.is_dark = is_dark
        self.colors = self._generate_color_scheme()
    
    def _generate_color_scheme(self) -> Dict[str, str]:
        """Generate a full color scheme from the primary color."""
        # Convert primary color from hex to HSV
        r, g, b = tuple(int(self.primary_color[i:i+2], 16) for i in (1, 3, 5))
        h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
        
        # Generate variations
        if self.is_dark:
            bg_color = self._adjust_color(h, 0.1, 0.2)  # Dark background
            text_color = self._adjust_color(h, 0.1, 0.9)  # Light text
            accent_color = self._adjust_color(h, 0.7, 0.8)  # Bright accent
        else:
            bg_color = self._adjust_color(h, 0.1, 0.95)  # Light background
            text_color = self._adjust_color(h, 0.1, 0.2)  # Dark text
            accent_color = self._adjust_color(h, 1.0, 0.7)  # Saturated accent
            
        # Create the color scheme
        return {
            'primary': self.primary_color,
            'background': bg_color,
            'text': text_color,
            'accent': accent_color,
            'accent_hover': self._adjust_brightness(accent_color, 0.9 if self.is_dark else 1.1),
            'success': "#2ECC71" if self.is_dark else "#27AE60",
            'warning': "#F39C12" if self.is_dark else "#E67E22",
            'error': "#E74C3C" if self.is_dark else "#C0392B",
            'border': self._adjust_brightness(bg_color, 0.8 if self.is_dark else 0.9)
        }
    
    def _adjust_color(self, hue: float, saturation: float, value: float) -> str:
        """Generate a color with the given HSV values."""
        r, g, b = colorsys.hsv_to_rgb(hue, saturation, value)
        return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
    
    def _adjust_brightness(self, color: str, factor: float) -> str:
        """Adjust the brightness of a color by a factor."""
        # Convert hex to RGB
        r, g, b = tuple(int(color[i:i+2], 16) for i in (1, 3, 5))
        
        # Convert to HSV
        h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
        
        # Adjust value (brightness)
        v = min(1.0, max(0.0, v * factor))
        
        # Convert back to RGB
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        
        # Convert to hex
        return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
    
    def get_contrasting_text_color(self, background_color: str) -> str:
        """Return white or black depending on which gives better contrast with background."""
        # Convert hex to RGB
        r, g, b = tuple(int(background_color[i:i+2], 16) for i in (1, 3, 5))
        
        # Calculate luminance (perceived brightness)
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        
        # Return white for dark backgrounds, black for light backgrounds
        return "#FFFFFF" if luminance < 0.5 else "#000000"


class SystemThemeDetector:
    """Detect and monitor system theme (light/dark) across platforms."""
    
    @staticmethod
    def get_system_theme() -> str:
        """
        Get the current system theme preference.
        Returns: "dark", "light", or "unknown"
        """
        system = platform.system()
        
        if system == "Windows":
            try:
                import winreg
                registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
                key = winreg.OpenKey(registry, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
                value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                return "light" if value == 1 else "dark"
            except:
                pass
        
        elif system == "Darwin":  # macOS
            try:
                import subprocess
                cmd = ["defaults", "read", "-g", "AppleInterfaceStyle"]
                result = subprocess.run(cmd, capture_output=True, text=True)
                return "dark" if "Dark" in result.stdout else "light"
            except:
                return "light"  # Default to light if command fails
        
        elif system == "Linux":
            # Try to detect GNOME theme
            if os.environ.get('DESKTOP_SESSION') in ['gnome', 'gnome-classic', 'ubuntu', 'pop']:
                try:
                    import subprocess
                    cmd = ["gsettings", "get", "org.gnome.desktop.interface", "gtk-theme"]
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    return "dark" if "dark" in result.stdout.lower() else "light"
                except:
                    pass
            
            # Try to detect KDE theme
            if os.environ.get('XDG_CURRENT_DESKTOP') == 'KDE':
                try:
                    import subprocess
                    cmd = ["kreadconfig5", "--file", "kdeglobals", "--group", "General", "--key", "ColorScheme"]
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    return "dark" if "dark" in result.stdout.lower() else "light"
                except:
                    pass
                    
        return "light"  # Default to light theme if detection fails


class MemoryVisualizer:
    """
    Visualize memory usage with advanced graphics and utilization indicators.
    """
    def __init__(self, canvas_widget, width=200, height=80, bg_color="#FFFFFF", 
                 progress_color="#3498DB", text_color="#2C3E50"):
        self.canvas = canvas_widget
        self.width = width
        self.height = height
        self.bg_color = bg_color
        self.progress_color = progress_color
        self.text_color = text_color
        self.setup_canvas()
        
    def setup_canvas(self):
        """Initialize the canvas."""
        self.canvas.config(width=self.width, height=self.height, bg=self.bg_color, 
                           highlightthickness=0)
    
    def update_display(self, used_percent, used_gb, total_gb):
        """Update the memory usage visualization."""
        self.canvas.delete("all")
        
        # Draw background bar
        bar_height = self.height * 0.6
        bar_y = (self.height - bar_height) / 2
        self.canvas.create_rectangle(
            10, bar_y, self.width - 10, bar_y + bar_height,
            fill="#EEEEEE", outline="#CCCCCC", width=1
        )
        
        # Draw usage bar
        used_width = (self.width - 20) * (used_percent / 100)
        self.canvas.create_rectangle(
            10, bar_y, 10 + used_width, bar_y + bar_height,
            fill=self.progress_color, outline="", width=0
        )
        
        # Add markers at 25%, 50%, 75%
        for mark in [0.25, 0.5, 0.75]:
            x_pos = 10 + (self.width - 20) * mark
            self.canvas.create_line(
                x_pos, bar_y - 3, x_pos, bar_y + bar_height + 3,
                fill="#AAAAAA", width=1
            )
        
        # Add usage text
        usage_text = f"{used_gb:.1f} GB / {total_gb:.1f} GB ({used_percent:.0f}%)"
        self.canvas.create_text(
            self.width / 2, self.height - 10,
            text=usage_text, fill=self.text_color, font=("Arial", 9)
        )


class WidgetFactory:
    """Factory for creating consistently styled widgets."""
    
    def __init__(self, theme):
        self.theme = theme
        
    def create_header(self, parent, text, **kwargs):
        """Create a header label with consistent styling."""
        label = ttk.Label(parent, text=text, style="Header.TLabel", **kwargs)
        return label
        
    def create_button(self, parent, text, command, is_primary=False, **kwargs):
        """Create a styled button."""
        style = "Primary.TButton" if is_primary else "TButton"
        button = ttk.Button(parent, text=text, command=command, style=style, **kwargs)
        return button
        
    def create_form_field(self, parent, label_text, default_value="", **kwargs):
        """Create a labeled form field."""
        frame = ttk.Frame(parent)
        
        # Create label and entry in frame
        ttk.Label(frame, text=label_text).pack(anchor="w", pady=(0, 2))
        
        # Create entry
        entry = ttk.Entry(frame, **kwargs)
        entry.insert(0, default_value)
        entry.pack(fill="x", expand=True)
        
        return frame, entry


def apply_tooltip(widget, text, delay=500):
    """Apply a tooltip to a widget with fade-in effect."""
    
    tooltip = None
    
    def on_enter(event):
        nonlocal tooltip
        # Get widget position
        x, y, _, _ = widget.bbox("insert")
        x += widget.winfo_rootx() + 25
        y += widget.winfo_rooty() + 25
        
        def show_tooltip():
            nonlocal tooltip
            tooltip = tk.Toplevel(widget)
            tooltip.wm_overrideredirect(True)  # Remove window decorations
            tooltip.wm_geometry(f"+{x}+{y}")
            
            # Create a frame with a border
            frame = ttk.Frame(tooltip, borderwidth=1, relief="solid")
            frame.pack(fill="both", expand=True)
            
            # Add the text with padding
            label = ttk.Label(frame, text=text, justify="left", wraplength=250, 
                             padding=(5, 3))
            label.pack()
            
            # Animation effect
            tooltip.attributes('-alpha', 0.0)
            for i in range(1, 11):
                tooltip.attributes('-alpha', i/10)
                tooltip.update()
                time.sleep(0.02)
        
        # Start timer to show tooltip after delay
        widget._timer = widget.after(delay, show_tooltip)
        
    def on_leave(event):
        nonlocal tooltip
        # Cancel timer if tooltip hasn't shown yet
        if hasattr(widget, '_timer'):
            widget.after_cancel(widget._timer)
            
        # Destroy tooltip with fade-out effect
        if tooltip:
            for i in range(10, 0, -1):
                tooltip.attributes('-alpha', i/10)
                tooltip.update()
                time.sleep(0.01)
            tooltip.destroy()
            tooltip = None
    
    # Bind events
    widget.bind("<Enter>", on_enter)
    widget.bind("<Leave>", on_leave)


def create_status_indicator(parent, width=10, height=10, initial_status="idle"):
    """Create a status indicator that shows different colors based on status."""
    canvas = tk.Canvas(parent, width=width, height=height, 
                      highlightthickness=0, bg=parent.cget("background"))
    
    status_colors = {
        "idle": "#AAAAAA",      # Gray
        "running": "#3498DB",   # Blue
        "success": "#2ECC71",   # Green
        "warning": "#F39C12",   # Orange
        "error": "#E74C3C",     # Red
        "pending": "#BDC3C7"    # Light gray
    }
    
    def update_status(status):
        color = status_colors.get(status, status_colors["idle"])
        canvas.delete("all")
        canvas.create_oval(0, 0, width, height, fill=color, outline="")
        
    update_status(initial_status)
    canvas.update_status = update_status  # Attach the method to the canvas
    
    return canvas


def create_progress_display(parent, width=300, stages=None):
    """
    Create a multi-stage progress display with labels and status indicators.
    
    Args:
        parent: Parent widget
        width: Total width of the progress display
        stages: List of stage names
    """
    if stages is None:
        stages = ["Process 1", "Process 2", "Process 3"]
        
    frame = ttk.Frame(parent)
    
    # Calculate spacing
    num_stages = len(stages)
    spacing = width / (num_stages - 0.5)
    
    # Store stage widgets for later updates
    stage_indicators = {}
    stage_labels = {}
    
    # Create the stages and connections
    for i, stage in enumerate(stages):
        x_pos = 25 + i * spacing
        
        # Create status indicator
        indicator = create_status_indicator(frame)
        indicator.place(x=x_pos, y=10, anchor="center")
        stage_indicators[stage] = indicator
        
        # Create label under indicator
        label = ttk.Label(frame, text=stage)
        label.place(x=x_pos, y=30, anchor="center")
        stage_labels[stage] = label
        
        # Create connecting line to next stage
        if i < num_stages - 1:
            frame._line = ttk.Separator(frame, orient="horizontal")
            frame._line.place(x=x_pos + 15, y=10, width=spacing - 30)
    
    # Create method to update stage status
    def update_stage(stage_name, status):
        if stage_name in stage_indicators:
            stage_indicators[stage_name].update_status(status)
            
    # Attach the method to the frame
    frame.update_stage = update_stage
    
    return frame


# Utility function to apply a theme to all widgets in a tree
def apply_theme_to_widgets(parent, theme_props):
    """
    Recursively apply theme properties to all widgets in a widget tree.
    
    Args:
        parent: Root widget
        theme_props: Dictionary of theme properties for different widget types
    """
    widget_class = parent.__class__.__name__
    
    # Apply properties for this widget type
    if widget_class in theme_props:
        for prop, value in theme_props[widget_class].items():
            try:
                parent[prop] = value
            except tk.TclError:
                # Some widgets don't support all properties
                pass
    
    # Apply to children
    for child in parent.winfo_children():
        apply_theme_to_widgets(child, theme_props)


# Function to detect high contrast mode
def is_high_contrast_mode():
    """Detect if the system is running in high contrast mode."""
    system = platform.system()
    
    if system == "Windows":
        try:
            import winreg
            registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
            key = winreg.OpenKey(registry, r"Control Panel\Accessibility\HighContrast")
            value, _ = winreg.QueryValueEx(key, "Flags")
            return (value & 1) == 1  # Check if the first bit is set
        except:
            return False
    
    # For other systems, try to detect high contrast using environment variables
    # For GNOME
    if os.environ.get('GTK_THEME', '').endswith(':hc'):
        return True
    
    return False


# Create an accessibility wrapper for GUI applications
def make_accessible(widget, role=None, label=None, description=None):
    """
    Enhance widget accessibility by adding appropriate metadata.
    Works on platforms that support accessibility features.
    """
    if platform.system() == "Windows":
        try:
            # For Windows, use MSAA/IAccessible
            widget.winfo_toplevel().update_idletasks()  # Ensure widget is created
            
            # This approach uses undocumented tcl command to set accessibility props
            if label:
                widget.tk.call('set_accessible_name', widget._w, label)
            if description:
                widget.tk.call('set_accessible_description', widget._w, description)
            if role:
                widget.tk.call('set_accessible_role', widget._w, role)
        except:
            pass
    
    elif platform.system() == "Darwin":  # macOS
        try:
            # For macOS, use NSAccessibility
            if label:
                widget.tk.call('::tk::unsupported::MacWindowStyle', 'accessibility', 
                              widget._w, 'setTitle', label)
            if description:
                widget.tk.call('::tk::unsupported::MacWindowStyle', 'accessibility', 
                              widget._w, 'setHelp', description)
        except:
            pass
    
    # For GTK/Linux accessibility, add common attributes
    widget.winfo_toplevel().update_idletasks()  # Ensure widget is created
    if label:
        widget.winfo_toplevel().winfo_screen


def visualize_geometry(ax, vertices, triangles, color='lightblue', alpha=0.7, wireframe=True):
    """
    Visualize a 3D geometry using triangular faces.
    
    Args:
        ax: Matplotlib 3D axis
        vertices: Array of vertex coordinates (Nx3)
        triangles: Array of triangle indices (Mx3)
        color: Color for the geometry faces
        alpha: Transparency value
        wireframe: Whether to show wireframe
        
    Returns:
        None - updates the provided axis
    """
    if len(vertices) == 0 or len(triangles) == 0:
        logger.warning("No geometry data to visualize")
        ax.text(0.5, 0.5, 0.5, "No geometry data", 
                horizontalalignment='center', verticalalignment='center')
        return
    
    # Clear existing content
    ax.clear()
    
    try:
        # Create triangles for visualization
        triangle_vertices = []
        for tri in triangles:
            triangle_vertices.append([vertices[i] for i in tri])
            
        # Create a collection of triangles
        tri_collection = Poly3DCollection(triangle_vertices)
        
        # Set face color and transparency
        tri_collection.set_facecolor(color)
        tri_collection.set_alpha(alpha)
        
        # Set edge color if wireframe is enabled
        if wireframe:
            tri_collection.set_edgecolor('black')
            tri_collection.set_linewidth(0.5)
        else:
            tri_collection.set_edgecolor('none')
            
        # Add the collection to the axis
        ax.add_collection3d(tri_collection)
        
        # Set axis limits based on geometry bounds
        min_coords = np.min(vertices, axis=0)
        max_coords = np.max(vertices, axis=0)
        
        # Add some padding
        padding = 0.1 * max(max_coords - min_coords)
        
        ax.set_xlim(min_coords[0] - padding, max_coords[0] + padding)
        ax.set_ylim(min_coords[1] - padding, max_coords[1] + padding)
        ax.set_zlim(min_coords[2] - padding, max_coords[2] + padding)
        
        # Set axis labels
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')
        
        # Set title
        ax.set_title('Geometry Visualization')
        
    except Exception as e:
        logger.error(f"Error in geometry visualization: {str(e)}")
        ax.clear()
        ax.text(0.5, 0.5, 0.5, f"Error: {str(e)}", 
                horizontalalignment='center', verticalalignment='center')


def visualize_mesh(ax, nodes, elements, color_by='solid', quality_data=None, show_edges=True, alpha=0.7):
    """
    Visualize a 3D mesh.
    
    Args:
        ax: Matplotlib 3D axis
        nodes: Array of node coordinates (Nx3)
        elements: Array of element node indices (Mx4 for tets, Mx8 for hexes)
        color_by: How to color the mesh ('solid', 'element_type', 'quality')
        quality_data: Array of quality metrics for coloring (required if color_by='quality')
        show_edges: Whether to show mesh edges
        alpha: Transparency value
        
    Returns:
        None - updates the provided axis
    """
    if len(nodes) == 0 or len(elements) == 0:
        logger.warning("No mesh data to visualize")
        ax.text(0.5, 0.5, 0.5, "No mesh data", 
                horizontalalignment='center', verticalalignment='center')
        return
    
    # Clear existing content
    ax.clear()
    
    try:
        # Extract faces from elements (assuming tetrahedral elements)
        # For each tetrahedron, extract the four triangular faces
        faces = []
        for element in elements:
            # Tetrahedron faces
            if len(element) == 4:  # Tetrahedral element
                faces.append([element[0], element[1], element[2]])
                faces.append([element[0], element[1], element[3]])
                faces.append([element[0], element[2], element[3]])
                faces.append([element[1], element[2], element[3]])
            elif len(element) == 8:  # Hexahedral element
                # Extract the six quadrilateral faces of a hexahedron
                # We'll triangulate each quad face into two triangles
                faces.append([element[0], element[1], element[2]])
                faces.append([element[0], element[2], element[3]])
                faces.append([element[4], element[5], element[6]])
                faces.append([element[4], element[6], element[7]])
                faces.append([element[0], element[1], element[5]])
                faces.append([element[0], element[5], element[4]])
                faces.append([element[2], element[3], element[7]])
                faces.append([element[2], element[7], element[6]])
                faces.append([element[0], element[3], element[7]])
                faces.append([element[0], element[7], element[4]])
                faces.append([element[1], element[2], element[6]])
                faces.append([element[1], element[6], element[5]])
                
        # Create faces for visualization
        face_vertices = []
        face_colors = []
        
        for i, face in enumerate(faces):
            face_vertices.append([nodes[i] for i in face])
            
            # Determine face color
            if color_by == 'solid':
                face_colors.append('lightblue')
            elif color_by == 'element_type':
                # Color by element type (e.g., different colors for tets vs. hexes)
                elem_idx = i // 4 if len(elements[0]) == 4 else i // 12
                if len(elements[elem_idx]) == 4:
                    face_colors.append('lightblue')
                else:
                    face_colors.append('lightgreen')
            elif color_by == 'quality' and quality_data is not None:
                # Use quality data to determine color
                elem_idx = i // 4 if len(elements[0]) == 4 else i // 12
                if elem_idx < len(quality_data):
                    # Map quality to color using a colormap
                    quality = quality_data[elem_idx]
                    face_colors.append(plt.cm.viridis(quality))
                else:
                    face_colors.append('gray')
            else:
                face_colors.append('lightblue')
                
        # Create a collection of triangles
        face_collection = Poly3DCollection(face_vertices)
        
        # Set face colors and transparency
        face_collection.set_facecolor(face_colors)
        face_collection.set_alpha(alpha)
        
        # Set edge color if edges are enabled
        if show_edges:
            face_collection.set_edgecolor('black')
            face_collection.set_linewidth(0.2)
        else:
            face_collection.set_edgecolor('none')
            
        # Add the collection to the axis
        ax.add_collection3d(face_collection)
        
        # Set axis limits based on node bounds
        min_coords = np.min(nodes, axis=0)
        max_coords = np.max(nodes, axis=0)
        
        # Add some padding
        padding = 0.1 * max(max_coords - min_coords)
        
        ax.set_xlim(min_coords[0] - padding, max_coords[0] + padding)
        ax.set_ylim(min_coords[1] - padding, max_coords[1] + padding)
        ax.set_zlim(min_coords[2] - padding, max_coords[2] + padding)
        
        # Set axis labels
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')
        
        # Set title
        ax.set_title('Mesh Visualization')
        
        # Add colorbar if coloring by quality
        if color_by == 'quality' and quality_data is not None:
            sm = plt.cm.ScalarMappable(cmap=plt.cm.viridis, 
                                      norm=plt.Normalize(vmin=min(quality_data), 
                                                        vmax=max(quality_data)))
            sm.set_array([])
            plt.colorbar(sm, ax=ax, label='Quality')
        
    except Exception as e:
        logger.error(f"Error in mesh visualization: {str(e)}")
        ax.clear()
        ax.text(0.5, 0.5, 0.5, f"Error: {str(e)}", 
                horizontalalignment='center', verticalalignment='center')


def visualize_results(ax, x, y, z, values, plot_type='contour', colormap='viridis', title=None):
    """
    Visualize CFD results (e.g., pressure, velocity) on a surface.
    
    Args:
        ax: Matplotlib axis (2D or 3D)
        x, y, z: Coordinates for the results
        values: Result values to visualize
        plot_type: Type of plot ('contour', 'surface', 'wireframe')
        colormap: Colormap to use
        title: Plot title
        
    Returns:
        None - updates the provided axis
    """
    if len(x) == 0 or len(values) == 0:
        logger.warning("No results data to visualize")
        ax.text(0.5, 0.5, "No results data", 
                horizontalalignment='center', verticalalignment='center')
        return
    
    # Clear existing content
    ax.clear()
    
    try:
        # Determine if we need a 3D or 2D plot
        is_3d = hasattr(ax, 'zaxis')
        
        if is_3d:
            # 3D visualization
            if plot_type == 'surface':
                # Create a surface plot
                surf = ax.plot_surface(x, y, z, facecolors=plt.cm.get_cmap(colormap)(values),
                                      rstride=1, cstride=1, alpha=0.8)
                
            elif plot_type == 'wireframe':
                # Create a wireframe plot
                wire = ax.plot_wireframe(x, y, z, color='black', linewidth=0.5)
                # Color points by values
                scatter = ax.scatter(x.flatten(), y.flatten(), z.flatten(), 
                                   c=values.flatten(), cmap=colormap)
                
            else:  # Default to contour
                # Create a 3D contour plot
                contour = ax.contourf(x, y, z, values, cmap=colormap)
                
            # Set axis labels
            ax.set_xlabel('X')
            ax.set_ylabel('Y')
            ax.set_zlabel('Z')
            
        else:
            # 2D visualization
            if plot_type == 'contour':
                # Create a filled contour plot
                contour = ax.contourf(x, y, values, cmap=colormap)
                # Add contour lines
                lines = ax.contour(x, y, values, colors='k', linewidths=0.5)
                ax.clabel(lines, inline=True, fontsize=8)
                
            else:  # Default to pcolormesh for 2D
                # Create a pseudocolor plot
                mesh = ax.pcolormesh(x, y, values, cmap=colormap, shading='gouraud')
                
            # Set axis labels
            ax.set_xlabel('X')
            ax.set_ylabel('Y')
            
        # Set title
        if title:
            ax.set_title(title)
        else:
            ax.set_title('Results Visualization')
            
        # Add colorbar
        plt.colorbar(plt.cm.ScalarMappable(norm=colors.Normalize(vmin=np.min(values), 
                                                              vmax=np.max(values)), 
                                         cmap=colormap), 
                    ax=ax, label='Value')
        
    except Exception as e:
        logger.error(f"Error in results visualization: {str(e)}")
        ax.clear()
        ax.text(0.5, 0.5, f"Error: {str(e)}", 
                horizontalalignment='center', verticalalignment='center')


def plot_convergence_history(ax, iterations, objective_values, best_value=None):
    """
    Plot convergence history for optimization runs.
    
    Args:
        ax: Matplotlib axis
        iterations: Array of iteration numbers
        objective_values: Array of objective function values
        best_value: Best objective function value found (optional)
        
    Returns:
        None - updates the provided axis
    """
    if len(iterations) == 0 or len(objective_values) == 0:
        logger.warning("No convergence history to plot")
        ax.text(0.5, 0.5, "No convergence history", 
                horizontalalignment='center', verticalalignment='center')
        return
    
    # Clear existing content
    ax.clear()
    
    try:
        # Plot convergence history
        ax.plot(iterations, objective_values, 'b-', marker='o', label='Objective')
        
        # Plot best value if provided
        if best_value is not None:
            ax.axhline(y=best_value, color='r', linestyle='--', label=f'Best: {best_value:.6f}')
            
        # Set axis labels and title
        ax.set_xlabel('Iteration')
        ax.set_ylabel('Objective Value')
        ax.set_title('Optimization Convergence History')
        
        # Add grid and legend
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.legend()
        
        # Set y-axis scale based on data
        if min(objective_values) > 0 and max(objective_values) / min(objective_values) > 100:
            ax.set_yscale('log')
        
    except Exception as e:
        logger.error(f"Error in convergence history plotting: {str(e)}")
        ax.clear()
        ax.text(0.5, 0.5, f"Error: {str(e)}", 
                horizontalalignment='center', verticalalignment='center')


def export_figure(fig, filename, dpi=300):
    """
    Export a matplotlib figure to a file.
    
    Args:
        fig: Matplotlib figure
        filename: Output filename
        dpi: Resolution in dots per inch
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)
        
        # Save the figure
        fig.savefig(filename, dpi=dpi, bbox_inches='tight')
        
        logger.info(f"Figure exported to {filename}")
        return True
        
    except Exception as e:
        logger.error(f"Error exporting figure: {str(e)}")
        return False
