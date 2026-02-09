#!/bin/bash

# Mela to Paprika Converter - Run Script

echo "🍳 Mela to Paprika Converter"
echo "=============================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is required but not installed."
    exit 1
fi

# Check if Flask is installed
if ! python3 -c "import flask" 2>/dev/null; then
    echo "📦 Installing dependencies..."
    pip3 install -r requirements.txt
    
    if [ $? -ne 0 ]; then
        echo "❌ Error: Failed to install dependencies."
        exit 1
    fi
fi

# Show configuration
echo ""
echo "Configuration:"
echo "  Max upload size: ${MAX_UPLOAD_MB:-500}MB"
echo "  Debug mode: enabled"
echo ""

echo "Starting web server..."
echo "Open your browser and go to: http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Run the Flask app
python3 app.py
