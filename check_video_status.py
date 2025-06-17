from runwayml import RunwayML

client = RunwayML()

# Check the status of our video generation task
task_id = "f645e2df-b639-4264-9bf2-fc7bceb6c658"

print(f"Checking status of task: {task_id}")
task = client.tasks.retrieve(task_id)

print(f"Status: {task.status}")
print(f"Progress: {getattr(task, 'progress', 'N/A')}")

if task.status == 'SUCCEEDED':
    print("🎉 Video generation completed!")
    print(f"Video URL: {task.output}")
elif task.status == 'FAILED':
    print("❌ Video generation failed")
    print(f"Error: {getattr(task, 'error', 'Unknown error')}")
elif task.status == 'RUNNING':
    print("⏳ Video is still being generated...")
else:
    print(f"Status: {task.status}")

print("\nFull task details:")
print(task)

