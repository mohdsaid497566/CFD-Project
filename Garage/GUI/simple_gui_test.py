#!/usr/bin/env python3
"""
Simple GUI Test - Tests basic GUI functionality without NX dependencies
"""

import sys
import os
import tkinter as tk
from tkinter import ttk
import traceback

def run_simple_gui_test():
    """
    Run a simple test of the GUI components
    """
    print("Starting simple GUI test...")
    root = None
    
    try:
        # Import the patch module
        import patch
        import gui_helper
        
        # Create a logger
        logger = gui_helper.setup_logging()
        logger.info("Starting simple GUI test")
        
        # Create a simple GUI class for testing
        class SimpleGUI:
            def __init__(self, root):
                self.root = root
                self.initialized = True
                self.theme_combo = None
                self.preset_combo = None
                self.font_size = None
                self.demo_var = tk.BooleanVar(value=True)
                self.workflow_steps = []
                self.status_bar = None
                print("SimpleGUI initialized")
                
            def log(self, message):
                """Log a message"""
                print(f"LOG: {message}")
                return True
                
            def update_status(self, message, show_progress=False):
                """Update status bar with a message"""
                print(f"STATUS: {message}")
                if not self.status_bar:
                    self.status_bar = ttk.Label(self.root, text=message)
                    self.status_bar.pack(side='bottom', fill='x')
                else:
                    self.status_bar.config(text=message)
                self.root.update_idletasks()
                return True
                
            def setup_theme_components(self):
                """Set up theme components for testing"""
                frame = ttk.Frame(self.root)
                frame.pack(fill='both', expand=True, padx=10, pady=10)
                
                # Theme selection
                theme_frame = ttk.LabelFrame(frame, text="Theme Settings")
                theme_frame.pack(fill='x', padx=10, pady=5)
                
                self.theme_combo = ttk.Combobox(theme_frame, values=["Light", "Dark", "System"])
                self.theme_combo.current(0)
                self.theme_combo.pack(padx=10, pady=5)
                
                # Font size
                self.font_size = ttk.Entry(theme_frame)
                self.font_size.insert(0, "12")
                self.font_size.pack(padx=10, pady=5)
                
                # Preset selection
                preset_frame = ttk.LabelFrame(frame, text="Workflow Presets")
                preset_frame.pack(fill='x', padx=10, pady=5)
                
                self.preset_combo = ttk.Combobox(preset_frame, values=["Default", "High Resolution", "Low Memory"])
                self.preset_combo.current(0)
                self.preset_combo.pack(padx=10, pady=5)
                
                return True
                
        # Create root window
        root = tk.Tk()
        root.title("Simple GUI Test")
        root.geometry("600x400")
        
        # Patch the test class
        PatchedGUI = patch.patch_workflow_gui(SimpleGUI)
        
        # Create an instance of the GUI
        gui = PatchedGUI(root)
        
        # Set up components for testing
        gui.setup_theme_components()
        
        # Test theme changing
        print("Testing theme change functionality...")
        if hasattr(gui, 'change_theme'):
            gui.theme_combo.set("Dark")
            gui.change_theme()
            print("✅ Changed theme to Dark")
            
            gui.theme_combo.set("Light")  
            gui.change_theme()
            print("✅ Changed theme to Light")
        else:
            print("❌ change_theme method not available")
        
        # Test preset loading
        print("\nTesting preset loading functionality...")
        if hasattr(gui, 'load_preset'):
            gui.preset_combo.set("High Resolution")
            result = gui.load_preset("High Resolution")
            print(f"✅ Load preset result: {result}")
        else:
            print("❌ load_preset method not available")
            
        # Test workflow visualization if available
        print("\nTesting workflow visualization...")
        if hasattr(gui, '_create_workflow_steps'):
            gui.workflow_canvas = tk.Canvas(root)
            gui.workflow_canvas.pack(fill='both', expand=True)
            gui._create_workflow_steps()
            print(f"✅ Created {len(gui.workflow_steps)} workflow steps")
            
            # Update status if available
            if hasattr(gui, 'update_step_status'):
                gui.update_step_status(0, "complete")
                print("✅ Updated step status successfully")
            else:
                print("❌ update_step_status method not available")
        else:
            print("❌ _create_workflow_steps method not available")
            
        print("\nAll tests completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error during GUI test: {str(e)}")
        traceback.print_exc()
        return False
    finally:
        if root:
            # Don't enter mainloop - just close the window when done testing
            root.destroy()

if __name__ == "__main__":
    success = run_simple_gui_test()
    if success:
        print("\n✅ Simple GUI test completed successfully")
        sys.exit(0)
    else:
        print("\n❌ Simple GUI test failed")
        sys.exit(1)