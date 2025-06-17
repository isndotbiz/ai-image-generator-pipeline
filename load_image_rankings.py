#!/usr/bin/env python3

import json
import glob
import os
from typing import Dict, Any

def load_image_rankings() -> Dict[str, Dict[str, Any]]:
    """
    Load image ranking data from all image_rankings_*.json files.
    
    Returns:
        Dictionary keyed by filename containing ranking data.
        If no ranking files exist, returns empty dict (default scores of 0).
    """
    rankings = {}
    
    # Find all image ranking files
    ranking_files = glob.glob("images/image_rankings_*.json")
    
    if not ranking_files:
        print("No image ranking files found. Using default scores of 0.")
        return {}
    
    print(f"Found {len(ranking_files)} ranking files: {ranking_files}")
    
    # Load and merge all ranking files
    for ranking_file in ranking_files:
        try:
            with open(ranking_file, 'r') as f:
                data = json.load(f)
                
            # Each file contains a list of image rankings
            for item in data:
                filename = item['filename']
                
                # If we already have this filename, keep the one with higher final_score
                # or more recent timestamp
                if filename in rankings:
                    existing_score = rankings[filename].get('final_score', 0)
                    new_score = item.get('final_score', 0)
                    
                    if new_score > existing_score:
                        rankings[filename] = item
                        print(f"Updated {filename} with better score: {new_score:.4f}")
                else:
                    rankings[filename] = item
                    
        except Exception as e:
            print(f"Error loading {ranking_file}: {e}")
            continue
    
    print(f"Loaded rankings for {len(rankings)} images")
    return rankings

def get_quality_adjective(final_score: float) -> str:
    """
    Convert numerical quality score to descriptive adjective.
    
    Args:
        final_score: Quality score (typically 0-1 range)
        
    Returns:
        Quality adjective for use in prompts
    """
    if final_score >= 0.8:
        return "exceptional"
    elif final_score >= 0.7:
        return "high-quality"
    elif final_score >= 0.6:
        return "good-quality"
    elif final_score >= 0.5:
        return "moderate-quality"
    elif final_score >= 0.3:
        return "fair-quality"
    else:
        return "low-quality"

def get_image_priority(rankings: Dict[str, Dict[str, Any]], filename: str) -> float:
    """
    Get priority score for an image (higher = more priority).
    
    Args:
        rankings: Dictionary of image rankings
        filename: Name of the image file
        
    Returns:
        Priority score (final_score if available, 0.0 if not)
    """
    if filename in rankings:
        return rankings[filename].get('final_score', 0.0)
    return 0.0

def example_usage():
    """
    Example of how to use the image rankings for prioritization and prompt enhancement.
    """
    print("=== Loading Image Rankings ===")
    rankings = load_image_rankings()
    
    if not rankings:
        print("No ranking data available - using default scores of 0.")
        return
    
    print("\n=== Image Rankings Summary ===")
    print("-" * 60)
    
    # Sort by final_score descending for priority
    sorted_images = sorted(rankings.items(), 
                         key=lambda x: x[1].get('final_score', 0), 
                         reverse=True)
    
    for filename, data in sorted_images:
        score = data.get('final_score', 0)
        adjective = get_quality_adjective(score)
        priority = get_image_priority(rankings, filename)
        print(f"{filename:<35} | {score:.4f} | {adjective:<15} | Priority: {priority:.4f}")
    
    print("\n=== Example: Using Rankings for Prompt Enhancement ===")
    # Show how to use rankings for the top 3 images
    top_images = sorted_images[:3]
    
    for filename, data in top_images:
        adjective = get_quality_adjective(data.get('final_score', 0))
        enhanced_prompt = f"Generate a video featuring this {adjective} image: {filename}"
        print(f"• {enhanced_prompt}")
    
    print("\n=== Example: Priority-Based Selection ===")
    # Example of selecting images above a certain threshold
    high_quality_threshold = 0.6
    high_quality_images = [img for img, data in rankings.items() 
                          if data.get('final_score', 0) >= high_quality_threshold]
    
    print(f"Images with quality score >= {high_quality_threshold}: {len(high_quality_images)}")
    for img in sorted(high_quality_images, 
                     key=lambda x: rankings[x].get('final_score', 0), 
                     reverse=True)[:5]:  # Show top 5
        score = rankings[img].get('final_score', 0)
        print(f"  • {img} (score: {score:.4f})")

if __name__ == "__main__":
    example_usage()

