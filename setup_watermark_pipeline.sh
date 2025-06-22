#!/bin/bash

echo "=== Fortuna Bound Watermark Pipeline Setup ==="

# Make sure we're in the right directory
if [ ! -f "watermark.py" ]; then
    echo "Error: Please run this script from the project root directory"
    exit 1
fi

# Check if watermark files exist
if [ ! -f "Fortuna_Bound_Watermark.png" ]; then
    echo "Warning: Fortuna_Bound_Watermark.png not found"
fi

if [ ! -f "Fortuna_Bound_Watermark_BW.png" ]; then
    echo "Warning: Fortuna_Bound_Watermark_BW.png not found"  
fi

# Make sure Python dependencies are available
echo "Checking Python dependencies..."
venv/bin/python -c "import PIL; print('✓ Pillow available')" || echo "✗ Pillow not available - install with: venv/bin/pip install Pillow"

# Create necessary directories
mkdir -p images/{pending,approved,rejected,selected_for_video,ranked}
mkdir -p video_outputs
mkdir -p uploads

# Make scripts executable
chmod +x auto_watermark_workflow.py
chmod +x pipeline_integration.py
chmod +x watermark.py

echo "=== Setup complete! ==="
echo ""
echo "Available commands:"
echo "  venv/bin/python auto_watermark_workflow.py --mode full    # Run complete workflow"
echo "  venv/bin/python auto_watermark_workflow.py --mode watermark # Just add watermarks"
echo "  venv/bin/python auto_watermark_workflow.py --mode cleanup   # Clean non-watermarked"
echo "  venv/bin/python app.py                                      # Start web interface"
echo ""
echo "Web interface will be available at: http://localhost:8080"
