# Enhanced Image Selection for Video Generation

## Overview

This document describes the implementation of Step 3: "Select N images for the current batch" with enhanced selection logic that sorts images by `final_score` and extracts metadata for intelligent video naming.

## Implementation Details

### Core Features

1. **Intelligent Sorting**
   - Primary: Sort by `final_score` in descending order
   - Fallback: Random sorting for images without scores
   - Prioritizes scored images over unscored ones

2. **Environment Variable Support**
   - Reads `MAX_VIDEOS` environment variable for batch size
   - Defaults to 10 if not set
   - Flexible configuration for different deployment scenarios

3. **Metadata Extraction**
   - **Descriptor Tokens**: Extracts meaningful content identifiers
   - **Platform Suffix**: Identifies target platform (_ig_, _tt_, _tw_)
   - **Quality Scores**: Preserves ranking data for video generation

4. **Enhanced Video Naming**
   - Uses descriptor tokens and platform suffix for meaningful filenames
   - Format: `{descriptor}_{platform}_video_{timestamp}.mp4`
   - Fallback: `{descriptor}_video_{timestamp}.mp4` for unknown platforms

### Selection Algorithm

```python
def get_sort_key(img):
    data = ranking_data.get(img.name, {})
    final_score = data.get('final_score', 0)
    # If no score available, use random value for fallback
    if final_score == 0:
        return (0, random.random())
    return (1, final_score)  # Prioritize scored images, then by score
```

### Metadata Structure

Each selected image includes:

```python
{
    'image_path': Path object,
    'filename': str,                    # Original filename
    'descriptor_tokens': str,           # Content identifier
    'platform_suffix': str | None,     # Target platform (ig/tt/tw)
    'ranking_data': dict,               # Full ranking information
    'final_score': float                # Quality score
}
```

### Usage Examples

#### Basic Usage
```bash
# Use default MAX_VIDEOS=10
python3 intelligent_video_generator.py
```

#### Custom Batch Size
```bash
# Generate 5 videos
MAX_VIDEOS=5 python3 intelligent_video_generator.py
```

#### Testing Selection Logic
```bash
# Test with mock data
python3 test_image_selection_with_mock_data.py

# Test with real ranking data
python3 test_image_selection.py
```

### Output Examples

#### Selection Process
```
🎬 Selected 5 images for video generation (max: 5)
  1. elegant_business_wellness_tt_draft_01.png (score: 0.942, platform: tt)
  2. elegant_business_office_tw_draft.png (score: 0.917, platform: tw)
  3. elegant_business_wellness_tt_draft_02.png (score: 0.802, platform: tt)
  4. elegant_luxury_business_tt_draft.png (score: 0.781, platform: tt)
  5. elegant_business_office_ig_draft.png (score: 0.764, platform: ig)
```

#### Generated Video Filenames
```
elegant_business_wellness_tt_video_20250617_034210.mp4
elegant_business_office_tw_video_20250617_034211.mp4
elegant_business_wellness_tt_video_20250617_034212.mp4
elegant_luxury_business_tt_video_20250617_034213.mp4
elegant_business_office_ig_video_20250617_034214.mp4
```

### Technical Implementation

#### File Locations
- **Main Implementation**: `intelligent_video_generator.py:423-528`
- **Enhanced Ranking Loader**: `intelligent_video_generator.py:392-421`
- **Metadata-based Video Generation**: `intelligent_video_generator.py:302-390`

#### Key Methods

1. **`generate_videos_from_selected(max_videos=None)`**
   - Main orchestration method
   - Implements sorting and selection logic
   - Extracts metadata for each selected image

2. **`load_ranking_data()`**
   - Enhanced ranking data loader
   - Searches multiple directories for ranking files
   - Creates extended lookup dictionary

3. **`generate_video_from_image_enhanced(image_path, metadata)`**
   - Uses metadata for intelligent video naming
   - Preserves descriptor tokens and platform information
   - Enhanced result tracking

### Filename Parsing Logic

#### Platform Suffix Detection
```python
platform_suffix = None
for platform in ['_ig_', '_tt_', '_tw_']:
    if platform in filename:
        platform_suffix = platform.strip('_')
        break
```

#### Descriptor Token Extraction
```python
descriptor_tokens = filename
if platform_suffix:
    # Split on platform and take the part before it
    descriptor_tokens = filename.split(f'_{platform_suffix}_')[0]
elif '_draft' in filename:
    # If no platform suffix, split on _draft
    descriptor_tokens = filename.split('_draft')[0]
```

### Configuration Options

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `MAX_VIDEOS` | 10 | Maximum number of videos to generate in batch |
| `RUNWAYML_API_SECRET` | Required | RunwayML API key for video generation |

### Benefits

1. **Quality-First Selection**: Prioritizes highest-scoring images
2. **Intelligent Naming**: Creates meaningful video filenames
3. **Platform Awareness**: Preserves platform-specific optimizations
4. **Flexible Configuration**: Environment variable control
5. **Robust Fallbacks**: Handles missing ranking data gracefully
6. **Comprehensive Metadata**: Full traceability from image to video

### Testing

The implementation includes comprehensive test scripts:

- **`test_image_selection.py`**: Tests with real ranking data
- **`test_image_selection_with_mock_data.py`**: Tests with simulated high-quality ranking data

Both scripts demonstrate the sorting logic, metadata extraction, and filename generation.

### Integration

This enhancement integrates seamlessly with:
- Existing image ranking systems
- RunwayML video generation pipeline
- Quality scoring and analysis tools
- Platform-specific optimization workflows

The implementation maintains backward compatibility while adding significant intelligence to the video generation process.

