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
- **Extensible Architecture**: Framework designed to support additional formats

## Basic Usage

### Reading Market Data

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

### Processing Market Data

To process messages and maintain order book state:

```python
from meatpy.itch50 import ITCH50MessageReader, ITCH50MarketProcessor

# Create a processor
processor = ITCH50MarketProcessor()

# Process messages
with ITCH50MessageReader("market_data.txt.gz") as reader:
    for message in reader:
        processor.process_message(message)

        # Access order book for a specific symbol
        if message.type == b'A':  # Add order message
            symbol = message.stock.decode()
            lob = processor.get_lob(symbol)
            if lob:
                print(f"{symbol} - Best bid: {lob.best_bid}, Best ask: {lob.best_ask}")
```

### Using Event Handlers

Event handlers allow you to capture and record market events:

```python
from meatpy.itch50 import ITCH50MessageReader, ITCH50MarketProcessor
from meatpy.event_handlers import LOBRecorder

# Create processor and event handler
processor = ITCH50MarketProcessor()
lob_recorder = LOBRecorder()

# Register event handler
processor.add_event_handler(lob_recorder)

# Process data
with ITCH50MessageReader("market_data.txt.gz") as reader:
    for message in reader:
        processor.process_message(message)

# Access recorded data
print(f"Recorded {len(lob_recorder.events)} LOB events")
```

## Working with Symbols

### Filtering by Symbol

You can filter data to specific symbols during processing:

```python
from meatpy.itch50 import ITCH50MessageReader, ITCH50Writer

# Extract data for specific symbols
with ITCH50MessageReader("full_data.txt.gz") as reader:
    with ITCH50Writer("filtered_data.itch50", symbols=["AAPL", "SPY"]) as writer:
        for message in reader:
            writer.process_message(message)
```

## Data Export

### CSV Export

```python
from meatpy.event_handlers import LOBRecorder

# After processing with LOBRecorder
with open("lob_data.csv", "w") as f:
    lob_recorder.write_csv(f)
```

### Parquet Export

```python
import pyarrow as pa
from meatpy.writers import ParquetWriter

# Create a custom event handler that uses ParquetWriter
# (See examples for complete implementation)
```

## Performance Tips

1. **Memory Management**: For large files, process data in chunks and clear intermediate results
2. **Symbol Filtering**: Filter early to reduce memory usage
3. **Event Handlers**: Only use necessary event handlers to minimize overhead
4. **File Formats**: Use compressed input files (.gz) to reduce I/O time

## Next Steps

- Explore detailed [Examples](examples.md) for common use cases
- Check the [API Reference](../api/overview.md) for complete method documentation
- See the [Contributing Guide](../contributing.md) to contribute to the project
