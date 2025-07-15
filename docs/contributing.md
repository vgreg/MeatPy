# Contributing to MeatPy

We welcome contributions to MeatPy! This document provides guidelines for contributing to the project.

## Development Setup

### Prerequisites

- Python 3.11 or higher
- Git
- `uv` package manager (recommended) or `pip`

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

```bash
# Run all tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=meatpy

# Run specific test file
uv run pytest tests/test_lob.py

# Run only fast tests (skip slow integration tests)
uv run pytest -m "not slow"

# Run only unit tests
uv run pytest -m unit

# Run only integration tests
uv run pytest -m integration
```

### Code Formatting and Linting

```bash
# Format code
uv run ruff format

# Check for linting issues
uv run ruff check

# Fix auto-fixable linting issues
uv run ruff check --fix

# Run all pre-commit hooks
uv run pre-commit run --all-files
```

## Contribution Guidelines

### Code Style

- Follow PEP 8 style guidelines
- Use type hints for all public APIs
- Write descriptive variable and function names
- Keep functions focused and modular
- Add docstrings to all public classes and methods

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

Use clear, descriptive commit messages:

- **Good**: `Add support for ITCH 5.1 message format`
- **Good**: `Fix memory leak in order book processing`
- **Bad**: `Fix bug`
- **Bad**: `Update code`

Format:
```
Short description (50 chars or less)

Longer explanation if needed. Wrap at 72 characters.
Explain what the change does and why it was needed.

- Use bullet points for multiple changes
- Reference issue numbers: Fixes #123
```

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

### Code Contributions

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature-name`
3. **Make your changes** following the guidelines above
4. **Add tests** for new functionality
5. **Update documentation** if needed
6. **Run the test suite** to ensure nothing breaks
7. **Commit your changes** with clear messages
8. **Push to your fork**: `git push origin feature-name`
9. **Create a pull request**

## Pull Request Process

1. **Ensure CI passes**: All tests and checks must pass
2. **Update documentation**: Include any necessary documentation updates
3. **Add tests**: New features require corresponding tests
4. **Describe changes**: Provide a clear description of what the PR does
5. **Reference issues**: Link to any related issues
6. **Request review**: Tag maintainers for review

### PR Template

```markdown
## Description
Brief description of the changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Refactoring

## Testing
- [ ] Added new tests
- [ ] All tests pass
- [ ] Manual testing performed

## Documentation
- [ ] Updated docstrings
- [ ] Updated user documentation
- [ ] Added examples if applicable

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review of the code completed
- [ ] Changes generate no new warnings
- [ ] Added tests that prove the fix/feature works
```

## Performance Considerations

When contributing code that processes market data:

- **Memory efficiency**: Be mindful of memory usage for large datasets
- **Processing speed**: Profile code for performance bottlenecks
- **Scalability**: Consider how changes affect processing of large files
- **Resource usage**: Monitor CPU and I/O usage patterns

## Architecture Guidelines

### Adding New Data Formats

To add support for a new market data format:

1. Create a new module under `src/meatpy/[format_name]/`
2. Implement `MessageReader` subclass for the format
3. Implement `MarketProcessor` subclass if needed
4. Define message types and validation
5. Add comprehensive tests
6. Update documentation

### Event Handler Development

When creating new event handlers:

1. Inherit from `MarketEventHandler`
2. Implement required abstract methods
3. Consider memory usage for long-running processes
4. Provide clear configuration options
5. Add examples and documentation

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
- Project documentation
- GitHub contributors list

Thank you for contributing to MeatPy!
