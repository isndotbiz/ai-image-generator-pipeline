#!/usr/bin/env python3
"""
Simple Video Generation Setup

Quickly create a video from the generated images without external API.
"""

import glob
import subprocess
import os
from datetime import datetime

def create_slideshow_video():
    """Create a simple slideshow video from generated images"""
    
    print("🎬 Creating slideshow video from generated images...")
    
    # Find watermarked images
    watermarked_images = glob.glob("images/direct_*_watermarked.png")
    
    if len(watermarked_images) < 5:
        print(f"❌ Need at least 5 images, found {len(watermarked_images)}")
        return False
    
    print(f"📸 Found {len(watermarked_images)} watermarked images")
    
    # Sort by creation time
    watermarked_images.sort(key=os.path.getctime)
    
    # Take up to 20 images
    selected_images = watermarked_images[:20]
    
    print(f"🎯 Using {len(selected_images)} images for video")
    
    # Create video filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    video_filename = f"video_outputs/fortuna_bound_slideshow_{timestamp}.mp4"
    
    # Ensure video_outputs directory exists
    os.makedirs("video_outputs", exist_ok=True)
    
    try:
        # Use existing slideshow creation script if available
        if os.path.exists("create_slideshow_videos.sh"):
            print("🔧 Using existing slideshow script")
            result = subprocess.run(["./create_slideshow_videos.sh"], 
                                  capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                print("✅ Slideshow video created successfully!")
                
                # Find the created video
                recent_videos = glob.glob("video_outputs/fortuna_bound_slideshow_*.mp4")
                if recent_videos:
                    latest_video = max(recent_videos, key=os.path.getctime)
                    size_mb = os.path.getsize(latest_video) / 1024 / 1024
                    print(f"📁 Video: {latest_video} ({size_mb:.1f}MB)")
                return True
            else:
                print(f"❌ Slideshow script failed: {result.stderr}")
                return False
        else:
            print("❌ Slideshow script not found")
            print("💡 Run: ./create_slideshow_videos.sh manually to create video")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Video creation timed out after 5 minutes")
        return False
    except Exception as e:
        print(f"❌ Error creating video: {e}")
        return False

def main():
    print("🎬 FORTUNA BOUND VIDEO SETUP")
    print("=" * 30)
    
    # Check if we have enough images
    watermarked_count = len(glob.glob("images/direct_*_watermarked.png"))
    print(f"📊 Available watermarked images: {watermarked_count}")
    
    if watermarked_count >= 5:
        create_slideshow_video()
    else:
        print("❌ Need at least 5 images to create video")
        print("💡 Generate more images first")

if __name__ == "__main__":
    main()

