#!/usr/bin/env -S bash -c 'source ~/menv/bin/activate && exec "$0" "$@"'
set -e

# Script to apply new logo watermark to all existing images
# This replaces the old text watermarks with the new Fortuna_Bound_Watermark.png logo

echo "🔄 Applying new logo watermark to all existing images..."
echo "============================================================"

# Check if watermark logo exists
if [ ! -f "Fortuna_Bound_Watermark.png" ]; then
    echo "❌ Error: Fortuna_Bound_Watermark.png not found in current directory"
    exit 1
fi

# Count total images
total_images=$(find images/ -name "*.png" ! -name "*_watermarked.png" ! -name "_*" | wc -l | tr -d ' ')
echo "📊 Found $total_images images to watermark"

processed=0
failed=0

# Process each image
for image_file in images/*.png; do
    # Skip watermarked images and temp files
    if [[ "$image_file" == *"_watermarked.png" ]] || [[ "$(basename "$image_file")" == _* ]]; then
        continue
    fi
    
    # Extract platform from filename
    filename=$(basename "$image_file" .png)
    if [[ "$filename" == *"_ig" ]]; then
        platform="instagram"
    elif [[ "$filename" == *"_tt" ]]; then
        platform="tiktok"  
    elif [[ "$filename" == *"_tw" ]]; then
        platform="twitter"
    else
        echo "⚠️  Skipping $image_file - cannot determine platform"
        continue
    fi
    
    processed=$((processed + 1))
    echo "[$processed/$total_images] Processing $image_file ($platform)..."
    
    # Apply logo watermark
    if python3 watermark.py "$image_file" "Fortuna_Bound_Watermark.png" "$platform" --logo > /dev/null 2>&1; then
        echo "  ✅ Successfully watermarked"
    else
        echo "  ❌ Failed to watermark"
        failed=$((failed + 1))
    fi
done

echo "\n🎯 Watermarking Complete!"
echo "============================================================"
echo "📈 Successfully processed: $((processed - failed)) images"
echo "❌ Failed: $failed images"
echo "📁 Watermarked images saved in images/ directory with _watermarked suffix"

if [ $failed -eq 0 ]; then
    echo "\n🎉 All images successfully watermarked with new logo!"
else
    echo "\n⚠️  Some images failed. Check the output above for details."
fi

