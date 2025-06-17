#!/usr/bin/env python3
"""
Generate Videos CLI - Complete Pipeline Orchestrator

A comprehensive CLI wrapper that orchestrates the entire video generation pipeline:
1. Environment validation (API keys, dependencies)
2. Image curation and selection
3. Video task creation on Runway
4. Task polling and monitoring
5. Video download and organization
6. Batch reporting and metrics

Usage:
    python generate_videos.py --max_videos 10 --platform ig
    python generate_videos.py --max_videos 5 --platform tt --timeout 900
    python generate_videos.py --platform tw --skip-validation --dry-run
"""

import os
import sys
import json
import time
import argparse
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Import pipeline components
try:
    from intelligent_video_generator import IntelligentVideoGenerator
    from kick_off_video_tasks import load_selected_images_with_prompts
    from runway_task_polling_loop import RunwayTaskPoller
    from download_succeeded_videos import VideoDownloader
    from batch_report_generator import BatchReportGenerator
    from smartproxy_utils import SmartproxyConfig
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please ensure all pipeline components are available.")
    sys.exit(1)

class VideoGenerationPipeline:
    """Complete video generation pipeline orchestrator."""
    
    def __init__(self, args):
        self.args = args
        self.start_time = datetime.now()
        self.timestamp = self.start_time.strftime('%Y%m%d_%H%M%S')
        self.pipeline_id = f"pipeline_{self.timestamp}"
        
        # Pipeline state tracking
        self.state = {
            'phase': 'initialization',
            'images_selected': 0,
            'tasks_created': 0,
            'tasks_completed': 0,
            'videos_downloaded': 0,
            'errors': [],
            'warnings': []
        }
        
        # Output directories
        self.video_queue_dir = Path("video_queue")
        self.video_outputs_dir = Path("video_outputs")
        self.logs_dir = Path("logs")
        self.logs_dir.mkdir(exist_ok=True)
        
        # Log file for this pipeline run
        self.log_file = self.logs_dir / f"pipeline_{self.timestamp}.log"
        
    def log(self, message: str, level: str = "INFO"):
        """Log message to both console and file."""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_message = f"[{timestamp}] {level}: {message}"
        
        # Print to console
        if level == "ERROR":
            print(f"❌ {message}")
        elif level == "WARNING":
            print(f"⚠️ {message}")
        elif level == "SUCCESS":
            print(f"✅ {message}")
        else:
            print(f"ℹ️ {message}")
        
        # Write to log file
        try:
            with open(self.log_file, 'a') as f:
                f.write(log_message + "\n")
        except Exception:
            pass  # Don't fail pipeline if logging fails
    
    def validate_environment(self) -> bool:
        """Validate required environment variables and dependencies."""
        self.log("🔍 Validating environment...")
        self.state['phase'] = 'environment_validation'
        
        validation_errors = []
        validation_warnings = []
        
        # Required environment variables
        required_env_vars = {
            'RUNWAYML_API_SECRET': 'RunwayML API key for video generation'
        }
        
        # Optional environment variables (for Smartproxy)
        optional_env_vars = {
            'SMARTPROXY_USERNAME': 'Smartproxy username for enhanced reliability',
            'SMARTPROXY_PASSWORD': 'Smartproxy password',
            'SMARTPROXY_AUTH_TOKEN': 'Smartproxy authentication token'
        }
        
        # Check required variables
        for var, description in required_env_vars.items():
            if not os.getenv(var):
                validation_errors.append(f"Missing required environment variable: {var} ({description})")
            else:
                self.log(f"✓ Found required environment variable: {var}")
        
        # Check optional variables (Smartproxy)
        smartproxy_vars = [var for var in optional_env_vars.keys() if os.getenv(var)]
        if len(smartproxy_vars) == len(optional_env_vars):
            self.log("✓ Smartproxy configuration detected - enhanced reliability enabled")
            
            # Test Smartproxy connection if credentials are present
            try:
                config = SmartproxyConfig()
                if config.test_connection():
                    self.log("✓ Smartproxy connection test successful")
                else:
                    validation_warnings.append("Smartproxy credentials found but connection test failed")
            except Exception as e:
                validation_warnings.append(f"Smartproxy configuration error: {e}")
        elif smartproxy_vars:
            validation_warnings.append(f"Partial Smartproxy configuration detected ({len(smartproxy_vars)}/{len(optional_env_vars)} variables)")
        else:
            self.log("ℹ️ Smartproxy not configured (optional) - using direct connections")
        
        # Check directory structure
        required_dirs = [self.video_queue_dir, self.video_outputs_dir]
        for directory in required_dirs:
            if not directory.exists():
                try:
                    directory.mkdir(exist_ok=True)
                    self.log(f"✓ Created directory: {directory}")
                except Exception as e:
                    validation_errors.append(f"Cannot create required directory {directory}: {e}")
            else:
                self.log(f"✓ Directory exists: {directory}")
        
        # Check for images in video_queue
        image_files = list(self.video_queue_dir.glob("*.png"))
        if not image_files:
            validation_errors.append(f"No PNG images found in {self.video_queue_dir}")
        else:
            self.log(f"✓ Found {len(image_files)} images in video queue")
        
        # Validate platform suffix
        valid_platforms = ['ig', 'tt', 'tw']
        if self.args.platform and self.args.platform not in valid_platforms:
            validation_errors.append(f"Invalid platform '{self.args.platform}'. Valid options: {', '.join(valid_platforms)}")
        
        # Report validation results
        for warning in validation_warnings:
            self.log(warning, "WARNING")
            self.state['warnings'].append(warning)
        
        for error in validation_errors:
            self.log(error, "ERROR")
            self.state['errors'].append(error)
        
        if validation_errors:
            self.log(f"Environment validation failed with {len(validation_errors)} errors", "ERROR")
            return False
        
        self.log("Environment validation successful", "SUCCESS")
        return True
    
    def phase_1_image_curation(self) -> List[Tuple[Path, str]]:
        """Phase 1: Load and curate images with intelligent prompts."""
        self.log("🖼️ Phase 1: Image curation and prompt generation...")
        self.state['phase'] = 'image_curation'
        
        try:
            # Load selected images with prompts
            selected_images_with_prompts = load_selected_images_with_prompts(
                video_queue_dir=str(self.video_queue_dir),
                max_images=self.args.max_videos
            )
            
            if not selected_images_with_prompts:
                raise ValueError("No images available for processing")
            
            self.state['images_selected'] = len(selected_images_with_prompts)
            self.log(f"Selected {len(selected_images_with_prompts)} images for video generation", "SUCCESS")
            
            # Log selected images
            for i, (image_path, prompt) in enumerate(selected_images_with_prompts, 1):
                self.log(f"  {i}. {image_path.name} -> {prompt[:60]}...")
            
            return selected_images_with_prompts
        
        except Exception as e:
            error_msg = f"Image curation failed: {e}"
            self.log(error_msg, "ERROR")
            self.state['errors'].append(error_msg)
            raise
    
    def phase_2_task_creation(self, selected_images_with_prompts: List[Tuple[Path, str]]) -> List[Dict]:
        """Phase 2: Create RunwayML video generation tasks."""
        self.log("🚀 Phase 2: Creating RunwayML video generation tasks...")
        self.state['phase'] = 'task_creation'
        
        try:
            # Initialize video generator
            generator = IntelligentVideoGenerator()
            
            # Create tasks
            task_queue = generator.kick_off_image_to_video_tasks(
                selected_images_with_prompts,
                max_videos=self.args.max_videos
            )
            
            if not task_queue:
                raise ValueError("No tasks were created")
            
            # Count successful tasks
            successful_tasks = [item for item in task_queue if item.get('task_id')]
            failed_tasks = [item for item in task_queue if not item.get('task_id')]
            
            self.state['tasks_created'] = len(successful_tasks)
            
            if failed_tasks:
                warning_msg = f"{len(failed_tasks)} tasks failed to create"
                self.log(warning_msg, "WARNING")
                self.state['warnings'].append(warning_msg)
            
            self.log(f"Successfully created {len(successful_tasks)} tasks", "SUCCESS")
            
            # Save task queue for polling
            task_queue_file = f"task_queue_{self.timestamp}.json"
            with open(task_queue_file, 'w') as f:
                json.dump(task_queue, f, indent=2)
            
            self.log(f"Task queue saved to: {task_queue_file}")
            
            return task_queue
        
        except Exception as e:
            error_msg = f"Task creation failed: {e}"
            self.log(error_msg, "ERROR")
            self.state['errors'].append(error_msg)
            raise
    
    def phase_3_task_polling(self, task_queue: List[Dict]) -> str:
        """Phase 3: Poll tasks until completion."""
        self.log("⏳ Phase 3: Polling tasks until completion...")
        self.state['phase'] = 'task_polling'
        
        try:
            # Initialize poller
            poller = RunwayTaskPoller(
                poll_interval_range=(8, 10),
                global_timeout=self.args.timeout
            )
            
            # Save temporary task queue file for poller
            temp_queue_file = f"temp_task_queue_{self.timestamp}.json"
            with open(temp_queue_file, 'w') as f:
                json.dump(task_queue, f, indent=2)
            
            # Load and poll tasks
            loaded_queue = poller.load_task_queue(temp_queue_file)
            completed_tasks = poller.poll_task_queue(
                loaded_queue,
                save_results=True,
                output_file=f"runway_polling_results_{self.timestamp}.json"
            )
            
            # Clean up temp file
            try:
                os.remove(temp_queue_file)
            except Exception:
                pass
            
            self.state['tasks_completed'] = len(completed_tasks)
            
            # Report polling results
            succeeded_count = sum(1 for task in completed_tasks if task.get('final_status') == 'SUCCEEDED')
            failed_count = sum(1 for task in completed_tasks if task.get('final_status') == 'FAILED')
            
            self.log(f"Polling completed: {succeeded_count} succeeded, {failed_count} failed", "SUCCESS")
            
            if failed_count > 0:
                warning_msg = f"{failed_count} tasks failed during processing"
                self.log(warning_msg, "WARNING")
                self.state['warnings'].append(warning_msg)
            
            results_file = f"runway_polling_results_{self.timestamp}.json"
            self.log(f"Polling results saved to: {results_file}")
            
            return results_file
        
        except Exception as e:
            error_msg = f"Task polling failed: {e}"
            self.log(error_msg, "ERROR")
            self.state['errors'].append(error_msg)
            raise
    
    def phase_4_video_download(self, results_file: str) -> int:
        """Phase 4: Download completed videos."""
        self.log("📥 Phase 4: Downloading completed videos...")
        self.state['phase'] = 'video_download'
        
        try:
            # Initialize downloader
            downloader = VideoDownloader(output_dir=str(self.video_outputs_dir))
            
            # Load polling results
            polling_results = downloader.load_polling_results(Path(results_file))
            if not polling_results:
                raise ValueError(f"Could not load polling results from {results_file}")
            
            # Get succeeded tasks
            succeeded_tasks = downloader.get_succeeded_tasks(polling_results)
            
            if not succeeded_tasks:
                self.log("No succeeded tasks found for download", "WARNING")
                return 0
            
            self.log(f"Found {len(succeeded_tasks)} succeeded tasks to download")
            
            # Download videos
            downloaded_count = 0
            for i, task in enumerate(succeeded_tasks, 1):
                self.log(f"Downloading video {i}/{len(succeeded_tasks)}...")
                
                if downloader.process_succeeded_task(task):
                    downloaded_count += 1
                else:
                    warning_msg = f"Failed to download video for task {task.get('task_id', 'unknown')}"
                    self.log(warning_msg, "WARNING")
                    self.state['warnings'].append(warning_msg)
            
            self.state['videos_downloaded'] = downloaded_count
            
            # Report download stats
            self.log(f"Video download stats:", "SUCCESS")
            self.log(f"  Downloaded: {downloader.stats['downloaded']}")
            self.log(f"  Already existed: {downloader.stats['already_exists']}")
            self.log(f"  Failed downloads: {downloader.stats['failed_downloads']}")
            
            return downloaded_count
        
        except Exception as e:
            error_msg = f"Video download failed: {e}"
            self.log(error_msg, "ERROR")
            self.state['errors'].append(error_msg)
            raise
    
    def phase_5_batch_reporting(self, results_file: str) -> str:
        """Phase 5: Generate comprehensive batch report."""
        self.log("📊 Phase 5: Generating batch report and metrics...")
        self.state['phase'] = 'batch_reporting'
        
        try:
            # Initialize report generator
            report_generator = BatchReportGenerator(output_dir=str(self.video_outputs_dir))
            
            # Load polling results
            polling_results = report_generator.load_polling_results(Path(results_file))
            if not polling_results:
                raise ValueError(f"Could not load polling results from {results_file}")
            
            # Calculate metrics
            metrics = report_generator.calculate_batch_metrics(polling_results)
            
            # Save batch report
            report_path = report_generator.save_batch_report(metrics, Path(results_file))
            
            # Print summary
            batch_summary = metrics['batch_summary']
            perf_metrics = metrics['performance_metrics']
            download_metrics = metrics['download_metrics']
            
            self.log("📈 Batch Report Summary:", "SUCCESS")
            self.log(f"  Total tasks: {batch_summary['total']}")
            self.log(f"  Succeeded: {batch_summary['succeeded']}")
            self.log(f"  Failed: {batch_summary['failed']}")
            self.log(f"  Success rate: {perf_metrics['success_rate_percent']}%")
            self.log(f"  Total duration: {batch_summary['elapsed_formatted']}")
            self.log(f"  Videos downloaded: {download_metrics['videos_downloaded']}")
            self.log(f"  Total storage: {download_metrics['total_storage_mb']} MB")
            
            self.log(f"Batch report saved to: {report_path}")
            
            return str(report_path)
        
        except Exception as e:
            error_msg = f"Batch reporting failed: {e}"
            self.log(error_msg, "ERROR")
            self.state['errors'].append(error_msg)
            raise
    
    def save_pipeline_state(self):
        """Save final pipeline state and summary."""
        pipeline_duration = datetime.now() - self.start_time
        
        final_state = {
            'pipeline_id': self.pipeline_id,
            'start_time': self.start_time.isoformat(),
            'end_time': datetime.now().isoformat(),
            'duration_seconds': pipeline_duration.total_seconds(),
            'duration_formatted': f"{pipeline_duration.total_seconds():.1f}s",
            'arguments': vars(self.args),
            'final_state': self.state,
            'log_file': str(self.log_file)
        }
        
        # Save pipeline state
        state_file = self.logs_dir / f"pipeline_state_{self.timestamp}.json"
        with open(state_file, 'w') as f:
            json.dump(final_state, f, indent=2)
        
        self.log(f"Pipeline state saved to: {state_file}")
        return final_state
    
    def run(self) -> bool:
        """Execute the complete video generation pipeline."""
        self.log(f"🎬 Starting Video Generation Pipeline - {self.pipeline_id}")
        self.log("=" * 70)
        
        try:
            # Phase 0: Environment validation
            if not self.args.skip_validation:
                if not self.validate_environment():
                    return False
            else:
                self.log("⚠️ Skipping environment validation as requested", "WARNING")
            
            # Check for dry run
            if self.args.dry_run:
                self.log("🧪 DRY RUN mode - pipeline would execute the following phases:")
                self.log("  1. Image curation and prompt generation")
                self.log("  2. RunwayML task creation")
                self.log("  3. Task polling and monitoring")
                self.log("  4. Video download and organization")
                self.log("  5. Batch reporting and metrics")
                self.log("DRY RUN completed - no actual work performed", "SUCCESS")
                return True
            
            # Phase 1: Image curation
            selected_images_with_prompts = self.phase_1_image_curation()
            
            # Phase 2: Task creation
            task_queue = self.phase_2_task_creation(selected_images_with_prompts)
            
            # Phase 3: Task polling
            results_file = self.phase_3_task_polling(task_queue)
            
            # Phase 4: Video download
            downloaded_count = self.phase_4_video_download(results_file)
            
            # Phase 5: Batch reporting
            report_path = self.phase_5_batch_reporting(results_file)
            
            # Final summary
            self.log("🎉 PIPELINE COMPLETED SUCCESSFULLY!", "SUCCESS")
            self.log("=" * 70)
            self.log(f"📊 Final Summary:")
            self.log(f"  Images processed: {self.state['images_selected']}")
            self.log(f"  Tasks created: {self.state['tasks_created']}")
            self.log(f"  Tasks completed: {self.state['tasks_completed']}")
            self.log(f"  Videos downloaded: {self.state['videos_downloaded']}")
            self.log(f"  Warnings: {len(self.state['warnings'])}")
            self.log(f"  Errors: {len(self.state['errors'])}")
            
            pipeline_duration = datetime.now() - self.start_time
            self.log(f"  Total duration: {pipeline_duration.total_seconds():.1f}s")
            
            return True
        
        except Exception as e:
            self.log(f"Pipeline failed with error: {e}", "ERROR")
            return False
        
        finally:
            # Always save pipeline state
            self.save_pipeline_state()

