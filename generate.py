#!/usr/bin/env python3
"""
Image generation utilities that wrap Replicate API calls.
"""

import sys
import os
import requests
from typing import Optional, Dict, Any

try:
    import replicate
except ImportError:
    print("Error: replicate module not found. Please install with: pip install replicate")
    sys.exit(1)

def generate_image(prompt: str, aspect_ratio: str = "4:5", 
                  negative_prompt: Optional[str] = None,
                  model: str = "black-forest-labs/flux-1.1-pro",
                  output_format: str = "png") -> Optional[str]:
    """
    Generate an image using Replicate API.
    
    Args:
        prompt: The generation prompt
        aspect_ratio: Image aspect ratio
        negative_prompt: Optional negative prompt for filtering
        model: Replicate model to use
        output_format: Output format (png, jpg, etc.)
        
    Returns:
        URL of the generated image, or None if failed
    """
    try:
        # Prepare input parameters
        input_params = {
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "output_format": output_format
        }
        
        if negative_prompt:
            input_params["negative_prompt"] = negative_prompt
        
        # Run the model
        result = replicate.run(model, input=input_params)
        
        # Convert result to string URL
        url = str(result)
        return url
        
    except Exception as e:
        print(f"Error generating image: {e}")
        return None

def download_image(url: str, output_path: str) -> bool:
    """
    Download an image from a URL to a local file.
    
    Args:
        url: URL of the image to download
        output_path: Local path to save the image
        
    Returns:
        True if successful, False otherwise
    """
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        with open(output_path, "wb") as f:
            f.write(response.content)
        
        return True
        
    except requests.RequestException as e:
        print(f"Error downloading image: {e}")
        return False
    except Exception as e:
        print(f"Error saving image: {e}")
        return False

def generate_and_save(prompt: str, output_path: str, 
                     aspect_ratio: str = "4:5",
                     negative_prompt: Optional[str] = None,
                     model: str = "black-forest-labs/flux-1.1-pro") -> bool:
    """
    Generate an image and save it to a local file.
    
    Args:
        prompt: The generation prompt
        output_path: Local path to save the image
        aspect_ratio: Image aspect ratio
        negative_prompt: Optional negative prompt
        model: Replicate model to use
        
    Returns:
        True if successful, False otherwise
    """
    # Generate the image
    url = generate_image(prompt, aspect_ratio, negative_prompt, model)
    if not url:
        return False
    
    # Download and save
    success = download_image(url, output_path)
    if success:
        print(f"Saved {output_path}")
    
    return success

def handle_generation_errors(error: Exception, output_path: str) -> None:
    """
    Handle and log generation errors appropriately.
    
    Args:
        error: The exception that occurred
        output_path: The intended output path
    """
    error_str = str(error)
    
    if "NSFW" in error_str:
        print(f"Skipped {output_path} - Content filter triggered")
    elif "rate limit" in error_str.lower():
        print(f"Rate limited for {output_path} - please wait and retry")
    elif "token" in error_str.lower() or "auth" in error_str.lower():
        print(f"Authentication error for {output_path} - check REPLICATE_API_TOKEN")
    else:
        print(f"Error generating {output_path}: {error}")

def check_api_token() -> bool:
    """
    Check if the Replicate API token is configured.
    
    Returns:
        True if token is available, False otherwise
    """
    token = os.getenv("REPLICATE_API_TOKEN")
    if not token:
        print("Error: REPLICATE_API_TOKEN environment variable not set")
        print("Please set it with: export REPLICATE_API_TOKEN=\"your_token_here\"")
        return False
    return True

def batch_generate(prompts_and_paths: list, aspect_ratio: str = "4:5",
                  negative_prompt: Optional[str] = None,
                  model: str = "black-forest-labs/flux-1.1-pro") -> Dict[str, bool]:
    """
    Generate multiple images in batch.
    
    Args:
        prompts_and_paths: List of (prompt, output_path) tuples
        aspect_ratio: Image aspect ratio
        negative_prompt: Optional negative prompt
        model: Replicate model to use
        
    Returns:
        Dictionary mapping output paths to success status
    """
    results = {}
    
    for prompt, output_path in prompts_and_paths:
        try:
            success = generate_and_save(prompt, output_path, aspect_ratio, negative_prompt, model)
            results[output_path] = success
        except Exception as e:
            handle_generation_errors(e, output_path)
            results[output_path] = False
    
    return results

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 generate.py <prompt> <output_path> [aspect_ratio] [negative_prompt]")
        sys.exit(1)
    
    # Check API token
    if not check_api_token():
        sys.exit(1)
    
    prompt = sys.argv[1]
    output_path = sys.argv[2]
    aspect_ratio = sys.argv[3] if len(sys.argv) > 3 else "4:5"
    negative_prompt = sys.argv[4] if len(sys.argv) > 4 else None
    
    try:
        success = generate_and_save(prompt, output_path, aspect_ratio, negative_prompt)
        if not success:
            sys.exit(1)
    except Exception as e:
        handle_generation_errors(e, output_path)
        sys.exit(1)

