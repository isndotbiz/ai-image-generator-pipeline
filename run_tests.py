#!/usr/bin/env python3
"""
Test runner for smoke tests and verification.
This script can run tests with or without pytest.
"""

import sys
import os
import subprocess
from pathlib import Path

def run_with_pytest():
    """Run tests using pytest if available."""
    try:
        import pytest
        # Run specific smoke tests that don't require API keys
        result1 = pytest.main([
            'tests/test_smoke.py::TestImageGenerationSmoke::test_import_dependencies',
            '-v'
        ])
        
        result2 = pytest.main([
            'tests/test_smoke.py::TestImageGenerationSmoke::test_images_directory_creation',
            '-v'
        ])
        
        return result1 == 0 and result2 == 0
    except ImportError:
        return False

def run_without_pytest():
    """Run tests directly using unittest if pytest is not available."""
    try:
        # Run the smoke tests directly
        result = subprocess.run([
            sys.executable, 'tests/test_smoke.py'
        ], capture_output=True, text=True)
        
        print("Test output:")
        print(result.stdout)
        if result.stderr:
            print("Errors:")
            print(result.stderr)
        
        return result.returncode == 0
    except Exception as e:
        print(f"Error running tests: {e}")
        return False

def run_verification():
    """Run the environment verification script."""
    try:
        result = subprocess.run([
            sys.executable, 'verify_setup.py'
        ], capture_output=True, text=True)
        
        print("Verification output:")
        print(result.stdout)
        if result.stderr:
            print("Verification errors:")
            print(result.stderr)
        
        return result.returncode == 0
    except Exception as e:
        print(f"Error running verification: {e}")
        return False

def main():
    """Main test runner function."""
    print("=== Running Environment Verification ===")
    verification_passed = run_verification()
    print()
    
    print("=== Running Smoke Tests ===")
    # Try pytest first, fall back to unittest
    if run_with_pytest():
        print("✓ Smoke tests passed (using pytest)")
        tests_passed = True
    elif run_without_pytest():
        print("✓ Smoke tests passed (using unittest)")
        tests_passed = True
    else:
        print("✗ Smoke tests failed")
        tests_passed = False
    
    print()
    print("=== Summary ===")
    if verification_passed and tests_passed:
        print("✓ All checks passed!")
        return 0
    else:
        print("✗ Some checks failed")
        return 1

if __name__ == '__main__':
    sys.exit(main())

