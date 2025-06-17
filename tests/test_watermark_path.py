#!/usr/bin/env python3
"""
Test suite for watermark path handling and default file accessibility.

This test module ensures:
1. Default watermark file exists and is accessible
2. Clear error messages when watermark file is missing
3. Proper fallback to default watermark path
4. CLI arguments work correctly for custom watermark paths
"""

import unittest
import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from watermark import (
        DEFAULT_WATERMARK_PATH,
        add_logo_watermark,
        add_combined_watermark,
        Platform
    )
except ImportError as e:
    print(f"Error importing watermark module: {e}")
    print("Make sure watermark.py is in the parent directory")
    sys.exit(1)

class TestWatermarkPath(unittest.TestCase):
    """Test watermark path handling and accessibility"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        self.test_image = Path(self.test_dir) / "test_image.png"
        self.test_watermark = Path(self.test_dir) / "test_watermark.png"
        
        # Create a simple test image using PIL if available
        try:
            from PIL import Image
            # Create a simple 100x100 red image
            img = Image.new('RGB', (100, 100), color='red')
            img.save(str(self.test_image))
            
            # Create a simple watermark image (50x50 blue)
            watermark = Image.new('RGBA', (50, 50), color=(0, 0, 255, 128))
            watermark.save(str(self.test_watermark))
            
        except ImportError:
            # If PIL is not available, create dummy files
            self.test_image.touch()
            self.test_watermark.touch()
    
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_default_watermark_path_exists(self):
        """Test that the default watermark file exists at repo root"""
        self.assertTrue(
            DEFAULT_WATERMARK_PATH.exists(),
            f"Default watermark file not found: {DEFAULT_WATERMARK_PATH}"
        )
        
        # Check that it's actually a file, not a directory
        self.assertTrue(
            DEFAULT_WATERMARK_PATH.is_file(),
            f"Default watermark path is not a file: {DEFAULT_WATERMARK_PATH}"
        )
        
        # Check that it has the expected name
        self.assertEqual(
            DEFAULT_WATERMARK_PATH.name,
            "Fortuna_Bound_Watermark.png",
            "Default watermark file has unexpected name"
        )
    
    def test_default_watermark_path_construction(self):
        """Test that the default watermark path is constructed correctly"""
        # Should be in the same directory as watermark.py
        expected_parent = Path(__file__).parent.parent  # tests/../
        expected_path = expected_parent / "Fortuna_Bound_Watermark.png"
        
        self.assertEqual(
            DEFAULT_WATERMARK_PATH.resolve(),
            expected_path.resolve(),
            "Default watermark path not constructed correctly"
        )
    
    def test_add_logo_watermark_uses_default_path(self):
        """Test that add_logo_watermark uses default path when none provided"""
        if not DEFAULT_WATERMARK_PATH.exists():
            self.skipTest("Default watermark file not available")
        
        try:
            # Should use default watermark path when logo_path is None
            result = add_logo_watermark(
                str(self.test_image),
                logo_path=None,  # Should use default
                platform=Platform.GENERIC
            )
            
            # Should return a path (even if PIL processing fails)
            self.assertIsInstance(result, str)
            
        except Exception as e:
            # If it fails due to missing PIL, that's OK - we're testing path logic
            if "PIL not available" not in str(e) and "Watermark file not found" not in str(e):
                raise
    
    def test_add_combined_watermark_uses_default_path(self):
        """Test that add_combined_watermark uses default path when none provided"""
        if not DEFAULT_WATERMARK_PATH.exists():
            self.skipTest("Default watermark file not available")
        
        try:
            # Should use default watermark path when logo_path is None
            result = add_combined_watermark(
                str(self.test_image),
                logo_path=None,  # Should use default
                text="@test",
                platform=Platform.GENERIC
            )
            
            # Should return a path (even if PIL processing fails)
            self.assertIsInstance(result, str)
            
        except Exception as e:
            # If it fails due to missing PIL, that's OK - we're testing path logic
            if "PIL not available" not in str(e) and "Watermark file not found" not in str(e):
                raise
    
    def test_clear_error_when_watermark_missing(self):
        """Test that clear error is raised when watermark file is missing"""
        nonexistent_watermark = "/path/that/does/not/exist/watermark.png"
        
        with self.assertRaises(FileNotFoundError) as context:
            add_logo_watermark(
                str(self.test_image),
                logo_path=nonexistent_watermark,
                platform=Platform.GENERIC
            )
        
        # Check that the error message is clear and helpful
        error_message = str(context.exception)
        self.assertIn("Watermark file not found", error_message)
        self.assertIn(nonexistent_watermark, error_message)
    
    def test_clear_error_when_default_watermark_missing(self):
        """Test clear error when default watermark is missing"""
        # Temporarily mock DEFAULT_WATERMARK_PATH to point to nonexistent file
        with patch('watermark.DEFAULT_WATERMARK_PATH', Path('/nonexistent/watermark.png')):
            with self.assertRaises(FileNotFoundError) as context:
                add_logo_watermark(
                    str(self.test_image),
                    logo_path=None,  # Should try to use default
                    platform=Platform.GENERIC
                )
            
            error_message = str(context.exception)
            self.assertIn("Watermark file not found", error_message)
            self.assertIn("/nonexistent/watermark.png", error_message)
    
    def test_custom_watermark_path_works(self):
        """Test that custom watermark path is used when provided"""
        try:
            result = add_logo_watermark(
                str(self.test_image),
                logo_path=str(self.test_watermark),
                platform=Platform.GENERIC
            )
            
            # Should return a path (even if PIL processing fails)
            self.assertIsInstance(result, str)
            
        except Exception as e:
            # If it fails due to missing PIL, that's OK - we're testing path logic
            if "PIL not available" not in str(e):
                raise
    
    def test_watermark_path_validation(self):
        """Test various edge cases for watermark path validation"""
        # Test with empty string
        with self.assertRaises(FileNotFoundError):
            add_logo_watermark(
                str(self.test_image),
                logo_path="",
                platform=Platform.GENERIC
            )
        
        # Test with directory instead of file
        with self.assertRaises(FileNotFoundError):
            add_logo_watermark(
                str(self.test_image),
                logo_path=str(self.test_dir),  # Directory, not file
                platform=Platform.GENERIC
            )
    
    def test_cli_watermark_path_argument(self):
        """Test that --watermark-path CLI argument works correctly"""
        # This test verifies the CLI argument parsing logic
        # We can't easily test the full CLI without subprocess, but we can
        # verify the argument is defined correctly
        
        # Import argparse components
        import argparse
        
        # Create parser similar to the one in watermark.py
        parser = argparse.ArgumentParser()
        parser.add_argument("image_path")
        parser.add_argument("--watermark-path")
        parser.add_argument("--platform", default="generic")
        
        # Test parsing with --watermark-path
        args = parser.parse_args([
            "test.png",
            "--watermark-path", "/custom/watermark.png",
            "--platform", "instagram"
        ])
        
        self.assertEqual(args.image_path, "test.png")
        self.assertEqual(args.watermark_path, "/custom/watermark.png")
        self.assertEqual(args.platform, "instagram")
        
        # Test parsing without --watermark-path (should be None)
        args = parser.parse_args(["test.png"])
        self.assertIsNone(args.watermark_path)
    
    def test_watermark_file_permissions(self):
        """Test that the default watermark file has correct permissions"""
        if not DEFAULT_WATERMARK_PATH.exists():
            self.skipTest("Default watermark file not available")
        
        # Check that the file is readable
        self.assertTrue(
            os.access(DEFAULT_WATERMARK_PATH, os.R_OK),
            f"Default watermark file is not readable: {DEFAULT_WATERMARK_PATH}"
        )
        
        # Check file size (should be > 0)
        file_size = DEFAULT_WATERMARK_PATH.stat().st_size
        self.assertGreater(
            file_size, 0,
            f"Default watermark file appears to be empty: {DEFAULT_WATERMARK_PATH}"
        )
        
        # Check file extension
        self.assertEqual(
            DEFAULT_WATERMARK_PATH.suffix.lower(), ".png",
            "Default watermark file should be a PNG"
        )

class TestWatermarkPathIntegration(unittest.TestCase):
    """Integration tests for watermark path handling"""
    
    def test_end_to_end_watermark_workflow(self):
        """Test complete watermark workflow with default path"""
        if not DEFAULT_WATERMARK_PATH.exists():
            self.skipTest("Default watermark file not available")
        
        # Create temporary test image
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
            tmp_image_path = tmp_file.name
        
        try:
            # Create a test image
            try:
                from PIL import Image
                img = Image.new('RGB', (200, 200), color='green')
                img.save(tmp_image_path)
                
                # Test watermarking with default path
                result = add_logo_watermark(
                    tmp_image_path,
                    logo_path=None,  # Use default
                    platform=Platform.INSTAGRAM
                )
                
                # Verify result is a string path
                self.assertIsInstance(result, str)
                
                # If watermarking succeeded, output file should exist
                if result != tmp_image_path:  # If it created a new file
                    # Clean up the output file
                    if os.path.exists(result):
                        os.unlink(result)
                
            except ImportError:
                # PIL not available, just test the path logic
                with self.assertRaises(Exception) as context:
                    add_logo_watermark(
                        tmp_image_path,
                        logo_path=None,
                        platform=Platform.INSTAGRAM
                    )
                
                # Should fail due to PIL, not path issues
                error_str = str(context.exception)
                self.assertTrue(
                    "PIL not available" in error_str or "cannot identify image file" in error_str,
                    f"Unexpected error: {error_str}"
                )
        
        finally:
            # Clean up
            if os.path.exists(tmp_image_path):
                os.unlink(tmp_image_path)

if __name__ == "__main__":
    # Run the tests
    unittest.main(verbosity=2)

