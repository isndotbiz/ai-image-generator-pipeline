#!/usr/bin/env python3
"""
Image Organizer and Quality Filter
Moves images to organized folders and filters out low-quality images
"""

import os
import shutil
from pathlib import Path
import json
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import pytesseract
import re
from datetime import datetime

class ImageOrganizer:
    def __init__(self, base_dir=".", images_dir="images"):
        self.base_dir = Path(base_dir)
        self.images_dir = Path(images_dir)
        self.images_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        self.approved_dir = self.images_dir / "approved"
        self.rejected_dir = self.images_dir / "rejected" 
        self.pending_dir = self.images_dir / "pending"
        
        for dir_path in [self.approved_dir, self.rejected_dir, self.pending_dir]:
            dir_path.mkdir(exist_ok=True)
            
        # Quality filters
        self.text_whitelist = [
            "@FORTUNA_BOUND",
            "Honor the Path to Prosperity",
            "Tribute Now, Thank Yourself Later",
            "Obey the Call of Currency",
            "Surrender to Sovereign Wealth",
            "Pay for Power, Stay Empowered",
            "Invest in My Indulgence",
            "Wealth Follows Devotion",
            "Submit to Success",
            "Your Tribute, My Triumph",
            "Luxury Earns Your Loyalty",
            "Claim Your Throne of Capital",
            "Serve the Yield, Earn the Life",
            "Bow to Balance Sheets",
            "Kneel Before Compounding",
            "Revere Residual Income"
        ]
        
        # Problematic text patterns to reject
        self.reject_patterns = [
            r'[A-Z]{4,}\s+[A-Z]{4,}',  # Random uppercase words
            r'\b\w{1,2}\b\s+\b\w{1,2}\b',  # Short random words
            r'[0-9]{3,}',  # Random numbers
            r'[!@#$%^&*()]{2,}',  # Symbol clusters
            r'\b(lorem|ipsum|dolor|amet)\b',  # Lorem ipsum
            r'\b(asdf|qwer|zxcv)\b',  # Keyboard mashing
        ]
    
    def move_images_to_folder(self):
        """Move all PNG images from base directory to images folder"""
        moved_count = 0
        png_files = list(self.base_dir.glob("*.png"))
        
        print(f"Found {len(png_files)} PNG files to organize...")
        
        for png_file in png_files:
            if png_file.parent == self.images_dir:
                continue  # Skip if already in images folder
                
            destination = self.pending_dir / png_file.name
            try:
                shutil.move(str(png_file), str(destination))
                moved_count += 1
                print(f"Moved: {png_file.name}")
            except Exception as e:
                print(f"Error moving {png_file.name}: {e}")
        
        print(f"Moved {moved_count} images to pending folder")
        return moved_count
    
    def extract_text_from_image(self, image_path):
        """Extract text from image using OCR"""
        try:
            image = cv2.imread(str(image_path))
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Improve OCR accuracy
            gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
            
            # Extract text
            text = pytesseract.image_to_string(gray, config='--psm 6')
            return text.strip()
        except Exception as e:
            print(f"OCR error for {image_path}: {e}")
            return ""
    
    def check_image_quality(self, image_path):
        """Check if image meets quality standards"""
        try:
            # Check file size (too small = low quality)
            file_size = os.path.getsize(image_path)
            if file_size < 50000:  # Less than 50KB
                return False, "File too small"
            
            # Check image dimensions
            with Image.open(image_path) as img:
                width, height = img.size
                if width < 512 or height < 512:
                    return False, "Resolution too low"
            
            # Check for corruption
            img = cv2.imread(str(image_path))
            if img is None:
                return False, "Corrupted image"
            
            # Check if image is mostly black/white (generation error)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
            
            # If 90% of pixels are in extreme ranges, likely a bad generation
            total_pixels = img.shape[0] * img.shape[1]
            dark_pixels = np.sum(hist[:50])
            light_pixels = np.sum(hist[200:])
            
            if (dark_pixels + light_pixels) / total_pixels > 0.9:
                return False, "Image too dark/light"
            
            return True, "Quality check passed"
            
        except Exception as e:
            return False, f"Error checking quality: {e}"
    
    def check_text_quality(self, text):
        """Check if extracted text is acceptable"""
        if not text:
            return True, "No text found"  # No text is acceptable
        
        text_lower = text.lower().strip()
        
        # Check if text contains only whitelisted content
        for allowed_text in self.text_whitelist:
            if allowed_text.lower() in text_lower:
                return True, f"Contains approved text: {allowed_text}"
        
        # Check for problematic patterns
        for pattern in self.reject_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return False, f"Contains problematic text pattern: {pattern}"
        
        # If text is short and alphanumeric, might be hallucinated
        if len(text) < 50 and len(text) > 5:
            words = text.split()
            if len(words) <= 3:
                return False, f"Suspicious short text: {text}"
        
        # If we have significant text that's not whitelisted, flag for review
        if len(text) > 10:
            return False, f"Non-approved text found: {text[:100]}..."
        
        return True, "Text check passed"
    
    def analyze_image(self, image_path):
        """Comprehensive image analysis"""
        results = {
            'filename': image_path.name,
            'quality_passed': False,
            'text_passed': False,
            'overall_status': 'rejected',
            'quality_reason': '',
            'text_reason': '',
            'extracted_text': '',
            'file_size': os.path.getsize(image_path),
            'timestamp': datetime.now().isoformat()
        }
        
        # Check image quality
        quality_ok, quality_reason = self.check_image_quality(image_path)
        results['quality_passed'] = quality_ok
        results['quality_reason'] = quality_reason
        
        if not quality_ok:
            results['overall_status'] = 'rejected'
            return results
        
        # Extract and check text
        extracted_text = self.extract_text_from_image(image_path)
        results['extracted_text'] = extracted_text
        
        text_ok, text_reason = self.check_text_quality(extracted_text)
        results['text_passed'] = text_ok
        results['text_reason'] = text_reason
        
        if quality_ok and text_ok:
            results['overall_status'] = 'approved'
        else:
            results['overall_status'] = 'rejected'
        
        return results
    
    def process_pending_images(self):
        """Process all images in pending folder"""
        pending_images = list(self.pending_dir.glob("*.png"))
        results = []
        
        print(f"Processing {len(pending_images)} pending images...")
        
        for image_path in pending_images:
            print(f"Analyzing: {image_path.name}")
            
            analysis = self.analyze_image(image_path)
            results.append(analysis)
            
            # Move to appropriate folder
            if analysis['overall_status'] == 'approved':
                destination = self.approved_dir / image_path.name
                print(f"✅ APPROVED: {image_path.name}")
            else:
                destination = self.rejected_dir / image_path.name
                print(f"❌ REJECTED: {image_path.name} - {analysis['quality_reason']} | {analysis['text_reason']}")
            
            try:
                shutil.move(str(image_path), str(destination))
            except Exception as e:
                print(f"Error moving {image_path.name}: {e}")
        
        # Save analysis results
        report_file = self.images_dir / f"analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        approved_count = sum(1 for r in results if r['overall_status'] == 'approved')
        rejected_count = len(results) - approved_count
        
        print(f"\n📊 ANALYSIS COMPLETE:")
        print(f"✅ Approved: {approved_count}")
        print(f"❌ Rejected: {rejected_count}")
        print(f"📄 Report saved: {report_file}")
        
        return results
    
    def get_stats(self):
        """Get current statistics"""
        stats = {
            'pending': len(list(self.pending_dir.glob("*.png"))),
            'approved': len(list(self.approved_dir.glob("*.png"))),
            'rejected': len(list(self.rejected_dir.glob("*.png"))),
        }
        stats['total'] = sum(stats.values())
        return stats

def main():
    organizer = ImageOrganizer()
    
    print("🚀 Starting Image Organization and Quality Control...")
    
    # Step 1: Move images from base directory
    moved_count = organizer.move_images_to_folder()
    
    if moved_count > 0:
        print(f"\n📁 Moved {moved_count} images to pending folder")
    
    # Step 2: Process pending images
    if organizer.get_stats()['pending'] > 0:
        print("\n🔍 Starting quality analysis...")
        results = organizer.process_pending_images()
    else:
        print("\n✅ No pending images to process")
    
    # Step 3: Show final stats
    stats = organizer.get_stats()
    print(f"\n📊 FINAL STATISTICS:")
    print(f"Total images: {stats['total']}")
    print(f"✅ Approved: {stats['approved']}")
    print(f"❌ Rejected: {stats['rejected']}")
    print(f"⏳ Pending: {stats['pending']}")

if __name__ == "__main__":
    main()

