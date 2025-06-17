#!/usr/bin/env python3
"""
Uplifting Mantra Generator for Fortuna Bound

Generates inspiring mantras for image overlays with perfect text placement.
Includes preview functionality and categorized mantra collections.

Usage:
    python3 mantra_generator.py --category prosperity
    python3 mantra_generator.py --random 5
    python3 mantra_generator.py --preview "Your Custom Mantra"
"""

import random
import argparse
import json
from typing import List, Dict, Optional
from datetime import datetime

class MantraGenerator:
    def __init__(self):
        self.mantras = {
            "prosperity": [
                "Honor the Path to Prosperity",
                "Abundance Flows Through Me",
                "Success is My Natural State",
                "I Create Wealth with Purpose",
                "Prosperity Aligns with My Values",
                "I Am Worthy of Financial Freedom",
                "My Success Inspires Others",
                "I Attract Abundant Opportunities",
                "Wealth Follows My Authentic Actions",
                "I Build Lasting Legacy"
            ],
            "empowerment": [
                "I Am the Architect of My Destiny",
                "My Power Comes from Within",
                "I Rise Above Every Challenge",
                "Strength Flows Through My Being",
                "I Command My Own Reality",
                "Confidence is My Foundation",
                "I Transform Obstacles into Opportunities",
                "My Voice Matters and is Heard",
                "I Lead with Courage and Grace",
                "Unstoppable Energy Drives Me Forward"
            ],
            "growth": [
                "Every Day I Become Better",
                "I Embrace Change as Growth",
                "Learning is My Superpower",
                "I Expand Beyond My Comfort Zone",
                "Progress Over Perfection",
                "I Evolve with Each Experience",
                "My Potential is Limitless",
                "I Turn Setbacks into Comebacks",
                "Growth Happens in the Challenge",
                "I Am Always Becoming More"
            ],
            "mindfulness": [
                "This Moment is My Power",
                "I Am Present and Aware",
                "Peace Flows Through My Being",
                "I Choose Calm in Every Storm",
                "Gratitude Fills My Heart",
                "I Find Joy in Simple Moments",
                "My Mind is Clear and Focused",
                "I Breathe in Peace, Exhale Stress",
                "Serenity is My Natural State",
                "I Am Centered and Grounded"
            ],
            "success": [
                "Excellence is My Standard",
                "I Achieve with Integrity",
                "Victory Follows My Dedication",
                "I Make Success Look Effortless",
                "My Dreams Become Reality",
                "I Win by Lifting Others",
                "Success is My Responsibility",
                "I Master What I Focus On",
                "Achievement Flows Naturally to Me",
                "I Create Success on My Terms"
            ],
            "luxury": [
                "I Deserve the Finest in Life",
                "Elegance is My Expression",
                "I Surround Myself with Beauty",
                "Quality Over Quantity Always",
                "I Live Life in Full Color",
                "Sophistication Defines My Style",
                "I Choose Premium Experiences",
                "Luxury is My Natural Environment",
                "I Appreciate Life's Refinements",
                "Excellence is Non-Negotiable"
            ]
        }
    
    def get_random_mantras(self, count: int = 5, category: Optional[str] = None) -> List[Dict]:
        """Get random mantras with metadata"""
        if category and category in self.mantras:
            source_mantras = [(mantra, category) for mantra in self.mantras[category]]
        else:
            source_mantras = [(mantra, cat) for cat, mantras in self.mantras.items() for mantra in mantras]
        
        selected = random.sample(source_mantras, min(count, len(source_mantras)))
        
        return [{
            "text": mantra,
            "category": cat,
            "length": len(mantra),
            "word_count": len(mantra.split()),
            "preview_id": f"mantra_{i+1}"
        } for i, (mantra, cat) in enumerate(selected)]
    
    def get_by_category(self, category: str) -> List[str]:
        """Get all mantras from a specific category"""
        return self.mantras.get(category, [])
    
    def get_all_categories(self) -> List[str]:
        """Get list of all available categories"""
        return list(self.mantras.keys())
    
    def preview_text_placement(self, text: str, image_width: int = 1080, image_height: int = 1350) -> Dict:
        """Preview text placement for given dimensions"""
        # Calculate optimal text size and position
        char_count = len(text)
        word_count = len(text.split())
        
        # Estimate font size based on image size and text length
        base_font_size = min(image_width, image_height) // 20
        font_size = max(24, base_font_size - (char_count // 8))
        
        # Calculate text dimensions (rough estimate)
        avg_char_width = font_size * 0.6
        text_width = len(text) * avg_char_width
        text_height = font_size * 1.2
        
        # Calculate optimal positioning (bottom third, centered)
        margin = min(image_width, image_height) * 0.05
        x_position = (image_width - text_width) // 2
        y_position = image_height - (image_height // 3) - text_height - margin
        
        return {
            "text": text,
            "font_size": font_size,
            "position": {
                "x": max(margin, x_position),
                "y": max(margin, y_position)
            },
            "dimensions": {
                "width": text_width,
                "height": text_height
            },
            "image_size": {
                "width": image_width,
                "height": image_height
            },
            "metrics": {
                "char_count": char_count,
                "word_count": word_count,
                "readability": "good" if char_count <= 40 else "long" if char_count <= 60 else "very_long"
            }
        }
    
    def generate_mantra_options(self, theme: Optional[str] = None, count: int = 5) -> Dict:
        """Generate mantra options with previews"""
        mantras = self.get_random_mantras(count, theme)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "theme": theme or "mixed",
            "count": len(mantras),
            "options": [
                {
                    **mantra,
                    "preview": self.preview_text_placement(mantra["text"])
                } for mantra in mantras
            ],
            "categories_available": self.get_all_categories()
        }

def main():
    parser = argparse.ArgumentParser(description="Generate uplifting mantras for image overlays")
    parser.add_argument("--category", choices=["prosperity", "empowerment", "growth", "mindfulness", "success", "luxury"], 
                       help="Category of mantras to generate")
    parser.add_argument("--random", type=int, default=5, 
                       help="Number of random mantras to generate")
    parser.add_argument("--preview", type=str, 
                       help="Preview text placement for custom mantra")
    parser.add_argument("--list-categories", action="store_true", 
                       help="List all available categories")
    parser.add_argument("--output", choices=["json", "text"], default="text", 
                       help="Output format")
    
    args = parser.parse_args()
    generator = MantraGenerator()
    
    if args.list_categories:
        print("Available mantra categories:")
        for category in generator.get_all_categories():
            print(f"  - {category}")
        return
    
    if args.preview:
        preview = generator.preview_text_placement(args.preview)
        if args.output == "json":
            print(json.dumps(preview, indent=2))
        else:
            print(f"Preview for: '{args.preview}'")
            print(f"Font size: {preview['font_size']}px")
            print(f"Position: ({preview['position']['x']}, {preview['position']['y']})")
            print(f"Readability: {preview['metrics']['readability']}")
        return
    
    # Generate mantra options
    options = generator.generate_mantra_options(args.category, args.random)
    
    if args.output == "json":
        print(json.dumps(options, indent=2))
    else:
        print(f"\n🌟 Generated {options['count']} mantras ({options['theme']} theme):\n")
        
        for i, option in enumerate(options['options'], 1):
            print(f"{i}. \"{option['text']}\"")
            print(f"   Category: {option['category']}")
            print(f"   Length: {option['word_count']} words, {option['length']} characters")
            print(f"   Readability: {option['preview']['metrics']['readability']}")
            print(f"   Font size: {option['preview']['font_size']}px")
            print()
        
        print(f"💡 Use --preview \"Your Mantra\" to test custom text placement")
        print(f"🎨 Available categories: {', '.join(options['categories_available'])}")

if __name__ == "__main__":
    main()

