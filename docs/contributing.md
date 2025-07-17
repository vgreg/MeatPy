# Contributing to MeatPy

We welcome contributions to MeatPy! This document provides guidelines for contributing to the project.

## Development Setup

### Prerequisites

- Python 3.11 or higher
- Git
- `uv` package manager

### Setting Up Development Environment

1. **Clone the repository:**
   ```bash
   git clone https://github.com/vgreg/MeatPy.git
   cd MeatPy
   ```

2. **Install dependencies using uv (recommended):**
   ```bash
   uv sync
   ```

   Or using pip:
   ```bash
   pip install -e ".[dev]"
   ```

3. **Install pre-commit hooks:**
   ```bash
   uv run pre-commit install
   ```

## Development Workflow

### Code Quality

We use several tools to maintain code quality:

- **Ruff**: For linting and formatting
- **Pre-commit**: For automated code checks
- **Pytest**: For testing

### Running Tests

It is best to run tests locally before submitting changes to ensure everything works as expected. Tests are also executed automatically in the CI pipeline when you create a pull request.

```bash
# Run all tests
uv run pytest
```

### Code Formatting and Linting

```bash
# Format code
uv run ruff format

# Check for linting issues
uv run ruff check

# Fix auto-fixable linting issues
uv run ruff check --fix
```

## Contribution Guidelines

### Code Style

- Follow Ruff (black) style guidelines
- Use type hints for all public APIs
- Write descriptive variable and function names
- Keep functions focused and modular
- Add Google-style docstrings to all public classes and methods

Example:
```python
def process_order_message(
    message: AddOrderMessage,
    lob: LimitOrderBook[Price, Volume, OrderID]
) -> None:
    """Process an add order message and update the limit order book.

    Args:
        message: The order message to process
        lob: The limit order book to update

    Raises:
        InvalidMessageError: If the message is malformed
    """
    # Implementation here
```

### Testing

- Write unit tests for all new functionality
- Maintain test coverage above 80%
- Use descriptive test names that explain what is being tested
- Group related tests in test classes
- Use pytest fixtures for common test setup

Example test structure:
```python
class TestLimitOrderBook:
    """Tests for the LimitOrderBook class."""

    def test_add_bid_order_updates_best_bid(self, empty_lob):
        """Test that adding a bid order correctly updates the best bid."""
        # Test implementation

    def test_cancel_order_removes_from_book(self, lob_with_orders):
        """Test that canceling an order removes it from the book."""
        # Test implementation
```

### Documentation

- Update documentation for any API changes
- Add examples for new features
- Use clear, concise language
- Include code examples where helpful

### Commit Messages

This project uses **automated semantic versioning** based on conventional commit messages. When code is merged to `main`, the system automatically:

1. Analyzes commit messages since the last release
2. Determines the version bump type (major, minor, or patch)
3. Updates the version in `pyproject.toml`
4. Creates a GitHub release with a new tag
5. Publishes the package to PyPI

#### Conventional Commit Format

Use these commit message patterns to trigger appropriate version bumps:

**Major Version Bump (Breaking Changes):**
- `BREAKING CHANGE:` in commit body
- `breaking:` prefix in commit message

**Minor Version Bump (New Features):**
- `feat:` prefix for new features
- `feature:` prefix for new features

**Patch Version Bump (Bug Fixes):**
- `fix:` prefix for bug fixes
- `bug:` prefix for bug fixes
- `patch:` prefix for patches

**Examples:**

```bash
# Patch version bump (0.1.0 -> 0.1.1)
git commit -m "fix: resolve issue with order book reconstruction"

# Minor version bump (0.1.0 -> 0.2.0)
git commit -m "feat: add support for new message types"

# Major version bump (0.1.0 -> 1.0.0)
git commit -m "refactor: redesign API for better performance

BREAKING CHANGE: MarketProcessor constructor now requires different parameters"
```

#### Manual Releases

If you need to publish a release manually:

1. Go to the GitHub repository
2. Navigate to Actions → Manual Publish to PyPI
3. Click "Run workflow" and specify the version

## Types of Contributions

### Bug Reports

When reporting bugs, please include:

- Python version and platform
- MeatPy version
- Minimal code example that reproduces the issue
- Expected vs actual behavior
- Error messages or stack traces

### Feature Requests

For new features:

- Describe the use case and motivation
- Provide examples of how the feature would be used
- Consider backward compatibility
- Discuss performance implications for large datasets

## Getting Help

- **Discussions**: Use GitHub Discussions for questions
- **Issues**: Create issues for bugs and feature requests
- **Email**: Contact maintainers for sensitive issues

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help maintain a welcoming environment
- Follow the project's code of conduct

## Recognition

Contributors will be acknowledged in:

- Release notes for significant contributions
- GitHub contributors list

Thank you for contributing to MeatPy!
