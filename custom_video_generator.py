import os
import pandas as pd
from pathlib import Path
from runwayml import RunwayML
from PIL import Image
import base64
import io
import random

def custom_video_generator():
    """Generate videos with custom prompts and selected images"""
    
    # Initialize client
    api_key = os.getenv('RUNWAY_API_KEY')
    if not api_key:
        print("❌ Please set RUNWAY_API_KEY environment variable")
        return
    
    client = RunwayML(api_key=api_key)
    print("✅ RunwayML client initialized")
    
    print("🎬 CUSTOM VIDEO GENERATOR")
    print("=" * 40)
    
    # Load available images
    try:
        selected_df = pd.read_csv("./outputs/selected_images.csv")
        print(f"📸 {len(selected_df)} images available")
    except Exception as e:
        print(f"❌ Error loading images: {e}")
        return
    
    print("\n🎯 Choose how to create your custom video:")
    print("1. Browse and select specific image")
    print("2. Random high-quality image")
    print("3. Best image from specific cluster")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    selected_image = None
    
    if choice == "1":
        selected_image = browse_and_select_image(selected_df)
    elif choice == "2":
        selected_image = get_random_high_quality_image(selected_df)
    elif choice == "3":
        selected_image = select_from_cluster(selected_df)
    else:
        print("Using random high-quality image...")
        selected_image = get_random_high_quality_image(selected_df)
    
    if selected_image is None:
        print("❌ No image selected")
        return
    
    # Get custom prompt
    print("\n📝 Enter your custom video prompt:")
    print("Examples:")
    print("  - 'Dramatic close-up with moody lighting and slow zoom'")
    print("  - 'Upbeat commercial style with bright colors and quick cuts'")
    print("  - 'Luxury showcase with golden hour lighting and smooth movement'")
    print("  - 'Minimalist aesthetic with clean lines and subtle animation'")
    
    custom_prompt = input("\nYour prompt: ").strip()
    
    if not custom_prompt:
        print("Using default prompt...")
        custom_prompt = "Professional product showcase with smooth camera movements and balanced lighting"
    
    # Video style options
    print("\n🎨 Choose video style:")
    print("1. Landscape (1280:768) - Best for YouTube, Instagram posts")
    print("2. Portrait (768:1280) - Best for TikTok, Instagram Stories")
    print("3. Square (1024:1024) - Best for Instagram posts")
    
    style_choice = input("\nEnter choice (1-3): ").strip()
    
    if style_choice == "2":
        ratio = "768:1280"
        style_name = "Portrait"
    elif style_choice == "3":
        ratio = "1024:1024"
        style_name = "Square"
    else:
        ratio = "1280:768"
        style_name = "Landscape"
    
    # Generate video
    print(f"\n🚀 Generating custom video...")
    print(f"   Image: {Path(selected_image['image_path']).name}")
    print(f"   Style: {style_name} ({ratio})")
    print(f"   Prompt: {custom_prompt}")
    
    # Convert image to base64
    try:
        with Image.open(selected_image['image_path']) as img:
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            if max(img.size) > 1024:
                img.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
            
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=90)
            image_b64 = base64.b64encode(buffer.getvalue()).decode()
    except Exception as e:
        print(f"❌ Error processing image: {e}")
        return
    
    try:
        # Submit to Runway
        print(f"\n📤 Submitting to Runway...")
        
        task = client.image_to_video.create(
            model='gen3a_turbo',
            prompt_image=f"data:image/jpeg;base64,{image_b64}",
            prompt_text=custom_prompt,
            duration=5,
            ratio=ratio
        )
        
        task_id = getattr(task, 'id', None) or str(task)
        task_status = getattr(task, 'status', 'SUBMITTED')
        
        print(f"✅ SUCCESS! Task ID: {task_id} | Status: {task_status}")
        
        # Save result
        result = {
            'task_id': task_id,
            'cluster_id': selected_image.get('cluster_id', 'custom'),
            'theme': f"Custom {style_name} Video",
            'prompt': custom_prompt,
            'image_path': selected_image['image_path'],
            'status': task_status,
            'video_style': style_name,
            'ratio': ratio,
            'aesthetic_score': selected_image.get('aesthetic_score', 0)
        }
        
        # Add to existing tasks
        existing_file = Path("video_outputs/generation_tasks.csv")
        if existing_file.exists():
            existing_df = pd.read_csv(existing_file)
            combined_df = pd.concat([existing_df, pd.DataFrame([result])], ignore_index=True)
        else:
            combined_df = pd.DataFrame([result])
        
        combined_df.to_csv(existing_file, index=False)
        
        print(f"\n💾 Custom video task saved")
        print(f"\n🕰️ To check status and download:")
        print("   python download_videos.py")
        
        return result
        
    except Exception as e:
        print(f"❌ Error generating video: {e}")
        return None

def browse_and_select_image(df):
    """Show top images for user to select from"""
    print("\n📸 Top 20 highest quality images:")
    top_images = df.nlargest(20, 'aesthetic_score')
    
    for i, (idx, row) in enumerate(top_images.iterrows(), 1):
        filename = Path(row['image_path']).name
        score = row['aesthetic_score']
        cluster = row.get('cluster_id', 'N/A')
        print(f"{i:2d}. {filename} (score: {score:.3f}, cluster: {cluster})")
    
    while True:
        try:
            choice = int(input("\nSelect image (1-20): "))
            if 1 <= choice <= len(top_images):
                return top_images.iloc[choice - 1]
            else:
                print("Invalid choice, try again.")
        except ValueError:
            print("Please enter a number.")

def get_random_high_quality_image(df):
    """Get a random image from the top 50% quality images"""
    high_quality = df[df['aesthetic_score'] > df['aesthetic_score'].median()]
    selected = high_quality.sample(n=1).iloc[0]
    
    filename = Path(selected['image_path']).name
    score = selected['aesthetic_score']
    print(f"\n🎲 Random selection: {filename} (score: {score:.3f})")
    
    return selected

def select_from_cluster(df):
    """Select best image from a specific cluster"""
    clusters = sorted(df['cluster_id'].unique())
    print(f"\n🎯 Available clusters: {clusters}")
    
    while True:
        try:
            cluster_choice = int(input("Enter cluster number: "))
            if cluster_choice in clusters:
                cluster_images = df[df['cluster_id'] == cluster_choice]
                best_image = cluster_images.loc[cluster_images['aesthetic_score'].idxmax()]
                
                filename = Path(best_image['image_path']).name
                score = best_image['aesthetic_score']
                print(f"\n🏆 Best from cluster {cluster_choice}: {filename} (score: {score:.3f})")
                
                return best_image
            else:
                print("Invalid cluster, try again.")
        except ValueError:
            print("Please enter a number.")

if __name__ == "__main__":
    custom_video_generator()

