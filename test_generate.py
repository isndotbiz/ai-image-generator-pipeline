#!/usr/bin/env python3
"""
Tests for generate.py functionality.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from generate import generate_and_save, download_image, DEFAULT_IMG_DIR


class TestGenerate(unittest.TestCase):
    """Test cases for generate.py functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.original_cwd = Path.cwd()
        os.chdir(self.test_dir)
        
    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)
    
    @patch('generate.generate_image')
    @patch('generate.download_image')
    def test_generate_and_save_with_filename_only(self, mock_download, mock_generate):
        """Test that filenames without path separators are saved to images/ directory."""
        # Setup mocks
        mock_generate.return_value = "http://example.com/image.png"
        mock_download.return_value = True
        
        # Test with filename only (no path separators)
        result = generate_and_save("test prompt", "test_image.png")
        
        # Verify success
        self.assertTrue(result)
        
        # Verify that generate_image was called
        mock_generate.assert_called_once()
        
        # Verify that download_image was called with the correct path in images/ directory
        expected_path = str(DEFAULT_IMG_DIR / "test_image.png")
        mock_download.assert_called_once_with("http://example.com/image.png", expected_path)
    
    @patch('generate.generate_image')
    @patch('generate.download_image')
    def test_generate_and_save_with_full_path(self, mock_download, mock_generate):
        """Test that full paths are used as-is (not modified)."""
        # Setup mocks
        mock_generate.return_value = "http://example.com/image.png"
        mock_download.return_value = True
        
        # Test with full path
        full_path = "custom/path/test_image.png"
        result = generate_and_save("test prompt", full_path)
        
        # Verify success
        self.assertTrue(result)
        
        # Verify that download_image was called with the original path
        mock_download.assert_called_once_with("http://example.com/image.png", full_path)
    
    @patch('requests.get')
    def test_download_image_creates_parent_dirs(self, mock_get):
        """Test that download_image creates parent directories."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.content = b"fake image data"
        mock_get.return_value = mock_response
        
        # Test downloading to a nested path
        nested_path = self.test_dir / "deep" / "nested" / "path" / "image.png"
        result = download_image("http://example.com/image.png", str(nested_path))
        
        # Verify success
        self.assertTrue(result)
        
        # Verify parent directories were created
        self.assertTrue(nested_path.parent.exists())
        self.assertTrue(nested_path.exists())
        
        # Verify file content
        with open(nested_path, "rb") as f:
            self.assertEqual(f.read(), b"fake image data")
    
    def test_default_img_dir_constant(self):
        """Test that DEFAULT_IMG_DIR is set correctly."""
        self.assertEqual(DEFAULT_IMG_DIR, Path("images"))
    
    def test_path_detection_logic(self):
        """Test the path detection logic for filenames vs full paths."""
        # Test filename only
        path_obj = Path("image.png")
        self.assertEqual(len(path_obj.parts), 1)
        
        # Test relative path
        path_obj = Path("folder/image.png")
        self.assertGreater(len(path_obj.parts), 1)
        
        # Test absolute path
        path_obj = Path("/absolute/path/image.png")
        self.assertGreater(len(path_obj.parts), 1)


if __name__ == '__main__':
    unittest.main()

