#!/usr/bin/env python3
"""
Test script to validate the whitelist checker functionality.
This script creates temporary scenarios to test the whitelist checker.
"""

import os
import sys
import tempfile
import subprocess
from pathlib import Path


def run_whitelist_check(whitelist_file, expected_exit_code=0):
    """Run the whitelist checker and return the result."""
    try:
        result = subprocess.run(
            [sys.executable, 'scripts/check_whitelist.py', whitelist_file],
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return -1, "", str(e)


def test_existing_whitelist():
    """Test with the actual core_files_whitelist.txt"""
    print("Testing with existing whitelist...")
    exit_code, stdout, stderr = run_whitelist_check('core_files_whitelist.txt')
    
    if exit_code == 0:
        print("✅ Existing whitelist test PASSED")
        return True
    else:
        print(f"❌ Existing whitelist test FAILED (exit code: {exit_code})")
        print(f"STDOUT: {stdout}")
        print(f"STDERR: {stderr}")
        return False


def test_missing_files():
    """Test with a whitelist that includes non-existent files"""
    print("Testing with missing files...")
    
    # Create temporary whitelist with missing files
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("# Test whitelist with missing files\n")
        f.write("generate.py\n")
        f.write("nonexistent_file.py\n")
        f.write("another_missing_file.txt\n")
        temp_whitelist = f.name
    
    try:
        exit_code, stdout, stderr = run_whitelist_check(temp_whitelist)
        
        if exit_code != 0:
            print("✅ Missing files test PASSED (correctly failed)")
            return True
        else:
            print("❌ Missing files test FAILED (should have failed but didn't)")
            return False
    finally:
        os.unlink(temp_whitelist)


def test_glob_patterns():
    """Test glob pattern matching"""
    print("Testing glob pattern matching...")
    
    # Create temporary whitelist with glob patterns
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("# Test whitelist with glob patterns\n")
        f.write("*.py\n")  # Should match existing .py files
        f.write("palette_*.json\n")  # Should match palette files
        temp_whitelist = f.name
    
    try:
        exit_code, stdout, stderr = run_whitelist_check(temp_whitelist)
        
        if exit_code == 0:
            print("✅ Glob patterns test PASSED")
            return True
        else:
            print(f"❌ Glob patterns test FAILED (exit code: {exit_code})")
            print(f"STDOUT: {stdout}")
            return False
    finally:
        os.unlink(temp_whitelist)


def test_empty_whitelist():
    """Test with empty whitelist (should pass)"""
    print("Testing with empty whitelist...")
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("# Empty whitelist - just comments\n")
        f.write("# This should pass\n")
        temp_whitelist = f.name
    
    try:
        exit_code, stdout, stderr = run_whitelist_check(temp_whitelist)
        
        if exit_code == 0:
            print("✅ Empty whitelist test PASSED")
            return True
        else:
            print(f"❌ Empty whitelist test FAILED (exit code: {exit_code})")
            return False
    finally:
        os.unlink(temp_whitelist)


def main():
    """Run all tests"""
    print("Running whitelist checker tests...\n")
    
    tests = [
        test_existing_whitelist,
        test_missing_files,
        test_glob_patterns,
        test_empty_whitelist
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests PASSED!")
        sys.exit(0)
    else:
        print("❌ Some tests FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()

