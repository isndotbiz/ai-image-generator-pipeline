#!/usr/bin/env -S bash -c 'source ~/menv/bin/activate && exec "$0" "$@"'
"""
Intelligent Video Generator
Generates videos from selected high-quality images with improved prompts and quality control
"""

import os
import json
import requests
import time
import base64
from pathlib import Path
from datetime import datetime
import random
from runwayml import RunwayML

class IntelligentVideoGenerator:
    def __init__(self, images_dir="video_queue"):
        self.images_dir = Path(images_dir)
        self.selected_dir = Path("video_queue")
        self.video_outputs_dir = Path("video_outputs")
        self.video_outputs_dir.mkdir(exist_ok=True)
        
        # Initialize RunwayML client
        self.api_key = os.getenv('RUNWAYML_API_SECRET')
        if self.api_key:
            self.client = RunwayML(api_key=self.api_key)
        else:
            self.client = None
        
        # Video generation parameters
        self.video_params = {
            "duration": 4,  # seconds
            "ratio": "16:9",
            "motion_strength": 3,  # Lower for more controlled motion
            "seed": None
        }
        
        # Improved prompts for better video quality
        self.motion_prompts = {
            "subtle": [
                "gentle camera movement, slow zoom in, cinematic lighting",
                "soft focus transition, elegant reveal, professional cinematography",
                "smooth dolly movement, steady camera, luxury ambiance",
                "gradual depth of field change, sophisticated presentation",
                "calm atmospheric movement, premium lighting, stable composition"
            ],
            "product_focus": [
                "product showcase rotation, premium display, studio lighting",
                "elegant product reveal, sophisticated presentation, clean aesthetics",
                "luxury item focus, professional photography style, minimal movement",
                "high-end product demonstration, premium brand presentation",
                "sophisticated product display, corporate elegance, refined movement"
            ],
            "environmental": [
                "ambient environmental movement, natural lighting changes",
                "subtle atmospheric shifts, organic lighting variation",
                "gentle environmental animation, realistic ambiance",
                "natural scene progression, environmental storytelling",
                "atmospheric depth creation, immersive environment"
            ]
        }
        
        # Content type detection patterns
        self.content_patterns = {
            "watch": "product_focus",
            "rolex": "product_focus",
            "camera": "product_focus",
            "leica": "product_focus",
            "bitcoin": "product_focus",
            "coin": "product_focus",
            "amex": "product_focus",
            "centurion": "product_focus",
            "iphone": "product_focus",
            "harley": "environmental",
            "davidson": "environmental",
            "rug": "environmental",
            "persian": "environmental",
            "throw": "environmental",
            "cashmere": "environmental",
            "decanter": "product_focus",
            "wine": "product_focus"
        }
    
    def detect_content_type(self, content_source):
        """Detect content type from filename or descriptor tokens to choose appropriate motion
        
        Args:
            content_source: Either a filename string or descriptor tokens (list/string)
        """
        # Handle different input types
        if isinstance(content_source, list):
            # If descriptor tokens are provided as a list, join them
            search_text = " ".join(str(token) for token in content_source).lower()
        else:
            # If it's a string (filename), use it directly
            search_text = str(content_source).lower()
        
        for pattern, motion_type in self.content_patterns.items():
            if pattern in search_text:
                return motion_type
        
        return "subtle"  # Default to subtle motion
    
    def generate_video_prompt(self, image_path, ranking_data=None, descriptor_tokens=None, platform_suffix=None):
        """Generate intelligent video prompt based on image content and quality
        
        Args:
            image_path: Path to the image file
            ranking_data: Optional ranking data from image analysis
            descriptor_tokens: Three descriptor tokens extracted from filename
            platform_suffix: Platform suffix (ig, tt, tw) for consistent naming
        
        Returns:
            String in format: "<chosen base motion>, <location/product/quality modifiers>, no text changes, maintain original composition, professional quality, stable objects"
        """
        filename = image_path.name
        
        # Use descriptor tokens if provided, otherwise fall back to filename detection
        content_source = descriptor_tokens if descriptor_tokens else filename
        content_type = self.detect_content_type(content_source)
        
        # Get base motion prompt
        motion_options = self.motion_prompts[content_type]
        chosen_base_motion = random.choice(motion_options)
        
        # Build location/product/quality modifiers
        modifier_phrases = []
        
        # Add location-specific enhancements (use descriptor tokens if available)
        search_source = descriptor_tokens or filename
        if isinstance(search_source, list):
            search_text = " ".join(str(token) for token in search_source).lower()
        else:
            search_text = str(search_source).lower()
            
        if "maldives" in search_text:
            modifier_phrases.append("tropical luxury setting")
        elif "london" in search_text:
            modifier_phrases.append("sophisticated urban elegance")
        elif "paris" in search_text:
            modifier_phrases.append("refined Parisian aesthetics")
        elif "tokyo" in search_text:
            modifier_phrases.append("modern metropolitan style")
        elif "dubai" in search_text:
            modifier_phrases.append("opulent desert luxury")
        
        # Add quality-based enhancements
        if ranking_data and ranking_data.get('final_score', 0) > 0.8:
            modifier_phrases.append("premium cinematic quality")
        
        # Add platform-specific optimizations using platform_suffix if provided
        if platform_suffix:
            if platform_suffix == "ig":
                modifier_phrases.append("Instagram-optimized framing")
            elif platform_suffix == "tt":
                modifier_phrases.append("TikTok vertical engagement")
            elif platform_suffix == "tw":
                modifier_phrases.append("Twitter horizontal presentation")
        else:
            # Fall back to filename detection if platform_suffix not provided
            if "_ig_" in filename:
                modifier_phrases.append("Instagram-optimized framing")
            elif "_tt_" in filename:
                modifier_phrases.append("TikTok vertical engagement")
            elif "_tw_" in filename:
                modifier_phrases.append("Twitter horizontal presentation")
        
        # Combine all elements in the specified format
        location_product_quality_modifiers = ", ".join(modifier_phrases) if modifier_phrases else ""
        
        # Build final prompt in the required format
        if location_product_quality_modifiers:
            full_prompt = f"{chosen_base_motion}, {location_product_quality_modifiers}, no text changes, maintain original composition, professional quality, stable objects"
        else:
            full_prompt = f"{chosen_base_motion}, no text changes, maintain original composition, professional quality, stable objects"
        
        return full_prompt
    
    def generate_video_from_image_sdk(self, image_path, prompt):
        """Generate video using RunwayML SDK"""
        if not self.client:
            raise ValueError("RUNWAYML_API_SECRET environment variable not set")
        
        # Use the SDK to generate video directly
        task = self.client.image_to_video.create(
            prompt_image=str(image_path),
            prompt_text=prompt,
            model="gen3a_turbo",
            ratio="16:9",
            duration=4
        )
        
        return task
    
    def kick_off_image_to_video_tasks(self, selected_images_with_prompts, max_videos=None):
        """Kick off RunwayML image-to-video tasks for selected images and store in queue for polling
        
        Args:
            selected_images_with_prompts: List of tuples (image_path, prompt) or list of dicts with image_path and prompt
            max_videos: Maximum number of videos to process (optional)
        
        Returns:
            List of task queue items for polling, each containing:
            - task_id: RunwayML task ID
            - image_path: Path to source image
            - prompt: Text prompt used
            - target_filename_stub: Calculated filename stub for final video
            - timestamp: When task was created
        """
        if not self.client:
            raise ValueError("RUNWAYML_API_SECRET environment variable not set")
        
        # Handle different input formats
        if not selected_images_with_prompts:
            print("❌ No selected images provided")
            return []
        
        # Convert to consistent format if needed
        processed_items = []
        for item in selected_images_with_prompts:
            if isinstance(item, tuple):
                image_path, prompt = item
            elif isinstance(item, dict):
                image_path = item.get('image_path')
                prompt = item.get('prompt')
            else:
                print(f"⚠️ Skipping invalid item format: {item}")
                continue
            
            if not image_path or not prompt:
                print(f"⚠️ Skipping item with missing image_path or prompt: {item}")
                continue
                
            processed_items.append((Path(image_path), prompt))
        
        # Apply max_videos limit if specified
        if max_videos:
            processed_items = processed_items[:max_videos]
        
        print(f"🚀 Kicking off {len(processed_items)} RunwayML image-to-video tasks...")
        
        task_queue = []
        
        for i, (image_path, prompt) in enumerate(processed_items, 1):
            try:
                print(f"\n📽️ Processing {i}/{len(processed_items)}: {image_path.name}")
                print(f"📝 Prompt: {prompt}")
                
                # Create task using gen4_turbo model as specified
                # Convert image to base64 data URL since API requires HTTPS URLs or data URLs
                import base64
                with open(image_path, 'rb') as img_file:
                    img_data = img_file.read()
                    img_b64 = base64.b64encode(img_data).decode('utf-8')
                    img_mime = 'image/png' if str(image_path).lower().endswith('.png') else 'image/jpeg'
                    data_url = f"data:{img_mime};base64,{img_b64}"
                
                task = self.client.image_to_video.create(
                    model="gen4_turbo",
                    prompt_image=data_url,
                    prompt_text=prompt,
                    ratio="1280:720",
                    duration=5,
                )
                
                # Calculate target filename stub for next step
                target_filename_stub = self._calculate_target_filename_stub(image_path)
                
                # Create queue item
                queue_item = {
                    'task_id': task.id,
                    'image_path': str(image_path),
                    'prompt': prompt,
                    'target_filename_stub': target_filename_stub,
                    'timestamp': datetime.now().isoformat(),
                    'status': 'PENDING'
                }
                
                task_queue.append(queue_item)
                
                print(f"✅ Task created: {task.id}")
                print(f"📄 Target filename stub: {target_filename_stub}")
                
                # Small delay to avoid rate limiting
                if i < len(processed_items):
                    time.sleep(2)
                    
            except Exception as e:
                print(f"❌ Error creating task for {image_path.name}: {e}")
                # Still add to queue with error status for tracking
                queue_item = {
                    'task_id': None,
                    'image_path': str(image_path),
                    'prompt': prompt,
                    'target_filename_stub': self._calculate_target_filename_stub(image_path),
                    'timestamp': datetime.now().isoformat(),
                    'status': 'FAILED',
                    'error': str(e)
                }
                task_queue.append(queue_item)
        
        # Save task queue to file for persistence
        queue_file = self.video_outputs_dir / f"task_queue_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(queue_file, 'w') as f:
            json.dump(task_queue, f, indent=2)
        
        successful_tasks = sum(1 for item in task_queue if item.get('task_id'))
        print(f"\n🎬 TASK CREATION COMPLETE:")
        print(f"✅ Successful tasks: {successful_tasks}/{len(processed_items)}")
        print(f"📄 Task queue saved: {queue_file}")
        print(f"📋 Queue contains {len(task_queue)} items for polling")
        
        return task_queue
    
    def _calculate_target_filename_stub(self, image_path):
        """Calculate target filename stub for final video based on image path
        
        This creates a clean filename stub that will be used when downloading the final video.
        Format: descriptor_platform_video (without timestamp or extension)
        """
        filename = image_path.stem  # Remove extension
        
        # Remove common suffixes like _draft, numbers, etc.
        clean_filename = filename
        
        # Remove _draft suffix if present
        if '_draft' in clean_filename:
            clean_filename = clean_filename.split('_draft')[0]
        
        # Remove trailing numbers (like _01, _02, etc.)
        import re
        clean_filename = re.sub(r'_\d+$', '', clean_filename)
        
        # Add video suffix to make it clear this is a video file stub
        target_filename_stub = f"{clean_filename}_video"
        
        return target_filename_stub
    
    def create_video_generation_task(self, image_id, prompt):
        """Create video generation task on Runway"""
        generation_url = f"{self.base_url}/image_to_video"
        
        payload = {
            "promptImage": image_id,
            "promptText": prompt,
            **self.video_params
        }
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'X-Runway-Version': '2024-09-13'
        }
        
        response = requests.post(generation_url, json=payload, headers=headers)
        
        if response.status_code == 200:
            return response.json()['id']
        else:
            raise Exception(f"Generation task creation failed: {response.status_code} - {response.text}")
    
    def check_generation_status(self, task_id):
        """Check status of video generation task"""
        status_url = f"{self.base_url}/tasks/{task_id}"
        headers = {'Authorization': f'Bearer {self.api_key}'}
        
        response = requests.get(status_url, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Status check failed: {response.status_code} - {response.text}")
    
    def download_video(self, video_url, output_path):
        """Download generated video"""
        response = requests.get(video_url, stream=True)
        
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
        else:
            return False
    
    def wait_for_completion(self, task_id, max_wait_time=300):
        """Wait for video generation to complete"""
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            try:
                status = self.check_generation_status(task_id)
                
                if status['status'] == 'SUCCEEDED':
                    return status['output']
                elif status['status'] == 'FAILED':
                    error_msg = status.get('failure_reason', 'Unknown error')
                    raise Exception(f"Generation failed: {error_msg}")
                
                print(f"Status: {status['status']}, waiting...")
                time.sleep(10)
                
            except Exception as e:
                print(f"Error checking status: {e}")
                time.sleep(5)
        
        raise Exception(f"Generation timed out after {max_wait_time} seconds")
    
    def generate_video_from_image(self, image_path, ranking_data=None):
        """Generate video from a single image using RunwayML SDK"""
        try:
            print(f"\n🎬 Generating video for: {image_path.name}")
            
            # Generate intelligent prompt
            prompt = self.generate_video_prompt(image_path, ranking_data)
            print(f"📝 Prompt: {prompt}")
            
            # Generate video using SDK
            print("🚀 Starting generation with RunwayML SDK...")
            task = self.generate_video_from_image_sdk(image_path, prompt)
            print(f"⏳ Task created: {task.id}")
            
            # Wait for completion
            print("⏱️ Waiting for completion...")
            task_id = task.id
            
            # Poll for completion
            max_wait_time = 300  # 5 minutes
            start_time = time.time()
            
            while time.time() - start_time < max_wait_time:
                # Retrieve task status
                task = self.client.tasks.retrieve(task_id)
                
                if task.status == "SUCCEEDED":
                    # Download video
                    video_filename = f"{image_path.stem}_video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
                    output_path = self.video_outputs_dir / video_filename
                    
                    print("💾 Downloading video...")
                    
                    # Get video URL from task output
                    video_url = task.output[0]  # Assuming output contains video URL
                    
                    if self.download_video(video_url, output_path):
                        print(f"✅ Video saved: {output_path}")
                        return {
                            'success': True,
                            'input_image': str(image_path),
                            'output_video': str(output_path),
                            'prompt': prompt,
                            'task_id': task_id,
                            'ranking_data': ranking_data,
                            'timestamp': datetime.now().isoformat()
                        }
                    else:
                        return {
                            'success': False,
                            'error': 'Failed to download video',
                            'input_image': str(image_path),
                            'prompt': prompt,
                            'task_id': task_id
                        }
                
                elif task.status == "FAILED":
                    error_msg = getattr(task, 'failure_reason', 'Unknown error')
                    raise Exception(f"Generation failed: {error_msg}")
                
                print(f"Status: {task.status}, waiting...")
                time.sleep(10)
            
            # Timeout
            raise Exception(f"Generation timed out after {max_wait_time} seconds")
        
        except Exception as e:
            print(f"❌ Error generating video: {e}")
            return {
                'success': False,
                'error': str(e),
                'input_image': str(image_path),
                'timestamp': datetime.now().isoformat()
            }
    
    def generate_video_from_image_enhanced(self, image_path, metadata):
        """Generate video from image with enhanced metadata for better file naming"""
        try:
            print(f"\n🎬 Generating video for: {image_path.name}")
            
            # Generate intelligent prompt using metadata
            prompt = self.generate_video_prompt(
                image_path, 
                metadata['ranking_data'], 
                metadata['descriptor_tokens'], 
                metadata['platform_suffix']
            )
            print(f"📝 Prompt: {prompt}")
            
            # Generate video using SDK
            print("🚀 Starting generation with RunwayML SDK...")
            task = self.generate_video_from_image_sdk(image_path, prompt)
            print(f"⏳ Task created: {task.id}")
            
            # Wait for completion
            print("⏱️ Waiting for completion...")
            task_id = task.id
            
            # Poll for completion
            max_wait_time = 300  # 5 minutes
            start_time = time.time()
            
            while time.time() - start_time < max_wait_time:
                # Retrieve task status
                task = self.client.tasks.retrieve(task_id)
                
                if task.status == "SUCCEEDED":
                    # Create enhanced video filename using metadata
                    descriptor = metadata['descriptor_tokens']
                    platform = metadata['platform_suffix']
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    
                    if platform:
                        video_filename = f"{descriptor}_{platform}_video_{timestamp}.mp4"
                    else:
                        video_filename = f"{descriptor}_video_{timestamp}.mp4"
                    
                    output_path = self.video_outputs_dir / video_filename
                    
                    print("💾 Downloading video...")
                    print(f"📝 Enhanced filename: {video_filename}")
                    
                    # Get video URL from task output
                    video_url = task.output[0]  # Assuming output contains video URL
                    
                    if self.download_video(video_url, output_path):
                        print(f"✅ Video saved: {output_path}")
                        return {
                            'success': True,
                            'input_image': str(image_path),
                            'output_video': str(output_path),
                            'video_filename': video_filename,
                            'descriptor_tokens': descriptor,
                            'platform_suffix': platform,
                            'final_score': metadata['final_score'],
                            'prompt': prompt,
                            'task_id': task_id,
                            'ranking_data': metadata['ranking_data'],
                            'timestamp': datetime.now().isoformat()
                        }
                    else:
                        return {
                            'success': False,
                            'error': 'Failed to download video',
                            'input_image': str(image_path),
                            'prompt': prompt,
                            'task_id': task_id,
                            'metadata': metadata
                        }
                
                elif task.status == "FAILED":
                    error_msg = getattr(task, 'failure_reason', 'Unknown error')
                    raise Exception(f"Generation failed: {error_msg}")
                
                print(f"Status: {task.status}, waiting...")
                time.sleep(10)
            
            # Timeout
            raise Exception(f"Generation timed out after {max_wait_time} seconds")
        
        except Exception as e:
            print(f"❌ Error generating video: {e}")
            return {
                'success': False,
                'error': str(e),
                'input_image': str(image_path),
                'metadata': metadata,
                'timestamp': datetime.now().isoformat()
            }
    
    def load_ranking_data(self):
        """Load latest ranking data for intelligent processing"""
        # Check multiple possible locations for ranking files
        search_dirs = [Path("images"), self.images_dir, Path("video_queue"), Path(".")]
        
        all_ranking_files = []
        for search_dir in search_dirs:
            ranking_files = list(search_dir.glob("*ranking*.json"))
            all_ranking_files.extend(ranking_files)
        
        if not all_ranking_files:
            return {}
        
        # Find the most recent ranking file
        latest_file = max(all_ranking_files, key=os.path.getctime)
        
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
    
    def generate_videos_from_selected(self, max_videos=None):
        """Generate videos from selected high-quality images with enhanced selection logic"""
        # Get max_videos from environment variable if not provided
        if max_videos is None:
            max_videos = int(os.getenv('MAX_VIDEOS', '10'))
        
        selected_images = list(self.selected_dir.glob("*.png"))
        
        if not selected_images:
            print("❌ No selected images found. Run image ranking first.")
            return []
        
        # Load ranking data for intelligent processing
        ranking_data = self.load_ranking_data()
        
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
        
        print(f"🎬 Selected {len(images_to_process)} images for video generation (max: {max_videos})")
        for i, meta in enumerate(selected_metadata, 1):
            score = meta['final_score']
            platform = meta['platform_suffix'] or 'unknown'
            print(f"  {i}. {meta['filename']} (score: {score:.3f}, platform: {platform})")
        
        print(f"🎬 Starting video generation for {len(images_to_process)} images...")
        
        results = []
        successful_videos = 0
        
        for i, meta in enumerate(selected_metadata, 1):
            image_path = meta['image_path']
            print(f"\n📽️ Processing {i}/{len(selected_metadata)}")
            print(f"📄 Image: {meta['filename']}")
            print(f"🏷️ Descriptor: {meta['descriptor_tokens']}")
            print(f"📱 Platform: {meta['platform_suffix'] or 'unknown'}")
            print(f"⭐ Score: {meta['final_score']:.3f}")
            
            # Generate video with enhanced metadata
            result = self.generate_video_from_image_enhanced(image_path, meta)
            results.append(result)
            
            if result['success']:
                successful_videos += 1
                print(f"✅ Success! ({successful_videos}/{i} completed)")
            else:
                print(f"❌ Failed: {result.get('error', 'Unknown error')}")
            
            # Add delay between generations to avoid rate limiting
            if i < len(selected_metadata):
                print("⏱️ Waiting 30 seconds before next generation...")
                time.sleep(30)
        
        # Save results
        results_file = self.video_outputs_dir / f"video_generation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n🎬 VIDEO GENERATION COMPLETE:")
        print(f"✅ Successful: {successful_videos}/{len(images_to_process)}")
        print(f"📄 Results saved: {results_file}")
        
        return results
    
    def get_stats(self):
        """Get video generation statistics - uses proper images/ subdirectory patterns"""
        video_files = list(self.video_outputs_dir.glob("*.mp4"))
        result_files = list(self.video_outputs_dir.glob("video_generation_results_*.json"))
        
        stats = {
            'total_videos': len(video_files),
            'selected_images': len(list(self.selected_dir.glob("*.png"))),
            'result_reports': len(result_files)
        }
        
        # Get success rate from latest results
        if result_files:
            latest_results = max(result_files, key=os.path.getctime)
            with open(latest_results, 'r') as f:
                results = json.load(f)
            
            successful = sum(1 for r in results if r.get('success', False))
            stats['latest_success_rate'] = successful / len(results) if results else 0
            stats['latest_batch_size'] = len(results)
        
        return stats

def main():
    generator = IntelligentVideoGenerator()
    
    print("🎬 Starting Intelligent Video Generation...")
    
    # Check if API key is set
    if not generator.api_key:
        print("❌ RUNWAYML_API_SECRET environment variable not set")
        print("Please set your Runway API key: export RUNWAYML_API_SECRET='your_key_here'")
        return
    
    # Generate videos from selected images
    results = generator.generate_videos_from_selected(max_videos=10)
    
    # Show final stats
    stats = generator.get_stats()
    print(f"\n📊 FINAL STATISTICS:")
    print(f"🎬 Total videos: {stats['total_videos']}")
    print(f"📸 Selected images: {stats['selected_images']}")
    print(f"📈 Latest success rate: {stats.get('latest_success_rate', 0):.1%}")

if __name__ == "__main__":
    main()

