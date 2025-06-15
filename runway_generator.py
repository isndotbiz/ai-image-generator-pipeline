import os
import pandas as pd
import json
from pathlib import Path
from runwayml import RunwayML
from PIL import Image
import base64
import io
import time

class RunwayVideoGenerator:
    def __init__(self):
        self.output_dir = Path("./video_outputs")
        self.output_dir.mkdir(exist_ok=True)
        
        # Get API key
        api_key = os.getenv('RUNWAY_API_KEY')
        if not api_key:
            print("⚠️  Please set RUNWAY_API_KEY environment variable")
            print("   export RUNWAY_API_KEY='your-key-here'")
            print("   Get your key from: https://app.runwayml.com/")
            self.client = None
        else:
            self.client = RunwayML(api_key=api_key)
            print("✅ RunwayML client initialized")
    
    def load_results(self):
        """Load pipeline results"""
        try:
            prompts_df = pd.read_csv("./outputs/video_prompts.csv")
            selected_df = pd.read_csv("./outputs/selected_images.csv")
            print(f"📊 Loaded {len(prompts_df)} prompts and {len(selected_df)} images")
            return prompts_df, selected_df
        except Exception as e:
            print(f"❌ Error loading results: {e}")
            return None, None
    
    def image_to_base64(self, image_path):
        """Convert image to base64 for Runway API"""
        try:
            with Image.open(image_path) as img:
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Resize if too large
                if max(img.size) > 1024:
                    img.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
                
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG', quality=90)
                return base64.b64encode(buffer.getvalue()).decode()
        except Exception as e:
            print(f"⚠️  Error processing image {image_path}: {e}")
            return None
    
    def generate_videos(self, max_videos=5):
        """Generate videos for top clusters"""
        if not self.client:
            print("❌ No API key - cannot generate videos")
            return self.simulate_generation(max_videos)
        
        prompts_df, selected_df = self.load_results()
        if prompts_df is None:
            return
        
        print(f"🎬 Generating {max_videos} videos with Runway Gen-4...\n")
        
        results = []
        
        for i, (idx, prompt_row) in enumerate(prompts_df.head(max_videos).iterrows()):
            cluster_id = prompt_row['cluster_id']
            theme = prompt_row['theme']
            prompt_text = prompt_row['prompt']
            
            print(f"{i+1}. Cluster {cluster_id}: {theme}")
            print(f"   Prompt: {prompt_text}")
            
            # Get best image from this cluster
            cluster_images = selected_df[selected_df['cluster_id'] == cluster_id]
            best_image = cluster_images.loc[cluster_images['aesthetic_score'].idxmax()]
            image_path = best_image['image_path']
            
            print(f"   Image: {Path(image_path).name} (score: {best_image['aesthetic_score']:.3f})")
            
            # Convert to base64
            image_b64 = self.image_to_base64(image_path)
            if not image_b64:
                continue
            
            try:
                # Submit to Runway
                print(f"   📤 Submitting to Runway...")
                
                # Use gen3a_turbo (confirmed available)
                task = self.client.image_to_video.create(
                    model='gen3a_turbo',
                    prompt_image=f"data:image/jpeg;base64,{image_b64}",
                    prompt_text=prompt_text,
                    duration=5,
                    ratio="1280:768"  # Correct ratio format
                )
                
                # Handle different response formats
                task_id = getattr(task, 'id', None) or getattr(task, 'task_id', None) or str(task)
                task_status = getattr(task, 'status', 'SUBMITTED')
                
                print(f"   ✅ Task ID: {task_id} | Status: {task_status}")
                
                results.append({
                    'task_id': task_id,
                    'cluster_id': cluster_id,
                    'theme': theme,
                    'prompt': prompt_text,
                    'image_path': image_path,
                    'status': task_status,
                    'response_object': str(task)  # For debugging
                })
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
            
            print()
        
        # Save results
        if results:
            results_df = pd.DataFrame(results)
            results_path = self.output_dir / "generation_tasks.csv"
            results_df.to_csv(results_path, index=False)
            print(f"💾 Task results saved to {results_path}")
        
        return results
    
    def simulate_generation(self, max_videos=5):
        """Simulate video generation without API key"""
        prompts_df, selected_df = self.load_results()
        if prompts_df is None:
            return
        
        print(f"🎬 SIMULATION: What would be generated with Runway Gen-4...\n")
        
        for i, (idx, prompt_row) in enumerate(prompts_df.head(max_videos).iterrows()):
            cluster_id = prompt_row['cluster_id']
            theme = prompt_row['theme']
            prompt_text = prompt_row['prompt']
            
            # Get best image from this cluster
            cluster_images = selected_df[selected_df['cluster_id'] == cluster_id]
            best_image = cluster_images.loc[cluster_images['aesthetic_score'].idxmax()]
            image_path = best_image['image_path']
            
            print(f"{i+1}. 🎬 VIDEO FOR CLUSTER {cluster_id}")
            print(f"   🎨 Theme: {theme}")
            print(f"   📝 Prompt: {prompt_text}")
            print(f"   📸 Source: {Path(image_path).name} (score: {best_image['aesthetic_score']:.3f})")
            print(f"   🗺️ Output: cluster_{cluster_id:02d}_{theme.split()[0].lower()}_video.mp4")
            print()
        
        print("🔑 To actually generate videos, set your RUNWAY_API_KEY and run again!")
    
    def check_status(self):
        """Check status of submitted tasks"""
        if not self.client:
            print("❌ No API key - cannot check status")
            return
        
        tasks_file = self.output_dir / "generation_tasks.csv"
        if not tasks_file.exists():
            print("❌ No tasks file found. Generate videos first.")
            return
        
        tasks_df = pd.read_csv(tasks_file)
        print(f"🔍 Checking status of {len(tasks_df)} tasks...\n")
        
        for idx, task_row in tasks_df.iterrows():
            task_id = task_row['task_id']
            try:
                task = self.client.tasks.retrieve(task_id)
                print(f"Task {task_id}: {task.status}")
                
                if task.status == 'SUCCEEDED' and task.output:
                    video_url = task.output[0]
                    print(f"   ✅ Video ready: {video_url}")
                elif task.status == 'FAILED':
                    print(f"   ❌ Task failed")
                    
            except Exception as e:
                print(f"   ⚠️  Error checking {task_id}: {e}")

def main():
    print("🎬 Runway Gen-4 Video Generator")
    print("=" * 40)
    
    generator = RunwayVideoGenerator()
    
    # Generate videos
    generator.generate_videos(max_videos=5)
    
    # If API key exists, offer to check status
    if generator.client:
        print("\n🕰️ To check task status later, run:")
        print("   python -c 'from runway_generator import RunwayVideoGenerator; RunwayVideoGenerator().check_status()'")

if __name__ == "__main__":
    main()

