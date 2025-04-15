#!/usr/bin/env python3

"""
GUI Fix Utility
This script helps diagnose and fix common GUI issues in the CFD Workflow Assistant.
"""

import os
import sys
import traceback
import importlib
import time
import gc

def check_tkinter():
    """Check if tkinter is functioning correctly"""
    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        # Test if tkinter can be initialized properly
        version = root.tk.call('info', 'patchlevel')
        print(f"Tkinter is working. Tcl/Tk version: {version}")
        root.destroy()
        return True
    except Exception as e:
        print(f"Tkinter issue detected: {str(e)}")
        return False

def check_display():
    """Check if the display server is accessible"""
    try:
        import os
        print(f"DISPLAY environment variable: {os.environ.get('DISPLAY', 'Not set')}")
        
        if sys.platform.startswith('linux'):
            if 'DISPLAY' not in os.environ:
                print("Warning: DISPLAY environment variable not set.")
                print("Tips: If running over SSH, make sure X11 forwarding is enabled.")
                print("      Use: ssh -X or ssh -Y for X11 forwarding.")
                return False
    except Exception as e:
        print(f"Display check error: {str(e)}")
        return False
    return True

def reduce_widget_leaks():
    """Apply fixes for widget-related memory leaks"""
    try:
        # Import the necessary modules
        from gui import workflow_gui
        
        # Define the destructor enhancement
        def enhanced_destroy(self):
            """Enhanced destroy method to properly clean up resources"""
            try:
                # Remove all traces and callbacks
                for attr_name in dir(self):
                    attr = getattr(self, attr_name)
                    # Check if it's a trace variable
                    if hasattr(attr, 'trace_vinfo'):
                        try:
                            for trace_mode, trace_callback in attr.trace_vinfo():
                                attr.trace_vdelete(trace_mode, trace_callback)
                        except Exception:
                            pass
                
                # Clean up any timers or after() calls
                if hasattr(self, 'after_ids') and self.after_ids:
                    for after_id in self.after_ids:
                        try:
                            self.after_cancel(after_id)
                        except Exception:
                            pass
                
                # Destroy all child widgets explicitly
                for widget in self.winfo_children():
                    try:
                        widget.destroy()
                    except Exception:
                        pass
                
                # Call original destroy method
                try:
                    self._original_destroy()
                except Exception:
                    pass
                
                # Force garbage collection
                gc.collect()
                
            except Exception as e:
                print(f"Error in enhanced destroy: {str(e)}")
        
        # Try to patch the WorkflowGUI class if available
        if hasattr(workflow_gui, 'WorkflowGUI'):
            # Store original destroy method
            if not hasattr(workflow_gui.WorkflowGUI, '_original_destroy'):
                workflow_gui.WorkflowGUI._original_destroy = workflow_gui.WorkflowGUI.destroy
                workflow_gui.WorkflowGUI.destroy = enhanced_destroy
                workflow_gui.WorkflowGUI.after_ids = []
                
                # Monkey patch after method to track IDs
                original_after = workflow_gui.WorkflowGUI.after
                def tracked_after(self, ms, func=None, *args):
                    after_id = original_after(self, ms, func, *args)
                    if not hasattr(self, 'after_ids'):
                        self.after_ids = []
                    self.after_ids.append(after_id)
                    return after_id
                
                workflow_gui.WorkflowGUI.after = tracked_after
                
                print("Applied widget leak fixes to WorkflowGUI")
                return True
    except Exception as e:
        print(f"Could not apply widget leak fixes: {str(e)}")
    return False

def optimize_gui_performance():
    """Apply optimization for GUI performance"""
    try:
        from gui import workflow_gui
        
        # Debounce/throttle function for performance improvements
        def debounce(wait):
            """Decorator to debounce a function"""
            def decorator(fn):
                last_call = [0]
                def debounced(*args, **kwargs):
                    current_time = time.time()
                    if current_time - last_call[0] >= wait:
                        last_call[0] = current_time
                        return fn(*args, **kwargs)
                return debounced
            return decorator
        
        # Find methods that might be causing performance issues
        for attr_name in dir(workflow_gui.WorkflowGUI):
            if attr_name.startswith('update_') or attr_name.startswith('refresh_'):
                try:
                    original_method = getattr(workflow_gui.WorkflowGUI, attr_name)
                    # Apply debounce to update/refresh methods
                    setattr(workflow_gui.WorkflowGUI, attr_name, debounce(0.1)(original_method))
                except Exception:
                    pass
        
        print("Applied GUI performance optimizations")
        return True
    except Exception as e:
        print(f"Could not apply GUI performance optimizations: {str(e)}")
    return False

