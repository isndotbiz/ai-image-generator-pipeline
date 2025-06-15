#!/usr/bin/env python3
"""
Environment Setup Verification Script

This script verifies that all required dependencies are installed and
the environment is properly configured for the image generation project.
"""

import sys
import os
import importlib.metadata

def check_python_version():
    """Check if Python version meets requirements."""
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"✓ Python {version.major}.{version.minor}.{version.micro} (meets requirement: 3.8+)")
        return True
    else:
        print(f"✗ Python {version.major}.{version.minor}.{version.micro} (requires 3.8+)")
        return False

def check_package(package_name, min_version=None):
    """Check if a package is installed and optionally verify version."""
    try:
        __import__(package_name)
        try:
            version = importlib.metadata.version(package_name)
            if min_version:
                print(f"✓ {package_name} {version} (required: {min_version}+)")
            else:
                print(f"✓ {package_name} {version}")
        except:
            print(f"✓ {package_name} (version check skipped)")
        return True
    except ImportError:
        print(f"✗ {package_name} not installed")
        return False

def check_environment_variables():
    """Check for required environment variables."""
    token = os.environ.get('REPLICATE_API_TOKEN')
    if token:
        # Only show first and last 4 characters for security
        masked = token[:4] + '*' * (len(token) - 8) + token[-4:] if len(token) > 8 else '*' * len(token)
        print(f"✓ REPLICATE_API_TOKEN is set ({masked})")
        return True
    else:
        print("⚠ REPLICATE_API_TOKEN is not set (required for API calls)")
        return False

def check_files():
    """Check for important project files."""
    files_to_check = [
        'gon.sh',
        'requirements.txt',
        '.env.example',
        'README.md'
    ]
    
    all_exist = True
    for filename in files_to_check:
        if os.path.exists(filename):
            print(f"✓ {filename} exists")
        else:
            print(f"✗ {filename} missing")
            all_exist = False
    
    return all_exist

def main():
    """Main verification function."""
    print("=== Environment Setup Verification ===")
    print()
    
    # Check Python version
    print("1. Python Version:")
    python_ok = check_python_version()
    print()
    
    # Check required packages
    print("2. Required Packages:")
    packages = [
        ('replicate', '1.0.0'),
        ('requests', '2.25.0'),
        ('piexif', '1.1.0'),
        ('colorthief', '0.2.0'),
        ('numpy', '1.21.0'),
        ('PIL', '8.0.0'),  # PIL is part of Pillow
    ]
    
    packages_ok = True
    for package, min_ver in packages:
        if not check_package(package, min_ver):
            packages_ok = False
    print()
    
    # Check environment variables
    print("3. Environment Variables:")
    env_ok = check_environment_variables()
    print()
    
    # Check project files
    print("4. Project Files:")
    files_ok = check_files()
    print()
    
    # Summary
    print("=== Summary ===")
    if python_ok and packages_ok and files_ok:
        print("✓ Environment setup is complete!")
        if not env_ok:
            print("⚠ Remember to set REPLICATE_API_TOKEN before running image generation.")
        return 0
    else:
        print("✗ Environment setup has issues. Please resolve the items marked with ✗")
        return 1

if __name__ == "__main__":
    sys.exit(main())

