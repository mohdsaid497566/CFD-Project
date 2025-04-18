"""
Helper functions and utilities for display settings tests
"""

import threading
import time
import tkinter as tk
from tkinter import ttk

def safe_thread_function(app, root, iterations=10):
    """A thread function that safely interacts with tkinter
    
    This avoids the 'main thread is not in main loop' error
    by not directly calling tkinter methods from the thread.
    """
    time.sleep(0.1)  # Short delay for UI to initialize
    
    # Use a flag to communicate with the main thread
    app.thread_data = []
    
    # Generate data that the main thread can process
    for i in range(iterations):
        app.thread_data.append(f"Background log {i}")
        time.sleep(0.1)

def start_safe_background_task(app, root):
    """Start a background task that doesn't directly modify the UI"""
    thread = threading.Thread(target=safe_thread_function, args=(app, root))
    thread.daemon = True
    thread.start()
    
    # Process the data from the main thread
    process_thread_data(app, root)
    return thread

def process_thread_data(app, root):
    """Process thread data from the main thread"""
    if hasattr(app, 'thread_data') and app.thread_data:
        message = app.thread_data.pop(0)
        if hasattr(app, 'log'):
            app.log(message)
        
        # Schedule next update if there's more data
        if app.thread_data:
            root.after(100, process_thread_data, app, root)
