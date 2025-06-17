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
        self.log_file = "watermark_workflow.log"
        
    def log(self, message: str, level="INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_msg = f"[{timestamp}] {level}: {message}"
        print(log_msg)
        
        with open(self.log_file, "a") as f:
            f.write(log_msg + "\n")
    
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
            self.log("Warning: Could not get git tracked files", "WARN")
            return set()
    
    def watermark_new_images(self) -> List[str]:
        """Apply watermarks to images that don't have them yet"""
        self.log("Starting watermark application process")
        
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
                self.log(f"Watermarking: {img_path}")
                result_path = add_logo_watermark(
                    str(img_path), 
                    self.watermark_path, 
                    self.platform, 
                    opacity=0.92, 
                    scale_factor=0.15
                )
                watermarked_files.append(result_path)
                self.log(f"✓ Watermarked: {result_path}")
            except Exception as e:
                self.log(f"✗ Error watermarking {img_path}: {e}", "ERROR")
        
        self.log(f"Watermarked {len(watermarked_files)} images")
        return watermarked_files
    
    def cleanup_non_watermarked(self) -> List[str]:
        """Remove non-watermarked images locally and from git"""
        self.log("Starting cleanup of non-watermarked images")
        
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
                    self.log(f"Removing non-watermarked: {img_path}")
                    
                    # Remove from git if tracked
                    try:
                        subprocess.run(["git", "rm", str(img_path)], 
                                     capture_output=True, check=True)
                        self.log(f"✓ Removed from git: {img_path}")
                    except subprocess.CalledProcessError:
                        # File might not be tracked, just remove locally
                        img_path.unlink()
                        self.log(f"✓ Removed locally: {img_path}")
                    
                    removed_files.append(str(img_path))
                    
            except Exception as e:
                self.log(f"✗ Error removing {img_path}: {e}", "ERROR")
        
        self.log(f"Cleaned up {len(removed_files)} non-watermarked images")
        return removed_files
    
    def check_git_sync(self) -> Dict[str, any]:
        """Check git sync status and identify cleanup opportunities"""
        self.log("Checking git sync status")
        
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
            self.log(f"Git sync check failed: {e}", "ERROR")
        
        return sync_info
    
    def sync_and_cleanup_remote(self, force=False) -> bool:
        """Sync changes and cleanup remote repository"""
        self.log("Starting git sync and remote cleanup")
        
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
                self.log("✓ Committed watermark changes")
                
                # Push changes
                subprocess.run(["git", "push"], check=True)
                self.log("✓ Pushed changes to remote")
                
                return True
            else:
                self.log("No changes to commit")
                return False
                
        except subprocess.CalledProcessError as e:
            self.log(f"Git sync failed: {e}", "ERROR")
            return False
    
    def run_full_workflow(self) -> Dict[str, any]:
        """Run the complete watermarking and cleanup workflow"""
        self.log("=== STARTING FULL WATERMARK WORKFLOW ===")
        
        results = {
            "watermarked_files": [],
            "removed_files": [],
            "git_synced": False,
            "sync_info": {},
            "errors": []
        }
        
        try:
            # Step 1: Watermark new images
            results["watermarked_files"] = self.watermark_new_images()
            
            # Step 2: Cleanup non-watermarked images
            results["removed_files"] = self.cleanup_non_watermarked()
            
            # Step 3: Check git sync
            results["sync_info"] = self.check_git_sync()
            
            # Step 4: Sync to remote
            results["git_synced"] = self.sync_and_cleanup_remote()
            
            self.log("=== WORKFLOW COMPLETED SUCCESSFULLY ===")
            
        except Exception as e:
            error_msg = f"Workflow error: {e}"
            self.log(error_msg, "ERROR")
            results["errors"].append(error_msg)
        
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
        print(f"  Watermarked: {len(results['watermarked_files'])} files")
        print(f"  Cleaned up: {len(results['removed_files'])} files")
        print(f"  Git synced: {results['git_synced']}")
        if results["errors"]:
            print(f"  Errors: {len(results['errors'])}")

if __name__ == "__main__":
    main()

