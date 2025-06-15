import os
import pandas as pd
from pathlib import Path
from runwayml import RunwayML
from PIL import Image
import base64
import io

def create_cluster_variations(clusters_to_expand=5, videos_per_cluster=3):
    """Generate additional videos from the same clusters using different images"""
    
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
        print(f"📊 Loaded pipeline data")
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return
    
    # Get the top clusters (highest scoring ones)
    top_clusters = prompts_df.head(clusters_to_expand)
    
    print(f"🎬 Creating {videos_per_cluster} additional videos for top {clusters_to_expand} clusters...\n")
    
    results = []
    
    for i, (idx, cluster_row) in enumerate(top_clusters.iterrows(), 1):
        cluster_id = cluster_row['cluster_id']
        theme = cluster_row['theme']
        original_prompt = cluster_row['prompt']
        
        print(f"{i}. Expanding Cluster {cluster_id}: {theme}")
        
        # Get all images from this cluster
        cluster_images = selected_df[selected_df['cluster_id'] == cluster_id]
        cluster_images_sorted = cluster_images.sort_values('aesthetic_score', ascending=False)
        
        if len(cluster_images_sorted) < videos_per_cluster + 1:
            available_videos = len(cluster_images_sorted) - 1  # Minus 1 for already generated
            print(f"   ⚠️  Only {available_videos} additional videos possible (limited images)")
            videos_to_create = min(videos_per_cluster, available_videos)
        else:
            videos_to_create = videos_per_cluster
        
        # Skip the first image (already used) and create videos from the rest
        for video_num in range(1, videos_to_create + 1):
            if video_num >= len(cluster_images_sorted):
                break
                
            image_row = cluster_images_sorted.iloc[video_num]
            image_path = image_row['image_path']
            score = image_row['aesthetic_score']
            
            print(f"   Video {video_num}: {Path(image_path).name} (score: {score:.3f})")
            
            # Create variation prompts for more diversity
            prompt_variations = [
                original_prompt,  # Original
                original_prompt.replace("smooth camera movements", "dynamic camera movements"),
                original_prompt.replace("golden hour lighting", "dramatic lighting"),
                original_prompt.replace("sweeping drone shots", "intimate close-up shots"),
                original_prompt.replace("cinematic depth of field", "vibrant colors and sharp focus")
            ]
            
            # Use different prompt variation for each video
            prompt_to_use = prompt_variations[video_num % len(prompt_variations)]
            
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
                print(f"     ❌ Error processing image: {e}")
                continue
            
            try:
                # Submit to Runway
                print(f"     📤 Submitting variation {video_num}...")
                
                task = client.image_to_video.create(
                    model='gen3a_turbo',
                    prompt_image=f"data:image/jpeg;base64,{image_b64}",
                    prompt_text=prompt_to_use,
                    duration=5,
                    ratio="1280:768"
                )
                
                task_id = getattr(task, 'id', None) or str(task)
                task_status = getattr(task, 'status', 'SUBMITTED')
                
                print(f"     ✅ Task ID: {task_id} | Status: {task_status}")
                
                results.append({
                    'task_id': task_id,
                    'cluster_id': cluster_id,
                    'theme': f"{theme} (Variation {video_num})",
                    'prompt': prompt_to_use,
                    'image_path': image_path,
                    'status': task_status,
                    'variation_number': video_num,
                    'aesthetic_score': score
                })
                
            except Exception as e:
                print(f"     ❌ Error: {e}")
        
        print()
    
    # Save results
    if results:
        # Load existing and append new
        existing_file = Path("video_outputs/generation_tasks.csv")
        if existing_file.exists():
            existing_df = pd.read_csv(existing_file)
            combined_df = pd.concat([existing_df, pd.DataFrame(results)], ignore_index=True)
        else:
            combined_df = pd.DataFrame(results)
        
        combined_df.to_csv(existing_file, index=False)
        
        print(f"💾 Saved {len(results)} cluster variation tasks")
        print(f"🎉 {len(results)} additional videos submitted for generation!")
        
        print("\n🕰️ To check status and download:")
        print("   python download_videos.py")
        
        print(f"\n📊 EXPANSION SUMMARY:")
        print(f"   • Original videos: 20")
        print(f"   • New variations: {len(results)}")
        print(f"   • Total after completion: {20 + len(results)}")
        
        return results
    else:
        print("❌ No variations could be created")
        return []

def quick_expand_top_clusters():
    """Quick function to expand the top 5 clusters with 3 videos each"""
    print("🚀 QUICK EXPANSION: Top 5 Clusters x 3 Videos Each")
    print("=" * 60)
    return create_cluster_variations(clusters_to_expand=5, videos_per_cluster=3)

def massive_expansion():
    """Create variations for all 20 clusters"""
    print("🛨️ MASSIVE EXPANSION: All 20 Clusters x 2 Videos Each")
    print("=" * 60)
    return create_cluster_variations(clusters_to_expand=20, videos_per_cluster=2)

if __name__ == "__main__":
    print("🎬 CLUSTER VARIATION GENERATOR")
    print("=" * 40)
    print("\nChoose expansion level:")
    print("1. Quick Expansion (15 new videos)")
    print("2. Massive Expansion (40 new videos)")
    print("3. Custom expansion")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        quick_expand_top_clusters()
    elif choice == "2":
        massive_expansion()
    elif choice == "3":
        clusters = int(input("How many clusters to expand? "))
        videos = int(input("How many videos per cluster? "))
        create_cluster_variations(clusters, videos)
    else:
        print("Running quick expansion by default...")
        quick_expand_top_clusters()

