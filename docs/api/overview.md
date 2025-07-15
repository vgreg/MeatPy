# API Reference

This section provides detailed documentation for MeatPy's public API.

## Core Modules

### `meatpy.market_processor`

The `MarketProcessor` is the main class for processing market messages and maintaining order book state.

```python
from meatpy.market_processor import MarketProcessor
```

**Key Methods:**
- `process_message(message)`: Process a single market message
- `get_lob(symbol)`: Get the current limit order book for a symbol
- `add_event_handler(handler)`: Register an event handler
- `get_trading_status(symbol)`: Get current trading status for a symbol

### `meatpy.lob`

The `LimitOrderBook` class represents the current state of buy and sell orders.

```python
from meatpy.lob import LimitOrderBook
```

**Key Properties:**
- `bids`: Dictionary of bid price levels
- `asks`: Dictionary of ask price levels
- `best_bid`: Best (highest) bid level
- `best_ask`: Best (lowest) ask level

**Key Methods:**
- `add_order(side, price, size, order_id)`: Add a new order
- `cancel_order(order_id)`: Cancel an existing order
- `execute_order(order_id, executed_size)`: Execute part or all of an order

### `meatpy.message_reader`

Abstract base class for reading market data messages.

```python
from meatpy.message_reader import MessageReader
```

**Key Methods:**
- `__iter__()`: Iterate over messages in the file
- `__enter__()` / `__exit__()`: Context manager support

## ITCH 5.0 Specific Modules

### `meatpy.itch50.ITCH50MessageReader`

Reader for NASDAQ ITCH 5.0 format files.

```python
from meatpy.itch50 import ITCH50MessageReader

with ITCH50MessageReader("data.txt.gz") as reader:
    for message in reader:
        print(message)
```

**Constructor Parameters:**
- `file_path`: Path to the ITCH file (supports .gz compression)
- `buffer_size`: Buffer size for reading (default: 8192)

### `meatpy.itch50.ITCH50MarketProcessor`

Market processor specifically designed for ITCH 5.0 messages.

```python
from meatpy.itch50 import ITCH50MarketProcessor

processor = ITCH50MarketProcessor()
```

**Key Features:**
- Handles all ITCH 5.0 message types
- Maintains separate order books for each symbol
- Tracks trading status changes
- Supports event handlers

### `meatpy.itch50.ITCH50Writer`

Writer for creating filtered ITCH 5.0 files.

```python
from meatpy.itch50 import ITCH50Writer

with ITCH50Writer("output.itch50", symbols=["AAPL", "SPY"]) as writer:
    writer.process_message(message)
```

**Constructor Parameters:**
- `file_path`: Output file path
- `symbols`: List of symbols to include (optional, includes all if None)

## Event Handlers

### `meatpy.event_handlers.LOBRecorder`

Records limit order book events for analysis.

```python
from meatpy.event_handlers import LOBRecorder

recorder = LOBRecorder()
processor.add_event_handler(recorder)

# After processing
recorder.write_csv(output_file)
```

### `meatpy.event_handlers.OFIRecorder`

Calculates and records Order Flow Imbalance metrics.

```python
from meatpy.event_handlers import OFIRecorder

ofi_recorder = OFIRecorder()
```

## Types and Data Structures

### Core Types

MeatPy uses generic types for flexibility across different data formats:

```python
from meatpy.types import Price, Volume, OrderID, TradeRef
```

- `Price`: Numeric type for prices
- `Volume`: Numeric type for volumes/sizes
- `OrderID`: Identifier type for orders
- `TradeRef`: Reference type for trades

### Trading Status

```python
from meatpy.trading_status import TradingStatus

# Available statuses
TradingStatus.HALTED
TradingStatus.QUOTE_ONLY
TradingStatus.TRADING
TradingStatus.CLOSING_AUCTION
```

## Message Types (ITCH 5.0)

### System Messages
- `SystemEventMessage`: System-wide events
- `StockDirectoryMessage`: Symbol information
- `StockTradingActionMessage`: Trading halts and resumptions

### Order Messages
- `AddOrderMessage`: New order placement
- `AddOrderMPIDMessage`: New order with MPID attribution
- `OrderExecutedMessage`: Order execution
- `OrderExecutedWithPriceMessage`: Order execution with price
- `OrderCancelMessage`: Order cancellation
- `OrderDeleteMessage`: Order deletion
- `OrderReplaceMessage`: Order modification

### Trade Messages
- `TradeMessage`: Non-cross trade
- `CrossTradeMessage`: Cross trade

## Error Handling

Common exceptions you may encounter:

```python
from meatpy.exceptions import (
    MeatPyError,
    MessageParsingError,
    InvalidMessageError,
    FileFormatError
)
```

## Utility Functions

### File Validation

```python
from meatpy.utils import validate_itch_file, get_file_info

# Check if file is valid ITCH format
is_valid = validate_itch_file("data.txt.gz")

# Get basic file information
info = get_file_info("data.txt.gz")
print(f"Message count: {info['message_count']}")
print(f"Symbols: {info['symbols']}")
```

### Performance Utilities

```python
from meatpy.utils import ProgressReporter

# Track processing progress
reporter = ProgressReporter(total_messages=1000000)
for i, message in enumerate(reader):
    processor.process_message(message)
    reporter.update(i)
```

## Configuration

### Processing Configuration

```python
from meatpy.config import ProcessingConfig

config = ProcessingConfig(
    track_lob=True,
    max_lob_depth=10,
    enable_validation=True,
    output_directory="output/"
)
```

### Performance Settings

```python
from meatpy.config import PerformanceConfig

perf_config = PerformanceConfig(
    buffer_size=65536,
    batch_size=10000,
    enable_caching=True
)
```

For complete API documentation with detailed method signatures and examples, see the individual module documentation.
