#!/usr/bin/env python3
"""
Enhanced diagnostic script for Intake CFD GUI.
Provides more comprehensive testing and troubleshooting suggestions.
"""
import os
import sys
import platform
import traceback
import importlib
import subprocess
import time

def print_header(title):
    """Print a formatted section header"""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)

def check_environment():
    """Check system environment with enhanced details"""
    print_header("ENVIRONMENT DIAGNOSTICS")
    
    # Basic system info
    print(f"Python version: {platform.python_version()}")
    print(f"Python executable: {sys.executable}")
    print(f"Platform: {platform.platform()}")
    print(f"System: {platform.system()} {platform.release()}")
    print(f"Architecture: {platform.machine()}")
    
    # WSL detection (enhanced)
    is_wsl = False
    wsl_details = []
    
    if platform.system() == "Linux":
        if "microsoft" in platform.release().lower():
            is_wsl = True
            wsl_details.append("'microsoft' found in platform.release()")
            
        try:
            with open("/proc/version", "r") as f:
                proc_version = f.read().lower()
                if "microsoft" in proc_version:
                    is_wsl = True
                    wsl_details.append("'microsoft' found in /proc/version")
                    if "wsl2" in proc_version:
                        wsl_details.append("WSL2 detected in /proc/version")
                    elif "wsl" in proc_version:
                        wsl_details.append("WSL1 detected in /proc/version")
        except:
            pass
            
        if os.path.exists("/proc/sys/fs/binfmt_misc/WSLInterop"):
            is_wsl = True
            wsl_details.append("WSLInterop found in /proc/sys/fs/binfmt_misc")
            
        if "wsl" in os.environ.get("WSL_DISTRO_NAME", "").lower():
            is_wsl = True
            wsl_details.append(f"WSL_DISTRO_NAME is {os.environ.get('WSL_DISTRO_NAME')}")
            
        if os.path.exists("/mnt/c/Windows"):
            is_wsl = True
            wsl_details.append("Windows mount found at /mnt/c/Windows")
    
    print(f"Running in WSL: {is_wsl}")
    if wsl_details:
        print("WSL detection details:")
        for detail in wsl_details:
            print(f"  - {detail}")
    
    # Display environment variables
    print("\nRelevant Environment Variables:")
    for var in ["DISPLAY", "PYTHONPATH", "GARAGE_DEMO_MODE", "HOME", "PATH"]:
        print(f"  {var} = {os.environ.get(var, '[not set]')}")
    
    # Check working directory and permissions
    cwd = os.getcwd()
    print(f"\nCurrent working directory: {cwd}")
    try:
        print(f"  Readable: {os.access(cwd, os.R_OK)}")
        print(f"  Writable: {os.access(cwd, os.W_OK)}")
        print(f"  Executable: {os.access(cwd, os.X_OK)}")
    except Exception as e:
        print(f"  Error checking directory permissions: {e}")
    
    # Check directory contents (top level only)
    print("\nDirectory contents:")
    try:
        for item in sorted(os.listdir('.')):
            try:
                item_type = "DIR " if os.path.isdir(item) else "FILE"
                exec_mark = "*" if os.access(item, os.X_OK) else " "
                print(f"  {item_type}{exec_mark} {item}")
            except:
                print(f"  ???? {item} (error getting info)")
    except Exception as e:
        print(f"  Error listing directory: {e}")
    
    # Check Python path in more detail
    print("\nPython path details:")
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print(f"Parent directory: {parent_dir}")
    print(f"Parent in sys.path: {parent_dir in sys.path}")
    
    site_packages = None
    for path in sys.path:
        if "site-packages" in path:
            site_packages = path
            break
    print(f"Site-packages: {site_packages}")
    
    # Show load path order
    print("\nModule load path (order matters!):")
    for i, path in enumerate(sys.path):
        print(f"  {i+1}: {path}")

