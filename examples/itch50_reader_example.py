from pathlib import Path

from meatpy.itch50 import ITCH50Parser

file_path = Path("/Users/vincentgregoire/Documents/Data/itch/20190530.BX_ITCH_50.gz")
file_path = Path("/Users/vincentgregoire/Documents/Data/itch/S081321-v50.txt.gz")

with ITCH50Parser(file_path) as parser:
    for i, message in enumerate(parser):
        if i > 1000:
            break
        print(message)
