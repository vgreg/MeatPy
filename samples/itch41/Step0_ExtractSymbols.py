"""Listing Symbols in an ITCH 4.1 File

This script shows how to extract all available symbols from an ITCH 4.1 file.
Based on the pattern from the MeatPy documentation notebooks.
"""

from pathlib import Path
from meatpy.itch41 import ITCH41MessageReader

# Define the path to our sample data file
script_dir = Path(__file__).parent
data_dir = script_dir / "data"
file_path = data_dir / "S083012-v41.txt.gz"

print(f"Reading ITCH 4.1 file: {file_path}")
if file_path.exists():
    file_size_mb = file_path.stat().st_size / (1024**2)
    print(f"File size: {file_size_mb:.2f} MB")
else:
    print("⚠️  Sample file not found - this is expected in most setups")
    print("You can download ITCH 4.1 sample files or use your own data")
    exit(1)

symbols = set()
message_count = 0

print("Reading ITCH 4.1 file to extract symbols...")

with ITCH41MessageReader(file_path) as reader:
    for message in reader:
        message_count += 1

        # Stock Directory messages (type 'R') contain symbol information
        if message.type == b"R":
            symbol = message.stock.decode().strip()
            symbols.add(symbol)

        # For ITCH 4.1, we can break early since stock directory messages
        # typically appear at the beginning of the file
        if message_count >= 50000:
            break

print(f"Found {len(symbols)} symbols after processing {message_count:,} messages")

symbols = sorted(symbols)

# Display first 20 symbols
print("\nFirst 20 symbols:")
for symbol in symbols[:20]:
    print(f"  {symbol}")

if len(symbols) > 20:
    print(f"  ... and {len(symbols) - 20} more")

# Save symbols to file
output_file = data_dir / "itch41_symbols.txt"
with open(output_file, "w") as f:
    for symbol in symbols:
        f.write(f"{symbol}\n")

print(f"\n✅ Symbols saved to: {output_file}")
