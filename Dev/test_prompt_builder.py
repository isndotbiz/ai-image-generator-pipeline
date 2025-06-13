#!/usr/bin/env python3
"""
Unit tests for prompt_builder module.
"""

import unittest
import sys
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open

# Add current directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from prompt_builder import (
    load_palette,
    extract_color_directives,
    get_brand_tone_phrase,
    build_enhanced_prompt_with_palette,
    build_product_prompt,
    get_negative_prompt,
    validate_prompt_args,
    BRAND_TONE_PHRASES
)

class TestPromptBuilder(unittest.TestCase):
    """Test cases for prompt_builder module."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_palette_data = {
            "colors": [
                {"hex": "#FF5733", "name": "red-orange"},
                {"hex": "#33C1FF", "name": "sky-blue"},
                {"hex": "#8D33FF", "name": "purple"}
            ]
        }
        
        self.test_theme = {
            "location": "luxury office",
            "item": "golden watch",
            "mantra": "Invest Now, Thank Yourself Later"
        }
    
    def test_get_brand_tone_phrase(self):
        """Test brand tone phrase retrieval."""
        # Test valid tone types
        for tone_type in BRAND_TONE_PHRASES.keys():
            phrase = get_brand_tone_phrase(tone_type)
            self.assertIsInstance(phrase, str)
            self.assertGreater(len(phrase), 0)
            self.assertIn(phrase, BRAND_TONE_PHRASES[tone_type])
        
        # Test invalid tone type
        phrase = get_brand_tone_phrase("invalid_tone")
        self.assertEqual(phrase, "refined sophistication")
        
        # Test default tone type
        default_phrase = get_brand_tone_phrase()
        sophisticated_phrase = get_brand_tone_phrase("sophisticated")
        self.assertEqual(default_phrase, sophisticated_phrase)
    
    def test_extract_color_directives(self):
        """Test color directive extraction from palette data."""
        # Test with valid palette data
        directive = extract_color_directives(self.test_palette_data)
        self.assertIsInstance(directive, str)
        self.assertIn("primary colors", directive)
        self.assertIn("#FF5733", directive)
        self.assertIn("#33C1FF", directive)
        self.assertIn("harmonious background", directive)
        
        # Test with empty palette data
        empty_directive = extract_color_directives({})
        self.assertEqual(empty_directive, "")
        
        # Test with None
        none_directive = extract_color_directives(None)
        self.assertEqual(none_directive, "")
        
        # Test with palette data without colors
        no_colors_directive = extract_color_directives({"other_data": "test"})
        self.assertEqual(no_colors_directive, "")
        
        # Test with empty colors list
        empty_colors_directive = extract_color_directives({"colors": []})
        self.assertEqual(empty_colors_directive, "")
    
    @patch('prompt_builder.Path')
    @patch('builtins.open', new_callable=mock_open)
    def test_load_palette_success(self, mock_file, mock_path):
        """Test successful palette loading."""
        # Mock file existence and content
        mock_path.return_value.exists.return_value = True
        mock_file.return_value.read.return_value = json.dumps(self.test_palette_data)
        
        with patch('json.load', return_value=self.test_palette_data):
            palette = load_palette("A")
            self.assertIsNotNone(palette)
            self.assertEqual(palette, self.test_palette_data)
    
    @patch('prompt_builder.Path')
    def test_load_palette_not_found(self, mock_path):
        """Test palette loading when file doesn't exist."""
        # Mock file not existing
        mock_path.return_value.exists.return_value = False
        
        palette = load_palette("NONEXISTENT")
        self.assertIsNone(palette)
    
    @patch('prompt_builder.Path')
    @patch('builtins.open', new_callable=mock_open)
    def test_load_palette_aggregated_colors(self, mock_file, mock_path):
        """Test loading palette with aggregated_colors structure."""
        aggregated_data = {
            "aggregated_colors": [
                {"hex": "#FF0000", "name": "red"},
                {"hex": "#00FF00", "name": "green"},
                {"hex": "#0000FF", "name": "blue"},
                {"hex": "#FFFF00", "name": "yellow"},
                {"hex": "#FF00FF", "name": "magenta"},
                {"hex": "#00FFFF", "name": "cyan"}
            ]
        }
        
        mock_path.return_value.exists.return_value = True
        
        with patch('json.load', return_value=aggregated_data):
            palette = load_palette("A")
            self.assertIsNotNone(palette)
            self.assertIn("colors", palette)
            self.assertEqual(len(palette["colors"]), 5)  # Should take first 5
    
    def test_build_enhanced_prompt_with_palette(self):
        """Test enhanced prompt building with palette injection."""
        with patch('prompt_builder.load_palette', return_value=self.test_palette_data):
            prompt = build_enhanced_prompt_with_palette(
                location=self.test_theme["location"],
                item=self.test_theme["item"],
                mantra=self.test_theme["mantra"],
                palette_id="A"
            )
            
            # Check that all components are included
            self.assertIn(self.test_theme["location"], prompt)
            self.assertIn(self.test_theme["item"], prompt)
            self.assertIn(self.test_theme["mantra"], prompt)
            self.assertIn("primary colors", prompt)
            self.assertIn("#FF5733", prompt)
            self.assertIn("#33C1FF", prompt)
            self.assertIn("refined aesthetics", prompt)  # Brand tone phrase
            self.assertIn("Canon EOS R5", prompt)  # Camera settings
            self.assertIn("4:5", prompt)  # Default aspect ratio
    
    def test_build_enhanced_prompt_without_palette(self):
        """Test enhanced prompt building without palette."""
        prompt = build_enhanced_prompt_with_palette(
            location=self.test_theme["location"],
            item=self.test_theme["item"],
            mantra=self.test_theme["mantra"]
        )
        
        # Check that basic components are included
        self.assertIn(self.test_theme["location"], prompt)
        self.assertIn(self.test_theme["item"], prompt)
        self.assertIn(self.test_theme["mantra"], prompt)
        
        # Check that palette-specific colors are not included
        self.assertNotIn("primary colors {", prompt)
    
    def test_build_product_prompt(self):
        """Test legacy product prompt building."""
        prompt = build_product_prompt(
            location="modern studio",
            item="leather briefcase",
            text_overlay="Build Success",
            aspect_ratio="3:4"
        )
        
        self.assertIn("modern studio", prompt)
        self.assertIn("leather briefcase", prompt)
        self.assertIn("Build Success", prompt)
        self.assertIn("3:4", prompt)
        self.assertIn("Canon EOS R5", prompt)
        self.assertIn("commercial photography style", prompt)
    
    def test_get_negative_prompt(self):
        """Test negative prompt generation."""
        negative = get_negative_prompt()
        
        self.assertIsInstance(negative, str)
        self.assertGreater(len(negative), 0)
        
        # Check for key filtering terms
        expected_terms = ["lowres", "jpeg artifacts", "plastic", "watermark", "nsfw"]
        for term in expected_terms:
            self.assertIn(term, negative)
    
    def test_validate_prompt_args_valid(self):
        """Test prompt argument validation with valid inputs."""
        valid = validate_prompt_args(
            location="luxury office",
            item="golden watch",
            text_overlay="Invest Now",
            aspect_ratio="4:5"
        )
        
        self.assertTrue(valid)
    
    def test_validate_prompt_args_invalid(self):
        """Test prompt argument validation with invalid inputs."""
        # Empty strings
        invalid = validate_prompt_args(
            location="",
            item="watch",
            text_overlay="text",
            aspect_ratio="4:5"
        )
        self.assertFalse(invalid)
        
        # Whitespace only
        invalid = validate_prompt_args(
            location="   ",
            item="watch",
            text_overlay="text",
            aspect_ratio="4:5"
        )
        self.assertFalse(invalid)
    
    def test_validate_prompt_args_unusual_ratio(self):
        """Test prompt argument validation with unusual aspect ratio."""
        # This should still return True but print a warning
        with patch('builtins.print') as mock_print:
            valid = validate_prompt_args(
                location="office",
                item="watch",
                text_overlay="text",
                aspect_ratio="7:3"
            )
            
            self.assertTrue(valid)
            mock_print.assert_called_once()
            self.assertIn("Warning", mock_print.call_args[0][0])
    
    def test_brand_tone_phrases_structure(self):
        """Test that BRAND_TONE_PHRASES has expected structure."""
        self.assertIsInstance(BRAND_TONE_PHRASES, dict)
        
        expected_tones = ["aspirational", "motivational", "professional", "sophisticated", "empowering"]
        for tone in expected_tones:
            self.assertIn(tone, BRAND_TONE_PHRASES)
            self.assertIsInstance(BRAND_TONE_PHRASES[tone], list)
            self.assertGreater(len(BRAND_TONE_PHRASES[tone]), 0)
            
            # Check that all phrases are strings
            for phrase in BRAND_TONE_PHRASES[tone]:
                self.assertIsInstance(phrase, str)
                self.assertGreater(len(phrase), 0)
    
    def test_complex_integration(self):
        """Test complex integration scenario."""
        with patch('prompt_builder.load_palette', return_value=self.test_palette_data):
            # Test with different tone types
            for tone_type in ["aspirational", "motivational", "professional"]:
                prompt = build_enhanced_prompt_with_palette(
                    location="modern gallery",
                    item="vintage camera",
                    mantra="Capture Excellence",
                    aspect_ratio="16:9",
                    palette_id="B",
                    tone_type=tone_type
                )
                
                # Verify all components are present
                self.assertIn("modern gallery", prompt)
                self.assertIn("vintage camera", prompt)
                self.assertIn("Capture Excellence", prompt)
                self.assertIn("16:9", prompt)
                self.assertIn("primary colors", prompt)
                
                # Verify tone-specific phrase is included
                tone_phrase = get_brand_tone_phrase(tone_type)
                self.assertIn(tone_phrase, prompt)

if __name__ == '__main__':
    unittest.main()

