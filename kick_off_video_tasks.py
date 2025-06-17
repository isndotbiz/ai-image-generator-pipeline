#!/usr/bin/env python3
"""
Kick Off RunwayML Image-to-Video Tasks

Demonstrates how to kick off multiple RunwayML image-to-video tasks
using the gen4_turbo model and store them in a queue for polling.

Usage:
    python kick_off_video_tasks.py [--max-videos N]
"""

import os
import sys
import argparse
from pathlib import Path
from intelligent_video_generator import IntelligentVideoGenerator

def load_selected_images_with_prompts(video_queue_dir="video_queue", max_images=None):
    """Load selected images from video_queue directory and generate prompts for them
    
    Returns:
        List of tuples (image_path, prompt)
    """
    queue_dir = Path(video_queue_dir)
    if not queue_dir.exists():
        print(f"❌ Video queue directory not found: {queue_dir}")
        return []
    
    # Get all PNG images from the queue
    image_files = list(queue_dir.glob("*.png"))
    
    if not image_files:
        print(f"❌ No PNG images found in {queue_dir}")
        return []
    
    # Apply max_images limit if specified
    if max_images:
        image_files = image_files[:max_images]
    
    print(f"📸 Found {len(image_files)} images in video queue")
    
    # Generate intelligent prompts for each image
    generator = IntelligentVideoGenerator()
    
    selected_images_with_prompts = []
    
    for image_path in image_files:
        # Generate prompt using the existing intelligent prompt generator
        prompt = generator.generate_video_prompt(image_path)
        selected_images_with_prompts.append((image_path, prompt))
        print(f"  📄 {image_path.name}")
        print(f"     🎯 Prompt: {prompt[:80]}...")
    
    return selected_images_with_prompts

def main():
    parser = argparse.ArgumentParser(
        description="Kick off RunwayML image-to-video tasks for selected images"
    )
    parser.add_argument(
        "--max-videos", 
        type=int, 
        default=None,
        help="Maximum number of videos to process (default: process all)"
    )
    parser.add_argument(
        "--queue-dir", 
        default="video_queue",
        help="Directory containing images to process (default: video_queue)"
    )
    
    args = parser.parse_args()
    
    print("🚀 Kicking off RunwayML Image-to-Video Tasks")
    print("="*50)
    
    # Check if API key is set
    if not os.getenv('RUNWAYML_API_SECRET'):
        print("❌ RUNWAYML_API_SECRET environment variable not set")
        print("Please set your Runway API key: export RUNWAYML_API_SECRET='your_key_here'")
        sys.exit(1)
    
    # Load selected images and generate prompts
    print(f"📂 Loading images from {args.queue_dir}...")
    selected_images_with_prompts = load_selected_images_with_prompts(
        args.queue_dir, 
        args.max_videos
    )
    
    if not selected_images_with_prompts:
        print("❌ No images found to process")
        sys.exit(1)
    
    # Initialize the video generator
    generator = IntelligentVideoGenerator()
    
    # Kick off all the tasks
    print(f"\n🎬 Starting RunwayML task creation...")
    task_queue = generator.kick_off_image_to_video_tasks(
        selected_images_with_prompts, 
        max_videos=args.max_videos
    )
    
    if task_queue:
        successful_tasks = [item for item in task_queue if item.get('task_id')]
        failed_tasks = [item for item in task_queue if not item.get('task_id')]
        
        print(f"\n📊 SUMMARY:")
        print(f"✅ Successfully created: {len(successful_tasks)} tasks")
        print(f"❌ Failed to create: {len(failed_tasks)} tasks")
        
        if successful_tasks:
            print(f"\n🎯 CREATED TASKS:")
            for i, item in enumerate(successful_tasks, 1):
                print(f"  {i}. Task ID: {item['task_id']}")
                print(f"     Image: {Path(item['image_path']).name}")
                print(f"     Target: {item['target_filename_stub']}")
        
        if failed_tasks:
            print(f"\n❌ FAILED TASKS:")
            for i, item in enumerate(failed_tasks, 1):
                print(f"  {i}. Image: {Path(item['image_path']).name}")
                print(f"     Error: {item.get('error', 'Unknown error')}")
        
        print(f"\n📋 Task queue ready for polling with {len(task_queue)} items")
        print(f"💡 Use check_video_status.py or similar to poll task completion")
    else:
        print("❌ No tasks were created")
        sys.exit(1)

if __name__ == "__main__":
    main()

