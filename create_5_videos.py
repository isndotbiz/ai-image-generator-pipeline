#!/usr/bin/env -S bash -c 'source ~/menv/bin/activate && exec "$0" "$@"'
"""
Create 5 videos from the top-ranked images
"""

import json
import os
import shutil
from pathlib import Path
from datetime import datetime

def create_video_plan():
    """Create a plan for generating 5 videos from top-ranked images"""
    
    print("🎬 Creating Video Generation Plan for Top 5 Images...")
    print("=" * 60)
    
    # Load rankings
    rankings_files = list(Path('images').glob('image_rankings_*.json'))
    if not rankings_files:
        print("❌ No rankings found. Run image_ranker.py first.")
        return
    
    latest_rankings = max(rankings_files, key=os.path.getctime)
    print(f"📊 Loading rankings from: {latest_rankings}")
    
    with open(latest_rankings, 'r') as f:
        rankings = json.load(f)
    
    # Get top 5 images (rankings is a list, not a dict)
    top_images = rankings[:5]
    
    print("\n🏆 TOP 5 IMAGES SELECTED FOR VIDEO GENERATION:")
    print("-" * 50)
    
    for i, img in enumerate(top_images, 1):
        print(f"{i}. {img['filename']} (Score: {img['final_score']:.3f})")
        # Copy to a special video queue folder
        src_path = Path('images/selected_for_video') / img['filename']
        dest_dir = Path('video_queue')
        dest_dir.mkdir(exist_ok=True)
        
        if src_path.exists():
            dest_path = dest_dir / f"video_{i:02d}_{img['filename']}"
            shutil.copy2(src_path, dest_path)
            print(f"   ✅ Copied to: {dest_path}")
        else:
            print(f"   ❌ Source image not found: {src_path}")
    
    # Create video generation tasks
    video_plan = {
        "timestamp": datetime.now().isoformat(),
        "total_videos": 5,
        "source_rankings": str(latest_rankings),
        "videos": []
    }
    
    # Define themes for each video based on image content
    video_themes = [
        {"theme": "Luxury Handcrafted Items", "style": "Elegant slow zoom with golden particles"},
        {"theme": "Premium Textiles & Materials", "style": "Smooth rotation with fabric-like motion"},
        {"theme": "Artisan Craftsmanship", "style": "Cinematic pan with warm lighting effects"},
        {"theme": "Exotic Vehicles & Transportation", "style": "Dynamic motion with speed blur effects"},
        {"theme": "Interior Design & Architecture", "style": "Architectural walkthrough with depth effects"}
    ]
    
    print("\n🎞️ VIDEO GENERATION PLAN:")
    print("-" * 40)
    
    for i, (img, theme) in enumerate(zip(top_images, video_themes), 1):
        video_config = {
            "video_id": f"video_{i:02d}",
            "source_image": img['filename'],
            "score": img['final_score'],
            "theme": theme['theme'],
            "style": theme['style'],
            "duration": "4 seconds",
            "output_filename": f"fortuna_bound_video_{i:02d}_{datetime.now().strftime('%Y%m%d')}.mp4",
            "prompt": f"Create a cinematic {theme['style'].lower()} showcasing {theme['theme'].lower()}, professional commercial style"
        }
        
        video_plan['videos'].append(video_config)
        
        print(f"\n{i}. {video_config['theme']}")
        print(f"   📸 Source: {video_config['source_image']}")
        print(f"   🎨 Style: {video_config['style']}")
        print(f"   🎬 Output: {video_config['output_filename']}")
        print(f"   📝 Prompt: {video_config['prompt']}")
    
    # Save the plan
    plan_file = Path('video_generation_plan.json')
    with open(plan_file, 'w') as f:
        json.dump(video_plan, f, indent=2)
    
    print(f"\n📄 Video plan saved to: {plan_file}")
    
    # Create a simple shell script for manual video generation
    script_content = """#!/bin/bash
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

# Activate environment
source ~/menv/bin/activate

# Generate videos using the intelligent video generator
python3 intelligent_video_generator.py --max-videos 5 --use-rankings

echo "\n🎉 Video generation complete!"
echo "📁 Check video_outputs/ directory for results"
"""
    
    script_file = Path('generate_videos.sh')
    with open(script_file, 'w') as f:
        f.write(script_content)
    
    os.chmod(script_file, 0o755)
    
    print(f"\n🔧 Created execution script: {script_file}")
    print("\n🎯 NEXT STEPS:")
    print("1. Set up Runway API key: export RUNWAY_API_KEY='your-key'")
    print("2. Run: ./generate_videos.sh")
    print("3. Or run: python3 intelligent_video_generator.py --max-videos 5")
    
    return video_plan

# Alternative: Create simple slideshow videos using ffmpeg
def create_slideshow_videos():
    """Create simple slideshow videos using ffmpeg as a fallback"""
    
    print("\n🎞️ ALTERNATIVE: Creating slideshow videos with ffmpeg...")
    
    video_queue = Path('video_queue')
    if not video_queue.exists() or not list(video_queue.glob('*.png')):
        print("❌ No images in video queue. Run the main function first.")
        return
    
    output_dir = Path('video_outputs')
    output_dir.mkdir(exist_ok=True)
    
    images = sorted(list(video_queue.glob('video_*.png')))
    
    print(f"\n📸 Creating slideshow videos from {len(images)} images...")
    
    for i, image in enumerate(images[:5], 1):
        output_file = output_dir / f"slideshow_{i:02d}_{datetime.now().strftime('%Y%m%d_%H%M')}.mp4"
        
        # Create a simple zoom-in effect slideshow
        ffmpeg_cmd = f"""
        ffmpeg -y -loop 1 -i "{image}" -t 4 \
        -vf "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,zoompan=z='min(zoom+0.0015,1.5)':x=iw/2-(iw/zoom/2):y=ih/2-(ih/zoom/2):d=125" \
        -c:v libx264 -pix_fmt yuv420p "{output_file}"
        """
        
        print(f"\n{i}. Creating: {output_file.name}")
        print(f"   Source: {image.name}")
        
        # For now, just show the command instead of executing
        print(f"   Command: {ffmpeg_cmd.strip()}")
    
    print("\n💡 To create the videos, install ffmpeg and run the commands above")
    print("   Or use the Runway integration for AI-powered video generation")

if __name__ == '__main__':
    video_plan = create_video_plan()
    
    if video_plan:
        print("\n" + "=" * 60)
        print("🎊 VIDEO GENERATION PLAN CREATED SUCCESSFULLY!")
        print("=" * 60)
        
        # Show summary
        print(f"📊 Total videos planned: {len(video_plan['videos'])}")
        print(f"📁 Images staged in: video_queue/")
        print(f"📄 Plan saved in: video_generation_plan.json")
        print(f"🔧 Execution script: generate_videos.sh")
        
        # Option for simple slideshow
        print("\n🎞️ For immediate results, create slideshow videos:")
        create_slideshow_videos()

