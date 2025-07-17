import datetime
from pathlib import Path

from meatpy.event_handlers.lob_recorder import LOBRecorder
from meatpy.itch50 import ITCH50MarketProcessor, ITCH50MessageReader
from meatpy.writers.parquet_writer import ParquetWriter

# Define paths and parameters
data_dir = Path("data")

file_path = data_dir / "S081321-v50-AAPL-SPY.itch50.gz"
outfile_path = data_dir / "spy_lob.parquet"
book_date = datetime.datetime(2021, 8, 13)

with ITCH50MessageReader(file_path) as reader, ParquetWriter(outfile_path) as writer:
    processor = ITCH50MarketProcessor("SPY", book_date)

    # We only care about the top of book
    lob_recorder = LOBRecorder(writer=writer, collapse_orders=False)
    # Generate a list of timedeltas from 9:30 to 16:00 (inclusive) in 30-minute increments
    market_open = book_date + datetime.timedelta(hours=9, minutes=30)
    market_close = book_date + datetime.timedelta(hours=16, minutes=0)
    record_timestamps = [
        market_open + datetime.timedelta(minutes=i)
        for i in range(
            int((market_close - market_open).total_seconds() // (30 * 60)) + 1
        )
    ]
    lob_recorder.record_timestamps = record_timestamps

    # Attach the recorders to the processor
    processor.handlers.append(lob_recorder)

    for message in reader:
        processor.process_message(message)
