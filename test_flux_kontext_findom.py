#!/usr/bin/env python3

import replicate
import os
import requests
from datetime import datetime

def upload_image_to_replicate(image_path):
    """Upload a local image file to Replicate and return the URL"""
    try:
        with open(image_path, "rb") as file:
            response = requests.post(
                "https://api.replicate.com/v1/files",
                headers={
                    "Authorization": f"Token {os.environ['REPLICATE_API_TOKEN']}",
                },
                files={"content": file}
            )
            response.raise_for_status()
            return response.json()["urls"]["get"]
    except Exception as e:
        print(f"Error uploading image: {e}")
        return None

def test_flux_kontext_findom():
    """Test FLUX Kontext Pro with findom prompts"""
    
    # Check if API token exists
    if not os.environ.get('REPLICATE_API_TOKEN'):
        print("Error: REPLICATE_API_TOKEN environment variable not set")
        return
    
    # Face reference image
    face_reference_path = "/Users/jonathanmallinger/Desktop/001.png"
    
    if not os.path.exists(face_reference_path):
        print(f"Error: Face reference image not found at {face_reference_path}")
        return
    
    print("Uploading face reference image...")
    face_reference_url = upload_image_to_replicate(face_reference_path)
    
    if not face_reference_url:
        print("Failed to upload face reference image")
        return
    
    print(f"Face reference uploaded: {face_reference_url}")
    
    # Findom prompts to test
    test_prompts = [
        {
            "name": "throne_ritual_command",
            "prompt": "Using the uploaded reference image, generate a photorealistic scene of the same woman seated on a dark velvet throne in a candlelit ritual chamber. She wears a fitted corset dress, hair cascading in waves. Two lit candles behind her cast soft shadows. Add realistic skin texture, soft lighting, and ornate throne detail. Cinematic mood, high-resolution styling. She looks directly into the camera with authority."
        },
        {
            "name": "mirror_of_control", 
            "prompt": "Generate a cinematic photorealistic image of the same woman seated before an antique gold-trimmed mirror. She adjusts an earring, making eye contact with her reflection. Room glows with warm, low candlelight. Outfit: satin slip gown with corset detailing. Background: velvet curtains. Maintain facial likeness, natural texture, detailed lighting on her cheekbones and neckline."
        },
        {
            "name": "champagne_command_ritual",
            "prompt": "Using the uploaded face reference, generate a photorealistic image of the same woman seated at a luxury table, holding a crystal champagne flute. Candlelight reflects on glassware. She wears a fitted satin dress, gold bracelet visible, posture relaxed but powerful. The background is soft-focus, lit with chandeliers. Maintain accurate facial features and textured skin detail."
        },
        {
            "name": "golden_watch_test",
            "prompt": "Generate a photorealistic portrait of the woman from the reference, holding an ornate gold pocket watch close to her face, partially lit by candlelight. She wears a corset with velvet detailing. Background: stone-textured wall, soft shadows. Skin texture should include realistic light falloff, pores, and detailed gaze. The mood is calm, commanding, ritualistic."
        }
    ]
    
    # Create output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"/Users/jonathanmallinger/Dev/flux_kontext_test_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Creating output directory: {output_dir}")
    
    # Test each prompt
    for i, test_case in enumerate(test_prompts, 1):
        print(f"\n=== Testing {i}/{len(test_prompts)}: {test_case['name']} ===")
        print(f"Prompt: {test_case['prompt'][:100]}...")
        
        try:
            # FLUX Kontext Pro input
            input_data = {
                "prompt": test_case['prompt'],
                "input_image": face_reference_url,
                "output_format": "jpg",
                "aspect_ratio": "match_input_image",
                "safety_tolerance": 2
            }
            
            print("Calling FLUX Kontext Pro...")
            output = replicate.run(
                "black-forest-labs/flux-kontext-pro",
                input=input_data
            )
            
            # Download the result
            if output:
                output_filename = f"{output_dir}/{test_case['name']}_flux_kontext.jpg"
                
                print("Downloading result...")
                response = requests.get(output)
                response.raise_for_status()
                
                with open(output_filename, "wb") as f:
                    f.write(response.content)
                
                print(f"✅ Success! Saved to: {output_filename}")
            else:
                print("❌ No output received")
                
        except Exception as e:
            print(f"❌ Error generating {test_case['name']}: {e}")
    
    print(f"\n🎉 Test complete! Results saved in: {output_dir}")

if __name__ == "__main__":
    test_flux_kontext_findom()
