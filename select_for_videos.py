#!/usr/bin/env -S bash -c 'source ~/menv/bin/activate && exec "$0" "$@"'
"""
Manually select high-quality images for video generation
"""

import os
import shutil
from pathlib import Path
import random

def select_images_for_videos():
    """Select diverse high-quality images for video generation"""
    
    # Create directories
    Path('images/approved').mkdir(exist_ok=True)
    Path('images/selected_for_video').mkdir(exist_ok=True)
    
    # Find all watermarked images
    images_dir = Path('images')
    watermarked_images = list(images_dir.glob('*_watermarked.png'))
    
    print(f"Found {len(watermarked_images)} watermarked images")
    
    # Filter for diverse, high-quality content
    selected_images = []
    
    # Categories to prioritize
    priority_keywords = [
        'maldives', 'london', 'paris', 'dubai', 'tokyo', 'santorini',
        'montreal', 'sydney', 'hong', 'singapore', 'tuscany', 'new',
        'amsterdam', 'barcelona', 'vancouver', 'cape', 'miami'
    ]
    
    # Select images from each category
    for keyword in priority_keywords:
        matching = [img for img in watermarked_images if keyword in img.name.lower()]
        if matching:
            # Prefer Instagram format for better quality
            ig_images = [img for img in matching if '_ig_' in img.name]
            if ig_images:
                selected_images.extend(random.sample(ig_images, min(2, len(ig_images))))
            else:
                selected_images.extend(random.sample(matching, min(1, len(matching))))
    
    # Deduplicate and limit to 30 images
    selected_images = list(set(selected_images))[:30]
    
    print(f"Selected {len(selected_images)} images for video generation:")
    
    # Copy to approved and selected_for_video directories
    for img in selected_images:
        print(f"  ✅ {img.name}")
        
        # Copy to approved
        shutil.copy2(img, 'images/approved/')
        
        # Copy to selected_for_video
        shutil.copy2(img, 'images/selected_for_video/')
    
    print(f"\n📁 Copied {len(selected_images)} images to:")
    print(f"   - images/approved/")
    print(f"   - images/selected_for_video/")
    
    return selected_images

if __name__ == '__main__':
    print("🎯 Selecting High-Quality Images for Video Generation...")
    selected = select_images_for_videos()
    print(f"\n🎉 Selection complete! Ready to generate {len(selected)} videos.")

