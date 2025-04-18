#!/usr/bin/env python3
"""
Diagnostic script to check environment and dependencies for Intake CFD GUI.
Run this script to diagnose issues before launching the main application.
"""
import os
import sys
import platform
import traceback

def check_environment():
    """Check the system environment and Python configuration"""
    print("=" * 50)
    print("ENVIRONMENT DIAGNOSTICS")
    print("=" * 50)
    print(f"Python version: {platform.python_version()}")
    print(f"Platform: {platform.platform()}")
    print(f"System: {platform.system()} {platform.release()}")
    
    # Check WSL
    is_wsl = False
    if platform.system() == "Linux":
        if "microsoft" in platform.release().lower():
            is_wsl = True
        try:
            with open("/proc/version", "r") as f:
                if "microsoft" in f.read().lower():
                    is_wsl = True
        except:
            pass
        if os.path.exists("/proc/sys/fs/binfmt_misc/WSLInterop"):
            is_wsl = True
        if "wsl" in os.environ.get("WSL_DISTRO_NAME", "").lower():
            is_wsl = True
        if os.path.exists("/mnt/c/Windows"):
            is_wsl = True
    print(f"Running in WSL: {is_wsl}")
    
    # Check working directory structure
    print(f"Current working directory: {os.getcwd()}")
    print("\nDirectory contents:")
    try:
        for item in os.listdir('.'):
            print(f"  - {item}")
    except Exception as e:
        print(f"  Error listing directory: {e}")
    
    # Check parent directory in path
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print(f"\nParent directory: {parent_dir}")
    print(f"Parent in sys.path: {parent_dir in sys.path}")
    
    # Check Python path
    print("\nPYTHONPATH:")
    python_path = os.environ.get('PYTHONPATH', '')
    if python_path:
        for path in python_path.split(os.pathsep):
            print(f"  - {path}")
    else:
        print("  [Not set]")
    
    print("\nsys.path:")
    for path in sys.path:
        print(f"  - {path}")

def check_dependencies():
    """Check for required dependencies"""
    print("\n" + "=" * 50)
    print("DEPENDENCY DIAGNOSTICS")
    print("=" * 50)
    
    dependencies = [
        "tkinter", "matplotlib", "numpy", "pandas", 
        "PIL", "json", "subprocess"
    ]
    
    for dep in dependencies:
        try:
            if dep == "tkinter":
                import tkinter as tk
                print(f"✓ {dep} (version {tk.TkVersion})")
            elif dep == "matplotlib":
                import matplotlib
                print(f"✓ {dep} (version {matplotlib.__version__})")
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
                __import__(dep)
                print(f"✓ {dep}")
        except ImportError:
            print(f"✗ {dep} - NOT FOUND")
        except Exception as e:
            print(f"✗ {dep} - ERROR: {str(e)}")

def check_project_modules():
    """Check project-specific modules"""
    print("\n" + "=" * 50)
    print("PROJECT MODULE DIAGNOSTICS")
    print("=" * 50)
    
    # Add parent directory to path if not already there
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if parent_dir not in sys.path:
        sys.path.append(parent_dir)
    
    modules = [
        "Expressions",
        "Utils.workflow_utils",
        "GUI.fix_hpc_gui"
    ]
    
    for module in modules:
        try:
            __import__(module)
            print(f"✓ {module} - Successfully imported")
        except ImportError as e:
            print(f"✗ {module} - NOT FOUND: {str(e)}")
        except Exception as e:
            print(f"✗ {module} - ERROR: {str(e)}")
    
    # Check if main.py can be imported
    try:
        import main
        print("✓ main.py - Successfully imported")
        if hasattr(main, "WorkflowGUI"):
            print("  ✓ WorkflowGUI class found in main.py")
        else:
            print("  ✗ WorkflowGUI class not found in main.py")
    except Exception as e:
        print(f"✗ main.py - ERROR: {str(e)}")

def run_diagnostics():
    """Run all diagnostic checks"""
    try:
        check_environment()
        check_dependencies()
        check_project_modules()
        
        print("\n" + "=" * 50)
        print("GUI TEST")
        print("=" * 50)
        
        try:
            import tkinter as tk
            root = tk.Tk()
            root.title("GUI Test")
            tk.Label(root, text="If you can see this window, basic GUI functionality is working").pack(padx=20, pady=20)
            tk.Button(root, text="Close", command=root.destroy).pack(pady=10)
            print("✓ Basic Tkinter window created successfully")
            print("  Close the test window to continue...")
            root.mainloop()
        except Exception as e:
            print(f"✗ Failed to create test window: {str(e)}")
        
        print("\n" + "=" * 50)
        print("DIAGNOSTICS COMPLETE")
        print("=" * 50)
        
    except Exception as e:
        print(f"\nERROR during diagnostics: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    run_diagnostics()
