#!/usr/bin/env python3
"""
Robust Output System for Fortuna Bound

Eliminates echo usage and implements descriptive filename generation.
Prevents workflow hanging and ensures autonomous operation.
"""

import os
import sys
import time
from datetime import datetime
from typing import List, Dict, Optional
import re
import random
from logging_config import get_logger

# RobustLogger class replaced with centralized logging
# Using get_logger from logging_config module for consistency

class DescriptiveFilenameGenerator:
    """Generate descriptive filenames with 3 descriptors + timestamp + platform"""
    
    def __init__(self):
        # Descriptor categories for rich filename generation
        self.descriptors = {
            "style": [
                "elegant", "luxury", "modern", "sophisticated", "premium", "refined",
                "professional", "stylish", "chic", "contemporary", "classic", "exclusive",
                "artistic", "minimal", "vibrant", "serene", "dynamic", "timeless"
            ],
            "subject": [
                "woman", "business", "lifestyle", "portrait", "executive", "entrepreneur",
                "professional", "model", "person", "individual", "leader", "innovator",
                "visionary", "achiever", "success", "luxury", "wellness", "mindfulness"
            ],
            "setting": [
                "cityscape", "office", "rooftop", "penthouse", "studio", "workspace",
                "urban", "metropolitan", "downtown", "skyline", "interior", "restaurant",
                "lounge", "terrace", "boardroom", "retreat", "spa", "garden"
            ],
            "mood": [
                "confident", "inspiring", "powerful", "calm", "focused", "determined",
                "serene", "ambitious", "successful", "peaceful", "energetic", "balanced",
                "motivated", "accomplished", "prosperous", "mindful", "centered", "driven"
            ],
            "quality": [
                "cinematic", "professional", "premium", "highend", "artistic", "commercial",
                "editorial", "corporate", "lifestyle", "portrait", "fashion", "luxury",
                "wellness", "business", "executive", "inspirational", "motivational", "aspirational"
            ]
        }
    
    def extract_descriptors_from_prompt(self, prompt: str) -> List[str]:
        """Extract descriptive keywords from the generation prompt"""
        descriptors = []
        prompt_lower = prompt.lower()
        
        # Look for key descriptive words in the prompt
        descriptor_patterns = {
            "elegant": ["elegant", "sophisticated", "refined"],
            "luxury": ["luxury", "premium", "exclusive", "high-end"],
            "business": ["business", "professional", "corporate", "executive"],
            "woman": ["woman", "female", "lady"],
            "cityscape": ["city", "urban", "skyline", "metropolitan"],
            "confident": ["confident", "powerful", "strong"],
            "serene": ["serene", "peaceful", "calm", "tranquil"],
            "modern": ["modern", "contemporary", "sleek"],
            "lifestyle": ["lifestyle", "living", "experience"],
            "office": ["office", "workspace", "boardroom"],
            "rooftop": ["rooftop", "terrace", "penthouse"],
            "wellness": ["wellness", "spa", "meditation", "yoga"],
            "success": ["success", "achievement", "winning"],
            "inspiring": ["inspiring", "motivational", "uplifting"]
        }
        
        for descriptor, patterns in descriptor_patterns.items():
            if any(pattern in prompt_lower for pattern in patterns):
                descriptors.append(descriptor)
        
        return descriptors[:3]  # Return max 3 descriptors
    
    def generate_random_descriptors(self, count: int = 3) -> List[str]:
        """Generate random descriptors when prompt analysis doesn't yield enough"""
        # Pick one from each category for variety
        categories = ["style", "subject", "setting"]
        descriptors = []
        
        for i, category in enumerate(categories[:count]):
            if category in self.descriptors:
                descriptor = random.choice(self.descriptors[category])
                descriptors.append(descriptor)
        
        return descriptors
    
    def generate_filename(self, prompt: str = "", platform: str = "ig", 
                         base_descriptors: Optional[List[str]] = None) -> str:
        """Generate descriptive filename: descriptor1_descriptor2_descriptor3_timestamp_platform.png"""
        
        # Extract or use provided descriptors
        if base_descriptors:
            descriptors = base_descriptors[:3]
        else:
            descriptors = self.extract_descriptors_from_prompt(prompt)
        
        # Fill missing descriptors with random ones
        while len(descriptors) < 3:
            random_descriptors = self.generate_random_descriptors(3 - len(descriptors))
            descriptors.extend(random_descriptors)
        
        # Ensure we have exactly 3 descriptors
        descriptors = descriptors[:3]
        
        # Clean descriptors (remove spaces, special chars)
        clean_descriptors = []
        for desc in descriptors:
            clean_desc = re.sub(r'[^a-zA-Z0-9]', '', desc.lower())
            clean_descriptors.append(clean_desc)
        
        # Generate timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Combine into filename
        filename = f"{clean_descriptors[0]}_{clean_descriptors[1]}_{clean_descriptors[2]}_{timestamp}_{platform}.png"
        
        return filename
    
    def generate_video_filename(self, descriptors: List[str], video_type: str = "slideshow") -> str:
        """Generate descriptive video filename"""
        clean_descriptors = []
        for desc in descriptors[:3]:
            clean_desc = re.sub(r'[^a-zA-Z0-9]', '', desc.lower())
            clean_descriptors.append(clean_desc)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{clean_descriptors[0]}_{clean_descriptors[1]}_{clean_descriptors[2]}_{video_type}_{timestamp}.mp4"
        
        return filename
    
    def generate_video_filename_stub(self, image_path: str, platform: str = "ig") -> str:
        """Generate video filename stub for Step 6: descriptor1_descriptor2_descriptor3{platform_suffix}_{YYYYMMDD_HHMMSS}
        
        This is the core Step 6 implementation that generates filenames like:
        rolex_oyster_gold_ig_20250617_153012
        
        Args:
            image_path: Path to the image file to derive descriptors from
            platform: Platform suffix (ig, fb, tw, etc.)
        
        Returns:
            Filename stub without .mp4 extension (will be added after download)
        """
        descriptors = self._extract_descriptors_from_image_path(image_path)
        
        # Ensure exactly 3 descriptors, each ≤15 characters, lowercase, snake_case
        clean_descriptors = []
        for desc in descriptors:
            # Convert to lowercase, replace spaces/hyphens with underscores
            clean_desc = desc.lower().replace(' ', '_').replace('-', '_')
            # Remove any non-alphanumeric characters except underscores
            clean_desc = re.sub(r'[^a-z0-9_]', '', clean_desc)
            # Truncate to 15 characters max
            clean_desc = clean_desc[:15]
            # Remove trailing underscores
            clean_desc = clean_desc.rstrip('_')
            clean_descriptors.append(clean_desc)
        
        # Ensure we have exactly 3 descriptors
        while len(clean_descriptors) < 3:
            clean_descriptors.append(self._get_fallback_descriptor(len(clean_descriptors)))
        clean_descriptors = clean_descriptors[:3]
        
        # Generate timestamp in YYYYMMDD_HHMMSS format
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        
        # Map platform to suffix
        platform_suffix = self._get_platform_suffix(platform)
        
        # Generate filename stub: descriptor1_descriptor2_descriptor3{platform_suffix}_{timestamp}
        filename_stub = f"{clean_descriptors[0]}_{clean_descriptors[1]}_{clean_descriptors[2]}{platform_suffix}_{timestamp}"
        
        return filename_stub
    
    def _extract_descriptors_from_image_path(self, image_path: str) -> List[str]:
        """Extract descriptors from image filename and path"""
        descriptors = []
        
        # Get filename without extension
        filename = os.path.splitext(os.path.basename(image_path))[0]
        
        # Look for common patterns in filename
        filename_lower = filename.lower()
        
        # Common luxury/business descriptor patterns
        descriptor_keywords = {
            'luxury': ['luxury', 'premium', 'exclusive', 'elegant', 'sophisticated'],
            'business': ['business', 'professional', 'corporate', 'executive', 'office'],
            'woman': ['woman', 'female', 'lady', 'professional'],
            'rolex': ['rolex', 'watch', 'timepiece'],
            'oyster': ['oyster', 'bracelet', 'band'],
            'gold': ['gold', 'golden', 'yellow'],
            'city': ['city', 'urban', 'skyline', 'metropolitan'],
            'office': ['office', 'workspace', 'boardroom'],
            'wellness': ['wellness', 'spa', 'meditation', 'mindful'],
            'success': ['success', 'achievement', 'winning', 'confident'],
            'lifestyle': ['lifestyle', 'living', 'experience'],
            'modern': ['modern', 'contemporary', 'sleek'],
            'portrait': ['portrait', 'headshot', 'professional']
        }
        
        # Extract descriptors based on filename content
        for key, patterns in descriptor_keywords.items():
            if any(pattern in filename_lower for pattern in patterns):
                descriptors.append(key)
                if len(descriptors) >= 3:
                    break
        
        # If filename doesn't yield enough descriptors, look for timestamp patterns
        # and use generic descriptors
        if len(descriptors) < 3:
            # Add default descriptors based on common themes
            default_descriptors = ['elegant', 'professional', 'lifestyle']
            for desc in default_descriptors:
                if desc not in descriptors:
                    descriptors.append(desc)
                    if len(descriptors) >= 3:
                        break
        
        return descriptors[:3]
    
    def _get_fallback_descriptor(self, index: int) -> str:
        """Get fallback descriptor for missing slots"""
        fallbacks = ['elegant', 'modern', 'premium']
        return fallbacks[index] if index < len(fallbacks) else 'quality'
    
    def _get_platform_suffix(self, platform: str) -> str:
        """Get platform suffix for filename"""
        platform_map = {
            'ig': '_ig',
            'instagram': '_ig', 
            'fb': '_fb',
            'facebook': '_fb',
            'tw': '_tw',
            'twitter': '_tw',
            'tt': '_tt',
            'tiktok': '_tt',
            'yt': '_yt',
            'youtube': '_yt'
        }
        return platform_map.get(platform.lower(), '_ig')  # Default to Instagram

