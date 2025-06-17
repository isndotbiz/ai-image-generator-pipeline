#!/usr/bin/env python3
"""
Image Curator for Video Queue
Scans images directory, applies quality heuristics, and copies qualifying files 
to video_queue with draft naming convention.
"""

import os
import shutil
import random
from pathlib import Path
from PIL import Image
import json
from datetime import datetime
import re

class ImageCurator:
    def __init__(self, base_dir=".", images_dir="images", video_queue_dir="video_queue"):
        self.base_dir = Path(base_dir)
        self.images_dir = self.base_dir / images_dir
        self.video_queue_dir = self.base_dir / video_queue_dir
        
        # Create video_queue directory if it doesn't exist
        self.video_queue_dir.mkdir(exist_ok=True)
        
        # Supported image extensions
        self.image_extensions = ('.png', '.jpg', '.jpeg')
        
        # Platform suffixes
        self.platform_suffixes = ['_ig', '_tt', '_tw']
        
        # Minimum resolution requirement
        self.min_resolution = 1024
        
        # Acceptable aspect ratios (with tolerance)
        self.acceptable_ratios = {
            '16:9': 16/9,
            '9:16': 9/16,
            '1:1': 1.0
        }
        self.ratio_tolerance = 0.1  # 10% tolerance
        
    def scan_images_recursively(self):
        """Recursively scan images directory for supported image files"""
        found_images = []
        
        if not self.images_dir.exists():
            print(f"Images directory {self.images_dir} does not exist!")
            return found_images
            
        print(f"Scanning {self.images_dir} recursively for images...")
        
        for ext in self.image_extensions:
            # Use glob with ** for recursive search
            pattern = f"**/*{ext}"
            found_images.extend(self.images_dir.glob(pattern))
            # Also search for uppercase extensions
            pattern = f"**/*{ext.upper()}"
            found_images.extend(self.images_dir.glob(pattern))
            
        print(f"Found {len(found_images)} image files")
        return found_images
    
    def check_image_quality(self, image_path):
        """Apply quality heuristics to determine if image should be included"""
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                
                # Check minimum resolution
                if width < self.min_resolution and height < self.min_resolution:
                    return False, f"Resolution too low: {width}x{height} (need ≥{self.min_resolution}px)"
                
                # Check aspect ratio
                aspect_ratio = width / height
                ratio_match = False
                
                for ratio_name, target_ratio in self.acceptable_ratios.items():
                    if abs(aspect_ratio - target_ratio) <= self.ratio_tolerance:
                        ratio_match = True
                        break
                
                if not ratio_match:
                    return False, f"Aspect ratio {aspect_ratio:.2f} doesn't match 16:9, 9:16, or 1:1"
                
                return True, f"Quality check passed: {width}x{height}, ratio: {aspect_ratio:.2f}"
                
        except Exception as e:
            return False, f"Error reading image: {e}"
    
    def extract_descriptors_from_filename(self, filename):
        """Extract descriptive tokens from filename"""
        # Remove extension and common prefixes/suffixes
        name = Path(filename).stem
        
        # Remove common patterns
        patterns_to_remove = [
            r'_watermarked?',
            r'_draft',
            r'_\d{8}_\d{6}',  # timestamp patterns
            r'_\d+',  # numbers at end
            r'^(custom|direct|generated?)_',  # common prefixes
            r'_(ig|tt|tw|li)$'  # platform suffixes
        ]
        
        for pattern in patterns_to_remove:
            name = re.sub(pattern, '', name, flags=re.IGNORECASE)
        
        # Split on common separators and filter
        tokens = re.split(r'[_\s-]+', name)
        
        # Filter out short tokens, numbers, and common words
        descriptors = []
        stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        
        for token in tokens:
            token = token.strip().lower()
            if (len(token) >= 3 and 
                not token.isdigit() and 
                token not in stop_words and
                token.isalpha()):
                descriptors.append(token)
        
        # Take up to 5 descriptors, pad with generic terms if needed
        if len(descriptors) < 3:
            generic_terms = ['image', 'visual', 'content', 'media', 'asset']
            descriptors.extend(generic_terms[:3 - len(descriptors)])
        
        return descriptors[:3]  # Return exactly 3 descriptors
    
    def generate_draft_filename(self, original_path):
        """Generate draft filename with descriptors and platform suffix"""
        descriptors = self.extract_descriptors_from_filename(original_path.name)
        platform_suffix = random.choice(self.platform_suffixes)
        extension = original_path.suffix.lower()
        
        # Join descriptors with underscores
        base_name = '_'.join(descriptors)
        draft_filename = f"{base_name}{platform_suffix}_draft{extension}"
        
        return draft_filename
    
    def copy_to_video_queue(self, source_path, draft_filename):
        """Copy file to video_queue with new filename"""
        destination_path = self.video_queue_dir / draft_filename
        
        # Handle filename conflicts
        counter = 1
        original_draft_filename = draft_filename
        while destination_path.exists():
            name_part = Path(original_draft_filename).stem
            extension = Path(original_draft_filename).suffix
            draft_filename = f"{name_part}_{counter:02d}{extension}"
            destination_path = self.video_queue_dir / draft_filename
            counter += 1
        
        try:
            shutil.copy2(source_path, destination_path)
            return True, str(destination_path)
        except Exception as e:
            return False, f"Error copying file: {e}"
    
    def curate_images(self):
        """Main curation process"""
        print("🎯 Starting Image Curation for Video Queue...")
        
        # Scan for images
        image_files = self.scan_images_recursively()
        
        if not image_files:
            print("No images found to process.")
            return []
        
        results = []
        approved_count = 0
        rejected_count = 0
        
        print(f"\n🔍 Processing {len(image_files)} images...")
        
        for image_path in image_files:
            print(f"\nProcessing: {image_path.name}")
            
            # Check quality
            quality_ok, quality_reason = self.check_image_quality(image_path)
            
            result = {
                'original_path': str(image_path),
                'filename': image_path.name,
                'quality_passed': quality_ok,
                'quality_reason': quality_reason,
                'draft_filename': None,
                'copied_to': None,
                'status': 'rejected',
                'timestamp': datetime.now().isoformat()
            }
            
            if quality_ok:
                # Generate draft filename
                draft_filename = self.generate_draft_filename(image_path)
                result['draft_filename'] = draft_filename
                
                # Copy to video queue
                copy_ok, copy_result = self.copy_to_video_queue(image_path, draft_filename)
                
                if copy_ok:
                    result['copied_to'] = copy_result
                    result['status'] = 'approved'
                    approved_count += 1
                    print(f"✅ APPROVED: {image_path.name} → {draft_filename}")
                    print(f"   Reason: {quality_reason}")
                else:
                    result['quality_reason'] = copy_result
                    rejected_count += 1
                    print(f"❌ COPY FAILED: {image_path.name} - {copy_result}")
            else:
                rejected_count += 1
                print(f"❌ REJECTED: {image_path.name}")
                print(f"   Reason: {quality_reason}")
            
            results.append(result)
        
        # Save curation report
        report_file = self.base_dir / f"curation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Summary
        print(f"\n📊 CURATION COMPLETE:")
        print(f"✅ Approved and copied: {approved_count}")
        print(f"❌ Rejected: {rejected_count}")
        print(f"📄 Report saved: {report_file}")
        print(f"📁 Files copied to: {self.video_queue_dir}")
        
        return results
    
    def list_video_queue(self):
        """List current contents of video_queue"""
        if not self.video_queue_dir.exists():
            print("Video queue directory doesn't exist yet.")
            return []
        
        queue_files = []
        for ext in self.image_extensions:
            queue_files.extend(self.video_queue_dir.glob(f"*{ext}"))
            queue_files.extend(self.video_queue_dir.glob(f"*{ext.upper()}"))
        
        print(f"\n📁 Current Video Queue Contents ({len(queue_files)} files):")
        for file_path in sorted(queue_files):
            file_size = os.path.getsize(file_path)
            print(f"  • {file_path.name} ({file_size:,} bytes)")
        
        return queue_files

