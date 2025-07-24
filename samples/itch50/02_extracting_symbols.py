from pathlib import Path

from meatpy.itch50 import ITCH50MessageReader, ITCH50Writer

# Define paths
data_dir = Path("data")
input_file = data_dir / "S081321-v50.txt.gz"
output_file = data_dir / "S081321-v50-AAPL-SPY.itch50.gz"

# Symbols we want to extract
target_symbols = ["AAPL", "SPY"]

input_size_gb = input_file.stat().st_size / (1024**3)
print(f"Input file size: {input_size_gb:.2f} GB")

# This takes about 10 minutes on a MacBook Pro M3 Max
message_count = 0
with ITCH50MessageReader(input_file) as reader:
    with ITCH50Writer(output_file, symbols=target_symbols) as writer:
        for message in reader:
            message_count += 1
            writer.process_message(message)

print(f"Total messages processed: {message_count:,}")


new_message_count = 0
with ITCH50MessageReader(output_file) as reader:
    for message in reader:
        new_message_count += 1

print(f"Total messages in filtered file: {new_message_count:,}")
output_size_gb = output_file.stat().st_size / (1024**3)
print(f"Output file size: {output_size_gb:.2f} GB")
