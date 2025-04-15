"""
GUI Error Handler - Utility functions for handling GUI errors
"""

import sys
import traceback
import os

def log_error(error_message, exception=None):
    """
    Log an error to a file and print it to console
    """
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    
    # Create logs directory if it doesn't exist
    if not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir)
        except:
            log_dir = os.path.dirname(os.path.abspath(__file__))
    
    log_file = os.path.join(log_dir, "gui_errors.log")
    
    timestamp = __import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Format the error message
    log_message = f"[{timestamp}] {error_message}\n"
    if exception:
        log_message += f"Exception: {str(exception)}\n"
        log_message += f"Traceback:\n{traceback.format_exc()}\n"
    
    # Print to console
    print(log_message)
    
    # Write to log file
    try:
        with open(log_file, "a") as f:
            f.write(log_message)
            f.write("-" * 80 + "\n")
    except:
        print(f"Failed to write to log file: {log_file}")

def check_required_attributes(obj, required_attrs, create_missing=False, default_value=None):
    """
    Check if an object has the required attributes and optionally create them if missing
    
    Args:
        obj: The object to check
        required_attrs: List of attribute names to check for
        create_missing: Whether to create missing attributes
        default_value: Default value for created attributes
        
    Returns:
        List of missing attribute names (empty if all present or created)
    """
    missing = []
    
    for attr in required_attrs:
        if not hasattr(obj, attr):
            if create_missing:
                setattr(obj, attr, default_value)
                print(f"Created missing attribute: {attr}")
            else:
                missing.append(attr)
    
    return missing

def wrap_method(obj, method_name, fallback=None):
    """
    Wrap a method with error handling, providing a fallback if the method doesn't exist
    
    Args:
        obj: The object containing the method
        method_name: Name of the method to wrap
        fallback: Fallback function to use if the method doesn't exist
        
    Returns:
        The wrapped method
    """
    if hasattr(obj, method_name):
        original_method = getattr(obj, method_name)
        
        def wrapped_method(*args, **kwargs):
            try:
                return original_method(*args, **kwargs)
            except Exception as e:
                log_error(f"Error in {method_name}", e)
                if fallback:
                    return fallback(*args, **kwargs)
                return None
        
        setattr(obj, method_name, wrapped_method)
        return wrapped_method
    elif fallback:
        setattr(obj, method_name, fallback)
        return fallback
    
    return None
