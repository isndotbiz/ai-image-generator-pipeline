#!/usr/bin/env python3
"""
Direct Prompt Generator for Fortuna Bound

Allows creation of images directly from custom prompts without requiring
location/item/mantra structure. Includes mantra integration and optimization.

Usage:
    python3 direct_prompt_generator.py "luxury car in mountains" --mantra "Success Follows Me"
    python3 direct_prompt_generator.py "elegant woman reading" --generate-mantra prosperity
    python3 direct_prompt_generator.py "beautiful sunset" --aspect-ratio 16:9 --platform tw
"""

import argparse
import sys
import os
from typing import Optional, Dict
from datetime import datetime

# Import our mantra generator
try:
    from mantra_generator import MantraGenerator
except ImportError:
    print("Error: mantra_generator.py not found")
    sys.exit(1)

class DirectPromptGenerator:
    def __init__(self):
        self.mantra_gen = MantraGenerator()
        
        # Style presets for different themes
        self.style_presets = {
            "luxury": "luxury lifestyle photography, elegant composition, premium lighting, sophisticated aesthetics",
            "business": "professional photography, corporate setting, clean composition, modern business aesthetic",
            "wellness": "serene atmosphere, natural lighting, calming composition, mindful aesthetic",
            "success": "aspirational photography, achievement theme, confident composition, success aesthetic",
            "nature": "natural photography, organic composition, environmental lighting, peaceful aesthetic",
            "urban": "urban photography, city aesthetic, modern composition, metropolitan style",
            "minimal": "minimalist photography, clean lines, simple composition, elegant restraint",
            "artistic": "creative photography, artistic composition, unique perspective, expressive style"
        }
        
        # Platform-specific optimizations
        self.platform_specs = {
            "ig": {"name": "Instagram", "optimal_ratios": ["1:1", "4:5", "9:16"], "style": "vibrant, engaging"},
            "tt": {"name": "TikTok", "optimal_ratios": ["9:16", "1:1"], "style": "dynamic, eye-catching"},
            "tw": {"name": "Twitter", "optimal_ratios": ["16:9", "2:1"], "style": "professional, clear"},
            "li": {"name": "LinkedIn", "optimal_ratios": ["1.91:1", "1:1"], "style": "professional, business-focused"},
            "fb": {"name": "Facebook", "optimal_ratios": ["1.91:1", "1:1"], "style": "engaging, social"}
        }
    
    def enhance_prompt(self, base_prompt: str, style: Optional[str] = None, 
                      platform: str = "ig", mantra: Optional[str] = None) -> str:
        """Enhance a basic prompt with style and technical specifications"""
        
        # Start with base prompt
        enhanced = base_prompt.strip()
        
        # Add explicit no-text directive since we add mantras via watermarking
        enhanced += ", no text, no writing, no words, no typography, no signs"
        
        # Add style preset if specified
        if style and style in self.style_presets:
            enhanced += f", {self.style_presets[style]}"
        
        # Add platform optimization
        if platform in self.platform_specs:
            platform_style = self.platform_specs[platform]["style"]
            enhanced += f", {platform_style} composition"
        
        # Add technical specifications
        enhanced += ", Canon EOS R5 35mm f/1.8 ISO 200, professional lighting"
        
        # Add color harmony
        enhanced += ", harmonious color palette, refined aesthetics"
        
        # NOTE: We don't add text overlay in the prompt since we add mantras via watermarking
        # The mantra parameter is kept for compatibility but not used in prompt
        
        # Add aspect ratio note
        enhanced += ", commercial photography style"
        
        return enhanced
    
    def generate_with_mantra(self, prompt: str, mantra_category: Optional[str] = None, 
                           custom_mantra: Optional[str] = None, count: int = 1) -> Dict:
        """Generate enhanced prompts with mantras"""
        
        results = []
        
        if custom_mantra:
            # Use provided mantra
            mantras = [{"text": custom_mantra, "category": "custom"}]
        elif mantra_category:
            # Generate mantras from category
            mantra_options = self.mantra_gen.generate_mantra_options(mantra_category, count)
            mantras = mantra_options["options"]
        else:
            # Generate mixed mantras
            mantra_options = self.mantra_gen.generate_mantra_options(None, count)
            mantras = mantra_options["options"]
        
        for i, mantra_data in enumerate(mantras):
            mantra_text = mantra_data["text"]
            enhanced_prompt = self.enhance_prompt(prompt, mantra=mantra_text)
            
            result = {
                "id": i + 1,
                "base_prompt": prompt,
                "enhanced_prompt": enhanced_prompt,
                "mantra": {
                    "text": mantra_text,
                    "category": mantra_data.get("category", "unknown"),
                    "preview": self.mantra_gen.preview_text_placement(mantra_text)
                },
                "timestamp": datetime.now().isoformat()
            }
            results.append(result)
        
        return {
            "base_prompt": prompt,
            "count": len(results),
            "results": results
        }
    
    def preview_generation(self, prompt: str, style: Optional[str] = None, 
                          platform: str = "ig", aspect_ratio: str = "4:5") -> Dict:
        """Preview what will be generated without actually creating image"""
        
        enhanced_prompt = self.enhance_prompt(prompt, style, platform)
        
        return {
            "preview": {
                "base_prompt": prompt,
                "enhanced_prompt": enhanced_prompt,
                "style": style or "default",
                "platform": self.platform_specs.get(platform, {"name": platform}),
                "aspect_ratio": aspect_ratio,
                "estimated_length": len(enhanced_prompt),
                "word_count": len(enhanced_prompt.split()),
                "timestamp": datetime.now().isoformat()
            },
            "recommendations": {
                "optimal_ratios": self.platform_specs.get(platform, {}).get("optimal_ratios", ["4:5"]),
                "style_suggestions": list(self.style_presets.keys()),
                "mantra_categories": self.mantra_gen.get_all_categories()
            }
        }

