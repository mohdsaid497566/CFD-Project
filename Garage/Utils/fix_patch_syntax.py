#!/usr/bin/env python3

"""
Fix Syntax Error in patch.py
This script identifies and fixes the syntax error on line 566 of patch.py
"""

import os
import sys
import re

def fix_patch_file():
    """Find and fix the syntax error in patch.py"""
    patch_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "patch.py")
    
    if not os.path.exists(patch_file):
        print(f"Error: {patch_file} not found!")
        return False
    
    print(f"Reading {patch_file}...")
    
    try:
        with open(patch_file, 'r') as f:
            lines = f.readlines()
        
        # Check if line 566 exists
        if len(lines) < 566:
            print(f"Error: patch.py has only {len(lines)} lines, not 566!")
            return False
        
        # Check line 566
        problematic_line = lines[565]  # Zero-based indexing
        print(f"Found problematic line 566: '{problematic_line.strip()}'")
        
        if "```" in problematic_line:
            # Fix the line
            lines[565] = "# End of code block - Fixed syntax error\n"
            print("Fixed line 566.")
            
            # Write back the file
            with open(patch_file, 'w') as f:
                f.writelines(lines)
            
            print("Successfully fixed patch.py!")
            return True
        else:
            # Double check nearby lines
            for i in range(max(0, 565-5), min(len(lines), 565+6)):
                if "```" in lines[i]:
                    print(f"Found problematic backticks on line {i+1}: '{lines[i].strip()}'")
                    lines[i] = "# End of code block - Fixed syntax error\n"
                    
                    # Write back the file
                    with open(patch_file, 'w') as f:
                        f.writelines(lines)
                    
                    print(f"Successfully fixed patch.py at line {i+1}!")
                    return True
            
            print("Couldn't find the exact issue with backticks. Checking for other syntax errors...")
            
            # Look for other common syntax errors
            for i, line in enumerate(lines):
                if re.search(r'[^\'"](```|\'\'\'|""")', line):
                    print(f"Found potential syntax error on line {i+1}: '{line.strip()}'")
                    # Fix by commenting out
                    lines[i] = f"# {line}"
                    fixed = True
            
            if fixed:
                # Write back the file
                with open(patch_file, 'w') as f:
                    f.writelines(lines)
                print("Fixed potential syntax errors in patch.py")
                return True
            
            print("Couldn't identify specific syntax errors.")
            return False
    
    except Exception as e:
        print(f"Error fixing patch.py: {str(e)}")
        return False

def create_backup():
    """Create a backup of patch.py before modifying it"""
    patch_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "patch.py")
    backup_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "patch.py.bak")
    
    try:
        if os.path.exists(patch_file):
            import shutil
            shutil.copy2(patch_file, backup_file)
            print(f"Created backup at {backup_file}")
            return True
    except Exception as e:
        print(f"Failed to create backup: {str(e)}")
    return False

def main():
    """Main function to fix patch.py"""
    print("Starting patch.py syntax error fix...")
    
    # Create backup first
    create_backup()
    
    # Fix the file
    if fix_patch_file():
        print("\nThe syntax error in patch.py has been fixed!")
        print("You can now run 'python patch.py' again.")
    else:
        print("\nCouldn't automatically fix the syntax error.")
        print("Consider manually editing line 566 of patch.py to remove the triple backticks (```).")
        print("Alternatively, check nearby lines for incorrect triple backticks and remove them.")
    
    print("\nA backup of the original file was created at 'patch.py.bak'.")

if __name__ == "__main__":
    main()
