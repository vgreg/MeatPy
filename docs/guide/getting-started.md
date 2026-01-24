# Getting Started with MeatPy

This guide will help you get started with MeatPy for processing financial market data.

## Basic Concepts

### Core Components

- **MarketProcessor**: Processes market messages and maintains order book state
- **MessageReader**: Reads market data from files in various formats
- **LimitOrderBook (LOB)**: Represents the current state of buy and sell orders
- **Event Handlers**: Process and record market events as they occur

### Supported Data Formats

MeatPy supports multiple versions of the NASDAQ ITCH protocol:

| Version | Format | Stock Symbol Size | Timestamp | Module |
|---------|--------|-------------------|-----------|--------|
| **ITCH 5.0** | Binary | 8 characters | Nanoseconds | `meatpy.itch50` |
| **ITCH 4.1** | Binary | 8 characters | Nanoseconds | `meatpy.itch41` |
| **ITCH 4.0** | Binary | 6 characters | Nanoseconds | `meatpy.itch4` |
| **ITCH 3.0** | ASCII | 6 characters | Milliseconds | `meatpy.itch3` |
| **ITCH 2.0** | ASCII | 6 characters | Milliseconds | `meatpy.itch2` |

Each version has its own `MessageReader`, `MarketProcessor`, and message classes following the same patterns.

MeatPy also supports:

- **IEX DEEP 1.0**: IEX Exchange's market data format (price-level data) via `meatpy.iex_deep`

## Basic Usage

### Reading ITCH 5.0 Data (Binary)

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

### Reading Other ITCH Versions

Each ITCH version follows the same interface pattern:

```python
# ITCH 4.1 (Binary, 8-char symbols)
from meatpy.itch41 import ITCH41MessageReader, ITCH41MarketProcessor

# ITCH 4.0 (Binary, 6-char symbols)
from meatpy.itch4 import ITCH4MessageReader, ITCH4MarketProcessor

# ITCH 3.0 (ASCII, separate timestamp messages)
from meatpy.itch3 import ITCH3MessageReader, ITCH3MarketProcessor

# ITCH 2.0 (ASCII, embedded timestamps)
from meatpy.itch2 import ITCH2MessageReader, ITCH2MarketProcessor
```

### Building a Limit Order Book

```python
import datetime
from meatpy.itch50 import ITCH50MessageReader, ITCH50MarketProcessor

book_date = datetime.datetime(2021, 8, 13)
processor = ITCH50MarketProcessor("AAPL", book_date)

with ITCH50MessageReader("market_data.txt.gz") as reader:
    for message in reader:
        processor.process_message(message)

# Access the limit order book
if processor.lob:
    print(f"Best bid: ${processor.lob.best_bid / 10000:.2f}")
    print(f"Best ask: ${processor.lob.best_ask / 10000:.2f}")
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