def check_dependencies():
    """Check for required dependencies with enhanced details"""
    print_header("DEPENDENCY DIAGNOSTICS")
    
    # Core dependencies that stop the app from running if missing
    core_deps = [
        "tkinter", "matplotlib", "numpy", "pandas", "PIL"
    ]
    
    # Extended dependencies that are needed for full functionality
    extended_deps = [
        "json", "subprocess", "threading", "traceback", "shutil", 
        "argparse", "logging", "time"
    ]
    
    # Try to import the core dependencies
    missing_core = []
    print("Core dependencies:")
    for dep in core_deps:
        try:
            if dep == "tkinter":
                import tkinter as tk
                print(f"✓ {dep} (version {tk.TkVersion})")
                # Try to create a simple window to test if tkinter works
                try:
                    root = tk.Tk()
                    root.withdraw()
                    root.update()
                    root.destroy()
                    print(f"  ✓ Created test Tk window successfully")
                except Exception as e:
                    print(f"  ✗ Failed to create Tk window: {e}")
            elif dep == "matplotlib":
                import matplotlib
                print(f"✓ {dep} (version {matplotlib.__version__})")
                try:
                    # Test backend
                    import matplotlib.pyplot as plt
                    print(f"  ✓ Matplotlib backend: {matplotlib.get_backend()}")
                except Exception as e:
                    print(f"  ✗ Error testing matplotlib backend: {e}")
            elif dep == "numpy":
                import numpy as np
                print(f"✓ {dep} (version {np.__version__})")
            elif dep == "pandas":
                import pandas as pd
                print(f"✓ {dep} (version {pd.__version__})")
            elif dep == "PIL":
                from PIL import Image, ImageTk
                import PIL
                print(f"✓ {dep} (version {PIL.__version__})")
            else:
                mod = __import__(dep)
                version = getattr(mod, "__version__", "unknown")
                print(f"✓ {dep} (version {version})")
        except ImportError as e:
            print(f"✗ {dep} - NOT FOUND: {e}")
            missing_core.append(dep)
        except Exception as e:
            print(f"✗ {dep} - ERROR: {str(e)}")
            missing_core.append(dep)
    
    print("\nExtended dependencies:")
    for dep in extended_deps:
        try:
            __import__(dep)
            print(f"✓ {dep}")
        except ImportError:
            print(f"✗ {dep} - NOT FOUND")
        except Exception as e:
            print(f"✗ {dep} - ERROR: {str(e)}")
    
    # Report critical missing dependencies
    if missing_core:
        print("\n⚠️ Missing critical dependencies!")
        print("   The following core dependencies must be installed:")
        for dep in missing_core:
            print(f"   - {dep}")
        print("\n   You can install them using pip:")
        print(f"   pip install {' '.join(missing_core)}")
    else:
        print("\n✓ All core dependencies are available.")

def check_project_modules():
    """Check project-specific modules with enhanced details"""
    print_header("PROJECT MODULE DIAGNOSTICS")
    
    # Add parent directory to path if not already there
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if parent_dir not in sys.path:
        sys.path.append(parent_dir)
        print(f"Added {parent_dir} to sys.path for testing")
    
    # Add current directory to path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
        print(f"Added {current_dir} to sys.path for testing")
    
    # Core modules
    print("Core project modules:")
    modules = [
        "Expressions",
        "Utils.workflow_utils",
        "GUI.fix_hpc_gui",
        "main"
    ]
    
    for module_name in modules:
        try:
            module = importlib.import_module(module_name)
            print(f"✓ {module_name} - Successfully imported")
            
            # Check specific attributes or features
            if module_name == "main":
                if hasattr(module, "WorkflowGUI"):
                    print(f"  ✓ WorkflowGUI class found in {module_name}")
                else:
                    print(f"  ✗ WorkflowGUI class not found in {module_name}")
                
                if hasattr(module, "main"):
                    print(f"  ✓ main() function found in {module_name}")
                else:
                    print(f"  ✗ main() function not found in {module_name}")
            
            if module_name == "Utils.workflow_utils":
                if hasattr(module, "patch_workflow_gui"):
                    print(f"  ✓ patch_workflow_gui() found in {module_name}")
                else:
                    print(f"  ✗ patch_workflow_gui() not found in {module_name}")
        except ImportError as e:
            print(f"✗ {module_name} - NOT FOUND: {str(e)}")
        except Exception as e:
            print(f"✗ {module_name} - ERROR: {str(e)}")
            print(f"  Traceback: {traceback.format_exc().splitlines()[-3]}")
    
    # Test importing WorkflowGUI directly
    try:
        from main import WorkflowGUI
        print("✓ Successfully imported WorkflowGUI from main")
    except ImportError as e:
        print(f"✗ Failed to import WorkflowGUI from main: {e}")
    except Exception as e:
        print(f"✗ Error importing WorkflowGUI from main: {e}")

