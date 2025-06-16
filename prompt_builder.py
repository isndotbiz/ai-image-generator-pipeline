#!/usr/bin/env -S bash -c 'source ~/menv/bin/activate && exec "$0" "$@"'
"""
Prompt building utilities for image generation with palette injection and brand tone integration.
"""

import sys
import json
import yaml
import textwrap
from typing import Optional, List, Dict, Any
from pathlib import Path

# Brand tone phrases from content blueprint
BRAND_TONE_PHRASES = {
    "aspirational": [
        "elevating excellence", "pursuing distinction", "achieving refinement", 
        "embracing sophistication", "aspiring to greatness"
    ],
    "motivational": [
        "empowering success", "inspiring achievement", "driving progress", 
        "fostering growth", "catalyzing advancement"
    ],
    "professional": [
        "commercial elegance", "business sophistication", "corporate refinement", 
        "executive presence", "professional distinction"
    ],
    "sophisticated": [
        "refined aesthetics", "premium craftsmanship", "luxurious appeal", 
        "elegant composition", "sophisticated styling"
    ],
    "empowering": [
        "confident presentation", "authoritative positioning", "commanding presence", 
        "influential messaging", "empowered perspective"
    ]
}

def load_palette(palette_id: str) -> Optional[Dict[str, Any]]:
    """
    Load palette data from JSON files.
    
    Args:
        palette_id: Palette identifier (e.g., 'A', 'B', or filename)
        
    Returns:
        Palette data dictionary or None if not found
    """
    current_dir = Path.cwd()
    
    # Try different palette file patterns
    palette_files = [
        f"palette_{palette_id.upper()}.json",
        f"palette_{palette_id.lower()}.json",
        f"{palette_id}.json",
        "palettes.json"  # Fallback to main palettes file
    ]
    
    for palette_file in palette_files:
        palette_path = current_dir / palette_file
        if palette_path.exists():
            try:
                with open(palette_path, 'r') as f:
                    data = json.load(f)
                    
                # Handle different palette file structures
                if 'colors' in data:  # Individual palette file
                    return data
                elif 'aggregated_colors' in data:  # Main palettes file
                    return {"colors": data['aggregated_colors'][:5]}  # Take first 5 colors
                    
            except (json.JSONDecodeError, FileNotFoundError):
                continue
    
    return None

def extract_color_directives(palette_data: Dict[str, Any]) -> str:
    """
    Extract and format color directives from palette data.
    
    Args:
        palette_data: Palette data dictionary
        
    Returns:
        Formatted color directive string
    """
    if not palette_data or 'colors' not in palette_data:
        return ""
    
    colors = palette_data['colors']
    if not colors:
        return ""
    
    # Take the first two dominant colors for primary colors
    primary_colors = []
    for color in colors[:2]:
        if 'hex' in color:
            primary_colors.append(color['hex'])
        elif isinstance(color, dict) and 'hex' in color:
            primary_colors.append(color['hex'])
    
    if primary_colors:
        color_list = ", ".join(primary_colors)
        return f"primary colors {{{color_list}}}, harmonious background"
    
    return ""

def get_brand_tone_phrase(tone_type: str = "sophisticated") -> str:
    """
    Get a brand tone phrase from the approved content blueprint.
    
    Args:
        tone_type: Type of tone to use
        
    Returns:
        Brand tone phrase
    """
    if tone_type in BRAND_TONE_PHRASES:
        phrases = BRAND_TONE_PHRASES[tone_type]
        # Use first phrase for consistency, could be randomized if needed
        return phrases[0]
    return "refined sophistication"

def build_enhanced_prompt_with_palette(location: str, item: str, mantra: str, 
                                     aspect_ratio: str = "4:5",
                                     palette_id: Optional[str] = None,
                                     tone_type: str = "sophisticated") -> str:
    """
    Build an enhanced product photography prompt with palette injection and brand tone.
    
    Args:
        location: The setting/background location
        item: The product item to feature
        mantra: Brand mantra/text overlay
        aspect_ratio: Image aspect ratio
        palette_id: Palette identifier for color injection
        tone_type: Brand tone type
        
    Returns:
        Enhanced prompt string with color directives and brand tone
    """
    # Start with base professional photography prompt
    base_prompt = f"Professional product photography: {location}, {item} prominently displayed"
    
    # Add color directives if palette is provided
    color_directive = ""
    if palette_id:
        palette_data = load_palette(palette_id)
        if palette_data:
            color_directive = extract_color_directives(palette_data)
    
    # Add camera and lighting settings
    camera_settings = "Canon EOS R5 35 mm f/1.8 ISO 200, clean natural lighting"
    
    # Inject color directives
    if color_directive:
        base_prompt += f", {camera_settings}, {color_directive}"
    else:
        base_prompt += f", {camera_settings}"
    
    # Add brand tone phrase
    brand_tone = get_brand_tone_phrase(tone_type)
    base_prompt += f", {brand_tone}"
    
    # Add mantra and aspect ratio
    base_prompt += f', text overlay "{mantra}", {aspect_ratio}, commercial photography style'
    
    return base_prompt

