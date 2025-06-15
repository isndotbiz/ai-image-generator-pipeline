import os
import pandas as pd
import requests
from pathlib import Path
from runwayml import RunwayML

def download_generated_videos():
    """Download completed videos using RunwayML API"""
    
    # Initialize client
    api_key = os.getenv('RUNWAY_API_KEY')
    if not api_key:
        print("❌ No RUNWAY_API_KEY found")
        return
    
    client = RunwayML(api_key=api_key)
    
    # Read task results
    tasks_file = Path("video_outputs/generation_tasks.csv")
    if not tasks_file.exists():
        print("❌ No tasks file found")
        return
    
    df = pd.read_csv(tasks_file)
    print(f"📥 Downloading {len(df)} AI-generated videos...\n")
    
    downloaded = 0
    
    for idx, row in df.iterrows():
        task_id = row['task_id']
        theme = row['theme'].replace(' ', '_').replace('(', '').replace(')', '').lower()
        cluster_id = row['cluster_id']
        
        print(f"{idx+1}. {theme} (Cluster {cluster_id})...")
        
        try:
            # Get task details
            task = client.tasks.retrieve(task_id)
            
            if task.status == 'SUCCEEDED' and task.output:
                video_url = task.output[0]
                
                # Download video
                print(f"   📥 Downloading from Runway...")
                response = requests.get(video_url)
                
                if response.status_code == 200:
                    # Create filename
                    filename = f"video_outputs/cluster_{cluster_id:02d}_{theme}.mp4"
                    
                    with open(filename, 'wb') as f:
                        f.write(response.content)
                    
                    file_size = len(response.content) / (1024 * 1024)  # MB
                    print(f"   ✅ Saved: {filename} ({file_size:.1f}MB)")
                    downloaded += 1
                    
                else:
                    print(f"   ❌ Download failed: HTTP {response.status_code}")
            
            elif task.status == 'FAILED':
                print(f"   ❌ Video generation failed")
            else:
                print(f"   ⏳ Status: {task.status}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()
    
    print(f"🎉 Downloaded {downloaded}/{len(df)} videos successfully!")
    
    if downloaded > 0:
        print(f"📁 Videos saved in: ./video_outputs/")
        print(f"🎬 Ready for your social media campaigns!")
        
        # List downloaded files
        video_files = list(Path("video_outputs").glob("*.mp4"))
        if video_files:
            print(f"\n📋 Downloaded videos:")
            for video in sorted(video_files):
                size = video.stat().st_size / (1024 * 1024)
                print(f"   • {video.name} ({size:.1f}MB)")

if __name__ == "__main__":
    download_generated_videos()

