#!/usr/bin/env python3
"""
Color palette extraction utilities for image generation.
"""

import sys
import os
from typing import List, Tuple, Optional

def extract_dominant_colors(image_path: str, num_colors: int = 5) -> List[Tuple[int, int, int]]:
    """
    Extract dominant colors from an image.
    
    Args:
        image_path: Path to the image file
        num_colors: Number of dominant colors to extract
        
    Returns:
        List of RGB tuples representing dominant colors
    """
    try:
        from PIL import Image
        import numpy as np
        from sklearn.cluster import KMeans
        
        # Load and resize image for faster processing
        img = Image.open(image_path)
        img = img.convert('RGB')
        img = img.resize((150, 150))
        
        # Convert to numpy array and reshape
        data = np.array(img)
        data = data.reshape((-1, 3))
        
        # Use KMeans to find dominant colors
        kmeans = KMeans(n_clusters=num_colors, random_state=42, n_init=10)
        kmeans.fit(data)
        
        # Get the colors
        colors = kmeans.cluster_centers_.astype(int)
        return [tuple(color) for color in colors]
        
    except ImportError:
        print("Warning: PIL/scikit-learn not available for color extraction")
        return [(128, 128, 128)] * num_colors
    except Exception as e:
        print(f"Error extracting colors: {e}")
        return [(128, 128, 128)] * num_colors

def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
    """
    Convert RGB tuple to hex string.
    
    Args:
        rgb: RGB color tuple
        
    Returns:
        Hex color string (e.g., '#FF5733')
    """
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"

def get_color_palette_prompt(colors: List[Tuple[int, int, int]]) -> str:
    """
    Generate a color palette description for prompts.
    
    Args:
        colors: List of RGB color tuples
        
    Returns:
        String description of the color palette
    """
    if not colors:
        return "natural color palette"
    
    hex_colors = [rgb_to_hex(color) for color in colors]
    return f"color palette featuring {', '.join(hex_colors[:3])}"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 palette_extractor.py <image_path> [num_colors]")
        sys.exit(1)
    
    image_path = sys.argv[1]
    num_colors = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    
    if not os.path.exists(image_path):
        print(f"Error: Image file '{image_path}' not found")
        sys.exit(1)
    
    colors = extract_dominant_colors(image_path, num_colors)
    palette_prompt = get_color_palette_prompt(colors)
    
    print(f"Dominant colors: {colors}")
    print(f"Palette prompt: {palette_prompt}")

