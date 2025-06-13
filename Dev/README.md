# GON Image Generator - Professional AI Image Generation Pipeline

This repository contains a sophisticated, modular image generation system that creates premium product photography using AI models with advanced color intelligence and platform-specific optimization.

## System Flow Diagram

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Theme Config   │───▶│ Palette System   │───▶│ Prompt Builder  │
│  (gon.sh)       │    │ (A/B Palettes)   │    │ + Brand Tone    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Multi-Platform │    │ Color Injection  │    │ Enhanced Prompt │
│  Orchestration  │    │ & Directives     │    │ with Palette    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                                              │
         ▼                                              ▼
┌─────────────────┐                          ┌─────────────────┐
│ Replicate API   │◀─────────────────────────│ Image Generator │
│ (Flux 1.1 Pro)  │                          │ (generate.py)   │
└─────────────────┘                          └─────────────────┘
         │                                              │
         ▼                                              ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Raw Generated  │───▶│ Platform-Specific│───▶│ Final Branded   │
│    Images       │    │   Watermarking   │    │    Images       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │ Multi-Platform   │
                       │ Output (IG/TT/TW)│
                       └──────────────────┘
```

## Architecture Overview

The system employs a sophisticated 4-layer modular architecture designed for scalability, maintainability, and professional-grade output:

### Layer 1: Core Intelligence Modules

1. **`palette_extractor.py`** - Advanced Color Intelligence System
   - **K-means clustering** for dominant color extraction
   - **RGB-to-hex conversion** with mathematical precision
   - **Palette description generation** for natural language prompts
   - **Color harmony analysis** for aesthetic consistency

2. **`prompt_builder.py`** - Brand-Aware Prompt Engineering
   - **Professional photography prompts** with camera settings
   - **Brand tone integration** from approved content blueprint
   - **Color palette injection** for cohesive visual identity
   - **Platform-optimized text overlays** and mantras
   - **Negative prompt filtering** for content safety

3. **`watermark.py`** - Platform-Optimized Branding System
   - **Multi-platform positioning** (Instagram: bottom-right, TikTok: mid-left, Twitter: top-right)
   - **Opacity control** at 92% for professional appearance
   - **Dynamic scaling** based on image dimensions
   - **Metadata embedding** for attribution and tracking
   - **Batch processing** capabilities

4. **`generate.py`** - Production-Grade API Wrapper
   - **Flux 1.1 Pro model** integration via Replicate
   - **Robust error handling** for rate limits and NSFW filtering
   - **Batch generation** with progress tracking
   - **Automatic retries** with exponential backoff
   - **Authentication validation** and token management

### Layer 2: Orchestration Engine

**`gon.sh`** - Multi-Platform Content Generation Pipeline
- **Theme-based generation** from curated location/item combinations
- **A/B palette testing** for optimal visual impact
- **Multi-platform optimization** (Instagram 4:5, TikTok 9:16, Twitter 16:9)
- **Automated workflow execution** with error recovery

## Usage Examples

### Quick Start - Individual Modules

#### 1. Color Palette Extraction
```bash
# Extract 5 dominant colors from reference image
python3 palette_extractor.py "luxury_watch.jpg" 5

# Output:
# Dominant colors: [(142, 115, 95), (89, 73, 61), (201, 185, 170), (62, 48, 39), (178, 162, 147)]
# Palette prompt: color palette featuring #8e735f, #59493d, #c9b9aa
```

#### 2. Advanced Prompt Building with Palette Injection
```bash
# Basic prompt without palette
python3 prompt_builder.py "luxury office" "golden watch" "Invest Now, Thank Yourself Later" "4:5"

# Enhanced prompt with palette A injection
python3 prompt_builder.py "luxury office" "golden watch" "Invest Now, Thank Yourself Later" "4:5" "A"

# Output includes:
# Location: luxury office
# Item: golden watch
# Mantra: Invest Now, Thank Yourself Later
# Aspect Ratio: 4:5
# Palette ID: A
# Color Directive: primary colors {#8e735f, #59493d}, harmonious background
# Prompt: Professional product photography: luxury office, golden watch prominently displayed, Canon EOS R5 35 mm f/1.8 ISO 200, clean natural lighting, primary colors {#8e735f, #59493d}, harmonious background, refined sophistication, text overlay "Invest Now, Thank Yourself Later", 4:5, commercial photography style
```

#### 3. Platform-Specific Image Generation
```bash
# Instagram post (4:5 aspect ratio)
python3 generate.py "Professional product photography: luxury office, golden watch prominently displayed..." "luxury_watch_ig.png" "4:5"

# TikTok video cover (9:16 aspect ratio)
python3 generate.py "Professional product photography: luxury office, golden watch prominently displayed..." "luxury_watch_tiktok.png" "9:16"

