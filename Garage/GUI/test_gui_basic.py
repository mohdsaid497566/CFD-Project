#!/usr/bin/env python3
"""
Basic GUI Test Script for Intake CFD Project
This script tests the basic GUI functionality with proper patching.
"""

import os
import sys
import time
import tkinter as tk
from tkinter import ttk
import logging

# Add the current directory to the path to ensure imports work properly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    handlers=[
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
        f.write("touch output.msh\n")
    
    # Create mock cfd_solver script
    with open("./cfd_solver", "w") as f:
        f.write("#!/bin/bash\n")
        f.write("echo 'Mock CFD solver running...'\n")
        f.write("mkdir -p cfd_results\n")
        f.write("echo '0.123' > cfd_results/pressure.dat\n")
    
    # Create mock process_results script
    with open("./process_results", "w") as f:
        f.write("#!/bin/bash\n")
        f.write("echo 'Mock results processor running...'\n")
        f.write("echo '0.123' > processed_results.csv\n")
    
    # Make scripts executable
    for exe in executables:
        try:
            os.chmod(f"./{exe}", 0o755)
        except Exception as e:
            logger.warning(f"Could not set executable permissions for {exe}: {str(e)}")
    
    logger.info("Mock executables created successfully")

def test_gui_basic():
    """
    Test basic GUI functionality
    
    This function tests:
    1. GUI initialization
    2. Workflow tab functionality
    3. Theme switching
    4. Demo mode toggling
    """
    try:
        # Import MDO and set demo mode
        import MDO
        from workflow_utils import patch_workflow_gui
        
        # Set demo mode and create mock executables
        MDO.DEMO_MODE = True
        create_mock_executables()
        logger.info(f"Set MDO.DEMO_MODE to {MDO.DEMO_MODE}")
        
        # Create root window
        root = tk.Tk()
        root.title("CFD GUI Basic Test")
        root.geometry("1280x800")
        
        # Make sure to properly patch the GUI class
        WorkflowGUI = patch_workflow_gui(MDO.WorkflowGUI)
        
        # Initialize the GUI
        app = WorkflowGUI(root)
        logger.info("GUI initialized successfully")
        
        # Check critical components
        critical_components = ['notebook', 'theme_combo', 'preset_combo']
        success = True
        
        for component in critical_components:
            if hasattr(app, component):
                logger.info(f"✅ Component '{component}' found")
            else:
                logger.error(f"❌ Component '{component}' missing")
                success = False
        
        # Test switching tabs if notebook exists
        if hasattr(app, 'notebook'):
            tabs_count = app.notebook.index("end")
            logger.info(f"Found {tabs_count} tabs in the notebook")
            
            for i in range(tabs_count):
                tab_name = app.notebook.tab(i, "text")
                app.notebook.select(i)
                root.update()
                logger.info(f"Selected tab {i}: {tab_name}")
                time.sleep(0.5)
        else:
            logger.error("Notebook component not found")
            success = False
        
        # Test theme switching if available
        if hasattr(app, 'theme_combo') and hasattr(app, 'change_theme'):
            original_theme = app.theme_combo.get()
            logger.info(f"Original theme: {original_theme}")
            
            # Try different themes
            themes = app.theme_combo['values']
            if len(themes) > 0:
                for theme in themes:
                    app.theme_combo.set(theme)
                    app.change_theme()
                    root.update()
                    logger.info(f"Switched to theme: {theme}")
                    time.sleep(0.5)
                
                # Restore original theme
                app.theme_combo.set(original_theme)
                app.change_theme()
                logger.info("Restored original theme")
            else:
                logger.warning("No themes found in theme_combo")
        else:
            logger.warning("Theme switching not available")
        
        # Test workflow steps visualization if available
        if hasattr(app, '_create_workflow_steps') and hasattr(app, 'workflow_canvas'):
            app._create_workflow_steps()
            root.update()
            
            if hasattr(app, 'workflow_steps'):
                logger.info(f"Created {len(app.workflow_steps)} workflow steps")
                
                # Test updating step status if available
                if hasattr(app, '_update_step_status'):
                    app._update_step_status("Mesh", "running")
                    root.update()
                    logger.info("Updated step status to 'running'")
                    time.sleep(0.5)
                    
                    app._update_step_status("Mesh", "complete")
                    root.update()
                    logger.info("Updated step status to 'complete'")
                    time.sleep(0.5)
            else:
                logger.warning("Workflow steps not created")
        else:
            logger.warning("Workflow visualization not available")
        
        # Verify that the app has the necessary patched methods
        patched_methods = [
            'load_preset', 'reset_parameters', 'run_complete_workflow', 'change_theme',
            'run_diagnostics', 'save_settings', 'load_settings'
        ]
        
        for method in patched_methods:
            if hasattr(app, method):
                logger.info(f"✅ Method '{method}' available")
            else:
                logger.warning(f"❓ Method '{method}' not found")
        
        # Run a few seconds to let any background processes complete
        logger.info("Running GUI for a few seconds...")
        start_time = time.time()
        while time.time() - start_time < 3:
            root.update()
            time.sleep(0.1)
        
        # Summary
        if success:
            logger.info("✅ Basic GUI test completed successfully")
        else:
            logger.error("❌ Some tests failed, see log for details")
        
        return success
        
    except Exception as e:
        logger.error(f"Error during GUI test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Clean up
        try:
            root.destroy()
        except:
            pass

if __name__ == "__main__":
    success = test_gui_basic()
    sys.exit(0 if success else 1)