def import_data(self):
    """Import data from various formats"""
    # Create window for import options
    import_window = tk.Toplevel(self.root)
    import_window.title("Import Data")
    import_window.geometry("500x400")
    import_window.transient(self.root)
    import_window.grab_set()
    
    # Create main frame
    main_frame = ttk.Frame(import_window, padding=20)
    main_frame.pack(fill="both", expand=True)
    
    ttk.Label(main_frame, text="Import Data", font=("Arial", 14, "bold")).pack(pady=(0, 20))
    
    # Data type selection
    ttk.Label(main_frame, text="Data Type:").pack(anchor="w")
    data_type = ttk.Combobox(main_frame, values=[
        "Geometry", 
        "Mesh", 
        "Results", 
        "Boundary Conditions", 
        "Material Properties"
    ])
    data_type.current(0)
    data_type.pack(fill="x", pady=(0, 10))
    
    # File format selection
    ttk.Label(main_frame, text="File Format:").pack(anchor="w")
    file_format = ttk.Combobox(main_frame, values=[])
    file_format.pack(fill="x", pady=(0, 10))
    
    # Update formats based on data type selection
    def update_formats(*args):
        selected = data_type.get()
        if selected == "Geometry":
            file_format['values'] = ["STEP (.stp, .step)", "IGES (.igs, .iges)", "STL (.stl)", "Other..."]
        elif selected == "Mesh":
            file_format['values'] = ["CGNS (.cgns)", "Gmsh (.msh)", "OpenFOAM (.foam)", "Other..."]
        elif selected == "Results":
            file_format['values'] = ["CSV (.csv)", "VTK (.vtk)", "EnSight (.case)", "Other..."]
        elif selected == "Boundary Conditions":
            file_format['values'] = ["JSON (.json)", "CSV (.csv)", "Text (.txt)", "Other..."]
        else:  # Material Properties
            file_format['values'] = ["JSON (.json)", "CSV (.csv)", "Text (.txt)", "Other..."]
            
        file_format.current(0)
    
    data_type.bind("<<ComboboxSelected>>", update_formats)
    update_formats()  # Initial call
    
    # File selection
    ttk.Label(main_frame, text="File Path:").pack(anchor="w", pady=(10, 0))
    file_frame = ttk.Frame(main_frame)
    file_frame.pack(fill="x", pady=(0, 10))
    
    file_path = ttk.Entry(file_frame)
    file_path.pack(side="left", fill="x", expand=True, padx=(0, 5))
    
    def browse_file():
        selected = data_type.get()
        format_selected = file_format.get()
        
        # Define appropriate file types
        if selected == "Geometry":
            if "STEP" in format_selected:
                filetypes = [("STEP Files", "*.stp *.step"), ("All Files", "*.*")]
            elif "IGES" in format_selected:
                filetypes = [("IGES Files", "*.igs *.iges"), ("All Files", "*.*")]
            elif "STL" in format_selected:
                filetypes = [("STL Files", "*.stl"), ("All Files", "*.*")]
            else:
                filetypes = [("All Files", "*.*")]
        elif selected == "Mesh":
            if "CGNS" in format_selected:
                filetypes = [("CGNS Files", "*.cgns"), ("All Files", "*.*")]
            elif "Gmsh" in format_selected:
                filetypes = [("Gmsh Files", "*.msh"), ("All Files", "*.*")]
            elif "OpenFOAM" in format_selected:
                filetypes = [("OpenFOAM Files", "*.foam"), ("All Files", "*.*")]
            else:
                filetypes = [("All Files", "*.*")]
        else:
            if "CSV" in format_selected:
                filetypes = [("CSV Files", "*.csv"), ("All Files", "*.*")]
            elif "JSON" in format_selected:
                filetypes = [("JSON Files", "*.json"), ("All Files", "*.*")]
            elif "VTK" in format_selected:
                filetypes = [("VTK Files", "*.vtk"), ("All Files", "*.*")]
            else:
                filetypes = [("All Files", "*.*")]
        
        filename = filedialog.askopenfilename(
            title=f"Select {selected} File",
            filetypes=filetypes
        )
        
        if filename:
            file_path.delete(0, "end")
            file_path.insert(0, filename)
    
    ttk.Button(file_frame, text="Browse...", command=browse_file).pack(side="right")
    
    # Import options
    options_frame = ttk.LabelFrame(main_frame, text="Import Options")
    options_frame.pack(fill="x", pady=10)
    
    # Create basic checkboxes for import options
    validate_var = tk.BooleanVar(value=True)
    ttk.Checkbutton(options_frame, text="Validate before import", variable=validate_var).pack(anchor="w", padx=10, pady=2)
    
    auto_fix_var = tk.BooleanVar(value=True)
    ttk.Checkbutton(options_frame, text="Auto-fix errors when possible", variable=auto_fix_var).pack(anchor="w", padx=10, pady=2)
    
    create_backup_var = tk.BooleanVar(value=True)
    ttk.Checkbutton(options_frame, text="Create backup", variable=create_backup_var).pack(anchor="w", padx=10, pady=2)
    
    # Button frame
    button_frame = ttk.Frame(main_frame)
    button_frame.pack(fill="x", pady=20)
    
    def perform_import():
        # In a real application, this would actually import the data
        # For now, just show a success message
        try:
            selected_file = file_path.get()
            if not selected_file:
                messagebox.showwarning("No File", "Please select a file to import.")
                return
            
            selected_type = data_type.get()
            selected_format = file_format.get()
            
            # Simulate import process
            self.update_status(f"Importing {selected_type} from {os.path.basename(selected_file)}...", 
                             show_progress=True)
            
            def import_task():
                # Simulate work
                for i in range(10):
                    time.sleep(0.2)
                    self.root.after(0, lambda val=(i+1)*10: self.progress.configure(value=val))
                
                # Update UI after import
                self.root.after(0, lambda: self.update_status(f"Successfully imported {selected_type}", 
                                                           show_progress=False))
                self.root.after(0, lambda: messagebox.showinfo("Import Complete", 
                                                           f"{selected_type} imported successfully from {os.path.basename(selected_file)}"))
                self.root.after(0, lambda: import_window.destroy())
                
                # Update workflow if appropriate
                if selected_type == "Geometry":
                    self.root.after(0, lambda: self.update_step_status(0, "complete"))
                elif selected_type == "Mesh":
                    self.root.after(0, lambda: self.update_step_status(1, "complete"))
                elif selected_type == "Results":
                    self.root.after(0, lambda: self.update_step_status(3, "complete"))
                    self.root.after(0, lambda: self.update_step_status(4, "active"))
            
            threading.Thread(target=import_task, daemon=True).start()
            
        except Exception as e:
            logger.error(f"Error during import: {str(e)}\n{traceback.format_exc()}")
            messagebox.showerror("Import Error", f"Failed to import file: {str(e)}")
    
    ttk.Button(button_frame, text="Import", command=perform_import).pack(side="right", padx=5)
    ttk.Button(button_frame, text="Cancel", command=import_window.destroy).pack(side="right", padx=5)
