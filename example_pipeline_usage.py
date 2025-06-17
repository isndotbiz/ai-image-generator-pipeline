#!/usr/bin/env python3
"""
Example Usage: Video Generation Pipeline

Demonstrates various ways to use the generate_videos.py CLI wrapper
for automated video generation from images.
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def run_command(cmd, description=""):
    """Run a shell command and return the result."""
    print(f"\n🚀 {description}")
    print(f"Command: {cmd}")
    print("-" * 50)
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(f"Error: {result.stderr}")
    
    return result.returncode == 0

def check_prerequisites():
    """Check if the environment is set up correctly."""
    print("🔍 Checking prerequisites...")
    
    # Check if the main script exists
    if not Path("generate_videos.py").exists():
        print("❌ generate_videos.py not found")
        return False
    
    # Check if required directories exist
    video_queue = Path("video_queue")
    if not video_queue.exists():
        print("📁 Creating video_queue directory...")
        video_queue.mkdir(exist_ok=True)
    
    # Check for images
    images = list(video_queue.glob("*.png"))
    print(f"📸 Found {len(images)} PNG images in video_queue/")
    
    # Check environment variable
    api_key = os.getenv('RUNWAYML_API_SECRET')
    if api_key:
        print("✅ RUNWAYML_API_SECRET is set")
    else:
        print("⚠️ RUNWAYML_API_SECRET not set (required for actual execution)")
    
    return True

def example_1_basic_usage():
    """Example 1: Basic video generation for Instagram."""
    print("\n" + "=" * 70)
    print("📱 EXAMPLE 1: Basic Instagram Video Generation")
    print("=" * 70)
    
    cmd = "python generate_videos.py --max_videos 3 --platform ig --dry-run"
    return run_command(cmd, "Generate 3 videos for Instagram (dry run)")

def example_2_platform_variations():
    """Example 2: Different platform configurations."""
    print("\n" + "=" * 70)
    print("🎯 EXAMPLE 2: Platform-Specific Configurations")
    print("=" * 70)
    
    platforms = [
        ("ig", "Instagram - 16:9 format, optimized framing"),
        ("tt", "TikTok - vertical format, engagement-focused"),
        ("tw", "Twitter - horizontal format, social-optimized")
    ]
    
    for platform, description in platforms:
        print(f"\n📺 {description}")
        cmd = f"python generate_videos.py --max_videos 2 --platform {platform} --dry-run"
        if not run_command(cmd, f"Testing {platform} configuration"):
            return False
    
    return True

def example_3_advanced_options():
    """Example 3: Advanced configuration options."""
    print("\n" + "=" * 70)
    print("⚙️ EXAMPLE 3: Advanced Configuration Options")
    print("=" * 70)
    
    # Extended timeout
    cmd1 = "python generate_videos.py --max_videos 5 --timeout 1200 --dry-run"
    if not run_command(cmd1, "Extended timeout (20 minutes) for larger batches"):
        return False
    
    # Skip validation (for debugging)
    cmd2 = "python generate_videos.py --max_videos 2 --skip-validation --dry-run"
    if not run_command(cmd2, "Skip environment validation (debugging mode)"):
        return False
    
    return True

def example_4_cron_setup():
    """Example 4: Cron job setup instructions."""
    print("\n" + "=" * 70)
    print("⏰ EXAMPLE 4: Automated Scheduling Setup")
    print("=" * 70)
    
    cmd = "python generate_videos.py --setup-cron"
    return run_command(cmd, "Show cron job setup instructions")

def example_5_help_and_info():
    """Example 5: Help and information commands."""
    print("\n" + "=" * 70)
    print("❓ EXAMPLE 5: Help and Information")
    print("=" * 70)
    
    cmd = "python generate_videos.py --help"
    return run_command(cmd, "Show complete help information")

def example_6_production_simulation():
    """Example 6: Simulate production execution."""
    print("\n" + "=" * 70)
    print("🏭 EXAMPLE 6: Production Execution Simulation")
    print("=" * 70)
    
    # Only run if we have API key and images
    api_key = os.getenv('RUNWAYML_API_SECRET')
    images = list(Path("video_queue").glob("*.png"))
    
    if not api_key:
        print("⚠️ Skipping production simulation - RUNWAYML_API_SECRET not set")
        print("\nTo run actual video generation:")
        print("1. Set RUNWAYML_API_SECRET environment variable")
        print("2. Add PNG images to video_queue/ directory")
        print("3. Run: python generate_videos.py --max_videos 10 --platform ig")
        return True
    
    if not images:
        print("⚠️ Skipping production simulation - no images in video_queue/")
        print("\nTo run actual video generation:")
        print("1. Add PNG images to video_queue/ directory")
        print("2. Run: python generate_videos.py --max_videos 10 --platform ig")
        return True
    
    print("✅ Ready for production execution!")
    print(f"📸 Found {len(images)} images")
    print("🔑 API key is configured")
    print("\n🚀 To run actual video generation:")
    print("python generate_videos.py --max_videos 5 --platform ig")
    
    # Ask user if they want to run actual generation
    response = input("\n❓ Run actual video generation? (y/N): ").strip().lower()
    if response == 'y':
        cmd = "python generate_videos.py --max_videos 2 --platform ig"
        return run_command(cmd, "ACTUAL video generation (limited to 2 videos for demo)")
    else:
        print("👍 Skipping actual execution as requested")
        return True

def show_output_structure():
    """Show the expected output directory structure."""
    print("\n" + "=" * 70)
    print("📁 EXPECTED OUTPUT STRUCTURE")
    print("=" * 70)
    
    structure = """
