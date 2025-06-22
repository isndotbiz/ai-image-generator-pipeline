#!/bin/bash
# Video Generation Script
# Run this script after setting up Runway API key

echo "🎬 Generating 5 Videos from Top-Ranked Images..."
echo "================================================"

if [ -z "$RUNWAY_API_KEY" ]; then
    echo "❌ RUNWAY_API_KEY not set. Please run:"
    echo "   export RUNWAY_API_KEY='your-api-key-here'"
    exit 1
fi

echo "✅ Runway API key found"
echo "🚀 Starting video generation..."

# Use local virtual environment executables
# Alternative: source venv/bin/activate && python intelligent_video_generator.py --max-videos 5 --use-rankings
venv/bin/python intelligent_video_generator.py --max-videos 5 --use-rankings

echo "
🎉 Video generation complete!"
echo "📁 Check video_outputs/ directory for results"
