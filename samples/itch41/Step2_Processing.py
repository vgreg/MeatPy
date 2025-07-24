import datetime
from pathlib import Path

from meatpy.event_handlers.lob_recorder import LOBRecorder
from meatpy.itch41 import ITCH41MarketProcessor, ITCH41MessageReader
from meatpy.lob import ExecutionPriorityExceptionList
from meatpy.writers.parquet_writer import ParquetWriter

# Define paths and parameters
data_dir = Path("data")

file_path = data_dir / "S083012-v41-AAPL-SPY.itch41.gz"
outfile_path = data_dir / "spy_tob.parquet"
book_date = datetime.datetime(2012, 8, 30)


with ITCH41MessageReader(file_path) as reader, ParquetWriter(outfile_path) as writer:
    processor = ITCH41MarketProcessor("SPY", book_date)

    # We only care about the top of book
    tob_recorder = LOBRecorder(writer=writer, max_depth=1)
    # Generate a list of timedeltas from 9:30 to 16:00 (inclusive) in 1-minute increments
    market_open = book_date + datetime.timedelta(hours=9, minutes=30)
    market_close = book_date + datetime.timedelta(hours=16, minutes=0)
    record_timestamps = [
        market_open + datetime.timedelta(minutes=i)
        for i in range(int((market_close - market_open).total_seconds() // 60) + 1)
    ]
    tob_recorder.record_timestamps = record_timestamps

    # Attach the recorders to the processor
    processor.handlers.append(tob_recorder)

    message_types = set()

    for i, message in enumerate(reader):
        # if i % 10_000 == 0:
        #     print(f"Processing message {i:,}...")
        if message.type != b"T":
            print(message)
        try:
            processor.process_message(message)
        except ExecutionPriorityExceptionList as e:
            print(f"Execution priority exception: {e}")
        message_types.add(message.type)

    print(f"Processed {i + 1:,} messages.")
    print(f"Message types: {message_types}")