class NonBlockingWorkflow:
    """Workflow manager that never hangs or blocks"""
    
    def __init__(self):
        self.logger = get_logger(__name__ + ".NonBlockingWorkflow")
        self.filename_gen = DescriptiveFilenameGenerator()
        self.timeout_default = 300  # 5 minutes default timeout
    
    def safe_execute(self, func, *args, timeout=None, **kwargs):
        """Execute function safely with timeout and error handling"""
        timeout = timeout or self.timeout_default
        
        try:
            # Simple timeout approach using time checks
            start_time = time.time()
            result = func(*args, **kwargs)
            
            # Check if we exceeded timeout (basic check)
            if time.time() - start_time > timeout:
                self.logger.warning(f"Function {func.__name__} took longer than {timeout}s")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Function {func.__name__} failed: {str(e)}")
            return None
    
    def batch_process_with_recovery(self, items: List, process_func, max_retries: int = 3):
        """Process items in batch with automatic recovery"""
        results = []
        failed_items = []
        
        for i, item in enumerate(items):
            self.logger.info(f"Processing item {i+1}/{len(items)}")
            
            success = False
            for attempt in range(max_retries):
                try:
                    result = self.safe_execute(process_func, item)
                    if result:
                        results.append(result)
                        success = True
                        break
                    else:
                        self.logger.warning(f"Attempt {attempt+1} failed for item {i+1}")
                        time.sleep(2)  # Brief pause between retries
                        
                except Exception as e:
                    self.logger.error(f"Attempt {attempt+1} error for item {i+1}: {str(e)}")
                    time.sleep(2)
            
            if not success:
                failed_items.append(item)
                self.logger.error(f"Failed to process item {i+1} after {max_retries} attempts")
        
        return {
            'successful': results,
            'failed': failed_items,
            'success_rate': len(results) / len(items) * 100 if items else 0
        }

