# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Package Management
- `uv sync` - Install dependencies and create virtual environment
- `uv run <command>` - Run commands in the virtual environment

### Testing
- `uv run pytest` - Run all tests with coverage
- `uv run pytest tests/test_<module>.py` - Run specific test file
- `uv run pytest -m "not slow"` - Skip slow tests
- `uv run pytest -m unit` - Run only unit tests
- `uv run pytest -m integration` - Run only integration tests
- Coverage reports are generated in `htmlcov/` directory

### Code Quality
- `uv run ruff check` - Lint code with ruff
- `uv run ruff format` - Format code with ruff
- `uv run pre-commit run --all-files` - Run all pre-commit hooks
- Pre-commit hooks include: ruff linting/formatting, trailing whitespace, file checks

### Documentation
- Documentation is built with Sphinx in the `docs/` directory
- Latest docs available at: https://meatpy.readthedocs.io/en/latest/

## Architecture Overview

MeatPy is a framework for processing high-frequency financial market data, specifically designed for limit order book reconstruction and analysis.

### Core Components

**MarketProcessor (`src/meatpy/market_processor.py`)**
- Abstract base class for processing market messages
- Maintains limit order book state and trading status
- Supports event handlers for real-time processing
- Generic typed for Price, Volume, OrderID, TradeRef, Qualifiers

**LimitOrderBook (`src/meatpy/lob.py`)**
- Core data structure representing the order book
- Tracks bid/ask levels with price-time priority
- Handles order additions, deletions, modifications, and executions

**MarketEventHandler (`src/meatpy/market_event_handler.py`)**
- Observer pattern for handling market events
- Allows pluggable event processing and recording

**MessageReader (`src/meatpy/message_reader.py`)**
- Abstract interface for reading market data messages
- Supports different data formats through subclassing

### ITCH 5.0 Implementation

The `src/meatpy/itch50/` module provides a complete implementation for Nasdaq ITCH 5.0 format:

- `itch50_market_processor.py` - ITCH-specific market processor
- `itch50_message_reader.py` - ITCH message parsing
- `itch50_market_message.py` - ITCH message types and validation
- `itch50_writer.py` - Writing ITCH data
- Various event recorders for different data output formats

### Event Handlers (`src/meatpy/event_handlers/`)

- `lob_event_recorder.py` - Records limit order book events
- `ofi_recorder.py` - Order flow imbalance calculations
- `spot_measures_recorder.py` - Real-time market measures

### Type System (`src/meatpy/types.py`)

Uses generic types for financial data:
- `Price`, `Volume`, `OrderID`, `TradeRef`, `Qualifiers`
- Enables type-safe market data processing

### Trading Status (`src/meatpy/trading_status.py`)

Comprehensive trading status tracking:
- Pre-trade, trade, halted, post-trade, quote-only states
- Closing auction and closed market states

## Project Structure

- `src/meatpy/` - Main source code
- `tests/` - Test suite with unit, integration, and performance tests
- `examples/` - Usage examples and demonstrations
- `samples/` - Sample processing scripts for ITCH 5.0
- `docs/` - Sphinx documentation source
- `rules/` - Development rules and guidelines

## Key Development Notes

- The codebase uses modern Python typing extensively
- All market data types are generic for flexibility across different exchanges
- Event-driven architecture allows for extensible data processing
- ITCH 5.0 implementation serves as reference for adding new data formats
- Tests include coverage requirements (minimum 80%)
- Pre-commit hooks enforce code quality and formatting
