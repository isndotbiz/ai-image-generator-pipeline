#!/usr/bin/env python3
"""
File Management Pipeline - Integration of Steps 3 and 5

Integrates file classification (Step 3) with file deletion (Step 5)
to provide a complete file management workflow.
"""

import argparse
from pathlib import Path
from typing import List, Dict, Tuple

# Import our modules
from file_classifier import classify_files, print_statistics
from file_deleter import execute_deletion, print_deletion_summary


def gather_files_from_directory(directory: str = ".", include_hidden: bool = False) -> List[str]:
    """
    Gather all files from a directory for processing.
    
    Args:
        directory: Directory to scan
        include_hidden: Whether to include hidden files
        
    Returns:
        List of file paths
    """
    gathered_paths = []
    
    try:
        for path in Path(directory).rglob('*'):
            if path.is_file():
                # Skip hidden files unless requested
                if not include_hidden and any(part.startswith('.') for part in path.parts):
                    continue
                gathered_paths.append(str(path))
    except PermissionError as e:
        print(f"Permission denied accessing {directory}: {e}")
    except Exception as e:
        print(f"Error scanning directory {directory}: {e}")
    
    return gathered_paths


def run_pipeline(directory: str = ".", soft_delete: bool = False, include_hidden: bool = False, 
                dry_run: bool = False) -> Dict[str, any]:
    """
    Run the complete file management pipeline.
    
    Args:
        directory: Directory to process
        soft_delete: Use soft delete (move to trash)
        include_hidden: Include hidden files in processing
        dry_run: Only classify, don't actually delete
        
    Returns:
        Dictionary with pipeline results
    """
    print("=" * 60)
    print("FILE MANAGEMENT PIPELINE")
    print("=" * 60)
    print(f"Directory: {directory}")
    print(f"Soft delete: {soft_delete}")
    print(f"Include hidden: {include_hidden}")
    print(f"Dry run: {dry_run}")
    print("=" * 60)
    
    # Step 1: Gather files
    print("\nStep 1: Gathering files...")
    gathered_paths = gather_files_from_directory(directory, include_hidden)
    print(f"Found {len(gathered_paths)} files")
    
    if not gathered_paths:
        print("No files found to process.")
        return {'status': 'no_files', 'gathered_paths': []}
    
    # Step 3: Classify files
    print("\nStep 3: Classifying files...")
    keep_list, delete_list, subfolder_stats, total_stats = classify_files(gathered_paths)
    
    # Print classification statistics
    print_statistics(subfolder_stats, total_stats)
    
    # Step 5: Execute deletion (if not dry run)
    deletion_results = None
    if not dry_run:
        if delete_list:
            print("\nStep 5: Executing deletion...")
            deletion_results = execute_deletion(delete_list, soft_delete, directory)
            print_deletion_summary(deletion_results)
        else:
            print("\nStep 5: No files to delete.")
    else:
        print("\nStep 5: Skipped (dry run mode)")
        print(f"Would delete {len(delete_list)} files")
    
    # Compile pipeline results
    pipeline_results = {
        'status': 'completed',
        'directory': directory,
        'gathered_paths': gathered_paths,
        'keep_list': keep_list,
        'delete_list': delete_list,
        'subfolder_stats': subfolder_stats,
        'total_stats': total_stats,
        'deletion_results': deletion_results,
        'dry_run': dry_run,
        'soft_delete': soft_delete
    }
    
    return pipeline_results


def main():
    """
    Main function with command line interface.
    """
    parser = argparse.ArgumentParser(description='File Management Pipeline - Steps 3 & 5')
    parser.add_argument('--directory', '-d', default='.', 
                       help='Directory to process (default: current directory)')
    parser.add_argument('--soft-delete', action='store_true',
                       help='Move files to .trash folder instead of permanent deletion')
    parser.add_argument('--include-hidden', action='store_true',
                       help='Include hidden files in processing')
    parser.add_argument('--dry-run', action='store_true',
                       help='Only classify files, do not actually delete them')
    
    args = parser.parse_args()
    
    # Run the pipeline
    results = run_pipeline(
        directory=args.directory,
        soft_delete=args.soft_delete,
        include_hidden=args.include_hidden,
        dry_run=args.dry_run
    )
    
    # Final summary
    print("\n" + "=" * 60)
    print("PIPELINE COMPLETED")
    print("=" * 60)
    print(f"Status: {results['status']}")
    if results['status'] == 'completed':
        print(f"Files processed: {len(results['gathered_paths'])}")
        print(f"Files to keep: {len(results['keep_list'])}")
        print(f"Files to delete: {len(results['delete_list'])}")
        
        if results['deletion_results']:
            print(f"Successfully deleted: {results['deletion_results']['successful_removals']}")
            print(f"Failed deletions: {results['deletion_results']['failures']}")
    print("=" * 60)
    
    return results


if __name__ == "__main__":
    main()

