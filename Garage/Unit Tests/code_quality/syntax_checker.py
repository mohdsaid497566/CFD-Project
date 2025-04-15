#!/usr/bin/env python3
"""
Syntax checker for Python files in the project
"""

import os
import sys
import ast
import importlib
import importlib.util
import argparse
import logging
import pylint.lint
from pylint.reporters.text import TextReporter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("SyntaxChecker")

class OutputCollector:
    """Collect output from pylint"""
    def __init__(self):
        self.content = []
        
    def write(self, text):
        self.content.append(text)
        
    def read(self):
        return "".join(self.content)

def check_syntax(file_path):
    """Check Python file syntax using ast.parse"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source_code = f.read()
        
        ast.parse(source_code, filename=file_path)
        logger.info(f"✅ Syntax check passed for {file_path}")
        return True
    except SyntaxError as e:
        logger.error(f"❌ Syntax error in {file_path}: {str(e)} at line {e.lineno}, column {e.offset}")
        logger.error(f"   {e.text}")
        logger.error(f"   {' ' * (e.offset - 1)}^")
        return False
    except Exception as e:
        logger.error(f"❌ Error checking syntax in {file_path}: {str(e)}")
        return False

def run_pylint(file_path):
    """Run pylint on the file to check for issues"""
    logger.info(f"Running pylint on {file_path}")
    
    output = OutputCollector()
    reporter = TextReporter(output)
    
    # Configure pylint args
    args = [
        "--disable=C0111",  # Missing docstring
        "--disable=C0103",  # Invalid name
        "--disable=C0303",  # Trailing whitespace
        "--disable=W0613",  # Unused argument
        "--disable=W0612",  # Unused variable
        "--disable=R0903",  # Too few public methods
        file_path
    ]
    
    # Run pylint
    pylint.lint.Run(args, reporter=reporter, exit=False)
    
    # Get the output
    lint_output = output.read()
    
    # Log only if there are warnings or errors
    if "Your code has been rated at 10.00/10" not in lint_output:
        logger.info("Pylint found issues:")
        for line in lint_output.split('\n'):
            if line.strip():
                logger.info(f"  {line}")
    else:
        logger.info("✅ Pylint found no issues")
    
    return lint_output

def check_imports(file_path):
    """Check if all imported modules can be imported"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source_code = f.read()
        
        # Parse the AST
        tree = ast.parse(source_code, filename=file_path)
        
        # Find all import statements
        issues = []
        import_nodes = [node for node in ast.walk(tree) 
                      if isinstance(node, (ast.Import, ast.ImportFrom))]
        
        # Check each import
        for node in import_nodes:
            if isinstance(node, ast.Import):
                for name in node.names:
                    module_name = name.name
                    try:
                        # Try to import the module to check if it's available
                        importlib.import_module(module_name)
                    except ImportError as e:
                        issues.append((module_name, str(e), node.lineno))
            elif isinstance(node, ast.ImportFrom):
                module_name = node.module
                if module_name:  # Could be None for "from . import x"
                    for name in node.names:
                        full_name = f"{module_name}.{name.name}"
                        try:
                            # Try to import the module or attribute
                            if module_name == "__future__":
                                continue  # Skip __future__ imports
                            importlib.import_module(module_name)
                        except ImportError as e:
                            issues.append((full_name, str(e), node.lineno))
        
        if issues:
            logger.warning(f"⚠️ Import issues in {file_path}:")
            for module, error, lineno in issues:
                logger.warning(f"  Line {lineno}: Could not import '{module}': {error}")
            return False
        
        logger.info(f"✅ All imports available in {file_path}")
        return True
    except Exception as e:
        logger.error(f"❌ Error checking imports in {file_path}: {str(e)}")
        return False

def check_file(file_path):
    """Run all checks on a single file"""
    logger.info(f"\nChecking file: {file_path}")
    
    # Check syntax first
    if not check_syntax(file_path):
        logger.error(f"Skipping further checks for {file_path} due to syntax errors")
        return False
    
    # Check imports
    imports_ok = check_imports(file_path)
    
    # Run pylint
    pylint_output = run_pylint(file_path)
    
    logger.info(f"Completed checking {file_path}")
    return imports_ok and "Your code has been rated at 10.00/10" in pylint_output

def scan_directory(directory, exclude_dirs=None):
    """Recursively scan a directory for Python files and check them"""
    if exclude_dirs is None:
        exclude_dirs = ["__pycache__", ".git", "venv", "env", "node_modules"]
    
    all_ok = True
    
    for root, dirs, files in os.walk(directory):
        # Filter out excluded directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        # Check Python files
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                if not check_file(file_path):
                    all_ok = False
    
    return all_ok

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Check Python files for syntax and other issues")
    parser.add_argument("path", nargs="?", default=".", help="File or directory path to check")
    parser.add_argument("--exclude", nargs="+", help="Directories to exclude from scanning")
    
    args = parser.parse_args()
    
    if args.exclude:
        exclude_dirs = args.exclude
    else:
        exclude_dirs = ["__pycache__", ".git", "venv", "env", "node_modules"]
    
    path = os.path.abspath(args.path)
    
    logger.info(f"Starting syntax checks on {path}")
    
    if os.path.isdir(path):
        success = scan_directory(path, exclude_dirs)
    elif os.path.isfile(path):
        success = check_file(path)
    else:
        logger.error(f"Path not found: {path}")
        return 1
    
    if success:
        logger.info("\n✅ All checks passed successfully!")
        return 0
    else:
        logger.error("\n❌ Some checks failed. Please fix the issues and try again.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
