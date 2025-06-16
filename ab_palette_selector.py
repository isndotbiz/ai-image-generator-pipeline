#!/usr/bin/env -S bash -c 'source ~/menv/bin/activate && exec "$0" "$@"'
"""
A/B Palette Selection Logic

Chooses the 2 highest-frequency palettes excluding overly similar HSL distances (<10).
Persists to palette_A.json and palette_B.json with daily rotation and timestamped naming.
"""

import json
import colorsys
import os
import shutil
from datetime import datetime
from typing import List, Tuple, Dict, Any

def rgb_to_hsl(rgb: Tuple[int, int, int]) -> Tuple[float, float, float]:
    """Convert RGB to HSL values."""
    r, g, b = [x/255.0 for x in rgb]
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    return (h * 360, s * 100, l * 100)

def calculate_hsl_distance(hsl1: Tuple[float, float, float], hsl2: Tuple[float, float, float]) -> float:
    """Calculate the Euclidean distance between two HSL colors."""
    h1, s1, l1 = hsl1
    h2, s2, l2 = hsl2
    
    # Handle hue wrapping (circular distance)
    hue_diff = min(abs(h1 - h2), 360 - abs(h1 - h2))
    
    # Calculate Euclidean distance in HSL space
    distance = ((hue_diff) ** 2 + (s1 - s2) ** 2 + (l1 - l2) ** 2) ** 0.5
    return distance

def create_palette_from_colors(colors: List[Dict[str, Any]], palette_name: str) -> Dict[str, Any]:
    """Create a palette structure from a list of colors."""
    return {
        "name": palette_name,
        "created_at": datetime.now().isoformat(),
        "colors": colors,
        "total_frequency": sum(color["frequency"] for color in colors),
        "color_count": len(colors)
    }

def select_ab_palettes(min_similarity_distance: float = 10.0) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Select the two highest-frequency color palettes that are not overly similar."""
    
    # Load palette data
    with open('palettes.json', 'r') as f:
        data = json.load(f)
    
    aggregated_colors = data['aggregated_colors']
    
    if len(aggregated_colors) < 2:
        raise ValueError("Not enough colors to create two palettes")
    
    # Sort colors by frequency (highest first)
    sorted_colors = sorted(aggregated_colors, key=lambda x: x['frequency'], reverse=True)
    
    # Select palette A (highest frequency color group)
    palette_a_colors = []
    palette_b_colors = []
    
    # Start with the highest frequency color for palette A
    palette_a_colors.append(sorted_colors[0])
    palette_a_base_hsl = rgb_to_hsl(tuple(sorted_colors[0]['rgb']))
    
    # Find colors for palette A (similar to the base color)
    for color in sorted_colors[1:]:
        color_hsl = rgb_to_hsl(tuple(color['rgb']))
        distance = calculate_hsl_distance(palette_a_base_hsl, color_hsl)
        
        if distance < min_similarity_distance:
            palette_a_colors.append(color)
    
    # Find palette B (highest frequency color that's sufficiently different)
    palette_b_base = None
    palette_b_base_hsl = None
    
    for color in sorted_colors:
        color_hsl = rgb_to_hsl(tuple(color['rgb']))
        
        # Check if this color is sufficiently different from palette A base
        distance_to_a = calculate_hsl_distance(palette_a_base_hsl, color_hsl)
        
        if distance_to_a >= min_similarity_distance:
            # Check if it's not already in palette A
            if color not in palette_a_colors:
                palette_b_base = color
                palette_b_base_hsl = color_hsl
                break
    
    if palette_b_base is None:
        # If no sufficiently different color found, use the second highest frequency
        palette_b_base = sorted_colors[1]
        palette_b_base_hsl = rgb_to_hsl(tuple(palette_b_base['rgb']))
        print(f"Warning: No color found with HSL distance >= {min_similarity_distance} from palette A base.")
        print(f"Using second highest frequency color instead.")
    
    # Add the base color to palette B
    palette_b_colors.append(palette_b_base)
    
    # Find similar colors for palette B
    for color in sorted_colors:
        if color == palette_b_base:
            continue
            
        color_hsl = rgb_to_hsl(tuple(color['rgb']))
        distance_to_b_base = calculate_hsl_distance(palette_b_base_hsl, color_hsl)
        
        # Add to palette B if similar to B base and not in palette A
        if distance_to_b_base < min_similarity_distance and color not in palette_a_colors:
            palette_b_colors.append(color)
    
    # Create palette structures
    palette_a = create_palette_from_colors(palette_a_colors, "Palette A")
    palette_b = create_palette_from_colors(palette_b_colors, "Palette B")
    
    return palette_a, palette_b

def backup_existing_palettes():
    """Backup existing palette files with timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    for palette_file in ['palette_A.json', 'palette_B.json']:
        if os.path.exists(palette_file):
            backup_name = f"{palette_file.replace('.json', '')}_{timestamp}.json"
            shutil.copy2(palette_file, backup_name)
            print(f"Backed up {palette_file} to {backup_name}")

