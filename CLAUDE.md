# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MeatPy is a Python framework for processing and analyzing high-frequency financial data, specifically designed for Nasdaq ITCH 5.0 format. It provides tools for parsing market messages, reconstructing limit order books, and analyzing market microstructure.

## Development Commands

### Environment Setup
```bash
# Install dependencies using uv (recommended)
uv sync

# Install pre-commit hooks
uv run pre-commit install
```

### Testing
```bash
# Run all tests with coverage
uv run pytest

# Run specific test markers
uv run pytest -m "not slow"  # Skip slow tests
uv run pytest -m unit        # Only unit tests
uv run pytest -m integration # Only integration tests
```

### Code Quality
```bash
# Format code
uv run ruff format

# Check linting issues
uv run ruff check

# Fix auto-fixable linting issues
uv run ruff check --fix
```

### Documentation
```bash
# Build documentation
mkdocs build

# Serve documentation locally
mkdocs serve
```

## Architecture Overview

### Core Components

**Market Processing Pipeline**: The library follows an event-driven architecture centered around `MarketProcessor` classes that process market messages and maintain limit order book state.

**Key Classes**:
- `MarketProcessor`: Abstract base class for processing market messages (src/meatpy/market_processor.py:19)
- `ITCH50MarketProcessor`: ITCH 5.0 specific implementation (src/meatpy/itch50/itch50_market_processor.py:87)
- `LimitOrderBook`: Maintains the current state of the order book (src/meatpy/lob.py)
- `MarketEventHandler`: Handles events during processing (src/meatpy/market_event_handler.py)

### Message Processing Flow

1. **Message Reading**: `MessageReader` classes parse binary market data into `MarketMessage` objects
2. **Event Processing**: `MarketProcessor` processes messages, updates the LOB, and notifies handlers
3. **Data Recording**: Event handlers record market events (trades, quotes, etc.) to various output formats

### Package Structure

- `src/meatpy/` - Core library code
  - `itch50/` - ITCH 5.0 specific implementations
  - `event_handlers/` - Event recording and processing handlers
  - `writers/` - Output format writers (CSV, Parquet)
- `tests/` - Test suite
- `docs/` - Documentation (MkDocs format)
- `samples/` - Example scripts showing typical usage patterns

### Generic Type System

The codebase uses extensive generic typing for market data types:
- `Price`, `Volume`, `OrderID`, `TradeRef`, `Qualifiers` are generic type parameters
- ITCH 5.0 implementation uses concrete types: `int` for prices/volumes/IDs, `dict[str, str]` for qualifiers

## Development Guidelines

### Code Style
- Use Google-style docstrings for all public APIs
- Type hints are required for all function signatures
- Follow Ruff formatting standards
- Maintain test coverage above 80%

### Testing Approach
- Tests use pytest with custom markers (unit, integration, slow, performance)
- Coverage reporting configured in pytest.ini
- Test data available in `tests/` and `docs/guide/data/`

### Configuration Files
- `pyproject.toml` - Project metadata, dependencies, and tool configuration
- `pytest.ini` - Test configuration with coverage requirements
- `mkdocs.yml` - Documentation configuration
- `rules/python.mdc` - Development guidelines for cursor/AI tools
