from pathlib import Path

from meatpy.itch50 import ITCH50MessageReader

file_path = Path("/Users/vincentgregoire/Documents/Data/itch/20190530.BX_ITCH_50.gz")
# file_path = Path("/Users/vincentgregoire/Documents/Data/itch/S081321-v50.txt.gz")

with ITCH50MessageReader(file_path) as parser:
    for i, message in enumerate(parser):
        # if i > 1000:
        #     break
        # print(message.to_json())
        x = message.to_json()
        if i % 1_000_000 == 0:
            print(f"Processed {i:,d} messages")