def save_palettes(palette_a: Dict[str, Any], palette_b: Dict[str, Any]):
    """Save the selected palettes to JSON files."""
    
    # Backup existing files
    backup_existing_palettes()
    
    # Save new palettes
    with open('palette_A.json', 'w') as f:
        json.dump(palette_a, f, indent=2)
    
    with open('palette_B.json', 'w') as f:
        json.dump(palette_b, f, indent=2)
    
    print(f"Saved palette_A.json with {len(palette_a['colors'])} colors (total frequency: {palette_a['total_frequency']})")
    print(f"Saved palette_B.json with {len(palette_b['colors'])} colors (total frequency: {palette_b['total_frequency']})")

def print_palette_summary(palette_a: Dict[str, Any], palette_b: Dict[str, Any]):
    """Print a summary of the selected palettes."""
    print("\n=== A/B PALETTE SELECTION SUMMARY ===")
    
    print(f"\nPalette A ({palette_a['name']}):")
    print(f"  Total colors: {palette_a['color_count']}")
    print(f"  Total frequency: {palette_a['total_frequency']}")
    print(f"  Colors:")
    for i, color in enumerate(palette_a['colors'][:5], 1):  # Show top 5
        print(f"    {i}. {color['hex']} (RGB: {color['rgb']}) - Frequency: {color['frequency']}")
    if len(palette_a['colors']) > 5:
        print(f"    ... and {len(palette_a['colors']) - 5} more colors")
    
    print(f"\nPalette B ({palette_b['name']}):")
    print(f"  Total colors: {palette_b['color_count']}")
    print(f"  Total frequency: {palette_b['total_frequency']}")
    print(f"  Colors:")
    for i, color in enumerate(palette_b['colors'][:5], 1):  # Show top 5
        print(f"    {i}. {color['hex']} (RGB: {color['rgb']}) - Frequency: {color['frequency']}")
    if len(palette_b['colors']) > 5:
        print(f"    ... and {len(palette_b['colors']) - 5} more colors")
    
    # Calculate HSL distance between palette bases
    if palette_a['colors'] and palette_b['colors']:
        base_a_hsl = rgb_to_hsl(tuple(palette_a['colors'][0]['rgb']))
        base_b_hsl = rgb_to_hsl(tuple(palette_b['colors'][0]['rgb']))
        distance = calculate_hsl_distance(base_a_hsl, base_b_hsl)
        print(f"\nHSL distance between palette bases: {distance:.2f}")

def main():
    """Main function to execute A/B palette selection."""
    try:
        print("Starting A/B palette selection...")
        
        # Select the two palettes
        palette_a, palette_b = select_ab_palettes(min_similarity_distance=10.0)
        
        # Print summary
        print_palette_summary(palette_a, palette_b)
        
        # Save to files
        save_palettes(palette_a, palette_b)
        
        print("\nA/B palette selection completed successfully!")
        
    except FileNotFoundError:
        print("Error: palettes.json file not found. Please ensure the file exists in the current directory.")
    except Exception as e:
        print(f"Error during A/B palette selection: {str(e)}")

if __name__ == "__main__":
    main()

