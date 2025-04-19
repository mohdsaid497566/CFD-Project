"""
Simple version of the CFD Intake application with minimal components
to help identify rendering issues.
"""
import reactpy as rp
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("simple-cfd-app")

def simple_app():
    """Create a simple React application with minimal components"""
    return rp.html.div(
        {"className": "app-container", "style": {"fontFamily": "Arial, sans-serif", "maxWidth": "1200px", "margin": "0 auto"}},
        [
            # Header
            rp.html.header(
                {"style": {"backgroundColor": "#4a6fa5", "color": "white", "padding": "1rem", "marginBottom": "1rem"}},
                rp.html.h1("Simple CFD Intake App")
            ),
            
            # Main content
            rp.html.div(
                {"style": {"padding": "1rem", "backgroundColor": "white", "borderRadius": "4px", "boxShadow": "0 2px 4px rgba(0,0,0,0.1)"}},
                [
                    rp.html.h2("Workflow Steps"),
                    # Simple workflow with a few steps
                    rp.html.div(
                        {"style": {"display": "flex", "gap": "10px", "marginBottom": "20px"}},
                        [
                            rp.html.div(
                                {"style": {"border": "1px solid #ddd", "borderRadius": "4px", "padding": "10px", "flex": "1"}},
                                [
                                    rp.html.h3("CAD"),
                                    rp.html.p("Updates the NX model with parameters")
                                ]
                            ),
                            rp.html.div(
                                {"style": {"border": "1px solid #ddd", "borderRadius": "4px", "padding": "10px", "flex": "1"}},
                                [
                                    rp.html.h3("Mesh"),
                                    rp.html.p("Generates mesh from geometry")
                                ]
                            ),
                            rp.html.div(
                                {"style": {"border": "1px solid #ddd", "borderRadius": "4px", "padding": "10px", "flex": "1"}},
                                [
                                    rp.html.h3("CFD"),
                                    rp.html.p("Runs CFD simulation")
                                ]
                            ),
                            rp.html.div(
                                {"style": {"border": "1px solid #ddd", "borderRadius": "4px", "padding": "10px", "flex": "1"}},
                                [
                                    rp.html.h3("Results"),
                                    rp.html.p("Processes simulation results")
                                ]
                            )
                        ]
                    ),
                    
                    # Simple button
                    rp.html.button(
                        {
                            "style": {
                                "backgroundColor": "#4a6fa5", 
                                "color": "white", 
                                "padding": "8px 16px", 
                                "border": "none",
                                "borderRadius": "4px",
                                "cursor": "pointer"
                            },
                            "onClick": lambda e: logger.info("Button clicked!")
                        },
                        "Run Workflow"
                    )
                ]
            ),
            
            # Footer
            rp.html.footer(
                {"style": {"marginTop": "2rem", "textAlign": "center", "color": "#666"}},
                rp.html.p("© 2025 Simple CFD App")
            )
        ]
    )

def main():
    """Run the application"""
    # Create FastAPI app
    app = FastAPI(title="Simple CFD App")
    
    # Create and mount a ReactPy component
    from reactpy.backend.fastapi import configure
    configure(app, simple_app)
    
    # Ensure static directory exists
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
    if not os.path.exists(static_dir):
        os.makedirs(static_dir, exist_ok=True)
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    
    # Run server
    logger.info("Starting simple CFD app on http://0.0.0.0:8070")
    uvicorn.run(app, host="0.0.0.0", port=8070)

if __name__ == "__main__":
    main()