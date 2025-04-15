#!/usr/bin/env python3

import sys
import platform
import os
import subprocess

def print_header(text):
    print("\n" + "="*80)
    print(f" {text} ".center(80, "="))
    print("="*80 + "\n")

def check_display():
    print_header("Checking DISPLAY environment")
    display = os.environ.get('DISPLAY', 'Not set')
    print(f"DISPLAY environment variable: {display}")
    
    if display == 'Not set':
        print("ERROR: DISPLAY environment variable is not set.")
        print("This is required for GUI applications.")
        print("Try setting it with: export DISPLAY=:0")
        return False
    
    if ':' not in display:
        print("WARNING: DISPLAY variable may be incorrectly formatted.")
    
    return True

def check_tk():
    print_header("Checking Tkinter")
    try:
        import tkinter as tk
        print(f"Tkinter version: {tk.TkVersion}")
        
        # Test if we can create a root window
        try:
            root = tk.Tk()
            print("Successfully created Tk root window")
            screen_width = root.winfo_screenwidth()
            screen_height = root.winfo_screenheight()
            print(f"Screen dimensions: {screen_width}x{screen_height}")
            root.destroy()
            return True
        except tk.TclError as e:
            print(f"ERROR: Failed to create Tk root window: {e}")
            print("This usually indicates a display connection problem.")
            return False
    except ImportError:
        print("ERROR: Tkinter is not installed or not working.")
        print("Install it with: sudo apt-get install python3-tk")
        return False
    except Exception as e:
        print(f"ERROR: Unexpected Tkinter error: {e}")
        return False

def check_matplotlib():
    print_header("Checking Matplotlib")
    try:
        import matplotlib
        print(f"Matplotlib version: {matplotlib.__version__}")
        print(f"Matplotlib backend: {matplotlib.get_backend()}")
        
        try:
            # Try creating a simple plot
            import matplotlib.pyplot as plt
            fig, ax = plt.subplots()
            ax.plot([1, 2, 3], [1, 2, 3])
            plt.close(fig)
            print("Successfully created a Matplotlib figure")
            return True
        except Exception as e:
            print(f"ERROR: Failed to create Matplotlib figure: {e}")
            print("This may indicate a display or backend problem.")
            return False
    except ImportError:
        print("ERROR: Matplotlib is not installed or not working.")
        return False
    except Exception as e:
        print(f"ERROR: Unexpected Matplotlib error: {e}")
        return False

def check_xserver():
    print_header("Checking X Server")
    
    # Check if we're running on WSL
    is_wsl = "microsoft" in platform.release().lower() or os.path.exists("/proc/sys/fs/binfmt_misc/WSLInterop")
    print(f"Running on WSL: {'Yes' if is_wsl else 'No'}")
    
    if is_wsl:
        print("For GUI apps on WSL, you need an X server running on Windows.")
        print("Common X servers for Windows include VcXsrv, Xming, and X410.")
    
    # Try running a simple X11 command
    try:
        result = subprocess.run(['xdpyinfo'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("X server connection successful.")
            return True
        else:
            print("ERROR: X server connection failed.")
            print(result.stderr)
            return False
    except FileNotFoundError:
        print("ERROR: xdpyinfo command not found.")
        print("Install it with: sudo apt-get install x11-utils")
        return False
    except subprocess.TimeoutExpired:
        print("ERROR: X server connection timed out.")
        return False
    except Exception as e:
        print(f"ERROR: Unexpected error checking X server: {e}")
        return False

def check_system_info():
    print_header("System Information")
    print(f"Python version: {sys.version}")
    print(f"Platform: {platform.platform()}")
    print(f"System: {platform.system()} {platform.release()}")
    
    # Check for environment variables that might affect GUI
    env_vars = ['DISPLAY', 'WAYLAND_DISPLAY', 'XDG_SESSION_TYPE', 'LIBGL_ALWAYS_INDIRECT']
    for var in env_vars:
        print(f"{var}: {os.environ.get(var, 'Not set')}")
    
    # Check for GPU acceleration
    try:
        result = subprocess.run(['glxinfo', '-B'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("\nGPU Information:")
            lines = result.stdout.split('\n')
            for line in lines[:15]:  # Print just the first few lines
                if any(x in line.lower() for x in ['vendor', 'renderer', 'version', 'direct']):
                    print(line.strip())
        else:
            print("\nGLX information not available.")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print("\nGLX information not available.")
    except Exception as e:
        print(f"\nUnable to get GPU information: {e}")

def suggest_fixes(display_ok, tk_ok, mpl_ok, x11_ok):
    print_header("Diagnosis and Suggestions")
    
    if display_ok and tk_ok and mpl_ok and x11_ok:
        print("All basic GUI components seem to be working!")
        print("If your application still doesn't display, check for:")
        print("1. Application-specific errors")
        print("2. Firewall issues blocking X11 connections")
        print("3. Try running with: python -v MDO.py to see verbose import information")
        return
    
    print("Recommended fixes based on diagnostics:")
    
    if not display_ok:
        print("\n1. Fix DISPLAY environment variable:")
        print("   export DISPLAY=:0")
        print("   # If using VcXsrv with default settings")
        print("   # or")
        print("   export DISPLAY=$(grep -m 1 nameserver /etc/resolv.conf | awk '{print $2}'):0")
        print("   # If using the host's IP address")
    
    if not x11_ok:
        print("\n2. Install and start an X server on Windows:")
        print("   - Download and install VcXsrv: https://sourceforge.net/projects/vcxsrv/")
        print("   - Launch XLaunch and configure with 'Disable access control' checked")
        print("   - Install X11 utilities in WSL: sudo apt-get install x11-apps")
        print("   - Test with: xeyes (you should see eyes following your cursor)")
    
    if not tk_ok:
        print("\n3. Install Tkinter:")
        print("   sudo apt-get update")
        print("   sudo apt-get install -y python3-tk")
        print("   # If already installed, try reinstalling:")
        print("   sudo apt-get install --reinstall python3-tk")
    
    if not mpl_ok:
        print("\n4. Fix Matplotlib:")
        print("   pip install --upgrade matplotlib")
        print("   # If that doesn't work, try:")
        print("   pip uninstall matplotlib")
        print("   pip install matplotlib")
        print("   # Or set a different backend:")
        print("   echo 'backend: TkAgg' > ~/.matplotlib/matplotlibrc")

def main():
    print_header("GUI Diagnostics Tool for Python")
    print("This tool diagnoses issues with GUI applications in Python,")
    print("particularly in WSL (Windows Subsystem for Linux) environments.")
    
    check_system_info()
    display_ok = check_display()
    x11_ok = check_xserver()
    tk_ok = check_tk()
    mpl_ok = check_matplotlib()
    
    suggest_fixes(display_ok, tk_ok, mpl_ok, x11_ok)

if __name__ == "__main__":
    main()