def perform_gui_test():
    """Perform a basic GUI functionality test"""
    print_header("GUI TEST")
    
    try:
        import tkinter as tk
        print("Creating test window...")
        root = tk.Tk()
        root.title("Intake CFD GUI Test")
        root.geometry("400x200")
        
        # Add a label with instructions
        tk.Label(root, text="If you can see this window, basic GUI functionality is working.",
                pady=20, padx=20).pack()
        
        # Add a label to show if we're in WSL
        is_wsl = False
        if platform.system() == "Linux" and ("microsoft" in platform.release().lower() or 
                                           os.path.exists("/mnt/c/Windows")):
            is_wsl = True
        
        wsl_text = "Running in WSL: Yes" if is_wsl else "Running in WSL: No"
        tk.Label(root, text=wsl_text).pack()
        
        # Add close button
        tk.Button(root, text="Close", command=root.destroy).pack(pady=20)
        
        print("✓ Test window created successfully")
        print("  Close the test window to continue...")
        
        # Set a timeout to close the window automatically
        root.after(30000, root.destroy)  # Close after 30 seconds
        
        # Main loop
        root.mainloop()
        print("✓ GUI test completed successfully")
        return True
    except Exception as e:
        print(f"✗ Failed to create test window: {str(e)}")
        print(traceback.format_exc())
        return False

