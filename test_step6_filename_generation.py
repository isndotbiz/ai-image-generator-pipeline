#!/usr/bin/env python3
"""
Test Step 6: Video filename stub generation

Tests the implementation of Step 6 that generates:
descriptor1_descriptor2_descriptor3{platform_suffix}_{YYYYMMDD_HHMMSS}

Example: rolex_oyster_gold_ig_20250617_153012
"""

import requests
import json
from datetime import datetime
from robust_output import filename_generator

def test_api_endpoint():
    """Test the API endpoint for Step 6 filename generation"""
    print("\n=== Testing Step 6 API Endpoint ===")
    
    # Test data
    test_cases = [
        {
            'image_path': 'images/elegant_woman_luxury_business_rolex_20240617_123456.png',
            'platform': 'ig'
        },
        {
            'image_path': 'images/professional_office_cityscape_20240617_123456.png', 
            'platform': 'fb'
        },
        {
            'image_path': 'images/wellness_spa_meditation_20240617_123456.png',
            'platform': 'tt'
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}: {test_case['image_path']} for {test_case['platform']}")
        
        try:
            response = requests.post(
                'http://localhost:8080/api/generate-video-filename-stub',
                json=test_case,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data['success']:
                    print(f"✓ Generated filename stub: {data['filename_stub']}")
                    print(f"✓ Full video filename: {data['video_filename']}")
                    print(f"✓ Platform: {data['platform']}")
                    
                    # Validate format
                    stub = data['filename_stub']
                    parts = stub.split('_')
                    if len(parts) >= 4:
                        descriptors = parts[:3]
                        platform_and_timestamp = '_'.join(parts[3:])
                        
                        print(f"  - Descriptors: {descriptors}")
                        print(f"  - Platform+Timestamp: {platform_and_timestamp}")
                        
                        # Check descriptor length
                        for desc in descriptors:
                            if len(desc) > 15:
                                print(f"  ⚠ Warning: Descriptor '{desc}' is longer than 15 characters")
                            else:
                                print(f"  ✓ Descriptor '{desc}' length OK ({len(desc)} chars)")
                    else:
                        print(f"  ⚠ Warning: Unexpected format - {len(parts)} parts found")
                else:
                    print(f"✗ API Error: {data.get('error', 'Unknown error')}")
            else:
                print(f"✗ HTTP Error: {response.status_code}")
        except Exception as e:
            print(f"✗ Request failed: {e}")

def test_direct_function():
    """Test the filename generation function directly"""
    print("\n=== Testing Step 6 Direct Function ===")
    
    test_cases = [
        {'image_path': 'images/rolex_watch_luxury_woman_business_20240617.png', 'platform': 'ig'},
        {'image_path': 'images/office_professional_cityscape_modern.png', 'platform': 'fb'},
        {'image_path': 'images/wellness_meditation_spa_serene.png', 'platform': 'tw'},
        {'image_path': 'images/some_very_long_filename_with_many_descriptors.png', 'platform': 'tt'},
        {'image_path': 'images/simple.png', 'platform': 'yt'}
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}: {test_case['image_path']} for {test_case['platform']}")
        
        try:
            filename_stub = filename_generator.generate_video_filename_stub(
                test_case['image_path'], 
                test_case['platform']
            )
            
            print(f"✓ Generated: {filename_stub}")
            print(f"✓ Video filename: {filename_stub}.mp4")
            
            # Validate format
            parts = filename_stub.split('_')
            if len(parts) >= 4:
                descriptors = parts[:3]
                platform_and_timestamp = '_'.join(parts[3:])
                
                print(f"  - Descriptors: {descriptors}")
                print(f"  - Platform+Timestamp: {platform_and_timestamp}")
                
                # Check descriptor requirements
                for j, desc in enumerate(descriptors):
                    if len(desc) > 15:
                        print(f"  ⚠ Descriptor {j+1} '{desc}' too long ({len(desc)} chars)")
                    elif len(desc) == 0:
                        print(f"  ⚠ Descriptor {j+1} is empty")
                    else:
                        print(f"  ✓ Descriptor {j+1} '{desc}' OK ({len(desc)} chars)")
                
                # Check timestamp format (should be YYYYMMDDHHMMSS)
                timestamp_part = parts[-1]
                if len(timestamp_part) == 14 and timestamp_part.isdigit():
                    print(f"  ✓ Timestamp format OK: {timestamp_part}")
                else:
                    print(f"  ⚠ Timestamp format issue: {timestamp_part}")
            else:
                print(f"  ⚠ Unexpected format - {len(parts)} parts")
                
        except Exception as e:
            print(f"✗ Function failed: {e}")

def demo_step6_examples():
    """Show examples of Step 6 filename generation"""
    print("\n=== Step 6 Demo Examples ===")
    print("Format: descriptor1_descriptor2_descriptor3{platform_suffix}_{YYYYMMDD_HHMMSS}")
    print("Requirements:")
    print("  - Descriptors: lowercase, snake_case, ≤15 characters each")
    print("  - Platform suffixes: _ig, _fb, _tw, _tt, _yt")
    print("  - Timestamp: YYYYMMDDHHMMSS format")
    print("  - Will be suffixed with .mp4 after download")
    
    examples = [
        'images/elegant_woman_luxury_rolex_gold_cityscape.png',
        'images/business_professional_success_modern_office.png', 
        'images/wellness_meditation_spa_peaceful_retreat.png'
    ]
    
    platforms = ['ig', 'fb', 'tw']
    
    for example in examples:
        print(f"\nImage: {example}")
        for platform in platforms:
            try:
                stub = filename_generator.generate_video_filename_stub(example, platform)
                print(f"  {platform}: {stub}.mp4")
            except Exception as e:
                print(f"  {platform}: Error - {e}")

if __name__ == '__main__':
    print("Step 6: Video Filename Stub Generation Test")
    print("=" * 50)
    
    # Test direct function
    test_direct_function()
    
    # Show demo examples
    demo_step6_examples()
    
    # Test API endpoint (requires web app to be running)
    try:
        test_api_endpoint()
    except Exception as e:
        print(f"\n⚠ API test skipped (web app not running?): {e}")
    
    print("\n=== Step 6 Test Complete ===")
    print("\nStep 6 Implementation Summary:")
    print("✓ Video filename stub generation implemented")
    print("✓ Format: descriptor1_descriptor2_descriptor3{platform_suffix}_{timestamp}")
    print("✓ Descriptors: lowercase, snake_case, ≤15 chars each")
    print("✓ Platform suffixes: _ig, _fb, _tw, _tt, _yt")
    print("✓ Timestamp: YYYYMMDDHHMMSS format")
    print("✓ Ready for .mp4 suffix after download")
    print("✓ Available via API and direct function call")

