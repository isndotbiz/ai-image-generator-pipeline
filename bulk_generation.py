#!/usr/bin/env python3
"""
Bulk Generation Script for Fortuna Bound

Creates 20 diverse images and 1 video using the enhanced pipeline.
Combines direct prompts, mantras, styles, and platforms for variety.
"""

import requests
import json
import time
import random
from datetime import datetime
from typing import List, Dict

# Import robust output system
try:
    from robust_output import log_safe, generate_descriptive_filename, workflow_manager
    ROBUST_OUTPUT_AVAILABLE = True
except ImportError:
    ROBUST_OUTPUT_AVAILABLE = False
    def log_safe(msg, level="INFO"): print(f"[{level}] {msg}")

class BulkGenerator:
    def __init__(self, base_url="http://localhost:8085"):
        self.base_url = base_url
        self.generated_images = []
        self.generation_log = []
        
        # Diverse prompt themes for variety
        self.prompt_themes = [
            # Luxury & Success
            "elegant woman in designer penthouse overlooking city skyline",
            "successful businessman in modern office with city view",
            "luxury sports car on mountain road at sunset",
            "sophisticated woman at exclusive rooftop restaurant",
            "private jet interior with business executive",
            
            # Wellness & Mindfulness  
            "serene woman meditating in zen garden at sunrise",
            "peaceful yoga session on pristine beach",
            "mindful reading in cozy library corner",
            "tranquil spa setting with natural elements",
            "mountain retreat with meditation space",
            
            # Urban & Professional
            "confident woman walking through modern city",
            "dynamic entrepreneur in startup office",
            "professional meeting in glass boardroom",
            "creative workspace with inspiring design",
            "networking event in upscale venue",
            
            # Lifestyle & Inspiration
            "inspiring home office with success symbols",
            "elegant dinner party with sophisticated guests",
            "luxury travel destination with stunning views",
            "artistic studio space with creative energy",
            "premium lifestyle brand photoshoot setting"
        ]
        
        # Style presets to rotate through
        self.styles = ["luxury", "business", "wellness", "success", "urban", "minimal", "artistic"]
        
        # Platform variety
        self.platforms = ["ig", "tt", "tw", "li", "fb"]
        
        # Aspect ratios for variety
        self.aspect_ratios = ["4:5", "1:1", "16:9", "9:16"]
        
        # Mantra categories
        self.mantra_categories = ["prosperity", "empowerment", "growth", "mindfulness", "success", "luxury"]
    
    def generate_image_via_api(self, prompt: str, style: str, platform: str, 
                              aspect_ratio: str, mantra_category: str) -> Dict:
        """Generate a single image via the web API"""
        
        url = f"{self.base_url}/api/generate-direct"
        payload = {
            "prompt": prompt,
            "style": style,
            "platform": platform,
            "aspect_ratio": aspect_ratio,
            "mantra_category": mantra_category
        }
        
        try:
            print(f"🎨 Generating: {prompt[:50]}... | Style: {style} | Platform: {platform}")
            
            response = requests.post(url, json=payload, timeout=120)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    return {
                        'success': True,
                        'filename': result.get('filename'),
                        'mantra': result.get('mantra', {}).get('text', 'No mantra'),
                        'enhanced_prompt': result.get('enhanced_prompt'),
                        'style': style,
                        'platform': platform,
                        'aspect_ratio': aspect_ratio
                    }
                else:
                    return {'success': False, 'error': result.get('error', 'Unknown error')}
            else:
                return {'success': False, 'error': f'HTTP {response.status_code}'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def generate_20_images(self) -> List[Dict]:
        """Generate 20 diverse images using different combinations"""
        
        print("\n🎯 Starting bulk generation of 20 images...")
        print("📋 Using diverse prompts, styles, platforms, and mantras\n")
        
        results = []
        
        for i in range(20):
            # Rotate through different combinations for variety
            prompt = self.prompt_themes[i % len(self.prompt_themes)]
            style = self.styles[i % len(self.styles)]
            platform = self.platforms[i % len(self.platforms)]
            aspect_ratio = self.aspect_ratios[i % len(self.aspect_ratios)]
            mantra_category = self.mantra_categories[i % len(self.mantra_categories)]
            
            print(f"[{i+1}/20] ", end="")
            
            result = self.generate_image_via_api(
                prompt, style, platform, aspect_ratio, mantra_category
            )
            
            if result['success']:
                print(f"✅ Success: {result['filename']}")
                print(f"    💫 Mantra: '{result['mantra']}'")
                results.append(result)
                self.generated_images.append(result['filename'])
            else:
                print(f"❌ Failed: {result['error']}")
                results.append(result)
            
            # Small delay between generations
            time.sleep(2)
            print()
        
        successful = len([r for r in results if r['success']])
        print(f"\n📊 Generation Summary:")
        print(f"✅ Successful: {successful}/20")
        print(f"❌ Failed: {20-successful}/20")
        
        return results
    
    def create_video_from_images(self) -> Dict:
        """Create a video from the generated images"""
        
        if len(self.generated_images) < 5:
            return {'success': False, 'error': 'Need at least 5 images for video'}
        
        print("\n🎬 Creating video from generated images...")
        
        try:
            # Use the video generation endpoint
            url = f"{self.base_url}/api/generate-videos"
            
            response = requests.post(url, json={'max_videos': 1}, timeout=300)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print("✅ Video generation completed successfully!")
                    return {'success': True, 'details': result}
                else:
                    print(f"❌ Video generation failed: {result.get('error')}")
                    return {'success': False, 'error': result.get('error')}
            else:
                error_msg = f"HTTP {response.status_code}"
                print(f"❌ Video API error: {error_msg}")
                return {'success': False, 'error': error_msg}
                
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Video generation exception: {error_msg}")
            return {'success': False, 'error': error_msg}
    
    def run_bulk_generation(self) -> Dict:
        """Run the complete bulk generation process"""
        
        start_time = datetime.now()
        print(f"🚀 Starting bulk generation at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 Target: 20 images + 1 video")
        print(f"🌐 Web app: {self.base_url}")
        
        # Generate images
        image_results = self.generate_20_images()
        
        # Create video
        video_result = self.create_video_from_images()
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        # Summary
        successful_images = len([r for r in image_results if r['success']])
        
        summary = {
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duration_minutes': duration.total_seconds() / 60,
            'images': {
                'total': 20,
                'successful': successful_images,
                'failed': 20 - successful_images,
                'filenames': self.generated_images
            },
            'video': video_result,
            'success_rate': (successful_images / 20) * 100
        }
        
        print(f"\n🎉 Bulk Generation Complete!")
        print(f"⏱️  Duration: {duration.total_seconds()/60:.1f} minutes")
        print(f"📊 Success Rate: {summary['success_rate']:.1f}%")
        print(f"🖼️  Images Created: {successful_images}/20")
        print(f"🎬 Video Created: {'✅' if video_result['success'] else '❌'}")
        
        return summary

def main():
    generator = BulkGenerator()
    summary = generator.run_bulk_generation()
    
    # Save summary to file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    summary_file = f'bulk_generation_summary_{timestamp}.json'
    
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n📄 Summary saved to: {summary_file}")

if __name__ == "__main__":
    main()