def main():
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        print("🎬 Image Curator for Video Queue")
        print("=" * 50)
        print("")
        print("This script:")
        print("")
        print("1. Recursively scans the 'images/' directory for .png, .jpg, .jpeg files")
        print("2. Applies quality heuristics:")
        print("   - Resolution ≥ 1024px (width or height)")
        print("   - Aspect ratio matches 16:9, 9:16, or 1:1 (±10% tolerance)")
        print("3. Copies qualifying files to 'video_queue/' with draft naming:")
        print("   - Format: descriptor1_descriptor2_descriptor3_PLATFORM_draft.ext")
        print("   - Platforms: _ig (Instagram), _tt (TikTok), _tw (Twitter)")
        print("   - Example: rolex_oyster_gold_ig_draft.png")
        print("")
        print("Usage: python3 image_curator.py [--help]")
        print("")
        return
    
    curator = ImageCurator()
    
    print("🎬 Image Curator for Video Queue")
    print("=" * 50)
    
    # Show current video queue
    curator.list_video_queue()
    
    # Run curation process
    results = curator.curate_images()
    
    # Show final video queue
    print("\n" + "=" * 50)
    curator.list_video_queue()
    
    # Summary stats
    if results:
        approved = [r for r in results if r['status'] == 'approved']
        rejected = [r for r in results if r['status'] == 'rejected']
        
        print("\n📈 SUMMARY STATISTICS:")
        print(f"Total files processed: {len(results)}")
        print(f"Approved rate: {len(approved)/len(results)*100:.1f}%")
        
        # Rejection reasons
        rejection_reasons = {}
        for r in rejected:
            reason = r['quality_reason'].split(':')[0] if ':' in r['quality_reason'] else r['quality_reason']
            rejection_reasons[reason] = rejection_reasons.get(reason, 0) + 1
        
        if rejection_reasons:
            print("\n❌ Rejection reasons:")
            for reason, count in sorted(rejection_reasons.items(), key=lambda x: x[1], reverse=True):
                print(f"   • {reason}: {count} files")
        
        # Platform distribution
        platform_dist = {'_ig': 0, '_tt': 0, '_tw': 0}
        for r in approved:
            if r['draft_filename']:
                for platform in platform_dist.keys():
                    if platform in r['draft_filename']:
                        platform_dist[platform] += 1
                        break
        
        print("\n🎯 Platform distribution:")
        for platform, count in platform_dist.items():
            platform_name = {'_ig': 'Instagram', '_tt': 'TikTok', '_tw': 'Twitter'}[platform]
            print(f"   • {platform_name}: {count} files")

if __name__ == "__main__":
    main()

