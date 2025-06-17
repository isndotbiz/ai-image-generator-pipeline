#!/usr/bin/env -S bash -c 'source ~/menv/bin/activate && exec "$0" "$@"'
"""
Watermarking utilities for generated images with platform-specific positioning.

This module implements a watermarking subsystem using Pillow that:
- Loads generated PNG images and blends semi-transparent logos or @handles at 92% opacity
- Provides platform-specific positioning:
  * Instagram: bottom-right (optimal for square/portrait posts)
  * TikTok: mid-left (avoiding caption area at bottom)
  * Twitter: top-right (standard positioning for social content)
  * Generic: bottom-right (default fallback)

Usage Examples:
    # Text watermark for Instagram
    watermark_for_platform('image.png', 'instagram', '@yourhandle')
    
    # Logo watermark for TikTok
    watermark_for_platform('image.png', 'tiktok', 'logo.png', is_logo=True)
    
    # Custom opacity text watermark
    add_text_watermark('image.png', '@handle', Platform.TWITTER, opacity=0.8)
    
    # Batch processing
    batch_watermark(['img1.png', 'img2.png'], 'instagram', '@handle')

Requirements:
    - Pillow >= 8.0.0
    - piexif (optional, for metadata support)
"""

import sys
import os
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from enum import Enum

try:
    import piexif
    from datetime import datetime
except ImportError as e:
    print(f"Warning: {e.name} not available for watermarking features")
    piexif = None
    datetime = None

class Platform(Enum):
    """Supported social media platforms with specific watermark positioning."""
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    TWITTER = "twitter"
    GENERIC = "generic"

