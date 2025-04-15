import os
import sys
import tkinter as tk

def launch_gui():
    """
    Launcher for the CFD Workflow GUI
    """
    try:
        # Import necessary modules
        try:
            import NXOpen
            import NXOpen.UI
            nx_available = True
        except ImportError:
            nx_available = False
            print("Warning: NXOpen modules not available - running in standalone mode")
        
        # Import the patch module
        import patch
        
        # Create a basic WorkflowGUI class for testing if MDO module isn't available
        class TestWorkflowGUI:
            def __init__(self, root=None):
                self.root = root
                print("TestWorkflowGUI initialized")
        
        # Create a root window
        root = tk.Tk()
        root.title("CFD Workflow Assistant")
        root.geometry("900x700")
        
        # Patch the test class
        PatchedGUI = patch.patch_workflow_gui(TestWorkflowGUI)
        
        # Create an instance to show the GUI
        gui = PatchedGUI(root)
        
        # Show the GUI
        if hasattr(gui, 'safe_show_gui'):
            gui.safe_show_gui()
        else:
            root.mainloop()
        
        print("GUI launched successfully")
        return True
        
    except ImportError as e:
        print(f"Error importing required modules: {str(e)}")
        if "NXOpen" in str(e):
            print("This script is running outside of NX - using standalone mode")
            # Re-try without NX dependencies
            return launch_gui_standalone()
        return False
    except Exception as e:
        print(f"Error launching GUI: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def launch_gui_standalone():
    """Fallback launcher that doesn't require NX"""
    try:
        import patch
        import tkinter as tk
        
        root = tk.Tk()
        root.title("CFD Workflow Assistant (Standalone)")
        root.geometry("900x700")
        
        # Create basic standalone GUI
        class StandaloneGUI:
            def __init__(self, root):
                self.root = root
                self.initialized = True
                print("Standalone GUI initialized")
        
        # Patch and create
        PatchedGUI = patch.patch_workflow_gui(StandaloneGUI)
        gui = PatchedGUI(root)
        
        # Show
        root.mainloop()
        return True
    except Exception as e:
        print(f"Error launching standalone GUI: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = launch_gui()
    if not success:
        print("Failed to launch GUI. See error messages above.")
