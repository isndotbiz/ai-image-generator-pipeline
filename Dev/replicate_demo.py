#!/usr/bin/env python3
"""
Demonstration script for using the Replicate API to generate images 
with the stability-ai/sdxl model.
"""

import os
import sys
import time
import replicate
from typing import List, Optional, Dict, Any, Union
import webbrowser
from urllib.parse import urlparse


def setup_api_key() -> bool:
    """
    Checks if REPLICATE_API_TOKEN is set in the environment.
    If not, prompts the user to set it.
    
    Returns:
        bool: True if API key is set, False otherwise
    """
    if not os.environ.get("REPLICATE_API_TOKEN"):
        print("REPLICATE_API_TOKEN environment variable is not set.")
        print("You can get your token from https://replicate.com/account/api-tokens")
        print("\nTo set it for this session only, run:")
        print("export REPLICATE_API_TOKEN=your_api_token_here")
        print("\nOr to set it permanently, add the line above to your .bashrc, .zshrc, etc.")
        return False
    return True


def generate_image(
    prompt: str, 
    negative_prompt: Optional[str] = None,
    width: int = 1024,
    height: int = 1024,
    num_outputs: int = 1
) -> Union[List[str], None]:
    """
    Generate images using the stability-ai/sdxl model.
    
    Args:
        prompt: Text description of the image to generate
        negative_prompt: Text that should not be in the image
        width: Width of the generated image
        height: Height of the generated image
        num_outputs: Number of images to generate
        
    Returns:
        List of image URLs or None if generation failed
    """
    try:
        # Model version from https://replicate.com/stability-ai/sdxl
        output = replicate.run(
            "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
            input={
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "width": width,
                "height": height,
                "num_outputs": num_outputs,
            }
        )
        
        # The output is a list of image URLs
        return output
    except Exception as e:
        print(f"Error generating image: {e}")
        return None


def open_image_in_browser(image_url: str) -> None:
    """Opens the generated image URL in the default web browser."""
    # Validate URL to ensure it's safe to open
    parsed_url = urlparse(image_url)
    if parsed_url.scheme in ('http', 'https'):
        print(f"Opening image: {image_url}")
        webbrowser.open(image_url)
    else:
        print(f"Invalid URL scheme: {image_url}")


def main():
    # Check if the API key is set
    if not setup_api_key():
        return 1
        
    try:
        # Get user input
        prompt = input("Enter an image prompt: ").strip()
        if not prompt:
            prompt = "A beautiful landscape with mountains and a lake at sunset, digital art"
            print(f"Using default prompt: {prompt}")
            
        negative_prompt = input("Enter a negative prompt (optional): ").strip()
        
        # Generate the image
        print("\nGenerating image... (this may take a minute)")
        start_time = time.time()
        
        image_urls = generate_image(
            prompt=prompt,
            negative_prompt=negative_prompt if negative_prompt else None,
            num_outputs=1
        )
        
        elapsed_time = time.time() - start_time
        
        if image_urls:
            print(f"\nImage generated in {elapsed_time:.2f} seconds!")
            for i, url in enumerate(image_urls):
                print(f"Image {i+1}: {url}")
                
            # Ask if user wants to open the image
            if input("\nOpen image in browser? (y/n): ").lower().startswith('y'):
                open_image_in_browser(image_urls[0])
        else:
            print("Failed to generate image.")
            return 1
            
        return 0
            
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        return 1
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

