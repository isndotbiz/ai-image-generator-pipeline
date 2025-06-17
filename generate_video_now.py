import time, base64
import os
from runwayml import RunwayML

client = RunwayML()

# Use one of your existing images
image = 'images/direct_20250616_215510_li.png'

# Check if image exists
if not os.path.exists(image):
    print(f"Error: Image {image} not found!")
    print("Available images:")
    for img in os.listdir('images/'):
        if img.lower().endswith(('.png', '.jpg', '.jpeg')):
            print(f"  - images/{img}")
    exit(1)

print(f"Using image: {image}")

# encode image to base64
with open(image, "rb") as f:
    base64_image = base64.b64encode(f.read()).decode("utf-8")

print("Image encoded to base64")

# Create a new image-to-video task using the "gen4_turbo" model
print("Creating video generation task...")
task = client.image_to_video.create(
    model='gen4_turbo',
    # Point this at your own image file
    prompt_image=f"data:image/png;base64,{base64_image}",
    prompt_text='Generate a smooth, calming video with gentle movement',
    ratio='1280:720',
    duration=5,
)
task_id = task.id
print(f"Task created with ID: {task_id}")

# Poll the task until it's complete
print("Waiting for video generation to complete...")
time.sleep(10)  # Wait for ten seconds before polling
task = client.tasks.retrieve(task_id)
while task.status not in ['SUCCEEDED', 'FAILED']:
    print(f"Status: {task.status}")
    time.sleep(10)  # Wait for ten seconds before polling
    task = client.tasks.retrieve(task_id)

print('Task complete:', task.status)
if task.status == 'SUCCEEDED':
    print("Video URL:", task.output)
else:
    print("Task failed:", task)

