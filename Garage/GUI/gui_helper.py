"""
GUI helper functions for the Intake CFD Optimization Suite.

This module provides helper functions for GUI components, including theme setup,
header creation, and other UI utilities.
"""

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import os
import platform
import logging
import sys
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("gui_helper")

class ModernTheme:
    """Modern theme settings for the application"""
    def __init__(self):
        # Color scheme - sophisticated blue theme
        self.bg_color = "#F5F7FA"  # Light background
        self.primary_color = "#2C3E50"  # Dark blue for headers
        self.accent_color = "#3498DB"  # Blue for buttons and accents
        self.accent_hover = "#2980B9"  # Darker blue for hover states
        self.text_color = "#2C3E50"  # Dark blue text
        self.light_text = "#ECF0F1"  # Light text for dark buttons
        self.success_color = "#2ECC71"  # Green for success messages
        self.warning_color = "#F39C12"  # Orange for warnings
        self.error_color = "#E74C3C"  # Red for errors
        self.border_color = "#BDC3C7"  # Light gray for borders

        # Font settings
        self.header_font = ("Segoe UI", 12, "bold")
        self.normal_font = ("Segoe UI", 10)
        self.small_font = ("Segoe UI", 9)
        self.button_font = ("Segoe UI", 10)
        self.code_font = ("Consolas", 9)

        # Padding and spacing
        self.padding = 10
        self.small_padding = 5
        self.large_padding = 15

def setup_theme(root):
    """
    Set up the modern theme for the application.
    
    Args:
        root: The Tkinter root window
    """
    theme = ModernTheme()
    
    # Configure the root window
    root.configure(background=theme.bg_color)
    
    # Configure styles for different widgets
    style = ttk.Style()
    style.configure("TFrame", background=theme.bg_color)
    style.configure("TLabel", background=theme.bg_color, foreground=theme.text_color, font=theme.normal_font)
    style.configure("TButton", 
                   background=theme.accent_color,
                   foreground=theme.light_text, 
                   font=theme.button_font,
                   borderwidth=0,
                   focusthickness=3,
                   focuscolor=theme.accent_color)
    style.map("TButton",
             background=[('active', theme.accent_hover), ('pressed', theme.accent_hover)],
             relief=[('pressed', 'groove'), ('!pressed', 'ridge')])
    
    # Configure special styles
    style.configure("Header.TLabel", font=theme.header_font, foreground=theme.primary_color)
    style.configure("Success.TLabel", foreground=theme.success_color)
    style.configure("Warning.TLabel", foreground=theme.warning_color)
    style.configure("Error.TLabel", foreground=theme.error_color)
    
    style.configure("Primary.TButton", 
                   background=theme.primary_color,
                   foreground=theme.light_text)
    style.map("Primary.TButton",
             background=[('active', theme.primary_color), ('pressed', theme.primary_color)])
             
    # Configure notebook styles
    style.configure("TNotebook", background=theme.bg_color, borderwidth=0)
    style.configure("TNotebook.Tab", 
                   background=theme.bg_color, 
                   foreground=theme.text_color,
                   font=theme.normal_font,
                   padding=[10, 5],
                   borderwidth=0)
    style.map("TNotebook.Tab",
             background=[('selected', theme.accent_color), ('active', theme.accent_hover)],
             foreground=[('selected', theme.light_text), ('active', theme.light_text)])
    
    # LabelFrame styling
    style.configure("TLabelframe", background=theme.bg_color)
    style.configure("TLabelframe.Label", 
                   font=theme.header_font,
                   foreground=theme.primary_color,
                   background=theme.bg_color)
                   
    # Entry and Combobox styling
    style.configure("TEntry", 
                   foreground=theme.text_color,
                   fieldbackground="white",
                   borderwidth=1,
                   relief="solid")
    style.map("TEntry", 
             fieldbackground=[('readonly', theme.bg_color)])
             
    style.configure("TCombobox", 
                   foreground=theme.text_color,
                   fieldbackground="white",
                   selectbackground=theme.accent_color,
                   selectforeground=theme.light_text)
    
    return theme

def create_header(root, title, icon_path=None):
    """
    Create a header section for the application.
    
    Args:
        root: The parent widget
        title: The application title
        icon_path: Path to the application icon (optional)
        
    Returns:
        The header frame
    """
    theme = ModernTheme()
    
    # Create header frame
    header_frame = ttk.Frame(root, padding=theme.padding)
    header_frame.pack(fill='x', expand=False)
    
    # Create logo if icon_path is provided
    if icon_path and os.path.exists(icon_path):
        try:
            # Load and resize the logo
            logo_img = Image.open(icon_path)
            logo_img = logo_img.resize((32, 32), Image.LANCZOS)
            logo_tk = ImageTk.PhotoImage(logo_img)
            
            # Create a label for the logo
            logo_label = ttk.Label(header_frame, image=logo_tk, background=theme.bg_color)
            logo_label.image = logo_tk  # Keep a reference
            logo_label.pack(side='left', padx=(0, theme.padding))
            
        except Exception as e:
            logger.error(f"Error loading logo: {str(e)}")
    
    # Create header title
    header_title = ttk.Label(header_frame, text=title, style="Header.TLabel", 
                           font=("Segoe UI", 16, "bold"))
    header_title.pack(side='left')
    
    return header_frame

