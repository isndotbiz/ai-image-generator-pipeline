import os
import base64
from pathlib import Path
from runwayml import RunwayML
from PIL import Image
import io

# Initialize client with current SDK
client = RunwayML(api_key="key_9f3063dad1809e5254d1586e3df0d3a9c251ba36a927b383e04482f83222d2360e707c004a5da8e4804dbe263ddb6525377acc3cdfe7e61cfbf1d93a054a9dca")

def process_image(path):
    """Process a single image and generate video"""
    print(f"Processing: {path}")
    
    # Convert image to base64
    with Image.open(path) as img:
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Resize if needed
        if max(img.size) > 1024:
            img.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
        
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=90)
        image_b64 = base64.b64encode(buffer.getvalue()).decode()
    
    # Generate video with current API
    try:
        task = client.image_to_video.create(
            model='gen3a_turbo',  # Current model name
            prompt_image=f"data:image/jpeg;base64,{image_b64}",
            prompt_text="Slow dolly camera movement with cinematic quality",  # Text prompt for movement
            ratio="1280:768",  # Landscape format
            duration=5  # 5 second duration (8 seconds not supported)
        )
        
        print(f"Task submitted: {task.id} | Status: {task.status}")
        
        # Note: The new API is asynchronous, so you need to poll for completion
        return task
        
    except Exception as e:
        print(f"Error processing {path}: {e}")
        return None

# Example usage (you'll need to define 'path' variable)
# path = "./images/your_image.png"
# task = process_image(path)

print("\n📝 Updated to use current RunwayML SDK!")
print("\n🔧 To use this script:")
print("1. Set the 'path' variable to your image file")
print("2. Call process_image(path)")
print("3. The API is now asynchronous - you'll get a task ID")
print("4. Use our runway_generator.py for a complete workflow")