📂 Project Directory
├── 📂 video_queue/                    # Input images (PNG format)
│   ├── luxury_watch_rolex_ig_001.png
│   ├── bitcoin_crypto_tt_002.png
│   └── ...
├── 📂 video_outputs/                  # Generated videos and reports
│   ├── luxury_watch_rolex_ig_001.mp4  # Generated video
│   ├── luxury_watch_rolex_ig_001.json # Video metadata
│   ├── bitcoin_crypto_tt_002.mp4
│   ├── bitcoin_crypto_tt_002.json
│   └── video_generation_results_TIMESTAMP.json  # Batch report
├── 📂 logs/                           # Pipeline execution logs
│   ├── pipeline_TIMESTAMP.log         # Detailed execution log
│   └── pipeline_state_TIMESTAMP.json  # Final pipeline state
├── 📄 runway_polling_results_TIMESTAMP.json  # Task polling results
├── 📄 task_queue_TIMESTAMP.json              # Original task queue
└── 📄 generate_videos.py              # Main CLI script
    """
    
    print(structure)

def main():
    """Run all examples and demonstrations."""
    print("🎬 Video Generation Pipeline - Usage Examples")
    print("=" * 70)
    print("This script demonstrates various ways to use the video generation pipeline.")
    print("All examples run in dry-run mode by default for safety.")
    
    # Check prerequisites
    if not check_prerequisites():
        print("❌ Prerequisites not met. Please check your setup.")
        sys.exit(1)
    
    # Run examples
    examples = [
        example_1_basic_usage,
        example_2_platform_variations,
        example_3_advanced_options,
        example_4_cron_setup,
        example_5_help_and_info,
        example_6_production_simulation
    ]
    
    success_count = 0
    for i, example_func in enumerate(examples, 1):
        try:
            if example_func():
                success_count += 1
            else:
                print(f"⚠️ Example {i} had issues")
        except Exception as e:
            print(f"❌ Example {i} failed: {e}")
        
        # Brief pause between examples
        time.sleep(1)
    
    # Show output structure
    show_output_structure()
    
    # Final summary
    print("\n" + "=" * 70)
    print("📊 EXAMPLES SUMMARY")
    print("=" * 70)
    print(f"✅ Completed: {success_count}/{len(examples)} examples")
    
    if success_count == len(examples):
        print("🎉 All examples completed successfully!")
        print("\n🚀 Next steps:")
        print("1. Add PNG images to video_queue/ directory")
        print("2. Set RUNWAYML_API_SECRET environment variable")
        print("3. Run: python generate_videos.py --max_videos 10 --platform ig")
    else:
        print("⚠️ Some examples had issues. Check the output above.")
    
    print("\n📚 For detailed documentation, see: CLI_VIDEO_GENERATION_GUIDE.md")

if __name__ == "__main__":
    main()