def export_data(self):
    """Export data to various formats"""
    # Create window for export options
    export_window = tk.Toplevel(self.root)
    export_window.title("Export Data")
    export_window.geometry("500x400")
    export_window.transient(self.root)
    export_window.grab_set()
    
    # Create main frame
    main_frame = ttk.Frame(export_window, padding=20)
    main_frame.pack(fill="both", expand=True)
    
    ttk.Label(main_frame, text="Export Data", font=("Arial", 14, "bold")).pack(pady=(0, 20))
    
    # Data type selection
    ttk.Label(main_frame, text="Data Type:").pack(anchor="w")
    data_type = ttk.Combobox(main_frame, values=[
        "Geometry", 
        "Mesh", 
        "Results", 
        "Report", 
        "Screenshots"
    ])
    data_type.current(0)
    data_type.pack(fill="x", pady=(0, 10))
    
    # File format selection
    ttk.Label(main_frame, text="File Format:").pack(anchor="w")
    file_format = ttk.Combobox(main_frame, values=[])
    file_format.pack(fill="x", pady=(0, 10))
    
    # Update formats based on data type selection
    def update_formats(*args):
        selected = data_type.get()
        if selected == "Geometry":
            file_format['values'] = ["STEP (.stp, .step)", "IGES (.igs, .iges)", "STL (.stl)", "Other..."]
        elif selected == "Mesh":
            file_format['values'] = ["CGNS (.cgns)", "Gmsh (.msh)", "OpenFOAM (.foam)", "Other..."]
        elif selected == "Results":
            file_format['values'] = ["VTK (.vtk)", "EnSight (.case)", "CSV (.csv)", "Other..."]
        elif selected == "Report":
            file_format['values'] = ["PDF (.pdf)", "HTML (.html)", "Markdown (.md)", "Text (.txt)"]
        else:  # Screenshots
            file_format['values'] = ["PNG (.png)", "JPEG (.jpg)", "SVG (.svg)"]
            
        file_format.current(0)
    
    data_type.bind("<<ComboboxSelected>>", update_formats)
    update_formats()  # Initial call
    
    # File selection
    ttk.Label(main_frame, text="Export Path:").pack(anchor="w", pady=(10, 0))
    file_frame = ttk.Frame(main_frame)
    file_frame.pack(fill="x", pady=(0, 10))
    
    file_path = ttk.Entry(file_frame)
    file_path.pack(side="left", fill="x", expand=True, padx=(0, 5))
    
    def browse_file():
        selected = data_type.get()
        format_selected = file_format.get()
        format_ext = format_selected.split('.')[-1].strip(')')
        
        # Create default filename
        default_filename = f"{self.project_name.get() if hasattr(self, 'project_name') else 'export'}_{selected.lower()}{format_ext}"
        
        filename = filedialog.asksaveasfilename(
            title=f"Export {selected}",
            initialfile=default_filename,
            defaultextension=format_ext
        )
        
        if filename:
            file_path.delete(0, "end")
            file_path.insert(0, filename)
    
    ttk.Button(file_frame, text="Browse...", command=browse_file).pack(side="right")
    
    # Export options
    options_frame = ttk.LabelFrame(main_frame, text="Export Options")
    options_frame.pack(fill="x", pady=10)
    
    # Create basic checkboxes for export options
    compress_var = tk.BooleanVar(value=False)
    ttk.Checkbutton(options_frame, text="Compress output", variable=compress_var).pack(anchor="w", padx=10, pady=2)
    
    include_metadata_var = tk.BooleanVar(value=True)
    ttk.Checkbutton(options_frame, text="Include metadata", variable=include_metadata_var).pack(anchor="w", padx=10, pady=2)
    
    # Button frame
    button_frame = ttk.Frame(main_frame)
    button_frame.pack(fill="x", pady=20)
    
    def perform_export():
        try:
            export_path = file_path.get()
            if not export_path:
                messagebox.showwarning("No File", "Please specify an export file path.")
                return
            
            selected_type = data_type.get()
            selected_format = file_format.get()
            
            # Simulate export process
            self.update_status(f"Exporting {selected_type} to {os.path.basename(export_path)}...", 
                             show_progress=True)
            
            def export_task():
                # Simulate work
                for i in range(10):
                    time.sleep(0.2)
                    self.root.after(0, lambda val=(i+1)*10: self.progress.configure(value=val))
                
                # Update UI after export
                self.root.after(0, lambda: self.update_status(f"Successfully exported {selected_type}", 
                                                           show_progress=False))
                self.root.after(0, lambda: messagebox.showinfo("Export Complete", 
                                                           f"{selected_type} exported successfully to {os.path.basename(export_path)}"))
                self.root.after(0, lambda: export_window.destroy())
            
            threading.Thread(target=export_task, daemon=True).start()
            
        except Exception as e:
            logger.error(f"Error during export: {str(e)}\n{traceback.format_exc()}")
            messagebox.showerror("Export Error", f"Failed to export file: {str(e)}")
    
    ttk.Button(button_frame, text="Export", command=perform_export).pack(side="right", padx=5)
    ttk.Button(button_frame, text="Cancel", command=export_window.destroy).pack(side="right", padx=5)
def project_file_operations(self):
    """Enhanced project file operations with backup and versioning"""
    # Create a menu for project file operations
    file_menu = tk.Menu(self.menu_bar, tearoff=0)
    self.menu_bar.add_cascade(label="Project", menu=file_menu)
    
    file_menu.add_command(label="New Project", command=self.new_project)
    file_menu.add_command(label="Open Project", command=self.open_project)
    file_menu.add_command(label="Save Project", command=self.save_project)
    file_menu.add_command(label="Save Project As...", command=self.save_project_as)
    file_menu.add_separator()
    
    # Version control submenu
    version_menu = tk.Menu(file_menu, tearoff=0)
    file_menu.add_cascade(label="Version Control", menu=version_menu)
    version_menu.add_command(label="Create Snapshot", command=self.create_project_snapshot)
    version_menu.add_command(label="View History", command=self.view_project_history)
    version_menu.add_command(label="Restore Version", command=self.restore_project_version)
    
    file_menu.add_separator()
    file_menu.add_command(label="Project Properties", command=self.show_project_properties)
    file_menu.add_command(label="Close Project", command=self.close_project)

def create_project_snapshot(self):
    """Create a snapshot of the current project state"""
    if not hasattr(self, 'current_project_path') or not self.current_project_path:
        messagebox.showwarning("No Project", "Please save the project first.")
        return
    
    # Ask for snapshot description
    description = simpledialog.askstring("Create Snapshot", "Enter a description for this snapshot:")
    if not description:
        return
    
    try:
        # Create snapshots directory if it doesn't exist
        project_dir = os.path.dirname(self.current_project_path)
        project_name = os.path.basename(self.current_project_path).replace('.cfd', '')
        snapshots_dir = os.path.join(project_dir, f"{project_name}_snapshots")
        os.makedirs(snapshots_dir, exist_ok=True)
        
        # Create snapshot file with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        snapshot_file = os.path.join(snapshots_dir, f"{project_name}_snapshot_{timestamp}.cfd")
        
        # Create project data with snapshot metadata
        project_data = {
            "project_name": self.project_name.get(),
            "description": self.project_description.get("1.0", tk.END) if hasattr(self, 'project_description') else "",
            "workflow_state": {step["name"]: step["status"] for step in self.workflow_steps},
            "settings": {
                "theme": self.theme_combo.get() if hasattr(self, 'theme_combo') else "Default",
                # Other project settings
            },
            "snapshot_info": {
                "timestamp": timestamp,
                "description": description,
                "created_by": os.getenv("USERNAME") or "Unknown"
            },
            "timestamp": datetime.now().isoformat()
        }
        
        # Save snapshot
        with open(snapshot_file, 'w') as f:
            json.dump(project_data, f, indent=2)
        
        self.update_status(f"Project snapshot created: {os.path.basename(snapshot_file)}")
        messagebox.showinfo("Snapshot Created", "Project snapshot created successfully.")
        
    except Exception as e:
        logger.error(f"Error creating snapshot: {str(e)}\n{traceback.format_exc()}")
        messagebox.showerror("Error", f"Failed to create snapshot: {str(e)}")

