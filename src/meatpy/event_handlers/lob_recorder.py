"""Recorder for limit order book (LOB) snapshots and CSV export.

This module provides the LOBRecorder class, which records LOB snapshots and
exports them to CSV files, supporting both aggregate and detailed order data.
"""

from io import TextIOWrapper
from pathlib import Path
from typing import Optional

from ..lob import LimitOrderBook
from .lob_event_recorder import LOBEventRecorder


class LOBRecorder(LOBEventRecorder):
    """Records limit order book snapshots and exports to CSV.

    Attributes:
        max_depth: Maximum depth of the book to record
        collapse_orders: Whether to aggregate orders by level
        show_age: Whether to include order age in output
    """

    def __init__(self, max_depth: Optional[int] = None):
        """Initialize the LOBRecorder.

        Args:
            max_depth: Maximum depth of the book to record (None for all)
        """
        self.max_depth: int | None = max_depth
        self.collapse_orders: bool = True
        self.show_age: bool = False
        LOBEventRecorder.__init__(self)

    def record(self, lob: LimitOrderBook, record_timestamp=None):
        """Record a snapshot of the limit order book.

        Args:
            lob: The current limit order book
            record_timestamp: Optional timestamp to override
        """
        new_record = lob.copy(max_level=self.max_depth)
        if record_timestamp is not None:
            new_record.timestamp = record_timestamp
        self.records.append(new_record)

    def write_csv(self, outfile: TextIOWrapper, collapse_orders=False, show_age=False):
        """Write recorded LOB snapshots to a CSV file.

        Args:
            outfile: File object to write to
            collapse_orders: Whether to aggregate orders by level
            show_age: Whether to include order age in output
        """
        outfile.write(self.get_csv_header(collapse_orders, show_age).encode())
        for x in self.records:
            x.write_csv(outfile, collapse_orders, show_age)

    def write_csv_header(self, outfile: TextIOWrapper):
        """Write the CSV header row to the file.

        Args:
            outfile: File object to write the header to
        """
        outfile.write(self.get_csv_header(self.collapse_orders, self.show_age).encode())

    def append_csv(self, outfile: str | Path):
        """Append recorded LOB snapshots to a CSV file.

        Args:
            outfile: File path or object to append to
        """
        for x in self.records:
            x.write_csv(outfile, self.collapse_orders, self.show_age)
        self.records = []

    def get_csv_header(self, collapse_orders: bool = False, show_age: bool = False):
        """Get the CSV header string for the output file.

        Args:
            collapse_orders: Whether to aggregate orders by level
            show_age: Whether to include order age in output

        Returns:
            str: The CSV header row
        """
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
