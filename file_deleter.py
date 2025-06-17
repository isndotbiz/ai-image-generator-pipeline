#!/usr/bin/env python3
"""
File Deletion Module - Step 5: Execute deletion with safety checks

For each file in delete list:
- Use try/except FileNotFoundError, PermissionError to handle issues
- Optionally move to temporary .trash subfolder before permanent deletion for extra safety (flag --soft-delete)
Maintain a counter of successful removals and failures.
"""

import os
import shutil
import argparse
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime


def create_trash_folder(base_path: str = ".") -> Path:
    """
    Create a .trash subfolder for soft deletion.
    
    Args:
        base_path: Base directory where .trash folder should be created
        
    Returns:
        Path to the .trash folder
    """
    trash_path = Path(base_path) / ".trash"
    trash_path.mkdir(exist_ok=True)
    return trash_path


def safe_delete_file(file_path: str, soft_delete: bool = False, trash_path: Path = None) -> Tuple[bool, str]:
    """
    Safely delete a single file with error handling.
    
    Args:
        file_path: Path to the file to delete
        soft_delete: If True, move to trash instead of permanent deletion
        trash_path: Path to trash folder (required if soft_delete=True)
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        file_path_obj = Path(file_path)
        
        # Check if file exists
        if not file_path_obj.exists():
            return False, f"File not found: {file_path}"
        
        if soft_delete:
            if trash_path is None:
                return False, "Trash path not provided for soft delete"
            
            # Create unique name in trash to avoid conflicts
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            safe_name = f"{file_path_obj.stem}_{timestamp}{file_path_obj.suffix}"
            trash_file_path = trash_path / safe_name
            
            # Move to trash
            shutil.move(str(file_path_obj), str(trash_file_path))
            return True, f"Moved to trash: {file_path} -> {trash_file_path}"
        else:
            # Permanent deletion
            file_path_obj.unlink()
            return True, f"Permanently deleted: {file_path}"
            
    except FileNotFoundError:
        return False, f"File not found during deletion: {file_path}"
    except PermissionError:
        return False, f"Permission denied: {file_path}"
    except OSError as e:
        return False, f"OS error deleting {file_path}: {str(e)}"
    except Exception as e:
        return False, f"Unexpected error deleting {file_path}: {str(e)}"


def execute_deletion(delete_list: List[str], soft_delete: bool = False, base_path: str = ".") -> Dict[str, any]:
    """
    Execute deletion for all files in the delete list with safety checks.
    
    Args:
        delete_list: List of file paths to delete
        soft_delete: If True, move files to .trash folder instead of permanent deletion
        base_path: Base directory for operations
        
    Returns:
        Dictionary with deletion results and statistics
    """
    # Initialize counters
    successful_removals = 0
    failures = 0
    
    # Track results
    success_messages = []
    failure_messages = []
    
    # Create trash folder if needed
    trash_path = None
    if soft_delete:
        trash_path = create_trash_folder(base_path)
        print(f"Created trash folder: {trash_path}")
    
    print(f"\nStarting deletion process for {len(delete_list)} files...")
    print(f"Mode: {'Soft delete (move to trash)' if soft_delete else 'Permanent deletion'}")
    print("-" * 60)
    
    # Process each file
    for i, file_path in enumerate(delete_list, 1):
        print(f"[{i}/{len(delete_list)}] Processing: {file_path}")
        
        success, message = safe_delete_file(file_path, soft_delete, trash_path)
        
        if success:
            successful_removals += 1
            success_messages.append(message)
            print(f"  ✓ {message}")
        else:
            failures += 1
            failure_messages.append(message)
            print(f"  ✗ {message}")
    
    # Compile results
    results = {
        'total_files': len(delete_list),
        'successful_removals': successful_removals,
        'failures': failures,
        'success_rate': (successful_removals / len(delete_list) * 100) if delete_list else 100,
        'soft_delete': soft_delete,
        'trash_path': str(trash_path) if trash_path else None,
        'success_messages': success_messages,
        'failure_messages': failure_messages,
        'timestamp': datetime.now().isoformat()
    }
    
    return results


def print_deletion_summary(results: Dict[str, any]):
    """
    Print a summary of the deletion operation.
    
    Args:
        results: Results dictionary from execute_deletion()
    """
    print("\n" + "=" * 60)
    print("FILE DELETION SUMMARY")
    print("=" * 60)
    
    print(f"Total files processed:    {results['total_files']}")
    print(f"Successful removals:      {results['successful_removals']}")
    print(f"Failures:                 {results['failures']}")
    print(f"Success rate:             {results['success_rate']:.1f}%")
    print(f"Deletion mode:            {'Soft delete' if results['soft_delete'] else 'Permanent'}")
    
    if results['trash_path']:
        print(f"Trash folder:             {results['trash_path']}")
    
    print(f"Completed at:             {results['timestamp']}")
    
    # Show failure details if any
    if results['failures'] > 0:
        print("\nFAILURE DETAILS:")
        print("-" * 40)
        for msg in results['failure_messages']:
            print(f"  • {msg}")
    
    print("=" * 60)


def main():
    """
    Main function to demonstrate file deletion with command line interface.
    """
    parser = argparse.ArgumentParser(description='File Deletion Module - Step 5')
    parser.add_argument('--soft-delete', action='store_true', 
                       help='Move files to .trash folder instead of permanent deletion')
    parser.add_argument('--base-path', default='.', 
                       help='Base directory for operations (default: current directory)')
    parser.add_argument('--demo', action='store_true',
                       help='Run with demo files (creates test files for demonstration)')
    
    args = parser.parse_args()
    
    if args.demo:
        # Create some demo files for testing
        demo_files = [
            'demo_temp_file1.tmp',
            'demo_temp_file2.log', 
            'demo_test_file.txt'
        ]
        
        print("Creating demo files for testing...")
        for demo_file in demo_files:
            Path(demo_file).write_text(f"This is a demo file: {demo_file}")
            print(f"Created: {demo_file}")
        
        delete_list = demo_files
    else:
        # In a real scenario, this would come from the file_classifier module
        # For now, we'll use an empty list
        delete_list = []
        print("No delete list provided. Use --demo to test with demo files.")
        print("In a real scenario, this would be called with a delete list from file_classifier.py")
        return
    
    if not delete_list:
        print("No files to delete.")
        return
    
    # Execute deletion
    results = execute_deletion(delete_list, args.soft_delete, args.base_path)
    
    # Print summary
    print_deletion_summary(results)
    
    return results


if __name__ == "__main__":
    main()

