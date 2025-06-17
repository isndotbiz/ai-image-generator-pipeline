#!/usr/bin/env python3
"""
Test script for image selection logic with mock ranking data
"""

import os
import json
import random
from pathlib import Path
from datetime import datetime

def create_mock_ranking_data():
    """Create mock ranking data for some video_queue images"""
    selected_dir = Path("video_queue")
    selected_images = list(selected_dir.glob("*.png"))
    
    # Create rankings for a subset of images
    mock_rankings = []
    
    for i, image_path in enumerate(selected_images[:15]):  # Mock data for first 15 images
        # Simulate different quality scores
        final_score = random.uniform(0.3, 0.9)
        
        # Give higher scores to certain patterns
        filename = image_path.name.lower()
        if "elegant" in filename:
            final_score = random.uniform(0.7, 0.95)
        elif "luxury" in filename:
            final_score = random.uniform(0.6, 0.9)
        elif "visual_content" in filename:
            final_score = random.uniform(0.4, 0.8)
        
        mock_rankings.append({
            "filename": image_path.name,
            "final_score": final_score,
            "sharpness": random.uniform(200, 800),
            "color_diversity": random.uniform(400, 700),
            "composition": random.uniform(0.02, 0.05),
            "contrast": random.uniform(50, 90),
            "problems": [],
            "file_size": image_path.stat().st_size,
            "timestamp": datetime.now().isoformat()
        })
    
    return mock_rankings

def test_image_selection_with_scores(max_videos=None):
    """Test the image selection logic with mock ranking data"""
    # Get max_videos from environment variable if not provided
    if max_videos is None:
        max_videos = int(os.getenv('MAX_VIDEOS', '5'))
    
    selected_dir = Path("video_queue")
    selected_images = list(selected_dir.glob("*.png"))
    
    if not selected_images:
        print("❌ No images found in video_queue/")
        return []
    
    print(f"Found {len(selected_images)} images in video_queue/")
    
    # Create mock ranking data
    mock_rankings = create_mock_ranking_data()
    ranking_data = {r['filename']: r for r in mock_rankings}
    
    print(f"Created mock ranking data for {len(ranking_data)} images")
    
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
    print("\nSelection Results (sorted by score):")
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
        
        # Show that this would be used for final video filename
        if platform != 'unknown':
            suggested_video_name = f"{descriptor}_{platform}_video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        else:
            suggested_video_name = f"{descriptor}_video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        print(f"    Suggested video name: {suggested_video_name}")
        print()
    
    return selected_metadata

if __name__ == "__main__":
    print("🧪 Testing Enhanced Image Selection Logic with Mock Data")
    print("=" * 60)
    
    # Test with different max_videos values
    for max_vids in [3, 5, 8]:
        print(f"\n--- Testing with MAX_VIDEOS = {max_vids} ---")
        os.environ['MAX_VIDEOS'] = str(max_vids)
        results = test_image_selection_with_scores()
        
        if results:
            scored_count = sum(1 for r in results if r['final_score'] > 0)
            total_score = sum(r['final_score'] for r in results)
            avg_score = total_score / len(results) if results else 0
            
            print(f"✅ Selected {len(results)} images:")
            print(f"   • {scored_count} with ranking scores")
            print(f"   • {len(results) - scored_count} random fallback")
            print(f"   • Average score: {avg_score:.3f}")
            print(f"   • Score range: {min(r['final_score'] for r in results):.3f} - {max(r['final_score'] for r in results):.3f}")
        else:
            print("❌ No results")

