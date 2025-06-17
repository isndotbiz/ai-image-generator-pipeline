#!/usr/bin/env python3

import os
import glob
from watermark import add_combined_watermark

def main():
    # Get current directory
    current_dir = os.getcwd()
    images_dir = os.path.join(current_dir, 'images')
    
    if not os.path.exists(images_dir):
        print(f"Images directory not found: {images_dir}")
        return
    
    # Find all original images (with platform suffixes, not watermarked)
    original_suffixes = ['_ig.png', '_tt.png', '_tw.png']
    original_images = []
    
    for suffix in original_suffixes:
        pattern = os.path.join(images_dir, f'*{suffix}')
        matching_files = glob.glob(pattern)
        # Filter out already watermarked files
        for file in matching_files:
            if 'watermarked' not in os.path.basename(file).lower():
                original_images.append(file)
    
    if not original_images:
        print("No original images found with suffixes _ig.png, _tt.png, or _tw.png")
        return
    
    print(f"Found {len(original_images)} original images to watermark:")
    for img in original_images:
        print(f"  - {os.path.basename(img)}")
    
    # Remove old watermarked images first
    print("\nRemoving old watermarked images...")
    watermarked_pattern = os.path.join(images_dir, '*watermarked*')
    old_watermarked = glob.glob(watermarked_pattern)
    removed_count = 0
    
    for old_file in old_watermarked:
        try:
            os.remove(old_file)
            print(f"  Removed: {os.path.basename(old_file)}")
            removed_count += 1
        except Exception as e:
            print(f"  Error removing {os.path.basename(old_file)}: {e}")
    
    print(f"Removed {removed_count} old watermarked images.")
    
    # Apply combined watermarks
    print("\nApplying combined watermarks...")
    logo_path = os.path.join(current_dir, 'Fortuna_Bound_Watermark.png')
    
    if not os.path.exists(logo_path):
        print(f"Logo watermark not found: {logo_path}")
        return
    
    success_count = 0
    error_count = 0
    
    for image_path in original_images:
        try:
            # Determine platform from filename suffix
            if image_path.endswith('_ig.png'):
                platform = 'instagram'
            elif image_path.endswith('_tt.png'):
                platform = 'tiktok'
            elif image_path.endswith('_tw.png'):
                platform = 'twitter'
            else:
                platform = 'instagram'  # default
            
            print(f"  Processing {os.path.basename(image_path)} for {platform}...")
            
            # Apply combined watermark
            add_combined_watermark(
                image_path=image_path,
                logo_path=logo_path,
                text="@Fortuna_Bound",
                platform=platform
            )
            
            success_count += 1
            print(f"    ✓ Successfully watermarked")
            
        except Exception as e:
            error_count += 1
            print(f"    ✗ Error: {e}")
    
    # Summary
    print(f"\n=== SUMMARY ===")
    print(f"Original images processed: {len(original_images)}")
    print(f"Successfully watermarked: {success_count}")
    print(f"Errors: {error_count}")
    print(f"Old watermarked images removed: {removed_count}")
    
    if success_count > 0:
        print(f"\nNew watermarked images saved with '_watermarked' suffix in the filename.")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Apply Combined Watermarks Script

This script applies both the Fortuna Bound logo and "@Fortuna_Bound" text 
watermarks to all original images, replacing old watermarked versions.

Usage:
    python3 apply_combined_watermarks.py

