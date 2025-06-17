#!/usr/bin/env python3
"""
Script to verify that all core files listed in whitelist are present.
Exits with non-zero status if any files are missing.

Usage: python3 scripts/check_whitelist.py <whitelist_file>
"""

import sys
import os
import glob
from pathlib import Path


def read_whitelist(whitelist_file):
    """Read and parse the whitelist file, ignoring comments and empty lines."""
    if not os.path.exists(whitelist_file):
        print(f"Error: Whitelist file '{whitelist_file}' not found")
        sys.exit(1)
    
    files = []
    with open(whitelist_file, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip empty lines and comments
            if line and not line.startswith('#'):
                files.append(line)
    
    return files


def check_file_exists(file_pattern, base_dir='.'):
    """Check if file or glob pattern exists. Returns list of missing patterns."""
    # Handle glob patterns
    if '*' in file_pattern or '?' in file_pattern:
        matches = glob.glob(os.path.join(base_dir, file_pattern))
        if not matches:
            return [file_pattern]
        return []
    else:
        # Regular file check
        file_path = os.path.join(base_dir, file_pattern)
        if not os.path.exists(file_path):
            return [file_pattern]
        return []


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 scripts/check_whitelist.py <whitelist_file>")
        sys.exit(1)
    
    whitelist_file = sys.argv[1]
    print(f"Checking whitelist: {whitelist_file}")
    
    # Read whitelist
    whitelisted_files = read_whitelist(whitelist_file)
    print(f"Found {len(whitelisted_files)} entries in whitelist")
    
    # Check each file
    missing_files = []
    for file_pattern in whitelisted_files:
        missing = check_file_exists(file_pattern)
        missing_files.extend(missing)
    
    # Report results
    if missing_files:
        print("\n❌ WHITELIST CHECK FAILED")
        print("The following core files are missing:")
        for missing_file in missing_files:
            print(f"  - {missing_file}")
        print(f"\nTotal missing files: {len(missing_files)}")
        sys.exit(1)
    else:
        print("\n✅ WHITELIST CHECK PASSED")
        print("All core files are present")
        sys.exit(0)


if __name__ == "__main__":
    main()

