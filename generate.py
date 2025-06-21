#!/usr/bin/env -S bash -c 'source ~/menv/bin/activate && exec "$0" "$@"'
"""
Image generation utilities that wrap Replicate API calls.
"""

import sys
import os
import requests
from pathlib import Path
from typing import Optional, Dict, Any
from logging_config import get_logger

# Initialize logger
logger = get_logger(__name__)

try:
    import replicate
except ImportError:
    print("Error: replicate module not found. Please install with: pip install replicate")
    sys.exit(1)

# Default directory for saving images
DEFAULT_IMG_DIR = Path("images")

def generate_image(prompt: str, aspect_ratio: str = "4:5", 
                  negative_prompt: Optional[str] = None,
                  model: str = "black-forest-labs/flux-1.1-pro",
                  output_format: str = "png") -> Optional[str]:
    """
    Generate an image using Replicate API.
    Enhanced to prevent AI-generated text since we add mantras via watermarking.
    
    Args:
        prompt: The generation prompt
        aspect_ratio: Image aspect ratio
        negative_prompt: Optional negative prompt for filtering
        model: Replicate model to use
        output_format: Output format (png, jpg, etc.)
        
    Returns:
        URL of the generated image, or None if failed
    """
    logger.info(f"Generating image with prompt: {prompt[:100]}...")
    try:
        # Prepare input parameters
        input_params = {
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "output_format": output_format
        }
        
        # Enhanced default negative prompt to prevent AI-generated text
        default_negative = ("text, watermark, writing, letters, words, typography, "
                          "signs, labels, captions, overlay text, generated text, "
                          "AI text, embedded text, lowres, jpeg artifacts, plastic, "
                          "logo, duplicate, deformed, bad anatomy, nsfw, inappropriate")
        
        if negative_prompt:
            # Combine user negative prompt with our anti-text directives
            combined_negative = f"{negative_prompt}, {default_negative}"
            input_params["negative_prompt"] = combined_negative
            logger.debug(f"Using combined negative prompt: {combined_negative}")
        else:
            input_params["negative_prompt"] = default_negative
            logger.debug(f"Using default anti-text negative prompt: {default_negative}")
        
        logger.debug(f"Using model: {model}, aspect_ratio: {aspect_ratio}")
        
        # Run the model
        result = replicate.run(model, input=input_params)
        
        # Convert result to string URL
        url = str(result)
        logger.info(f"Successfully generated image, URL: {url}")
        return url
        
    except Exception as e:
        logger.error(f"Error generating image: {e}")
        return None

def download_image(url: str, output_path: str) -> bool:
    """
    Download an image from a URL to a local file.
    Creates parent directories if they don't exist.
    
    Args:
        url: URL of the image to download
        output_path: Local path to save the image
        
    Returns:
        True if successful, False otherwise
    """
    logger.debug(f"Downloading image from {url} to {output_path}")
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Create parent directories if they don't exist
        output_path_obj = Path(output_path)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "wb") as f:
            f.write(response.content)
        
        logger.info(f"Successfully downloaded image to {output_path}")
        return True
        
    except requests.RequestException as e:
        logger.error(f"Error downloading image: {e}")
        return False
    except Exception as e:
        logger.error(f"Error saving image: {e}")
        return False

def generate_and_save(prompt: str, output_path: str, 
                     aspect_ratio: str = "4:5",
                     negative_prompt: Optional[str] = None,
                     model: str = "black-forest-labs/flux-1.1-pro") -> bool:
    """
    Generate an image and save it to a local file.
    If output_path lacks path separators, saves to the default images directory.
    
    Args:
        prompt: The generation prompt
        output_path: Local path to save the image (if no path separators, saves to images/)
        aspect_ratio: Image aspect ratio
        negative_prompt: Optional negative prompt
        model: Replicate model to use
        
    Returns:
        True if successful, False otherwise
    """
    # Check if output_path lacks path separators, if so prepend default directory
    path_obj = Path(output_path)
    if len(path_obj.parts) == 1:  # Only filename, no path separators
        output_path = str(DEFAULT_IMG_DIR / output_path)
    
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
        logger.warning(f"Skipped {output_path} - Content filter triggered")
    elif "rate limit" in error_str.lower():
        logger.warning(f"Rate limited for {output_path} - please wait and retry")
    elif "token" in error_str.lower() or "auth" in error_str.lower():
        logger.error(f"Authentication error for {output_path} - check REPLICATE_API_TOKEN")
    else:
        logger.error(f"Error generating {output_path}: {error}")

def check_api_token() -> bool:
    """
    Check if the Replicate API token is configured.
    
    Returns:
        True if token is available, False otherwise
    """
    token = os.getenv("REPLICATE_API_TOKEN")
    if not token:
        logger.error("REPLICATE_API_TOKEN environment variable not set")
        logger.error("Please set it with: export REPLICATE_API_TOKEN=\"your_token_here\"")
        return False
    logger.debug("API token configured")
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
    
    # Check if output_path lacks path separators, if so prepend default directory
    path_obj = Path(output_path)
    if len(path_obj.parts) == 1:  # Only filename, no path separators
        output_path = str(DEFAULT_IMG_DIR / output_path)
    
    try:
        success = generate_and_save(prompt, output_path, aspect_ratio, negative_prompt)
        if not success:
            sys.exit(1)
    except Exception as e:
        handle_generation_errors(e, output_path)
        sys.exit(1)

