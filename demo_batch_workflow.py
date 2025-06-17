#!/usr/bin/env python3
"""
Demo: Complete Video Download and Batch Reporting Workflow

This script demonstrates the complete workflow for Step 9:
1. Download succeeded videos (using download_succeeded_videos.py)
2. Generate batch report with success metrics (using batch_report_generator.py)
3. Optionally commit artifacts and upload to cloud

Usage:
    python demo_batch_workflow.py [--commit] [--upload-to-cloud] [--dry-run]
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from datetime import datetime

def run_command(cmd, description, dry_run=False):
    """Run a command with optional dry-run mode"""
    print(f"\n🔧 {description}")
    print(f"   Command: {' '.join(cmd)}")
    
    if dry_run:
        print(f"   ⚠️ DRY RUN - Command would be executed")
        return True
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"   ✅ Success")
        if result.stdout:
            print(f"   Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Failed: {e}")
        if e.stderr:
            print(f"   Error: {e.stderr.strip()}")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False

def find_latest_polling_results():
    """Find the most recent polling results file"""
    current_dir = Path(".")
    pattern = "runway_polling_results_*.json"
    results_files = list(current_dir.glob(pattern))
    
    # Also check in video_outputs directory
    video_outputs_dir = current_dir / "video_outputs"
    if video_outputs_dir.exists():
        results_files.extend(video_outputs_dir.glob(pattern))
    
    if not results_files:
        return None
    
    # Return the most recent file
    return sorted(results_files, key=lambda f: f.stat().st_mtime, reverse=True)[0]

def main():
    parser = argparse.ArgumentParser(
        description="Demo: Complete video download and batch reporting workflow",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example workflow:
  python demo_batch_workflow.py                    # Basic workflow
  python demo_batch_workflow.py --commit           # With git commit
  python demo_batch_workflow.py --upload-to-cloud  # With cloud upload
  python demo_batch_workflow.py --dry-run          # Preview commands only
        """
    )
    
    parser.add_argument(
        "--commit",
        action="store_true",
        help="Commit generated artifacts to git"
    )
    
    parser.add_argument(
        "--upload-to-cloud",
        action="store_true",
        help="Upload artifacts to cloud storage/CDN"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be executed without actually running commands"
    )
    
    parser.add_argument(
        "--polling-results-file",
        help="Path to specific polling results file (default: auto-detect latest)"
    )
    
    args = parser.parse_args()
    
    print(f"{'=' * 80}")
    print(f"🎬 VIDEO DOWNLOAD & BATCH REPORTING WORKFLOW")
    print(f"{'=' * 80}")
    print(f"🕐 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if args.dry_run:
        print(f"⚠️ DRY RUN MODE - No actual commands will be executed")
    
    # Step 1: Check for polling results files
    if args.polling_results_file:
        polling_file = Path(args.polling_results_file)
        if not polling_file.exists():
            print(f"❌ Specified polling results file not found: {polling_file}")
            sys.exit(1)
    else:
        polling_file = find_latest_polling_results()
        if not polling_file:
            print(f"❌ No polling results files found.")
            print(f"   Run the polling loop first to generate runway_polling_results_*.json")
            sys.exit(1)
    
    print(f"\n📋 Using polling results file: {polling_file}")
    
    # Step 2: Download succeeded videos
    print(f"\n{'=' * 60}")
    print(f"STEP 1: Download Succeeded Videos")
    print(f"{'=' * 60}")
    
    download_cmd = ["python", "download_succeeded_videos.py", "--polling-results-file", str(polling_file)]
    if not run_command(download_cmd, "Downloading succeeded videos", args.dry_run):
        print(f"❌ Video download failed. Stopping workflow.")
        sys.exit(1)
    
    # Step 3: Generate batch report
    print(f"\n{'=' * 60}")
    print(f"STEP 2: Generate Batch Report & Success Metrics")
    print(f"{'=' * 60}")
    
    report_cmd = ["python", "batch_report_generator.py", "--polling-results-file", str(polling_file)]
    if not run_command(report_cmd, "Generating batch report and success metrics", args.dry_run):
        print(f"❌ Batch report generation failed. Stopping workflow.")
        sys.exit(1)
    
    # Step 4: Optional Git commit
    if args.commit:
        print(f"\n{'=' * 60}")
        print(f"STEP 3: Commit Artifacts to Git")
        print(f"{'=' * 60}")
        
        commit_cmd = ["python", "batch_report_generator.py", "--polling-results-file", str(polling_file), "--commit"]
        if not run_command(commit_cmd, "Committing artifacts to git", args.dry_run):
            print(f"⚠️ Git commit failed, but continuing workflow")
    
    # Step 5: Optional Cloud upload
    if args.upload_to_cloud:
        print(f"\n{'=' * 60}")
        print(f"STEP 4: Upload to Cloud Storage/CDN")
        print(f"{'=' * 60}")
        
        upload_cmd = ["python", "batch_report_generator.py", "--polling-results-file", str(polling_file), "--upload-to-cloud"]
        if not run_command(upload_cmd, "Uploading artifacts to cloud", args.dry_run):
            print(f"⚠️ Cloud upload failed, but workflow completed")
    
    # Final summary
    print(f"\n{'=' * 80}")
    print(f"🎉 WORKFLOW COMPLETE")
    print(f"{'=' * 80}")
    print(f"🕐 Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if not args.dry_run:
        # Show summary of generated files
        video_outputs = Path("video_outputs")
        if video_outputs.exists():
            video_files = list(video_outputs.glob("*.mp4"))
            json_files = list(video_outputs.glob("*.json"))
            
            print(f"\n📁 Generated Files:")
            print(f"   • {len(video_files)} video files (.mp4)")
            print(f"   • {len(json_files)} metadata/report files (.json)")
            
            # Calculate total storage
            total_size_mb = sum(f.stat().st_size for f in video_files) / (1024 * 1024)
            print(f"   • Total storage: {total_size_mb:.2f} MB")
            
            print(f"\n📂 Output directory: {video_outputs.absolute()}")
    
    print(f"\n✨ Step 9 (Batch Report & Success Metrics) implementation complete!")

if __name__ == "__main__":
    main()

