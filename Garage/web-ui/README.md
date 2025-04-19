# CFD Intake Design Tool - Web UI

This is a web-based interface for the CFD Intake Design Tool, which helps in designing and analyzing intake geometries.

## Features

- Design intake geometries with customizable parameters
- Visualize the intake in 3D
- Run CFD simulations on the designed intakes
- Export results and visualizations

## Installation

1. Make sure you have Python 3.6+ installed
2. Install required packages:
   ```
   pip install flask
   ```
3. For better performance, install gunicorn:
   ```
   pip install gunicorn
   ```

## Usage

### Running the application

For development:
```
python app.py
```

For production (recommended):
```
./run.sh
```

### Accessing the application

Open your browser and navigate to:
```
http://localhost:5000
```

### Performance optimization

If the application loads slowly, run the optimizer:
```
python optimize.py
```

## Files

- `app.py`: Main Flask application
- `optimize.py`: Performance diagnostics tool
- `run.sh`: Convenient startup script
- `templates/`: HTML templates for the web interface
- `static/`: CSS, JavaScript, and other static files

## Troubleshooting

### Slow loading times
- Try running with gunicorn instead of the Flask development server
- Check WSL I/O performance using the optimize.py script
- Ensure your project is on the Linux filesystem, not a Windows-mounted drive

### No visualization
- Make sure your browser supports WebGL
- Check the browser console for any JavaScript errors
