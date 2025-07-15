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

    def __init__(self, writer, max_depth: Optional[int] = None):
        """Initialize the LOBRecorder.

        Args:
            writer: DataWriter instance for output
            max_depth: Maximum depth of the book to record (None for all)
        """
        self.max_depth: int | None = max_depth
        self.collapse_orders: bool = True
        self.show_age: bool = False
        LOBEventRecorder.__init__(self, writer=writer)

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

    def get_schema(self):
        """Get schema definition for the data writer."""
        if self.show_age:
            if self.collapse_orders:
                return {
                    "fields": {
                        "Timestamp": "string",
                        "Type": "string",
                        "Level": "int64",
                        "Price": "float64",
                        "Volume": "int64",
                        "N Orders": "int64",
                        "Volume-Weighted Average Age": "float64",
                        "Average Age": "float64",
                        "First Age": "float64",
                        "Last Age": "float64",
                    }
                }
            else:
                return {
                    "fields": {
                        "Timestamp": "string",
                        "Type": "string",
                        "Level": "int64",
                        "Price": "float64",
                        "Order ID": "int64",
                        "Volume": "int64",
                        "Order Timestamp": "string",
                        "Age": "float64",
                    }
                }
        else:
            if self.collapse_orders:
                return {
                    "fields": {
                        "Timestamp": "string",
                        "Type": "string",
                        "Level": "int64",
                        "Price": "float64",
                        "Volume": "int64",
                        "N Orders": "int64",
                    }
                }
            else:
                return {
                    "fields": {
                        "Timestamp": "string",
                        "Type": "string",
                        "Level": "int64",
                        "Price": "float64",
                        "Order ID": "int64",
                        "Volume": "int64",
                        "Order Timestamp": "string",
                    }
                }

    def format_records_for_writer(self, records):
        """Format LOB records for the data writer."""
        formatted_records = []
        for lob in records:
            lob_records = self._convert_lob_to_records(lob)
            formatted_records.extend(lob_records)
        return formatted_records

    def _convert_lob_to_records(self, lob):
        """Convert a single LOB snapshot to records."""
        import io

        if not hasattr(lob, "write_csv"):
            return []

        temp_output = io.BytesIO()
        lob.write_csv(temp_output, self.collapse_orders, self.show_age)
        temp_output.seek(0)

        csv_content = temp_output.read().decode("utf-8")
        lines = csv_content.strip().split("\n")

        records = []
        for line in lines:
            if line.strip():
                values = line.split(",")
                if self.show_age:
                    if self.collapse_orders:
                        records.append(
                            {
                                "Timestamp": values[0],
                                "Type": values[1],
                                "Level": int(values[2]) if values[2] else 0,
                                "Price": float(values[3]) if values[3] else 0.0,
                                "Volume": int(values[4]) if values[4] else 0,
                                "N Orders": int(values[5]) if values[5] else 0,
                                "Volume-Weighted Average Age": float(values[6])
                                if values[6]
                                else 0.0,
                                "Average Age": float(values[7]) if values[7] else 0.0,
                                "First Age": float(values[8]) if values[8] else 0.0,
                                "Last Age": float(values[9]) if values[9] else 0.0,
                            }
                        )
                    else:
                        records.append(
                            {
                                "Timestamp": values[0],
                                "Type": values[1],
                                "Level": int(values[2]) if values[2] else 0,
                                "Price": float(values[3]) if values[3] else 0.0,
                                "Order ID": int(values[4]) if values[4] else 0,
                                "Volume": int(values[5]) if values[5] else 0,
                                "Order Timestamp": values[6],
                                "Age": float(values[7]) if values[7] else 0.0,
                            }
                        )
                else:
                    if self.collapse_orders:
                        records.append(
                            {
                                "Timestamp": values[0],
                                "Type": values[1],
                                "Level": int(values[2]) if values[2] else 0,
                                "Price": float(values[3]) if values[3] else 0.0,
                                "Volume": int(values[4]) if values[4] else 0,
                                "N Orders": int(values[5]) if values[5] else 0,
                            }
                        )
                    else:
                        records.append(
                            {
                                "Timestamp": values[0],
                                "Type": values[1],
                                "Level": int(values[2]) if values[2] else 0,
                                "Price": float(values[3]) if values[3] else 0.0,
                                "Order ID": int(values[4]) if values[4] else 0,
                                "Volume": int(values[5]) if values[5] else 0,
                                "Order Timestamp": values[6],
                            }
                        )

        return records