# Twitter header (16:9 aspect ratio)
python3 generate.py "Professional product photography: luxury office, golden watch prominently displayed..." "luxury_watch_twitter.png" "16:9"
```

#### 4. Multi-Platform Watermarking
```bash
# Instagram watermark (bottom-right positioning)
python3 watermark.py "luxury_watch_ig.png" "@YourBrand" "instagram"

# TikTok watermark (mid-left positioning, avoiding caption area)
python3 watermark.py "luxury_watch_tiktok.png" "@YourBrand" "tiktok"

# Twitter watermark (top-right positioning)
python3 watermark.py "luxury_watch_twitter.png" "@YourBrand" "twitter"

# Logo watermarking
python3 watermark.py "image.png" "logo.png" "instagram" --logo
```

### Production Pipeline Setup

#### Environment Configuration
```bash
# 1. Set up API credentials
export REPLICATE_API_TOKEN="r8_your_actual_token_here"

# 2. Install all dependencies
pip3 install replicate requests pillow scikit-learn numpy piexif

# Alternative: use requirements file
pip3 install -r requirements.txt

# 3. Verify setup
python3 verify_setup.py
```

#### Full Automated Pipeline
```bash
# Execute complete generation pipeline
# Generates 150 unique themes × 2 palettes × 3 platforms = 900 images
./gon.sh

# Pipeline includes:
# - Theme processing from curated list
# - A/B palette injection
# - Multi-platform optimization
# - Automated watermarking
# - Error handling and retry logic
```

### Advanced Usage Patterns

#### Batch Processing with Custom Themes
```bash
# Create custom theme configuration
cat << EOF > custom_themes.txt
Maldives overwater bungalow | vintage Leica camera | Honor the Path to Prosperity | maldives_vintage_1
London riverside flat | silk cashmere throw | Serve the Yield, Earn the Life | london_silk_2
Paris Montmartre attic | platinum Rolex | Bow to Balance Sheets | paris_platinum_3
EOF

# Process custom themes
while IFS='|' read -r location item mantra slug; do
  for palette in A B; do
    for platform in ig tt tw; do
      case "$platform" in
        "ig") aspect_ratio="4:5" ;;
        "tt") aspect_ratio="9:16" ;;
        "tw") aspect_ratio="16:9" ;;
      esac
      
      # Generate with custom pipeline
      python3 prompt_builder.py "$location" "$item" "$mantra" "$aspect_ratio" "$palette" > prompt.txt
      python3 generate.py "$(grep '^Prompt:' prompt.txt | sed 's/^Prompt: //')" "${slug}_${palette}_${platform}.png" "$aspect_ratio"
      python3 watermark.py "${slug}_${palette}_${platform}.png" "@YourBrand" "$platform"
    done
  done
done < custom_themes.txt
```

#### A/B Testing with Color Palettes
```bash
# Compare performance between palettes
# Palette A: Warm, luxury tones
# Palette B: Cool, modern tones

# Generate test variants
python3 prompt_builder.py "modern studio" "luxury briefcase" "Build Your Empire" "4:5" "A"
python3 prompt_builder.py "modern studio" "luxury briefcase" "Build Your Empire" "4:5" "B"

# Analyze color injection differences
diff <(python3 prompt_builder.py "modern studio" "luxury briefcase" "Build Your Empire" "4:5" "A" | grep "Color Directive") \
     <(python3 prompt_builder.py "modern studio" "luxury briefcase" "Build Your Empire" "4:5" "B" | grep "Color Directive")
```

## Configuration

### Environment Variables
- `REPLICATE_API_TOKEN` - Required for image generation via Replicate API
- `PYTHONPATH` - Optional: Add project directory to Python path for imports

### Dependencies
Install all required dependencies:
```bash
pip3 install -r requirements.txt
```

**Core Dependencies:**
- `replicate` - API client for image generation
- `requests` - HTTP library for downloading images
- `Pillow` - Image processing and watermarking
- `scikit-learn` - K-means clustering for color extraction
- `numpy` - Numerical operations for color analysis
- `piexif` - EXIF metadata handling

### Palette Configuration
The system uses two main palette files:
- `palette_A.json` - Warm, luxury-focused color schemes
- `palette_B.json` - Cool, modern color schemes
- `palettes.json` - Aggregated palette database

## Advanced Features

### Brand Tone Integration
The system includes sophisticated brand tone phrases from an approved content blueprint:

```python
BRAND_TONE_PHRASES = {
    "aspirational": ["elevating excellence", "pursuing distinction", "achieving refinement"],
    "motivational": ["empowering success", "inspiring achievement", "driving progress"],
    "professional": ["commercial elegance", "business sophistication", "corporate refinement"],
    "sophisticated": ["refined aesthetics", "premium craftsmanship", "luxurious appeal"],
    "empowering": ["confident presentation", "authoritative positioning", "commanding presence"]
}
```

### Platform-Specific Optimizations

| Platform | Aspect Ratio | Watermark Position | Optimal Use Case |
|----------|-------------|-------------------|------------------|
| Instagram | 4:5 | Bottom-right | Feed posts, stories |
| TikTok | 9:16 | Mid-left | Video covers, portraits |
| Twitter | 16:9 | Top-right | Headers, landscape posts |
| Generic | 4:5 | Bottom-right | Default fallback |

### Error Handling & Recovery

The system includes comprehensive error handling:

```bash
# Common error scenarios and responses:
# - NSFW content filter: Automatically skips and logs
# - Rate limiting: Implements exponential backoff
# - Authentication errors: Clear token validation messages
# - Network failures: Retry logic with timeout handling
# - Invalid prompts: Validation and sanitization
```

### Batch Processing Capabilities

The pipeline supports efficient batch operations:
- **Parallel generation**: Multiple images can be processed concurrently
- **Progress tracking**: Real-time status updates during batch operations
- **Selective retry**: Only failed generations are retried
- **Resource management**: Automatic cleanup of temporary files

## Troubleshooting

### Common Issues

#### Authentication Errors
```bash
# Verify token is set correctly
echo $REPLICATE_API_TOKEN

