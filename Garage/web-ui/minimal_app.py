"""
Minimal standalone ReactPy application with inline styling.
This deliberately avoids external files, CSS, or complex components
to provide a baseline that should work in any environment.
"""
import reactpy as rp
from fastapi import FastAPI
import uvicorn

def minimal_app():
    """Create an absolutely minimal React application"""
    return rp.html.div(
        {
            "style": {
                "fontFamily": "sans-serif",
                "maxWidth": "800px",
                "margin": "0 auto",
                "backgroundColor": "#f5f5f5",
                "padding": "20px",
                "borderRadius": "8px",
                "boxShadow": "0 2px 4px rgba(0,0,0,0.1)"
            }
        },
        [
            rp.html.h1(
                {"style": {"color": "#4a6fa5"}},
                "CFD Intake Project (Minimal Test)"
            ),
            rp.html.p(
                {"style": {"fontSize": "18px"}},
                "If you can see this text, ReactPy rendering is working correctly!"
            ),
            rp.html.div(
                {"style": {"marginTop": "20px"}},
                [
                    rp.html.button(
                        {
                            "style": {
                                "backgroundColor": "#4a6fa5",
                                "color": "white",
                                "padding": "10px 15px",
                                "border": "none",
                                "borderRadius": "4px",
                                "cursor": "pointer"
                            },
                            "onClick": lambda e: print("Button clicked!")
                        },
                        "Test Button"
                    )
                ]
            )
        ]
    )

def main():
    print("Starting minimal ReactPy test application...")
    print("This application uses only ReactPy and FastAPI with no external dependencies")
    
    # Create a FastAPI application
    app = FastAPI()
    
    # Configure ReactPy with FastAPI
    from reactpy.backend.fastapi import configure
    configure(app, minimal_app)
    
    # Run the server
    print("\nStarting server on http://localhost:8050")
    print("Try accessing this URL in your web browser")
    print("If you see content, then ReactPy is working correctly")
    print("If not, check your browser's developer console (F12) for errors\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8050)

if __name__ == "__main__":
    main()