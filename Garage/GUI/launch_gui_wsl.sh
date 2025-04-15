#!/bin/bash
# WSL GUI launcher script - auto-generated

# Export display settings
export DISPLAY=127.0.0.1:0.0
export LIBGL_ALWAYS_INDIRECT=1

# Detect VcXsrv or X410
if ps -ef | grep -i "vcxsrv\|x410" | grep -v grep > /dev/null; then
    echo "X server detected. Good!"
else
    echo "WARNING: No X server detected. Please start VcXsrv, X410, or another X server on Windows."
    echo "For VcXsrv, make sure to run with options: -ac -multiwindow -clipboard -wgl"
    echo "Continuing anyway in case the detection failed..."
fi

# Set better font rendering
export GDK_DPI_SCALE=1.0
export QT_SCALE_FACTOR=1.0

# Launch the GUI
cd "$(dirname "$0")"
echo "Launching patched GUI..."
python patch.py