# Test API connection
python3 -c "import replicate; print('Token valid')" || echo "Token invalid"
```

#### Missing Dependencies
```bash
# Install missing packages
pip3 install replicate requests pillow scikit-learn numpy piexif

# Verify installation
python3 verify_setup.py
```

#### Palette File Issues
```bash
# Check palette files exist
ls -la palette_*.json

# Validate JSON format
python3 -c "import json; print(json.load(open('palette_A.json')))"
```

#### Generation Failures
```bash
# Test individual components
python3 prompt_builder.py "test location" "test item" "test mantra"
python3 generate.py "test prompt" "test.png" "4:5"
```

### Performance Optimization

#### Rate Limit Management
```bash
# Monitor API usage
echo "Checking rate limits..."
curl -H "Authorization: Token $REPLICATE_API_TOKEN" \
     https://api.replicate.com/v1/predictions
```

#### Batch Size Optimization
```bash
# Process in smaller batches for better memory management
# Recommended batch size: 10-20 images per batch
for i in {1..10}; do
  ./gon.sh --batch-size 10 --batch-number $i
done
```

## Features

### Core Capabilities
- **Modular Design**: Each component can be used independently
- **Error Handling**: Robust error handling for API failures and rate limits
- **Batch Processing**: Generate multiple images efficiently
- **Platform Support**: Generate images for different social media platforms
- **Color Intelligence**: Extract and use color palettes from reference images
- **Professional Quality**: Commercial photography style prompts
- **Watermarking**: Add branding and metadata to generated images

### Advanced Features
- **A/B Palette Testing**: Compare performance between color schemes
- **Brand Tone Integration**: Sophisticated tone phrases from content blueprint
- **Platform-Specific Positioning**: Optimized watermark placement
- **Metadata Embedding**: Attribution and tracking information
- **Retry Logic**: Automatic recovery from transient failures
- **Progress Tracking**: Real-time status updates during generation

## File Structure

```
.
├── gon.sh                    # Main orchestration script (150 themes × 2 palettes × 3 platforms)
├── palette_extractor.py      # Color extraction module with K-means clustering
├── prompt_builder.py         # Brand-aware prompt engineering with palette injection
├── watermark.py             # Platform-optimized branding system
├── generate.py              # Production-grade Replicate API wrapper
├── verify_setup.py          # Environment validation and testing
├── requirements.txt         # Python dependencies
├── palette_A.json           # Warm, luxury-focused color palette
├── palette_B.json           # Cool, modern color palette
├── palettes.json           # Aggregated palette database
├── content_blueprint.yaml   # Brand tone and messaging guidelines
└── README.md               # This comprehensive documentation
```

## Benefits of Modular Architecture

### Technical Advantages
1. **Maintainability**: Each module has a single responsibility
2. **Testability**: Individual components can be tested in isolation
3. **Reusability**: Modules can be used in other projects
4. **Flexibility**: Easy to extend or modify specific functionality
5. **Debugging**: Easier to isolate and fix issues
6. **Performance**: Reduced inline Python execution in shell script

### Business Benefits
1. **Scalability**: Easy to increase generation capacity
2. **Quality Consistency**: Standardized prompts and branding
3. **Brand Compliance**: Integrated tone and color guidelines
4. **Multi-Platform Support**: Optimized for different social media
5. **Cost Efficiency**: Batch processing reduces API costs
6. **Rapid Iteration**: Quick testing of new themes and concepts

## Contributing

When contributing to this codebase:

1. **Follow the modular pattern**: Keep components focused and independent
2. **Add comprehensive docstrings**: Document all functions with type hints
3. **Include error handling**: Handle edge cases and API failures gracefully
4. **Test thoroughly**: Verify changes work with different palettes and platforms
5. **Update documentation**: Keep README and inline comments current

## License

This project is designed for professional content generation and brand marketing applications.