def main():
    parser = argparse.ArgumentParser(description="Generate images directly from custom prompts")
    parser.add_argument("prompt", help="Base image prompt/description")
    parser.add_argument("--style", choices=list(DirectPromptGenerator().style_presets.keys()),
                       help="Style preset to apply")
    parser.add_argument("--platform", choices=["ig", "tt", "tw", "li", "fb"], default="ig",
                       help="Target platform for optimization")
    parser.add_argument("--aspect-ratio", default="4:5", 
                       help="Image aspect ratio (e.g., 4:5, 16:9, 1:1)")
    parser.add_argument("--mantra", type=str, 
                       help="Custom mantra to overlay on image")
    parser.add_argument("--generate-mantra", choices=["prosperity", "empowerment", "growth", "mindfulness", "success", "luxury"],
                       help="Generate mantras from category")
    parser.add_argument("--mantra-count", type=int, default=3,
                       help="Number of mantras to generate")
    parser.add_argument("--preview-only", action="store_true",
                       help="Only preview the enhanced prompt, don't generate image")
    parser.add_argument("--output", default="enhanced_prompt",
                       help="Output file path for generated image")
    parser.add_argument("--list-styles", action="store_true",
                       help="List all available style presets")
    
    args = parser.parse_args()
    generator = DirectPromptGenerator()
    
    if args.list_styles:
        print("\n🎨 Available style presets:")
        for style, description in generator.style_presets.items():
            print(f"  {style:12} - {description}")
        print("\n💡 Example: python3 direct_prompt_generator.py 'woman reading' --style luxury")
        return
    
    if not args.prompt:
        print("Error: Please provide a prompt")
        return
    
    if args.preview_only:
        # Just preview the enhanced prompt
        preview = generator.preview_generation(args.prompt, args.style, args.platform, args.aspect_ratio)
        
        print(f"\n🔍 Prompt Preview:")
        print(f"📝 Base: {preview['preview']['base_prompt']}")
        print(f"✨ Enhanced: {preview['preview']['enhanced_prompt']}")
        print(f"🎨 Style: {preview['preview']['style']}")
        print(f"📱 Platform: {preview['preview']['platform'].get('name', args.platform)}")
        print(f"📐 Aspect Ratio: {preview['preview']['aspect_ratio']}")
        print(f"📊 Length: {preview['preview']['word_count']} words")
        
        print(f"\n💡 Recommendations:")
        print(f"📐 Optimal ratios: {', '.join(preview['recommendations']['optimal_ratios'])}")
        print(f"🎨 Style options: {', '.join(preview['recommendations']['style_suggestions'][:5])}...")
        return
    
    # Handle mantra generation or custom mantra
    if args.mantra or args.generate_mantra:
        if args.mantra and args.generate_mantra:
            print("Warning: Both custom mantra and generated mantra specified. Using custom mantra.")
        
        result = generator.generate_with_mantra(
            args.prompt,
            args.generate_mantra,
            args.mantra,
            args.mantra_count if args.generate_mantra else 1
        )
        
        print(f"\n🌟 Generated {result['count']} enhanced prompt(s) with mantras:\n")
        
        for i, item in enumerate(result['results']):
            print(f"{i+1}. Enhanced Prompt:")
            print(f"   {item['enhanced_prompt']}")
            print(f"")
            print(f"   💫 Mantra: '{item['mantra']['text']}'")
            print(f"   📂 Category: {item['mantra']['category']}")
            print(f"   📏 Font size: {item['mantra']['preview']['font_size']}px")
            print(f"   📍 Position: ({item['mantra']['preview']['position']['x']}, {item['mantra']['preview']['position']['y']})")
            print()
    
    else:
        # Generate without mantra
        enhanced_prompt = generator.enhance_prompt(args.prompt, args.style, args.platform)
        
        print(f"\n✨ Enhanced Prompt:")
        print(f"{enhanced_prompt}")
        print(f"\n📊 Details:")
        print(f"📝 Base prompt: {args.prompt}")
        print(f"🎨 Style: {args.style or 'default'}")
        print(f"📱 Platform: {generator.platform_specs.get(args.platform, {}).get('name', args.platform)}")
        print(f"📐 Aspect ratio: {args.aspect_ratio}")
    
    print(f"\n🚀 To generate image:")
    if args.mantra or args.generate_mantra:
        print(f"   Copy one of the enhanced prompts above")
    else:
        print(f"   python3 generate.py \"{enhanced_prompt.replace('"', '\"')}\" \"images/{args.output}.png\" \"{args.aspect_ratio}\"")

if __name__ == "__main__":
    main()

