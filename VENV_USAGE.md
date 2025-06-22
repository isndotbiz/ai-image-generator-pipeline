# Virtual Environment Usage Guide

This document explains how to use the local virtual environment (`venv`) with the Fortuna Bound project scripts.

## Overview

All project scripts have been updated to use the local virtual environment located at `venv/`. This ensures consistent dependency management and avoids conflicts with system Python packages.

## Setup

1. Create the virtual environment:
   ```bash
   python3 -m venv venv
   ```

2. Activate and install dependencies:
   ```bash
   source venv/bin/activate
   pip install -r requirements.txt
   ```

## Usage Methods

### Method 1: Direct venv executable (Recommended for scripts)

Use the Python executable directly from the venv:

```bash
# From project root
venv/bin/python script_name.py

# Example: Generate videos
venv/bin/python intelligent_video_generator.py --max-videos 5

# Example: Run benchmarks
venv/bin/python benchmarking/model_benchmark.py
```

### Method 2: Activate first (Recommended for interactive work)

Activate the virtual environment, then use python normally:

```bash
source venv/bin/activate
python script_name.py
# ... run multiple commands ...
deactivate  # when done
```

### Method 3: Shell script shebang (For script files)

Scripts can auto-activate the venv using this shebang:

```bash
#!/usr/bin/env -S bash -c 'source venv/bin/activate && exec "$0" "$@"'
```

## Updated Scripts

The following scripts have been updated to use `venv/bin/python`:

### Shell Scripts (`*.sh`)
- `generate_videos.sh` - Uses venv for video generation
- `gon.sh` - Uses venv for image generation pipeline  
- `setup_runway.sh` - Uses venv for Runway setup
- `test_gen.sh` - Uses venv for generation testing
- `test_pipeline.sh` - Uses venv for pipeline testing
- `setup_watermark_pipeline.sh` - Uses venv for watermark setup
- `daily_palette_rotation.sh` - Uses venv for palette rotation
- `run_watermark_with_logging.sh` - Uses venv for watermark workflow
- `upload.sh` - Uses venv activation

### Benchmarking Scripts
- `benchmarking/model_benchmark.py` - Template script with venv usage examples
- `benchmarking/run_benchmarks.sh` - Runner script using venv

## Migration from ~/menv

Scripts previously used `~/menv/bin/activate`. These have been updated to use the local `venv/bin/activate` for better project isolation.

### Key Changes Made:
1. **Shebang lines**: Changed from `source ~/menv/bin/activate` to `source venv/bin/activate`
2. **Python calls**: Changed from `python3` to `venv/bin/python`
3. **Documentation**: Updated all usage examples to show venv commands

## Best Practices

1. **For shell scripts**: Use `venv/bin/python` directly
2. **For interactive work**: Activate venv first with `source venv/bin/activate`
3. **For documentation**: Always show both activation and direct usage methods
4. **For CI/CD**: Prefer direct venv paths for reproducibility

## Verification

To verify your virtual environment is working correctly:

```bash
# Check Python executable location
venv/bin/python -c "import sys; print(sys.executable)"

# Check installed packages
venv/bin/pip list

# Run a simple test
venv/bin/python -c "print('Virtual environment is working!')"
```

## Troubleshooting

### Virtual environment doesn't exist
```bash
# Create it
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Scripts fail with import errors
```bash
# Make sure dependencies are installed
source venv/bin/activate
pip install -r requirements.txt
```

### Permission denied
```bash
# Make scripts executable
chmod +x script_name.sh
```

## Example Usage

### Running the complete pipeline
```bash
# Generate videos
./generate_videos.sh

# Or manually with venv
venv/bin/python intelligent_video_generator.py --max-videos 5
```

### Running benchmarks
```bash
# Using the runner script
cd benchmarking
./run_benchmarks.sh

# Or directly
venv/bin/python benchmarking/model_benchmark.py
```

### Running watermark workflow
```bash
# Using the setup script
./setup_watermark_pipeline.sh

# Then run the workflow
venv/bin/python auto_watermark_workflow.py --mode full
```

This ensures all project components use the same Python environment and dependencies.

