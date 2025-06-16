#!/usr/bin/env python3
"""
Smoke tests for the AI image generation pipeline.
This test actually generates an image and verifies the output.
"""

import unittest
import tempfile
import shutil
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generate import generate_and_save


class TestImageGenerationSmoke(unittest.TestCase):
    """Smoke tests for the complete image generation pipeline."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.original_cwd = Path.cwd()
        
    def tearDown(self):
        """Clean up test fixtures."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def test_generate_image_smoke(self):
        """Smoke test: Generate an actual image and verify file output."""
        # Define the test prompt and output filename
        test_prompt = "A simple geometric shape"
        output_filename = "smoke_test_image.png"
        expected_path = Path("images") / output_filename
        
        # Clean up any existing file
        if expected_path.exists():
            expected_path.unlink()
        
        # Generate the image
        result = generate_and_save(test_prompt, output_filename)
        
        # Assert that generation was successful
        self.assertTrue(result, "Image generation should return True on success")
        
        # Assert that the file was created
        self.assertTrue(expected_path.exists(), f"Generated image file should exist at {expected_path}")
        
        # Assert that the file has reasonable size (not empty, not too small)
        file_size = expected_path.stat().st_size
        self.assertGreater(file_size, 1000, "Generated image should be larger than 1KB")
        self.assertLess(file_size, 50_000_000, "Generated image should be smaller than 50MB")
        
        # Clean up
        if expected_path.exists():
            expected_path.unlink()
        
        print(f"✓ Smoke test passed: Generated {output_filename} ({file_size} bytes)")
    
    def test_import_dependencies(self):
        """Test that critical dependencies can be imported without errors."""
        try:
            import torch
            import cv2
            print(f"✓ torch version: {torch.__version__}")
            print(f"✓ opencv version: {cv2.__version__}")
            print(f"✓ CUDA available: {torch.cuda.is_available()}")
        except ImportError as e:
            self.fail(f"Failed to import critical dependencies: {e}")
    
    def test_images_directory_creation(self):
        """Test that the images directory is created if it doesn't exist."""
        # Remove images directory if it exists
        images_dir = Path("images")
        if images_dir.exists():
            temp_backup = Path("images_backup")
            if temp_backup.exists():
                shutil.rmtree(temp_backup)
            images_dir.rename(temp_backup)
        
        try:
            # Generate an image which should create the directory
            result = generate_and_save("Test directory creation", "dir_test.png")
            
            # Assert directory was created
            self.assertTrue(images_dir.exists(), "Images directory should be created")
            self.assertTrue(images_dir.is_dir(), "Images path should be a directory")
            
            # Assert file was created
            test_file = images_dir / "dir_test.png"
            self.assertTrue(test_file.exists(), "Test image should be created")
            
            # Clean up test file
            if test_file.exists():
                test_file.unlink()
                
        finally:
            # Restore original images directory if it existed
            temp_backup = Path("images_backup")
            if temp_backup.exists():
                if images_dir.exists():
                    shutil.rmtree(images_dir)
                temp_backup.rename(images_dir)


if __name__ == '__main__':
    unittest.main(verbosity=2)

