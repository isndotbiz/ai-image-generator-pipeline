#!/usr/bin/env python3
"""
Batch Report & Success Metrics Generator

After all downloads finish:
• Produce a summary dict {total, succeeded, failed, elapsed}.
• Append it to (or create) video_outputs/video_generation_results_<timestamp>.json.
• Print human-readable stats (success rate, average latency).
Optionally commit these artefacts or upload to cloud storage/CDN.

Usage:
    python batch_report_generator.py [--polling-results-file path/to/results.json]
    python batch_report_generator.py --all  # Process all polling results files
    python batch_report_generator.py --commit  # Commit results to git
    python batch_report_generator.py --upload-to-cloud  # Upload to cloud storage
"""

import os
import sys
import json
import argparse
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
from collections import defaultdict

class BatchReportGenerator:
    def __init__(self, output_dir="video_outputs"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
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
    
    def calculate_batch_metrics(self, polling_results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate comprehensive batch metrics from polling results"""
        start_time = datetime.now()
        
        # Extract basic stats from polling_stats if available
        polling_stats = polling_results.get('polling_stats', {})
        task_results = polling_results.get('task_results', [])
        
        # Calculate timing metrics
        start_time_str = polling_stats.get('start_time')
        end_time_str = polling_stats.get('end_time')
        
        elapsed_seconds = 0
        if start_time_str and end_time_str:
            try:
                start_dt = datetime.fromisoformat(start_time_str)
                end_dt = datetime.fromisoformat(end_time_str)
                elapsed_seconds = (end_dt - start_dt).total_seconds()
            except ValueError:
                elapsed_seconds = 0
        
        # Count task outcomes
        total_tasks = len(task_results)
        succeeded_count = 0
        failed_count = 0
        cancelled_count = 0
        pending_count = 0
        
        # Track detailed metrics
        status_counts = defaultdict(int)
        task_durations = []
        downloaded_videos = []
        
        for task in task_results:
            final_status = task.get('final_status', task.get('status', 'UNKNOWN'))
            status_counts[final_status] += 1
            
            if final_status == 'SUCCEEDED':
                succeeded_count += 1
                # Check if video was actually downloaded
                stub = self.get_filename_stub(task)
                video_path = self.output_dir / f"{stub}.mp4"
                if video_path.exists():
                    downloaded_videos.append({
                        'filename': f"{stub}.mp4",
                        'size_mb': round(video_path.stat().st_size / (1024*1024), 2),
                        'task_id': task.get('task_id', ''),
                        'prompt': task.get('prompt', '')[:100] + '...' if len(task.get('prompt', '')) > 100 else task.get('prompt', '')
                    })
                
                # Calculate individual task duration if available
                task_start = task.get('timestamp')
                task_end = task.get('completion_time')
                if task_start and task_end:
                    try:
                        task_start_dt = datetime.fromisoformat(task_start)
                        task_end_dt = datetime.fromisoformat(task_end)
                        duration = (task_end_dt - task_start_dt).total_seconds()
                        task_durations.append(duration)
                    except ValueError:
                        pass
            
            elif final_status == 'FAILED':
                failed_count += 1
            elif final_status == 'CANCELLED':
                cancelled_count += 1
            elif final_status in ['PENDING', 'RUNNING']:
                pending_count += 1
        
        # Calculate success rate
        success_rate = (succeeded_count / total_tasks * 100) if total_tasks > 0 else 0
        
        # Calculate average latency
        avg_task_duration = sum(task_durations) / len(task_durations) if task_durations else 0
        
        # Calculate storage metrics
        total_storage_mb = sum(video['size_mb'] for video in downloaded_videos)
        
        # Build comprehensive metrics dict
        metrics = {
            'batch_summary': {
                'total': total_tasks,
                'succeeded': succeeded_count,
                'failed': failed_count,
                'cancelled': cancelled_count,
                'pending': pending_count,
                'elapsed_seconds': elapsed_seconds,
                'elapsed_formatted': self.format_duration(elapsed_seconds)
            },
            'performance_metrics': {
                'success_rate_percent': round(success_rate, 2),
                'average_task_duration_seconds': round(avg_task_duration, 2),
                'average_task_duration_formatted': self.format_duration(avg_task_duration),
                'total_poll_count': polling_stats.get('poll_count', 0),
                'tasks_per_second': round(total_tasks / elapsed_seconds, 3) if elapsed_seconds > 0 else 0
            },
            'download_metrics': {
                'videos_downloaded': len(downloaded_videos),
                'total_storage_mb': round(total_storage_mb, 2),
                'total_storage_gb': round(total_storage_mb / 1024, 3),
                'average_video_size_mb': round(total_storage_mb / len(downloaded_videos), 2) if downloaded_videos else 0
            },
            'detailed_status_counts': dict(status_counts),
            'downloaded_videos': downloaded_videos,
            'batch_metadata': {
                'generated_at': datetime.now().isoformat(),
                'batch_id': self.timestamp,
                'source_polling_file': None,  # Will be set by caller
                'generator_version': '1.0.0'
            }
        }
        
        return metrics
    
    def get_filename_stub(self, task: Dict[str, Any]) -> str:
        """Generate filename stub from task info (matches download_succeeded_videos.py logic)"""
        if 'target_filename_stub' in task and task['target_filename_stub']:
            return task['target_filename_stub']
        
        task_id = task.get('task_id', 'unknown')
        return f"video_{task_id[:8]}"
    
    def format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format"""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = seconds // 60
            secs = seconds % 60
            return f"{int(minutes)}m {secs:.1f}s"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            secs = seconds % 60
            return f"{int(hours)}h {int(minutes)}m {secs:.1f}s"
    
    def save_batch_report(self, metrics: Dict[str, Any], source_file: Optional[Path] = None) -> Path:
        """Save batch report to timestamped JSON file"""
        if source_file:
            metrics['batch_metadata']['source_polling_file'] = str(source_file)
        
        # Generate filename
        report_filename = f"video_generation_results_{self.timestamp}.json"
        report_path = self.output_dir / report_filename
        
        # Check if file already exists and append if it does
        if report_path.exists():
            try:
                with open(report_path, 'r') as f:
                    existing_data = json.load(f)
                
                # If existing data is a list, append to it
                if isinstance(existing_data, list):
                    existing_data.append(metrics)
                    final_data = existing_data
                else:
                    # If existing data is a dict, create a list
                    final_data = [existing_data, metrics]
            except (json.JSONDecodeError, Exception):
                # If file exists but is corrupted, overwrite
                final_data = metrics
        else:
            final_data = metrics
        
        # Save the report
        with open(report_path, 'w') as f:
            json.dump(final_data, f, indent=2)
        
        return report_path
    
    def print_human_readable_stats(self, metrics: Dict[str, Any]):
        """Print comprehensive human-readable statistics"""
        batch = metrics['batch_summary']
        perf = metrics['performance_metrics']
        downloads = metrics['download_metrics']
        
        print(f"\n{'=' * 80}")
        print(f"📊 BATCH REPORT & SUCCESS METRICS")
        print(f"{'=' * 80}")
        print(f"🕐 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🆔 Batch ID: {self.timestamp}")
        
        print(f"\n📈 BATCH SUMMARY:")
        print(f"  • Total tasks: {batch['total']}")
        print(f"  • ✅ Succeeded: {batch['succeeded']}")
        print(f"  • ❌ Failed: {batch['failed']}")
        print(f"  • ⏹️ Cancelled: {batch['cancelled']}")
        print(f"  • ⏳ Pending: {batch['pending']}")
        print(f"  • ⏱️ Total elapsed: {batch['elapsed_formatted']}")
        
        print(f"\n🚀 PERFORMANCE METRICS:")
        print(f"  • Success rate: {perf['success_rate_percent']}%")
        print(f"  • Average task duration: {perf['average_task_duration_formatted']}")
        print(f"  • Tasks per second: {perf['tasks_per_second']}")
        print(f"  • Total polling cycles: {perf['total_poll_count']}")
        
        print(f"\n📥 DOWNLOAD METRICS:")
        print(f"  • Videos downloaded: {downloads['videos_downloaded']}")
        print(f"  • Total storage: {downloads['total_storage_mb']} MB ({downloads['total_storage_gb']} GB)")
        print(f"  • Average video size: {downloads['average_video_size_mb']} MB")
        
        if metrics.get('downloaded_videos'):
            print(f"\n🎬 DOWNLOADED VIDEOS:")
            for i, video in enumerate(metrics['downloaded_videos'][:10], 1):  # Show first 10
                print(f"  {i:2d}. {video['filename']} ({video['size_mb']} MB)")
                if video['prompt']:
                    print(f"      Prompt: {video['prompt']}")
            
            if len(metrics['downloaded_videos']) > 10:
                print(f"  ... and {len(metrics['downloaded_videos']) - 10} more videos")
        
        print(f"\n📊 STATUS BREAKDOWN:")
        for status, count in metrics.get('detailed_status_counts', {}).items():
            percentage = (count / batch['total'] * 100) if batch['total'] > 0 else 0
            print(f"  • {status}: {count} ({percentage:.1f}%)")
        
        print(f"\n{'=' * 80}")
    
    def commit_artifacts(self, report_path: Path) -> bool:
        """Commit batch report and video artifacts to git"""
        try:
            print(f"\n🔄 Committing artifacts to git...")
            
            # Add the report file
            subprocess.run(['git', 'add', str(report_path)], check=True, capture_output=True)
            
            # Add all video files
            video_files = list(self.output_dir.glob("*.mp4"))
            json_files = list(self.output_dir.glob("*.json"))
            
            for file_path in video_files + json_files:
                subprocess.run(['git', 'add', str(file_path)], check=True, capture_output=True)
            
            # Commit with descriptive message
            commit_message = f"Batch report {self.timestamp}: {len(video_files)} videos generated"
            subprocess.run(['git', 'commit', '-m', commit_message], check=True, capture_output=True)
            
            print(f"✅ Committed {len(video_files)} videos and {len(json_files)} metadata files")
            print(f"📝 Commit message: {commit_message}")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Git commit failed: {e}")
            return False
        except Exception as e:
            print(f"❌ Error during commit: {e}")
            return False
    
    def upload_to_cloud(self, report_path: Path) -> bool:
        """Upload artifacts to cloud storage/CDN (placeholder implementation)"""
        try:
            print(f"\n☁️ Uploading artifacts to cloud storage...")
            
            # This is a placeholder - implement based on your cloud provider
            # Examples:
            # - AWS S3: aws s3 sync video_outputs/ s3://your-bucket/videos/
            # - Google Cloud: gsutil -m cp -r video_outputs/ gs://your-bucket/videos/
            # - Azure: az storage blob upload-batch
            
            video_files = list(self.output_dir.glob("*.mp4"))
            json_files = list(self.output_dir.glob("*.json"))
            
            print(f"📤 Would upload:")
            print(f"  • {len(video_files)} video files")
            print(f"  • {len(json_files)} metadata files")
            print(f"  • Batch report: {report_path.name}")
            
            # Uncomment and modify based on your cloud provider:
            # Example for AWS S3:
            # subprocess.run(['aws', 's3', 'sync', str(self.output_dir), 's3://your-bucket/videos/'], check=True)
            
            print(f"⚠️  Cloud upload is not configured. Enable by modifying upload_to_cloud() method.")
            return False
            
        except Exception as e:
            print(f"❌ Cloud upload failed: {e}")
            return False
    
    def process_polling_results_file(self, results_file: Path) -> Dict[str, Any]:
        """Process a single polling results file and generate batch report"""
        print(f"\n📋 Processing polling results: {results_file.name}")
        
        polling_results = self.load_polling_results(results_file)
        if not polling_results:
            return {}
        
        # Calculate metrics
        metrics = self.calculate_batch_metrics(polling_results)
        
        # Save batch report
        report_path = self.save_batch_report(metrics, results_file)
        print(f"📄 Batch report saved: {report_path}")
        
        # Print human-readable stats
        self.print_human_readable_stats(metrics)
        
        return metrics

def main():
    parser = argparse.ArgumentParser(
        description="Generate batch report and success metrics after video downloads",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python batch_report_generator.py
  python batch_report_generator.py --polling-results-file runway_polling_results_20240101_120000.json
  python batch_report_generator.py --all
  python batch_report_generator.py --commit
  python batch_report_generator.py --upload-to-cloud
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
        help="Output directory for reports (default: video_outputs)"
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
    
    args = parser.parse_args()
    
    try:
        generator = BatchReportGenerator(output_dir=args.output_dir)
        report_paths = []
        
        if args.polling_results_file:
            # Process specific file
            results_file = Path(args.polling_results_file)
            if not results_file.exists():
                print(f"❌ File not found: {results_file}")
                sys.exit(1)
            
            metrics = generator.process_polling_results_file(results_file)
            if metrics:
                report_paths.append(generator.output_dir / f"video_generation_results_{generator.timestamp}.json")
            
        elif args.all:
            # Process all polling results files
            results_files = generator.find_all_polling_results()
            
            if not results_files:
                print("❌ No polling results files found")
                sys.exit(1)
            
            print(f"🔍 Found {len(results_files)} polling results files")
            
            for results_file in results_files:
                metrics = generator.process_polling_results_file(results_file)
                if metrics:
                    report_paths.append(generator.output_dir / f"video_generation_results_{generator.timestamp}.json")
            
        else:
            # Find and process the latest results file
            results_files = generator.find_all_polling_results()
            
            if not results_files:
                print("❌ No polling results files found")
                print("Run the polling loop first or specify --polling-results-file")
                sys.exit(1)
            
            latest_file = results_files[0]  # Already sorted by modification time
            print(f"📁 Using latest results file: {latest_file}")
            
            metrics = generator.process_polling_results_file(latest_file)
            if metrics:
                report_paths.append(generator.output_dir / f"video_generation_results_{generator.timestamp}.json")
        
        # Handle post-processing options
        if report_paths:
            latest_report = report_paths[-1]
            
            if args.commit:
                generator.commit_artifacts(latest_report)
            
            if args.upload_to_cloud:
                generator.upload_to_cloud(latest_report)
        
        print(f"\n🎉 Batch report generation complete!")
        
    except KeyboardInterrupt:
        print(f"\n⏹️ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

