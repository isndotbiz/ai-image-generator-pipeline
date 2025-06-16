# CI Pipeline Setup

This document describes the Continuous Integration (CI) pipeline configured to ensure environment consistency and guard against dependency drift.

## Overview

The CI pipeline implements the following steps to ensure environment consistency:

1. **Virtual Environment Setup**: `python -m venv venv && source venv/bin/activate`
2. **Dependency Installation**: `pip install -r requirements.txt`
3. **Verification & Smoke Tests**: Run environment verification and smoke tests

This approach guards against future dependency drift by testing the complete environment setup process on every commit.

## Workflows

### Primary Workflow: `environment-check.yml`

A focused workflow that directly implements the requested CI pipeline:

- **Triggers**: Push to main/master, pull requests, weekly schedule (Mondays 2 AM UTC), manual dispatch
- **Purpose**: Test environment consistency and catch dependency drift
- **Steps**:
  1. Checkout code
  2. Set up Python 3.11
  3. Create and activate virtual environment
  4. Install dependencies from requirements.txt
  5. Run verification and smoke tests
  6. Verify critical imports
  7. Generate summary report

### Comprehensive Workflow: `ci.yml`

A more comprehensive workflow that includes additional checks:

- **Multi-Python Testing**: Tests across Python versions 3.8, 3.9, 3.10, 3.11
- **Code Quality**: Optional flake8 and black formatting checks
- **Security**: Dependency vulnerability scanning with safety
- **Requirements Analysis**: Dependency tree analysis and conflict detection

## Test Scripts

### `run_tests.py`

A unified test runner that handles both pytest and unittest execution:

```bash
# Run all verification and smoke tests
python run_tests.py
```

Features:
- Automatically detects pytest availability
- Falls back to unittest if pytest is not available
- Runs environment verification
- Executes safe smoke tests (no API calls required)

### `verify_setup.py`

Environment verification script that checks:
- Python version compatibility
- Required package installations
- Environment variable configuration
- Project file existence

### `tests/test_smoke.py`

Smoke tests for critical functionality:
- Dependency import verification
- Directory creation functionality
- Basic pipeline components

## Benefits

### Dependency Drift Protection

- **Early Detection**: Catches breaking changes in dependencies before they affect production
- **Version Compatibility**: Tests across multiple Python versions
- **Clean Environment**: Each test runs in a fresh virtual environment

### Environment Consistency

- **Reproducible Setup**: Ensures `requirements.txt` accurately reflects needed dependencies
- **Cross-Platform**: Tests on GitHub's Ubuntu runners mimic common deployment environments
- **Automated Verification**: No manual intervention required

### Continuous Monitoring

- **Weekly Checks**: Scheduled runs catch drift even without code changes
- **Pull Request Validation**: New changes are tested before merge
- **Security Scanning**: Regular vulnerability checks on dependencies

## Usage

### Local Testing

Before pushing changes, you can run the same checks locally:

```bash
# Create clean virtual environment
python -m venv test_venv
source test_venv/bin/activate  # On Windows: test_venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Run verification
python verify_setup.py

# Run smoke tests
python run_tests.py
```

### Monitoring CI Results

1. **GitHub Actions Tab**: View workflow runs and results
2. **PR Checks**: See CI status on pull requests
3. **Scheduled Runs**: Monitor weekly drift detection
4. **Email Notifications**: GitHub can notify on workflow failures

## Customization

### Adding New Tests

To add new smoke tests:

1. Add test methods to `tests/test_smoke.py`
2. Ensure tests don't require external API calls
3. Update `run_tests.py` if needed

### Modifying Python Versions

Edit the matrix in `.github/workflows/ci.yml`:

```yaml
strategy:
  matrix:
    python-version: ['3.8', '3.9', '3.10', '3.11', '3.12']  # Add/remove versions
```

### Environment Variables

For tests requiring API keys:

1. Add secrets to GitHub repository settings
2. Reference in workflow: `${{ secrets.YOUR_SECRET_NAME }}`
3. Provide fallback values for public repositories

## Troubleshooting

### Common Issues

1. **Import Errors**: Check if new dependencies were added to `requirements.txt`
2. **Version Conflicts**: Review dependency versions and compatibility
3. **Platform Differences**: Consider OS-specific dependencies
4. **Memory/Time Limits**: Large dependencies may need workflow adjustments

### Debugging Failed Runs

1. Check the GitHub Actions logs for detailed error messages
2. Run the same commands locally to reproduce issues
3. Verify `requirements.txt` accuracy
4. Test in a clean virtual environment

## Maintenance

- **Monthly Review**: Check for new dependency updates
- **Security Updates**: Monitor and apply security patches
- **Python Version Updates**: Test new Python releases
- **Workflow Updates**: Keep GitHub Actions up to date

This CI setup provides robust protection against dependency drift while maintaining development velocity through automated testing and verification.

