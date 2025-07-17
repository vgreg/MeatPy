from pathlib import Path

from meatpy.itch50 import ITCH50MessageReader

# Define the path to our sample data file
data_dir = Path("data")
file_path = data_dir / "S081321-v50.txt.gz"
print(f"✅ Found sample file: {file_path}")
print(f"File size: {file_path.stat().st_size / (1024**3):.2f} GB")

symbols = set()
message_count = 0

print("Reading ITCH file to extract symbols...")

with ITCH50MessageReader(file_path) as reader:
    for message in reader:
        message_count += 1

        # Stock Directory messages (type 'R') contain symbol information
        if message.type == b"R":
            symbol = message.stock.decode().strip()
            symbols.add(symbol)

        if message_count >= 100000:
            break

print(f"Found {len(symbols)} symbols after processing {message_count:,} messages")

symbols = sorted(symbols)

print("First 20 symbols:")
for symbol in symbols[:20]:
    print(symbol)
