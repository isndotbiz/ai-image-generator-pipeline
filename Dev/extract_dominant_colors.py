#!/usr/bin/env python3
"""
Dominant Color Palette Extraction from Videos

This script extracts dominant color palettes from MP4 videos by:
1. Extracting frames at 25% and 75% duration using ffmpeg
2. Using colorthief to get top 5 dominant colors per frame
3. Storing results in palettes.json
4. Aggregating and ranking colors by frequency
"""

import os
import json
import glob
import subprocess
import tempfile
from collections import Counter, defaultdict
from colorthief import ColorThief
from PIL import Image
import sys

def get_video_duration(video_path):
    """Get video duration in seconds using ffprobe"""
    try:
        cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json',
            '-show_format', video_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        info = json.loads(result.stdout)
        duration = float(info['format']['duration'])
        return duration
    except (subprocess.CalledProcessError, KeyError, ValueError) as e:
        print(f"Error getting duration for {video_path}: {e}", file=sys.stderr)
        return None

def extract_frame_at_time(video_path, time_seconds, output_path):
    """Extract a single frame at specified time using ffmpeg"""
    try:
        cmd = [
            'ffmpeg', '-i', video_path, '-ss', str(time_seconds),
            '-vframes', '1', '-y', output_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error extracting frame from {video_path} at {time_seconds}s: {e}", file=sys.stderr)
        return False

def get_dominant_colors(image_path, num_colors=5):
    """Extract dominant colors using ColorThief"""
    try:
        color_thief = ColorThief(image_path)
        # Get the dominant color and top colors
        dominant_color = color_thief.get_color(quality=1)
        
        # Get palette of colors (including the dominant one)
        if num_colors > 1:
            palette = color_thief.get_palette(color_count=num_colors, quality=1)
        else:
            palette = [dominant_color]
        
        return palette
    except Exception as e:
        print(f"Error extracting colors from {image_path}: {e}", file=sys.stderr)
        return []

def rgb_to_hex(rgb):
    """Convert RGB tuple to hex string"""
    return "#{:02x}{:02x}{:02x}".format(rgb[0], rgb[1], rgb[2])

def process_video(video_path):
    """Process a single video and extract color palettes"""
    print(f"Processing: {os.path.basename(video_path)}")
    
    # Get video duration
    duration = get_video_duration(video_path)
    if duration is None:
        return None
    
    # Calculate frame extraction times (25% and 75%)
    frame_25_time = duration * 0.25
    frame_75_time = duration * 0.75
    
    video_colors = []
    
    # Extract frames and colors
    with tempfile.TemporaryDirectory() as temp_dir:
        for frame_time, label in [(frame_25_time, '25%'), (frame_75_time, '75%')]:
            frame_path = os.path.join(temp_dir, f"frame_{label.replace('%', 'pct')}.jpg")
            
            if extract_frame_at_time(video_path, frame_time, frame_path):
                colors = get_dominant_colors(frame_path, num_colors=5)
                if colors:
                    frame_data = {
                        'timestamp': frame_time,
                        'position': label,
                        'colors_rgb': colors,
                        'colors_hex': [rgb_to_hex(color) for color in colors]
                    }
                    video_colors.append(frame_data)
                    print(f"  Extracted {len(colors)} colors from {label} frame")
    
    return video_colors

def aggregate_colors(all_video_data):
    """Aggregate and rank colors by frequency across all videos"""
    color_counter = Counter()
    color_details = defaultdict(list)
    
    for video_name, frames in all_video_data.items():
        if frames:  # Skip failed extractions
            for frame in frames:
                for i, color_hex in enumerate(frame['colors_hex']):
                    color_counter[color_hex] += 1
                    color_details[color_hex].append({
                        'video': video_name,
                        'frame_position': frame['position'],
                        'color_rank': i + 1,  # 1-based ranking
                        'rgb': frame['colors_rgb'][i]
                    })
    
    # Create ranked list
    ranked_colors = []
    for color_hex, frequency in color_counter.most_common():
        ranked_colors.append({
            'hex': color_hex,
            'rgb': color_details[color_hex][0]['rgb'],  # RGB from first occurrence
            'frequency': frequency,
            'appearances': color_details[color_hex]
        })
    
    return ranked_colors

def main():
    """Main function to process all videos and create palettes.json"""
    video_dir = "video_outputs"
    output_file = "palettes.json"
    
    # Find all MP4 files
    video_pattern = os.path.join(video_dir, "*.mp4")
    video_files = glob.glob(video_pattern)
    
    if not video_files:
        print(f"No MP4 files found in {video_dir}")
        return
    
    print(f"Found {len(video_files)} video files to process")
    
    # Process each video
    all_video_data = {}
    successful_videos = 0
    
    for video_path in sorted(video_files):
        video_name = os.path.basename(video_path)
        video_colors = process_video(video_path)
        
        if video_colors:
            all_video_data[video_name] = video_colors
            successful_videos += 1
        else:
            all_video_data[video_name] = None
            print(f"  Failed to process {video_name}")
    
    print(f"\nSuccessfully processed {successful_videos}/{len(video_files)} videos")
    
    # Aggregate colors across all videos
    print("Aggregating and ranking colors...")
    ranked_colors = aggregate_colors(all_video_data)
    
    # Create final output structure
    output_data = {
        'summary': {
            'total_videos': len(video_files),
            'successful_videos': successful_videos,
            'total_unique_colors': len(ranked_colors),
            'total_color_instances': sum(color['frequency'] for color in ranked_colors)
        },
        'video_palettes': all_video_data,
        'aggregated_colors': ranked_colors
    }
    
    # Save to JSON file
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\nResults saved to {output_file}")
    print(f"Top 10 most frequent colors:")
    for i, color in enumerate(ranked_colors[:10], 1):
        print(f"  {i:2d}. {color['hex']} (RGB: {color['rgb']}) - appears {color['frequency']} times")

if __name__ == "__main__":
    main()

