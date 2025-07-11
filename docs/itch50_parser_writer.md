# ITCH 5.0 Parser and Writer

This document describes the decoupled ITCH 5.0 parser and writer classes that provide a clean separation of concerns for processing ITCH market data files.

## Overview

The original `ITCH50MessageParser` class combined parsing and writing functionality, which made it complex and difficult to use for different scenarios. The new design separates these concerns into two distinct classes:

- **`ITCH50MessageReader`**: A generator-based parser that yields messages one at a time
- **`ITCH50Writer`**: A writer that handles buffering and writing messages to files

Both classes support the context manager protocol (`with` statement) for automatic resource management.

## ITCH50MessageReader

The `ITCH50MessageReader` class provides a clean generator interface for parsing ITCH 5.0 files.

### Features

- **Natural interface**: Pass file path to constructor and iterate directly
- **Generator interface**: Use `for` loops to iterate through messages
- **Automatic compression detection**: Supports gzip, bzip2, xz, and zip files
- **Message filtering**: Filter by message types and symbols
- **Memory efficient**: Processes messages one at a time
- **Context manager support**: Use with `with` statements for automatic file handling

### Usage

#### Natural Interface (Recommended)

```python
from meatpy.itch50 import ITCH50MessageReader

# Parse all messages (natural interface)
with ITCH50MessageReader("data.itch") as parser:
    for message in parser:
        print(f"Message: {message.__class__.__name__}")

# Parse only specific message types
with ITCH50MessageReader("data.itch", keep_message_types=b"RAP") as parser:  # Stock directory, add order, trade
    for message in parser:
        print(f"Message: {message.__class__.__name__}")

# Parse only specific symbols
symbols = [b"AAPL   ", b"MSFT   "]  # Note: 8-byte padded
with ITCH50MessageReader("data.itch", symbols=symbols) as parser:
    for message in parser:
        print(f"Message: {message.__class__.__name__}")
```

#### Legacy Interface (Still Supported)

```python
# Parse all messages (legacy interface)
parser = ITCH50MessageReader()
for message in parser.parse_file("data.itch"):
    print(f"Message: {message.__class__.__name__}")

# Parse with context manager (legacy style)
with ITCH50MessageReader() as parser:
    for message in parser.parse_file("data.itch"):
        print(f"Message: {message.__class__.__name__}")
```

### Supported Compression Formats

The parser automatically detects and handles:
- **gzip** (`.gz`)
- **bzip2** (`.bz2`)
- **xz** (`.xz`)
- **zip** (`.zip`)

## ITCH50Writer

The `ITCH50Writer` class handles writing ITCH messages to files with buffering and compression support.

### Features

- **Symbol filtering**: Write messages for specific symbols only
- **Message buffering**: Configurable buffer size for memory efficiency
- **Compression support**: Write compressed files (gzip, bzip2, xz)
- **Order tracking**: Automatically tracks order references and matches
- **System message handling**: Properly handles system messages that apply to all symbols
- **Context manager support**: Use with `with` statements for automatic flushing

### Usage

```python
from meatpy.itch50 import ITCH50Writer

# Basic usage (without context manager)
writer = ITCH50Writer(output_path="output.itch")
writer.process_message(message)
writer.flush()
writer.close()

# With context manager (recommended)
with ITCH50Writer(output_path="output.itch") as writer:
    writer.process_message(message)
    # Automatically flushes on exit

# With compression
with ITCH50Writer(
    output_path="output.itch.gz",
    compress=True,
    compression_type="gzip"
) as writer:
    writer.process_message(message)

# For specific symbols
with ITCH50Writer(
    symbols=[b"AAPL   ", b"MSFT   "],
    output_path="symbols.itch",
    message_buffer=1000
) as writer:
    writer.process_message(message)
```

## Combined Usage

The typical workflow involves using both classes together with context managers:

### Natural Interface (Recommended)

```python
from meatpy.itch50 import ITCH50MessageReader, ITCH50Writer

# Single parser with single writer
with ITCH50MessageReader("input.itch") as parser:
    with ITCH50Writer(output_path="output.itch", compress=True) as writer:
        for message in parser:
            writer.process_message(message)

# Multiple writers
with ITCH50MessageReader("input.itch", keep_message_types=b"AFECXDP") as parser:
    with ITCH50Writer(output_path="orders.itch", compress=True) as order_writer:
        with ITCH50Writer(output_path="trades.itch", compress=True) as trade_writer:
            for message in parser:
                order_writer.process_message(message)
                trade_writer.process_message(message)
```

### Legacy Interface

```python
# Parse and distribute messages
parser = ITCH50MessageReader(keep_message_types=b"AFECXDP")  # Order and trade messages
order_writer = ITCH50Writer(output_path="orders.itch", compress=True)
trade_writer = ITCH50Writer(output_path="trades.itch", compress=True)

for message in parser.parse_file("input.itch"):
    order_writer.process_message(message)
    trade_writer.process_message(message)

# Flush all writers
order_writer.flush()
trade_writer.flush()
order_writer.close()
trade_writer.close()
```

## Message Types

The parser and writer support all ITCH 5.0 message types:

- **S**: System Event Message
- **R**: Stock Directory Message
- **H**: Stock Trading Action Message
- **Y**: Reg SHO Short Sale Message
- **L**: Market Participant Position Message
- **V**: MWCB Decline Level Message
- **W**: MWCB Breach Message
- **K**: IPO Quoting Period Update Message
- **J**: LULD Auction Collar Message
- **h**: Operational Halt Message
- **A**: Add Order Message
- **F**: Add Order MPID Message
- **E**: Order Executed Message
- **C**: Order Executed Price Message
- **X**: Order Cancel Message
- **D**: Order Delete Message
- **U**: Order Replace Message
- **P**: Trade Message
- **Q**: Cross Trade Message
- **B**: Broken Trade Message
- **I**: NOII Message
- **N**: RPI Message
- **O**: Direct Listing Capital Raise Message

## Performance Considerations

- **Memory usage**: The parser processes messages one at a time, making it memory efficient for large files
- **Buffering**: The writer buffers messages before writing to disk, reducing I/O operations
- **Compression**: Use compression for large output files to save disk space
- **Symbol filtering**: Filter by symbols early to reduce processing overhead
- **Context managers**: Use `with` statements to ensure proper resource cleanup

## Migration from ITCH50MessageParser

If you're migrating from the old `ITCH50MessageParser`:

1. Replace parser instantiation:
   ```python
   # Old
   parser = ITCH50MessageParser()
   parser.parse_file("file.itch", write=True)

   # New (natural interface)
   with ITCH50MessageReader("file.itch") as parser:
       with ITCH50Writer(output_path="output.itch") as writer:
           for message in parser:
               writer.process_message(message)
   ```

2. Use the generator interface instead of callbacks
3. Use context managers for automatic resource management
4. Handle buffering explicitly with the writer's `flush()` method if not using context managers