def view_project_history(self):
    """View the history of project snapshots"""
    if not hasattr(self, 'current_project_path') or not self.current_project_path:
        messagebox.showwarning("No Project", "Please open a project first.")
        return
    
    try:
        # Find snapshots directory
        project_dir = os.path.dirname(self.current_project_path)
        project_name = os.path.basename(self.current_project_path).replace('.cfd', '')
        snapshots_dir = os.path.join(project_dir, f"{project_name}_snapshots")
        
        if not os.path.exists(snapshots_dir):
            messagebox.showinfo("No History", "No snapshots found for this project.")
            return
        
        # Get list of snapshot files
        snapshot_files = [f for f in os.listdir(snapshots_dir) if f.endswith('.cfd')]
        
        if not snapshot_files:
            messagebox.showinfo("No History", "No snapshots found for this project.")
            return
        
        # Create history window
        history_window = tk.Toplevel(self.root)
        history_window.title("Project History")
        history_window.geometry("600x400")
        history_window.transient(self.root)
        history_window.grab_set()
        
        # Create treeview for snapshots
        columns = ("timestamp", "description", "created_by")
        history_tree = ttk.Treeview(history_window, columns=columns, show="headings")
        
        history_tree.heading("timestamp", text="Date & Time")
        history_tree.heading("description", text="Description")
        history_tree.heading("created_by", text="Created By")
        
        history_tree.column("timestamp", width=150)
        history_tree.column("description", width=300)
        history_tree.column("created_by", width=100)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(history_window, orient="vertical", command=history_tree.yview)
        history_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack tree and scrollbar
        history_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Load and display snapshot information
        snapshots = []
        for snapshot_file in snapshot_files:
            try:
                with open(os.path.join(snapshots_dir, snapshot_file), 'r') as f:
                    data = json.load(f)
                
                if "snapshot_info" in data:
                    info = data["snapshot_info"]
                    timestamp = info.get("timestamp", "Unknown")
                    # Convert timestamp to readable format
                    if timestamp != "Unknown":
                        try:
                            dt = datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
                            timestamp = dt.strftime("%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            pass
                    
                    snapshots.append({
                        "file": snapshot_file,
                        "timestamp": timestamp,
                        "description": info.get("description", ""),
                        "created_by": info.get("created_by", "Unknown")
                    })
            except Exception as e:
                logger.error(f"Error loading snapshot {snapshot_file}: {str(e)}")
        
        # Sort snapshots by timestamp (newest first)
        snapshots.sort(key=lambda x: x["file"], reverse=True)
        
        # Add to tree
        for snapshot in snapshots:
            history_tree.insert("", "end", values=(
                snapshot["timestamp"],
                snapshot["description"],
                snapshot["created_by"]
            ))
        
        # Add button frame
        button_frame = ttk.Frame(history_window)
        button_frame.pack(fill="x", pady=10)
        
        ttk.Button(button_frame, text="View Snapshot", command=lambda: self.view_snapshot(
            history_tree, snapshots_dir)).pack(side="left", padx=5)
        
        ttk.Button(button_frame, text="Restore Snapshot", command=lambda: self.restore_snapshot(
            history_tree, snapshots_dir)).pack(side="left", padx=5)
            
        ttk.Button(button_frame, text="Close", command=history_window.destroy).pack(side="right", padx=5)
        
    except Exception as e:
        logger.error(f"Error viewing project history: {str(e)}\n{traceback.format_exc()}")
        messagebox.showerror("Error", f"Failed to view project history: {str(e)}")

def view_snapshot(self, tree, snapshots_dir):
    """View details of selected snapshot"""
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("No Selection", "Please select a snapshot to view.")
        return
    
    try:
        # Get selected snapshot's index
        index = tree.index(selected[0])
        
        # Get snapshot file from snapshots list
        snapshot_files = [f for f in os.listdir(snapshots_dir) if f.endswith('.cfd')]
        snapshot_files.sort(reverse=True)  # Newest first
        
        if index >= len(snapshot_files):
            messagebox.showerror("Error", "Invalid snapshot selection.")
            return
        
        snapshot_file = os.path.join(snapshots_dir, snapshot_files[index])
        
        # Load snapshot data
        with open(snapshot_file, 'r') as f:
            data = json.load(f)
        
        # Create viewer window
        viewer = tk.Toplevel(self.root)
        viewer.title(f"Snapshot: {snapshot_files[index]}")
        viewer.geometry("600x500")
        viewer.transient(self.root)
        
        # Create a text widget to display snapshot details
        text = tk.Text(viewer, wrap="word")
        text.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(text, orient="vertical", command=text.yview)
        text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        
        # Format and display data
        text.insert("end", f"Snapshot: {snapshot_files[index]}\n\n", "heading")
        
        if "snapshot_info" in data:
            info = data["snapshot_info"]
            text.insert("end", f"Description: {info.get('description', 'None')}\n", "section")
            text.insert("end", f"Created: {info.get('timestamp', 'Unknown')}\n", "section")
            text.insert("end", f"Created By: {info.get('created_by', 'Unknown')}\n\n", "section")
        
        text.insert("end", f"Project Name: {data.get('project_name', 'Unknown')}\n", "section")
        text.insert("end", f"Description: {data.get('description', 'None')}\n\n", "section")
        
        # Add workflow state
        if "workflow_state" in data:
            text.insert("end", "Workflow State:\n", "heading2")
            for step, status in data["workflow_state"].items():
                text.insert("end", f"  - {step}: {status}\n", "normal")
            text.insert("end", "\n")
        
        # Add settings
        if "settings" in data:
            text.insert("end", "Settings:\n", "heading2")
            for setting, value in data["settings"].items():
                text.insert("end", f"  - {setting}: {value}\n", "normal")
        
        # Configure text tags
        text.tag_configure("heading", font=("Arial", 12, "bold"))
        text.tag_configure("heading2", font=("Arial", 10, "bold"))
        text.tag_configure("section", font=("Arial", 10))
        text.tag_configure("normal", font=("Arial", 10))
        
        # Make text read-only
        text.configure(state="disabled")
        
        # Add close button
        ttk.Button(viewer, text="Close", command=viewer.destroy).pack(pady=10)
        
    except Exception as e:
        logger.error(f"Error viewing snapshot: {str(e)}\n{traceback.format_exc()}")
        messagebox.showerror("Error", f"Failed to view snapshot: {str(e)}")
def create_comparison_tab(self):
    """Create a tab for comparing multiple CFD results"""
    self.comparison_tab = ttk.Frame(self.notebook)
    self.notebook.add(self.comparison_tab, text="Comparison")
    
    # Split the tab into two panes: selection on left, comparison on right
    paned = ttk.PanedWindow(self.comparison_tab, orient="horizontal")
    paned.pack(fill="both", expand=True, padx=10, pady=10)
    
    # Left panel for case selection
    selection_frame = ttk.Frame(paned)
    paned.add(selection_frame, weight=1)
    
    # Case selection
    cases_frame = ttk.LabelFrame(selection_frame, text="Cases")
    cases_frame.pack(fill="both", expand=True, padx=5, pady=5)
    
    # Case list with checkboxes
    self.case_vars = []
    self.case_frames = []
    
    # Create a canvas with scrollbar for the cases
    case_canvas = tk.Canvas(cases_frame)
    scrollbar = ttk.Scrollbar(cases_frame, orient="vertical", command=case_canvas.yview)
    case_canvas.configure(yscrollcommand=scrollbar.set)
    
    scrollbar.pack(side="right", fill="y")
    case_canvas.pack(side="left", fill="both", expand=True)
    
    # Create a frame inside the canvas for the case checkboxes
    self.cases_container = ttk.Frame(case_canvas)
    case_canvas.create_window((0, 0), window=self.cases_container, anchor="nw")
    
    # Add some sample cases
    self._add_sample_cases()
    
    # Update scroll region when size changes
    self.cases_container.bind("<Configure>", lambda e: case_canvas.configure(
        scrollregion=case_canvas.bbox("all")))
    
    # Comparison settings
    comp_settings_frame = ttk.LabelFrame(selection_frame, text="Comparison Settings")
    comp_settings_frame.pack(fill="x", padx=5, pady=5)
    
    ttk.Label(comp_settings_frame, text="Compare:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
    self.comp_type = ttk.Combobox(comp_settings_frame, values=[
        "Pressure Coefficient", 
        "Force History", 
        "Residual Convergence", 
        "Performance"
    ])
    self.comp_type.current(0)
    self.comp_type.grid(row=0, column=1, padx=5, pady=5, sticky="w")
    
    ttk.Label(comp_settings_frame, text="Display:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
    self.comp_display = ttk.Combobox(comp_settings_frame, values=[
        "Line Graph", 
        "Bar Chart", 
        "Table", 
        "Side-by-Side"
    ])
    self.comp_display.current(0)
    self.comp_display.grid(row=1, column=1, padx=5, pady=5, sticky="w")
    
    # Action buttons
    action_frame = ttk.Frame(selection_frame)
    action_frame.pack(fill="x", padx=5, pady=10)
    
    ttk.Button(action_frame, text="Compare Selected", command=self.run_comparison).pack(side="left", padx=5)
    ttk.Button(action_frame, text="Export Comparison", command=self.export_comparison).pack(side="left", padx=5)
    ttk.Button(action_frame, text="Clear", command=self.clear_comparison).pack(side="left", padx=5)
    
    # Right panel for comparison visualization
    vis_frame = ttk.Frame(paned)
    paned.add(vis_frame, weight=2)
    
    # Comparison visualization area
    self.comp_canvas = tk.Canvas(vis_frame, bg="white")
    self.comp_canvas.pack(fill="both", expand=True)
    
    # Initial text
    self.comp_canvas.create_text(300, 200, text="Select cases to compare and click 'Compare Selected'", 
                              font=("Arial", 14))

def _add_sample_cases(self):
    """Add sample cases for demonstration"""
    sample_cases = [
        {"name": "Baseline", "date": "2023-07-15", "description": "Initial CFD run with default settings"},
        {"name": "Refined Mesh", "date": "2023-07-16", "description": "Run with 50% finer mesh"},
        {"name": "Modified Geometry", "date": "2023-07-18", "description": "Modified inlet profile"},
        {"name": "Higher Reynolds", "date": "2023-07-20", "description": "Reynolds number increased to 1e6"},
        {"name": "Turbulence Study", "date": "2023-07-22", "description": "Using k-omega SST model"},
        {"name": "Optimization Run", "date": "2023-07-25", "description": "Result of shape optimization"}
    ]
    
    for i, case in enumerate(sample_cases):
        # Create a variable for checkbox state
        var = tk.BooleanVar(value=False)
        self.case_vars.append(var)
        
        # Create frame for this case
        case_frame = ttk.Frame(self.cases_container)
        case_frame.pack(fill="x", padx=5, pady=2)
        self.case_frames.append(case_frame)
        
        # Add checkbox with case name
        ttk.Checkbutton(case_frame, text=case["name"], variable=var).grid(row=0, column=0, sticky="w")
        
        # Add date and description
        ttk.Label(case_frame, text=f"Date: {case['date']}").grid(row=1, column=0, padx=(20, 0), sticky="w")
        ttk.Label(case_frame, text=case["description"], wraplength=200).grid(row=2, column=0, padx=(20, 0), sticky="w")
        
        # Add separator except for last item
        if i < len(sample_cases) - 1:
            ttk.Separator(self.cases_container, orient="horizontal").pack(fill="x", padx=5, pady=5)

def run_comparison(self):
    """Run comparison of selected cases"""
    # Get selected cases
    selected_cases = [i for i, var in enumerate(self.case_vars) if var.get()]
    
    if not selected_cases:
        messagebox.showwarning("No Selection", "Please select at least one case to compare.")
        return
    
    # Update status
    self.update_status(f"Comparing {len(selected_cases)} cases...", show_progress=True)
    
    # Simulate comparison process
    def compare_cases():
        # Update progress
        for i in range(10):
            time.sleep(0.2)  # Simulate work
            self.root.after(0, lambda val=(i+1)*10: self.progress.configure(value=val))
        
        # Generate comparison visualization
        self.root.after(0, lambda: self._create_comparison_visualization(selected_cases))
        self.root.after(0, lambda: self.update_status(f"Comparison complete", show_progress=False))
    
    threading.Thread(target=compare_cases, daemon=True).start()

def _create_comparison_visualization(self, selected_indices):
    """Create visualization for selected cases comparison"""
    # Clear canvas
    self.comp_canvas.delete("all")
    
    # Get canvas dimensions
    width = self.comp_canvas.winfo_width()
    height = self.comp_canvas.winfo_height()
    
    # Get selected comparison type and display type
    comp_type = self.comp_type.get()
    display_type = self.comp_display.get()
    
    # Draw title
    self.comp_canvas.create_text(width/2, 20, text=f"Comparison: {comp_type}", font=("Arial", 14, "bold"))
    
    # Draw comparison based on type and display
    if display_type == "Line Graph":
        self._draw_comparison_line_graph(selected_indices, width, height)
    elif display_type == "Bar Chart":
        self._draw_comparison_bar_chart(selected_indices, width, height)
    elif display_type == "Table":
        self._draw_comparison_table(selected_indices, width, height)
    else:  # Side-by-Side
        self._draw_comparison_side_by_side(selected_indices, width, height)
def generate_analysis(self):
    """Generate the selected analysis visualization"""
    # Show that we're processing
    self.update_status(f"Generating {self.analysis_type.get()} analysis...", show_progress=True)
    
    # This would normally involve complex calculations based on CFD results
    # For demonstration, we'll just simulate processing time and create a demo visualization
    def process_analysis():
        # Simulate processing time
        for i in range(10):
            time.sleep(0.2)  # Simulate work
            self.root.after(0, lambda val=(i+1)*10: self.progress.configure(value=val))
        
        # Generate demo visualization based on analysis type
        self.root.after(0, lambda: self._create_demo_visualization())
        self.root.after(0, lambda: self.update_status(f"{self.analysis_type.get()} analysis complete", show_progress=False))
    
    threading.Thread(target=process_analysis, daemon=True).start()

def _create_demo_visualization(self):
    """Create a demonstration visualization based on the selected analysis type"""
    import random
    import math
    
    # Clear existing visualization
    self.vis_canvas.delete("all")
    
    # Clear data tree
    for item in self.data_tree.get_children():
        self.data_tree.delete(item)
    
    # Get canvas dimensions
    width = self.vis_canvas.winfo_width()
    height = self.vis_canvas.winfo_height()
    
    # Add title
    analysis_type = self.analysis_type.get()
    result_field = getattr(self, 'result_field', None)
    result_field_text = result_field.get() if hasattr(result_field, 'get') else "Results"
    
    title = f"{analysis_type}: {result_field_text}"
    self.vis_canvas.create_text(width/2, 20, text=title, font=("Arial", 14, "bold"))
    
    # Draw based on analysis type
    if analysis_type == "Flow Field" or analysis_type == "Surface Pressure":
        # Draw a contour plot
        self._draw_contour_plot(width, height)
        
    elif analysis_type == "Force Coefficients":
        # Draw a bar chart
        self._draw_force_coefficients(width, height)
        
    elif analysis_type == "Residual History":
        # Draw a convergence plot
        self._draw_residual_history(width, height)
        
    else:  # Custom Query
        # Draw a generic visualization
        self._draw_custom_query(width, height)

def _draw_contour_plot(self, width, height):
    """Draw a demonstration contour plot"""
    import random
    
    # Set up axes
    padding = 50
    x_origin = padding
    y_origin = height - padding
    x_end = width - padding
    y_end = padding
    
    # Draw axes
    self.vis_canvas.create_line(x_origin, y_origin, x_end, y_origin, width=2, arrow=tk.LAST)  # X axis
    self.vis_canvas.create_line(x_origin, y_origin, x_origin, y_end, width=2, arrow=tk.LAST)  # Y axis
    
    # Draw axis labels
    self.vis_canvas.create_text(width/2, height-10, text="X Position (m)")
    self.vis_canvas.create_text(15, height/2, angle=90, text="Y Position (m)")
    
    # Draw contour field (as colored rectangles)
    result_field = getattr(self, 'result_field', None)
    field_name = result_field.get() if hasattr(result_field, 'get') else "Pressure"
    
    # Check if we're using the slice plane option
    slice_plane = getattr(self, 'slice_plane', None)
    slice_plane_val = slice_plane.get() if hasattr(slice_plane, 'get') else "XY"
    
    # Create a grid of colored cells
    cell_width = (x_end - x_origin) / 40
    cell_height = (y_origin - y_end) / 40
    
    # Generate random but smooth data for demonstration
    from math import sin, cos, sqrt
    
    # Create color gradient for legend
    colors = []
    min_val = 0
    max_val = 10
    
    # Generate data values
    data_points = []
    for i in range(40):
        row = []
        for j in range(40):
            # Create somewhat realistic data based on analysis type
            x = i / 40
            y = j / 40
            
            if field_name == "Pressure" or field_name == "p" or field_name == "Cp":
                val = 5 + 2 * sin(x * 5) * cos(y * 5)  # Pressure-like field
            elif field_name == "Velocity" or field_name == "U":
                val = 5 + 3 * sqrt((x - 0.5)**2 + (y - 0.5)**2)  # Velocity magnitude
            elif field_name == "Temperature" or field_name == "T":
                val = 5 + 4 * (1 - sqrt((x - 0.5)**2 + (y - 0.5)**2))  # Temperature field
            else:
                val = 5 + random.uniform(-2, 2)  # Generic field
            
            row.append(val)
            
            # Add some data points to the tree view
            if i % 10 == 0 and j % 10 == 0:
                self.data_tree.insert("", "end", values=(
                    f"({i/4:.2f}, {j/4:.2f}, 0.00)", 
                    f"{val:.3f}", 
                    field_name
                ))
        data_points.append(row)
    
    # Find global min/max for color scaling
    min_val = min([min(row) for row in data_points])
    max_val = max([max(row) for row in data_points])
    
    # Draw the contour cells
    for i in range(40):
        for j in range(40):
            x = x_origin + i * cell_width
            y = y_origin - (j + 1) * cell_height
            
            val = data_points[i][j]
            # Map value to color (blue to red gradient)
            norm_val = (val - min_val) / (max_val - min_val) if max_val > min_val else 0.5
            r = int(255 * norm_val)
            b = int(255 * (1 - norm_val))
            g = int(100 * (1 - abs(2 * norm_val - 1)))
            
            color = f"#{r:02x}{g:02x}{b:02x}"
            
            self.vis_canvas.create_rectangle(
                x, y, x + cell_width, y + cell_height,
                fill=color, outline=""
            )
    
    # Draw color legend
    legend_width = 20
    legend_height = y_origin - y_end - 40
    legend_x = x_end + 30
    legend_y = y_end + 20
    
    # Draw the gradient bar
    for i in range(100):
        y = legend_y + i * (legend_height / 100)
        norm_val = 1 - (i / 100)  # Flip so max is at top
        r = int(255 * norm_val)
        b = int(255 * (1 - norm_val))
        g = int(100 * (1 - abs(2 * norm_val - 1)))
        color = f"#{r:02x}{g:02x}{b:02x}"
        
        self.vis_canvas.create_rectangle(
            legend_x, y,
            legend_x + legend_width, y + legend_height / 100,
            fill=color, outline=""
        )
    
    # Add legend border
    self.vis_canvas.create_rectangle(
        legend_x, legend_y,
        legend_x + legend_width, legend_y + legend_height,
        outline="black"
    )
    
    # Add legend labels
    self.vis_canvas.create_text(
        legend_x + legend_width / 2, legend_y - 10,
        text=f"{max_val:.2f}"
    )
    self.vis_canvas.create_text(
        legend_x + legend_width / 2, legend_y + legend_height + 10,
        text=f"{min_val:.2f}"
    )
    self.vis_canvas.create_text(
        legend_x + legend_width / 2, legend_y + legend_height / 2,
        text=field_name, angle=90
    )

def _draw_force_coefficients(self, width, height):
    """Draw a demonstration bar chart for force coefficients"""
    import random
    
    # Set up bar chart
    padding = 60
    x_origin = padding
    y_origin = height - padding
    x_end = width - padding
    y_end = padding
    
    # Draw axes
    self.vis_canvas.create_line(x_origin, y_origin, x_end, y_origin, width=2)  # X axis
    self.vis_canvas.create_line(x_origin, y_origin, x_origin, y_end, width=2)  # Y axis
    
    # Generate sample coefficient data
    coeff_data = {
        "Cd": random.uniform(0.2, 0.5),
        "Cl": random.uniform(-0.1, 0.3),
        "Cm": random.uniform(-0.05, 0.05),
        "Cf": random.uniform(0.01, 0.05)
    }
    
    # Add to data tree
    for coeff, value in coeff_data.items():
        self.data_tree.insert("", "end", values=(coeff, f"{value:.5f}", "-"))
    
    # Find max absolute value for scaling
    max_abs_val = max([abs(val) for val in coeff_data.values()])
    
    # Draw bars
    bar_width = (x_end - x_origin) / (len(coeff_data) * 2)
    for i, (coeff, val) in enumerate(coeff_data.items()):
        # Calculate bar position and height
        x = x_origin + bar_width + i * bar_width * 2
        
        # Bar height scaled to fit in chart
        bar_height = val * (y_origin - y_end - 50) / max_abs_val
        
        # Bar starts at x-axis (negative values go down)
        y_start = y_origin
        if val < 0:
            y_start = y_origin
            bar_height = abs(bar_height)  # Make height positive for drawing
            color = "#f44336"  # Red for negative
        else:
            y_start = y_origin - bar_height
            color = "#2196f3"  # Blue for positive
        
        # Draw bar
        self.vis_canvas.create_rectangle(
            x - bar_width/2, y_start,
            x + bar_width/2, y_origin if val >= 0 else y_origin + bar_height,
            fill=color, outline="black"
        )
        
        # Draw coefficient label
        self.vis_canvas.create_text(
            x, y_origin + 20,
            text=coeff
        )
        
        # Draw value label
        self.vis_canvas.create_text(
            x, y_start - 10 if val >= 0 else y_start + bar_height + 10,
            text=f"{val:.3f}"
        )
    
    # Draw chart title
    title = f"Force Coefficients - {getattr(self, 'result_field', None).get() if hasattr(getattr(self, 'result_field', None), 'get') else 'Results'}"
    self.vis_canvas.create_text(width/2, 20, text=title, font=("Arial", 14, "bold"))
def setup_hpc_tab(self):
    """Set up HPC tab with enhanced connection management"""
    # Check if HPC tab already exists
    if hasattr(self, 'hpc_tab'):
        self.notebook.select(self.notebook.index(self.hpc_tab))
        return

    # Create HPC tab
    self.hpc_tab = ttk.Frame(self.notebook)
    self.notebook.add(self.hpc_tab, text="HPC")
    
    # Connection settings section
    conn_frame = ttk.LabelFrame(self.hpc_tab, text="HPC Connection")
    conn_frame.pack(fill="x", padx=20, pady=10)
    
    # Create a grid for connection settings
    grid = ttk.Frame(conn_frame)
    grid.pack(fill="x", padx=10, pady=10)
    
    # Connection profile selector
    ttk.Label(grid, text="Connection Profile:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
    self.conn_profile = ttk.Combobox(grid)
    self.conn_profile.grid(row=0, column=1, padx=5, pady=5, sticky="w")
    ttk.Button(grid, text="Save Profile", command=self.save_hpc_profile).grid(row=0, column=2, padx=5, pady=5)
    ttk.Button(grid, text="Delete Profile", command=self.delete_hpc_profile).grid(row=0, column=3, padx=5, pady=5)
    
    # Host settings
    ttk.Label(grid, text="HPC Host:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
    self.hpc_host = ttk.Entry(grid, width=30)
    self.hpc_host.grid(row=1, column=1, padx=5, pady=5, sticky="w")
    
    ttk.Label(grid, text="Username:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
    self.hpc_username = ttk.Entry(grid, width=30)
    self.hpc_username.grid(row=2, column=1, padx=5, pady=5, sticky="w")
    
    ttk.Label(grid, text="Port:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
    self.hpc_port = ttk.Entry(grid, width=10)
    self.hpc_port.grid(row=3, column=1, padx=5, pady=5, sticky="w")
    self.hpc_port.insert(0, "22")
    
    # Authentication method
    ttk.Label(grid, text="Authentication:").grid(row=4, column=0, padx=5, pady=5, sticky="w")
    self.auth_method = tk.StringVar(value="password")
    ttk.Radiobutton(grid, text="Password", variable=self.auth_method, value="password").grid(row=4, column=1, padx=5, pady=5, sticky="w")
    ttk.Radiobutton(grid, text="SSH Key", variable=self.auth_method, value="key").grid(row=4, column=2, padx=5, pady=5, sticky="w")
    
    ttk.Label(grid, text="SSH Key:").grid(row=5, column=0, padx=5, pady=5, sticky="w")
    key_frame = ttk.Frame(grid)
    key_frame.grid(row=5, column=1, columnspan=3, padx=5, pady=5, sticky="w")
    self.key_path = ttk.Entry(key_frame, width=40)
    self.key_path.pack(side="left", padx=(0, 5))
    ttk.Button(key_frame, text="Browse...", command=self.select_key_file).pack(side="left")
    
    # Remote directory
    ttk.Label(grid, text="Remote Directory:").grid(row=6, column=0, padx=5, pady=5, sticky="w")
    self.remote_dir = ttk.Entry(grid, width=40)
    self.remote_dir.grid(row=6, column=1, columnspan=3, padx=5, pady=5, sticky="w")
    self.remote_dir.insert(0, "/home/user/cfd_projects")
    
    # Connection actions
    btn_frame = ttk.Frame(conn_frame)
    btn_frame.pack(fill="x", padx=10, pady=10)
    ttk.Button(btn_frame, text="Test Connection", command=self.test_connection).pack(side="left", padx=5)
    ttk.Button(btn_frame, text="Connect", command=self.connect_to_hpc).pack(side="left", padx=5)
    ttk.Button(btn_frame, text="Disconnect", command=self.disconnect_from_hpc).pack(side="left", padx=5)
    
    # Connection status indicator
    self.conn_status_var = tk.StringVar(value="Not Connected")
    self.conn_status = ttk.Label(btn_frame, textvariable=self.conn_status_var, 
                                foreground="red", font=("Arial", 10, "bold"))
    self.conn_status.pack(side="right", padx=10)
    
    # Job management section
    job_frame = ttk.LabelFrame(self.hpc_tab, text="HPC Job Management")
    job_frame.pack(fill="both", expand=True, padx=20, pady=10)
    
    # Create job list with scrollbar
    job_list_frame = ttk.Frame(job_frame)
    job_list_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    # Create Treeview for job list
    columns = ("id", "name", "status", "queue", "nodes", "time")
    self.job_tree = ttk.Treeview(job_list_frame, columns=columns, show="headings")
    
    # Define column headings
    self.job_tree.heading("id", text="Job ID")
    self.job_tree.heading("name", text="Name")
    self.job_tree.heading("status", text="Status")
    self.job_tree.heading("queue", text="Queue")
    self.job_tree.heading("nodes", text="Nodes")
    self.job_tree.heading("time", text="Run Time")
    
    # Configure column widths
    self.job_tree.column("id", width=80)
    self.job_tree.column("name", width=150)
    self.job_tree.column("status", width=80)
    self.job_tree.column("queue", width=80)
    self.job_tree.column("nodes", width=60)
    self.job_tree.column("time", width=80)
    
    # Add scrollbar
    scrollbar = ttk.Scrollbar(job_list_frame, orient="vertical", command=self.job_tree.yview)
    self.job_tree.configure(yscrollcommand=scrollbar.set)
    
    # Pack tree and scrollbar
    self.job_tree.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    # Job control buttons
    job_control_frame = ttk.Frame(job_frame)
    job_control_frame.pack(fill="x", padx=10, pady=10)
    
    ttk.Button(job_control_frame, text="Refresh", command=self.refresh_job_list).pack(side="left", padx=5)
    ttk.Button(job_control_frame, text="Submit Job", command=self.submit_job).pack(side="left", padx=5)
    ttk.Button(job_control_frame, text="Cancel Job", command=self.cancel_job).pack(side="left", padx=5)
    ttk.Button(job_control_frame, text="Job Details", command=self.show_job_details).pack(side="left", padx=5)
    ttk.Button(job_control_frame, text="Download Results", command=self.download_results).pack(side="left", padx=5)
    
    # Load saved HPC settings
    self.load_hpc_profiles()
    self.load_hpc_profiles()

def test_connection(self):
    """Test the connection to the HPC system"""
    host = self.hpc_host.get()
    username = self.hpc_username.get()
    port = int(self.hpc_port.get())
    
    if not host or not username:
        messagebox.showwarning("Connection Error", "Please enter host and username.")
        return
        
    # Update status
    self.update_status(f"Testing connection to {host}...", show_progress=True)
    
    # Run connection test in a separate thread to avoid freezing the UI
    def run_test():
        try:
            # Try to import paramiko (for SSH connections)
            try:
                import paramiko
            except ImportError:
                self.root.after(0, lambda: messagebox.showerror("Missing Dependency", 
                                                              "Paramiko module not found. Please install it with:\npip install paramiko"))
                self.root.after(0, lambda: self.update_status("Connection test failed: Missing paramiko module"))
                return
                
            # Set up SSH client
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Connect based on authentication method
            try:
                if self.auth_method.get() == "key" and self.key_path.get():
                    key = paramiko.RSAKey.from_private_key_file(self.key_path.get())
                    client.connect(hostname=host, port=port, username=username, pkey=key, timeout=10)
                else:
                    # For demo purposes, we'll just try to connect without password
                    # In a real implementation, you would prompt for password
                    client.connect(hostname=host, port=port, username=username, timeout=5)
                    
                # Try to execute a command
                stdin, stdout, stderr = client.exec_command("hostname")
                result = stdout.read().decode().strip()
                client.close()
                
                # Update UI from main thread
                self.root.after(0, lambda: self.conn_status_var.set("Connected"))
                self.root.after(0, lambda: self.conn_status.configure(foreground="green"))
                self.root.after(0, lambda: self.update_status(f"Connected to {result}", show_progress=False))
                self.root.after(0, lambda: messagebox.showinfo("Connection Successful", 
                                                           f"Successfully connected to {result}"))
            except Exception as e:
                logger.error(f"Connection test failed: {str(e)}")
                self.root.after(0, lambda: self.conn_status_var.set("Not Connected"))
                self.root.after(0, lambda: self.conn_status.configure(foreground="red"))
                self.root.after(0, lambda: self.update_status("Connection test failed", show_progress=False))
                self.root.after(0, lambda: messagebox.showerror("Connection Failed", 
                                                            f"Failed to connect to {host}:\n{str(e)}"))
        except Exception as e:
            logger.error(f"Error during connection test: {str(e)}\n{traceback.format_exc()}")
            self.root.after(0, lambda: self.update_status("Connection test failed with error", show_progress=False))
            self.root.after(0, lambda: messagebox.showerror("Error", 
                                                        f"An error occurred during the connection test:\n{str(e)}"))
    
    threading.Thread(target=run_test, daemon=True).start()
def save_project(self):
    """Save the current project with enhanced error handling"""
    try:
        if not hasattr(self, 'current_project_path') or not self.current_project_path:
            return self.save_project_as()
            
        project_data = {
            "project_name": self.project_name.get(),
            "description": self.project_description.get("1.0", tk.END) if hasattr(self, 'project_description') else "",
            "workflow_state": {step["name"]: step["status"] for step in self.workflow_steps},
            "settings": {
                "theme": self.theme_combo.get() if hasattr(self, 'theme_combo') else "Default",
                # Other project settings
            },
            "timestamp": datetime.now().isoformat()
        }
        
        with open(self.current_project_path, 'w') as f:
            json.dump(project_data, f, indent=2)
            
        self.update_status(f"Project saved: {self.project_name.get()}")
        self.add_to_recent_projects(self.current_project_path)
        return True
    except Exception as e:
        logger.error(f"Error saving project: {str(e)}\n{traceback.format_exc()}")
        messagebox.showerror("Save Error", f"Failed to save project: {str(e)}")
        return False

def save_project_as(self):
    """Save the project to a new file"""
    try:
        file_path = filedialog.asksaveasfilename(
            title="Save Project As",
            initialdir=self.project_location.get() if hasattr(self, 'project_location') else os.path.expanduser("~"),
            initialfile=f"{self.project_name.get()}.cfd",
            defaultextension=".cfd",
            filetypes=[("CFD Project Files", "*.cfd"), ("All Files", "*.*")]
        )
        
        if not file_path:
            return False  # User cancelled
            
        self.current_project_path = file_path
        return self.save_project()
    except Exception as e:
        logger.error(f"Error in save_project_as: {str(e)}\n{traceback.format_exc()}")
        messagebox.showerror("Save Error", f"Failed to save project: {str(e)}")
        return False

def add_to_recent_projects(self, project_path):
    """Add project to recent projects list"""
    try:
        config_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config")
        os.makedirs(config_dir, exist_ok=True)
        recent_file = os.path.join(config_dir, "recent_projects.json")
        
        recent_projects = []
        if os.path.exists(recent_file):
            with open(recent_file, 'r') as f:
                recent_projects = json.load(f)
                
        # Remove if already exists (to move to top)
        if project_path in recent_projects:
            recent_projects.remove(project_path)
            
        # Add to beginning of list
        recent_projects.insert(0, project_path)
        
        # Keep only the most recent 10
        recent_projects = recent_projects[:10]
        
        with open(recent_file, 'w') as f:
            json.dump(recent_projects, f, indent=2)
            
        # Update recent projects menu if it exists
        if hasattr(self, 'update_recent_menu'):
            self.update_recent_menu(recent_projects)
    except Exception as e:
        logger.error(f"Error updating recent projects: {str(e)}")
import tkinter as tkdef create_status_bar(self):









































































        print(f"Step {step_index + 1} clicked.")        """Handle step click event"""    
        def on_step_click(self, step_index):        
            self.workflow_canvas.tag_bind(widget_id, "<Leave>", leave)        
            self.workflow_canvas.tag_bind(widget_id, "<Enter>", enter)                        
            tooltip = None                
            tooltip.destroy()            
            if tooltip:           
                nonlocal tooltip        
        def leave(event):                    
            label.pack()                             
            background="#ffffcc", relief="solid", borderwidth=1, padding=(5, 5))            label = ttk.Label(tooltip, text=text, wraplength=200,                        tooltip.wm_geometry(f"+{x}+{y}")            tooltip.wm_overrideredirect(True)            tooltip = tk.Toplevel(self.workflow_canvas)            # Create tooltip window                        y += self.workflow_canvas.winfo_rooty() + 40            x += self.workflow_canvas.winfo_rootx() + 40            x, y, _, _ = self.workflow_canvas.bbox(widget_id)            nonlocal tooltip        def enter(event):                tooltip = None        """Create a tooltip for a canvas widget"""    def create_tooltip(self, widget_id, text):                                       lambda event, idx=i: self.on_step_click(idx))            self.workflow_canvas.tag_bind(circle_id, "<Button-1>",             # Make step clickable                        self.create_tooltip(circle_id, f"Step {i+1}: {step['name']}\nStatus: {step['status'].title()}\n{step['description']}")            # Add tooltips and clickable behavior                        self.workflow_canvas.create_text(x, y, text=step["name"], font=("Arial", 12))            # Create text and other elements                                                                  fill=circle_color, outline="#007acc", width=2)            circle_id = self.workflow_canvas.create_oval(x-30, y-30, x+30, y+30,             x, y = 100 + i * 150, 100  # Example positioning            # Create the step circle with the status color                        circle_color = status_colors.get(step["status"], "#f0f0f0")            # Use the appropriate status color                        step["current_status"] = step["status"]            # Store the current status for reference                        }                "error": "#f44336"     # Red                "complete": "#4caf50", # Green                "active": "#2196f3",   # Blue                "pending": "#f0f0f0",  # Light gray            status_colors = {            # Draw indicator for step status                    for i, step in enumerate(self.workflow_steps):        # Enhanced step visualization with better status indicators                """Create visual workflow steps with enhanced visuals and interaction"""    def _create_workflow_steps(self):        self.workflow_steps = workflow_steps        self.workflow_canvas = workflow_canvas    def __init__(self, workflow_canvas, workflow_steps):class WorkflowManager:from tkinter import ttk    """Create an enhanced status bar with progress indication"""
    self.status_frame = ttk.Frame(self.root)
    self.status_frame.pack(side="bottom", fill="x")
    
    self.status_var = tk.StringVar()
    self.status_var.set("Ready")
    self.status_bar = ttk.Label(self.status_frame, textvariable=self.status_var, relief="sunken", anchor="w")
    self.status_bar.pack(side="left", fill="x", expand=True)
    
    self.progress = ttk.Progressbar(self.status_frame, orient="horizontal", length=200, mode="determinate")
    self.progress.pack(side="right", padx=10)
    
    self.progress_task = None  # For cancelling ongoing progress updates

def update_status(self, message, show_progress=False, progress_max=100):
    """Update the status bar with an optional progress indicator"""
    logger.info(f"Status update: {message}")
    self.status_var.set(message)
    self.root.update_idletasks()  # Force update
    
    if show_progress:
        self.progress["maximum"] = progress_max
        self.progress["value"] = 0
        self.progress.pack(side="right", padx=10)
    else:
        self.progress.pack_forget()
def create_menu_bar(self):
    """Create a menu bar with standard application features"""
    menubar = tk.Menu(self.root)
    self.root.config(menu=menubar)
    
    # File menu
    file_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="File", menu=file_menu)
    file_menu.add_command(label="New Project", command=self.new_project, accelerator="Ctrl+N")
    file_menu.add_command(label="Open Project", command=self.open_project, accelerator="Ctrl+O")
    file_menu.add_command(label="Save Project", command=self.save_project, accelerator="Ctrl+S")
    file_menu.add_command(label="Save Project As...", command=self.save_project_as)
    file_menu.add_separator()
    file_menu.add_command(label="Export Results...", command=self.export_results)
    file_menu.add_separator()
    file_menu.add_command(label="Exit", command=self.on_exit)
    
    # Edit menu
    edit_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Edit", menu=edit_menu)
    edit_menu.add_command(label="Preferences...", command=lambda: self.notebook.select(self.notebook.index(self.settings_tab)))
    
    # View menu
    view_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="View", menu=view_menu)
    view_menu.add_command(label="Reset Layout", command=self.reset_layout)
    
    # Theme submenu
    theme_menu = tk.Menu(view_menu, tearoff=0)
    view_menu.add_cascade(label="Theme", menu=theme_menu)
    for theme_name in self.themes.keys():
        theme_menu.add_radiobutton(label=theme_name, 
                                  command=lambda tn=theme_name: self.apply_theme(tn))
    
    # Tools menu
    tools_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Tools", menu=tools_menu)
    tools_menu.add_command(label="Connect to HPC...", command=self.setup_hpc_tab)
    
    # Help menu
    help_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Help", menu=help_menu)
    help_menu.add_command(label="Documentation", command=self.show_documentation)
    help_menu.add_command(label="About", command=self.show_about)
    
    # Keyboard shortcuts
    self.root.bind("<Control-n>", lambda event: self.new_project())
    self.root.bind("<Control-o>", lambda event: self.open_project())
    self.root.bind("<Control-s>", lambda event: self.save_project())
"""
WorkflowGUI - Main GUI class for CFD Workflow Assistant
"""
import os
import tkinter as tk
from tkinter import ttk, messagebox
import json
import threading

class WorkflowGUI:
    """Main GUI class for CFD Workflow Assistant"""
    
    def __init__(self, root):
        """Initialize the GUI"""
        self.root = root
        self.root.title("CFD Workflow Assistant")
        self.root.geometry("1000x700")
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Create main tab
        self.main_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.main_tab, text="Main")
        
        # Create content in main tab
        self.create_main_tab()
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief="sunken", anchor="w")
        self.status_bar.pack(side="bottom", fill="x")
        
        # Additional initialization
        self.initialize_themes()
        
        print("WorkflowGUI initialized successfully")
        
    def create_main_tab(self):
        """Create the main tab content"""
        # Welcome message
        welcome_frame = ttk.Frame(self.main_tab, padding=20)
        welcome_frame.pack(fill="both", expand=True)
        
        ttk.Label(welcome_frame, text="Welcome to CFD Workflow Assistant", 
                 font=("Arial", 16, "bold")).pack(pady=(0, 20))
        
        ttk.Label(welcome_frame, text="This tool helps you set up and run CFD simulations.").pack()
        
        # Settings section
        settings_frame = ttk.LabelFrame(welcome_frame, text="Settings")
        settings_frame.pack(fill="x", padx=20, pady=20)
        
        # Theme settings
        theme_frame = ttk.Frame(settings_frame)
        theme_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Label(theme_frame, text="Theme:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.theme_combo = ttk.Combobox(theme_frame, values=["Default", "Dark"])
        self.theme_combo.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.theme_combo.current(0)
        self.theme_combo.bind("<<ComboboxSelected>>", lambda e: self.change_theme())
        
        # Workflow section
        workflow_frame = ttk.LabelFrame(welcome_frame, text="Workflow Steps")
        workflow_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.workflow_canvas = tk.Canvas(workflow_frame, height=150)
        self.workflow_canvas.pack(fill="both", expand=True, padx=10, pady=10)
        
        self._create_workflow_steps()
        
    def initialize_themes(self):
        """Initialize theme settings"""
        self.themes = {
            "Default": {
                "bg": "#f0f0f0",
                "fg": "#000000",
                "accent": "#007acc"
            },
            "Dark": {
                "bg": "#2d2d2d",
                "fg": "#ffffff",
                "accent": "#007acc"
            }
        }
    
    def change_theme(self):
        """Change the application theme"""
        theme_name = self.theme_combo.get()
        theme = self.themes.get(theme_name, self.themes["Default"])
        
        style = ttk.Style()
        if theme_name == "Dark":
            self.root.configure(background=theme["bg"])
            style.configure(".", background=theme["bg"], foreground=theme["fg"])
            style.configure("TLabel", background=theme["bg"], foreground=theme["fg"])
            style.configure("TFrame", background=theme["bg"])
            style.configure("TButton", background=theme["accent"])
            style.configure("TNotebook", background=theme["bg"])
            style.map("TNotebook.Tab", background=[("selected", theme["accent"])])
        else:
            style.theme_use("default")
            
        self.status_var.set(f"Theme changed to {theme_name}")
    
    def _create_workflow_steps(self):
        """Create visual workflow steps"""
        self.workflow_steps = [
            {"name": "NX Model", "status": "pending"},
            {"name": "Mesh", "status": "pending"},
            {"name": "CFD", "status": "pending"},
            {"name": "Results", "status": "pending"}
        ]
        
        # Draw workflow steps
        x_offset = 50
        for i, step in enumerate(self.workflow_steps):
            # Draw circle
            x = x_offset + i * 200
            y = 75
            circle_id = self.workflow_canvas.create_oval(x-30, y-30, x+30, y+30, 
                                                      fill="#f0f0f0", outline="#007acc", width=2)
            # Draw text
            text_id = self.workflow_canvas.create_text(x, y, text=step["name"])
            
            # Store IDs in the step dict
            step["circle_id"] = circle_id
            step["text_id"] = text_id
            
            # Draw connecting line if not the first step
            if i > 0:
                prev_x = x_offset + (i-1) * 200 + 30
                line_id = self.workflow_canvas.create_line(prev_x, y, x-30, y, 
                                                        fill="#007acc", width=2)
                step["line_id"] = line_id
    
    def update_step_status(self, step_index, status):
        """Update the status of a workflow step"""
        if step_index < 0 or step_index >= len(self.workflow_steps):
            return
            
        step = self.workflow_steps[step_index]
        step["status"] = status
        
        # Update visual representation
        color = "#f0f0f0"  # default
        if status == "complete":
            color = "#4caf50"  # green
        elif status == "active":
            color = "#2196f3"  # blue
        elif status == "error":
            color = "#f44336"  # red
            
        self.workflow_canvas.itemconfig(step["circle_id"], fill=color)

    def setup_hpc_tab(self):
        """Set up the HPC tab if not already created"""
        # Check if HPC tab already exists
        for tab_id in self.notebook.tabs():
            if self.notebook.tab(tab_id, "text") == "HPC":
                return  # Tab already exists
        
        # Create HPC tab
        self.hpc_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.hpc_tab, text="HPC")
        
        # Create content in HPC tab
        self.create_hpc_tab_content()
        
    def create_hpc_tab_content(self):
        """Create the HPC tab content"""
        # HPC Connection settings
        settings_frame = ttk.LabelFrame(self.hpc_tab, text="HPC Connection Settings")
        settings_frame.pack(fill="x", padx=20, pady=20)
        
        # HPC Host
        host_frame = ttk.Frame(settings_frame)
        host_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(host_frame, text="HPC Host:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.hpc_host = ttk.Entry(host_frame, width=30)
        self.hpc_host.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # Username
        ttk.Label(host_frame, text="Username:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.hpc_username = ttk.Entry(host_frame, width=30)
        self.hpc_username.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        # Port
        ttk.Label(host_frame, text="Port:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.hpc_port = ttk.Entry(host_frame, width=10)
        self.hpc_port.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        self.hpc_port.insert(0, "22")
        
        # Remote directory
        ttk.Label(host_frame, text="Remote Directory:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.hpc_remote_dir = ttk.Entry(host_frame, width=40)
        self.hpc_remote_dir.grid(row=3, column=1, padx=5, pady=5, sticky="w")
        
        # Authentication
        auth_frame = ttk.Frame(settings_frame)
        auth_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Label(auth_frame, text="Authentication:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.auth_method = tk.StringVar(value="password")
        ttk.Radiobutton(auth_frame, text="Password", variable=self.auth_method, value="password").grid(row=0, column=1, padx=5, pady=5, sticky="w")
        ttk.Radiobutton(auth_frame, text="SSH Key", variable=self.auth_method, value="key").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        
        # SSH Key path
        ttk.Label(auth_frame, text="SSH Key Path:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.key_path = ttk.Entry(auth_frame, width=40)
        self.key_path.grid(row=1, column=1, columnspan=2, padx=5, pady=5, sticky="w")
        
        # Button frame
        button_frame = ttk.Frame(settings_frame)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Button(button_frame, text="Test Connection", command=self.test_connection).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Save Settings", command=self.save_hpc_profiles).pack(side="left", padx=5)
        
        # Load settings
        self.load_hpc_profiles()
    
    def load_hpc_profiles(self):
        """Load HPC settings from config file"""
        try:
            import workflow_utils
            if hasattr(workflow_utils, 'load_hpc_profiles'):
                settings = workflow_utils.load_hpc_profiles()
                
                if hasattr(self, 'hpc_host'):
                    self.hpc_host.delete(0, tk.END)
                    self.hpc_host.insert(0, settings.get("hpc_host", ""))
                
                if hasattr(self, 'hpc_username'):
                    self.hpc_username.delete(0, tk.END)
                    self.hpc_username.insert(0, settings.get("hpc_username", ""))
                
                if hasattr(self, 'hpc_port'):
                    self.hpc_port.delete(0, tk.END)
                    self.hpc_port.insert(0, str(settings.get("hpc_port", 22)))
                
                if hasattr(self, 'hpc_remote_dir'):
                    self.hpc_remote_dir.delete(0, tk.END)
                    self.hpc_remote_dir.insert(0, settings.get("hpc_remote_dir", ""))
                
                if hasattr(self, 'auth_method'):
                    self.auth_method.set("key" if settings.get("use_key_auth", False) else "password")
                
                if hasattr(self, 'key_path'):
                    self.key_path.delete(0, tk.END)
                    self.key_path.insert(0, settings.get("key_path", ""))
            else:
                print("Warning: load_hpc_profiles function not found in workflow_utils")
        except Exception as e:
            print(f"Error loading HPC settings: {e}")
    
    def save_hpc_profiles(self):
        """Save HPC settings to config file"""
        try:
            settings = {
                "hpc_enabled": True,
                "hpc_host": self.hpc_host.get(),
                "hpc_username": self.hpc_username.get(),
                "hpc_port": int(self.hpc_port.get()),
                "hpc_remote_dir": self.hpc_remote_dir.get(),
                "use_key_auth": self.auth_method.get() == "key",
                "key_path": self.key_path.get(),
                "visible_in_gui": True
            }
            
            config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config")
            os.makedirs(config_dir, exist_ok=True)
            
            settings_file = os.path.join(config_dir, "hpc_profiles.json")
            with open(settings_file, 'w') as f:
                json.dump(settings, f, indent=4)
            
            messagebox.showinfo("Settings Saved", "HPC settings saved successfully")
            self.status_var.set("HPC settings saved")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save HPC settings: {str(e)}")
    
    def test_connection(self):
        """Test connection to HPC"""
        try:
            host = self.hpc_host.get()
            username = self.hpc_username.get()
            port = int(self.hpc_port.get())
            auth_method = self.auth_method.get()
            key_path = self.key_path.get() if auth_method == "key" else None
            
            # Try to import paramiko
            try:
                import paramiko
            except ImportError:
                messagebox.showerror("Missing Dependency", 
                                    "The paramiko module is required for SSH connections.\n"
                                    "Install it with: pip install paramiko")
                return
                
            self.status_var.set("Testing connection...")
            
            # Define a function to test the connection in a separate thread
            def do_test_connection():
                try:
                    client = paramiko.SSHClient()
                    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    
                    if auth_method == "key" and key_path:
                        key = paramiko.RSAKey.from_private_key_file(key_path)
                        client.connect(hostname=host, port=port, username=username, pkey=key, timeout=10)
                    else:
                        # For password auth, this will trigger a password prompt
                        # which we can't handle in a background thread
                        messagebox.showinfo("Password Required", 
                                         "Password authentication requires interactive input.\n"
                                         "This test will only check if the host is reachable.")
                        import socket
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.settimeout(5)
                        result = sock.connect_ex((host, port))
                        sock.close()
                        
                        if result != 0:
                            raise Exception(f"Could not connect to {host}:{port}")
                        return
                    
                    # Run a simple command
                    stdin, stdout, stderr = client.exec_command("hostname")
                    result = stdout.read().decode().strip()
                    
                    # Update GUI from main thread
                    self.root.after(0, lambda: messagebox.showinfo("Connection Success", 
                                                                f"Connected to HPC system: {result}"))
                    self.root.after(0, lambda: self.status_var.set(f"Connected to {result}"))
                    
                    # Close connection
                    client.close()
                except Exception as e:
                    # Update GUI from main thread
                    self.root.after(0, lambda: messagebox.showerror("Connection Error", 
                                                                  f"Failed to connect to HPC: {str(e)}"))
                    self.root.after(0, lambda: self.status_var.set("Connection failed"))
            
            # Start the connection test in a separate thread
            threading.Thread(target=do_test_connection, daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error setting up connection test: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = WorkflowGUI(root)
    root.mainloop()