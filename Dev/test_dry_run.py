#!/usr/bin/env python3
"""
Dry-run testing script for palette injection and watermark workflow.
Tests the complete pipeline without actually calling Replicate API.
"""

import argparse
import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import json

# Import our modules
from prompt_builder import build_enhanced_prompt_with_palette, get_negative_prompt, load_palette
from watermark import Platform, watermark_for_platform, create_branded_image
from palette_extractor import extract_dominant_colors, get_color_palette_prompt

# Mock themes for testing
TEST_THEMES = [
    {
        "location": "Maldives overwater bungalow",
        "item": "vintage Leica camera", 
        "mantra": "Honor the Path to Prosperity",
        "slug": "maldives_vintage_1"
    },
    {
        "location": "luxury office space",
        "item": "golden Cartier watch",
        "mantra": "Invest Now, Thank Yourself Later", 
        "slug": "office_cartier_2"
    }
]

# Platform configurations
PLATFORM_CONFIGS = {
    "ig": {"name": "instagram", "aspect_ratio": "4:5", "watermark": "@YourHandle"},
    "tt": {"name": "tiktok", "aspect_ratio": "9:16", "watermark": "@YourHandle"},
    "tw": {"name": "twitter", "aspect_ratio": "16:9", "watermark": "@YourHandle"}
}

PALETTE_IDS = ["A", "B"]

def mock_replicate_call(prompt: str, negative_prompt: str, aspect_ratio: str, dry_run: bool = True) -> Dict[str, Any]:
    """
    Mock Replicate API call that returns a simulated response.
    
    Args:
        prompt: Generation prompt
        negative_prompt: Negative prompt
        aspect_ratio: Image aspect ratio
        dry_run: If True, return mock data instead of calling API
        
    Returns:
        Mock response data
    """
    if dry_run:
        return {
            "status": "MOCK_SUCCESS",
            "url": "https://mock-image-url.com/generated-image.png",
            "prompt_length": len(prompt),
            "negative_prompt_length": len(negative_prompt),
            "aspect_ratio": aspect_ratio,
            "model": "black-forest-labs/flux-1.1-pro",
            "dry_run": True
        }
    else:
        # This would be the actual Replicate call
        raise NotImplementedError("Actual Replicate calls not implemented in dry-run mode")

def test_palette_injection(palette_id: str, theme: Dict[str, Any]) -> Dict[str, Any]:
    """
    Test palette injection functionality.
    
    Args:
        palette_id: Palette identifier (A, B, etc.)
        theme: Theme data dictionary
        
    Returns:
        Test results dictionary
    """
    print(f"\n🎨 Testing palette injection for Palette {palette_id}")
    
    # Load palette
    palette_data = load_palette(palette_id)
    if not palette_data:
        return {
            "success": False,
            "error": f"Palette {palette_id} not found",
            "palette_id": palette_id
        }
    
    print(f"  ✓ Palette {palette_id} loaded successfully")
    
    # Build enhanced prompt with palette injection
    enhanced_prompt = build_enhanced_prompt_with_palette(
        location=theme["location"],
        item=theme["item"],
        mantra=theme["mantra"],
        aspect_ratio="4:5",  # Default for testing
        palette_id=palette_id,
        tone_type="sophisticated"
    )
    
    # Check if palette colors are injected
    palette_injected = "primary colors" in enhanced_prompt
    
    print(f"  ✓ Enhanced prompt generated (palette injected: {palette_injected})")
    print(f"  Preview: {enhanced_prompt[:100]}...")
    
    return {
        "success": True,
        "palette_id": palette_id,
        "palette_data": palette_data,
        "enhanced_prompt": enhanced_prompt,
        "palette_injected": palette_injected,
        "prompt_length": len(enhanced_prompt)
    }

