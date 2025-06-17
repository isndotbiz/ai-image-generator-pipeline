#!/usr/bin/env python3
"""
File Classification Module - Step 3: Classify files into keep vs delete lists

Iterates over gathered paths, applies should_keep(), appends to keep or delete lists,
and builds statistics (counts per sub-folder, total).
"""

import os
from collections import defaultdict
from pathlib import Path
from typing import List, Dict, Tuple


def should_keep(file_path: str) -> bool:
    """
    Determine whether a file should be kept or deleted.
    
    This is a placeholder implementation - customize based on your needs.
    
    Args:
        file_path: Path to the file to evaluate
        
    Returns:
        True if file should be kept, False if it should be deleted
    """
    # Example criteria - customize as needed:
    path = Path(file_path)
    
    # Keep if it's a source code file
    if path.suffix in ['.py', '.js', '.html', '.css', '.md']:
        return True
    
    # Delete temporary files
    if path.name.startswith('temp_') or path.suffix in ['.tmp', '.log']:
        return False
    
    # Keep configuration files
    if path.name in ['config.json', 'requirements.txt', '.gitignore']:
        return True
    
    # Default: keep
    return True


def classify_files(gathered_paths: List[str]) -> Tuple[List[str], List[str], Dict[str, Dict[str, int]]]:
    """
    Classify files into keep vs delete lists and build statistics.
    
    Args:
        gathered_paths: List of file paths to classify
        
    Returns:
        Tuple containing:
        - keep_list: Files to keep
        - delete_list: Files to delete
        - statistics: Dict with counts per sub-folder and totals
    """
    keep_list = []
    delete_list = []
    
    # Statistics tracking
    subfolder_stats = defaultdict(lambda: {'keep': 0, 'delete': 0, 'total': 0})
    total_stats = {'keep': 0, 'delete': 0, 'total': 0}
    
    print(f"Classifying {len(gathered_paths)} files...")
    
    for file_path in gathered_paths:
        # Apply should_keep() function
        if should_keep(file_path):
            keep_list.append(file_path)
            action = 'keep'
        else:
            delete_list.append(file_path)
            action = 'delete'
        
        # Get subfolder for statistics
        path_obj = Path(file_path)
        if path_obj.parent == Path('.'):
            subfolder = 'root'
        else:
            # Use the first directory in the path as subfolder
            parts = path_obj.parts
            subfolder = parts[0] if len(parts) > 1 else 'root'
        
        # Update statistics
        subfolder_stats[subfolder][action] += 1
        subfolder_stats[subfolder]['total'] += 1
        total_stats[action] += 1
        total_stats['total'] += 1
    
    return keep_list, delete_list, dict(subfolder_stats), total_stats


def print_statistics(subfolder_stats: Dict[str, Dict[str, int]], total_stats: Dict[str, int]):
    """
    Print classification statistics in a readable format.
    
    Args:
        subfolder_stats: Statistics per subfolder
        total_stats: Overall statistics
    """
    print("\n" + "="*60)
    print("FILE CLASSIFICATION STATISTICS")
    print("="*60)
    
    print("\nPer Sub-folder:")
    print("-" * 40)
    for subfolder, stats in sorted(subfolder_stats.items()):
        print(f"{subfolder:20} | Keep: {stats['keep']:4d} | Delete: {stats['delete']:4d} | Total: {stats['total']:4d}")
    
    print("-" * 40)
    print(f"{'TOTAL':20} | Keep: {total_stats['keep']:4d} | Delete: {total_stats['delete']:4d} | Total: {total_stats['total']:4d}")
    print("="*60)


def main():
    """
    Main function to demonstrate file classification.
    """
    # Example: gather paths from current directory (you would replace this with your actual gathered paths)
    gathered_paths = []
    
    # Gather all files in current directory and subdirectories
    for root, dirs, files in os.walk('.'):
        for file in files:
            file_path = os.path.join(root, file)
            # Skip hidden files and directories
            if not any(part.startswith('.') for part in Path(file_path).parts[1:]):
                gathered_paths.append(file_path)
    
    # Step 3: Classify files into keep vs delete lists
    keep_list, delete_list, subfolder_stats, total_stats = classify_files(gathered_paths)
    
    # Print results
    print(f"\nClassification Results:")
    print(f"Files to KEEP: {len(keep_list)}")
    print(f"Files to DELETE: {len(delete_list)}")
    
    # Print statistics
    print_statistics(subfolder_stats, total_stats)
    
    # Optionally, show first few files in each category
    print("\nSample files to KEEP:")
    for file_path in keep_list[:5]:
        print(f"  {file_path}")
    if len(keep_list) > 5:
        print(f"  ... and {len(keep_list) - 5} more")
    
    print("\nSample files to DELETE:")
    for file_path in delete_list[:5]:
        print(f"  {file_path}")
    if len(delete_list) > 5:
        print(f"  ... and {len(delete_list) - 5} more")
    
    return keep_list, delete_list, subfolder_stats, total_stats


if __name__ == "__main__":
    main()

