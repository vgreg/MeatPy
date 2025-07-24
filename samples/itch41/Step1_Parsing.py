"""Extracting Specific Symbols from ITCH 4.1 File

This script demonstrates how to create a new ITCH 4.1 file containing only data
for specific symbols of interest. Based on the pattern from MeatPy documentation.
"""

from pathlib import Path

from meatpy.itch41 import ITCH41MessageReader, ITCH41Writer

# Define paths
data_dir = Path("data")
input_file = data_dir / "S083012-v41.txt.gz"
output_file = data_dir / "S083012-v41-AAPL-SPY.itch41.gz"

# Symbols we want to extract
target_symbols = ["AAPL", "SPY"]

print(f"Input file: {input_file}")
if input_file.exists():
    input_size_mb = input_file.stat().st_size / (1024**2)
    print(f"Input file size: {input_size_mb:.2f} MB")
else:
    print("⚠️  Sample file not found - this is expected in most setups")
    print("You can download ITCH 4.1 sample files or use your own data")
    exit(1)

print(f"Extracting symbols: {target_symbols}")
print(f"Output file: {output_file}")

# Process the file and filter for target symbols
message_count = 0
with (
    ITCH41MessageReader(input_file) as reader,
    ITCH41Writer(output_file, symbols=target_symbols) as writer,
):
    for message in reader:
        message_count += 1
        writer.process_message(message)

        # Progress update every 10,000 messages
        if message_count % 10000 == 0:
            print(f"Processed {message_count:,} messages...")

print(f"Total messages processed: {message_count:,}")

# # Check the filtered file
# if output_file.exists():
#     new_message_count = 0
#     with ITCH41MessageReader(output_file) as reader:
#         for message in reader:
#             print(message)
#             new_message_count += 1

#     print(f"Total messages in filtered file: {new_message_count:,}")
#     output_size_mb = output_file.stat().st_size / (1024**2)
#     print(f"Output file size: {output_size_mb:.2f} MB")

#     size_reduction = (1 - output_size_mb / input_size_mb) * 100
#     print(f"Size reduction: {size_reduction:.1f}%")

#     print(f"\n✅ Filtered file created: {output_file}")
# else:
#     print("❌ Failed to create output file")
