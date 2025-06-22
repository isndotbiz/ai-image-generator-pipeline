#!/usr/bin/env python3
"""
Fortuna Bound Project Setup Script

This setup script ensures proper virtual environment usage and project installation.
It demonstrates how to use the local venv for all Python operations.

Usage:
    # Using local venv (recommended):
    venv/bin/python setup.py install

    # Or activate venv first:
    source venv/bin/activate
    python setup.py install
"""

import os
import sys
import subprocess
from pathlib import Path
from setuptools import setup, find_packages

# Ensure we're using the local venv
def check_virtual_env():
    """Check if we're using the local virtual environment"""
    venv_path = Path("venv")
    current_executable = Path(sys.executable)
    
    if venv_path.exists():
        expected_python = venv_path / "bin" / "python"
        if current_executable != expected_python:
            print("⚠️  Warning: Not using local virtual environment")
            print(f"Current Python: {current_executable}")
            print(f"Expected Python: {expected_python}")
            print("\nRecommended usage:")
            print(f"  {expected_python} setup.py install")
            print("Or:")
            print("  source venv/bin/activate")
            print("  python setup.py install")
    else:
        print("❌ Virtual environment not found at ./venv")
        print("Please create it first:")
        print("  python3 -m venv venv")
        print("  source venv/bin/activate")
        print("  pip install -r requirements.txt")
        sys.exit(1)

def get_requirements():
    """Read requirements from requirements.txt"""
    requirements_file = Path("requirements.txt")
    if requirements_file.exists():
        with open(requirements_file, 'r') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return []

def run_post_install():
    """Run post-installation setup tasks"""
    print("\n" + "="*60)
    print("🚀 Running post-installation setup...")
    
    # Make scripts executable
    script_files = [
        "generate_videos.sh",
        "gon.sh", 
        "setup_runway.sh",
        "test_gen.sh",
        "test_pipeline.sh",
        "setup_watermark_pipeline.sh",
        "daily_palette_rotation.sh",
        "run_watermark_with_logging.sh",
        "upload.sh",
        "benchmarking/run_benchmarks.sh"
    ]
    
    for script in script_files:
        script_path = Path(script)
        if script_path.exists():
            script_path.chmod(0o755)
            print(f"✅ Made {script} executable")
    
    # Create necessary directories
    directories = [
        "images/pending",
        "images/approved", 
        "images/rejected",
        "images/selected_for_video",
        "images/ranked",
        "video_outputs",
        "uploads",
        "logs",
        "benchmarking/results"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")
    
    print("\n🎉 Setup complete! All scripts now use local venv.")
    print("\nNext steps:")
    print("1. Generate videos: ./generate_videos.sh")
    print("2. Run benchmarks: venv/bin/python benchmarking/model_benchmark.py")
    print("3. Start watermark pipeline: ./setup_watermark_pipeline.sh")
    print("\nSee VENV_USAGE.md for detailed usage instructions.")

# Check virtual environment before proceeding
check_virtual_env()

# Project metadata
setup(
    name="fortuna-bound",
    version="1.0.0",
    description="AI-powered image and video generation pipeline with luxury branding",
    author="Fortuna Bound",
    python_requires=">=3.8",
    packages=find_packages(),
    install_requires=get_requirements(),
    
    # Entry points for command-line scripts
    entry_points={
        'console_scripts': [
            # These will use the activated venv automatically
            'fortuna-generate=generate:main',
            'fortuna-watermark=auto_watermark_workflow:main',
            'fortuna-benchmark=benchmarking.model_benchmark:main',
        ],
    },
    
    # Development dependencies
    extras_require={
        'dev': [
            'pytest',
            'black',
            'flake8',
            'mypy',
        ],
    },
    
    # Include additional files
    include_package_data=True,
    package_data={
        '': ['*.md', '*.txt', '*.yml', '*.yaml', '*.json'],
    },
    
    # Custom commands
    cmdclass={},
)

# Run post-installation tasks
if 'install' in sys.argv:
    run_post_install()