def create_status_bar(root, initial_status="Ready"):
    """
    Create a status bar for the application.
    
    Args:
        root: The parent widget
        initial_status: Initial status message
        
    Returns:
        The status frame and status label
    """
    theme = ModernTheme()
    
    # Create status frame
    status_frame = ttk.Frame(root)
    status_frame.pack(side='bottom', fill='x')
    
    # Add a separator
    separator = ttk.Separator(status_frame, orient='horizontal')
    separator.pack(fill='x')
    
    # Create status label
    status_var = tk.StringVar(value=initial_status)
    status_label = ttk.Label(status_frame, textvariable=status_var, 
                           font=theme.small_font, padding=(theme.padding, 2))
    status_label.pack(side='left')
    
    # Create progress bar (hidden by default)
    progress_var = tk.DoubleVar(value=0)
    progress_bar = ttk.Progressbar(status_frame, variable=progress_var, mode='indeterminate')
    
    def update_status(message, show_progress=False):
        """Update status bar message and progress indicator"""
        status_var.set(message)
        
        if show_progress:
            progress_bar.pack(side='right', fill='x', expand=True, padx=theme.padding, pady=2)
            progress_bar.start(10)
        else:
            progress_bar.stop()
            progress_bar.pack_forget()
    
    # Attach the update method to the status_frame
    status_frame.update_status = update_status
    
    return status_frame, status_var

def detect_platform():
    """
    Detect the current platform and return platform-specific information.
    
    Returns:
        dict: Platform information
    """
    system = platform.system()
    info = {
        'system': system,
        'release': platform.release(),
        'version': platform.version(),
        'is_wsl': False
    }
    
    # Check for WSL (Windows Subsystem for Linux)
    if system == "Linux":
        if "microsoft" in platform.release().lower():
            info['is_wsl'] = True
        elif os.path.exists("/proc/version"):
            try:
                with open("/proc/version", "r") as f:
                    if "microsoft" in f.read().lower():
                        info['is_wsl'] = True
            except:
                pass
        elif os.path.exists("/mnt/c/Windows"):
            info['is_wsl'] = True
    
    return info

def create_tooltip(widget, text, delay=500):
    """
    Create a tooltip for a widget.
    
    Args:
        widget: The widget to attach the tooltip to
        text: The tooltip text
        delay: Delay before showing tooltip in milliseconds
    """
    tooltip = None
    
    def enter(event):
        nonlocal tooltip
        x, y, _, _ = widget.bbox("insert")
        x += widget.winfo_rootx() + 25
        y += widget.winfo_rooty() + 25
        
        # Create new tooltip window
        tooltip = tk.Toplevel(widget)
        tooltip.wm_overrideredirect(True)  # Remove window decoration
        tooltip.wm_geometry(f"+{x}+{y}")
        
        label = ttk.Label(tooltip, text=text, wraplength=250,
                        background="#FFFFDD", relief="solid", borderwidth=1,
                        padding=(5, 3))
        label.pack()
        
    def leave(event):
        nonlocal tooltip
        if tooltip:
            tooltip.destroy()
            tooltip = None
    
    def schedule_tooltip():
        widget.after(delay, enter)
    
    widget.bind('<Enter>', lambda e: schedule_tooltip())
    widget.bind('<Leave>', leave)

def is_dark_mode():
    """
    Detect if the system is using a dark mode theme.
    
    Returns:
        bool: True if dark mode is enabled, False otherwise
    """
    system = platform.system()
    
    if system == "Windows":
        try:
            import winreg
            registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
            key = winreg.OpenKey(registry, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            return value == 0
        except:
            pass
    
    elif system == "Darwin":  # macOS
        try:
            import subprocess
            result = subprocess.run(
                ['defaults', 'read', '-g', 'AppleInterfaceStyle'],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            return 'Dark' in result.stdout
        except:
            pass
    
    elif system == "Linux":
        # Check for GNOME dark theme
        try:
            import subprocess
            result = subprocess.run(
                ['gsettings', 'get', 'org.gnome.desktop.interface', 'gtk-theme'],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            return 'dark' in result.stdout.lower()
        except:
            pass
    
    # Default to light mode if detection fails
    return False
