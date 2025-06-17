#!/usr/bin/env python3
"""
Robust Status Checker for Fortuna Bound

Avoids shell quote issues by using Python for output formatting.
"""

import os
import glob
import json
from pathlib import Path
from datetime import datetime

def check_bulk_generation_results():
    """Check and display bulk generation results"""
    
    print("🎉 BULK GENERATION STATUS CHECK")
    print("=" * 40)
    
    # Count generated images
    direct_images = glob.glob("images/direct_20250616_21*.png")
    watermarked_images = [img for img in direct_images if "_watermarked" in img]
    original_images = [img for img in direct_images if "_watermarked" not in img]
    
    print(f"📊 RESULTS:")
    print(f"✅ Total images: {len(direct_images)}")
    print(f"🎨 Watermarked: {len(watermarked_images)}")
    print(f"📷 Originals: {len(original_images)}")
    print(f"📈 Success rate: {len(watermarked_images)/len(original_images)*100:.1f}%" if original_images else "N/A")
    print()
    
    # Check summary file
    summary_files = glob.glob("bulk_generation_summary_*.json")
    if summary_files:
        latest_summary = max(summary_files, key=os.path.getctime)
        print(f"📄 Summary file: {latest_summary}")
        
        try:
            with open(latest_summary, 'r') as f:
                summary = json.load(f)
                
            print(f"⏱️  Duration: {summary.get('duration_minutes', 0):.1f} minutes")
            print(f"📊 Success rate: {summary.get('success_rate', 0):.1f}%")
            
            video_result = summary.get('video', {})
            video_status = "✅" if video_result.get('success') else "❌"
            print(f"🎬 Video: {video_status}")
            
        except Exception as e:
            print(f"❌ Error reading summary: {e}")
    else:
        print("📄 No summary file found")
    
    print()
    
    # Sample of generated files
    if watermarked_images:
        print("📋 SAMPLE FILES:")
        for img in watermarked_images[:5]:
            filename = os.path.basename(img)
            size_mb = os.path.getsize(img) / 1024 / 1024
            print(f"  • {filename} ({size_mb:.1f}MB)")
        
        if len(watermarked_images) > 5:
            print(f"  ... and {len(watermarked_images) - 5} more")
    
    print()
    print("🌐 Web app: http://localhost:8085")
    print("📁 Location: images/ directory")
    print("✨ All images include Fortuna Bound watermark and mantras")

def check_web_app_status():
    """Check if web app is running"""
    import requests
    
    try:
        response = requests.get("http://localhost:8085/api/status", timeout=5)
        if response.status_code == 200:
            print("🌐 Web app: ✅ Running on port 8085")
            return True
        else:
            print(f"🌐 Web app: ❌ Responding with status {response.status_code}")
            return False
    except:
        print("🌐 Web app: ❌ Not responding")
        return False

def main():
    print(f"🕐 Status check at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    check_web_app_status()
    print()
    check_bulk_generation_results()

if __name__ == "__main__":
    main()

