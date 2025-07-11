from pathlib import Path

from meatpy.itch50 import ITCH50MessageReader, ITCH50Writer

file_path = Path("/Users/vincentgregoire/Documents/Data/itch/20190530.BX_ITCH_50.gz")
# file_path = Path("/Users/vincentgregoire/Documents/Data/itch/S081321-v50.txt.gz")
output_path = Path(
    "/Users/vincentgregoire/Documents/Data/itch/20190530.BX_ITCH_50_AAPL_SPY.itch50"
)

with ITCH50MessageReader(file_path) as reader:
    with ITCH50Writer(output_path, symbols=["AAPL", "SPY"]) as writer:
        for i, message in enumerate(reader):
            # if i > 1000:
            #     break
            # print(message.to_json())
            writer.process_message(message)
            if i % 1_000_000 == 0:
                print(f"Processed {i:,d} messages")

with ITCH50MessageReader(output_path) as reader:
    for i, message in enumerate(reader):
        if i > 100:
            break
        print(message.to_json())
