# Examples

This page provides practical examples for common MeatPy use cases. All examples use the sample file `S081321-v50.txt.gz`.

!!! note "Sample Data"
    The examples reference `S081321-v50.txt.gz` which should be placed in your working directory. This file is not included in the repository due to size constraints.

## Listing Symbols in an ITCH 5.0 File

This example shows how to extract all available symbols from an ITCH 5.0 file:

```python
from meatpy.itch50 import ITCH50MessageReader

def list_symbols(file_path):
    """Extract all symbols from an ITCH 5.0 file."""
    symbols = set()

    with ITCH50MessageReader(file_path) as reader:
        for message in reader:
            # Stock Directory messages (type 'R') contain symbol information
            if message.message_type == b'R':
                symbol = message.stock.decode().strip()
                symbols.add(symbol)
            # We can break early since all stock directory messages
            # appear at the beginning of the file
            elif len(symbols) > 0 and message.message_type != b'R':
                # Once we've seen stock directory messages and encounter
                # a different message type, we've likely seen all symbols
                pass

    return sorted(symbols)

# Usage
if __name__ == "__main__":
    file_path = "S081321-v50.txt.gz"
    symbols = list_symbols(file_path)

    print(f"Found {len(symbols)} symbols:")
    for symbol in symbols:
        print(f"  {symbol}")
```

## Extracting Specific Symbols (AAPL and SPY)

This example demonstrates how to create a new ITCH file containing only data for specific symbols:

```python
from pathlib import Path
from meatpy.itch50 import ITCH50MessageReader, ITCH50Writer

def extract_symbols(input_file, output_file, symbols):
    """Extract data for specific symbols from an ITCH file."""
    symbols_bytes = [symbol.encode().ljust(8) for symbol in symbols]

    message_count = 0
    filtered_count = 0

    with ITCH50MessageReader(input_file) as reader:
        with ITCH50Writer(output_file, symbols=symbols) as writer:
            for message in reader:
                message_count += 1

                # Process all system messages and stock directory messages
                if (message.message_type in [b'S', b'R', b'H', b'Y', b'L', b'V', b'W', b'K', b'J']
                    or not hasattr(message, 'stock')):
                    writer.process_message(message)
                    filtered_count += 1
                # Process messages for our target symbols
                elif hasattr(message, 'stock') and message.stock in symbols_bytes:
                    writer.process_message(message)
                    filtered_count += 1

                if message_count % 1_000_000 == 0:
                    print(f"Processed {message_count:,} messages, "
                          f"kept {filtered_count:,} messages")

    print(f"Extraction complete: {filtered_count:,} messages written to {output_file}")
    return filtered_count

# Usage
if __name__ == "__main__":
    input_file = "S081321-v50.txt.gz"
    output_file = "S081321-v50-AAPL-SPY.itch50"
    target_symbols = ["AAPL", "SPY"]

    extract_symbols(input_file, output_file, target_symbols)

    # Verify the output by reading a few messages
    print("\nFirst 10 messages in filtered file:")
    with ITCH50MessageReader(output_file) as reader:
        for i, message in enumerate(reader):
            if i >= 10:
                break
            if hasattr(message, 'stock'):
                symbol = message.stock.decode().strip()
                print(f"  {i}: {message.message_type.decode()} - {symbol}")
            else:
                print(f"  {i}: {message.message_type.decode()} - System message")
```

## Extracting Top of Book Snapshots at One-Minute Intervals

This example captures the best bid and ask prices at regular intervals:

```python
from datetime import datetime, timedelta
from meatpy.itch50 import ITCH50MessageReader, ITCH50MarketProcessor

def extract_top_of_book_snapshots(file_path, symbols, interval_minutes=1):
    """Extract top of book snapshots at regular intervals."""
    processor = ITCH50MarketProcessor()
    snapshots = []

    # Convert interval to nanoseconds
    interval_ns = interval_minutes * 60 * 1_000_000_000
    next_snapshot_time = None

    with ITCH50MessageReader(file_path) as reader:
        for message in reader:
            processor.process_message(message)

            # Initialize snapshot time based on first message
            if next_snapshot_time is None and hasattr(message, 'timestamp'):
                next_snapshot_time = message.timestamp + interval_ns

            # Check if it's time for a snapshot
            if (hasattr(message, 'timestamp') and
                message.timestamp >= next_snapshot_time):

                # Take snapshot for each symbol
                for symbol in symbols:
                    lob = processor.get_lob(symbol)
                    if lob and lob.best_bid and lob.best_ask:
                        snapshot = {
                            'timestamp': message.timestamp,
                            'symbol': symbol,
                            'best_bid': lob.best_bid.price,
                            'best_bid_size': lob.best_bid.size,
                            'best_ask': lob.best_ask.price,
                            'best_ask_size': lob.best_ask.size,
                            'spread': lob.best_ask.price - lob.best_bid.price,
                            'mid_price': (lob.best_bid.price + lob.best_ask.price) / 2
                        }
                        snapshots.append(snapshot)

                # Set next snapshot time
                next_snapshot_time += interval_ns

                if len(snapshots) % 100 == 0:
                    print(f"Captured {len(snapshots)} snapshots")

    return snapshots

def save_snapshots_to_csv(snapshots, output_file):
    """Save snapshots to CSV file."""
    import csv

    if not snapshots:
        print("No snapshots to save")
        return

    fieldnames = snapshots[0].keys()

    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(snapshots)

    print(f"Saved {len(snapshots)} snapshots to {output_file}")

# Usage
if __name__ == "__main__":
    file_path = "S081321-v50.txt.gz"
    symbols = ["AAPL", "SPY"]

    # Extract 1-minute snapshots
    snapshots = extract_top_of_book_snapshots(file_path, symbols, interval_minutes=1)

    # Save to CSV
    save_snapshots_to_csv(snapshots, "top_of_book_snapshots.csv")

    # Display summary
    if snapshots:
        print(f"\nSnapshot Summary:")
        print(f"Total snapshots: {len(snapshots)}")
        print(f"Symbols: {set(s['symbol'] for s in snapshots)}")
        print(f"Time range: {min(s['timestamp'] for s in snapshots)} to {max(s['timestamp'] for s in snapshots)}")
```

