#!/usr/bin/env -S bash -c 'source ~/menv/bin/activate && exec "$0" "$@"'
"""
Intelligent Video Generator
Generates videos from selected high-quality images with improved prompts and quality control
"""

import os
import json
import requests
import time
from pathlib import Path
from datetime import datetime
import random

class IntelligentVideoGenerator:
    def __init__(self, images_dir="images"):
        self.images_dir = Path(images_dir)
        self.selected_dir = self.images_dir / "selected_for_video"
        self.video_outputs_dir = Path("video_outputs")
        self.video_outputs_dir.mkdir(exist_ok=True)
        
        # Runway API configuration
        self.api_key = os.getenv('RUNWAY_API_KEY')
        self.base_url = "https://api.runwayml.com/v1"
        
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
    
    def detect_content_type(self, filename):
        """Detect content type from filename to choose appropriate motion"""
        filename_lower = filename.lower()
        
        for pattern, motion_type in self.content_patterns.items():
            if pattern in filename_lower:
                return motion_type
        
        return "subtle"  # Default to subtle motion
    
    def generate_video_prompt(self, image_path, ranking_data=None):
        """Generate intelligent video prompt based on image content and quality"""
        filename = image_path.name
        content_type = self.detect_content_type(filename)
        
        # Get base motion prompt
        motion_options = self.motion_prompts[content_type]
        base_prompt = random.choice(motion_options)
        
        # Enhance prompt based on content
        enhancement_phrases = []
        
        # Add location-specific enhancements
        if "maldives" in filename.lower():
            enhancement_phrases.append("tropical luxury setting")
        elif "london" in filename.lower():
            enhancement_phrases.append("sophisticated urban elegance")
        elif "paris" in filename.lower():
            enhancement_phrases.append("refined Parisian aesthetics")
        elif "tokyo" in filename.lower():
            enhancement_phrases.append("modern metropolitan style")
        elif "dubai" in filename.lower():
            enhancement_phrases.append("opulent desert luxury")
        
        # Add quality-based enhancements
        if ranking_data and ranking_data.get('final_score', 0) > 0.8:
            enhancement_phrases.append("premium cinematic quality")
        
        # Add platform-specific optimizations
        if "_ig_" in filename:
            enhancement_phrases.append("Instagram-optimized framing")
        elif "_tt_" in filename:
            enhancement_phrases.append("TikTok vertical engagement")
        elif "_tw_" in filename:
            enhancement_phrases.append("Twitter horizontal presentation")
        
        # Combine all elements
        full_prompt = base_prompt
        if enhancement_phrases:
            full_prompt += ", " + ", ".join(enhancement_phrases)
        
        # Add universal quality modifiers
        full_prompt += ", no text changes, maintain original composition, professional quality, stable objects"
        
        return full_prompt
    
    def upload_image_to_runway(self, image_path):
        """Upload image to Runway for video generation"""
        if not self.api_key:
            raise ValueError("RUNWAY_API_KEY environment variable not set")
        
        upload_url = f"{self.base_url}/uploads"
        
        with open(image_path, 'rb') as image_file:
            files = {'file': image_file}
            headers = {'Authorization': f'Bearer {self.api_key}'}
            
            response = requests.post(upload_url, files=files, headers=headers)
            
            if response.status_code == 200:
                return response.json()['id']
            else:
                raise Exception(f"Upload failed: {response.status_code} - {response.text}")
    
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
            'Content-Type': 'application/json'
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
        """Generate video from a single image"""
        try:
            print(f"\n🎬 Generating video for: {image_path.name}")
            
            # Generate intelligent prompt
            prompt = self.generate_video_prompt(image_path, ranking_data)
            print(f"📝 Prompt: {prompt}")
            
            # Upload image
            print("📤 Uploading image...")
            image_id = self.upload_image_to_runway(image_path)
            print(f"✅ Image uploaded: {image_id}")
            
            # Create generation task
            print("🚀 Starting generation...")
            task_id = self.create_video_generation_task(image_id, prompt)
            print(f"⏳ Task created: {task_id}")
            
            # Wait for completion
            print("⏱️ Waiting for completion...")
            output_urls = self.wait_for_completion(task_id)
            
            # Download video
            video_filename = f"{image_path.stem}_video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
            output_path = self.video_outputs_dir / video_filename
            
            print("💾 Downloading video...")
            if self.download_video(output_urls[0], output_path):
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
        
        except Exception as e:
            print(f"❌ Error generating video: {e}")
            return {
                'success': False,
                'error': str(e),
                'input_image': str(image_path),
                'timestamp': datetime.now().isoformat()
            }
    
    def load_ranking_data(self):
        """Load latest ranking data for intelligent processing"""
        ranking_files = list(self.images_dir.glob("image_rankings_*.json"))
        if not ranking_files:
            return {}
        
        latest_file = max(ranking_files, key=os.path.getctime)
        with open(latest_file, 'r') as f:
            rankings = json.load(f)
        
        # Convert to dictionary for quick lookup
        return {r['filename']: r for r in rankings}
    
    def generate_videos_from_selected(self, max_videos=10):
        """Generate videos from selected high-quality images - uses images/selected_for_video/ pattern"""
        selected_images = list(self.selected_dir.glob("*.png"))
        
        if not selected_images:
            print("❌ No selected images found. Run image ranking first.")
            return []
        
        # Load ranking data for intelligent processing
        ranking_data = self.load_ranking_data()
        
        # Sort by ranking score if available
        def get_score(img):
            data = ranking_data.get(img.name, {})
            return data.get('final_score', 0)
        
        selected_images.sort(key=get_score, reverse=True)
        
        # Limit to max_videos
        images_to_process = selected_images[:max_videos]
        
        print(f"🎬 Starting video generation for {len(images_to_process)} images...")
        
        results = []
        successful_videos = 0
        
        for i, image_path in enumerate(images_to_process, 1):
            print(f"\n📽️ Processing {i}/{len(images_to_process)}")
            
            # Get ranking data for this image
            img_ranking = ranking_data.get(image_path.name)
            
            # Generate video
            result = self.generate_video_from_image(image_path, img_ranking)
            results.append(result)
            
            if result['success']:
                successful_videos += 1
                print(f"✅ Success! ({successful_videos}/{i} completed)")
            else:
                print(f"❌ Failed: {result.get('error', 'Unknown error')}")
            
            # Add delay between generations to avoid rate limiting
            if i < len(images_to_process):
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
        print("❌ RUNWAY_API_KEY environment variable not set")
        print("Please set your Runway API key: export RUNWAY_API_KEY='your_key_here'")
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

