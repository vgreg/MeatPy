"""lob_recorder.py: A recorder for limit order book snapshots."""

from io import TextIOWrapper
from pathlib import Path
from typing import Optional

from ..lob import LimitOrderBook
from .lob_event_recorder import LOBEventRecorder


class LOBRecorder(LOBEventRecorder):
    def __init__(self, max_depth: Optional[int] = None):
        self.max_depth: int | None = max_depth
        self.collapse_orders: bool = True
        self.show_age: bool = False
        # Indicates if we should collapse the orders by level, only applies
        # to CSV output written during recording
        LOBEventRecorder.__init__(self)

    def record(self, lob: LimitOrderBook, record_timestamp=None):
        new_record = lob.copy(max_level=self.max_depth)
        if record_timestamp is not None:
            new_record.timestamp = record_timestamp
        self.records.append(new_record)

    def write_csv(self, outfile: TextIOWrapper, collapse_orders=False, show_age=False):
        """Write to a file in CSV format

        Collapse order means exporting aggregate level data rather than
        individual orders."""
        # Write header row
        outfile.write(self.get_csv_header(collapse_orders, show_age).encode())

        # Write content
        for x in self.records:
            x.write_csv(outfile, collapse_orders, show_age)

    def write_csv_header(self, outfile: TextIOWrapper):  # Write header row
        outfile.write(self.get_csv_header(self.collapse_orders, self.show_age).encode())

    def append_csv(self, outfile: str | Path):
        # Write content
        for x in self.records:
            x.write_csv(outfile, self.collapse_orders, self.show_age)
        self.records = []

    def get_csv_header(self, collapse_orders: bool = False, show_age: bool = False):
        if show_age:
            if collapse_orders:
                return "Timestamp,Type,Level,Price,Volume,N Orders,Volume-Weighted Average Age,Average Age,First Age,Last Age\n"
            else:
                return (
                    "Timestamp,Type,Level,Price,Order ID,Volume,Order Timestamp,Age\n"
                )
        else:
            if collapse_orders:
                return "Timestamp,Type,Level,Price,Volume,N Orders\n"
            else:
                return "Timestamp,Type,Level,Price,Order ID,Volume,Order Timestamp\n"