# Legacy functions for backward compatibility
def build_product_prompt(location: str, item: str, text_overlay: str, 
                        aspect_ratio: str = "4:5", 
                        style: str = "commercial photography style") -> str:
    """
    Build a professional product photography prompt (legacy function).
    
    Args:
        location: The setting/background location
        item: The product item to feature
        text_overlay: Text to overlay on the image
        aspect_ratio: Image aspect ratio
        style: Photography style description
        
    Returns:
        Formatted prompt string
    """
    prompt = f"""Professional product photography: modern {location}, {item} prominently displayed, \
Canon EOS R5 35 mm f/1.8 ISO 200, clean natural lighting, \
text overlay "{text_overlay}", {aspect_ratio}, {style}"""
    return prompt

def get_negative_prompt() -> str:
    """
    Get the standard negative prompt for filtering unwanted content.
    
    Returns:
        Negative prompt string
    """
    return ("lowres, jpeg artifacts, plastic, text, watermark, "
            "logo, duplicate, deformed, bad anatomy, nsfw, inappropriate")

def build_enhanced_prompt(location: str, item: str, text_overlay: str, 
                         aspect_ratio: str = "4:5",
                         color_palette: Optional[str] = None,
                         lighting: str = "clean natural lighting",
                         camera: str = "Canon EOS R5 35 mm f/1.8 ISO 200") -> str:
    """
    Build an enhanced product photography prompt with optional color palette (legacy function).
    
    Args:
        location: The setting/background location
        item: The product item to feature
        text_overlay: Text to overlay on the image
        aspect_ratio: Image aspect ratio
        color_palette: Optional color palette description
        lighting: Lighting description
        camera: Camera and settings description
        
    Returns:
        Enhanced prompt string
    """
    base_prompt = f"Professional product photography: modern {location}, {item} prominently displayed, {camera}, {lighting}"
    
    if color_palette:
        base_prompt += f", {color_palette}"
    
    base_prompt += f', text overlay "{text_overlay}", {aspect_ratio}, commercial photography style'
    
    return base_prompt

def validate_prompt_args(location: str, item: str, text_overlay: str, aspect_ratio: str) -> bool:
    """
    Validate prompt arguments.
    
    Args:
        location: Location string
        item: Item string
        text_overlay: Text overlay string
        aspect_ratio: Aspect ratio string
        
    Returns:
        True if all arguments are valid
    """
    if not all([location.strip(), item.strip(), text_overlay.strip(), aspect_ratio.strip()]):
        return False
    
    valid_ratios = ["1:1", "4:5", "3:4", "9:16", "16:9", "2:3", "3:2"]
    if aspect_ratio not in valid_ratios:
        print(f"Warning: Aspect ratio '{aspect_ratio}' not in common ratios: {valid_ratios}")
    
    return True

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python3 prompt_builder.py <location> <item> <mantra> [aspect_ratio] [palette_id]")
        print("")
        print("Enhanced prompt builder with palette injection and brand tone phrases")
        print("")
        print("Arguments:")
        print("  location     - Setting/background location (e.g., 'luxury office', 'modern studio')")
        print("  item         - Product item to feature (e.g., 'golden watch', 'leather briefcase')")
        print("  mantra       - Brand mantra/text overlay (e.g., 'Invest Now, Thank Yourself Later')")
        print("  aspect_ratio - Image aspect ratio (optional, default: '4:5')")
        print("  palette_id   - Palette identifier for color injection (optional, e.g., 'A', 'B')")
        print("")
        print("Examples:")
        print("  python3 prompt_builder.py 'luxury office' 'golden watch' 'Invest Now, Thank Yourself Later'")
        print("  python3 prompt_builder.py 'modern studio' 'leather briefcase' 'Build Your Capital Foundation' '3:4' 'A'")
        sys.exit(1)
    
    location = sys.argv[1]
    item = sys.argv[2]
    mantra = sys.argv[3]
    aspect_ratio = sys.argv[4] if len(sys.argv) > 4 else "4:5"
    palette_id = sys.argv[5] if len(sys.argv) > 5 else None
    
    if not validate_prompt_args(location, item, mantra, aspect_ratio):
        print("Error: Invalid arguments provided")
        sys.exit(1)
    
    # Use the new enhanced prompt builder with palette injection
    prompt = build_enhanced_prompt_with_palette(
        location=location,
        item=item,
        mantra=mantra,
        aspect_ratio=aspect_ratio,
        palette_id=palette_id,
        tone_type="sophisticated"  # Can be made configurable if needed
    )
    
    negative_prompt = get_negative_prompt()
    
    print("=== Enhanced Prompt Builder Output ===")
    print(f"Location: {location}")
    print(f"Item: {item}")
    print(f"Mantra: {mantra}")
    print(f"Aspect Ratio: {aspect_ratio}")
    if palette_id:
        print(f"Palette ID: {palette_id}")
        palette_data = load_palette(palette_id)
        if palette_data:
            color_directive = extract_color_directives(palette_data)
            if color_directive:
                print(f"Color Directive: {color_directive}")
            else:
                print("Color Directive: None (no valid colors found)")
        else:
            print(f"Warning: Palette '{palette_id}' not found")
    print("")
    print(f"Prompt: {prompt}")
    print("")
    print(f"Negative prompt: {negative_prompt}")

