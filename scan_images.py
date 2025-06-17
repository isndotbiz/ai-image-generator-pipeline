#!/usr/bin/env python3
"""
Step 2: Recursively scan images directory

Use Path("images").rglob("*.[pj][pn]g") to gather every .png/.jpg/.jpeg file
and build a list of absolute paths.
"""

from pathlib import Path
from typing import List

def scan_images_directory() -> List[Path]:
    """
    Recursively scan the images directory for .png/.jpg/.jpeg files.
    
    Returns:
        List of absolute paths to all image files found
    """
    image_paths = []
    
    # Use rglob to find all image files matching the pattern
    # Pattern *.[pj][pn]g matches:
    # - *.png (when [pj] = 'p' and [pn] = 'n')
    # - *.jpg (when [pj] = 'j' and [pn] = 'p')
    for image_file in Path("images").rglob("*.[pj][pn]g"):
        # Convert to absolute path and add to list
        absolute_path = image_file.resolve()
        image_paths.append(absolute_path)
    
    return image_paths

if __name__ == "__main__":
    # Scan for images
    print("Scanning images directory...")
    images = scan_images_directory()
    
    print(f"\nFound {len(images)} image files:")
    print("\nList of absolute paths:")
    for i, path in enumerate(images, 1):
        print(f"{i:3d}. {path}")
    
    print(f"\nTotal: {len(images)} image files found")

