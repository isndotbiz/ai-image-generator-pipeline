#!/usr/bin/env python3
"""
Video Downloader for SUCCEEDED Runway Tasks

For every SUCCEEDED item:
  • Stream-download via requests.get(video_url, stream=True)
  • Save to video_outputs/{stub}.mp4
  • Write per-video metadata (input path, prompt, seed, Runway task json) to video_outputs/{stub}.json for traceability

Usage:
    python download_succeeded_videos.py [--polling-results-file path/to/results.json]
    python download_succeeded_videos.py --all  # Process all polling results files
"""

import os
import sys
import json
import requests
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

class VideoDownloader:
    def __init__(self, output_dir="video_outputs"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.stats = {
            'total_succeeded': 0,
            'downloaded': 0,
            'failed_downloads': 0,
            'already_exists': 0
        }
    
    def load_polling_results(self, results_file: Path) -> Dict[str, Any]:
        """Load polling results from JSON file"""
        try:
            with open(results_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Error loading {results_file}: {e}")
            return {}
    
    def find_all_polling_results(self, directory: str = ".") -> List[Path]:
        """Find all runway polling results files"""
        search_dir = Path(directory)
        pattern = "runway_polling_results_*.json"
        results_files = list(search_dir.glob(pattern))
        
        # Also check in video_outputs directory
        video_outputs_dir = search_dir / "video_outputs"
        if video_outputs_dir.exists():
            results_files.extend(video_outputs_dir.glob(pattern))
        
        return sorted(results_files, key=lambda f: f.stat().st_mtime, reverse=True)
    
    def get_succeeded_tasks(self, polling_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract SUCCEEDED tasks from polling results"""
        succeeded_tasks = []
        
        task_results = polling_results.get('task_results', [])
        for task in task_results:
            if task.get('final_status') == 'SUCCEEDED' and task.get('video_url'):
                succeeded_tasks.append(task)
        
        return succeeded_tasks
    
    def generate_filename_stub(self, task: Dict[str, Any]) -> str:
        """Generate filename stub from task info"""
        # Use target_filename_stub if available, otherwise generate from task_id
        if 'target_filename_stub' in task and task['target_filename_stub']:
            return task['target_filename_stub']
        
        # Fallback to task_id based naming
        task_id = task.get('task_id', 'unknown')
        return f"video_{task_id[:8]}"
    
    def download_video_stream(self, video_url: str, output_path: Path) -> bool:
        """Download video using streaming requests"""
        try:
            print(f"  📥 Streaming download from: {video_url[:50]}...")
            
            # Use streaming download with timeout
            response = requests.get(video_url, stream=True, timeout=30)
            response.raise_for_status()
            
            # Get content length for progress tracking
            content_length = response.headers.get('content-length')
            if content_length:
                total_size = int(content_length)
                print(f"  📊 File size: {total_size / (1024*1024):.2f} MB")
            
            # Write file in chunks
            with open(output_path, 'wb') as f:
                downloaded = 0
                chunk_size = 8192  # 8KB chunks
                
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:  # filter out keep-alive chunks
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Show progress for larger files
                        if content_length and downloaded % (chunk_size * 100) == 0:
                            progress = (downloaded / total_size) * 100
                            print(f"  ⏳ Progress: {progress:.1f}%", end='\r')
            
            # Verify file was created and has content
            if output_path.exists() and output_path.stat().st_size > 0:
                final_size = output_path.stat().st_size
                print(f"  ✅ Downloaded: {final_size / (1024*1024):.2f} MB")
                return True
            else:
                print(f"  ❌ File was not created or is empty")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"  ❌ Network error: {e}")
            return False
        except Exception as e:
            print(f"  ❌ Download error: {e}")
            return False
    
    def create_metadata_json(self, task: Dict[str, Any], video_path: Path, metadata_path: Path) -> bool:
        """Create metadata JSON file for traceability"""
        try:
            # Extract relevant metadata
            metadata = {
                'video_file': video_path.name,
                'download_timestamp': datetime.now().isoformat(),
                'input_path': task.get('image_path', ''),
                'prompt': task.get('prompt', ''),
                'seed': task.get('seed', None),  # May not be present in all tasks
                'runway_task_json': {
                    'task_id': task.get('task_id', ''),
                    'final_status': task.get('final_status', ''),
                    'completion_time': task.get('completion_time', ''),
                    'video_url': task.get('video_url', ''),
                    'original_status': task.get('status', ''),
                    'timestamp': task.get('timestamp', '')
                },
                'target_filename_stub': task.get('target_filename_stub', ''),
                'file_info': {
                    'size_bytes': video_path.stat().st_size if video_path.exists() else 0,
                    'size_mb': round(video_path.stat().st_size / (1024*1024), 2) if video_path.exists() else 0
                }
            }
            
            # Add any additional task fields that might be useful
            for key in ['cluster_id', 'theme', 'duration', 'resolution']:
                if key in task:
                    metadata['runway_task_json'][key] = task[key]
            
            # Write metadata file
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"  📄 Metadata saved: {metadata_path.name}")
            return True
            
        except Exception as e:
            print(f"  ❌ Metadata creation error: {e}")
            return False
    
    def process_succeeded_task(self, task: Dict[str, Any]) -> bool:
        """Process a single SUCCEEDED task - download video and create metadata"""
        task_id = task.get('task_id', 'unknown')
        video_url = task.get('video_url')
        
        if not video_url:
            print(f"  ❌ No video URL found for task {task_id}")
            return False
        
        # Generate filenames
        stub = self.generate_filename_stub(task)
        video_filename = f"{stub}.mp4"
        metadata_filename = f"{stub}.json"
        
        video_path = self.output_dir / video_filename
        metadata_path = self.output_dir / metadata_filename
        
        # Check if video already exists
        if video_path.exists():
            print(f"  ⚠️ Video already exists: {video_filename}")
            self.stats['already_exists'] += 1
            
            # Still create/update metadata if it doesn't exist
            if not metadata_path.exists():
                self.create_metadata_json(task, video_path, metadata_path)
            
            return True
        
        # Download video
        print(f"  🎬 Downloading: {video_filename}")
        
        if self.download_video_stream(video_url, video_path):
            # Create metadata file
            self.create_metadata_json(task, video_path, metadata_path)
            self.stats['downloaded'] += 1
            return True
        else:
            # Clean up failed download
            if video_path.exists():
                video_path.unlink()
            self.stats['failed_downloads'] += 1
            return False
    
    def process_polling_results_file(self, results_file: Path) -> int:
        """Process a single polling results file"""
        print(f"\n📋 Processing: {results_file.name}")
        
        polling_results = self.load_polling_results(results_file)
        if not polling_results:
            return 0
        
        succeeded_tasks = self.get_succeeded_tasks(polling_results)
        
        if not succeeded_tasks:
            print(f"  ℹ️ No SUCCEEDED tasks found")
            return 0
        
        print(f"  ✅ Found {len(succeeded_tasks)} SUCCEEDED tasks")
        self.stats['total_succeeded'] += len(succeeded_tasks)
        
        processed = 0
        for i, task in enumerate(succeeded_tasks, 1):
            task_id = task.get('task_id', 'unknown')[:8]
            print(f"\n  {i}/{len(succeeded_tasks)} Task {task_id}...")
            
            if self.process_succeeded_task(task):
                processed += 1
        
        return processed
    
    def print_final_stats(self):
        """Print final download statistics"""
        print(f"\n{'=' * 60}")
        print(f"📊 DOWNLOAD STATISTICS")
        print(f"{'=' * 60}")
        print(f"✅ Total SUCCEEDED tasks found: {self.stats['total_succeeded']}")
        print(f"📥 Videos downloaded: {self.stats['downloaded']}")
        print(f"⚠️ Already existed: {self.stats['already_exists']}")
        print(f"❌ Failed downloads: {self.stats['failed_downloads']}")
        
        if self.stats['total_succeeded'] > 0:
            success_rate = ((self.stats['downloaded'] + self.stats['already_exists']) / self.stats['total_succeeded']) * 100
            print(f"📈 Success rate: {success_rate:.1f}%")
        
        # List downloaded videos
        video_files = list(self.output_dir.glob("*.mp4"))
        if video_files:
            print(f"\n📁 Videos in {self.output_dir}:")
            total_size = 0
            for video in sorted(video_files):
                size_mb = video.stat().st_size / (1024*1024)
                total_size += size_mb
                print(f"  • {video.name} ({size_mb:.2f} MB)")
            print(f"\n💾 Total storage used: {total_size:.2f} MB")

def main():
    parser = argparse.ArgumentParser(
        description="Download videos from SUCCEEDED Runway tasks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python download_succeeded_videos.py
  python download_succeeded_videos.py --polling-results-file runway_polling_results_20240101_120000.json
  python download_succeeded_videos.py --all
  python download_succeeded_videos.py --output-dir /path/to/videos
        """
    )
    
    parser.add_argument(
        "--polling-results-file",
        help="Path to specific polling results JSON file"
    )
    
    parser.add_argument(
        "--all",
        action="store_true",
        help="Process all polling results files found"
    )
    
    parser.add_argument(
        "--output-dir",
        default="video_outputs",
        help="Output directory for videos and metadata (default: video_outputs)"
    )
    
    args = parser.parse_args()
    
    try:
        downloader = VideoDownloader(output_dir=args.output_dir)
        
        if args.polling_results_file:
            # Process specific file
            results_file = Path(args.polling_results_file)
            if not results_file.exists():
                print(f"❌ File not found: {results_file}")
                sys.exit(1)
            
            downloader.process_polling_results_file(results_file)
            
        elif args.all:
            # Process all polling results files
            results_files = downloader.find_all_polling_results()
            
            if not results_files:
                print("❌ No polling results files found")
                print("Run the polling loop first to generate results")
                sys.exit(1)
            
            print(f"🔍 Found {len(results_files)} polling results files")
            
            for results_file in results_files:
                downloader.process_polling_results_file(results_file)
            
        else:
            # Find and process the latest results file
            results_files = downloader.find_all_polling_results()
            
            if not results_files:
                print("❌ No polling results files found")
                print("Run the polling loop first or specify --polling-results-file")
                sys.exit(1)
            
            latest_file = results_files[0]  # Already sorted by modification time
            print(f"📁 Using latest results file: {latest_file}")
            
            downloader.process_polling_results_file(latest_file)
        
        downloader.print_final_stats()
        
    except KeyboardInterrupt:
        print(f"\n⏹️ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

