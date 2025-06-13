#!/usr/bin/env python3
"""
Image generation utilities that wrap Replicate API calls.
"""

import sys
import os
import requests
import time
import csv
import random
import json
from typing import Optional, Dict, Any
from pathlib import Path

try:
    import replicate
except ImportError:
    print("Error: replicate module not found. Please install with: pip install replicate")
    sys.exit(1)

# Import smartproxy utilities
try:
    import smartproxy_utils
    from smartproxy_utils import make_proxied_request, SmartproxyConfig
    PROXY_AVAILABLE = True
    
    # Instantiate config once
    config = smartproxy_utils.SmartproxyConfig()
    proxies = config.get_proxy_config()
    headers = config.get_auth_headers()
    
    # Set proxy environment variables for Replicate client
    os.environ["HTTP_PROXY"] = proxies["http"]
    os.environ["HTTPS_PROXY"] = proxies["https"]
    
    # Log proxy configuration
    print(f"Using Smartproxy: {proxies['http']}")
    
except ImportError:
    PROXY_AVAILABLE = False
    make_proxied_request = None
    SmartproxyConfig = None
    config = None
    proxies = None
    headers = None

def exponential_backoff_retry(func, max_retries=5, base_delay=1.0, max_delay=60.0, backoff_factor=2.0):
    """
    Execute a function with exponential backoff retry.
    
    Args:
        func: Function to execute
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        backoff_factor: Multiplier for delay after each failure
        
    Returns:
        Result of the function or raises the last exception
    """
    delay = base_delay
    
    for attempt in range(max_retries + 1):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries:
                raise e
            
            # Check if it's a rate limit error
            error_str = str(e).lower()
            if "rate limit" in error_str or "too many requests" in error_str:
                actual_delay = min(delay + random.uniform(0, delay * 0.1), max_delay)
                print(f"Rate limited, retrying in {actual_delay:.1f}s (attempt {attempt + 1}/{max_retries + 1})")
                time.sleep(actual_delay)
                delay = min(delay * backoff_factor, max_delay)
            else:
                # For other errors, use shorter delay
                actual_delay = min(delay * 0.5, 10.0)
                print(f"Error occurred, retrying in {actual_delay:.1f}s (attempt {attempt + 1}/{max_retries + 1}): {e}")
                time.sleep(actual_delay)
                delay = min(delay * backoff_factor, max_delay)

def log_generation_result(prompt: str, output_path: str, success: bool, error_msg: str = None):
    """
    Log generation result to appropriate file.
    
    Args:
        prompt: The generation prompt
        output_path: Path where image was saved
        success: Whether generation was successful
        error_msg: Error message if failed
    """
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    
    if success:
        # Log to manifest.csv
        manifest_path = Path("manifest.csv")
        file_exists = manifest_path.exists()
        
        with open(manifest_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['timestamp', 'prompt', 'output_path', 'status'])
            writer.writerow([timestamp, prompt, output_path, 'success'])
    else:
        # Log to failed.log
        with open("failed.log", 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] FAILED: {output_path}\n")
            f.write(f"  Prompt: {prompt}\n")
            f.write(f"  Error: {error_msg}\n\n")

def generate_image(prompt: str, aspect_ratio: str = "4:5", 
                  negative_prompt: Optional[str] = None,
                  model: str = "black-forest-labs/flux-1.1-pro",
                  output_format: str = "png") -> Optional[str]:
    """
    Generate an image using Replicate API with exponential backoff retry.
    
    Args:
        prompt: The generation prompt
        aspect_ratio: Image aspect ratio
        negative_prompt: Optional negative prompt for filtering
        model: Replicate model to use
        output_format: Output format (png, jpg, etc.)
        
    Returns:
        URL of the generated image, or None if failed
    """
    def _generate():
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
        return str(result)
    
    try:
        url = exponential_backoff_retry(_generate)
        return url
    except Exception as e:
        print(f"Error generating image after retries: {e}")
        return None

def download_image(url: str, output_path: str) -> bool:
    """
    Download an image from a URL to a local file with proxy support.
    
    Args:
        url: URL of the image to download
        output_path: Local path to save the image
        
    Returns:
        True if successful, False otherwise
    """
    def _download():
        # Use proxy if available and configured
        if PROXY_AVAILABLE and make_proxied_request:
            try:
                response = make_proxied_request(url, method='GET', timeout=30)
            except Exception:
                # Fallback to regular request if proxy fails
                response = requests.get(url, timeout=30)
        else:
            response = requests.get(url, timeout=30)
        
        response.raise_for_status()
        return response.content
    
    try:
        # Download with retry mechanism
        content = exponential_backoff_retry(_download, max_retries=3)
        
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, "wb") as f:
            f.write(content)
        
        return True
        
    except Exception as e:
        print(f"Error downloading/saving image {output_path}: {e}")
        return False

def generate_and_save(prompt: str, output_path: str, 
                     aspect_ratio: str = "4:5",
                     negative_prompt: Optional[str] = None,
                     model: str = "black-forest-labs/flux-1.1-pro") -> bool:
    """
    Generate an image and save it to a local file with comprehensive logging.
    
    Args:
        prompt: The generation prompt
        output_path: Local path to save the image
        aspect_ratio: Image aspect ratio
        negative_prompt: Optional negative prompt
        model: Replicate model to use
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Generate the image
        url = generate_image(prompt, aspect_ratio, negative_prompt, model)
        if not url:
            log_generation_result(prompt, output_path, False, "Failed to generate image URL")
            return False
        
        # Download and save
        success = download_image(url, output_path)
        if success:
            print(f"Saved {output_path}")
            log_generation_result(prompt, output_path, True)
        else:
            log_generation_result(prompt, output_path, False, "Failed to download image")
        
        return success
    except Exception as e:
        error_msg = str(e)
        log_generation_result(prompt, output_path, False, error_msg)
        print(f"Error generating {output_path}: {error_msg}")
        return False

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
    # Parse arguments including --dry-run flag
    args = sys.argv[1:]
    dry_run = False
    
    if "--dry-run" in args:
        dry_run = True
        args.remove("--dry-run")
    
    if len(args) < 2:
        print("Usage: python3 generate.py <prompt> <output_path> [aspect_ratio] [negative_prompt] [--dry-run]")
        sys.exit(1)
    
    # Check API token
    if not check_api_token():
        sys.exit(1)
    
    prompt = args[0]
    output_path = args[1]
    aspect_ratio = args[2] if len(args) > 2 else "4:5"
    negative_prompt = args[3] if len(args) > 3 else None
    
    try:
        if dry_run:
            print(f"DRY RUN: Would generate image with prompt: '{prompt}'")
            print(f"DRY RUN: Would save to: {output_path}")
            print(f"DRY RUN: Aspect ratio: {aspect_ratio}")
            if negative_prompt:
                print(f"DRY RUN: Negative prompt: {negative_prompt}")
            
            # Test the API connection by generating the image but not saving it
            print("DRY RUN: Testing Replicate API connection...")
            url = generate_image(prompt, aspect_ratio, negative_prompt)
            if url:
                print(f"✓ DRY RUN: Successfully generated image URL: {url[:50]}...")
                print("✓ DRY RUN: Replicate API connection successful")
            else:
                print("✗ DRY RUN: Failed to generate image")
                sys.exit(1)
        else:
            success = generate_and_save(prompt, output_path, aspect_ratio, negative_prompt)
            if not success:
                sys.exit(1)
    except Exception as e:
        handle_generation_errors(e, output_path)
        sys.exit(1)

