import sys
import os
import reactpy as rp
from reactpy.backend.fastapi import configure
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from workflow_manager import WorkflowManager
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from visualization_manager import Visualization_Manager
from optimization_manager import Optimization_Manager
from hpc_manager import HPC_Manager
from settings_manager import Settings_Manager
import json
import logging

class GUI:
    def __init__(self, workflow_manager=None):
        """Initialize the GUI with managers and connect to the workflow manager from main.py"""
        # Use provided workflow_manager or create a new one with the correct parameters
        if workflow_manager:
            self.workflow_manager = workflow_manager
        else:
            self.workflow_manager = WorkflowManager(logger=logging.getLogger("intake-cfd-web").info, demo_mode=True)
            
        # Add render method to workflow_manager
        self._add_render_to_workflow_manager()
            
        self.visualization_manager = Visualization_Manager()
        self.optimization_manager = Optimization_Manager()
        self.hpc_manager = HPC_Manager()
        self.settings_manager = Settings_Manager()
        
        # Setup logger
        self.logger = logging.getLogger("intake-cfd-web")
        
    def _add_render_to_workflow_manager(self):
        """Add a render method to the workflow manager if it doesn't have one"""
        if not hasattr(self.workflow_manager, 'render'):
            # Define a basic render method for WorkflowManager
            def render():
                steps = []
                for step in self.workflow_manager.workflow_steps:
                    steps.append(
                        rp.html.div(
                            {"className": f"workflow-step step-{step['status']}"},
                            [
                                rp.html.h3(step['name']),
                                rp.html.p(step.get('desc', '')),
                                rp.html.span({"className": "status-badge"}, step['status'])
                            ]
                        )
                    )
                
                return rp.html.div(
                    {"className": "workflow-component"},
                    [
                        rp.html.div({"className": "workflow-steps"}, steps),
                        rp.html.div(
                            {"className": "workflow-controls"},
                            [
                                rp.html.button(
                                    {
                                        "onClick": lambda e: self._run_workflow(),
                                        "disabled": self.workflow_manager.workflow_running
                                    },
                                    "Run Workflow"
                                ),
                                rp.html.button(
                                    {
                                        "onClick": lambda e: self.workflow_manager.cancel_workflow(),
                                        "disabled": not self.workflow_manager.workflow_running
                                    },
                                    "Cancel"
                                )
                            ]
                        )
                    ]
                )
            
            # Add the render method to the instance
            self.workflow_manager.render = render
            
    def _run_workflow(self):
        """Handle running the workflow with default parameters"""
        if not self.workflow_manager.workflow_running:
            default_params = {
                'L4': 3.0,
                'L5': 3.0,
                'alpha1': 15.0,
                'alpha2': 15.0,
                'alpha3': 15.0
            }
            
            # Start the workflow in a background thread
            import threading
            def run_workflow_thread():
                self.workflow_manager.run_workflow(default_params)
                
            thread = threading.Thread(target=run_workflow_thread)
            thread.daemon = True
            thread.start()
        
    def create_app(self):
        """Create the main React application structure"""
        return rp.html.div(
            {"className": "app-container"},
            [
                self.create_header(),
                self.create_main_content(),
                self.create_footer()
            ]
        )
    
    def create_header(self):
        """Create the application header"""
        return rp.html.header(
            {"className": "app-header"},
            [
                rp.html.h1("CFD Intake Project"),
                self.create_navigation()
            ]
        )
    
    def create_navigation(self):
        """Create the main navigation menu"""
        return rp.html.nav(
            {"className": "main-nav"},
            rp.html.ul([
                rp.html.li(rp.html.a({"href": "#workflow"}, "Workflow")),
                rp.html.li(rp.html.a({"href": "#visualization"}, "Visualization")),
                rp.html.li(rp.html.a({"href": "#optimization"}, "Optimization")),
                rp.html.li(rp.html.a({"href": "#hpc"}, "HPC")),
                rp.html.li(rp.html.a({"href": "#settings"}, "Settings"))
            ])
        )
    
    def create_main_content(self):
        """Create the main content area with different sections"""
        return rp.html.main(
            {"className": "main-content"},
            [
                self.create_workflow_section(),
                self.create_visualization_section(),
                self.create_optimization_section(),
                self.create_hpc_section(),
                self.create_settings_section()
            ]
        )
    
    def create_workflow_section(self):
        """Create the workflow management section"""
        return rp.html.section(
            {"id": "workflow", "className": "content-section"},
            [
                rp.html.h2("Workflow Management"),
                self.workflow_manager.render()
            ]
        )
    
    def create_visualization_section(self):
        """Create the visualization section"""
        return rp.html.section(
            {"id": "visualization", "className": "content-section"},
            [
                rp.html.h2("Visualization"),
                self.visualization_manager.render()
            ]
        )
    
    def create_optimization_section(self):
        """Create the optimization section"""
        return rp.html.section(
            {"id": "optimization", "className": "content-section"},
            [
                rp.html.h2("Optimization"),
                self.optimization_manager.render()
            ]
        )
    
    def create_hpc_section(self):
        """Create the HPC management section"""
        return rp.html.section(
            {"id": "hpc", "className": "content-section"},
            [
                rp.html.h2("HPC Management"),
                self.hpc_manager.render()
            ]
        )
    
    def create_settings_section(self):
        """Create the settings section"""
        return rp.html.section(
            {"id": "settings", "className": "content-section"},
            [
                rp.html.h2("Settings"),
                self.settings_manager.render()
            ]
        )
    
    def create_footer(self):
        """Create the application footer"""
        return rp.html.footer(
            {"className": "app-footer"},
            [
                rp.html.p("© 2023 CFD Intake Project")
            ]
        )
    
    def run(self, host="0.0.0.0", port=8000):
        """Run the application with proper FastAPI backend for production use"""
        self.logger.info(f"Starting CFD Intake web interface on {host}:{port}")
        
        try:
            # Create FastAPI app with minimal configuration
            app = FastAPI(title="CFD Intake Project")
            
            # Create a simple template without any ReactPy-specific elements
            index_html = """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <title>CFD Intake Project</title>
                <link rel="stylesheet" href="/static/css/styles.css">
            </head>
            <body>
                <div id="root"></div>
            </body>
            </html>
            """
            
            # Mount static files directory first
            static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
            if not os.path.exists(static_dir):
                os.makedirs(static_dir, exist_ok=True)
                
                # Create css directory if it doesn't exist
                css_dir = os.path.join(static_dir, "css")
                if not os.path.exists(css_dir):
                    os.makedirs(css_dir, exist_ok=True)
                    
                # Create a basic styles.css file if it doesn't exist
                css_file = os.path.join(css_dir, "styles.css")
                if not os.path.exists(css_file):
                    with open(css_file, "w") as f:
                        f.write("""
                        /* Basic styles for CFD Intake Project */
                        :root {
                          --primary-color: #4a6fa5;
                          --text-color: #333333;
                          --bg-color: #f5f5f5;
                        }
                        body {
                          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                          margin: 0;
                          padding: 0;
                          background-color: var(--bg-color);
                          color: var(--text-color);
                        }
                        .app-container {
                          display: flex;
                          flex-direction: column;
                          min-height: 100vh;
                        }
                        .app-header {
                          background-color: var(--primary-color);
                          color: white;
                          padding: 1rem;
                        }
                        """)
            
            self.logger.info(f"Mounting static files from {static_dir}")
            app.mount("/static", StaticFiles(directory=static_dir), name="static")
            
            # Configure ReactPy with FastAPI after mounting static files
            self.logger.info("Configuring ReactPy with FastAPI")
            configure(app, self.create_app())
            
            # Create a simple index route that serves our HTML
            @app.get("/", response_class=HTMLResponse)
            async def get_index():
                return index_html
            
            # Run the server
            import uvicorn
            self.logger.info(f"Server starting at http://{host}:{port}")
            self.logger.info(f"Access the application at http://localhost:{port}")
            uvicorn.run(app, host=host, port=port)
        except ImportError as e:
            self.logger.error(f"Import error: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Error starting server: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            raise