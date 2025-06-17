#!/usr/bin/env python3
r"""
Repository Cleanup Script

Deletes:
- *_*.bak files  
- Timestamped JSONs matching regex (20\d{6}_\d{4,6}).*\.json in any folder  
- run_*.tgz, *.log older than 14 days (except pipeline.log*)  
- Extra build artefacts in video_outputs/ and images/ directories

Prompts for confirmation and prints summary.
"""

import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict


def find_files_to_delete() -> Dict[str, List[Path]]:
    """Find all files that match deletion criteria."""
    root_path = Path('.')
    files_to_delete = {
        'bak_files': [],
        'timestamped_jsons': [],
        'old_tgz_files': [],
        'old_log_files': [],
        'video_artifacts': [],
        'image_artifacts': []
    }
    
    # Pattern for timestamped JSONs: (20\d{6}_\d{4,6}).*\.json
    timestamp_pattern = re.compile(r'.*(20\d{6}_\d{4,6}).*\.json$')
    
    # Get cutoff date (14 days ago)
    cutoff_date = datetime.now() - timedelta(days=14)
    
    # Walk through all directories
    for file_path in root_path.rglob('*'):
        if not file_path.is_file():
            continue
            
        filename = file_path.name
        relative_path = file_path.relative_to(root_path)
        
        # Check for *.bak files (all backup files)
        if filename.endswith('.bak'):
            files_to_delete['bak_files'].append(relative_path)
        
        # Check for timestamped JSON files
        if timestamp_pattern.match(filename):
            files_to_delete['timestamped_jsons'].append(relative_path)
        
        # Check for run_*.tgz files older than 14 days
        if filename.startswith('run_') and filename.endswith('.tgz'):
            if file_path.stat().st_mtime < cutoff_date.timestamp():
                files_to_delete['old_tgz_files'].append(relative_path)
        
        # Check for *.log files older than 14 days (except pipeline.log*)
        if (filename.endswith('.log') and 
            not filename.startswith('pipeline.log') and
            file_path.stat().st_mtime < cutoff_date.timestamp()):
            files_to_delete['old_log_files'].append(relative_path)
    
    # Check video_outputs directory for build artifacts
    video_outputs_path = root_path / 'video_outputs'
    if video_outputs_path.exists():
        for file_path in video_outputs_path.iterdir():
            if file_path.is_file():
                filename = file_path.name
                # Remove task queue JSONs and other temp files, but keep actual video outputs
                if (filename.startswith('task_queue_') or 
                    filename.endswith('_temp.json') or
                    filename.endswith('_processing.json')):
                    files_to_delete['video_artifacts'].append(file_path.relative_to(root_path))
    
    # Check images directory for build artifacts
    images_path = root_path / 'images'
    if images_path.exists():
        for file_path in images_path.rglob('*'):
            if file_path.is_file():
                filename = file_path.name
                # Remove analysis reports, rankings, and other temp files
                if (filename.startswith('analysis_report_') or 
                    filename.startswith('image_rankings_') or
                    filename.startswith('video_selection_') or
                    filename.endswith('_temp.json') or
                    filename.endswith('_processing.json')):
                    files_to_delete['image_artifacts'].append(file_path.relative_to(root_path))
    
    return files_to_delete


def print_summary(files_to_delete: Dict[str, List[Path]]) -> None:
    """Print a summary of files to be deleted."""
    total_files = sum(len(file_list) for file_list in files_to_delete.values())
    
    print(f"\n=== Repository Cleanup Summary ===")
    print(f"Total files to delete: {total_files}\n")
    
    for category, file_list in files_to_delete.items():
        if file_list:
            category_name = category.replace('_', ' ').title()
            print(f"{category_name} ({len(file_list)} files):")
            for file_path in sorted(file_list):
                print(f"  - {file_path}")
            print()


def delete_files(files_to_delete: Dict[str, List[Path]]) -> Dict[str, int]:
    """Delete the specified files and return deletion statistics."""
    stats = {
        'deleted': 0,
        'failed': 0,
        'errors': []
    }
    
    for category, file_list in files_to_delete.items():
        for relative_path in file_list:
            file_path = Path('.') / relative_path
            try:
                if file_path.exists():
                    file_path.unlink()
                    stats['deleted'] += 1
                    print(f"Deleted: {relative_path}")
                else:
                    print(f"Warning: File not found: {relative_path}")
            except Exception as e:
                stats['failed'] += 1
                error_msg = f"Failed to delete {relative_path}: {str(e)}"
                stats['errors'].append(error_msg)
                print(f"Error: {error_msg}")
    
    return stats


def main():
    """Main cleanup function."""
    print("Repository Cleanup Script")
    print("=" * 25)
    
    # Find files to delete
    print("Scanning repository for cleanup targets...")
    files_to_delete = find_files_to_delete()
    
    # Print summary
    print_summary(files_to_delete)
    
    # Check if there are any files to delete
    total_files = sum(len(file_list) for file_list in files_to_delete.values())
    if total_files == 0:
        print("No files found matching cleanup criteria.")
        return
    
    # Prompt for confirmation
    try:
        response = input(f"Do you want to delete these {total_files} files? [y/N]: ").strip().lower()
        if response not in ['y', 'yes']:
            print("Cleanup cancelled.")
            return
    except KeyboardInterrupt:
        print("\nCleanup cancelled.")
        return
    
    # Delete files
    print("\nDeleting files...")
    stats = delete_files(files_to_delete)
    
    # Print final summary
    print(f"\n=== Cleanup Complete ===")
    print(f"Files deleted: {stats['deleted']}")
    if stats['failed'] > 0:
        print(f"Failed deletions: {stats['failed']}")
        print("Errors:")
        for error in stats['errors']:
            print(f"  - {error}")
    print("Repository cleanup finished.")


if __name__ == '__main__':
    main()