def improve_threading():
    """Apply threading improvements to prevent UI freezes"""
    try:
        import threading
        from gui import workflow_gui
        
        # Define a thread-safe UI update function
        def run_in_main_thread(self, func, *args, **kwargs):
            """Run a function in the main thread"""
            if not hasattr(self, 'root') or not self.root:
                return func(*args, **kwargs)
            return self.root.after(0, func, *args, **kwargs)
        
        # Add the method to the WorkflowGUI class
        workflow_gui.WorkflowGUI.run_in_main_thread = run_in_main_thread
        
        # Find methods that might be doing heavy work
        heavy_work_keywords = ['calculate', 'process', 'generate', 'load', 'export']
        
        def run_in_background(func):
            """Decorator to run a function in the background"""
            def wrapper(self, *args, **kwargs):
                thread = threading.Thread(target=func, args=(self, *args), kwargs=kwargs)
                thread.daemon = True
                thread.start()
            return wrapper
        
        for attr_name in dir(workflow_gui.WorkflowGUI):
            for keyword in heavy_work_keywords:
                if keyword in attr_name and callable(getattr(workflow_gui.WorkflowGUI, attr_name)):
                    try:
                        original_method = getattr(workflow_gui.WorkflowGUI, attr_name)
                        # Only apply threading if the method isn't already using it
                        if 'thread' not in original_method.__code__.co_names:
                            setattr(workflow_gui.WorkflowGUI, attr_name, run_in_background(original_method))
                    except Exception:
                        pass
        
        print("Applied threading improvements")
        return True
    except Exception as e:
        print(f"Could not apply threading improvements: {str(e)}")
    return False

def fix_style_issues():
    """Fix common style and appearance issues"""
    try:
        from gui import workflow_gui
        import tkinter as tk
        from tkinter import ttk
        
        original_init = workflow_gui.WorkflowGUI.__init__
        
        def patched_init(self, *args, **kwargs):
            """Patched initialization with style fixes"""
            original_init(self, *args, **kwargs)
            
            # Configure ttk styles for better appearance
            style = ttk.Style(self.root)
            
            # Enable font scaling for high DPI displays
            self.root.tk.call('tk', 'scaling', 1.0)
            
            # Configure consistent padding for all widgets
            style.configure("TButton", padding=5)
            style.configure("TEntry", padding=5)
            style.configure("TLabel", padding=5)
            style.configure("TFrame", padding=5)
            style.configure("TLabelframe", padding=5)
            style.configure("TNotebook", padding=5)
            style.configure("TNotebook.Tab", padding=(10, 5))
            
            # Fix notebook tab appearance
            if self.notebook:
                self.notebook.config(padding=5)
            
            # Fix any scrollbar issues
            for widget in self.root.winfo_children():
                if isinstance(widget, tk.Scrollbar) or isinstance(widget, ttk.Scrollbar):
                    widget.config(width=16)  # Make scrollbars more visible
            
            # Ensure consistent font
            default_font = ('Arial', 10)
            self.root.option_add("*Font", default_font)
            
            # Update all frames to ensure correct display
            for widget in self.root.winfo_children():
                widget.update()
        
        # Apply the patched init
        workflow_gui.WorkflowGUI.__init__ = patched_init
        
        print("Applied style and appearance fixes")
        return True
    except Exception as e:
        print(f"Could not apply style and appearance fixes: {str(e)}")
    return False

def fix_refresh_issues():
    """Fix issues with GUI not refreshing properly"""
    try:
        from gui import workflow_gui
        
        # Define a method to ensure GUI refreshes
        def force_update(self):
            """Force the GUI to update"""
            try:
                self.root.update_idletasks()
                self.root.update()
            except Exception:
                pass
        
        # Add the method to the WorkflowGUI class
        workflow_gui.WorkflowGUI.force_update = force_update
        
        # Patch methods that might need forced updates
        methods_to_patch = ['on_tab_changed', 'update_ui', 'populate_fields']
        
        for method_name in methods_to_patch:
            if hasattr(workflow_gui.WorkflowGUI, method_name):
                original_method = getattr(workflow_gui.WorkflowGUI, method_name)
                
                def create_patched_method(orig):
                    def patched_method(self, *args, **kwargs):
                        result = orig(self, *args, **kwargs)
                        self.force_update()
                        return result
                    return patched_method
                
                setattr(workflow_gui.WorkflowGUI, method_name, create_patched_method(original_method))
        
        print("Applied GUI refresh fixes")
        return True
    except Exception as e:
        print(f"Could not apply GUI refresh fixes: {str(e)}")
    return False

def main():
    """Main function to run all fixes"""
    print("Starting GUI diagnostic and fix utility...")
    
    # Check tkinter functionality
    check_tkinter()
    
    # Check display server
    check_display()
    
    # Apply GUI improvements
    fixes_applied = False
    
    fixes_applied |= reduce_widget_leaks()
    fixes_applied |= optimize_gui_performance()
    fixes_applied |= improve_threading()
    fixes_applied |= fix_style_issues()
    fixes_applied |= fix_refresh_issues()
    
    if fixes_applied:
        print("\nApplied fixes to improve GUI stability and performance.")
        print("Please restart the application to see the improvements.")
    else:
        print("\nNo fixes were applied. The GUI may require more specific troubleshooting.")
    
    print("\nAdditional troubleshooting tips:")
    print("1. Try clearing any temp files in the application directory")
    print("2. Ensure you have the latest version of Python and Tkinter")
    print("3. Check for any conflicting applications using significant resources")
    print("4. On Windows WSL, ensure proper X11 forwarding is configured")
    print("5. Consider increasing the memory allocation for the application if possible")

if __name__ == "__main__":
    main()
