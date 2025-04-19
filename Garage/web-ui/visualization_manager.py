import reactpy as rp
import numpy as np
import math

class Visualization_Manager:
    """Manages visualization of CFD results for the web interface"""
    
    def __init__(self):
        """Initialize the visualization manager"""
        self.visualization_data = {
            'X': None,
            'Y': None,
            'Z': None,
            'Pressure': None,
            'Velocity': None,
            'Temperature': None,
            'Turbulence': None
        }
        self.current_field = "Pressure"
        self.color_map = "viridis"
        self.auto_range = True
        self.min_value = 0.0
        self.max_value = 1.0
        self.show_grid = True
        self.show_colorbar = True
        
    def set_data(self, data):
        """Set the visualization data"""
        if data:
            self.visualization_data.update(data)
            
            # Calculate min/max for auto-range
            if self.current_field in data and data[self.current_field] is not None:
                field_data = data[self.current_field]
                if isinstance(field_data, list):
                    flat_data = [item for sublist in field_data for item in sublist]
                    self.min_value = min(flat_data)
                    self.max_value = max(flat_data)
    
    def get_statistics(self, field=None):
        """Get statistics for the current field"""
        field = field or self.current_field
        
        stats = {
            'min': None,
            'max': None,
            'mean': None,
            'median': None,
            'std': None
        }
        
        if field in self.visualization_data and self.visualization_data[field] is not None:
            try:
                data = self.visualization_data[field]
                if isinstance(data, list):
                    # Convert list to numpy array for statistics
                    data_array = np.array(data)
                    stats['min'] = float(np.min(data_array))
                    stats['max'] = float(np.max(data_array))
                    stats['mean'] = float(np.mean(data_array))
                    stats['median'] = float(np.median(data_array))
                    stats['std'] = float(np.std(data_array))
            except Exception as e:
                print(f"Error computing statistics: {str(e)}")
                
        return stats
    
    def render(self):
        """Render the visualization manager UI"""
        # Create tabs for different visualization sections
        tabs = self._create_tabs()
        
        # Create the control panel for visualization settings
        control_panel = self._create_control_panel()
        
        # Create the main layout with control panel and visualization area
        layout = rp.html.div(
            {"className": "visualization-container"},
            [
                rp.html.div(
                    {"className": "visualization-header"},
                    rp.html.h2("CFD Results Visualization")
                ),
                rp.html.div(
                    {"className": "visualization-content"},
                    [
                        rp.html.div(
                            {"className": "control-panel"},
                            control_panel
                        ),
                        rp.html.div(
                            {"className": "visualization-panel"},
                            tabs
                        )
                    ]
                )
            ]
        )
        
        return layout
    
    def _create_tabs(self):
        """Create tabs for different visualization types"""
        # Create tab buttons
        tab_buttons = rp.html.div(
            {"className": "tab-buttons"},
            [
                rp.html.button(
                    {
                        "className": "tab-button active",
                        "id": "cfd-results-tab",
                        "onClick": lambda e: self._select_tab("cfd-results")
                    },
                    "CFD Results"
                ),
                rp.html.button(
                    {
                        "className": "tab-button",
                        "id": "3d-view-tab",
                        "onClick": lambda e: self._select_tab("3d-view")
                    },
                    "3D View"
                ),
                rp.html.button(
                    {
                        "className": "tab-button",
                        "id": "statistics-tab",
                        "onClick": lambda e: self._select_tab("statistics")
                    },
                    "Statistics"
                ),
                rp.html.button(
                    {
                        "className": "tab-button",
                        "id": "comparison-tab",
                        "onClick": lambda e: self._select_tab("comparison")
                    },
                    "Comparison"
                )
            ]
        )
        
        # Create tab content for each tab
        tab_content = rp.html.div(
            {"className": "tab-content"},
            [
                self._create_cfd_results_tab(),
                self._create_3d_view_tab(),
                self._create_statistics_tab(),
                self._create_comparison_tab()
            ]
        )
        
        return rp.html.div(
            {"className": "tabs-container"},
            [tab_buttons, tab_content]
        )
    
    def _create_cfd_results_tab(self):
        """Create the CFD results tab content"""
        # Check if we have visualization data
        if (not self.visualization_data['X'] or 
            not self.visualization_data['Y'] or 
            not self.visualization_data[self.current_field]):
            # Show placeholder if no data
            return rp.html.div(
                {
                    "className": "tab-pane active",
                    "id": "cfd-results"
                },
                [
                    rp.html.div(
                        {"className": "no-data-placeholder"},
                        [
                            rp.html.p("No visualization data available."),
                            rp.html.p("Run a simulation workflow to generate results.")
                        ]
                    )
                ]
            )
        
        # In a real application, we would render a contour plot or other visualization here
        # For this demo, we'll just show a placeholder representation of the data
        return rp.html.div(
            {
                "className": "tab-pane active",
                "id": "cfd-results"
            },
            [
                rp.html.div(
                    {"className": "result-visualization"},
                    [
                        rp.html.h3(f"{self.current_field} Visualization"),
                        rp.html.div(
                            {"className": "viz-placeholder"},
                            f"Visualization for {self.current_field} would be rendered here using a plotting library."
                        ),
                        rp.html.div(
                            {"className": "field-info"},
                            [
                                rp.html.p(f"Field: {self.current_field}"),
                                rp.html.p(f"Color Map: {self.color_map}"),
                                rp.html.p(f"Range: {self.min_value:.4f} to {self.max_value:.4f}")
                            ]
                        )
                    ]
                )
            ]
        )
    
    def _create_3d_view_tab(self):
        """Create the 3D view tab content"""
        return rp.html.div(
            {
                "className": "tab-pane",
                "id": "3d-view"
            },
            [
                rp.html.h3("3D Visualization"),
                rp.html.div(
                    {"className": "threejs-container"},
                    "3D visualization would be rendered here using Three.js or a similar library."
                ),
                rp.html.div(
                    {"className": "view-controls"},
                    [
                        rp.html.div(
                            {"className": "control-group"},
                            [
                                rp.html.label({"htmlFor": "elevation"}, "Elevation:"),
                                rp.html.input({
                                    "type": "range",
                                    "id": "elevation",
                                    "min": 0,
                                    "max": 90,
                                    "value": 30,
                                    "className": "slider"
                                })
                            ]
                        ),
                        rp.html.div(
                            {"className": "control-group"},
                            [
                                rp.html.label({"htmlFor": "azimuth"}, "Azimuth:"),
                                rp.html.input({
                                    "type": "range",
                                    "id": "azimuth",
                                    "min": 0,
                                    "max": 360,
                                    "value": 45,
                                    "className": "slider"
                                })
                            ]
                        )
                    ]
                )
            ]
        )
    
    def _create_statistics_tab(self):
        """Create the statistics tab content"""
        # Get statistics for the current field
        stats = self.get_statistics()
        
        # Create a statistics table
        stats_table = rp.html.table(
            {"className": "stats-table"},
            [
                rp.html.thead(
                    rp.html.tr([
                        rp.html.th("Statistic"),
                        rp.html.th("Value")
                    ])
                ),
                rp.html.tbody([
                    rp.html.tr([
                        rp.html.td("Minimum"),
                        rp.html.td(f"{stats['min']:.6f}" if stats['min'] is not None else "N/A")
                    ]),
                    rp.html.tr([
                        rp.html.td("Maximum"),
                        rp.html.td(f"{stats['max']:.6f}" if stats['max'] is not None else "N/A")
                    ]),
                    rp.html.tr([
                        rp.html.td("Mean"),
                        rp.html.td(f"{stats['mean']:.6f}" if stats['mean'] is not None else "N/A")
                    ]),
                    rp.html.tr([
                        rp.html.td("Median"),
                        rp.html.td(f"{stats['median']:.6f}" if stats['median'] is not None else "N/A")
                    ]),
                    rp.html.tr([
                        rp.html.td("Standard Deviation"),
                        rp.html.td(f"{stats['std']:.6f}" if stats['std'] is not None else "N/A")
                    ])
                ])
            ]
        )
        
        return rp.html.div(
            {
                "className": "tab-pane",
                "id": "statistics"
            },
            [
                rp.html.h3(f"Statistics for {self.current_field}"),
                stats_table,
                rp.html.div(
                    {"className": "export-section"},
                    [
                        rp.html.button(
                            {
                                "className": "export-button",
                                "onClick": lambda e: self._export_statistics()
                            },
                            "Export Statistics"
                        )
                    ]
                )
            ]
        )
    
    def _create_comparison_tab(self):
        """Create the comparison tab content"""
        return rp.html.div(
            {
                "className": "tab-pane",
                "id": "comparison"
            },
            [
                rp.html.h3("Comparison View"),
                rp.html.div(
                    {"className": "comparison-controls"},
                    [
                        rp.html.div(
                            {"className": "comparison-select"},
                            [
                                rp.html.label({"htmlFor": "dataset1"}, "Dataset 1:"),
                                rp.html.select(
                                    {
                                        "id": "dataset1",
                                        "className": "select-input"
                                    },
                                    [
                                        rp.html.option({"value": "current"}, "Current Results")
                                    ]
                                )
                            ]
                        ),
                        rp.html.div(
                            {"className": "comparison-select"},
                            [
                                rp.html.label({"htmlFor": "dataset2"}, "Dataset 2:"),
                                rp.html.select(
                                    {
                                        "id": "dataset2",
                                        "className": "select-input"
                                    },
                                    [
                                        rp.html.option({"value": "none"}, "Select Dataset...")
                                    ]
                                )
                            ]
                        ),
                        rp.html.button(
                            {
                                "className": "compare-button",
                                "disabled": True
                            },
                            "Compare"
                        )
                    ]
                ),
                rp.html.div(
                    {"className": "comparison-placeholder"},
                    "Select two datasets to compare and click 'Compare'"
                )
            ]
        )
    
    def _create_control_panel(self):
        """Create the control panel for visualization settings"""
        # Field selection
        field_selector = rp.html.div(
            {"className": "control-section"},
            [
                rp.html.h3("Field Selection"),
                rp.html.select(
                    {
                        "className": "select-input",
                        "value": self.current_field,
                        "onChange": lambda e: self._set_field(e["target"]["value"])
                    },
                    [
                        rp.html.option({"value": "Pressure"}, "Pressure"),
                        rp.html.option({"value": "Velocity"}, "Velocity"),
                        rp.html.option({"value": "Temperature"}, "Temperature"),
                        rp.html.option({"value": "Turbulence"}, "Turbulence")
                    ]
                )
            ]
        )
        
        # Appearance controls
        appearance_controls = rp.html.div(
            {"className": "control-section"},
            [
                rp.html.h3("Appearance"),
                rp.html.div(
                    {"className": "control-group"},
                    [
                        rp.html.label({"htmlFor": "colormap"}, "Color Map:"),
                        rp.html.select(
                            {
                                "id": "colormap",
                                "className": "select-input",
                                "value": self.color_map,
                                "onChange": lambda e: self._set_colormap(e["target"]["value"])
                            },
                            [
                                rp.html.option({"value": "viridis"}, "Viridis"),
                                rp.html.option({"value": "plasma"}, "Plasma"),
                                rp.html.option({"value": "inferno"}, "Inferno"),
                                rp.html.option({"value": "magma"}, "Magma"),
                                rp.html.option({"value": "cividis"}, "Cividis"),
                                rp.html.option({"value": "cool"}, "Cool"),
                                rp.html.option({"value": "hot"}, "Hot"),
                                rp.html.option({"value": "jet"}, "Jet")
                            ]
                        )
                    ]
                ),
                rp.html.div(
                    {"className": "control-group"},
                    [
                        rp.html.label({}, "Range:"),
                        rp.html.div(
                            {"className": "checkbox-group"},
                            [
                                rp.html.input({
                                    "type": "checkbox",
                                    "id": "auto-range",
                                    "checked": self.auto_range,
                                    "onChange": lambda e: self._toggle_auto_range(e["target"]["checked"])
                                }),
                                rp.html.label({"htmlFor": "auto-range"}, "Auto Range")
                            ]
                        )
                    ]
                )
            ]
        )
        
        # Range controls (only shown when auto-range is off)
        range_controls = rp.html.div(
            {"className": "control-section", "style": {"display": "none" if self.auto_range else "block"}},
            [
                rp.html.div(
                    {"className": "control-group"},
                    [
                        rp.html.label({"htmlFor": "min-value"}, "Min Value:"),
                        rp.html.input({
                            "type": "number",
                            "id": "min-value",
                            "className": "number-input",
                            "value": self.min_value,
                            "step": "0.01",
                            "onChange": lambda e: self._set_min_value(e["target"]["value"])
                        })
                    ]
                ),
                rp.html.div(
                    {"className": "control-group"},
                    [
                        rp.html.label({"htmlFor": "max-value"}, "Max Value:"),
                        rp.html.input({
                            "type": "number",
                            "id": "max-value",
                            "className": "number-input",
                            "value": self.max_value,
                            "step": "0.01",
                            "onChange": lambda e: self._set_max_value(e["target"]["value"])
                        })
                    ]
                )
            ]
        )
        
        # Display options
        display_options = rp.html.div(
            {"className": "control-section"},
            [
                rp.html.h3("Display Options"),
                rp.html.div(
                    {"className": "checkbox-group"},
                    [
                        rp.html.input({
                            "type": "checkbox",
                            "id": "show-grid",
                            "checked": self.show_grid,
                            "onChange": lambda e: self._toggle_grid(e["target"]["checked"])
                        }),
                        rp.html.label({"htmlFor": "show-grid"}, "Show Grid")
                    ]
                ),
                rp.html.div(
                    {"className": "checkbox-group"},
                    [
                        rp.html.input({
                            "type": "checkbox",
                            "id": "show-colorbar",
                            "checked": self.show_colorbar,
                            "onChange": lambda e: self._toggle_colorbar(e["target"]["checked"])
                        }),
                        rp.html.label({"htmlFor": "show-colorbar"}, "Show Colorbar")
                    ]
                )
            ]
        )
        
        # Action buttons
        action_buttons = rp.html.div(
            {"className": "control-section"},
            [
                rp.html.h3("Actions"),
                rp.html.button(
                    {
                        "className": "action-button",
                        "onClick": lambda e: self._export_image()
                    },
                    "Export Image"
                ),
                rp.html.button(
                    {
                        "className": "action-button",
                        "onClick": lambda e: self._export_data()
                    },
                    "Export Data"
                )
            ]
        )
        
        return [field_selector, appearance_controls, range_controls, display_options, action_buttons]
    
    def _select_tab(self, tab_id):
        """Handle tab selection - this would be implemented with proper state management in a real app"""
        print(f"Selected tab: {tab_id}")
        # In a real application, we would update the UI to show the selected tab
        
    def _set_field(self, field_name):
        """Set the current field for visualization"""
        self.current_field = field_name
        print(f"Field set to: {field_name}")
        
        # Update min/max values for auto-range
        if self.auto_range and field_name in self.visualization_data and self.visualization_data[field_name] is not None:
            stats = self.get_statistics(field_name)
            if stats['min'] is not None and stats['max'] is not None:
                self.min_value = stats['min']
                self.max_value = stats['max']
    
    def _set_colormap(self, colormap):
        """Set the colormap for visualization"""
        self.color_map = colormap
        print(f"Colormap set to: {colormap}")
    
    def _toggle_auto_range(self, auto_range):
        """Toggle auto-range for visualization"""
        self.auto_range = auto_range
        print(f"Auto-range set to: {auto_range}")
        
        # Update min/max values if auto-range is turned on
        if auto_range and self.current_field in self.visualization_data:
            stats = self.get_statistics()
            if stats['min'] is not None and stats['max'] is not None:
                self.min_value = stats['min']
                self.max_value = stats['max']
    
    def _set_min_value(self, value):
        """Set the minimum value for visualization range"""
        try:
            self.min_value = float(value)
            print(f"Min value set to: {self.min_value}")
        except ValueError:
            print(f"Invalid min value: {value}")
    
    def _set_max_value(self, value):
        """Set the maximum value for visualization range"""
        try:
            self.max_value = float(value)
            print(f"Max value set to: {self.max_value}")
        except ValueError:
            print(f"Invalid max value: {value}")
    
    def _toggle_grid(self, show_grid):
        """Toggle grid display in visualization"""
        self.show_grid = show_grid
        print(f"Show grid set to: {show_grid}")
    
    def _toggle_colorbar(self, show_colorbar):
        """Toggle colorbar display in visualization"""
        self.show_colorbar = show_colorbar
        print(f"Show colorbar set to: {show_colorbar}")
    
    def _export_image(self):
        """Export the current visualization as an image"""
        print("Export image requested")
        # In a real application, we would generate and download an image
    
    def _export_data(self):
        """Export the current visualization data"""
        print("Export data requested")
        # In a real application, we would export the data as CSV or similar
    
    def _export_statistics(self):
        """Export statistics for the current field"""
        print("Export statistics requested")
        # In a real application, we would generate and download statistics
