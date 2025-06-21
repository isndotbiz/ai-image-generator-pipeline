#!/usr/bin/env python3
"""
Automated Watermarking and Git Cleanup Workflow

This script provides:
1. Automatic watermarking of new images
2. Cleanup of non-watermarked images
3. Git sync checking and remote cleanup
4. Integration with image generation pipeline

Usage:
    python3 auto_watermark_workflow.py --mode [watermark|cleanup|sync-check|full]
    
Modes:
    watermark   - Apply watermarks to new images only
    cleanup     - Remove non-watermarked images locally and from git
    sync-check  - Check git sync status and clean remote if needed
    full        - Run complete workflow (watermark + cleanup + sync)
"""

import os
import sys
import argparse
import subprocess
import json
from pathlib import Path
from typing import List, Dict, Set
from datetime import datetime
from logging_config import get_logger

# Import our watermarking functions
try:
    from watermark import add_logo_watermark, Platform
except ImportError:
    print("Error: watermark.py module not found. Make sure it's in the same directory.")
    sys.exit(1)

class WatermarkWorkflow:
    def __init__(self, watermark_path="Fortuna_Bound_Watermark.png", 
                 images_dir="images", platform="generic"):
        self.watermark_path = watermark_path
        self.images_dir = Path(images_dir)
        self.platform = Platform.GENERIC
        self.logger = get_logger(__name__ + ".WatermarkWorkflow")
    
    def find_images(self, include_watermarked=True) -> List[Path]:
        """Find all image files in the images directory"""
        extensions = ["*.png", "*.jpg", "*.jpeg", "*.PNG", "*.JPG", "*.JPEG"]
        images = []
        
        for ext in extensions:
            images.extend(self.images_dir.rglob(ext))
        
        # Filter out watermark files themselves
        images = [img for img in images if "Fortuna_Bound_Watermark" not in str(img)]
        
        if not include_watermarked:
            images = [img for img in images if "_watermarked" not in str(img)]
            
        return sorted(images)
    
    def get_git_tracked_files(self) -> Set[str]:
        """Get list of files tracked by git"""
        try:
            result = subprocess.run(["git", "ls-files"], 
                                  capture_output=True, text=True, check=True)
            return set(result.stdout.strip().split("\n"))
        except subprocess.CalledProcessError:
            self.logger.warning("Could not get git tracked files")
            return set()
    
    def watermark_new_images(self) -> List[str]:
        """Apply watermarks to images that don't have them yet"""
        self.logger.info("Starting watermark application process")
        
        # Find non-watermarked images
        all_images = self.find_images(include_watermarked=True)
        watermarked_images = {str(img) for img in all_images if "_watermarked" in str(img)}
        
        # Find base names of watermarked images
        watermarked_base_names = set()
        for wm_img in watermarked_images:
            base_name = wm_img.replace("_watermarked", "")
            watermarked_base_names.add(base_name)
        
        # Find images that need watermarking
        images_to_watermark = []
        for img in all_images:
            if "_watermarked" not in str(img):
                # Check if watermarked version doesn't exist
                base_path = str(img).replace(".png", "").replace(".jpg", "").replace(".jpeg", "")
                watermarked_path = base_path + "_watermarked.png"
                if watermarked_path not in watermarked_images:
                    images_to_watermark.append(img)
        
        # Apply watermarks
        watermarked_files = []
        for img_path in images_to_watermark:
            try:
                self.logger.info(f"Watermarking: {img_path}")
                result_path = add_logo_watermark(
                    str(img_path), 
                    self.watermark_path, 
                    self.platform, 
                    opacity=0.92, 
                    scale_factor=0.15
                )
                watermarked_files.append(result_path)
                self.logger.info(f"✓ Watermarked: {result_path}")
            except Exception as e:
                self.logger.error(f"✗ Error watermarking {img_path}: {e}")
        
        self.logger.info(f"Watermarked {len(watermarked_files)} images")
        return watermarked_files
    
    def cleanup_non_watermarked(self) -> List[str]:
        """Remove non-watermarked images locally and from git"""
        self.logger.info("Starting cleanup of non-watermarked images")
        
        # Find non-watermarked images
        non_watermarked = self.find_images(include_watermarked=False)
        removed_files = []
        
        for img_path in non_watermarked:
            try:
                # Check if there's a watermarked version
                base_path = str(img_path).replace(".png", "").replace(".jpg", "").replace(".jpeg", "")
                watermarked_variants = [
                    base_path + "_watermarked.png",
                    base_path + "_watermarked.jpg",
                    base_path + "_watermarked.jpeg"
                ]
                
                has_watermarked_version = any(Path(wm).exists() for wm in watermarked_variants)
                
                if has_watermarked_version:
                    self.logger.info(f"Removing non-watermarked: {img_path}")
                    
                    # Remove from git if tracked
                    try:
                        subprocess.run(["git", "rm", str(img_path)], 
                                     capture_output=True, check=True)
                        self.logger.info(f"✓ Removed from git: {img_path}")
                    except subprocess.CalledProcessError:
                        # File might not be tracked, just remove locally
                        img_path.unlink()
                        self.logger.info(f"✓ Removed locally: {img_path}")
                    
                    removed_files.append(str(img_path))
                    
            except Exception as e:
                self.logger.error(f"✗ Error removing {img_path}: {e}")
        
        self.logger.info(f"Cleaned up {len(removed_files)} non-watermarked images")
        return removed_files
    
    def check_git_sync(self) -> Dict[str, any]:
        """Check git sync status and identify cleanup opportunities"""
        self.logger.info("Checking git sync status")
        
        sync_info = {
            "local_changes": [],
            "remote_behind": False,
            "remote_ahead": False,
            "untracked_images": [],
            "missing_local_images": []
        }
        
        try:
            # Check for local changes
            result = subprocess.run(["git", "status", "--porcelain"], 
                                  capture_output=True, text=True, check=True)
            if result.stdout.strip():
                sync_info["local_changes"] = result.stdout.strip().split("\n")
            
            # Check remote sync status
            subprocess.run(["git", "fetch"], capture_output=True, check=True)
            
            # Check if local is behind remote
            result = subprocess.run(["git", "rev-list", "HEAD..origin/main"], 
                                  capture_output=True, text=True, check=True)
            if result.stdout.strip():
                sync_info["remote_ahead"] = True
            
            # Check if local is ahead of remote  
            result = subprocess.run(["git", "rev-list", "origin/main..HEAD"], 
                                  capture_output=True, text=True, check=True)
            if result.stdout.strip():
                sync_info["remote_behind"] = True
            
            # Find untracked images
            git_tracked = self.get_git_tracked_files()
            local_images = self.find_images()
            
            for img in local_images:
                try:
                    rel_path = str(img.relative_to(Path.cwd()))
                    if rel_path not in git_tracked:
                        sync_info["untracked_images"].append(rel_path)
                except ValueError:
                    # Handle images outside current directory
                    abs_path = str(img.resolve())
                    if abs_path not in git_tracked:
                        sync_info["untracked_images"].append(abs_path)
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Git sync check failed: {e}")
        
        return sync_info
    
    def sync_and_cleanup_remote(self, force=False) -> bool:
        """Sync changes and cleanup remote repository"""
        self.logger.info("Starting git sync and remote cleanup")
        
        try:
            # Add all watermarked images
            subprocess.run(["git", "add", "images/"], check=True)
            
            # Check if there are changes to commit
            result = subprocess.run(["git", "diff", "--cached", "--name-only"], 
                                  capture_output=True, text=True, check=True)
            
            if result.stdout.strip():
                # Commit changes
                commit_msg = f"Automated watermark workflow - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                subprocess.run(["git", "commit", "-m", commit_msg], check=True)
                self.logger.info("✓ Committed watermark changes")
                
                # Push changes
                subprocess.run(["git", "push"], check=True)
                self.logger.info("✓ Pushed changes to remote")
                
                return True
            else:
                self.logger.info("No changes to commit")
                return False
                
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Git sync failed: {e}")
            return False
    
    def detect_double_text_images(self) -> List[str]:
        """Detect and remove images that may have double text overlays"""
        self.logger.info("Scanning for double-text images")
        
        double_text_images = []
        all_images = self.find_images(include_watermarked=True)
        
        # Simple heuristic: look for images with "_text" or "_overlay" in filename
        # or images that are suspiciously large (indicating multiple overlays)
        for img_path in all_images:
            try:
                # Check filename patterns that might indicate double text
                filename = str(img_path).lower()
                suspicious_patterns = ['_text_', '_overlay_', '_double_', '_dup_']
                
                if any(pattern in filename for pattern in suspicious_patterns):
                    double_text_images.append(str(img_path))
                    self.logger.info(f"Found suspicious double-text image: {img_path}")
                    
                # You could add more sophisticated detection here
                # such as checking file size or using image analysis
                    
            except Exception as e:
                self.logger.error(f"Error checking image {img_path}: {e}")
        
        # Remove detected double-text images
        removed_count = 0
        for img_path in double_text_images:
            try:
                Path(img_path).unlink()
                removed_count += 1
                self.logger.info(f"✓ Removed double-text image: {img_path}")
            except Exception as e:
                self.logger.error(f"✗ Failed to remove {img_path}: {e}")
        
        self.logger.info(f"Removed {removed_count} double-text images")
        return double_text_images
    
    def run_full_workflow(self) -> Dict[str, any]:
        """Run the complete watermarking and cleanup workflow"""
        start_time = datetime.now()
        self.logger.info("=== STARTING FULL WATERMARK WORKFLOW ===")
        self.logger.info(f"Workflow started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Initialize comprehensive metrics
        results = {
            "workflow_start_time": start_time.isoformat(),
            "total_images_processed": 0,
            "watermarked_files": [],
            "originals_deleted": [],
            "double_text_images_removed": [],
            "git_synced": False,
            "sync_info": {},
            "errors": [],
            "metrics": {
                "total_images_found": 0,
                "watermarked_count": 0,
                "originals_deleted_count": 0,
                "double_text_removed_count": 0,
                "processing_time_seconds": 0
            }
        }
        
        try:
            # Count total images at start
            all_images = self.find_images(include_watermarked=True)
            results["metrics"]["total_images_found"] = len(all_images)
            self.logger.info(f"Found {len(all_images)} total images to process")
            
            # Step 1: Watermark new images
            self.logger.info("--- STEP 1: WATERMARKING NEW IMAGES ---")
            results["watermarked_files"] = self.watermark_new_images()
            results["metrics"]["watermarked_count"] = len(results["watermarked_files"])
            
            # Step 2: Cleanup non-watermarked images (originals)
            self.logger.info("--- STEP 2: CLEANING UP ORIGINAL IMAGES ---")
            results["originals_deleted"] = self.cleanup_non_watermarked()
            results["metrics"]["originals_deleted_count"] = len(results["originals_deleted"])
            
            # Step 3: Detect and remove double-text images
            self.logger.info("--- STEP 3: REMOVING DOUBLE-TEXT IMAGES ---")
            results["double_text_images_removed"] = self.detect_double_text_images()
            results["metrics"]["double_text_removed_count"] = len(results["double_text_images_removed"])
            
            # Step 4: Check git sync
            self.logger.info("--- STEP 4: CHECKING GIT SYNC STATUS ---")
            results["sync_info"] = self.check_git_sync()
            
            # Step 5: Sync to remote
            self.logger.info("--- STEP 5: SYNCING TO REMOTE ---")
            results["git_synced"] = self.sync_and_cleanup_remote()
            
            # Calculate total processed
            results["total_images_processed"] = (
                results["metrics"]["watermarked_count"] + 
                results["metrics"]["originals_deleted_count"] + 
                results["metrics"]["double_text_removed_count"]
            )
            
            # Calculate processing time
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            results["metrics"]["processing_time_seconds"] = processing_time
            results["workflow_end_time"] = end_time.isoformat()
            
            # Log comprehensive summary
            self.logger.info("=== WORKFLOW METRICS SUMMARY ===")
            self.logger.info(f"Total images found: {results['metrics']['total_images_found']}")
            self.logger.info(f"Total images processed: {results['total_images_processed']}")
            self.logger.info(f"Number of watermarked files: {results['metrics']['watermarked_count']}")
            self.logger.info(f"Number of originals deleted: {results['metrics']['originals_deleted_count']}")
            self.logger.info(f"Number of double-text images removed: {results['metrics']['double_text_removed_count']}")
            self.logger.info(f"Git synced successfully: {results['git_synced']}")
            self.logger.info(f"Processing time: {processing_time:.2f} seconds")
            self.logger.info(f"Workflow completed at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            self.logger.info("=== WORKFLOW COMPLETED SUCCESSFULLY ===")
            
        except Exception as e:
            error_msg = f"Workflow error: {e}"
            self.logger.error(error_msg)
            results["errors"].append(error_msg)
            
            # Still calculate processing time on error
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            results["metrics"]["processing_time_seconds"] = processing_time
            results["workflow_end_time"] = end_time.isoformat()
        
        return results

def main():
    parser = argparse.ArgumentParser(description="Automated Watermarking Workflow")
    parser.add_argument("--mode", choices=["watermark", "cleanup", "sync-check", "full"], 
                       default="full", help="Workflow mode to run")
    parser.add_argument("--watermark", default="Fortuna_Bound_Watermark.png", 
                       help="Path to watermark file")
    parser.add_argument("--images-dir", default="images", 
                       help="Images directory path")
    parser.add_argument("--force", action="store_true", 
                       help="Force operations without confirmation")
    
    args = parser.parse_args()
    
    # Initialize workflow
    workflow = WatermarkWorkflow(args.watermark, args.images_dir)
    
    if args.mode == "watermark":
        results = workflow.watermark_new_images()
        print(f"Watermarked {len(results)} images")
        
    elif args.mode == "cleanup":
        results = workflow.cleanup_non_watermarked()
        print(f"Cleaned up {len(results)} images")
        
    elif args.mode == "sync-check":
        results = workflow.check_git_sync()
        print("Git Sync Status:")
        print(json.dumps(results, indent=2))
        
    elif args.mode == "full":
        results = workflow.run_full_workflow()
        print("\nWorkflow Results:")
        print(f"  Total images processed: {results['total_images_processed']}")
        print(f"  Watermarked: {len(results['watermarked_files'])} files")
        print(f"  Originals deleted: {len(results['originals_deleted'])} files")
        print(f"  Double-text images removed: {len(results['double_text_images_removed'])} files")
        print(f"  Git synced: {results['git_synced']}")
        print(f"  Processing time: {results['metrics']['processing_time_seconds']:.2f} seconds")
        if results["errors"]:
            print(f"  Errors: {len(results['errors'])}")

if __name__ == "__main__":
    main()