def get_platform_position(platform: Platform, image_size: Tuple[int, int], 
                          watermark_size: Tuple[int, int]) -> Tuple[int, int]:
    """
    Calculate platform-specific watermark position.
    
    Args:
        platform: Target platform
        image_size: (width, height) of the base image
        watermark_size: (width, height) of the watermark
        
    Returns:
        (x, y) coordinates for watermark placement
    """
    img_width, img_height = image_size
    wm_width, wm_height = watermark_size
    margin = max(20, min(img_width, img_height) // 40)  # Dynamic margin based on image size
    
    if platform == Platform.INSTAGRAM:
        # Bottom-right for Instagram
        x = img_width - wm_width - margin
        y = img_height - wm_height - margin
    elif platform == Platform.TIKTOK:
        # Mid-left for TikTok (avoiding caption area at bottom)
        x = margin
        y = (img_height - wm_height) // 2
    elif platform == Platform.TWITTER:
        # Top-right for Twitter
        x = img_width - wm_width - margin
        y = margin
    else:  # GENERIC
        # Default to bottom-right
        x = img_width - wm_width - margin
        y = img_height - wm_height - margin
    
    return (max(0, x), max(0, y))

def add_logo_watermark(image_path: str, logo_path: str, platform: Platform = Platform.GENERIC,
                      opacity: float = 0.92, scale_factor: float = 0.15, 
                      output_path: Optional[str] = None) -> str:
    """
    Add a logo watermark to an image with platform-specific positioning.
    
    Args:
        image_path: Path to the input image
        logo_path: Path to the logo image
        platform: Target platform for positioning
        opacity: Watermark opacity (0.0 to 1.0)
        scale_factor: Size of logo relative to image (0.1 = 10% of image width)
        output_path: Optional output path, defaults to input_path with _watermarked suffix
        
    Returns:
        Path to the watermarked image
    """
    try:
        from PIL import Image, ImageEnhance
        
        # Load base image
        base_img = Image.open(image_path).convert('RGBA')
        
        # Load and process logo
        logo = Image.open(logo_path).convert('RGBA')
        
        # Scale logo based on image size
        target_width = int(base_img.size[0] * scale_factor)
        logo_aspect = logo.size[1] / logo.size[0]
        target_height = int(target_width * logo_aspect)
        logo = logo.resize((target_width, target_height), Image.Resampling.LANCZOS)
        
        # Adjust logo opacity
        if opacity < 1.0:
            alpha = logo.split()[-1]
            enhancer = ImageEnhance.Brightness(alpha)
            alpha = enhancer.enhance(opacity)
            logo.putalpha(alpha)
        
        # Get platform-specific position
        position = get_platform_position(platform, base_img.size, logo.size)
        
        # Create a copy of base image and paste logo
        watermarked = base_img.copy()
        watermarked.paste(logo, position, logo)
        
        # Convert back to RGB if needed
        if watermarked.mode == 'RGBA':
            background = Image.new('RGB', watermarked.size, (255, 255, 255))
            background.paste(watermarked, mask=watermarked.split()[-1])
            watermarked = background
        
        # Determine output path
        if output_path is None:
            base, ext = os.path.splitext(image_path)
            basename = os.path.basename(base)
            # Place in images/ directory if not already there
            if not image_path.startswith('images/'):
                output_path = f"images/{basename}_watermarked{ext}"
            else:
                output_path = f"{base}_watermarked{ext}"
        
        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Save the watermarked image
        watermarked.save(output_path, quality=95)
        return output_path
        
    except ImportError:
        print("Warning: PIL not available for watermarking")
        return image_path
    except Exception as e:
        print(f"Error adding logo watermark: {e}")
        return image_path

def add_text_watermark(image_path: str, text: str, platform: Platform = Platform.GENERIC,
                      opacity: float = 0.92, font_scale: float = 0.03, 
                      output_path: Optional[str] = None) -> str:
    """
    Add a text watermark (like @handle) to an image with platform-specific positioning.
    
    Args:
        image_path: Path to the input image
        text: Watermark text (e.g., '@yourhandle')
        platform: Target platform for positioning
        opacity: Watermark opacity (0.0 to 1.0)
        font_scale: Font size relative to image width (0.03 = 3% of image width)
        output_path: Optional output path, defaults to input_path with _watermarked suffix
        
    Returns:
        Path to the watermarked image
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # Load image
        img = Image.open(image_path).convert('RGBA')
        
        # Create a transparent overlay
        overlay = Image.new('RGBA', img.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Dynamic font sizing
        font_size = max(16, int(img.size[0] * font_scale))
        
        # Try to use a better font
        try:
            # Try system fonts in order of preference
            font_paths = [
                "/System/Library/Fonts/Arial Bold.ttf",
                "/System/Library/Fonts/Helvetica.ttc",
                "/System/Library/Fonts/Arial.ttf",
            ]
            font = None
            for font_path in font_paths:
                if os.path.exists(font_path):
                    font = ImageFont.truetype(font_path, font_size)
                    break
            if font is None:
                font = ImageFont.load_default()
        except:
            font = ImageFont.load_default()
        
        # Get text size
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Get platform-specific position
        position = get_platform_position(platform, img.size, (text_width, text_height))
        
        # Draw text with semi-transparent background for better readability
        padding = 8
        bg_x1, bg_y1 = position[0] - padding, position[1] - padding
        bg_x2, bg_y2 = position[0] + text_width + padding, position[1] + text_height + padding
        
        # Semi-transparent background
        bg_alpha = int(255 * opacity * 0.3)  # 30% of text opacity for background
        draw.rectangle([bg_x1, bg_y1, bg_x2, bg_y2], fill=(0, 0, 0, bg_alpha))
        
        # Draw text with specified opacity
        text_alpha = int(255 * opacity)
        draw.text(position, text, font=font, fill=(255, 255, 255, text_alpha))
        
        # Composite the overlay onto the original image
        watermarked = Image.alpha_composite(img, overlay)
        
        # Convert back to RGB if needed
        if watermarked.mode == 'RGBA':
            background = Image.new('RGB', watermarked.size, (255, 255, 255))
            background.paste(watermarked, mask=watermarked.split()[-1])
            watermarked = background
        
        # Determine output path
        if output_path is None:
            base, ext = os.path.splitext(image_path)
            basename = os.path.basename(base)
            # Place in images/ directory if not already there
            if not image_path.startswith('images/'):
                output_path = f"images/{basename}_watermarked{ext}"
            else:
                output_path = f"{base}_watermarked{ext}"
        
        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Save the watermarked image
        watermarked.save(output_path, quality=95)
        return output_path
        
    except ImportError:
        print("Warning: PIL not available for watermarking")
        return image_path
    except Exception as e:
        print(f"Error adding text watermark: {e}")
        return image_path

def add_metadata(image_path: str, metadata: dict, output_path: Optional[str] = None) -> str:
    """
    Add metadata to an image file.
    
    Args:
        image_path: Path to the input image
        metadata: Dictionary of metadata to add
        output_path: Optional output path, defaults to input path
        
    Returns:
        Path to the image with metadata
    """
    if not piexif:
        print("Warning: piexif not available for metadata")
        return image_path
        
    try:
        # Load existing EXIF data or create new
        try:
            exif_dict = piexif.load(image_path)
        except:
            exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}
        
        # Add metadata
        if "description" in metadata:
            exif_dict["0th"][piexif.ImageIFD.ImageDescription] = metadata["description"].encode('utf-8')
        
        if "artist" in metadata:
            exif_dict["0th"][piexif.ImageIFD.Artist] = metadata["artist"].encode('utf-8')
        
        if "software" in metadata:
            exif_dict["0th"][piexif.ImageIFD.Software] = metadata["software"].encode('utf-8')
        
        # Add timestamp
        if datetime:
            timestamp = datetime.now().strftime("%Y:%m:%d %H:%M:%S")
            exif_dict["0th"][piexif.ImageIFD.DateTime] = timestamp.encode('utf-8')
        
        # Convert to bytes
        exif_bytes = piexif.dump(exif_dict)
        
        # Determine output path
        if output_path is None:
            output_path = image_path
        
        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Save with metadata
        from PIL import Image
        img = Image.open(image_path)
        img.save(output_path, exif=exif_bytes, quality=95)
        
        return output_path
        
    except Exception as e:
        print(f"Error adding metadata: {e}")
        return image_path

def watermark_for_platform(image_path: str, platform_name: str, 
                           watermark_content: str, is_logo: bool = False,
                           opacity: float = 0.92, output_path: Optional[str] = None) -> str:
    """
    Convenience function to add platform-specific watermarks.
    
    Args:
        image_path: Path to the input image
        platform_name: Platform name ('instagram', 'tiktok', 'twitter', or 'generic')
        watermark_content: Text content or path to logo file
        is_logo: True if watermark_content is a logo file path, False for text
        opacity: Watermark opacity (default 0.92 as specified)
        output_path: Optional output path (if None, defaults to images/ directory)
        
    Returns:
        Path to the watermarked image (in images/ directory unless explicitly overridden)
    """
    # Convert platform name to enum
    platform_map = {
        'instagram': Platform.INSTAGRAM,
        'tiktok': Platform.TIKTOK,
        'twitter': Platform.TWITTER,
        'generic': Platform.GENERIC
    }
    
    platform = platform_map.get(platform_name.lower(), Platform.GENERIC)
    
    # If no output_path is specified, ensure it goes in images/ directory
    # The individual watermark functions handle this logic
    
    if is_logo:
        return add_logo_watermark(image_path, watermark_content, platform, opacity, output_path=output_path)
    else:
        return add_text_watermark(image_path, watermark_content, platform, opacity, output_path=output_path)

def create_branded_image(image_path: str, brand_text: str = "Generated by GON", 
                        platform: Platform = Platform.GENERIC,
                        output_path: Optional[str] = None) -> str:
    """
    Create a branded version of an image with watermark and metadata.
    
    Args:
        image_path: Path to the input image
        brand_text: Branding text to add
        platform: Target platform for positioning
        output_path: Optional output path
        
    Returns:
        Path to the branded image
    """
    # Add watermark with 92% opacity
    watermarked_path = add_text_watermark(image_path, brand_text, platform, 0.92, output_path=output_path)
    
    # Add metadata
    metadata = {
        "description": "AI-generated content with platform-specific watermarking",
        "artist": "GON Image Generator",
        "software": "GON v2.0 - Platform-Optimized"
    }
    
    final_path = add_metadata(watermarked_path, metadata)
    return final_path

def add_combined_watermark(image_path: str, logo_path: str, text: str, 
                          platform: Platform = Platform.GENERIC,
                          opacity: float = 0.92, logo_scale: float = 0.15, 
                          text_scale: float = 0.03, output_path: Optional[str] = None) -> str:
    """
    Add both logo and text watermarks to an image with platform-specific positioning.
    
    Args:
        image_path: Path to the input image
        logo_path: Path to the logo image
        text: Watermark text (e.g., '@Fortuna_Bound')
        platform: Target platform for positioning
        opacity: Watermark opacity (0.0 to 1.0)
        logo_scale: Size of logo relative to image (0.1 = 10% of image width)
        text_scale: Font size relative to image width (0.03 = 3% of image width)
        output_path: Optional output path, defaults to input_path with _watermarked suffix
        
    Returns:
        Path to the watermarked image
    """
    try:
        from PIL import Image, ImageEnhance, ImageDraw, ImageFont
        
        # Load base image
        base_img = Image.open(image_path).convert('RGBA')
        
        # Load and process logo
        logo = Image.open(logo_path).convert('RGBA')
        
        # Scale logo based on image size
        target_width = int(base_img.size[0] * logo_scale)
        logo_aspect = logo.size[1] / logo.size[0]
        target_height = int(target_width * logo_aspect)
        logo = logo.resize((target_width, target_height), Image.Resampling.LANCZOS)
        
        # Adjust logo opacity
        if opacity < 1.0:
            alpha = logo.split()[-1]
            enhancer = ImageEnhance.Brightness(alpha)
            alpha = enhancer.enhance(opacity)
            logo.putalpha(alpha)
        
        # Get platform-specific position for logo
        logo_position = get_platform_position(platform, base_img.size, logo.size)
        
        # Create a copy of base image and paste logo
        watermarked = base_img.copy()
        watermarked.paste(logo, logo_position, logo)
        
        # Now add text watermark
        # Create a transparent overlay for text
        overlay = Image.new('RGBA', watermarked.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Dynamic font sizing
        font_size = max(16, int(base_img.size[0] * text_scale))
        
        # Try to use a better font
        try:
            # Try system fonts in order of preference
            font_paths = [
                "/System/Library/Fonts/Arial Bold.ttf",
                "/System/Library/Fonts/Helvetica.ttc",
                "/System/Library/Fonts/Arial.ttf",
            ]
            font = None
            for font_path in font_paths:
                if os.path.exists(font_path):
                    font = ImageFont.truetype(font_path, font_size)
                    break
            if font is None:
                font = ImageFont.load_default()
        except:
            font = ImageFont.load_default()
        
        # Get text size
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Position text below/near the logo based on platform
        margin = max(20, min(base_img.size[0], base_img.size[1]) // 40)
        if platform == Platform.INSTAGRAM:
            # Text above logo for Instagram (bottom-right)
            text_x = logo_position[0]
            text_y = max(margin, logo_position[1] - text_height - 10)
        elif platform == Platform.TIKTOK:
            # Text below logo for TikTok (mid-left)
            text_x = logo_position[0]
            text_y = min(base_img.size[1] - text_height - margin, logo_position[1] + target_height + 10)
        elif platform == Platform.TWITTER:
            # Text below logo for Twitter (top-right)
            text_x = logo_position[0]
            text_y = min(base_img.size[1] - text_height - margin, logo_position[1] + target_height + 10)
        else:
            # Text above logo (bottom-right)
            text_x = logo_position[0]
            text_y = max(margin, logo_position[1] - text_height - 10)
        
        text_position = (max(0, text_x), max(0, text_y))
        
        # Draw text with semi-transparent background for better readability
        padding = 8
        bg_x1, bg_y1 = text_position[0] - padding, text_position[1] - padding
        bg_x2, bg_y2 = text_position[0] + text_width + padding, text_position[1] + text_height + padding
        
        # Semi-transparent background
        bg_alpha = int(255 * opacity * 0.3)
        draw.rectangle([bg_x1, bg_y1, bg_x2, bg_y2], fill=(0, 0, 0, bg_alpha))
        
        # Draw text with specified opacity
        text_alpha = int(255 * opacity)
        draw.text(text_position, text, font=font, fill=(255, 255, 255, text_alpha))
        
        # Composite the text overlay onto the logo-watermarked image
        final_watermarked = Image.alpha_composite(watermarked, overlay)
        
        # Convert back to RGB if needed
        if final_watermarked.mode == 'RGBA':
            background = Image.new('RGB', final_watermarked.size, (255, 255, 255))
            background.paste(final_watermarked, mask=final_watermarked.split()[-1])
            final_watermarked = background
        
        # Determine output path
        if output_path is None:
            base, ext = os.path.splitext(image_path)
            basename = os.path.basename(base)
            # Place in images/ directory if not already there
            if not image_path.startswith('images/'):
                output_path = f"images/{basename}_watermarked{ext}"
            else:
                output_path = f"{base}_watermarked{ext}"
        
        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Save the watermarked image
        final_watermarked.save(output_path, quality=95)
        return output_path
        
    except ImportError:
        print("Warning: PIL not available for watermarking")
        return image_path
    except Exception as e:
        print(f"Error adding combined watermark: {e}")
        return image_path

def batch_watermark(image_paths: list, platform_name: str, 
                   watermark_content: str, is_logo: bool = False,
                   opacity: float = 0.92) -> list:
    """
    Apply watermarks to multiple images for a specific platform.
    
    Args:
        image_paths: List of paths to input images
        platform_name: Platform name ('instagram', 'tiktok', 'twitter', or 'generic')
        watermark_content: Text content or path to logo file
        is_logo: True if watermark_content is a logo file path, False for text
        opacity: Watermark opacity (default 0.92)
        
    Returns:
        List of paths to watermarked images
    """
    results = []
    for image_path in image_paths:
        try:
            result_path = watermark_for_platform(image_path, platform_name, 
                                                watermark_content, is_logo, opacity)
            results.append(result_path)
            print(f"Watermarked: {image_path} -> {result_path}")
        except Exception as e:
            print(f"Error processing {image_path}: {e}")
            results.append(image_path)
    
    return results

def batch_combined_watermark(image_paths: list, logo_path: str, text: str,
                            platform_name: str = 'generic', opacity: float = 0.92) -> list:
    """
    Apply combined logo and text watermarks to multiple images.
    
    Args:
        image_paths: List of paths to input images
        logo_path: Path to the logo image
        text: Watermark text (e.g., '@Fortuna_Bound')
        platform_name: Platform name ('instagram', 'tiktok', 'twitter', or 'generic')
        opacity: Watermark opacity (default 0.92)
        
    Returns:
        List of paths to watermarked images
    """
    platform_map = {
        'instagram': Platform.INSTAGRAM,
        'tiktok': Platform.TIKTOK,
        'twitter': Platform.TWITTER,
        'generic': Platform.GENERIC
    }
    
    platform = platform_map.get(platform_name.lower(), Platform.GENERIC)
    
    results = []
    for image_path in image_paths:
        try:
            result_path = add_combined_watermark(image_path, logo_path, text, platform, opacity)
            results.append(result_path)
            print(f"Combined watermark applied: {image_path} -> {result_path}")
        except Exception as e:
            print(f"Error processing {image_path}: {e}")
            results.append(image_path)
    
    return results

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 watermark.py <image_path> [watermark_content] [platform] [--logo]")
        print("\nPlatform options: instagram, tiktok, twitter, generic")
        print("\nExamples:")
        print("  python3 watermark.py image.png '@yourhandle' instagram")
        print("  python3 watermark.py image.png logo.png instagram --logo")
        print("  python3 watermark.py image.png 'Custom Text' tiktok")
        sys.exit(1)
    
    image_path = sys.argv[1]
    watermark_content = sys.argv[2] if len(sys.argv) > 2 else "@yourhandle"
    platform_name = sys.argv[3] if len(sys.argv) > 3 else "generic"
    is_logo = "--logo" in sys.argv
    
    if not os.path.exists(image_path):
        print(f"Error: Image file '{image_path}' not found")
        sys.exit(1)
    
    if is_logo and not os.path.exists(watermark_content):
        print(f"Error: Logo file '{watermark_content}' not found")
        sys.exit(1)
    
    print(f"Adding {'logo' if is_logo else 'text'} watermark for {platform_name}...")
    result_path = watermark_for_platform(image_path, platform_name, watermark_content, is_logo)
    print(f"Watermarked image saved to: {result_path}")
    
    # Demonstrate platform-specific positioning
    if len(sys.argv) == 2:  # If only image path provided, create examples for all platforms
        print("\nCreating examples for all platforms...")
        platforms = ['instagram', 'tiktok', 'twitter']
        for platform in platforms:
            base, ext = os.path.splitext(image_path)
            output_path = f"{base}_{platform}{ext}"
            result = watermark_for_platform(image_path, platform, '@yourhandle', False, 0.92, output_path)
            print(f"  {platform.capitalize()}: {result}")

