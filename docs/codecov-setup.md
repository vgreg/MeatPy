# Codecov Configuration Guide

This guide explains how to set up code coverage reporting with Codecov for the MeatPy project.

## Overview

The project is configured to:
- Generate coverage reports during testing
- Upload coverage data to Codecov via GitHub Actions
- Display coverage badges and detailed reports
- Track coverage trends over time

## Configuration Files

### 1. Test Workflow (`.github/workflows/test.yml`)
- Runs tests on multiple Python versions (3.11, 3.12, 3.13)
- Generates coverage reports in XML format
- Uploads coverage to Codecov using the official action

### 2. Codecov Configuration (`codecov.yml`)
- Sets coverage targets (80% for project and patches)
- Configures which files to ignore
- Sets up coverage comment format for PRs

### 3. Pytest Configuration (`pytest.ini`)
- Enables branch coverage tracking
- Outputs coverage in multiple formats (terminal, HTML, XML)
- Sets minimum coverage threshold to 80%

### 4. Coverage Configuration (`.coveragerc`)
- Excludes test files and debug code from coverage
- Configures coverage exclusion patterns
- Sets up HTML report generation

## Setup Steps

### 1. Repository Setup on Codecov
1. Go to [codecov.io](https://codecov.io)
2. Sign in with your GitHub account
3. Find and enable the MeatPy repository
4. Copy the repository upload token

### 2. GitHub Secrets Configuration
1. Go to your GitHub repository settings
2. Navigate to Secrets and Variables → Actions
3. Add a new repository secret:
   - Name: `CODECOV_TOKEN`
   - Value: [Your Codecov upload token]

### 3. Badge Setup (Optional)
Add coverage badge to README.md:

```markdown
[![codecov](https://codecov.io/gh/vgreg/MeatPy/branch/main/graph/badge.svg)](https://codecov.io/gh/vgreg/MeatPy)
```

## Local Testing

Test coverage generation locally:

```bash
# Run tests with coverage
uv run pytest

# Generate coverage report
uv run pytest --cov=src/meatpy --cov-report=html

# View HTML report
open htmlcov/index.html
```

## Coverage Targets

- **Project Coverage**: 80% minimum
- **Patch Coverage**: 80% minimum for new code
- **Branch Coverage**: Enabled for better accuracy

## Excluded Files

The following are excluded from coverage:
- Test files (`tests/`)
- Documentation (`docs/`)
- Sample files (`samples/`)
- Setup/build files

## Troubleshooting

### Common Issues

1. **Coverage not uploading**: Check that `CODECOV_TOKEN` is correctly set in GitHub secrets
2. **Low coverage**: Review the coverage report to identify untested code
3. **CI failing**: Ensure all tests pass before coverage upload

### Debugging Coverage

```bash
# Run with coverage debug info
uv run pytest --cov=src/meatpy --cov-report=term-missing --cov-branch -v

# Check coverage configuration
uv run coverage config --help
```

## Resources

- [Codecov Documentation](https://docs.codecov.com/)
- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