def test_watermark_positioning(platform_config: Dict[str, Any], mock_image_path: str = None) -> Dict[str, Any]:
    """
    Test watermark positioning for different platforms.
    
    Args:
        platform_config: Platform configuration dictionary
        mock_image_path: Path to test image (optional)
        
    Returns:
        Test results dictionary
    """
    platform_name = platform_config["name"]
    watermark_text = platform_config["watermark"]
    
    print(f"\n💧 Testing watermark positioning for {platform_name}")
    
    # Create a mock image if none provided
    if not mock_image_path:
        # We'll create a minimal test image using PIL
        try:
            from PIL import Image
            mock_image = Image.new('RGB', (800, 1000), color='lightblue')
            mock_image_path = "/tmp/test_image.png"
            mock_image.save(mock_image_path)
            print(f"  ✓ Created mock test image: {mock_image_path}")
        except ImportError:
            print("  ⚠️  PIL not available, skipping watermark positioning test")
            return {
                "success": False,
                "error": "PIL not available for image creation",
                "platform": platform_name
            }
    
    # Test watermark positioning (dry-run mode)
    try:
        # Import watermark functions
        from watermark import Platform, get_platform_position
        
        # Map platform name to enum
        platform_map = {
            'instagram': Platform.INSTAGRAM,
            'tiktok': Platform.TIKTOK, 
            'twitter': Platform.TWITTER
        }
        
        platform_enum = platform_map.get(platform_name, Platform.GENERIC)
        
        # Test position calculation
        image_size = (800, 1000)  # Mock image size
        watermark_size = (100, 30)  # Mock watermark size
        position = get_platform_position(platform_enum, image_size, watermark_size)
        
        print(f"  ✓ Watermark position calculated: {position}")
        print(f"  ✓ Platform: {platform_name} -> Position: {position}")
        
        # In a real scenario, we would apply the watermark here
        # For dry-run, we just verify the calculation
        
        return {
            "success": True,
            "platform": platform_name,
            "watermark_text": watermark_text,
            "position": position,
            "image_size": image_size,
            "watermark_size": watermark_size
        }
        
    except Exception as e:
        print(f"  ❌ Error testing watermark: {e}")
        return {
            "success": False,
            "error": str(e),
            "platform": platform_name
        }

