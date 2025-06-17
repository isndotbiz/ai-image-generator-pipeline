#!/bin/bash

# Create 5 slideshow videos from top-ranked images using ffmpeg

echo "🎬 Creating 5 Slideshow Videos from Top-Ranked Images..."
echo "========================================================"

# Check if ffmpeg is available
if ! command -v ffmpeg &> /dev/null; then
    echo "❌ ffmpeg not found. Please install it first:"
    echo "   brew install ffmpeg"
    exit 1
fi

echo "✅ ffmpeg found"

# Create output directory
mkdir -p video_outputs

# Video themes and styles
themes=(
    "Luxury Handcrafted Items - Elegant slow zoom with golden particles"
    "Premium Textiles & Materials - Smooth rotation with fabric-like motion"
    "Artisan Craftsmanship - Cinematic pan with warm lighting effects"
    "Exotic Vehicles & Transportation - Dynamic motion with speed blur effects"
    "Interior Design & Architecture - Architectural walkthrough with depth effects"
)

echo "📸 Processing 5 videos..."

# Process each image in the video queue
i=1
for image in video_queue/video_*.png; do
    if [ $i -gt 5 ]; then
        break
    fi
    
    if [ -f "$image" ]; then
        timestamp=$(date +"%Y%m%d_%H%M")
        output_file="video_outputs/fortuna_bound_slideshow_$(printf "%02d" $i)_${timestamp}.mp4"
        
        echo "\n${i}. Creating: $(basename "$output_file")"
        echo "   Source: $(basename "$image")"
        echo "   Theme: ${themes[$((i-1))]}"
        
        # Create slideshow with zoom effect (4 seconds duration)
        ffmpeg -y -loop 1 -i "$image" -t 4 \
            -vf "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,zoompan=z='min(zoom+0.0015,1.5)':x=iw/2-(iw/zoom/2):y=ih/2-(ih/zoom/2):d=125" \
            -c:v libx264 -pix_fmt yuv420p "$output_file" \
            > /dev/null 2>&1
        
        if [ $? -eq 0 ]; then
            file_size=$(ls -lh "$output_file" | awk '{print $5}')
            echo "   ✅ Created: $file_size"
        else
            echo "   ❌ Failed to create video"
        fi
    else
        echo "   ❌ Image not found: $image"
    fi
    
    ((i++))
done

echo "\n🎉 Video creation complete!"
echo "📁 Videos saved in: video_outputs/"
echo "📊 Total videos created: $((i-1))"

# List created videos
echo "\n📽️ Created videos:"
ls -lh video_outputs/fortuna_bound_slideshow_*_$(date +"%Y%m%d")*.mp4 2>/dev/null | while read line; do
    echo "   $(echo $line | awk '{print $9 " (" $5 ")"}')"
done

echo "\n🚀 Ready for upload to social media platforms!"
echo "💡 For AI-powered videos, set up Runway API and run: ./generate_videos.sh"

