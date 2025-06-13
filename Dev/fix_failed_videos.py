import os
import pandas as pd
from pathlib import Path
from runwayml import RunwayML
from PIL import Image
import base64
import io

def fix_failed_videos():
    """Regenerate failed videos with alternative images/prompts"""
    
    # Initialize client
    api_key = os.getenv('RUNWAY_API_KEY')
    if not api_key:
        print("❌ Please set RUNWAY_API_KEY environment variable")
        return
    
    client = RunwayML(api_key=api_key)
    print("✅ RunwayML client initialized")
    
    # Load data
    try:
        prompts_df = pd.read_csv("./outputs/video_prompts.csv")
        selected_df = pd.read_csv("./outputs/selected_images.csv")
        tasks_df = pd.read_csv("./video_outputs/generation_tasks.csv")
        print(f"📊 Loaded pipeline data")
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return
    
    # Check which videos failed
    print("🔍 Checking for failed videos...")
    
    failed_clusters = []
    for idx, row in tasks_df.iterrows():
        task_id = row['task_id']
        cluster_id = row['cluster_id']
        
        try:
            task = client.tasks.retrieve(task_id)
            if task.status == 'FAILED':
                failed_clusters.append({
                    'cluster_id': cluster_id,
                    'task_id': task_id,
                    'original_theme': row['theme'],
                    'original_prompt': row['prompt']
                })
                print(f"❌ Cluster {cluster_id}: FAILED")
        except Exception as e:
            print(f"⚠️  Error checking task {task_id}: {e}")
    
    if not failed_clusters:
        print("✅ No failed videos found! All videos generated successfully.")
        return
    
    print(f"\n🔧 Fixing {len(failed_clusters)} failed videos...\n")
    
    new_results = []
    
    for i, failed in enumerate(failed_clusters, 1):
        cluster_id = failed['cluster_id']
        print(f"{i}. Fixing Cluster {cluster_id}...")
        
        # Get all images from this cluster (not just the best one)
        cluster_images = selected_df[selected_df['cluster_id'] == cluster_id]
        
        if len(cluster_images) == 0:
            print(f"   ⚠️  No images found for cluster {cluster_id}")
            continue
        
        # Try alternative images (2nd best, 3rd best, etc.)
        cluster_images_sorted = cluster_images.sort_values('aesthetic_score', ascending=False)
        
        success = False
        for img_idx, (_, image_row) in enumerate(cluster_images_sorted.iterrows()):
            if img_idx >= 3:  # Try max 3 different images
                break
                
            image_path = image_row['image_path']
            score = image_row['aesthetic_score']
            
            print(f"   Trying image {img_idx + 1}: {Path(image_path).name} (score: {score:.3f})")
            
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
            
            # Get original prompt but make it simpler if it failed before
            original_prompt = failed['original_prompt']
            
            # Simplify prompt for retry
            if 'luxury' in original_prompt.lower():
                simplified_prompt = "Elegant luxury product showcase with smooth camera movement and premium lighting"
            elif 'travel' in original_prompt.lower():
                simplified_prompt = "Cinematic travel montage with smooth camera movements and vibrant colors"
            else:
                simplified_prompt = "Professional product showcase with smooth camera movements and balanced lighting"
            
            print(f"   Using simplified prompt: {simplified_prompt}")
            
            try:
                # Submit to Runway with simplified prompt
                print(f"   📤 Submitting to Runway (attempt {img_idx + 1})...")
                
                task = client.image_to_video.create(
                    model='gen3a_turbo',
                    prompt_image=f"data:image/jpeg;base64,{image_b64}",
                    prompt_text=simplified_prompt,
                    duration=5,
                    ratio="1280:768"
                )
                
                task_id = getattr(task, 'id', None) or str(task)
                task_status = getattr(task, 'status', 'SUBMITTED')
                
                print(f"   ✅ NEW Task ID: {task_id} | Status: {task_status}")
                
                new_results.append({
                    'task_id': task_id,
                    'cluster_id': cluster_id,
                    'theme': failed['original_theme'] + ' (FIXED)',
                    'prompt': simplified_prompt,
                    'image_path': image_path,
                    'status': task_status,
                    'retry_attempt': img_idx + 1
                })
                
                success = True
                break
                
            except Exception as e:
                print(f"   ❌ Error on attempt {img_idx + 1}: {e}")
                continue
        
        if not success:
            print(f"   ❌ Could not fix cluster {cluster_id} after trying multiple images")
        
        print()
    
    # Save new results
    if new_results:
        # Add to existing tasks file
        updated_df = pd.concat([tasks_df, pd.DataFrame(new_results)], ignore_index=True)
        updated_df.to_csv("./video_outputs/generation_tasks.csv", index=False)
        
        print(f"💾 Saved {len(new_results)} fixed video tasks")
        print(f"🎉 Fixed videos submitted for generation!")
        
        print("\n🕰️ To check status and download fixed videos:")
        print("   python download_videos.py")
        
        return new_results
    else:
        print("❌ Could not fix any failed videos")
        return []

if __name__ == "__main__":
    fix_failed_videos()

