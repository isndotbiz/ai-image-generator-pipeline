import os
from runwayml import RunwayML
from PIL import Image
import base64
import io

def test_simple_generation():
    api_key = os.getenv('RUNWAY_API_KEY')
    if not api_key:
        print("❌ No API key found")
        return
    
    client = RunwayML(api_key=api_key)
    print("📤 Testing simple video generation with Runway...\n")
    
    # Get one of our best images
    image_path = "./images/los_goldBitcoincoin_249_ig.png"
    
    try:
        # Convert image to base64
        with Image.open(image_path) as img:
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Make smaller for testing
            img.thumbnail((512, 512), Image.Resampling.LANCZOS)
            
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=85)
            image_b64 = base64.b64encode(buffer.getvalue()).decode()
        
        print(f"📸 Using image: {image_path}")
        print(f"📏 Image size after processing: {img.size}")
        
        # Simple prompt
        prompt = "Elegant showcase of luxury gold items with smooth camera movements"
        print(f"📝 Prompt: {prompt}")
        
        # Try with gen3a_turbo
        print(f"\n📤 Submitting to Runway gen3a_turbo...")
        
        task = client.image_to_video.create(
            model='gen3a_turbo',
            prompt_image=f"data:image/jpeg;base64,{image_b64}",
            prompt_text=prompt,
            ratio="1280:768"  # Landscape format
        )
        
        print(f"✅ SUCCESS!")
        print(f"   Task ID: {task.id}")
        print(f"   Status: {task.status}")
        
        # Save task info
        with open("test_task.txt", "w") as f:
            f.write(f"Task ID: {task.id}\n")
            f.write(f"Status: {task.status}\n")
            f.write(f"Model: gen3a_turbo\n")
            f.write(f"Prompt: {prompt}\n")
        
        print(f"\n💾 Task info saved to test_task.txt")
        print(f"🕰️ Check status with:")
        print(f"   python -c \"")
        print(f"   from runwayml import RunwayML")
        print(f"   import os")
        print(f"   client = RunwayML(api_key=os.getenv('RUNWAY_API_KEY'))")
        print(f"   task = client.tasks.retrieve('{task.id}')")
        print(f"   print(f'Status: {{task.status}}')")
        print(f"   if task.status == 'SUCCEEDED': print(f'Video: {{task.output[0]}}')")
        print(f"   \"")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        
        # Try with different model
        print(f"\n🔄 Trying with gen3a...")
        try:
            task = client.image_to_video.create(
                model='gen3a',
                prompt_image=f"data:image/jpeg;base64,{image_b64}",
                prompt_text=prompt,
                ratio="16:9"
            )
            print(f"✅ SUCCESS with gen3a!")
            print(f"   Task ID: {task.id}")
            print(f"   Status: {task.status}")
        except Exception as e2:
            print(f"❌ Error with gen3a too: {e2}")
            
            # Check if it's account related
            print(f"\n💡 Possible issues:")
            print(f"   1. Account might need credits or subscription")
            print(f"   2. API key might have limited access")
            print(f"   3. Check https://app.runwayml.com/ for account status")

if __name__ == "__main__":
    test_simple_generation()

