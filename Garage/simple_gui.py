#!/usr/bin/env python3
"""
Simplified version of the Intake CFD GUI.
This contains just the essential elements to test that the GUI framework works.
"""
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox

class SimpleCFDGui:
    def __init__(self, root):
        self.root = root
        self.root.title("Simple Intake CFD Interface")
        self.root.geometry("800x600")
        
        # Basic color scheme
        self.bg_color = "#F5F7FA"
        self.accent_color = "#3498DB"
        self.text_color = "#2C3E50"
        
        # Configure the root window
        self.root.configure(background=self.bg_color)
        
        # Create header
        header_frame = tk.Frame(self.root, bg=self.text_color)
        header_frame.pack(side=tk.TOP, fill=tk.X)
        
        # Header title
        title_label = tk.Label(header_frame, 
                              text="Intake CFD - Simple Interface", 
                              font=("Segoe UI", 16, "bold"),
                              fg="white", 
                              bg=self.text_color)
        title_label.pack(side=tk.LEFT, padx=10, pady=10)
        
        # Main content area with tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create tabs
        self.workflow_tab = ttk.Frame(self.notebook)
        self.visualization_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.workflow_tab, text="Workflow")
        self.notebook.add(self.visualization_tab, text="Visualization")
        
        # Set up workflow tab with basic input form
        self.setup_workflow_tab()
        
        # Set up visualization tab with placeholder
        self.setup_visualization_tab()
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        
        status_bar = tk.Frame(self.root, bg=self.bg_color)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        status_label = tk.Label(status_bar, textvariable=self.status_var, 
                              bg=self.bg_color, fg=self.text_color)
        status_label.pack(side=tk.LEFT, padx=10, pady=5)
        
    def setup_workflow_tab(self):
        """Set up a simple workflow tab with input parameters"""
        # Input frame
        input_frame = ttk.LabelFrame(self.workflow_tab, text="Input Parameters", padding=10)
        input_frame.pack(side=tk.LEFT, fill='y', padx=10, pady=10)
        
        # Parameter inputs
        ttk.Label(input_frame, text="L4:").grid(row=0, column=0, sticky='w', pady=5)
        self.l4_entry = ttk.Entry(input_frame, width=10)
        self.l4_entry.grid(row=0, column=1, padx=5)
        self.l4_entry.insert(0, "2.0")
        
        ttk.Label(input_frame, text="L5:").grid(row=1, column=0, sticky='w', pady=5)
        self.l5_entry = ttk.Entry(input_frame, width=10)
        self.l5_entry.grid(row=1, column=1, padx=5)
        self.l5_entry.insert(0, "3.0")
        
        ttk.Label(input_frame, text="Alpha1:").grid(row=2, column=0, sticky='w', pady=5)
        self.alpha1_entry = ttk.Entry(input_frame, width=10)
        self.alpha1_entry.grid(row=2, column=1, padx=5)
        self.alpha1_entry.insert(0, "10.0")
        
        # Control buttons
        button_frame = ttk.Frame(input_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="Run Simulation", 
                  command=self.run_simulation).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Reset", 
                  command=self.reset_parameters).pack(side=tk.LEFT, padx=5)
        
        # Workflow steps display
        steps_frame = ttk.LabelFrame(self.workflow_tab, text="Workflow Steps", padding=10)
        steps_frame.pack(side=tk.RIGHT, fill='both', expand=True, padx=10, pady=10)
        
        # Simple workflow steps as a list
        self.steps_list = tk.Listbox(steps_frame, height=10)
        self.steps_list.pack(fill='both', expand=True)
        
        # Add workflow steps
        steps = [
            "1. Parametric CAD model",
            "2. Mesh generation",
            "3. CFD simulation",
            "4. Results processing"
        ]
        
        for step in steps:
            self.steps_list.insert(tk.END, step)
    
    def setup_visualization_tab(self):
        """Set up a simple visualization placeholder"""
        viz_frame = ttk.Frame(self.visualization_tab, padding=10)
        viz_frame.pack(fill='both', expand=True)
        
        # Message that visualization requires matplotlib
        msg = "Visualization would normally use matplotlib.\n\n"
        msg += "If you can see this message, the basic GUI framework is working correctly."
        
        ttk.Label(viz_frame, text=msg, justify='center').pack(expand=True)
    
    def run_simulation(self):
        """Simulate running a workflow"""
        try:
            # Get parameter values
            l4 = float(self.l4_entry.get())
            l5 = float(self.l5_entry.get())
            alpha1 = float(self.alpha1_entry.get())
            
            self.status_var.set("Running simulation...")
            
            # Simulate processing steps
            self.root.after(500, lambda: self.update_step(0))
            self.root.after(1500, lambda: self.update_step(1))
            self.root.after(2500, lambda: self.update_step(2))
            self.root.after(3500, lambda: self.update_step(3))
            self.root.after(4000, lambda: self.simulation_complete())
            
        except ValueError:
            messagebox.showerror("Input Error", "Please enter valid numeric values.")
    
    def update_step(self, step_index):
        """Update the workflow step status"""
        self.steps_list.itemconfig(step_index, {'bg': 'light green'})
        step_names = ["CAD model", "Mesh generation", "CFD simulation", "Results processing"]
        if step_index < len(step_names):
            self.status_var.set(f"Running {step_names[step_index]}...")
    
    def simulation_complete(self):
        """Handle simulation completion"""
        self.status_var.set("Simulation complete!")
        messagebox.showinfo("Success", "Simulation completed successfully!")
    
    def reset_parameters(self):
        """Reset parameters to default values"""
        self.l4_entry.delete(0, tk.END)
        self.l4_entry.insert(0, "2.0")
        
        self.l5_entry.delete(0, tk.END)
        self.l5_entry.insert(0, "3.0")
        
        self.alpha1_entry.delete(0, tk.END)
        self.alpha1_entry.insert(0, "10.0")
        
        # Reset workflow steps
        for i in range(self.steps_list.size()):
            self.steps_list.itemconfig(i, {'bg': 'white'})
        
        self.status_var.set("Parameters reset")

def main():
    try:
        root = tk.Tk()
        app = SimpleCFDGui(root)
        root.mainloop()
        return 0
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
