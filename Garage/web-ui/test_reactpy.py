"""
Minimal standalone ReactPy application to test if the setup is working correctly.
"""
import reactpy as rp
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn
import os

def minimal_app():
    """Create a minimal React application to verify ReactPy is working"""
    return rp.html.div(
        {
            "style": {
                "fontFamily": "sans-serif",
                "maxWidth": "800px",
                "margin": "40px auto",
                "padding": "20px",
                "background": "#f5f5f5",
                "border": "1px solid #ddd",
                "borderRadius": "8px"
            }
        },
        [
            rp.html.h1(
                {"style": {"color": "#4a6fa5"}},
                "ReactPy Test Page"
            ),
            rp.html.p(
                {"style": {"fontSize": "18px"}},
                "If you can see this text, ReactPy is working correctly!"
            ),
            rp.html.button(
                {
                    "style": {
                        "background": "#4a6fa5",
                        "color": "white",
                        "border": "none",
                        "padding": "8px 16px",
                        "borderRadius": "4px",
                        "cursor": "pointer",
                        "marginTop": "20px"
                    },
                    "onClick": lambda e: print("Button clicked!")
                },
                "Click Me"
            )
        ]
    )

def main():
    # Create a FastAPI app
    app = FastAPI()
    
    # Define a simple HTML template
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>ReactPy Test</title>
    </head>
    <body>
        <div id="root"></div>
    </body>
    </html>
    """
    
    # Configure ReactPy with FastAPI
    from reactpy.backend.fastapi import configure
    configure(app, minimal_app)
    
    # Add a route for the main page
    @app.get("/", response_class=HTMLResponse)
    async def get_index():
        return html_template
    
    # Run the server
    print("Starting test server on http://0.0.0.0:8050")
    print("Try accessing http://localhost:8050 in your browser")
    uvicorn.run(app, host="0.0.0.0", port=8050)

if __name__ == "__main__":
    main()