## Extracting Full Limit Order Book Snapshots at One-Minute Intervals

This example captures the full order book depth at regular intervals:

```python
from meatpy.itch50 import ITCH50MessageReader, ITCH50MarketProcessor

def extract_lob_snapshots(file_path, symbols, interval_minutes=1, max_depth=10):
    """Extract full limit order book snapshots at regular intervals."""
    processor = ITCH50MarketProcessor()
    snapshots = []

    # Convert interval to nanoseconds
    interval_ns = interval_minutes * 60 * 1_000_000_000
    next_snapshot_time = None

    with ITCH50MessageReader(file_path) as reader:
        for message in reader:
            processor.process_message(message)

            # Initialize snapshot time
            if next_snapshot_time is None and hasattr(message, 'timestamp'):
                next_snapshot_time = message.timestamp + interval_ns

            # Check if it's time for a snapshot
            if (hasattr(message, 'timestamp') and
                message.timestamp >= next_snapshot_time):

                # Take snapshot for each symbol
                for symbol in symbols:
                    lob = processor.get_lob(symbol)
                    if lob:
                        snapshot = capture_lob_snapshot(lob, symbol, message.timestamp, max_depth)
                        if snapshot:
                            snapshots.append(snapshot)

                # Set next snapshot time
                next_snapshot_time += interval_ns

                if len(snapshots) % 50 == 0:
                    print(f"Captured {len(snapshots)} LOB snapshots")

    return snapshots

def capture_lob_snapshot(lob, symbol, timestamp, max_depth):
    """Capture a snapshot of the limit order book."""
    if not lob.bids or not lob.asks:
        return None

    snapshot = {
        'timestamp': timestamp,
        'symbol': symbol,
    }

    # Capture bid side (sorted by price descending)
    bid_levels = sorted(lob.bids.items(), key=lambda x: x[0], reverse=True)[:max_depth]
    for i, (price, level) in enumerate(bid_levels):
        snapshot[f'bid_price_{i+1}'] = price
        snapshot[f'bid_size_{i+1}'] = level.size
        snapshot[f'bid_count_{i+1}'] = level.count

    # Capture ask side (sorted by price ascending)
    ask_levels = sorted(lob.asks.items(), key=lambda x: x[0])[:max_depth]
    for i, (price, level) in enumerate(ask_levels):
        snapshot[f'ask_price_{i+1}'] = price
        snapshot[f'ask_size_{i+1}'] = level.size
        snapshot[f'ask_count_{i+1}'] = level.count

    # Add summary statistics
    if bid_levels and ask_levels:
        best_bid = bid_levels[0][0]
        best_ask = ask_levels[0][0]
        snapshot['spread'] = best_ask - best_bid
        snapshot['mid_price'] = (best_bid + best_ask) / 2
        snapshot['total_bid_volume'] = sum(level.size for _, level in bid_levels)
        snapshot['total_ask_volume'] = sum(level.size for _, level in ask_levels)

    return snapshot

def save_lob_snapshots_to_csv(snapshots, output_file):
    """Save LOB snapshots to CSV file."""
    import csv

    if not snapshots:
        print("No snapshots to save")
        return

    # Get all possible field names from all snapshots
    fieldnames = set()
    for snapshot in snapshots:
        fieldnames.update(snapshot.keys())
    fieldnames = sorted(fieldnames)

    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(snapshots)

    print(f"Saved {len(snapshots)} LOB snapshots to {output_file}")

# Usage
if __name__ == "__main__":
    file_path = "S081321-v50.txt.gz"
    symbols = ["AAPL", "SPY"]
    max_depth = 5  # Capture top 5 levels on each side

    # Extract 1-minute LOB snapshots
    snapshots = extract_lob_snapshots(file_path, symbols,
                                    interval_minutes=1, max_depth=max_depth)

    # Save to CSV
    save_lob_snapshots_to_csv(snapshots, "lob_snapshots.csv")

    # Display summary
    if snapshots:
        print(f"\nLOB Snapshot Summary:")
        print(f"Total snapshots: {len(snapshots)}")
        print(f"Symbols: {set(s['symbol'] for s in snapshots)}")
        print(f"Max depth: {max_depth} levels")
```

## Performance Notes

- **Large Files**: The example files can be several GB. Monitor memory usage for large datasets.
- **Filtering Early**: When extracting specific symbols, filter as early as possible to reduce processing time.
- **Batch Processing**: For very large files, consider processing in batches or using streaming approaches.
- **Output Formats**: Consider using Parquet format for large datasets instead of CSV for better compression and performance.

## Error Handling

Always include proper error handling in production code:

```python
try:
    with ITCH50MessageReader(file_path) as reader:
        for message in reader:
            # Process message
            pass
except FileNotFoundError:
    print(f"File {file_path} not found")
except Exception as e:
    print(f"Error processing file: {e}")
```
