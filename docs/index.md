# MeatPy

MeatPy is a high-performance Python framework for processing financial market data, specifically designed for limit order book reconstruction and analysis. It provides efficient tools for handling high-frequency trading data formats like NASDAQ ITCH 5.0.

## Key Features

- **Limit Order Book Processing**: Complete reconstruction and analysis of limit order books
- **High Performance**: Optimized for processing large volumes of market data
- **ITCH 5.0 Support**: Full implementation for NASDAQ ITCH 5.0 format
- **Event-Driven Architecture**: Extensible framework for real-time market data processing
- **Type Safety**: Modern Python typing for robust financial data handling
- **Multiple Output Formats**: Support for CSV, Parquet, and custom formats

## Architecture Overview

MeatPy is built around several core components:

- **MarketProcessor**: Abstract base class for processing market messages
- **LimitOrderBook**: Core data structure representing the order book state
- **MessageReader**: Interface for reading different market data formats
- **Event Handlers**: Observer pattern for handling market events and recording data

## Quick Start

```python
from meatpy.itch50 import ITCH50MessageReader, ITCH50MarketProcessor

# Read and process ITCH 5.0 data
reader = ITCH50MessageReader("market_data.txt")
processor = ITCH50MarketProcessor()

for message in reader:
    processor.process_message(message)
    # Access current order book state
    lob = processor.get_lob("AAPL")
```

## What's Next?

- Check out the [Installation Guide](installation.md) to get started
- Explore [Examples](guide/examples.md) for common use cases
- Read the [User Guide](guide/getting-started.md) for detailed usage instructions
- See [Contributing](contributing.md) if you want to contribute to the project
