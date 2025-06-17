# Mantra Overlay Guide

## Overview
The `overlay_mantras.py` script adds mantra text overlays to freshly generated images **AFTER** the generation process. This ensures no text is added during the diffusion stage itself.

## Key Features
- ✅ Processes freshly generated `direct_*_<platform>.png` images (non-watermarked)
- ✅ Applies text overlays to **watermarked** copies (keeping logo + text together)
- ✅ Uses MantraGenerator for optimal text placement with `preview_text_placement()`
- ✅ Supports different mantra categories (prosperity, empowerment, growth, etc.)
- ✅ Auto-detects best available fonts with shadow for readability
- ✅ Preserves image quality with high-quality PNG output

## Usage

### Basic Usage
```bash
# Process all images with random mantras
python3 overlay_mantras.py

# Process with specific mantra category
python3 overlay_mantras.py --mantra-category prosperity

# Preview text placement without applying
python3 overlay_mantras.py --preview --limit 5
```

### Advanced Options
```bash
# Specify custom images directory
python3 overlay_mantras.py --images-dir ./custom_images

# Limit number of images processed
python3 overlay_mantras.py --limit 10

# Combine options
python3 overlay_mantras.py --mantra-category luxury --limit 5 --images-dir images
```

## How It Works

1. **Image Discovery**: Finds all `direct_*_*.png` files (excludes watermarked versions)
2. **Mantra Generation**: Uses MantraGenerator to create appropriate mantras
3. **Text Placement**: Calculates optimal position using `preview_text_placement()`
4. **Overlay Application**: Applies text to the **watermarked** version with:
   - Shadow for readability
   - Best available system font
   - High-quality rendering
5. **Preservation**: Saves over watermarked file (logo + text combined)

## Mantra Categories
- `prosperity` - Wealth and abundance focused
- `empowerment` - Personal power and confidence
- `growth` - Learning and development
- `mindfulness` - Peace and presence
- `success` - Achievement and excellence 
- `luxury` - Sophistication and quality

## Technical Details

### File Processing Logic
```python
# For each non-watermarked image:
direct_20250616_215346_ig.png          # ← Source (non-watermarked)
→ direct_20250616_215346_ig_watermarked.png  # ← Target (gets logo + mantra)
```

### Text Rendering Features
- Dynamic font sizing based on image dimensions
- Platform-optimal positioning (bottom third, centered)
- Text shadow for contrast and readability
- RGBA overlay composition for quality
- Automatic font fallback (Arial Bold → Helvetica → Default)

### Error Handling
- Graceful handling of missing watermarked files
- Font loading fallbacks
- Individual image failure isolation
- Detailed progress reporting

## Integration with Workflow

This script is designed for **Step 5** of the image generation pipeline:

1. Generate 20 images via direct prompts ✅
2. Apply watermarks (logos) ✅  
3. Select best images for videos ✅
4. Create video content ✅
5. **Add mantra overlays** ← **THIS SCRIPT**

## Example Output
```
🎯 Found 20 images to process
📁 Images directory: images
🎨 Mantra category: prosperity

[1/20] Processing direct_20250616_215346_ig.png...
    🎲 Generated mantra: Abundance Flows Through Me
✅ Mantra 'Abundance Flows Through Me' applied to direct_20250616_215346_ig.png

📊 Summary:
✅ Successful: 20
❌ Failed: 0
📝 Total processed: 20

🎉 Mantra overlays have been applied to 20 watermarked images!
💡 The logo and text are now combined on the watermarked versions.
```

## Best Practices

1. **Run AFTER watermarking**: Ensure watermarked versions exist first
2. **Use specific categories**: Target mantras for your content theme
3. **Preview first**: Test text placement with `--preview` flag
4. **Batch processing**: Process all 20 images at once for consistency
5. **Quality check**: Verify a few results before proceeding with workflow

## Troubleshooting

**No images found?**
- Check `--images-dir` path
- Ensure files follow `direct_*_*.png` pattern
- Verify you're in the correct directory

**Missing watermarked files?**
- Run watermarking step first
- Check watermarked files exist with `_watermarked.png` suffix

**Font issues?**
- Script auto-detects best available fonts
- Fallbacks to default if needed
- No manual font installation required

