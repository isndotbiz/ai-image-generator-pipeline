#!/usr/bin/env python3
"""
Test script for image selection logic in IntelligentVideoGenerator
"""

import os
import json
import random
from pathlib import Path
from datetime import datetime

def load_ranking_data(images_dir):
    """Load latest ranking data for intelligent processing"""
    # Check multiple possible locations for ranking files
    search_dirs = [Path(images_dir), Path("video_queue"), Path(".")]
    
    all_ranking_files = []
    for search_dir in search_dirs:
        ranking_files = list(search_dir.glob("*ranking*.json"))
        all_ranking_files.extend(ranking_files)
    
    if not all_ranking_files:
        print("No ranking files found")
        return {}
    
    # Find the most recent ranking file
    latest_file = max(all_ranking_files, key=os.path.getctime)
    print(f"Loading ranking data from: {latest_file}")
    
    with open(latest_file, 'r') as f:
        rankings = json.load(f)
    
    # Convert to dictionary for quick lookup
    ranking_dict = {r['filename']: r for r in rankings}
    
    # Also check for basename matches (without directory prefixes)
    extended_dict = {}
    for filename, data in ranking_dict.items():
        # Store both original filename and basename
        extended_dict[filename] = data
        extended_dict[Path(filename).name] = data
    
    return extended_dict

def test_image_selection(max_videos=None):
    """Test the image selection logic"""
    # Get max_videos from environment variable if not provided
    if max_videos is None:
        max_videos = int(os.getenv('MAX_VIDEOS', '5'))  # Default to 5 for testing
    
    selected_dir = Path("video_queue")
    selected_images = list(selected_dir.glob("*.png"))
    
    if not selected_images:
        print("❌ No images found in video_queue/")
        return []
    
    print(f"Found {len(selected_images)} images in video_queue/")
    
    # Load ranking data for intelligent processing
    ranking_data = load_ranking_data("images")
    print(f"Loaded ranking data for {len(ranking_data)} images")
    
    # Enhanced sorting: by final_score descending, fallback to random
    def get_sort_key(img):
        data = ranking_data.get(img.name, {})
        final_score = data.get('final_score', 0)
        # If no score available, use random value for fallback
        if final_score == 0:
            return (0, random.random())
        return (1, final_score)  # Prioritize scored images, then by score
    
    # Sort with enhanced logic
    selected_images.sort(key=get_sort_key, reverse=True)
    
    # Slice to max_videos
    images_to_process = selected_images[:max_videos]
    
    # Extract metadata for each selected image
    selected_metadata = []
    for image_path in images_to_process:
        # Parse filename to extract descriptor tokens and platform suffix
        filename = image_path.stem  # Remove .png extension
        
        # Extract platform suffix (_ig_, _tt_, _tw_)
        platform_suffix = None
        for platform in ['_ig_', '_tt_', '_tw_']:
            if platform in filename:
                platform_suffix = platform.strip('_')
                break
        
        # Extract descriptor tokens (everything before platform suffix or before _draft)
        descriptor_tokens = filename
        if platform_suffix:
            # Split on platform and take the part before it
            descriptor_tokens = filename.split(f'_{platform_suffix}_')[0]
        elif '_draft' in filename:
            # If no platform suffix, split on _draft
            descriptor_tokens = filename.split('_draft')[0]
        
        selected_metadata.append({
            'image_path': image_path,
            'filename': image_path.name,
            'descriptor_tokens': descriptor_tokens,
            'platform_suffix': platform_suffix,
            'ranking_data': ranking_data.get(image_path.name, {}),
            'final_score': ranking_data.get(image_path.name, {}).get('final_score', 0)
        })
    
    print(f"\n🎬 Selected {len(images_to_process)} images for video generation (max: {max_videos})")
    print("\nSelection Results:")
    print("=" * 80)
    
    for i, meta in enumerate(selected_metadata, 1):
        score = meta['final_score']
        platform = meta['platform_suffix'] or 'unknown'
        descriptor = meta['descriptor_tokens']
        
        print(f"{i:2d}. {meta['filename']}")
        print(f"    Score: {score:.4f}")
        print(f"    Platform: {platform}")
        print(f"    Descriptor: {descriptor}")
        print(f"    Has ranking data: {'Yes' if meta['ranking_data'] else 'No'}")
        print()
    
    return selected_metadata

if __name__ == "__main__":
    print("🧪 Testing Image Selection Logic")
    print("=" * 50)
    
    # Test with different max_videos values
    for max_vids in [3, 5, 10]:
        print(f"\n--- Testing with MAX_VIDEOS = {max_vids} ---")
        os.environ['MAX_VIDEOS'] = str(max_vids)
        results = test_image_selection()
        
        if results:
            scored_count = sum(1 for r in results if r['final_score'] > 0)
            print(f"✅ Selected {len(results)} images ({scored_count} with scores, {len(results) - scored_count} fallback)")
        else:
            print("❌ No results")

