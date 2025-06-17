#!/usr/bin/env python3
"""
Mantra Text Overlay Script for Fortuna Bound

Adds mantra text overlays to freshly generated images AFTER generation.
Applies overlays to watermarked copies to keep logo + text together.

Usage:
    python3 overlay_mantras.py [--images-dir DIR] [--mantra-category CATEGORY]
"""

import os
import glob
import argparse
import json
from pathlib import Path
from typing import List, Dict, Optional
from PIL import Image, ImageDraw, ImageFont
from mantra_generator import MantraGenerator

def get_watermarked_path(base_path: str) -> str:
    """Get the watermarked version path for a base image path."""
    base, ext = os.path.splitext(base_path)
    return f"{base}_watermarked{ext}"

def get_best_font(font_size: int) -> ImageFont.ImageFont:
    """Get the best available font for the system."""
    # Try system fonts in order of preference
    font_paths = [
        "/System/Library/Fonts/Arial Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc", 
        "/System/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/Georgia.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  # Linux
        "C:\\Windows\\Fonts\\arial.ttf",  # Windows
    ]
    
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                return ImageFont.truetype(font_path, font_size)
            except Exception:
                continue
    
    # Fallback to default font
    return ImageFont.load_default()

def apply_mantra_overlay(image_path: str, mantra_text: str, mg: MantraGenerator) -> bool:
    """Apply mantra text overlay to a watermarked image."""
    try:
        watermarked_path = get_watermarked_path(image_path)
        
        # Check if watermarked version exists
        if not os.path.exists(watermarked_path):
            print(f"❌ Watermarked version doesn't exist: {watermarked_path}")
            return False
            
        # Load the watermarked image
        img = Image.open(watermarked_path).convert("RGBA")
        
        # Get text placement preview
        preview = mg.preview_text_placement(mantra_text, img.width, img.height)
        
        # Create transparent overlay
        overlay = Image.new('RGBA', img.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Get the best available font
        font = get_best_font(preview["font_size"])
        
        # Add text shadow for better readability
        shadow_offset = max(1, preview["font_size"] // 20)
        shadow_color = (0, 0, 0, 180)  # Semi-transparent black
        text_color = (255, 255, 255, 255)  # White
        
        # Draw shadow
        draw.text(
            (preview["position"]["x"] + shadow_offset, preview["position"]["y"] + shadow_offset),
            mantra_text, 
            font=font, 
            fill=shadow_color
        )
        
        # Draw main text
        draw.text(
            (preview["position"]["x"], preview["position"]["y"]),
            mantra_text, 
            font=font, 
            fill=text_color
        )
        
        # Combine with original image
        combined = Image.alpha_composite(img, overlay)
        
        # Convert back to RGB if needed
        if combined.mode == 'RGBA':
            background = Image.new('RGB', combined.size, (255, 255, 255))
            background.paste(combined, mask=combined.split()[-1])
            combined = background
        
        # Save the result
        combined.save(watermarked_path, "PNG", quality=95)
        
        print(f"✅ Mantra '{mantra_text}' applied to {os.path.basename(image_path)}")
        return True
        
    except Exception as e:
        print(f"❌ Error processing {image_path}: {e}")
        return False

def find_image_files(images_dir: str = ".") -> List[str]:
    """Find all direct_*_<platform>.png files (non-watermarked)."""
    pattern = os.path.join(images_dir, "direct_*_*.png")
    all_files = glob.glob(pattern)
    
    # Filter out watermarked files
    non_watermarked = [f for f in all_files if "_watermarked" not in f]
    
    # Sort by creation time (newest first)
    non_watermarked.sort(key=lambda x: os.path.getctime(x), reverse=True)
    
    return non_watermarked

def load_generation_metadata(images_dir: str = ".") -> Dict[str, str]:
    """Try to load mantra metadata from generation response files."""
    metadata = {}
    
    # Look for JSON files that might contain generation responses
    json_files = glob.glob(os.path.join(images_dir, "*.json"))
    json_files.extend(glob.glob("*.json"))
    
    for json_file in json_files:
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
                
            # Extract mantra info if available
            if isinstance(data, dict) and "images" in data:
                # Handle bulk generation summary format
                if "filenames" in data["images"]:
                    # No mantra data in this format, skip
                    continue
                    
            # TODO: Add more metadata extraction logic based on actual response format
            
        except Exception:
            continue
    
    return metadata

def main():
    parser = argparse.ArgumentParser(description="Add mantra text overlays to generated images")
    parser.add_argument("--images-dir", default="images", 
                       help="Directory containing images (default: images)")
    parser.add_argument("--mantra-category", 
                       choices=["prosperity", "empowerment", "growth", "mindfulness", "success", "luxury"],
                       help="Mantra category to use (default: random)")
    parser.add_argument("--limit", type=int, default=20,
                       help="Maximum number of images to process (default: 20)")
    parser.add_argument("--preview", action="store_true",
                       help="Preview text placement without applying")
    
    args = parser.parse_args()
    
    # Initialize mantra generator
    mg = MantraGenerator()
    
    # Find image files
    image_files = find_image_files(args.images_dir)
    
    if not image_files:
        print("❌ No direct_*_*.png files found!")
        return
    
    # Limit to specified number
    image_files = image_files[:args.limit]
    
    print(f"🎯 Found {len(image_files)} images to process")
    print(f"📁 Images directory: {args.images_dir}")
    print(f"🎨 Mantra category: {args.mantra_category or 'random'}")
    print()
    
    # Load any existing metadata
    metadata = load_generation_metadata(args.images_dir)
    
    # Process each image
    successful = 0
    failed = 0
    
    for i, image_path in enumerate(image_files, 1):
        filename = os.path.basename(image_path)
        print(f"[{i}/{len(image_files)}] Processing {filename}...")
        
        # Get mantra for this image
        if filename in metadata:
            mantra_text = metadata[filename]
            print(f"    📝 Using metadata mantra: {mantra_text}")
        else:
            # Generate random mantra
            mantra_options = mg.get_random_mantras(1, args.mantra_category)
            mantra_text = mantra_options[0]["text"]
            print(f"    🎲 Generated mantra: {mantra_text}")
        
        if args.preview:
            # Just show preview info
            preview = mg.preview_text_placement(mantra_text, 1080, 1350)
            print(f"    👁️  Preview: Font size {preview['font_size']}px at ({preview['position']['x']}, {preview['position']['y']})")
            print(f"    📊 Readability: {preview['metrics']['readability']}")
            successful += 1
        else:
            # Apply the overlay
            if apply_mantra_overlay(image_path, mantra_text, mg):
                successful += 1
            else:
                failed += 1
        
        print()
    
    # Summary
    print(f"📊 Summary:")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"📝 Total processed: {len(image_files)}")
    
    if not args.preview and successful > 0:
        print(f"\n🎉 Mantra overlays have been applied to {successful} watermarked images!")
        print(f"💡 The logo and text are now combined on the watermarked versions.")

if __name__ == "__main__":
    main()

