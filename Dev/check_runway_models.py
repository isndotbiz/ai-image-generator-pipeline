import os
from runwayml import RunwayML

def check_available_models():
    api_key = os.getenv('RUNWAY_API_KEY')
    if not api_key:
        print("❌ No API key found")
        return
    
    client = RunwayML(api_key=api_key)
    print("🔍 Checking available Runway models...\n")
    
    # Try different model variants
    models_to_test = [
        'gen3a_turbo',
        'gen3a', 
        'gen3',
        'gen2',
        'runway-ml/gen2',
        'runway-ml/gen3',
        'runway-ml/gen3a'
    ]
    
    available_models = []
    
    for model in models_to_test:
        try:
            print(f"Testing model: {model}")
            # Try to create a minimal request to test availability
            # This should fail gracefully if model exists but we're missing params
            task = client.image_to_video.create(
                model=model,
                prompt_text="test"
            )
            available_models.append(model)
            print(f"✅ {model} - Available")
        except Exception as e:
            error_msg = str(e)
            if "not available" in error_msg.lower():
                print(f"❌ {model} - Not available")
            elif "missing" in error_msg.lower() or "required" in error_msg.lower():
                print(f"✅ {model} - Available (missing required params in test)")
                available_models.append(model)
            else:
                print(f"⚠️  {model} - Unknown error: {error_msg}")
    
    print(f"\n📊 Summary:")
    if available_models:
        print(f"✅ Available models: {available_models}")
    else:
        print("❌ No models found available")
        print("\n💡 This might mean:")
        print("   1. API key doesn't have video generation access")
        print("   2. Account needs to be upgraded")
        print("   3. Different model names are used")
        print("\n🔗 Check your account at: https://app.runwayml.com/")

if __name__ == "__main__":
    check_available_models()

