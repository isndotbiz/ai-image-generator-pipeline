import requests
import os
from runwayml import RunwayML
from datetime import datetime

client = RunwayML()

# Get the completed task
task_id = "f645e2df-b639-4264-9bf2-fc7bceb6c658"
task = client.tasks.retrieve(task_id)

if task.status == 'SUCCEEDED' and task.output:
    video_url = task.output[0]  # Get the first (and likely only) video URL
    
    # Create a filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"generated_video_{timestamp}.mp4"
    filepath = os.path.join("video_outputs", filename)
    
    # Make sure video_outputs directory exists
    os.makedirs("video_outputs", exist_ok=True)
    
    print(f"Downloading video to: {filepath}")
    
    # Download the video
    response = requests.get(video_url)
    
    if response.status_code == 200:
        with open(filepath, 'wb') as f:
            f.write(response.content)
        print(f"✅ Video downloaded successfully: {filepath}")
        print(f"📁 File size: {os.path.getsize(filepath) / (1024*1024):.2f} MB")
    else:
        print(f"❌ Failed to download video. Status code: {response.status_code}")
else:
    print(f"❌ Task not completed successfully. Status: {task.status}")

