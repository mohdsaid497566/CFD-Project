#!/usr/bin/env python3
"""
Tool to automatically fix common code issues in the project
"""

import os
import sys
import re
import argparse
import logging
import autopep8
import shutil
import subprocess
import tempfile
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("CodeFix")

class CodeFixer:
    """Fixes common code issues"""
    
    def __init__(self, dry_run=False):
        self.dry_run = dry_run
        self.files_checked = 0
        self.files_modified = 0
        self.fixes_applied = 0
    
    def fix_file(self, file_path: str) -> bool:
        """Fix issues in a single file"""
        logger.info(f"Checking {file_path}...")
        self.files_checked += 1
        
        # Read the file
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logger.error(f"Error reading {file_path}: {str(e)}")
            return False
        
        # Keep original content for comparison
        original_content = content
        
        # Apply various fixes
        content = self._fix_imports(content)
        content = self._fix_indentation(content)
        content = self._fix_line_endings(content)
        content = self._fix_trailing_whitespace(content)
        content = self._apply_pep8(content, file_path)
        
        # Check if content was modified
        if content != original_content:
            self.files_modified += 1
            
            # Write changes back to file
            if not self.dry_run:
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    logger.info(f"✅ Fixed issues in {file_path}")
                except Exception as e:
                    logger.error(f"Error writing to {file_path}: {str(e)}")
                    return False
            else:
                logger.info(f"✅ Would fix issues in {file_path} (dry run)")
            
            return True
        else:
            logger.info(f"✓ No issues to fix in {file_path}")
            return True
    
    def _fix_imports(self, content: str) -> str:
        """Fix import ordering and grouping"""
        lines = content.split('\n')
        
        # Find import statements
        import_start = None
        import_end = None
        
        for i, line in enumerate(lines):
            # Skip comments and multiline strings
            if line.strip().startswith('#') or line.strip().startswith('"""') or line.strip().startswith("'''"):
                continue
            
            if line.strip().startswith('import ') or line.strip().startswith('from '):
                if import_start is None:
                    import_start = i
                import_end = i
            elif import_start is not None and import_end is not None and line.strip() and not line.strip().startswith('#'):
                # End of imports section
                break
        
        # If no imports found, return original content
        if import_start is None or import_end is None:
            return content
        
        # Extract import statements
        import_lines = lines[import_start:import_end + 1]
        
        # Group imports into standard library, third party, and local
        std_lib_imports = []
        third_party_imports = []
        local_imports = []
        
        # Standard library modules
        std_libs = {
            'abc', 'argparse', 'ast', 'asyncio', 'base64', 'collections', 'configparser', 'copy', 
            'csv', 'datetime', 'enum', 'functools', 'glob', 'gzip', 'hashlib', 'hmac', 'html', 
            'http', 'importlib', 'inspect', 'io', 'itertools', 'json', 'logging', 'math', 'mimetypes', 
            'multiprocessing', 'os', 'pathlib', 'pickle', 'random', 're', 'shutil', 'signal', 'socket', 
            'sqlite3', 'ssl', 'string', 'subprocess', 'sys', 'tempfile', 'threading', 'time', 
            'traceback', 'typing', 'unittest', 'urllib', 'uuid', 'warnings', 'xml', 'zipfile'
        }
        
        for line in import_lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            if line.startswith('import '):
                module = line[7:].split(' as ')[0].split(',')[0].strip()
            elif line.startswith('from '):
                module = line[5:].split(' import')[0].strip()
            else:
                continue
                
            # Determine the type of import
            base_module = module.split('.')[0]
            if base_module in std_libs:
                std_lib_imports.append(line)
            elif base_module in ('tkinter', 'paramiko', 'numpy', 'matplotlib', 'pandas', 'PIL'):
                third_party_imports.append(line)
            else:
                local_imports.append(line)
        
        # Create new import section with proper grouping and blank lines
        new_imports = []
        
        if std_lib_imports:
            new_imports.extend(sorted(std_lib_imports))
            new_imports.append('')
        
        if third_party_imports:
            new_imports.extend(sorted(third_party_imports))
            new_imports.append('')
        
        if local_imports:
            new_imports.extend(sorted(local_imports))
        
        # Replace old imports with new ones
        lines[import_start:import_end + 1] = new_imports
        
        self.fixes_applied += 1
        return '\n'.join(lines)
    
    def _fix_indentation(self, content: str) -> str:
        """Fix inconsistent indentation"""
        # Split into lines
        lines = content.split('\n')
        fixed_lines = []
        
        # Determine if file predominantly uses tabs or spaces
        space_count = sum(1 for line in lines if line.startswith('    '))
        tab_count = sum(1 for line in lines if line.startswith('\t'))
        
        # Use spaces by default, or tabs if file predominantly uses tabs
        use_tabs = tab_count > space_count
        
        for line in lines:
            # Skip empty lines
            if not line.strip():
                fixed_lines.append(line)
                continue
                
            # Find leading whitespace
            indent = len(line) - len(line.lstrip())
            if indent == 0:
                # No indentation, keep as is
                fixed_lines.append(line)
                continue
                
            # Count spaces and tabs in indentation
            spaces = line[:indent].count(' ')
            tabs = line[:indent].count('\t')
            
            if (use_tabs and spaces > 0) or (not use_tabs and tabs > 0):
                # Mixed indentation, fix it
                if use_tabs:
                    # Convert to tabs (4 spaces = 1 tab)
                    new_indent = '\t' * ((spaces // 4) + tabs)
                else:
                    # Convert to spaces
                    new_indent = ' ' * (4 * tabs + spaces)
                
                fixed_lines.append(new_indent + line[indent:])
                self.fixes_applied += 1
            else:
                # Consistent indentation, keep as is
                fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)
    
    def _fix_line_endings(self, content: str) -> str:
        """Fix inconsistent line endings"""
        # Check for windows line endings
        if '\r\n' in content:
            content = content.replace('\r\n', '\n')
            self.fixes_applied += 1
        
        return content
    
    def _fix_trailing_whitespace(self, content: str) -> str:
        """Fix trailing whitespace"""
        lines = content.split('\n')
        fixed_lines = []
        
        for line in lines:
            stripped = line.rstrip()
            if stripped != line:
                fixed_lines.append(stripped)
                self.fixes_applied += 1
            else:
                fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)
    
    def _apply_pep8(self, content: str, file_path: str) -> str:
        """Apply PEP 8 formatting"""
        try:
            fixed = autopep8.fix_code(
                content, 
                options={
                    'aggressive': 1,
                    'max_line_length': 100,
                    'ignore': ['E501']  # Don't enforce line length
                }
            )
            
            if fixed != content:
                self.fixes_applied += 1
            
            return fixed
        except Exception as e:
            logger.warning(f"PEP 8 fixing failed for {file_path}: {str(e)}")
            return content
    
    def scan_directory(self, directory: str, exclude_dirs: List[str] = None) -> bool:
        """Recursively scan directory and fix Python files"""
        if exclude_dirs is None:
            exclude_dirs = ["__pycache__", ".git", "venv", "env", "node_modules", ".vscode"]
        
        success = True
        
        for root, dirs, files in os.walk(directory):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            # Process Python files
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    if not self.fix_file(file_path):
                        success = False
        
        return success

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Fix common code issues in Python files")
    parser.add_argument("path", nargs="?", default=".", help="File or directory to fix")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be fixed without making changes")
    parser.add_argument("--exclude", nargs="+", help="Directories to exclude from scanning")
    
    args = parser.parse_args()
    
    logger.info("Starting code fixes")
    if args.dry_run:
        logger.info("Dry run mode: no changes will be made")
    
    path = os.path.abspath(args.path)
    fixer = CodeFixer(dry_run=args.dry_run)
    
    exclude_dirs = args.exclude or ["__pycache__", ".git", "venv", "env", "node_modules", ".vscode"]
    
    success = False
    if os.path.isdir(path):
        success = fixer.scan_directory(path, exclude_dirs)
    elif os.path.isfile(path):
        success = fixer.fix_file(path)
    else:
        logger.error(f"Path not found: {path}")
        return 1
    
    # Print summary
    logger.info("\nFix Summary:")
    logger.info(f"Files checked: {fixer.files_checked}")
    logger.info(f"Files modified: {fixer.files_modified}")
    logger.info(f"Fixes applied: {fixer.fixes_applied}")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
