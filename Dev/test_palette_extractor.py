#!/usr/bin/env python3
"""
Unit tests for palette_extractor module.
"""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock

# Add current directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from palette_extractor import (
    extract_dominant_colors,
    rgb_to_hex,
    get_color_palette_prompt
)

class TestPaletteExtractor(unittest.TestCase):
    """Test cases for palette_extractor module."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_colors = [
            (255, 87, 51),   # #FF5733 - red-orange
            (51, 193, 255),  # #33C1FF - sky blue
            (141, 51, 255),  # #8D33FF - purple
            (255, 255, 0),   # #FFFF00 - yellow
            (128, 128, 128)  # #808080 - gray
        ]
        
        self.test_image_path = "/tmp/test_image.png"
    
    def test_rgb_to_hex(self):
        """Test RGB to hex conversion."""
        # Test standard colors
        test_cases = [
            ((255, 0, 0), "#ff0000"),      # Red
            ((0, 255, 0), "#00ff00"),      # Green
            ((0, 0, 255), "#0000ff"),      # Blue
            ((255, 255, 255), "#ffffff"),  # White
            ((0, 0, 0), "#000000"),        # Black
            ((255, 87, 51), "#ff5733"),    # Custom color
            ((128, 128, 128), "#808080"),  # Gray
        ]
        
        for rgb, expected_hex in test_cases:
            with self.subTest(rgb=rgb):
                result = rgb_to_hex(rgb)
                self.assertEqual(result, expected_hex)
                self.assertIsInstance(result, str)
                self.assertTrue(result.startswith('#'))
                self.assertEqual(len(result), 7)
    
    def test_get_color_palette_prompt_with_colors(self):
        """Test color palette prompt generation with colors."""
        prompt = get_color_palette_prompt(self.test_colors)
        
        self.assertIsInstance(prompt, str)
        self.assertGreater(len(prompt), 0)
        
        # Should contain the expected format
        self.assertIn("color palette featuring", prompt)
        
        # Should contain the first 3 colors in hex format
        self.assertIn("#ff5733", prompt)  # First color
        self.assertIn("#33c1ff", prompt)  # Second color  
        self.assertIn("#8d33ff", prompt)  # Third color
        
        # Should NOT contain the 4th and 5th colors (only first 3)
        self.assertNotIn("#ffff00", prompt)  # Fourth color
        self.assertNotIn("#808080", prompt)  # Fifth color
    
    def test_get_color_palette_prompt_empty_colors(self):
        """Test color palette prompt generation with empty colors list."""
        prompt = get_color_palette_prompt([])
        
        self.assertEqual(prompt, "natural color palette")
    
    def test_get_color_palette_prompt_none_colors(self):
        """Test color palette prompt generation with None colors."""
        prompt = get_color_palette_prompt(None)
        
        self.assertEqual(prompt, "natural color palette")
    
    def test_get_color_palette_prompt_single_color(self):
        """Test color palette prompt generation with single color."""
        single_color = [(255, 0, 0)]  # Red
        prompt = get_color_palette_prompt(single_color)
        
        self.assertIn("color palette featuring", prompt)
        self.assertIn("#ff0000", prompt)
    
    def test_get_color_palette_prompt_two_colors(self):
        """Test color palette prompt generation with two colors."""
        two_colors = [(255, 0, 0), (0, 255, 0)]  # Red, Green
        prompt = get_color_palette_prompt(two_colors)
        
        self.assertIn("color palette featuring", prompt)
        self.assertIn("#ff0000", prompt)
        self.assertIn("#00ff00", prompt)
    
    @patch('palette_extractor.Image')
    @patch('palette_extractor.np')
    @patch('palette_extractor.KMeans')
    def test_extract_dominant_colors_success(self, mock_kmeans, mock_np, mock_image):
        """Test successful dominant color extraction."""
        # Mock PIL Image
        mock_img = MagicMock()
        mock_img.size = (100, 100)
        mock_img.convert.return_value = mock_img
        mock_img.resize.return_value = mock_img
        mock_image.open.return_value = mock_img
        
        # Mock numpy array
        mock_array = MagicMock()
        mock_array.reshape.return_value = mock_array
        mock_np.array.return_value = mock_array
        
        # Mock KMeans
        mock_kmeans_instance = MagicMock()
        mock_kmeans_instance.cluster_centers_ = mock_np.array([
            [255, 87, 51],
            [51, 193, 255],
            [141, 51, 255],
            [255, 255, 0],
            [128, 128, 128]
        ])
        mock_kmeans_instance.cluster_centers_.astype.return_value = [
            [255, 87, 51],
            [51, 193, 255], 
            [141, 51, 255],
            [255, 255, 0],
            [128, 128, 128]
        ]
        mock_kmeans.return_value = mock_kmeans_instance
        
        colors = extract_dominant_colors(self.test_image_path, 5)
        
        # Verify result
        self.assertIsInstance(colors, list)
        self.assertEqual(len(colors), 5)
        
        # Verify each color is a tuple of 3 integers
        for color in colors:
            self.assertIsInstance(color, tuple)
            self.assertEqual(len(color), 3)
            for component in color:
                self.assertIsInstance(component, (int, float))
    
    @patch('palette_extractor.Image')
    def test_extract_dominant_colors_import_error(self, mock_image):
        """Test dominant color extraction when dependencies are missing."""
        # Simulate ImportError for PIL
        with patch('palette_extractor.Image', side_effect=ImportError()):
            colors = extract_dominant_colors(self.test_image_path, 3)
            
            # Should return gray colors as fallback
            self.assertEqual(colors, [(128, 128, 128), (128, 128, 128), (128, 128, 128)])
    
    @patch('palette_extractor.KMeans', side_effect=ImportError())
    def test_extract_dominant_colors_sklearn_import_error(self, mock_kmeans):
        """Test dominant color extraction when scikit-learn is missing."""
        colors = extract_dominant_colors(self.test_image_path, 4)
        
        # Should return gray colors as fallback
        self.assertEqual(colors, [(128, 128, 128), (128, 128, 128), (128, 128, 128), (128, 128, 128)])
    
    @patch('palette_extractor.Image')
    def test_extract_dominant_colors_file_error(self, mock_image):
        """Test dominant color extraction when image file cannot be opened."""
        # Mock file error
        mock_image.open.side_effect = FileNotFoundError("File not found")
        
        colors = extract_dominant_colors("/nonexistent/path.png", 3)
        
        # Should return gray colors as fallback
        self.assertEqual(colors, [(128, 128, 128), (128, 128, 128), (128, 128, 128)])
    
    @patch('palette_extractor.Image')
    @patch('palette_extractor.np')
    @patch('palette_extractor.KMeans')
    def test_extract_dominant_colors_processing_error(self, mock_kmeans, mock_np, mock_image):
        """Test dominant color extraction when processing fails."""
        # Mock successful image loading
        mock_img = MagicMock()
        mock_image.open.return_value = mock_img
        
        # But make numpy processing fail
        mock_np.array.side_effect = Exception("Processing error")
        
        colors = extract_dominant_colors(self.test_image_path, 2)
        
        # Should return gray colors as fallback
        self.assertEqual(colors, [(128, 128, 128), (128, 128, 128)])
    
    @patch('palette_extractor.Image')
    @patch('palette_extractor.np')
    @patch('palette_extractor.KMeans')
    def test_extract_dominant_colors_default_num_colors(self, mock_kmeans, mock_np, mock_image):
        """Test dominant color extraction with default number of colors."""
        # Mock successful extraction
        mock_img = MagicMock()
        mock_image.open.return_value = mock_img
        mock_img.convert.return_value = mock_img
        mock_img.resize.return_value = mock_img
        
        mock_array = MagicMock()
        mock_np.array.return_value = mock_array
        mock_array.reshape.return_value = mock_array
        
        # Mock KMeans with 5 colors (default)
        mock_kmeans_instance = MagicMock()
        mock_centers = [[255, 0, 0], [0, 255, 0], [0, 0, 255], [255, 255, 0], [255, 0, 255]]
        mock_kmeans_instance.cluster_centers_.astype.return_value = mock_centers
        mock_kmeans.return_value = mock_kmeans_instance
        
        colors = extract_dominant_colors(self.test_image_path)  # No num_colors specified
        
        # Should have called KMeans with n_clusters=5 (default)
        mock_kmeans.assert_called_once_with(n_clusters=5, random_state=42, n_init=10)
        
        # Should return 5 colors
        self.assertEqual(len(colors), 5)
    
    @patch('palette_extractor.Image')
    @patch('palette_extractor.np')
    @patch('palette_extractor.KMeans')
    def test_extract_dominant_colors_image_processing(self, mock_kmeans, mock_np, mock_image):
        """Test that image is properly processed before color extraction."""
        # Mock PIL Image operations
        mock_img = MagicMock()
        mock_img.size = (1000, 800)  # Original size
        mock_resized_img = MagicMock()
        mock_converted_img = MagicMock()
        
        mock_image.open.return_value = mock_img
        mock_img.convert.return_value = mock_converted_img
        mock_converted_img.resize.return_value = mock_resized_img
        
        # Mock numpy operations
        mock_array = MagicMock()
        mock_np.array.return_value = mock_array
        mock_array.reshape.return_value = mock_array
        
        # Mock KMeans
        mock_kmeans_instance = MagicMock()
        mock_kmeans_instance.cluster_centers_.astype.return_value = [[255, 0, 0]]
        mock_kmeans.return_value = mock_kmeans_instance
        
        extract_dominant_colors(self.test_image_path, 1)
        
        # Verify image processing steps
        mock_img.convert.assert_called_once_with('RGB')
        mock_converted_img.resize.assert_called_once_with((150, 150))
        
        # Verify numpy processing
        mock_np.array.assert_called_once_with(mock_resized_img)
        mock_array.reshape.assert_called_once_with((-1, 3))
        
        # Verify KMeans configuration
        mock_kmeans.assert_called_once_with(n_clusters=1, random_state=42, n_init=10)
        mock_kmeans_instance.fit.assert_called_once_with(mock_array)
    
    def test_integration_extract_and_prompt(self):
        """Test integration between color extraction and prompt generation."""
        # Mock the color extraction to return known colors
        with patch('palette_extractor.extract_dominant_colors') as mock_extract:
            mock_extract.return_value = self.test_colors
            
            # Extract colors
            colors = extract_dominant_colors(self.test_image_path, 5)
            
            # Generate prompt
            prompt = get_color_palette_prompt(colors)
            
            # Verify integration
            self.assertEqual(len(colors), 5)
            self.assertIn("color palette featuring", prompt)
            
            # Should contain first 3 colors
            for color in colors[:3]:
                hex_color = rgb_to_hex(color)
                self.assertIn(hex_color, prompt)
    
    def test_edge_case_extreme_colors(self):
        """Test edge cases with extreme color values."""
        extreme_colors = [
            (0, 0, 0),       # Pure black
            (255, 255, 255), # Pure white
            (255, 0, 0),     # Pure red
            (0, 255, 0),     # Pure green
            (0, 0, 255),     # Pure blue
        ]
        
        # Test RGB to hex conversion
        for color in extreme_colors:
            hex_color = rgb_to_hex(color)
            self.assertIsInstance(hex_color, str)
            self.assertTrue(hex_color.startswith('#'))
            self.assertEqual(len(hex_color), 7)
        
        # Test prompt generation
        prompt = get_color_palette_prompt(extreme_colors)
        self.assertIn("color palette featuring", prompt)
        self.assertIn("#000000", prompt)  # Black
        self.assertIn("#ffffff", prompt)  # White
        self.assertIn("#ff0000", prompt)  # Red

if __name__ == '__main__':
    unittest.main()

