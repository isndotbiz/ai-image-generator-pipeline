#!/usr/bin/env python3
"""
Color Palette Analysis Script

Analyzes the extracted color palettes from palettes.json
and provides additional insights and statistics.
"""

import json
import colorsys
from collections import defaultdict, Counter

def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hsl(rgb):
    """Convert RGB to HSL"""
    r, g, b = [x/255.0 for x in rgb]
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    return (int(h*360), int(s*100), int(l*100))

def categorize_color(hsl):
    """Categorize color based on HSL values"""
    h, s, l = hsl
    
    # Check for grayscale
    if s < 10:
        if l < 20:
            return "Black/Dark Gray"
        elif l < 40:
            return "Dark Gray"
        elif l < 60:
            return "Medium Gray"
        elif l < 80:
            return "Light Gray"
        else:
            return "White/Very Light"
    
    # Chromatic colors
    if l < 25:
        brightness = "Dark"
    elif l < 50:
        brightness = "Medium"
    else:
        brightness = "Light"
    
    # Hue categories
    if h < 15 or h >= 345:
        hue_name = "Red"
    elif h < 45:
        hue_name = "Orange"
    elif h < 75:
        hue_name = "Yellow"
    elif h < 105:
        hue_name = "Yellow-Green"
    elif h < 135:
        hue_name = "Green"
    elif h < 165:
        hue_name = "Blue-Green"
    elif h < 195:
        hue_name = "Cyan"
    elif h < 225:
        hue_name = "Blue"
    elif h < 255:
        hue_name = "Blue-Purple"
    elif h < 285:
        hue_name = "Purple"
    elif h < 315:
        hue_name = "Magenta"
    else:
        hue_name = "Pink"
    
    return f"{brightness} {hue_name}"

def analyze_palettes():
    """Main analysis function"""
    with open('palettes.json', 'r') as f:
        data = json.load(f)
    
    print("=== COLOR PALETTE ANALYSIS ===")
    print(f"Total videos processed: {data['summary']['total_videos']}")
    print(f"Successful extractions: {data['summary']['successful_videos']}")
    print(f"Total unique colors: {data['summary']['total_unique_colors']}")
    print(f"Total color instances: {data['summary']['total_color_instances']}")
    print()
    
    # Analyze color categories
    color_categories = defaultdict(int)
    video_categories = defaultdict(set)
    
    for color_data in data['aggregated_colors']:
        rgb = color_data['rgb']
        hsl = rgb_to_hsl(rgb)
        category = categorize_color(hsl)
        
        color_categories[category] += color_data['frequency']
        
        # Track which videos contain each category
        for appearance in color_data['appearances']:
            video_categories[category].add(appearance['video'])
    
    print("=== COLOR CATEGORY DISTRIBUTION ===")
    sorted_categories = sorted(color_categories.items(), key=lambda x: x[1], reverse=True)
    for category, count in sorted_categories:
        video_count = len(video_categories[category])
        print(f"{category:20} : {count:3d} instances across {video_count:2d} videos")
    print()
    
    # Analyze video types and their dominant colors
    video_type_colors = defaultdict(list)
    
    for video_name, palette_data in data['video_palettes'].items():
        if palette_data:  # Skip failed extractions
            # Extract video type from filename
            if 'travel' in video_name.lower():
                video_type = 'Travel'
            elif 'luxury' in video_name.lower():
                video_type = 'Luxury'
            elif 'technology' in video_name.lower():
                video_type = 'Technology'
            elif 'business' in video_name.lower():
                video_type = 'Business'
            else:
                video_type = 'Other'
            
            # Get all colors from this video
            for frame in palette_data:
                for color_hex in frame['colors_hex']:
                    video_type_colors[video_type].append(color_hex)
    
    print("=== COLORS BY VIDEO CATEGORY ===")
    for video_type, colors in video_type_colors.items():
        color_counter = Counter(colors)
        total_colors = len(colors)
        unique_colors = len(color_counter)
        
        print(f"\n{video_type} Videos:")
        print(f"  Total color instances: {total_colors}")
        print(f"  Unique colors: {unique_colors}")
        print(f"  Top 5 colors:")
        
        for i, (color, count) in enumerate(color_counter.most_common(5), 1):
            rgb = hex_to_rgb(color)
            hsl = rgb_to_hsl(rgb)
            category = categorize_color(hsl)
            print(f"    {i}. {color} ({category}) - {count} times")
    
    print("\n=== MOST FREQUENT COLORS OVERALL ===")
    for i, color_data in enumerate(data['aggregated_colors'][:20], 1):
        rgb = color_data['rgb']
        hsl = rgb_to_hsl(rgb)
        category = categorize_color(hsl)
        
        print(f"{i:2d}. {color_data['hex']} ({category:20}) - {color_data['frequency']} times")
    
    # Frame position analysis
    print("\n=== FRAME POSITION ANALYSIS ===")
    position_colors = {'25%': [], '75%': []}
    
    for video_name, palette_data in data['video_palettes'].items():
        if palette_data:
            for frame in palette_data:
                position_colors[frame['position']].extend(frame['colors_hex'])
    
    for position, colors in position_colors.items():
        color_counter = Counter(colors)
        print(f"\n{position} frame position:")
        print(f"  Total colors: {len(colors)}")
        print(f"  Unique colors: {len(color_counter)}")
        print(f"  Top 5 colors:")
        
        for i, (color, count) in enumerate(color_counter.most_common(5), 1):
            rgb = hex_to_rgb(color)
            category = categorize_color(rgb_to_hsl(rgb))
            print(f"    {i}. {color} ({category}) - {count} times")

if __name__ == "__main__":
    analyze_palettes()

