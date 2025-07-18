"""Top of Book Snapshots from ITCH 4.1 File

This script demonstrates how to capture best bid and ask prices at regular intervals
from ITCH 4.1 data. Based on the pattern from MeatPy documentation notebooks.
"""

from pathlib import Path
import datetime
from meatpy.itch41 import ITCH41MessageReader, ITCH41MarketProcessor
from meatpy.event_handlers.lob_recorder import LOBRecorder
from meatpy.writers.csv_writer import CSVWriter

# Define paths and parameters
data_dir = Path("data")
output_dir = data_dir / "output"
output_dir.mkdir(exist_ok=True)

# You can use either the original file or a filtered file from Step1
file_path = data_dir / "S083012-v41.txt.gz"
# Alternative: use filtered file if available
# file_path = data_dir / "S083012-v41-AAPL-MSFT.itch41.gz"

outfile_path = output_dir / "aapl_tob.csv"
stock_symbol = "AAPL"
book_date = datetime.datetime(2012, 8, 30)  # Date from sample file S083012

print(f"Input file: {file_path}")
if not file_path.exists():
    print("⚠️  Sample file not found - this is expected in most setups")
    print("You can download ITCH 4.1 sample files or use your own data")
    print("Or run Step1_Parsing.py first to create a filtered file")
    exit(1)

print(f"Processing {stock_symbol} for date: {book_date.date()}")
print(f"Output file: {outfile_path}")

# Create market processor and recorder
with ITCH41MessageReader(file_path) as reader, CSVWriter(outfile_path) as writer:
    processor = ITCH41MarketProcessor(stock_symbol, book_date)

    # We only care about the top of book
    tob_recorder = LOBRecorder(writer=writer, max_depth=1)

    # Generate timestamps for snapshots during market hours
    # Market typically opens at 9:30 AM and closes at 4:00 PM
    market_open = book_date + datetime.timedelta(hours=9, minutes=30)
    market_close = book_date + datetime.timedelta(hours=16, minutes=0)

    # Create list of timestamps every minute during market hours
    record_timestamps = []
    current = market_open
    while current <= market_close:
        record_timestamps.append(current)
        current += datetime.timedelta(minutes=1)

    tob_recorder.record_timestamps = record_timestamps
    print(
        f"Will capture {len(record_timestamps)} snapshots from {market_open.time()} to {market_close.time()}"
    )

    # Attach the recorder to the processor
    processor.handlers.append(tob_recorder)

    # Process all messages
    message_count = 0
    stock_message_count = 0

    for message in reader:
        message_count += 1

        # Process system messages and messages for our stock
        if (
            message.type == b"S"  # System messages
            or (
                hasattr(message, "stock")
                and message.stock.decode().strip() == stock_symbol
            )
        ):
            if hasattr(message, "stock"):
                stock_message_count += 1

            processor.process_message(message)

        # Progress update
        if message_count % 50000 == 0:
            print(
                f"Processed {message_count:,} total messages, {stock_message_count:,} for {stock_symbol}"
            )

print("\n✅ Processing complete!")
print(f"Total messages processed: {message_count:,}")
print(f"Messages for {stock_symbol}: {stock_message_count:,}")

if outfile_path.exists():
    file_size_kb = outfile_path.stat().st_size / 1024
    print(f"Output file size: {file_size_kb:.1f} KB")
    print(f"Top of book data saved to: {outfile_path}")

    # Show first few lines of output
    print("\nFirst few lines of output:")
    with open(outfile_path, "r") as f:
        for i, line in enumerate(f):
            if i >= 5:  # Show first 5 lines
                break
            print(f"  {line.strip()}")
else:
    print("❌ No output file was created")
