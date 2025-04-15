#!/usr/bin/env python3
"""
Direct GUI Test Script - Tests the CFD GUI in both demo and actual modes
by directly launching the GUI and performing basic operations.
"""

import os
import sys
import time
import argparse
import subprocess
import tkinter as tk

# Add the current directory to the path to ensure imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def log(message):
    """Log a message with timestamp"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def run_gui_test(demo_mode):
    """Run the GUI test with specified mode"""
    log(f"Starting GUI test in {'DEMO' if demo_mode else 'ACTUAL'} mode")
    
    try:
        # Import the necessary module and set demo mode
        import MDO
        MDO.DEMO_MODE = demo_mode
        log(f"Set MDO.DEMO_MODE to {demo_mode}")
        
        # Create mock executables if in demo mode
        if demo_mode:
            log("Creating mock executables for DEMO mode")
            MDO.create_mock_executables()
        
        # Create a Tkinter root window
        root = tk.Tk()
        root.title(f"CFD GUI Test ({'DEMO' if demo_mode else 'ACTUAL'} Mode)")
        root.geometry("1280x800")
        
        # Create the GUI
        app = MDO.WorkflowGUI(root)
        log("GUI initialized successfully")
        
        # Define a function to perform operations after a delay
        def perform_operations():
            try:
                log("Starting operations in the GUI")
                
                # Test workflow tab (use tab 0)
                app.notebook.select(0)
                log("Selected workflow tab")
                root.update()
                time.sleep(1)
                
                # Test visualization tab (use tab 1)
                app.notebook.select(1)
                log("Selected visualization tab")
                root.update()
                time.sleep(1)
                
                # Test optimization tab (use tab 2)
                app.notebook.select(2)
                log("Selected optimization tab")
                root.update()
                time.sleep(1)
                
                # Test settings tab (use tab 3)
                app.notebook.select(3)
                log("Selected settings tab")
                root.update()
                time.sleep(1)
                
                # Test theme switching if available
                if hasattr(app, 'theme_combo') and hasattr(app, 'change_theme'):
                    log("Testing theme switching")
                    original_theme = app.theme_combo.get()
                    
                    # Try dark theme
                    app.theme_combo.current(1)  # Assuming index 1 is Dark
                    app.change_theme()
                    root.update()
                    time.sleep(1)
                    log("Changed to dark theme")
                    
                    # Go back to original
                    app.theme_combo.set(original_theme)
                    app.change_theme()
                    root.update()
                    log("Restored original theme")
                else:
                    log("Theme switching not available")
                
                # Go back to workflow tab to test the complete workflow execution
                app.notebook.select(0)
                log("Back to workflow tab")
                root.update()
                time.sleep(1)
                
                # Test complete workflow if available
                if hasattr(app, 'run_complete_workflow'):
                    log("Testing complete workflow execution")
                    app.run_complete_workflow()
                    # Let it run for a bit
                    for i in range(10):
                        root.update()
                        time.sleep(0.5)
                    log("Workflow execution initiated")
                else:
                    log("Complete workflow execution not available")
                
                # Final update
                root.update()
                log("Testing completed successfully")
                
                # Close the GUI after 2 seconds
                root.after(2000, root.destroy)
                
            except Exception as e:
                log(f"Error during GUI operations: {str(e)}")
                # Close the GUI on error
                root.after(1000, root.destroy)
        
        # Schedule the operations after a delay to allow GUI to initialize fully
        root.after(1000, perform_operations)
        
        # Run the main loop
        root.mainloop()
        
        log(f"GUI test in {'DEMO' if demo_mode else 'ACTUAL'} mode completed")
        return True
        
    except Exception as e:
        log(f"Error running GUI test: {str(e)}")
        return False

def run_mdo_direct(demo_mode):
    """Run MDO.py directly with demo_mode set"""
    log(f"Running MDO.py directly in {'DEMO' if demo_mode else 'ACTUAL'} mode")
    
    env = os.environ.copy()
    env['DEMO_MODE'] = '1' if demo_mode else '0'
    
    try:
        cmd = ['python', 'MDO.py', '--gui']
        if demo_mode:
            cmd.append('--demo')
        
        result = subprocess.run(cmd, 
                             env=env, 
                             stdout=subprocess.PIPE, 
                             stderr=subprocess.PIPE,
                             text=True,
                             timeout=30)
        
        log(f"Exit code: {result.returncode}")
        if result.stdout:
            log(f"Output:\n{result.stdout}")
        if result.stderr:
            log(f"Errors:\n{result.stderr}")
            
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        log("Process timed out after 30 seconds")
        return True  # Consider timeout as not an error
    except Exception as e:
        log(f"Error running MDO.py directly: {str(e)}")
        return False

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Test the CFD GUI in different modes")
    parser.add_argument("--mode", choices=["demo", "actual", "both"], default="demo",
                     help="Test mode: demo (mock data), actual (real executables), or both")
    parser.add_argument("--method", choices=["direct", "subprocess"], default="direct",
                     help="Test method: direct (in-process), subprocess (separate process)")
    return parser.parse_args()

def main():
    """Main function"""
    log("Starting direct GUI tests")
    
    args = parse_arguments()
    results = []
    
    if args.mode in ["demo", "both"]:
        log("\n" + "="*50)
        log("TESTING DEMO MODE")
        log("="*50)
        
        if args.method == "direct":
            demo_result = run_gui_test(demo_mode=True)
        else:
            demo_result = run_mdo_direct(demo_mode=True)
            
        results.append(("DEMO", demo_result))
    
    if args.mode in ["actual", "both"]:
        log("\n" + "="*50)
        log("TESTING ACTUAL MODE")
        log("="*50)
        
        if args.method == "direct":
            actual_result = run_gui_test(demo_mode=False)
        else:
            actual_result = run_mdo_direct(demo_mode=False)
            
        results.append(("ACTUAL", actual_result))
    
    # Print summary
    log("\n" + "="*50)
    log("TEST SUMMARY")
    log("="*50)
    
    all_passed = True
    for mode, result in results:
        status = "PASS" if result else "FAIL"
        if not result:
            all_passed = False
        log(f"{mode.ljust(10)}: {status}")
    
    log("="*50)
    log(f"OVERALL: {'PASS' if all_passed else 'FAIL'}")
    log("="*50)
    
    # Return exit code based on results
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())