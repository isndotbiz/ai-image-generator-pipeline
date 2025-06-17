# Image Curator for Video Queue

## Overview

The `image_curator.py` script automates the process of scanning, filtering, and preparing images for video generation. It implements the exact requirements specified in Step 1 of the video pipeline.

## Features

### 🔍 Recursive Image Scanning
- Scans `images/` directory recursively for `.png`, `.jpg`, and `.jpeg` files
- Handles both lowercase and uppercase file extensions
- Processes 104 images in the current test run

### 🎯 Quality Heuristics
- **Resolution Filter**: Requires at least 1024px in width OR height
- **Aspect Ratio Filter**: Accepts 16:9, 9:16, or 1:1 ratios (±10% tolerance)
- **Error Handling**: Gracefully handles corrupted or unreadable images

### 📝 Draft Naming Convention
- Automatically extracts 3 descriptive terms from original filenames
- Removes common patterns like timestamps, watermark indicators, platform suffixes
- Assigns random platform suffix: `_ig` (Instagram), `_tt` (TikTok), `_tw` (Twitter)
- Format: `descriptor1_descriptor2_descriptor3_PLATFORM_draft.ext`

### Examples of Generated Names
```
rolex_oyster_gold_ig_draft.png
elegant_business_serene_tt_draft.png
elegant_luxury_business_tw_draft.png
image_visual_content_ig_draft.png
```

## Usage

```bash
# Run the curator
python3 image_curator.py

# Show help
python3 image_curator.py --help
```

## Results from Test Run

✅ **Successfully processed 104 images**
- **Approved**: 61 files (58.7%)
- **Rejected**: 43 files (41.3%)

### Rejection Reasons
- **Aspect ratio issues**: 38 files (didn't match 16:9, 9:16, or 1:1)
- **Resolution too low**: 5 files (less than 1024px)

### Platform Distribution
- **Instagram**: 23 files
- **TikTok**: 19 files  
- **Twitter**: 19 files

## Output Files

1. **Video Queue**: 61 curated images copied to `video_queue/` with draft naming
2. **Curation Report**: JSON file with detailed analysis of each processed image
3. **Console Output**: Real-time progress and summary statistics

## Key Benefits

✅ **Automated Quality Control**: Eliminates manual filtering of low-quality images
✅ **Consistent Naming**: Ensures all files follow the required draft convention
✅ **Platform Ready**: Random platform assignment prepares files for multi-platform deployment
✅ **Comprehensive Logging**: Full audit trail of decisions and transformations
✅ **Conflict Resolution**: Handles duplicate names with sequential numbering

## Technical Implementation

- **Language**: Python 3
- **Dependencies**: PIL (Pillow), pathlib, json, shutil
- **Architecture**: Object-oriented design with modular methods
- **Error Handling**: Robust exception handling for file operations
- **Performance**: Processes 104 images in ~3 seconds

## Script Location

`/Users/jonathanmallinger/Dev/image_curator.py`

The script is ready for immediate use and can be integrated into the broader video generation pipeline.

