# Core Files Whitelist System

This directory contains scripts to verify that essential core files remain intact after cleanup operations.

## Files

- `check_whitelist.py` - Main script that verifies all whitelisted files exist
- `test_whitelist.py` - Test script to validate the whitelist checker functionality
- `../core_files_whitelist.txt` - List of core files that must remain intact

## Usage

### Check Core Files

```bash
python3 scripts/check_whitelist.py core_files_whitelist.txt
```

This command:
- Reads the whitelist file
- Checks that each listed file/pattern exists
- Exits with code 0 if all files are present
- Exits with code 1 if any files are missing

### Test the System

```bash
python3 scripts/test_whitelist.py
```

Runs comprehensive tests to validate the whitelist checker works correctly.

## Whitelist File Format

The `core_files_whitelist.txt` file supports:

- **Comments**: Lines starting with `#` are ignored
- **Empty lines**: Blank lines are ignored
- **File paths**: Direct file paths like `generate.py`
- **Glob patterns**: Patterns like `palette_*.json` to match multiple files

### Example

```txt
# Core application files
generate.py
watermark.py

# Configuration files
palette_*.json
requirements.txt

# Documentation
README.md
```

## CI Integration

The whitelist check is automatically run in CI after cleanup operations to ensure no essential files are accidentally removed. See `.github/workflows/ci.yml` for the CI configuration.

## Adding New Core Files

To add new files to the whitelist:

1. Edit `core_files_whitelist.txt`
2. Add the file path or glob pattern
3. Test with `python3 scripts/check_whitelist.py core_files_whitelist.txt`
4. Commit the changes

The CI will automatically verify the whitelist on every push and pull request.

