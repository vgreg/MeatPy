# IEX DEEP Guide

This guide covers working with IEX DEEP market data in MeatPy.

## Overview

IEX DEEP is a market data feed from IEX Exchange that provides real-time depth of book quotations. Unlike NASDAQ ITCH which provides individual order-level data, IEX DEEP provides **aggregated price-level data** - the total size available at each price level rather than individual orders.

### Key Characteristics

| Feature | IEX DEEP | NASDAQ ITCH |
|---------|----------|-------------|
| Data granularity | Price levels (aggregated) | Individual orders |
| Byte order | Little endian | Big endian |
| Timestamps | Nanoseconds since POSIX epoch | Nanoseconds since midnight |
| File format | PCAP/PCAP-NG | Raw binary |
| Price format | 8 bytes, 4 decimal places | 4 bytes, 4 decimal places |

## Data Format

IEX DEEP data is distributed in PCAP or PCAP-NG file format, with messages encapsulated in the IEX Transport Protocol (IEX-TP). MeatPy handles all the transport layer parsing automatically.

### Message Types

IEX DEEP 1.0 includes 12 message types:

| Type | Code | Description |
|------|------|-------------|
| System Event | S | Market-wide events (start/end of day) |
| Security Directory | D | Security information for IEX-listed securities |
| Trading Status | H | Trading status updates (halted, trading, etc.) |
| Operational Halt | O | Operational halt status |
| Short Sale Price Test | P | Short sale restriction status |
| Security Event | E | Opening/closing auction events |
| Price Level Update (Buy) | 8 | Bid side price level update |
| Price Level Update (Sell) | 5 | Ask side price level update |
| Trade Report | T | Trade execution reports |
| Official Price | X | Official opening/closing prices |
| Trade Break | B | Trade cancellation |
| Auction Information | A | Auction imbalance information |

## Basic Usage

### Reading Messages

```python
from meatpy.iex_deep import IEXDEEPMessageReader

reader = IEXDEEPMessageReader()

# Read from a PCAP file (supports .gz, .bz2, .xz compression)
for message in reader.read_file("data_feeds_20180529_DEEP1.0.pcap.gz"):
    print(f"{type(message).__name__}: {message.timestamp}")
```

### Processing Messages

The `IEXDEEPMarketProcessor` reconstructs the order book for a specific symbol:

```python
from meatpy.iex_deep import IEXDEEPMessageReader, IEXDEEPMarketProcessor

# Create a processor for SPY
processor = IEXDEEPMarketProcessor("SPY")
reader = IEXDEEPMessageReader()

for message in reader.read_file("data_feeds_20180529_DEEP1.0.pcap.gz"):
    processor.process_message(message)

# Get the current best bid and offer
best_bid = processor.get_best_bid()  # Returns (price, size) or None
best_ask = processor.get_best_ask()  # Returns (price, size) or None
bbo = processor.get_bbo()            # Returns (best_bid, best_ask)

if best_bid and best_ask:
    # Prices are in integer format with 4 decimal places
    bid_price = best_bid[0] / 10000
    ask_price = best_ask[0] / 10000
    print(f"BBO: ${bid_price:.4f} x {best_bid[1]} | ${ask_price:.4f} x {best_ask[1]}")
```

### Accessing Price Levels

The processor maintains dictionaries of all price levels:

```python
# Access all bid levels (price -> size)
for price in sorted(processor._bid_levels.keys(), reverse=True):
    size = processor._bid_levels[price]
    print(f"Bid: ${price/10000:.4f} x {size}")

# Access all ask levels (price -> size)
for price in sorted(processor._ask_levels.keys()):
    size = processor._ask_levels[price]
    print(f"Ask: ${price/10000:.4f} x {size}")
```

### Tracking Trades

Trade IDs are tracked automatically:

```python
# After processing messages
print(f"Number of trades: {len(processor._trade_ids)}")
```

## Working with Specific Message Types

### Price Level Updates

Price level updates tell you the new total size at a price level. A size of 0 means the level should be removed:

```python
from meatpy.iex_deep.iex_deep_market_message import (
    PriceLevelUpdateBuySideMessage,
    PriceLevelUpdateSellSideMessage,
)

for message in reader.read_file(filename):
    if isinstance(message, PriceLevelUpdateBuySideMessage):
        symbol = message.symbol.decode().strip()
        price = message.price / 10000
        size = message.size
        print(f"BID {symbol}: ${price:.4f} x {size}")

    elif isinstance(message, PriceLevelUpdateSellSideMessage):
        symbol = message.symbol.decode().strip()
        price = message.price / 10000
        size = message.size
        print(f"ASK {symbol}: ${price:.4f} x {size}")
```

### Trade Reports

```python
from meatpy.iex_deep.iex_deep_market_message import TradeReportMessage

for message in reader.read_file(filename):
    if isinstance(message, TradeReportMessage):
        symbol = message.symbol.decode().strip()
        price = message.price / 10000
        size = message.size
        trade_id = message.trade_id
        print(f"TRADE {symbol}: {size} @ ${price:.4f} (ID: {trade_id})")
```

### System Events

```python
from meatpy.iex_deep.iex_deep_market_message import SystemEventMessage

SYSTEM_EVENTS = {
    b"O": "Start of Messages",
    b"S": "Start of System Hours",
    b"R": "Start of Regular Market Hours",
    b"M": "End of Regular Market Hours",
    b"E": "End of System Hours",
    b"C": "End of Messages",
}

for message in reader.read_file(filename):
    if isinstance(message, SystemEventMessage):
        event_name = SYSTEM_EVENTS.get(message.system_event, "Unknown")
        print(f"System Event: {event_name}")
```

## Differences from ITCH Processing

### No Individual Order Tracking

Unlike ITCH, IEX DEEP does not provide individual order IDs for quotes. The processor tracks aggregated price levels only:

```python
# ITCH: tracks individual orders
# processor.current_lob.bid_levels[0].queue  # List of individual orders

# IEX DEEP: tracks aggregated levels
# processor._bid_levels  # {price: total_size}
```

### Timestamp Handling

IEX DEEP timestamps are nanoseconds since the POSIX epoch (January 1, 1970), not nanoseconds since midnight like ITCH:

```python
import datetime

# Convert IEX DEEP timestamp to datetime
timestamp_ns = message.timestamp
timestamp_s = timestamp_ns / 1_000_000_000
dt = datetime.datetime.fromtimestamp(timestamp_s, tz=datetime.timezone.utc)
print(f"Time: {dt}")
```

## Data Sources

IEX DEEP historical data can be obtained from:

- [IEX Cloud](https://iexcloud.io/) - Historical DEEP data
- [IEX Exchange](https://exchange.iex.io/products/market-data/) - Direct exchange data

Sample data files are typically named like:
```
data_feeds_YYYYMMDD_YYYYMMDD_IEXTP1_DEEP1.0.pcap.gz
```

## API Reference

### IEXDEEPMessageReader

```python
class IEXDEEPMessageReader:
    def read_file(self, filename: str) -> Generator[IEXDEEPMarketMessage, None, None]:
        """Read messages from a PCAP/PCAP-NG file.

        Supports compressed files (.gz, .bz2, .xz, .zip).
        """
```

### IEXDEEPMarketProcessor

```python
class IEXDEEPMarketProcessor:
    def __init__(self, instrument: str | bytes, book_date: datetime = None, track_lob: bool = False):
        """Initialize processor for a specific symbol.

        Args:
            instrument: Symbol to track (e.g., "SPY")
            book_date: Trading date (optional, defaults to current date)
            track_lob: Whether to track full LOB (default False)
        """

    def process_message(self, message: IEXDEEPMarketMessage) -> None:
        """Process a single market message."""

    def get_best_bid(self) -> tuple[int, int] | None:
        """Get best bid (price, size) or None if no bids."""

    def get_best_ask(self) -> tuple[int, int] | None:
        """Get best ask (price, size) or None if no asks."""

    def get_bbo(self) -> tuple[tuple[int, int] | None, tuple[int, int] | None]:
        """Get (best_bid, best_ask) tuple."""
```