def create_cron_job():
    """Create a cron job entry for nightly pipeline execution."""
    cron_command = f"0 2 * * * cd {os.getcwd()} && python generate_videos.py --max_videos 10 --platform ig >> logs/nightly_pipeline.log 2>&1"
    
    print("📅 To set up nightly execution, add this cron job:")
    print("\nRun: crontab -e")
    print("Add this line:")
    print(cron_command)
    print("\nThis will run the pipeline every night at 2 AM with 10 videos for Instagram.")
    print("\nAlternatively, use the provided GitHub Actions workflow for cloud-based scheduling.")

def main():
    parser = argparse.ArgumentParser(
        description="Complete Video Generation Pipeline CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate_videos.py --max_videos 10 --platform ig
  python generate_videos.py --max_videos 5 --platform tt --timeout 900
  python generate_videos.py --platform tw --skip-validation --dry-run
  python generate_videos.py --setup-cron

Environment Variables Required:
  RUNWAYML_API_SECRET    - RunwayML API key for video generation

Environment Variables Optional (Smartproxy):
  SMARTPROXY_USERNAME    - Smartproxy username for enhanced reliability
  SMARTPROXY_PASSWORD    - Smartproxy password
  SMARTPROXY_AUTH_TOKEN  - Smartproxy authentication token
        """
    )
    
    parser.add_argument(
        "--max_videos",
        type=int,
        default=10,
        help="Maximum number of videos to generate (default: 10)"
    )
    
    parser.add_argument(
        "--platform",
        choices=['ig', 'tt', 'tw'],
        default='ig',
        help="Target platform: ig (Instagram), tt (TikTok), tw (Twitter) (default: ig)"
    )
    
    parser.add_argument(
        "--timeout",
        type=int,
        default=600,
        help="Global timeout for task polling in seconds (default: 600 = 10 minutes)"
    )
    
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Skip environment validation (not recommended)"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be executed without actually running the pipeline"
    )
    
    parser.add_argument(
        "--setup-cron",
        action="store_true",
        help="Show instructions for setting up nightly cron job"
    )
    
    args = parser.parse_args()
    
    # Handle cron setup
    if args.setup_cron:
        create_cron_job()
        return
    
    # Create and run pipeline
    pipeline = VideoGenerationPipeline(args)
    success = pipeline.run()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()

