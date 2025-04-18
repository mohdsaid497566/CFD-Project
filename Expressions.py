"""
Expressions module for formatting and writing expressions for the intake CFD project.
This module handles formatting of NX expressions and writing them to files.
"""

import os
import logging
import json

logger = logging.getLogger(__name__)

def format_exp(name, exp_type, value, unit="", comment=""):
    """
    Format an expression for NX/CAD systems
    
    Args:
        name (str): Name of the expression
        exp_type (str): Type of expression (e.g., 'number', 'string', 'point', etc.)
        value: The value of the expression
        unit (str, optional): Unit for the expression. Defaults to "".
        comment (str, optional): Comment for the expression. Defaults to "".
        
    Returns:
        dict: Formatted expression dictionary
    """
    try:
        if exp_type.lower() == 'number':
            # Ensure number is correctly formatted
            value_str = str(float(value))
        else:
            value_str = str(value)
            
        # Format the expression
        expression = {
            'name': name,
            'type': exp_type.lower(),
            'value': value_str,
            'unit': unit,
            'comment': comment
        }
        
        return expression
    except Exception as e:
        logger.error(f"Error formatting expression {name}: {str(e)}")
        # Return a default expression if there's an error
        return {
            'name': name,
            'type': 'number',
            'value': '0.0',
            'unit': '',
            'comment': 'Error formatting expression'
        }

def write_exp_file(expressions, filename, append=False):
    """
    Write expressions to a file
    
    Args:
        expressions (list): List of expression dictionaries
        filename (str): Name of the file to write to (without extension)
        append (bool, optional): Whether to append to existing file. Defaults to False.
        
    Returns:
        str: Path to the created file
    """
    try:
        # Ensure filename has the correct extension
        if not filename.endswith('.exp'):
            file_path = f"{filename}.exp"
        else:
            file_path = filename
            
        # Determine write mode
        mode = 'a' if append else 'w'
        
        with open(file_path, mode) as f:
            # Write header if creating a new file
            if not append:
                f.write("# NX Expressions File\n")
                f.write("# Format: name, type, value, unit, comment\n\n")
            
            # Write each expression
            for exp in expressions:
                line = f"{exp['name']},{exp['type']},{exp['value']},{exp['unit']},{exp['comment']}\n"
                f.write(line)
                
        logger.info(f"Expressions written to {file_path}")
        return file_path
    except Exception as e:
        logger.error(f"Error writing expressions to file {filename}: {str(e)}")
        return None

def read_exp_file(filename):
    """
    Read expressions from a file
    
    Args:
        filename (str): Path to the expressions file
        
    Returns:
        list: List of expression dictionaries
    """
    try:
        if not filename.endswith('.exp'):
            file_path = f"{filename}.exp"
        else:
            file_path = filename
            
        if not os.path.exists(file_path):
            logger.error(f"Expression file not found: {file_path}")
            return []
            
        expressions = []
        with open(file_path, 'r') as f:
            lines = f.readlines()
            
        # Skip header lines (lines starting with #)
        for line in lines:
            if line.strip() and not line.strip().startswith('#'):
                parts = line.strip().split(',')
                if len(parts) >= 3:
                    # Handle case where there might be fewer than 5 parts
                    name = parts[0]
                    exp_type = parts[1]
                    value = parts[2]
                    unit = parts[3] if len(parts) > 3 else ""
                    comment = parts[4] if len(parts) > 4 else ""
                    
                    expressions.append({
                        'name': name,
                        'type': exp_type,
                        'value': value,
                        'unit': unit,
                        'comment': comment
                    })
                    
        logger.info(f"Read {len(expressions)} expressions from {file_path}")
        return expressions
    except Exception as e:
        logger.error(f"Error reading expressions from file {filename}: {str(e)}")
        return []

def convert_to_json(expressions, json_path):
    """
    Convert expressions to JSON format and save to file
    
    Args:
        expressions (list): List of expression dictionaries
        json_path (str): Path to save the JSON file
        
    Returns:
        str: Path to the created JSON file
    """
    try:
        with open(json_path, 'w') as f:
            json.dump(expressions, f, indent=4)
        
        logger.info(f"Expressions converted to JSON and saved to {json_path}")
        return json_path
    except Exception as e:
        logger.error(f"Error converting expressions to JSON: {str(e)}")
        return None