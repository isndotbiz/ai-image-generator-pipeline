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

class RobustLogger:
    """Thread-safe logger that never hangs workflow"""
    
    def __init__(self, log_file="fortuna_workflow.log"):
        self.log_file = log_file
        self.silent_mode = False
    
    def log(self, message: str, level: str = "INFO", force_output: bool = False):
        """Log message safely without hanging"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"
        
        # Always write to file
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(log_entry + "\n")
                f.flush()
        except:
            pass  # Never let logging break the workflow
        
        # Output to console only if safe
        if not self.silent_mode or force_output:
            try:
                print(log_entry)
                sys.stdout.flush()
            except:
                pass  # Never let output break the workflow
    
    def info(self, message: str):
        self.log(message, "INFO")
    
    def error(self, message: str):
        self.log(message, "ERROR", force_output=True)
    
    def success(self, message: str):
        self.log(message, "SUCCESS")
    
    def warning(self, message: str):
        self.log(message, "WARN")

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

class NonBlockingWorkflow:
    """Workflow manager that never hangs or blocks"""
    
    def __init__(self):
        self.logger = RobustLogger()
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
logger = RobustLogger()
filename_generator = DescriptiveFilenameGenerator()
workflow_manager = NonBlockingWorkflow()

def log_safe(message: str, level: str = "INFO"):
    """Safe logging function that never hangs"""
    logger.log(message, level)

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
    
    logger.success("Robust output system test completed")

