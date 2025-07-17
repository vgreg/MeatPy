# Getting Started with MeatPy

This guide will help you get started with MeatPy for processing financial market data.

## Basic Concepts

### Core Components

- **MarketProcessor**: Processes market messages and maintains order book state
- **MessageReader**: Reads market data from files in various formats
- **LimitOrderBook (LOB)**: Represents the current state of buy and sell orders
- **Event Handlers**: Process and record market events as they occur

### Supported Data Formats

MeatPy currently supports:

- **ITCH 5.0**: NASDAQ's binary market data format

## Basic Usage

The simplest way to read ITCH 5.0 data:

```python
from meatpy.itch50 import ITCH50MessageReader

# Read messages from an ITCH file
with ITCH50MessageReader("market_data.txt.gz") as reader:
    for i, message in enumerate(reader):
        print(f"Message {i}: {message}")
        if i >= 10:  # Just show first 10 messages
            break
```


Other common tasks include:

- **Listing Symbols**: Extracting unique stock symbols from ITCH files
- **Extracting Specific Symbols**: Creating new ITCH files with only specific symbols
- **Top of Book Snapshots**: Generating snapshots of the top of book state for analysis
- **Order Book Snapshots**: Creating snapshots of the full limit order book state