# Global instances for easy import  
logger = get_logger(__name__)
filename_generator = DescriptiveFilenameGenerator()
workflow_manager = NonBlockingWorkflow()

def log_safe(message: str, level: str = "INFO"):
    """Safe logging function that never hangs"""
    if level.upper() == "ERROR":
        logger.error(message)
    elif level.upper() == "WARNING" or level.upper() == "WARN":
        logger.warning(message)
    else:
        logger.info(message)

def generate_descriptive_filename(prompt: str = "", platform: str = "ig", 
                                 descriptors: Optional[List[str]] = None) -> str:
    """Generate descriptive filename safely"""
    return filename_generator.generate_filename(prompt, platform, descriptors)

if __name__ == "__main__":
    # Test the system
    logger.info("Testing robust output system")
    
    # Test filename generation
    test_prompt = "elegant woman in luxury penthouse overlooking city skyline"
    filename = generate_descriptive_filename(test_prompt, "ig")
    logger.info(f"Generated filename: {filename}")
    
    # Test with descriptors
    custom_descriptors = ["sophisticated", "business", "rooftop"]
    filename2 = generate_descriptive_filename("", "tt", custom_descriptors)
    logger.info(f"Generated filename with descriptors: {filename2}")
    
    logger.info("Robust output system test completed")

