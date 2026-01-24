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

- **ITCH 4.1/5.0**: NASDAQ's binary market data format (order-level data)
- **IEX DEEP 1.0**: IEX Exchange's market data format (price-level data)

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


## Reading IEX DEEP Data

IEX DEEP data comes in PCAP/PCAP-NG format. Here's how to read it:

```python
from meatpy.iex_deep import IEXDEEPMessageReader, IEXDEEPMarketProcessor

# Read messages from a PCAP file
reader = IEXDEEPMessageReader()
for i, message in enumerate(reader.read_file("data_feeds_20180529_DEEP1.0.pcap.gz")):
    print(f"Message {i}: {type(message).__name__}")
    if i >= 10:
        break

# Process messages and reconstruct order book for a specific symbol
processor = IEXDEEPMarketProcessor("SPY")
for message in reader.read_file("data_feeds_20180529_DEEP1.0.pcap.gz"):
    processor.process_message(message)

# Get best bid and offer
bbo = processor.get_bbo()
if bbo[0] and bbo[1]:
    print(f"Best Bid: ${bbo[0][0]/10000:.2f} x {bbo[0][1]}")
    print(f"Best Ask: ${bbo[1][0]/10000:.2f} x {bbo[1][1]}")
```

For more details on IEX DEEP, see the [IEX DEEP Guide](iex-deep.md).

## Other Common Tasks

- **Listing Symbols**: Extracting unique stock symbols from ITCH files
- **Extracting Specific Symbols**: Creating new ITCH files with only specific symbols
- **Top of Book Snapshots**: Generating snapshots of the top of book state for analysis
- **Order Book Snapshots**: Creating snapshots of the full limit order book state
