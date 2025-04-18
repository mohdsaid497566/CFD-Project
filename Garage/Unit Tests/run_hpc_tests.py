#!/usr/bin/env python3

import os
import sys
import subprocess
import argparse
import glob

def find_test_files(test_dir, pattern="test_hpc_*.py"):
    """Find all test files matching the pattern in the test directory."""
    return glob.glob(os.path.join(test_dir, pattern))

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run HPC tests")
    parser.add_argument("--test", "-t", help="Specific test file to run (without path)")
    parser.add_argument("--pattern", "-p", default="test_hpc_*.py", 
                        help="Pattern to match test files (default: test_hpc_*.py)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Increase verbosity")
    parser.add_argument("--fix-imports", "-f", action="store_true", 
                        help="Create missing module stubs for tests to run")
    args = parser.parse_args()
    
    # Get the project root directory
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    test_dir = os.path.join(project_dir, 'Unit Tests')
    
    # Add both the project directory AND the test directory to PYTHONPATH
    env = os.environ.copy()
    python_paths = [project_dir, test_dir]
    
    if 'PYTHONPATH' in env:
        python_paths.append(env['PYTHONPATH'])
    
    # Use proper path separator based on OS
    path_separator = ';' if sys.platform.startswith('win') else ':'
    env['PYTHONPATH'] = path_separator.join(python_paths)
    
    # Check for workflow_utils.py in the test directory
    workflow_utils_path = os.path.join(test_dir, "workflow_utils.py")
    if not os.path.exists(workflow_utils_path) and args.fix_imports:
        print(f"Creating stub workflow_utils.py file...")
        with open(workflow_utils_path, 'w') as f:
            f.write("""# Auto-generated stub for workflow_utils
print("workflow_utils.py loaded (stub).")

def patch_workflow_gui(*args, **kwargs):
    print("Using stub patch_workflow_gui function")
    return None
""")
        print(f"Created stub workflow_utils.py in {test_dir}")
    
    # Check for hpc_connector folder and create stub if needed
    hpc_connector_dir = os.path.join(project_dir, "hpc_connector")
    hpc_connector_init = os.path.join(hpc_connector_dir, "__init__.py")
    if args.fix_imports and not os.path.exists(hpc_connector_dir):
        os.makedirs(hpc_connector_dir, exist_ok=True)
        with open(hpc_connector_init, 'w') as f:
            f.write("""# Auto-generated stub for hpc_connector
print("Using stub hpc_connector module.")
""")
        print(f"Created stub hpc_connector module in {project_dir}")
    
    # Determine which test files to run
    if args.test:
        test_files = [os.path.join(test_dir, args.test)]
        if not os.path.exists(test_files[0]):
            print(f"Error: Test file {args.test} not found")
            return 1
    else:
        test_files = find_test_files(test_dir, args.pattern)
        if not test_files:
            print(f"No test files found matching pattern '{args.pattern}'")
            return 1
    
    if args.verbose:
        print(f"Found {len(test_files)} test files to run:")
        for test_file in test_files:
            print(f"  - {os.path.basename(test_file)}")
        print(f"PYTHONPATH set to: {env['PYTHONPATH']}")
    
    # Run each test file
    return_code = 0
    for test_file in test_files:
        if args.verbose or True:  # Always show which file is running
            print(f"\nRunning {os.path.basename(test_file)}...")
        
        cmd = [sys.executable, test_file]  # Use sys.executable for reliability
        if args.verbose:
            cmd.append('-v')
            
        try:
            result = subprocess.run(cmd, env=env)
            if result.returncode != 0:
                return_code = result.returncode
                print(f"Test {os.path.basename(test_file)} failed with code {result.returncode}")
            elif args.verbose:
                print(f"Test {os.path.basename(test_file)} passed!")
        except Exception as e:
            print(f"Error running {os.path.basename(test_file)}: {str(e)}")
            return_code = 1
    
    if args.verbose:
        if return_code == 0:
            print("\nAll tests completed successfully!")
        else:
            print(f"\nSome tests failed with return code {return_code}")
    
    return return_code

if __name__ == "__main__":
    sys.exit(main())