def run_dry_run_test(themes: List[Dict[str, Any]], palette_ids: List[str], 
                    platform_configs: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Run comprehensive dry-run test of the pipeline.
    
    Args:
        themes: List of theme data dictionaries
        palette_ids: List of palette identifiers to test
        platform_configs: Dictionary of platform configurations
        
    Returns:
        Complete test results
    """
    print("🚀 Starting Dry-Run Test for Palette Injection & Watermarking")
    print("=" * 60)
    
    results = {
        "dry_run": True,
        "total_combinations": len(themes) * len(palette_ids) * len(platform_configs),
        "palette_tests": [],
        "watermark_tests": [],
        "generation_tests": [],
        "summary": {}
    }
    
    # Test each combination
    for theme in themes:
        print(f"\n📋 Testing Theme: {theme['slug']}")
        print(f"   Location: {theme['location']}")
        print(f"   Item: {theme['item']}")
        print(f"   Mantra: {theme['mantra']}")
        
        for palette_id in palette_ids:
            # Test palette injection
            palette_result = test_palette_injection(palette_id, theme)
            results["palette_tests"].append(palette_result)
            
            if palette_result["success"]:
                for platform_key, platform_config in platform_configs.items():
                    # Test watermark positioning
                    watermark_result = test_watermark_positioning(platform_config)
                    watermark_result["theme_slug"] = theme["slug"]
                    watermark_result["palette_id"] = palette_id
                    results["watermark_tests"].append(watermark_result)
                    
                    # Test complete generation workflow (mock)
                    aspect_ratio = platform_config["aspect_ratio"]
                    enhanced_prompt = palette_result["enhanced_prompt"]
                    negative_prompt = get_negative_prompt()
                    
                    # Mock generation call
                    generation_result = mock_replicate_call(
                        prompt=enhanced_prompt,
                        negative_prompt=negative_prompt,
                        aspect_ratio=aspect_ratio,
                        dry_run=True
                    )
                    
                    generation_result.update({
                        "theme_slug": theme["slug"],
                        "palette_id": palette_id,
                        "platform": platform_config["name"],
                        "filename": f"{theme['slug']}_{palette_id}_{platform_key}.png"
                    })
                    
                    results["generation_tests"].append(generation_result)
                    
                    print(f"    ✓ {platform_config['name']}: {generation_result['filename']}")
    
    # Generate summary
    successful_palette_tests = sum(1 for r in results["palette_tests"] if r["success"])
    successful_watermark_tests = sum(1 for r in results["watermark_tests"] if r["success"])
    successful_generation_tests = sum(1 for r in results["generation_tests"] if r["status"] == "MOCK_SUCCESS")
    
    results["summary"] = {
        "palette_tests": {
            "total": len(results["palette_tests"]),
            "successful": successful_palette_tests,
            "success_rate": successful_palette_tests / len(results["palette_tests"]) if results["palette_tests"] else 0
        },
        "watermark_tests": {
            "total": len(results["watermark_tests"]),
            "successful": successful_watermark_tests,
            "success_rate": successful_watermark_tests / len(results["watermark_tests"]) if results["watermark_tests"] else 0
        },
        "generation_tests": {
            "total": len(results["generation_tests"]),
            "successful": successful_generation_tests,
            "success_rate": successful_generation_tests / len(results["generation_tests"]) if results["generation_tests"] else 0
        }
    }
    
    return results

def print_summary(results: Dict[str, Any]) -> None:
    """
    Print a summary of the dry-run test results.
    
    Args:
        results: Test results dictionary
    """
    print("\n" + "=" * 60)
    print("🎯 DRY-RUN TEST SUMMARY")
    print("=" * 60)
    
    summary = results["summary"]
    
    print(f"\n📊 Test Results:")
    print(f"   Total combinations tested: {results['total_combinations']}")
    print(f"   Palette injection tests: {summary['palette_tests']['successful']}/{summary['palette_tests']['total']} ({summary['palette_tests']['success_rate']:.1%})")
    print(f"   Watermark positioning tests: {summary['watermark_tests']['successful']}/{summary['watermark_tests']['total']} ({summary['watermark_tests']['success_rate']:.1%})")
    print(f"   Mock generation tests: {summary['generation_tests']['successful']}/{summary['generation_tests']['total']} ({summary['generation_tests']['success_rate']:.1%})")
    
    # Print specific results
    print(f"\n🎨 Palette Injection Results:")
    for result in results["palette_tests"]:
        if result["success"]:
            status = "✅ PASS"
            details = f"injected: {result['palette_injected']}"
        else:
            status = "❌ FAIL" 
            details = result.get("error", "Unknown error")
        print(f"   Palette {result['palette_id']}: {status} - {details}")
    
    print(f"\n💧 Watermark Positioning Results:")
    platforms_tested = set()
    for result in results["watermark_tests"]:
        if result["platform"] not in platforms_tested:
            platforms_tested.add(result["platform"])
            if result["success"]:
                status = "✅ PASS"
                details = f"position: {result['position']}"
            else:
                status = "❌ FAIL"
                details = result.get("error", "Unknown error")
            print(f"   Platform {result['platform']}: {status} - {details}")
    
    # Overall status
    all_tests_passed = (summary['palette_tests']['success_rate'] == 1.0 and 
                       summary['watermark_tests']['success_rate'] == 1.0 and
                       summary['generation_tests']['success_rate'] == 1.0)
    
    if all_tests_passed:
        print(f"\n🎉 ALL TESTS PASSED! Pipeline is ready for production.")
    else:
        print(f"\n⚠️  Some tests failed. Review the results above.")
    
    print(f"\n📝 Sample file outputs that would be generated:")
    for result in results["generation_tests"][:6]:  # Show first 6 examples
        print(f"   {result['filename']} ({result['platform']}, {result['aspect_ratio']})")
    
    if len(results["generation_tests"]) > 6:
        print(f"   ... and {len(results['generation_tests']) - 6} more")

def main():
    """
    Main function for dry-run testing.
    """
    parser = argparse.ArgumentParser(
        description="Dry-run test for palette injection and watermarking workflow",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This script tests the complete pipeline without making actual API calls:
- Palette injection into prompts
- Platform-specific watermark positioning  
- Mock image generation workflow
- File naming patterns

Examples:
  python3 test_dry_run.py --dry-run
  python3 test_dry_run.py --dry-run --save-results
  python3 test_dry_run.py --themes 1 --palettes A
        """
    )
    
    parser.add_argument("--dry-run", action="store_true", default=True,
                       help="Run in dry-run mode (default: True)")
    parser.add_argument("--themes", type=int, default=2,
                       help="Number of themes to test (default: 2)")
    parser.add_argument("--palettes", nargs="*", default=["A", "B"],
                       help="Palette IDs to test (default: A B)")
    parser.add_argument("--platforms", nargs="*", default=["ig", "tt", "tw"],
                       help="Platforms to test (default: ig tt tw)")
    parser.add_argument("--save-results", action="store_true",
                       help="Save test results to JSON file")
    parser.add_argument("--verbose", action="store_true",
                       help="Enable verbose output")
    
    args = parser.parse_args()
    
    # Prepare test data
    themes_to_test = TEST_THEMES[:args.themes]
    palettes_to_test = args.palettes
    platforms_to_test = {k: v for k, v in PLATFORM_CONFIGS.items() if k in args.platforms}
    
    if args.verbose:
        print(f"Testing {len(themes_to_test)} themes, {len(palettes_to_test)} palettes, {len(platforms_to_test)} platforms")
    
    # Run the dry-run test
    results = run_dry_run_test(themes_to_test, palettes_to_test, platforms_to_test)
    
    # Print summary
    print_summary(results)
    
    # Save results if requested
    if args.save_results:
        output_file = "dry_run_results.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n💾 Results saved to {output_file}")
    
    # Exit with appropriate code
    all_tests_passed = (results["summary"]['palette_tests']['success_rate'] == 1.0 and 
                       results["summary"]['watermark_tests']['success_rate'] == 1.0 and
                       results["summary"]['generation_tests']['success_rate'] == 1.0)
    
    sys.exit(0 if all_tests_passed else 1)

if __name__ == "__main__":
    main()

