import os
from runwayml import RunwayML
import base64
from PIL import Image
import io

def check_runway_api_status():
    """Comprehensive Runway API status checker"""
    
    api_key = os.getenv('RUNWAY_API_KEY')
    if not api_key:
        print("❌ No RUNWAY_API_KEY environment variable found")
        return
    
    print("🔍 RUNWAY API STATUS CHECK")
    print("=" * 40)
    
    try:
        client = RunwayML(api_key=api_key)
        print("✅ RunwayML client initialized")
    except Exception as e:
        print(f"❌ Client initialization failed: {e}")
        return
    
    # Test 1: API Key validity
    print("\n1. 🔑 Testing API Key Validity...")
    
    # Create a minimal test image
    test_img = Image.new('RGB', (256, 256), color='red')
    buffer = io.BytesIO()
    test_img.save(buffer, format='JPEG')
    test_image_b64 = base64.b64encode(buffer.getvalue()).decode()
    
    # Test different models
    models_to_test = [
        'gen3a_turbo',
        'gen3a', 
        'gen3',
        'gen2'
    ]
    
    print("\n2. 🎭 Testing Model Availability...")
    
    available_models = []
    
    for model in models_to_test:
        try:
            print(f"   Testing {model}...", end=" ")
            
            # Attempt to create a task
            task = client.image_to_video.create(
                model=model,
                prompt_image=f"data:image/jpeg;base64,{test_image_b64}",
                prompt_text="test video generation",
                ratio="1280:768"
            )
            
            print(f"✅ Available (Task ID: {task.id})")
            available_models.append(model)
            
            # Cancel the task to avoid charges
            try:
                # Note: Runway API might not have cancel endpoint
                pass
            except:
                pass
                
        except Exception as e:
            error_msg = str(e)
            
            if "not available" in error_msg.lower():
                print(f"❌ Not available")
            elif "credit" in error_msg.lower():
                print(f"💳 Available but no credits")
                available_models.append(f"{model} (needs credits)")
            elif "403" in error_msg:
                print(f"🚫 Access denied")
            elif "401" in error_msg:
                print(f"🔑 Invalid API key")
            elif "429" in error_msg:
                print(f"⏱️ Rate limited")
            else:
                print(f"⚠️  Error: {error_msg[:50]}...")
    
    # Test 3: Account Information
    print("\n3. 📊 Account Status...")
    
    if not available_models:
        print("❌ No models available")
        print("\n💡 Possible Issues:")
        print("   • Account needs verification")
        print("   • Subscription required for API access")
        print("   • Regional restrictions")
        print("   • API key has limited permissions")
    else:
        print(f"✅ {len(available_models)} model(s) accessible")
        for model in available_models:
            print(f"   • {model}")
    
    # Test 4: Credit Status (if we got far enough)
    if available_models and "credits" not in str(available_models).lower():
        print("\n4. 💳 Credit Status...")
        print("✅ Credits available (task creation succeeded)")
    elif "credits" in str(available_models).lower():
        print("\n4. 💳 Credit Status...")
        print("⚠️  No credits available")
    
    # Summary and recommendations
    print("\n" + "=" * 40)
    print("📝 SUMMARY & RECOMMENDATIONS")
    print("=" * 40)
    
    if available_models and "credits" not in str(available_models).lower():
        print("✅ 🎉 API is fully functional!")
        print("   • You can generate videos")
        print("   • Credits are available")
        print(f"   • Recommended model: {available_models[0]}")
    elif "credits" in str(available_models).lower():
        print("⚠️  API works but needs credits")
        print("   • Add credits at: https://app.runwayml.com/")
        print("   • Estimated cost: ~$0.25 per 5-second video")
    else:
        print("❌ API access issues detected")
        print("   • Visit: https://app.runwayml.com/")
        print("   • Check account status")
        print("   • Verify API key permissions")
        print("   • Consider upgrading account")
    
    print("\n🔗 Useful Links:")
    print("   • Account Dashboard: https://app.runwayml.com/")
    print("   • API Documentation: https://docs.dev.runwayml.com/")
    print("   • Pricing: https://runwayml.com/pricing/")

if __name__ == "__main__":
    check_runway_api_status()

