#!/usr/bin/env -S bash -c 'source ~/menv/bin/activate && exec "$0" "$@"'

# Runway Gen-4 Setup Script
echo "🎬 Runway Gen-4 Video Generation Setup"
echo "====================================="
echo

# Check if API key is already set
if [ -n "$RUNWAY_API_KEY" ]; then
    echo "✅ RUNWAY_API_KEY is already set"
    echo "🎬 Ready to generate videos!"
    echo
    echo "Run: python runway_generator.py"
else
    echo "🔑 RUNWAY_API_KEY not found"
    echo
    echo "📝 To set up Runway Gen-4 video generation:"
    echo
    echo "1. Get your API key:"
    echo "   🌐 Visit: https://app.runwayml.com/"
    echo "   📝 Sign up or log in"
    echo "   🔑 Go to Settings > API Keys"
    echo "   ➕ Create a new API key"
    echo
    echo "2. Set the API key:"
    echo "   export RUNWAY_API_KEY='your-api-key-here'"
    echo
    echo "3. Run the generator:"
    echo "   python runway_generator.py"
    echo
    echo "💡 You can also add the export to your ~/.zshrc to make it permanent"
    echo
fi

echo "📊 Current pipeline status:"
if [ -f "./outputs/video_prompts.csv" ]; then
    prompt_count=$(wc -l < "./outputs/video_prompts.csv")
    echo "   ✅ Video prompts ready: $((prompt_count - 1))"
else
    echo "   ❌ No video prompts found - run complete_pipeline.py first"
fi

if [ -f "./outputs/selected_images.csv" ]; then
    image_count=$(wc -l < "./outputs/selected_images.csv")
    echo "   ✅ Selected images ready: $((image_count - 1))"
else
    echo "   ❌ No selected images found - run complete_pipeline.py first"
fi

echo
echo "🚀 Ready to create amazing videos with AI!"

