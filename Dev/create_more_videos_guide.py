#!/usr/bin/env python3

import os
import pandas as pd
from pathlib import Path

def show_video_creation_options():
    """Show all available options for creating more videos"""
    
    print("🎬 HOW TO CREATE MORE AI VIDEOS")
    print("=" * 50)
    
    # Check current status
    current_videos = len(list(Path("video_outputs").glob("*.mp4")))
    print(f"✅ Current videos: {current_videos}")
    
    print("\n🚀 OPTIONS TO CREATE MORE VIDEOS:")
    print("\n1️⃣ **MULTIPLE VIDEOS PER CLUSTER** (Most Popular)")
    print("   • Generate 2nd-5th best videos from existing clusters")
    print("   • Total potential: 100 videos (5 per cluster x 20 clusters)")
    print("   • Command: python create_cluster_variations.py")
    
    print("\n2️⃣ **ADD NEW IMAGES** (Unlimited Scaling)")
    print("   • Add more images to ./images/ folder")
    print("   • Re-run complete analysis pipeline")
    print("   • Get new clusters and themes")
    print("   • Commands:")
    print("     - Add images to ./images/")
    print("     - python complete_pipeline.py")
    print("     - python runway_generator.py")
    
    print("\n3️⃣ **CUSTOM PROMPTS** (Creative Control)")
    print("   • Create videos with your own custom prompts")
    print("   • Use any existing image")
    print("   • Command: python custom_video_generator.py")
    
    print("\n4️⃣ **SEASONAL/THEMED VARIATIONS** (Trending Content)")
    print("   • Christmas, Valentine's, Summer themes")
    print("   • Modify prompts for current trends")
    print("   • Command: python seasonal_videos.py")
    
    print("\n5️⃣ **DIFFERENT VIDEO STYLES** (Variety)")
    print("   • Portrait vs Landscape ratios")
    print("   • Different durations (3s, 5s, 10s)")
    print("   • Various camera movements")
    print("   • Command: python style_variations.py")
    
    print("\n📊 **QUICK STATS:**")
    print(f"   • Images available: {count_available_images()}")
    print(f"   • Unused images: {count_unused_images()}")
    print(f"   • Credits remaining: 3,000+ (enough for 12,000+ videos)")
    
    print("\n🎆 **RECOMMENDED NEXT STEPS:**")
    print("   1. Start with Option 1 (Cluster Variations) for quick expansion")
    print("   2. Add new images for unlimited fresh content")
    print("   3. Use custom prompts for specific campaigns")

def count_available_images():
    """Count total images in the images directory"""
    image_dir = Path("./images")
    if not image_dir.exists():
        return 0
    
    extensions = ["*.png", "*.jpg", "*.jpeg", "*.PNG", "*.JPG", "*.JPEG"]
    total = 0
    for ext in extensions:
        total += len(list(image_dir.glob(ext)))
    return total

def count_unused_images():
    """Count how many images haven't been used for video generation yet"""
    try:
        selected_df = pd.read_csv("./outputs/selected_images.csv")
        used_images = set(selected_df['image_path'].tolist())
        
        # Count all available images
        image_dir = Path("./images")
        extensions = ["*.png", "*.jpg", "*.jpeg", "*.PNG", "*.JPG", "*.JPEG"]
        all_images = set()
        for ext in extensions:
            for img in image_dir.glob(ext):
                all_images.add(str(img))
        
        return len(all_images - used_images)
    except:
        return "Unknown"

if __name__ == "__main__":
    show_video_creation_options()

