import os
import pandas as pd
from pathlib import Path
from runwayml import RunwayML
from PIL import Image
import base64
import io

def generate_more_videos(start_cluster=5, num_videos=5):
    """Generate videos from additional clusters"""
    
    # Initialize client
    api_key = os.getenv('RUNWAY_API_KEY')
    if not api_key:
        print("❌ Please set RUNWAY_API_KEY environment variable")
        return
    
    client = RunwayML(api_key=api_key)
    print("✅ RunwayML client initialized")
    
    # Load pipeline results
    try:
        prompts_df = pd.read_csv("./outputs/video_prompts.csv")
        selected_df = pd.read_csv("./outputs/selected_images.csv")
        print(f"📊 Loaded {len(prompts_df)} prompts and {len(selected_df)} images")
    except Exception as e:
        print(f"❌ Error loading results: {e}")
        return
    
    # Skip already generated clusters and select next batch
    remaining_prompts = prompts_df.iloc[start_cluster:start_cluster+num_videos]
    
    if len(remaining_prompts) == 0:
        print("⚠️  No more clusters available to generate")
        print(f"   You've already processed clusters 0-{start_cluster-1}")
        print(f"   Total available clusters: {len(prompts_df)}")
        return
    
    print(f"🎬 Generating {len(remaining_prompts)} more videos (clusters {start_cluster}-{start_cluster+len(remaining_prompts)-1})...\n")
    
    results = []
    
    for i, (idx, prompt_row) in enumerate(remaining_prompts.iterrows()):
        cluster_id = prompt_row['cluster_id']
        theme = prompt_row['theme']
        prompt_text = prompt_row['prompt']
        
        print(f"{i+1}. Cluster {cluster_id}: {theme}")
        print(f"   Prompt: {prompt_text}")
        
        # Get best image from this cluster
        cluster_images = selected_df[selected_df['cluster_id'] == cluster_id]
        if len(cluster_images) == 0:
            print(f"   ⚠️  No images found for cluster {cluster_id}")
            continue
            
        best_image = cluster_images.loc[cluster_images['aesthetic_score'].idxmax()]
        image_path = best_image['image_path']
        
        print(f"   Image: {Path(image_path).name} (score: {best_image['aesthetic_score']:.3f})")
        
        # Convert to base64
        try:
            with Image.open(image_path) as img:
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                if max(img.size) > 1024:
                    img.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
                
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG', quality=90)
                image_b64 = base64.b64encode(buffer.getvalue()).decode()
        except Exception as e:
            print(f"   ❌ Error processing image: {e}")
            continue
        
        try:
            # Submit to Runway
            print(f"   📤 Submitting to Runway...")
            
            task = client.image_to_video.create(
                model='gen3a_turbo',
                prompt_image=f"data:image/jpeg;base64,{image_b64}",
                prompt_text=prompt_text,
                duration=5,
                ratio="1280:768"
            )
            
            task_id = getattr(task, 'id', None) or str(task)
            task_status = getattr(task, 'status', 'SUBMITTED')
            
            print(f"   ✅ Task ID: {task_id} | Status: {task_status}")
            
            results.append({
                'task_id': task_id,
                'cluster_id': cluster_id,
                'theme': theme,
                'prompt': prompt_text,
                'image_path': image_path,
                'status': task_status
            })
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()
    
    # Save additional results
    if results:
        # Load existing results and append new ones
        existing_file = Path("video_outputs/generation_tasks.csv")
        if existing_file.exists():
            existing_df = pd.read_csv(existing_file)
            combined_df = pd.concat([existing_df, pd.DataFrame(results)], ignore_index=True)
        else:
            combined_df = pd.DataFrame(results)
        
        combined_df.to_csv(existing_file, index=False)
        print(f"💾 Updated task results saved to {existing_file}")
        print(f"🎉 {len(results)} additional videos submitted for generation!")
        
        print("\n🕰️ To check status of all videos:")
        print("   python download_videos.py")
    
    return results

def show_generation_options():
    """Show available generation options"""
    print("🎬 VIDEO GENERATION OPTIONS")
    print("=" * 40)
    
    # Check existing generations
    existing_file = Path("video_outputs/generation_tasks.csv")
    if existing_file.exists():
        existing_df = pd.read_csv(existing_file)
        generated_clusters = set(existing_df['cluster_id'].tolist())
        print(f"✅ Already generated: {len(generated_clusters)} videos")
        print(f"   Clusters: {sorted(generated_clusters)}")
    else:
        generated_clusters = set()
        print("🎆 No videos generated yet")
    
    # Check total available
    try:
        prompts_df = pd.read_csv("./outputs/video_prompts.csv")
        total_clusters = len(prompts_df)
        remaining_clusters = total_clusters - len(generated_clusters)
        
        print(f"📊 Total available: {total_clusters} clusters")
        print(f"🎯 Remaining: {remaining_clusters} clusters")
        
        if remaining_clusters > 0:
            print("\n🚀 GENERATION OPTIONS:")
            print(f"   1. Next 5 videos: python -c 'from generate_more_videos import *; generate_more_videos({len(generated_clusters)}, 5)'")
            print(f"   2. Next 10 videos: python -c 'from generate_more_videos import *; generate_more_videos({len(generated_clusters)}, 10)'")
            print(f"   3. ALL remaining: python -c 'from generate_more_videos import *; generate_more_videos({len(generated_clusters)}, {remaining_clusters})'")
        else:
            print("\n🎉 All clusters have been generated!")
            
    except Exception as e:
        print(f"❌ Error checking available clusters: {e}")

if __name__ == "__main__":
    show_generation_options()

