#!/usr/bin/env python3
"""
Unit tests for watermark module.
"""

import unittest
import sys
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

# Add current directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from watermark import (
    Platform,
    get_platform_position,
    add_logo_watermark,
    add_text_watermark,
    watermark_for_platform,
    create_branded_image,
    batch_watermark,
    add_metadata
)

class TestWatermark(unittest.TestCase):
    """Test cases for watermark module."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_image_size = (800, 1000)
        self.test_watermark_size = (100, 30)
        # Updated to use consistent path patterns for testing
        self.test_image_path = "images/test_image.png"
        self.test_logo_path = "images/test_logo.png"
    
    def test_platform_enum(self):
        """Test Platform enum values."""
        self.assertEqual(Platform.INSTAGRAM.value, "instagram")
        self.assertEqual(Platform.TIKTOK.value, "tiktok")
        self.assertEqual(Platform.TWITTER.value, "twitter")
        self.assertEqual(Platform.GENERIC.value, "generic")
    
    def test_get_platform_position_instagram(self):
        """Test watermark positioning for Instagram (bottom-right)."""
        position = get_platform_position(
            Platform.INSTAGRAM, 
            self.test_image_size, 
            self.test_watermark_size
        )
        
        # Instagram should be bottom-right
        expected_x = self.test_image_size[0] - self.test_watermark_size[0] - 20  # margin
        expected_y = self.test_image_size[1] - self.test_watermark_size[1] - 20  # margin
        
        self.assertEqual(position, (expected_x, expected_y))
        self.assertEqual(position, (680, 950))
    
    def test_get_platform_position_tiktok(self):
        """Test watermark positioning for TikTok (mid-left)."""
        position = get_platform_position(
            Platform.TIKTOK, 
            self.test_image_size, 
            self.test_watermark_size
        )
        
        # TikTok should be mid-left
        expected_x = 20  # margin
        expected_y = (self.test_image_size[1] - self.test_watermark_size[1]) // 2
        
        self.assertEqual(position, (expected_x, expected_y))
        self.assertEqual(position, (20, 485))
    
    def test_get_platform_position_twitter(self):
        """Test watermark positioning for Twitter (top-right)."""
        position = get_platform_position(
            Platform.TWITTER, 
            self.test_image_size, 
            self.test_watermark_size
        )
        
        # Twitter should be top-right
        expected_x = self.test_image_size[0] - self.test_watermark_size[0] - 20  # margin
        expected_y = 20  # margin
        
        self.assertEqual(position, (expected_x, expected_y))
        self.assertEqual(position, (680, 20))
    
    def test_get_platform_position_generic(self):
        """Test watermark positioning for generic platform (bottom-right)."""
        position = get_platform_position(
            Platform.GENERIC, 
            self.test_image_size, 
            self.test_watermark_size
        )
        
        # Generic should be bottom-right (same as Instagram)
        expected_x = self.test_image_size[0] - self.test_watermark_size[0] - 20
        expected_y = self.test_image_size[1] - self.test_watermark_size[1] - 20
        
        self.assertEqual(position, (expected_x, expected_y))
        self.assertEqual(position, (680, 950))
    
    def test_get_platform_position_dynamic_margin(self):
        """Test that margin scales with image size."""
        # Test with small image
        small_image_size = (200, 200)
        small_watermark_size = (40, 20)
        
        position = get_platform_position(
            Platform.INSTAGRAM,
            small_image_size,
            small_watermark_size
        )
        
        # Margin should be max(20, min(200, 200) // 40) = max(20, 5) = 20
        expected_x = 200 - 40 - 20
        expected_y = 200 - 20 - 20
        self.assertEqual(position, (140, 160))
        
        # Test with very large image
        large_image_size = (4000, 3000)
        position = get_platform_position(
            Platform.INSTAGRAM,
            large_image_size,
            self.test_watermark_size
        )
        
        # Margin should be max(20, min(4000, 3000) // 40) = max(20, 75) = 75
        expected_x = 4000 - 100 - 75
        expected_y = 3000 - 30 - 75
        self.assertEqual(position, (3825, 2895))
    
    def test_get_platform_position_edge_cases(self):
        """Test edge cases for position calculation."""
        # Test when watermark is larger than image
        large_watermark_size = (1000, 1200)
        position = get_platform_position(
            Platform.INSTAGRAM,
            self.test_image_size,
            large_watermark_size
        )
        
        # Should return (0, 0) when position would be negative
        self.assertEqual(position, (0, 0))
    
    @patch('watermark.Image')
    @patch('watermark.ImageEnhance')
    def test_add_logo_watermark_success(self, mock_enhance, mock_image):
        """Test successful logo watermark addition."""
        # Mock PIL Image objects
        mock_base_img = MagicMock()
        mock_base_img.size = self.test_image_size
        mock_base_img.mode = 'RGBA'
        mock_base_img.copy.return_value = mock_base_img
        
        mock_logo = MagicMock()
        mock_logo.size = (200, 100)
        mock_logo.resize.return_value = mock_logo
        mock_logo.split.return_value = [None, None, None, MagicMock()]  # RGBA channels
        
        mock_image.open.side_effect = [mock_base_img, mock_logo]
        mock_image.new.return_value = MagicMock()
        
        # Mock enhancer
        mock_enhancer = MagicMock()
        mock_enhance.Brightness.return_value = mock_enhancer
        
        result = add_logo_watermark(
            self.test_image_path,
            self.test_logo_path,
            Platform.INSTAGRAM
        )
        
        # Should return the expected output path
        expected_output = self.test_image_path.replace('.png', '_watermarked.png')
        self.assertEqual(result, expected_output)
        
        # Verify logo was resized
        mock_logo.resize.assert_called_once()
        
        # Verify image was saved
        mock_base_img.save.assert_called_once()
    
    @patch('watermark.Image')
    def test_add_logo_watermark_import_error(self, mock_image):
        """Test logo watermark when PIL is not available."""
        # Simulate ImportError
        with patch('watermark.Image', side_effect=ImportError()):
            result = add_logo_watermark(
                self.test_image_path,
                self.test_logo_path
            )
            
            # Should return original path when PIL is not available
            self.assertEqual(result, self.test_image_path)
    
    @patch('watermark.Image')
    @patch('watermark.ImageDraw')
    @patch('watermark.ImageFont')
    def test_add_text_watermark_success(self, mock_font, mock_draw, mock_image):
        """Test successful text watermark addition."""
        # Mock PIL objects
        mock_img = MagicMock()
        mock_img.size = self.test_image_size
        mock_img.mode = 'RGBA'
        
        mock_overlay = MagicMock()
        mock_draw_obj = MagicMock()
        mock_draw_obj.textbbox.return_value = (0, 0, 80, 20)  # text bounding box
        
        mock_image.open.return_value = mock_img
        mock_image.new.return_value = mock_overlay
        mock_image.alpha_composite.return_value = mock_img
        mock_draw.Draw.return_value = mock_draw_obj
        
        # Mock font loading
        mock_font_obj = MagicMock()
        mock_font.truetype.return_value = mock_font_obj
        
        with patch('os.path.exists', return_value=True):
            result = add_text_watermark(
                self.test_image_path,
                "@TestHandle",
                Platform.TWITTER
            )
        
        # Should return the expected output path
        expected_output = self.test_image_path.replace('.png', '_watermarked.png')
        self.assertEqual(result, expected_output)
        
        # Verify text was drawn
        mock_draw_obj.text.assert_called_once()
        mock_draw_obj.rectangle.assert_called_once()  # Background rectangle
    
    @patch('watermark.Image')
    def test_add_text_watermark_import_error(self, mock_image):
        """Test text watermark when PIL is not available."""
        with patch('watermark.Image', side_effect=ImportError()):
            result = add_text_watermark(
                self.test_image_path,
                "@TestHandle"
            )
            
            # Should return original path when PIL is not available
            self.assertEqual(result, self.test_image_path)
    
    def test_watermark_for_platform_text(self):
        """Test platform-specific watermarking with text."""
        with patch('watermark.add_text_watermark') as mock_text_watermark:
            mock_text_watermark.return_value = "/tmp/watermarked.png"
            
            result = watermark_for_platform(
                self.test_image_path,
                "instagram",
                "@TestHandle",
                is_logo=False
            )
            
            mock_text_watermark.assert_called_once_with(
                self.test_image_path,
                "@TestHandle",
                Platform.INSTAGRAM,
                0.92,
                output_path=None
            )
            self.assertEqual(result, "/tmp/watermarked.png")
    
    def test_watermark_for_platform_logo(self):
        """Test platform-specific watermarking with logo."""
        with patch('watermark.add_logo_watermark') as mock_logo_watermark:
            mock_logo_watermark.return_value = "/tmp/watermarked.png"
            
            result = watermark_for_platform(
                self.test_image_path,
                "tiktok",
                self.test_logo_path,
                is_logo=True
            )
            
            mock_logo_watermark.assert_called_once_with(
                self.test_image_path,
                self.test_logo_path,
                Platform.TIKTOK,
                0.92,
                output_path=None
            )
            self.assertEqual(result, "/tmp/watermarked.png")
    
    def test_watermark_for_platform_invalid_platform(self):
        """Test watermarking with invalid platform name."""
        with patch('watermark.add_text_watermark') as mock_text_watermark:
            mock_text_watermark.return_value = "/tmp/watermarked.png"
            
            result = watermark_for_platform(
                self.test_image_path,
                "invalid_platform",
                "@TestHandle",
                is_logo=False
            )
            
            # Should default to GENERIC platform
            mock_text_watermark.assert_called_once_with(
                self.test_image_path,
                "@TestHandle",
                Platform.GENERIC,
                0.92,
                output_path=None
            )
    
    def test_create_branded_image(self):
        """Test creation of branded image with watermark and metadata."""
        with patch('watermark.add_text_watermark') as mock_text_watermark, \
             patch('watermark.add_metadata') as mock_add_metadata:
            
            mock_text_watermark.return_value = "/tmp/watermarked.png"
            mock_add_metadata.return_value = "/tmp/branded.png"
            
            result = create_branded_image(
                self.test_image_path,
                "Custom Brand Text",
                Platform.INSTAGRAM
            )
            
            # Check text watermark was added
            mock_text_watermark.assert_called_once_with(
                self.test_image_path,
                "Custom Brand Text",
                Platform.INSTAGRAM,
                0.92,
                output_path=None
            )
            
            # Check metadata was added
            mock_add_metadata.assert_called_once()
            self.assertEqual(result, "/tmp/branded.png")
    
    def test_batch_watermark_success(self):
        """Test batch watermarking of multiple images."""
        image_paths = ["/tmp/img1.png", "/tmp/img2.png", "/tmp/img3.png"]
        
        with patch('watermark.watermark_for_platform') as mock_watermark:
            mock_watermark.side_effect = [
                "/tmp/img1_watermarked.png",
                "/tmp/img2_watermarked.png", 
                "/tmp/img3_watermarked.png"
            ]
            
            results = batch_watermark(
                image_paths,
                "twitter",
                "@BatchTest"
            )
            
            # Should have called watermark_for_platform for each image
            self.assertEqual(mock_watermark.call_count, 3)
            
            # Should return list of watermarked paths
            expected_results = [
                "/tmp/img1_watermarked.png",
                "/tmp/img2_watermarked.png",
                "/tmp/img3_watermarked.png"
            ]
            self.assertEqual(results, expected_results)
    
    def test_batch_watermark_with_errors(self):
        """Test batch watermarking when some images fail."""
        image_paths = ["/tmp/img1.png", "/tmp/img2.png"]
        
        def side_effect(path, platform, content, is_logo, opacity):
            if "img1" in path:
                raise Exception("Watermarking failed")
            return "/tmp/img2_watermarked.png"
        
        with patch('watermark.watermark_for_platform', side_effect=side_effect), \
             patch('builtins.print'):
            
            results = batch_watermark(
                image_paths,
                "instagram",
                "@ErrorTest"
            )
            
            # Should return original path for failed image, watermarked path for successful
            expected_results = [
                "/tmp/img1.png",  # Original path due to error
                "/tmp/img2_watermarked.png"  # Watermarked path
            ]
            self.assertEqual(results, expected_results)
    
    @patch('watermark.piexif')
    @patch('watermark.datetime')
    def test_add_metadata_success(self, mock_datetime, mock_piexif):
        """Test successful metadata addition."""
        # Mock piexif functionality
        mock_piexif.load.return_value = {
            "0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None
        }
        mock_piexif.dump.return_value = b"mock_exif_data"
        mock_piexif.ImageIFD.ImageDescription = 270
        mock_piexif.ImageIFD.Artist = 315
        mock_piexif.ImageIFD.Software = 305
        mock_piexif.ImageIFD.DateTime = 306
        
        # Mock datetime
        mock_datetime.now.return_value.strftime.return_value = "2024:01:01 12:00:00"
        
        metadata = {
            "description": "Test description",
            "artist": "Test artist",
            "software": "Test software"
        }
        
        with patch('watermark.Image') as mock_image:
            mock_img = MagicMock()
            mock_image.open.return_value = mock_img
            
            result = add_metadata(self.test_image_path, metadata)
            
            # Should return the image path
            self.assertEqual(result, self.test_image_path)
            
            # Should have saved with metadata
            mock_img.save.assert_called_once()
    
    def test_add_metadata_no_piexif(self):
        """Test metadata addition when piexif is not available."""
        with patch('watermark.piexif', None):
            result = add_metadata(self.test_image_path, {"test": "data"})
            
            # Should return original path when piexif is not available
            self.assertEqual(result, self.test_image_path)
    
    def test_watermark_for_platform_images_directory_default(self):
        """Test that watermark_for_platform defaults to images/ directory."""
        with patch('watermark.add_text_watermark') as mock_text_watermark:
            # Mock the return value to be in images/ directory
            mock_text_watermark.return_value = "images/test_image_watermarked.png"
            
            result = watermark_for_platform(
                "/tmp/test_image.png",
                "instagram",
                "@TestHandle",
                is_logo=False
            )
            
            # Should call add_text_watermark with no explicit output_path
            mock_text_watermark.assert_called_once_with(
                "/tmp/test_image.png",
                "@TestHandle",
                Platform.INSTAGRAM,
                0.92,
                output_path=None
            )
            
            # Result should be in images/ directory
            self.assertTrue(result.startswith("images/"))
    
    @patch('watermark.Path')
    def test_output_directory_creation(self, mock_path):
        """Test that output directories are created when needed."""
        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.parent = MagicMock()
        
        with patch('watermark.Image') as mock_image:
            mock_img = MagicMock()
            mock_img.size = (800, 600)
            mock_img.mode = 'RGBA'
            mock_img.copy.return_value = mock_img
            mock_image.open.return_value = mock_img
            mock_image.new.return_value = MagicMock()
            
            with patch('watermark.ImageDraw') as mock_draw, \
                 patch('watermark.ImageFont'):
                mock_draw_obj = MagicMock()
                mock_draw_obj.textbbox.return_value = (0, 0, 80, 20)
                mock_draw.Draw.return_value = mock_draw_obj
                
                add_text_watermark(
                    "/tmp/test_image.png",
                    "@TestHandle",
                    Platform.INSTAGRAM
                )
                
                # Should have called mkdir on the parent directory
                mock_path_instance.parent.mkdir.assert_called_once_with(
                    parents=True, exist_ok=True
                )
    
    def test_images_directory_path_logic(self):
        """Test the logic for determining output paths in images/ directory."""
        with patch('watermark.Image') as mock_image, \
             patch('watermark.ImageDraw') as mock_draw, \
             patch('watermark.ImageFont') as mock_font, \
             patch('watermark.Path') as mock_path:
            
            # Setup mocks
            mock_img = MagicMock()
            mock_img.size = (800, 600)
            mock_img.mode = 'RGBA'
            mock_img.copy.return_value = mock_img
            mock_image.open.return_value = mock_img
            mock_image.new.return_value = MagicMock()
            mock_image.alpha_composite.return_value = mock_img
            
            mock_draw_obj = MagicMock()
            mock_draw_obj.textbbox.return_value = (0, 0, 80, 20)
            mock_draw.Draw.return_value = mock_draw_obj
            
            mock_font.load_default.return_value = MagicMock()
            
            mock_path_instance = MagicMock()
            mock_path.return_value = mock_path_instance
            mock_path_instance.parent = MagicMock()
            
            # Test 1: Input not in images/ should output to images/
            result = add_text_watermark(
                "/tmp/test_image.png",
                "@TestHandle",
                Platform.INSTAGRAM
            )
            
            # Should save to images/ directory
            expected_calls = mock_img.save.call_args_list
            self.assertTrue(any("images/" in str(call) for call in expected_calls))
            
            # Reset mock
            mock_img.save.reset_mock()
            
            # Test 2: Input already in images/ should stay in images/
            result = add_text_watermark(
                "images/test_image.png",
                "@TestHandle",
                Platform.INSTAGRAM
            )
            
            # Should save with _watermarked suffix in same directory
            expected_calls = mock_img.save.call_args_list
            self.assertTrue(any("_watermarked" in str(call) for call in expected_calls))
    
    def test_explicit_output_path_override(self):
        """Test that explicit output_path parameter overrides images/ default."""
        with patch('watermark.add_text_watermark') as mock_text_watermark:
            mock_text_watermark.return_value = "/custom/path/output.png"
            
            result = watermark_for_platform(
                "/tmp/test_image.png",
                "instagram",
                "@TestHandle",
                is_logo=False,
                output_path="/custom/path/output.png"
            )
            
            # Should call with explicit output_path
            mock_text_watermark.assert_called_once_with(
                "/tmp/test_image.png",
                "@TestHandle",
                Platform.INSTAGRAM,
                0.92,
                output_path="/custom/path/output.png"
            )
            
            # Result should be the custom path
            self.assertEqual(result, "/custom/path/output.png")

if __name__ == '__main__':
    unittest.main()