Features:
- Applies logo watermark from Fortuna_Bound_Watermark.png
- Adds "@Fortuna_Bound" text watermark
- Platform-specific positioning (Instagram, TikTok, Twitter)
- Removes old watermarked images before creating new ones
- Progress tracking
"""

import os
import sys
import glob
from pathlib import Path
from watermark import batch_combined_watermark, Platform

def get_platform_from_suffix(filename):
    """Determine platform from file suffix."""
    if filename.endswith('_ig.png'):
        return 'instagram'
    elif filename.endswith('_tt.png'):
        return 'tiktok' 
    elif filename.endswith('_tw.png'):
        return 'twitter'
    else:
        return 'generic'

def remove_old_watermarked_images():
    """Remove all existing watermarked images."""
    print("\n🗑️  Removing old watermarked images...")
    
    watermarked_patterns = [
        'images/*_watermarked.png',
        'images/*_watermarked.jpg',
        'images/*_watermarked.jpeg'
    ]
    
    removed_count = 0
    for pattern in watermarked_patterns:
        watermarked_files = glob.glob(pattern)
        for file_path in watermarked_files:
            try:
                os.remove(file_path)
                removed_count += 1
                print(f"  ✅ Removed: {os.path.basename(file_path)}")
            except Exception as e:
                print(f"  ❌ Error removing {file_path}: {e}")
    
    print(f"\n📊 Removed {removed_count} old watermarked images\n")
    return removed_count

def find_original_images():
    """Find all original images (not watermarked) for processing."""
    print("🔍 Finding original images...")
    
    # Get all PNG files in images directory
    all_images = glob.glob('images/*.png')
    
    # Filter out watermarked images and non-platform specific files
    original_images = []
    for img in all_images:
        basename = os.path.basename(img)
        # Skip if already watermarked or not platform-specific
        if ('_watermarked' not in basename and 
            (basename.endswith('_ig.png') or 
             basename.endswith('_tt.png') or 
             basename.endswith('_tw.png'))):
            original_images.append(img)
    
    print(f"📊 Found {len(original_images)} original images to process\n")
    return sorted(original_images)

def group_images_by_platform(image_paths):
    """Group images by their target platform."""
    platform_groups = {
        'instagram': [],
        'tiktok': [],
        'twitter': [],
        'generic': []
    }
    
    for img_path in image_paths:
        platform = get_platform_from_suffix(img_path)
        platform_groups[platform].append(img_path)
    
    return platform_groups

def apply_watermarks():
    """Apply combined watermarks to all original images."""
    logo_path = 'Fortuna_Bound_Watermark.png'
    text = '@Fortuna_Bound'
    
    # Check if logo exists
    if not os.path.exists(logo_path):
        print(f"❌ Error: Logo file '{logo_path}' not found!")
        print("   Please ensure the Fortuna Bound logo is in the current directory.")
        return False
    
    print(f"🎨 Using logo: {logo_path}")
    print(f"📝 Using text: {text}")
    
    # Remove old watermarked images first
    remove_old_watermarked_images()
    
    # Find original images
    original_images = find_original_images()
    if not original_images:
        print("⚠️  No original images found to process.")
        return True
    
    # Group by platform
    platform_groups = group_images_by_platform(original_images)
    
    total_processed = 0
    total_errors = 0
    
    # Process each platform group
    for platform_name, image_list in platform_groups.items():
        if not image_list:
            continue
            
        print(f"\n🎯 Processing {len(image_list)} images for {platform_name.upper()}...")
        
        try:
            # Apply combined watermarks
            results = batch_combined_watermark(
                image_paths=image_list,
                logo_path=logo_path,
                text=text,
                platform_name=platform_name,
                opacity=0.92
            )
            
            # Count successful vs failed
            for i, result_path in enumerate(results):
                if result_path != image_list[i]:  # Successfully watermarked
                    total_processed += 1
                    print(f"  ✅ {os.path.basename(image_list[i])} → {os.path.basename(result_path)}")
                else:  # Failed to watermark
                    total_errors += 1
                    print(f"  ❌ Failed: {os.path.basename(image_list[i])}")
                    
        except Exception as e:
            print(f"❌ Error processing {platform_name} images: {e}")
            total_errors += len(image_list)
    
    # Summary
    print(f"\n📊 SUMMARY:")
    print(f"   ✅ Successfully processed: {total_processed} images")
    print(f"   ❌ Failed: {total_errors} images")
    print(f"   🎯 Total attempted: {len(original_images)} images")
    
    if total_processed > 0:
        print(f"\n🎉 Combined watermarking complete!")
        print(f"   📁 Watermarked images saved in: images/ directory")
        print(f"   🏷️  Each image now has both logo and '@Fortuna_Bound' text")
    
    return total_errors == 0

def main():
    """Main function."""
    print("🚀 Combined Watermark Application Started")
    print("   Logo + Text: Fortuna_Bound_Watermark.png + '@Fortuna_Bound'")
    print("   Platform positioning: Instagram, TikTok, Twitter")
    
    # Change to script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    success = apply_watermarks()
    
    if success:
        print("\n✨ All watermarks applied successfully!")
        return 0
    else:
        print("\n⚠️  Some errors occurred during processing.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

