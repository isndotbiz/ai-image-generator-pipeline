# A/B Palette Selection System

This system automatically selects the 2 highest-frequency color palettes from extracted video color data, ensuring they are sufficiently different (HSL distance ≥ 10) for effective A/B testing.

## Files Overview

### Core Scripts
- **`ab_palette_selector.py`** - Main script that analyzes color frequencies and creates A/B palettes
- **`daily_palette_rotation.sh`** - Shell script for automated daily palette rotation
- **`palette_rotation.log`** - Log file tracking rotation activities

### Generated Files
- **`palette_A.json`** - Current Palette A (highest frequency palette)
- **`palette_B.json`** - Current Palette B (sufficiently different high-frequency palette)
- **`palette_A_YYYYMMDD_HHMMSS.json`** - Timestamped backups of previous Palette A
- **`palette_B_YYYYMMDD_HHMMSS.json`** - Timestamped backups of previous Palette B

## How It Works

### Selection Algorithm

1. **Load Color Data**: Reads `palettes.json` containing extracted color frequencies
2. **Sort by Frequency**: Orders all colors by their appearance frequency
3. **Select Palette A**: 
   - Starts with the highest frequency color as the base
   - Adds similar colors (HSL distance < 10) to create a cohesive palette
4. **Select Palette B**:
   - Finds the highest frequency color that's sufficiently different (HSL distance ≥ 10) from Palette A base
   - Adds similar colors to create the second cohesive palette
5. **Ensure Distinction**: Validates that the two palette bases have HSL distance ≥ 10

### HSL Distance Calculation

The system uses HSL (Hue, Saturation, Lightness) color space to measure color similarity:
- **Hue**: Circular distance (0-360°)
- **Saturation**: Percentage (0-100%)
- **Lightness**: Percentage (0-100%)
- **Distance**: Euclidean distance in 3D HSL space

## Usage

### Manual Execution

```bash
# Run palette selection once
python3 ab_palette_selector.py
```

### Automated Daily Rotation

1. **Set up cron job** for daily execution at 8 AM:
   ```bash
   crontab -e
   ```
   Add this line:
   ```
   0 8 * * * /path/to/your/project/daily_palette_rotation.sh
   ```

2. **Manual daily rotation**:
   ```bash
   ./daily_palette_rotation.sh
   ```

### Monitor Logs

```bash
# View recent rotation activity
tail -f palette_rotation.log

# View full rotation history
cat palette_rotation.log
```

## Output Format

Each palette JSON file contains:

```json
{
  "name": "Palette A",
  "created_at": "2025-06-13T06:23:47.474216",
  "colors": [
    {
      "hex": "#97c8ee",
      "rgb": [151, 200, 238],
      "frequency": 2,
      "appearances": [
        {
          "video": "cluster_03_travel_destinations_1_matches.mp4",
          "frame_position": "25%",
          "color_rank": 2,
          "rgb": [151, 200, 238]
        }
      ]
    }
  ],
  "total_frequency": 3,
  "color_count": 2
}
```

## Configuration

### Adjusting HSL Distance Threshold

Modify the `min_similarity_distance` parameter in `ab_palette_selector.py`:

```python
# Current setting: 10.0
palette_a, palette_b = select_ab_palettes(min_similarity_distance=10.0)

# For more similar palettes, use lower value:
palette_a, palette_b = select_ab_palettes(min_similarity_distance=5.0)

# For more distinct palettes, use higher value:
palette_a, palette_b = select_ab_palettes(min_similarity_distance=15.0)
```

### Backup Retention

The daily rotation script automatically removes backups older than 30 days. To change this:

```bash
# Edit daily_palette_rotation.sh
# Change the number in this line:
find . -name "palette_*_????????_??????.json" -mtime +30 -delete 2>/dev/null

# For 7 days retention:
find . -name "palette_*_????????_??????.json" -mtime +7 -delete 2>/dev/null
```

## Integration with A/B Testing

The generated palette files can be directly consumed by A/B testing frameworks:

```python
# Example usage in Python
import json

# Load palettes
with open('palette_A.json', 'r') as f:
    palette_a = json.load(f)

with open('palette_B.json', 'r') as f:
    palette_b = json.load(f)

# Use in A/B test
def get_test_palette(user_group):
    if user_group == 'A':
        return palette_a['colors']
    else:
        return palette_b['colors']
```

## Troubleshooting

### Common Issues

1. **"palettes.json file not found"**
   - Ensure `palettes.json` exists in the same directory
   - Run color extraction pipeline first

2. **"Not enough colors to create two palettes"**
   - Need at least 2 colors in aggregated_colors
   - Check if color extraction was successful

3. **Warning about HSL distance**
   - All colors are too similar
   - Consider lowering the similarity threshold
   - May indicate limited color variety in source videos

### Validation

```bash
# Check if palettes are valid JSON
jq . palette_A.json
jq . palette_B.json

# Verify HSL distance between palettes
python3 -c "
import json
from ab_palette_selector import rgb_to_hsl, calculate_hsl_distance

with open('palette_A.json') as f: pa = json.load(f)
with open('palette_B.json') as f: pb = json.load(f)

hsl_a = rgb_to_hsl(tuple(pa['colors'][0]['rgb']))
hsl_b = rgb_to_hsl(tuple(pb['colors'][0]['rgb']))
dist = calculate_hsl_distance(hsl_a, hsl_b)
print(f'HSL distance: {dist:.2f}')
"
```

## Performance Notes

- Script typically runs in < 1 second for datasets with hundreds of colors
- Memory usage scales with the number of unique colors in `palettes.json`
- Backup files accumulate over time (cleaned up automatically after 30 days)

