#!/usr/bin/env python3
"""
Pipeline Integration for Automatic Watermarking

This module integrates watermarking into the image generation pipeline,
ensuring all generated images are automatically watermarked and non-watermarked
versions are cleaned up.

Usage:
    # Integration with existing generation scripts
    from pipeline_integration import AutoWatermarkPipeline
    
    pipeline = AutoWatermarkPipeline()
    
    # Method 1: Wrap existing generation function
    @pipeline.auto_watermark
    def generate_image(prompt, output_path):
        # Your existing image generation code
        return output_path
    
    # Method 2: Direct integration
    image_path = generate_some_image()
    watermarked_path = pipeline.process_generated_image(image_path)
"""

import os
import functools
from pathlib import Path
from typing import Optional, Callable, Any
from auto_watermark_workflow import WatermarkWorkflow

class AutoWatermarkPipeline:
    """Automatic watermarking integration for image generation pipeline"""
    
    def __init__(self, watermark_path="Fortuna_Bound_Watermark.png",
                 auto_cleanup=True, auto_sync=True):
        self.workflow = WatermarkWorkflow(watermark_path)
        self.auto_cleanup = auto_cleanup
        self.auto_sync = auto_sync
        
    def process_generated_image(self, image_path: str) -> str:
        """Process a newly generated image with watermarking and cleanup"""
        try:
            # Apply watermark
            watermarked_path = self.workflow.watermark_new_images()
            
            if watermarked_path:
                # Clean up original if auto_cleanup is enabled
                if self.auto_cleanup:
                    self.workflow.cleanup_non_watermarked()
                
                # Sync to git if auto_sync is enabled
                if self.auto_sync:
                    self.workflow.sync_and_cleanup_remote()
                
                return watermarked_path[0] if watermarked_path else image_path
            
            return image_path
            
        except Exception as e:
            self.workflow.log(f"Error processing {image_path}: {e}", "ERROR")
            return image_path
    
    def auto_watermark(self, func: Callable) -> Callable:
        """Decorator to automatically watermark function outputs"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Call original function
            result = func(*args, **kwargs)
            
            # Process result if it's an image path
            if isinstance(result, (str, Path)):
                result_path = str(result)
                if any(result_path.endswith(ext) for ext in ['.png', '.jpg', '.jpeg']):
                    # Check if this is in the images directory
                    if 'images/' in result_path or result_path.startswith('images'):
                        watermarked_result = self.process_generated_image(result_path)
                        return watermarked_result
            
            return result
        
        return wrapper
    
    def batch_process(self, image_paths: list) -> list:
        """Process multiple generated images"""
        processed_paths = []
        
        for image_path in image_paths:
            processed_path = self.process_generated_image(image_path)
            processed_paths.append(processed_path)
        
        return processed_paths

# Global pipeline instance for easy import
default_pipeline = AutoWatermarkPipeline()

# Convenience functions
def auto_watermark(func: Callable) -> Callable:
    """Convenience decorator using default pipeline"""
    return default_pipeline.auto_watermark(func)

def process_image(image_path: str) -> str:
    """Convenience function to process a single image"""
    return default_pipeline.process_generated_image(image_path)

def batch_process(image_paths: list) -> list:
    """Convenience function to process multiple images"""
    return default_pipeline.batch_process(image_paths)

