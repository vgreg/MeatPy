from datetime import datetime
from pathlib import Path

from meatpy.itch50 import ITCH50MarketProcessor, ITCH50MessageReader

file_path = Path(
    "/Users/vincentgregoire/Documents/Data/itch/20190530.BX_ITCH_50_AAPL_SPY.itch50"
)

processor = ITCH50MarketProcessor(instrument="AAPL", book_date=datetime(2019, 5, 30))

with ITCH50MessageReader(file_path) as reader:
    for i, message in enumerate(reader):
        processor.process_message(message)

        if i % 1_000_000 == 0:
            if processor.current_lob is not None:
                print(processor.current_lob.print_out())

    if processor.current_lob is not None:
        print(processor.current_lob.print_out())
