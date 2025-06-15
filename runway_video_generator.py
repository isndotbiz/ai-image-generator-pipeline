import os
import pandas as pd
import json
import asyncio
from pathlib import Path
from tqdm import tqdm
import base64
from runwayml import RunwayML
from PIL import Image
import io

class RunwayVideoGenerator:
    def __init__(self, api_key=None, output_dir="./video_outputs"):
        """
        Initialize the Runway video generator
        
        Args:
            api_key: Runway API key (if None, will look for RUNWAY_API_KEY env var)
            output_dir: Directory to save generated videos
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize Runway client
        if api_key is None:
            api_key = os.getenv('RUNWAY_API_KEY')
            
        if not api_key:
            print("⚠️  No API key provided. Please set RUNWAY_API_KEY environment variable or pass api_key parameter.")
            print("   You can get your API key from: https://app.runwayml.com/")
            self.client = None
        else:
            self.client = RunwayML(api_key=api_key)
            print("✅ RunwayML client initialized successfully")
    
    def load_pipeline_results(self, results_dir="./outputs"):
        """
        Load results from the complete pipeline
        
        Returns:
            dict: Pipeline results including video prompts and selected images
        """
        results_path = Path(results_dir)
        
        try:
            # Load video prompts
            prompts_df = pd.read_csv(results_path / "video_prompts.csv")
            
            # Load selected images
            selected_df = pd.read_csv(results_path / "selected_images.csv")
            
            # Load diversity report
            with open(results_path / "diversity_report.json", 'r') as f:
                diversity_report = json.load(f)
            
            print(f"📊 Loaded {len(prompts_df)} video prompts and {len(selected_df)} selected images")
            
            return {
                'video_prompts': prompts_df,
                'selected_images': selected_df,
                'diversity_report': diversity_report
            }
        
        except Exception as e:
            print(f"❌ Error loading pipeline results: {e}")
            print("   Please run complete_pipeline.py first to generate the required files.")
            return None
    
    def image_to_base64(self, image_path):
        """
        Convert image to base64 string for Runway API
        
        Args:
            image_path: Path to image file
            
        Returns:
            str: Base64 encoded image
        """
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if needed
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Resize if too large (Runway has size limits)
                max_size = 1024
                if max(img.size) > max_size:
                    img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                
                # Convert to base64
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG', quality=90)
                img_str = base64.b64encode(buffer.getvalue()).decode()
                
                return f"data:image/jpeg;base64,{img_str}"
        
        except Exception as e:
            print(f"⚠️  Error processing image {image_path}: {e}")
            return None
    
    def generate_video_from_prompt(self, prompt_data, selected_images_df, max_videos_per_cluster=1):
        """
        Generate video from prompt data using Runway Gen-4
        
        Args:
            prompt_data: Row from video_prompts.csv
            selected_images_df: DataFrame of selected images
            max_videos_per_cluster: Maximum videos to generate per cluster
            
        Returns:
            dict: Generation results
        """
        if not self.client:
            print("❌ RunwayML client not initialized. Please provide API key.")
            return None
        
        cluster_id = prompt_data['cluster_id']
        prompt_text = prompt_data['prompt']
        theme = prompt_data['theme']
        
        print(f"🎬 Generating video for Cluster {cluster_id}: {theme}")
        print(f"   Prompt: {prompt_text}")
        
        # Get images from this cluster
        cluster_images = selected_images_df[
            selected_images_df['cluster_id'] == cluster_id
        ].nlargest(max_videos_per_cluster, 'aesthetic_score')
        
        results = []
        
        for idx, image_row in cluster_images.iterrows():
            try:
                image_path = image_row['image_path']
                aesthetic_score = image_row['aesthetic_score']
                
                print(f"   📸 Using image: {Path(image_path).name} (score: {aesthetic_score:.3f})")
                
                # Convert image to base64
                image_b64 = self.image_to_base64(image_path)
                if not image_b64:
                    continue
                
                # Generate video using Runway Gen-4
                print(f"   🎥 Submitting to Runway Gen-4...")
                
                task = self.client.image_to_video.create(
                    model='gen4',
                    prompt_image=image_b64,
                    prompt_text=prompt_text,
                    duration=5,  # 5 second video
                    ratio="16:9",  # Standard video aspect ratio
                    seed=42  # For reproducible results
                )
                
                print(f"   ⏳ Task submitted with ID: {task.id}")
                print(f"   📊 Status: {task.status}")
                
                # Store result info
                result = {
                    'task_id': task.id,
                    'cluster_id': cluster_id,
                    'theme': theme,
                    'prompt': prompt_text,
                    'source_image': image_path,
                    'aesthetic_score': aesthetic_score,
                    'status': task.status,
                    'task_object': task
                }
                
                results.append(result)
                
            except Exception as e:
                print(f"   ❌ Error generating video: {e}")
                continue
        
        return results
    
    async def wait_for_completion(self, task_results, check_interval=10):
        """
        Wait for video generation tasks to complete
        
        Args:
            task_results: List of task result dictionaries
            check_interval: Seconds between status checks
            
        Returns:
            list: Updated task results with completion status
        """
        if not self.client:
            return task_results
        
        print(f"⏳ Waiting for {len(task_results)} video generation tasks to complete...")
        
        completed_results = []
        
        for result in tqdm(task_results, desc="Checking task status"):
            task_id = result['task_id']
            
            try:
                # Poll for completion
                while True:
                    task = self.client.tasks.retrieve(task_id)
                    result['status'] = task.status
                    
                    if task.status == 'SUCCEEDED':
                        result['video_url'] = task.output[0] if task.output else None
                        print(f"✅ Task {task_id} completed successfully")
                        break
                    elif task.status == 'FAILED':
                        result['error'] = "Task failed"
                        print(f"❌ Task {task_id} failed")
                        break
                    elif task.status in ['PENDING', 'RUNNING']:
                        print(f"⏳ Task {task_id} still {task.status.lower()}...")
                        await asyncio.sleep(check_interval)
                    else:
                        print(f"⚠️  Unknown status for task {task_id}: {task.status}")
                        break
                
                completed_results.append(result)
                
            except Exception as e:
                print(f"❌ Error checking task {task_id}: {e}")
                result['error'] = str(e)
                completed_results.append(result)
        
        return completed_results
    
    def download_videos(self, completed_results):
        """
        Download completed videos to local storage
        
        Args:
            completed_results: List of completed task results
            
        Returns:
            list: Results with local file paths
        """
        downloaded_results = []
        
        for result in completed_results:
            if result.get('video_url'):
                try:
                    # Create filename
                    cluster_id = result['cluster_id']
                    theme_clean = result['theme'].split('(')[0].strip().replace(' ', '_').lower()
                    filename = f"cluster_{cluster_id:02d}_{theme_clean}.mp4"
                    local_path = self.output_dir / filename
                    
                    # Download video
                    print(f"📥 Downloading video for cluster {cluster_id}...")
                    
                    import requests
                    response = requests.get(result['video_url'])
                    response.raise_for_status()
                    
                    with open(local_path, 'wb') as f:
                        f.write(response.content)
                    
                    result['local_path'] = str(local_path)
                    print(f"✅ Saved: {local_path}")
                    
                except Exception as e:
                    print(f"❌ Error downloading video: {e}")
                    result['download_error'] = str(e)
            
            downloaded_results.append(result)
        
        return downloaded_results
    
    def save_generation_report(self, final_results):
        """
        Save video generation report
        
        Args:
            final_results: List of final results with all data
        """
        report_data = []
        
        for result in final_results:
            report_data.append({
                'task_id': result.get('task_id'),
                'cluster_id': result.get('cluster_id'),
                'theme': result.get('theme'),
                'prompt': result.get('prompt'),
                'source_image': result.get('source_image'),
                'aesthetic_score': result.get('aesthetic_score'),
                'status': result.get('status'),
                'video_url': result.get('video_url'),
                'local_path': result.get('local_path'),
                'error': result.get('error', result.get('download_error'))
            })
        
        # Save as CSV
        report_df = pd.DataFrame(report_data)
        report_path = self.output_dir / "video_generation_report.csv"
        report_df.to_csv(report_path, index=False)
        
        # Save as JSON for programmatic access
        json_path = self.output_dir / "video_generation_report.json"
        with open(json_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"📊 Generation report saved to {report_path}")
        
        # Print summary
        successful = len([r for r in final_results if r.get('status') == 'SUCCEEDED'])
        failed = len([r for r in final_results if r.get('status') == 'FAILED'])
        
        print(f"\n📊 VIDEO GENERATION SUMMARY:")
        print(f"   ✅ Successful: {successful}")
        print(f"   ❌ Failed: {failed}")
        print(f"   📁 Videos saved to: {self.output_dir}")
    
    async def generate_videos_from_pipeline(self, max_clusters=5, max_videos_per_cluster=1):
        """
        Generate videos from the complete pipeline results
        
        Args:
            max_clusters: Maximum number of clusters to generate videos for
            max_videos_per_cluster: Maximum videos per cluster
        """
        print("🚀 Starting Runway Gen-4 Video Generation from Pipeline Results\n")
        
        # Load pipeline results
        pipeline_data = self.load_pipeline_results()
        if not pipeline_data:
            return
        
        video_prompts = pipeline_data['video_prompts']
        selected_images = pipeline_data['selected_images']
        
        # Take top clusters by score
        top_prompts = video_prompts.head(max_clusters)
        
        print(f"🎯 Generating videos for top {len(top_prompts)} clusters...\n")
        
        all_results = []
        
        # Generate videos for each cluster
        for idx, prompt_data in top_prompts.iterrows():
            results = self.generate_video_from_prompt(
                prompt_data, 
                selected_images, 
                max_videos_per_cluster
            )
            if results:
                all_results.extend(results)
            print()  # Empty line for readability
        
        if not all_results:
            print("❌ No videos were successfully submitted for generation")
            return
        
        print(f"📊 {len(all_results)} videos submitted for generation\n")
        
        # Wait for completion
        completed_results = await self.wait_for_completion(all_results)
        
        # Download videos
        final_results = self.download_videos(completed_results)
        
        # Save report
        self.save_generation_report(final_results)
        
        return final_results


def main():
    """
    Main function to run video generation
    """
    print("🎬 Runway Gen-4 Video Generator")
    print("=" * 50)
    
    # Check for API key
    api_key = os.getenv('RUNWAY_API_KEY')
    if not api_key:
        print("\n⚠️  RUNWAY_API_KEY environment variable not set!")
        print("\n📝 To use this script:")
        print("   1. Get your API key from: https://app.runwayml.com/")
        print("   2. Set it as an environment variable:")
        print("      export RUNWAY_API_KEY='your-api-key-here'")
        print("   3. Run this script again")
        print("\n🔧 For testing without API key, the script will show what would be generated.")
        print()
    
    # Initialize generator
    generator = RunwayVideoGenerator()
    
    # Run generation
    try:
        asyncio.run(generator.generate_videos_from_pipeline(
            max_clusters=5,  # Generate for top 5 clusters
            max_videos_per_cluster=1  # 1 video per cluster
        ))
    except Exception as e:
        print(f"❌ Error during video generation: {e}")


if __name__ == "__main__":
    main()