def test_display_connection():
    """Test display server connection (particularly important for WSL)"""
    print_header("DISPLAY CONNECTION TEST")
    
    # Check if we're in WSL
    is_wsl = False
    if platform.system() == "Linux" and ("microsoft" in platform.release().lower() or 
                                       os.path.exists("/mnt/c/Windows")):
        is_wsl = True
    
    if not is_wsl:
        print("Not running in WSL, skipping WSL-specific display tests.")
        return
    
    # Check DISPLAY environment variable
    display_var = os.environ.get("DISPLAY", "")
    print(f"DISPLAY environment variable: {display_var}")
    
    if not display_var:
        print("⚠️ DISPLAY environment variable is not set!")
        print("  This is required for GUI applications in WSL.")
        print("  Try setting it with: export DISPLAY=:0")
        return
    
    # Try to run a simple X11 command to check connectivity
    try:
        print("Testing X11 connection with xset command...")
        result = subprocess.run(["xset", "q"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print("✓ X11 connection successful!")
    except FileNotFoundError:
        print("✗ 'xset' command not found. X11 utilities may not be installed.")
        print("  Try installing them with: sudo apt-get install x11-xserver-utils")
    except Exception as e:
        print(f"✗ X11 connection test failed: {e}")
        print(f"  This may indicate that no X server is running or accessible.")
        print(f"  If using WSL, make sure an X server (like VcXsrv) is running on Windows.")
    
    # Additional WSL-specific advice
    print("\nWSL GUI Application Tips:")
    print("1. Make sure an X server like VcXsrv or Xming is installed and running on Windows")
    print("2. Configure the X server to allow connections from network clients")
    print("3. Set the DISPLAY variable correctly (export DISPLAY=:0 or similar)")
    print("4. For WSL2, you may need to allow WSL to access the Windows X server through the firewall")

def run_minimal_app_test():
    """Try to run a minimal version of the application"""
    print_header("MINIMAL APPLICATION TEST")
    
    try:
        import tkinter as tk
        from tkinter import ttk
        import importlib
        
        # Create a basic window
        root = tk.Tk()
        root.title("Minimal CFD App Test")
        root.geometry("600x400")
        
        # Add some content
        frame = ttk.Frame(root, padding=20)
        frame.pack(fill='both', expand=True)
        
        ttk.Label(frame, text="Minimal Intake CFD App", font=("Arial", 16)).pack(pady=20)
        
        # Try to import the main module and report status
        status_text = tk.StringVar(value="Testing imports...")
        ttk.Label(frame, textvariable=status_text).pack(pady=10)
        
        # Progress bar
        progress = ttk.Progressbar(frame, mode='indeterminate')
        progress.pack(fill='x', pady=10)
        progress.start()
        
        def test_imports():
            """Test importing the main components"""
            results = []
            try:
                import main
                results.append("✓ Imported main module")
                
                if hasattr(main, "WorkflowGUI"):
                    results.append("✓ Found WorkflowGUI class")
                else:
                    results.append("✗ WorkflowGUI class not found")
                    
                # Try importing other key modules
                try:
                    import Expressions
                    results.append("✓ Imported Expressions module")
                except Exception as e:
                    results.append(f"✗ Failed to import Expressions: {e}")
                
                try:
                    from Utils import workflow_utils
                    results.append("✓ Imported workflow_utils module")
                except Exception as e:
                    results.append(f"✗ Failed to import workflow_utils: {e}")
                
            except Exception as e:
                results.append(f"✗ Failed to import main: {e}")
            
            # Update the UI with results
            status_text.set("\n".join(results))
            progress.stop()
            
            # Add close button after tests
            ttk.Button(frame, text="Close", command=root.destroy).pack(pady=20)
        
        # Schedule import test after window appears
        root.after(500, test_imports)
        
        print("Running minimal application test...")
        print("Close the window to continue diagnostics.")
        root.mainloop()
        
    except Exception as e:
        print(f"Error during minimal app test: {str(e)}")
        print(traceback.format_exc())

def suggest_fixes():
    """Provide suggestions based on diagnostic results"""
    print_header("SUGGESTED FIXES")
    
    # WSL-specific fixes
    is_wsl = False
    if platform.system() == "Linux" and ("microsoft" in platform.release().lower() or 
                                       os.path.exists("/mnt/c/Windows")):
        is_wsl = True
    
    if is_wsl:
        print("WSL Environment Fixes:")
        print("1. Set up the DISPLAY environment variable:")
        print("   export DISPLAY=:0")
        print("   # Add this line to your ~/.bashrc file to make it permanent")
        print("\n2. Install X server software on Windows (if not already installed):")
        print("   - VcXsrv: https://sourceforge.net/projects/vcxsrv/")
        print("   - Configure VcXsrv to allow public access and disable access control")
        print("\n3. Install required X11 packages in WSL:")
        print("   sudo apt-get update")
        print("   sudo apt-get install libx11-dev libxext-dev libxrender-dev libxinerama-dev libxi-dev libxrandr-dev libxcursor-dev")
    
    # Python environment fixes
    print("\nPython Environment Fixes:")
    print("1. Make sure all dependencies are installed:")
    print("   pip install numpy pandas matplotlib pillow")
    
    # Script execution fixes
    print("\nScript Execution Fixes:")
    print("1. Make the script executable:")
    print("   chmod +x main.py")
    print("\n2. Use the enhanced launcher for better error reporting:")
    print("   python run_gui.py")
    
    # Path fixes
    print("\nPath Fixes:")
    print("1. Make sure the parent directory is in your Python path:")
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print(f"   export PYTHONPATH={parent_dir}:$PYTHONPATH")
    
    # Display an overall recommendation
    print("\nRecommended Troubleshooting Steps:")
    print("1. Use the new launcher script: python run_gui.py")
    print("2. Check the console output for specific error messages")
    print("3. If you're using WSL, ensure X server is properly configured")
    print("4. Verify all dependencies are installed with: pip list")

def run_diagnostics():
    """Run all diagnostic checks"""
    try:
        print("Starting Intake CFD GUI diagnostics...")
        print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        check_environment()
        check_dependencies()
        check_project_modules()
        test_display_connection()
        gui_test_result = perform_gui_test()
        
        if gui_test_result:
            run_minimal_app_test()
            
        suggest_fixes()
        
        print_header("DIAGNOSTICS COMPLETE")
        print("See above for suggested fixes and troubleshooting steps.")
        
    except Exception as e:
        print(f"\nERROR during diagnostics: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    run_diagnostics()
