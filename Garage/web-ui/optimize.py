"""
This script checks for performance issues in the web UI.
Run with: python optimize.py
"""
import os
import time
import sys
import datetime

# Try to import requests, but provide a fallback if not available
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("WARNING: 'requests' module not found. Limited diagnostics available.")
    print("To install: pip install requests")

def check_flask_performance():
    """Checks the Flask server response time"""
    print("Testing Flask server response time...")
    
    if not REQUESTS_AVAILABLE:
        print("Skipping Flask server check (requests module not available)")
        return False
    
    try:
        start_time = time.time()
        response = requests.get('http://127.0.0.1:5000/debug')
        end_time = time.time()
        
        if response.status_code == 200:
            print(f"Server is responsive. Response time: {end_time - start_time:.3f} seconds")
            print(f"Server time: {response.json().get('time')}")
            return True
        else:
            print(f"Server responded with status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"Cannot connect to the Flask server: {str(e)}")
        return False

def check_wsl_io_performance():
    """Checks WSL I/O performance which can affect Flask in WSL"""
    print("\nTesting WSL I/O performance...")
    
    # Create a test file and measure write speed
    test_file = "test_performance.tmp"
    size_mb = 10
    
    try:
        # Write test
        data = b'0' * (1024 * 1024)  # 1MB data
        start_time = time.time()
        
        with open(test_file, 'wb') as f:
            for _ in range(size_mb):
                f.write(data)
        
        write_time = time.time() - start_time
        
        # Read test
        start_time = time.time()
        with open(test_file, 'rb') as f:
            while f.read(1024 * 1024):
                pass
        
        read_time = time.time() - start_time
        
        print(f"Write speed: {size_mb / write_time:.2f} MB/s")
        print(f"Read speed: {size_mb / read_time:.2f} MB/s")
        
        if size_mb / write_time < 10 or size_mb / read_time < 10:
            print("\nWARNING: WSL I/O performance appears to be slow.")
            print("This may cause Flask to load slowly. Consider these optimizations:")
            print("1. Ensure your project files are on the Linux filesystem, not on Windows drives")
            print("2. Try using WSL 2 instead of WSL 1")
            print("3. Add 'threaded=True' to app.run() in app.py")
        
        # Clean up
        os.remove(test_file)
    except Exception as e:
        print(f"Error during I/O test: {e}")

def check_dependencies():
    """Check if required dependencies are installed"""
    print("\nChecking required dependencies...")
    
    dependencies = {
        "flask": "Web framework",
        "numpy": "Numerical computations",
        "matplotlib": "Plotting library",
        "requests": "HTTP requests (for diagnostics)",
    }
    
    missing = []
    
    for dep, desc in dependencies.items():
        try:
            __import__(dep)
            print(f"✓ {dep}: Installed")
        except ImportError:
            print(f"✗ {dep}: Missing - {desc}")
            missing.append(dep)
    
    if missing:
        print("\nInstall missing dependencies with:")
        print(f"pip install {' '.join(missing)}")
        return False
    
    return True

def suggest_optimizations():
    """Suggests optimizations for Flask in WSL"""
    print("\nSuggested optimizations:")
    print("1. Make sure app.py has the following line:")
    print("   app.run(debug=True, threaded=True, host='0.0.0.0')")
    print("2. Use a production WSGI server instead of Flask's built-in server:")
    print("   pip install gunicorn")
    print("   gunicorn -w 4 -b 0.0.0.0:5000 app:app")
    print("3. Simplify templates and static files to reduce loading time")
    print("4. Use Flask caching to improve performance:")
    print("   pip install Flask-Caching")

if __name__ == "__main__":
    print("Web UI Performance Diagnostics")
    print("==============================")
    print(f"Current time: {datetime.datetime.now()}")
    
    check_dependencies()
    check_wsl_io_performance()
    
    if REQUESTS_AVAILABLE:
        flask_ok = check_flask_performance()
    
    suggest_optimizations()
    
    print("\nDiagnostics complete.")
