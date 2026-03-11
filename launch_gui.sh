#!/bin/bash

# Morphometric Classification GUI Launcher
# Simple script to launch the PyQt6 GUI application

set -e

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "=========================================="
echo "Morphometric Classification GUI Launcher"
echo "=========================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed."
    echo "Please install Python 3.9 or higher from https://www.python.org"
    exit 1
fi

# Get Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Found Python: $PYTHON_VERSION"

# Check if the GUI script exists
if [ ! -f "$SCRIPT_DIR/morphometrics_gui.py" ]; then
    echo "ERROR: morphometrics_gui.py not found in $SCRIPT_DIR"
    exit 1
fi

echo "✓ Found GUI script: morphometrics_gui.py"
echo ""

# Check if requirements are installed
echo "Checking dependencies..."
python3 -c "import PyQt6" 2>/dev/null || {
    echo "⚠ PyQt6 not installed. Installing dependencies..."
    pip install -r "$SCRIPT_DIR/requirements_gui.txt" || {
        echo "ERROR: Failed to install dependencies."
        echo "Try running manually: pip install -r requirements_gui.txt"
        exit 1
    }
}

echo "✓ All dependencies are available"
echo ""
echo "Launching Morphometric Classification GUI..."
echo ""

# Launch the GUI
cd "$SCRIPT_DIR"
python3 morphometrics_gui.py
