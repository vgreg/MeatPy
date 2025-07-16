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

    def __init__(
        self,
        writer,
        max_depth: Optional[int] = None,
        collapse_orders: bool = True,
        show_age: bool = False,
    ):
        """Initialize the LOBRecorder.

        Args:
            writer: DataWriter instance for output
            max_depth: Maximum depth of the book to record (None for all)
            collapse_orders: Whether to aggregate orders by level
            show_age: Whether to include order age in output
        """
        self.max_depth: int | None = max_depth
        self.collapse_orders: bool = collapse_orders
        self.show_age: bool = show_age
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

        This method now uses the new direct data access approach for better performance.

        Args:
            outfile: File object to write to
            collapse_orders: Whether to aggregate orders by level
            show_age: Whether to include order age in output
        """
        outfile.write(self.get_csv_header(collapse_orders, show_age).encode())
        for lob in self.records:
            # Use the new direct data access method
            records = lob.to_records(
                collapse_orders=collapse_orders,
                show_age=show_age,
                max_depth=self.max_depth,
            )
            for record in records:
                # Convert record back to CSV format
                if show_age:
                    if collapse_orders:
                        line = f"{record['Timestamp']},{record['Type']},{record['Level']},{record['Price']},{record['Volume']},{record['N Orders']},{record['Volume-Weighted Average Age']},{record['Average Age']},{record['First Age']},{record['Last Age']}\n"
                    else:
                        line = f"{record['Timestamp']},{record['Type']},{record['Level']},{record['Price']},{record['Order ID']},{record['Volume']},{record['Order Timestamp']},{record['Age']}\n"
                else:
                    if collapse_orders:
                        line = f"{record['Timestamp']},{record['Type']},{record['Level']},{record['Price']},{record['Volume']},{record['N Orders']}\n"
                    else:
                        line = f"{record['Timestamp']},{record['Type']},{record['Level']},{record['Price']},{record['Order ID']},{record['Volume']},{record['Order Timestamp']}\n"
                outfile.write(line.encode())

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
        with open(outfile, "ab") as file:
            for lob in self.records:
                # Use the new direct data access method
                records = lob.to_records(
                    collapse_orders=self.collapse_orders,
                    show_age=self.show_age,
                    max_depth=self.max_depth,
                )
                for record in records:
                    # Convert record back to CSV format
                    if self.show_age:
                        if self.collapse_orders:
                            line = f"{record['Timestamp']},{record['Type']},{record['Level']},{record['Price']},{record['Volume']},{record['N Orders']},{record['Volume-Weighted Average Age']},{record['Average Age']},{record['First Age']},{record['Last Age']}\n"
                        else:
                            line = f"{record['Timestamp']},{record['Type']},{record['Level']},{record['Price']},{record['Order ID']},{record['Volume']},{record['Order Timestamp']},{record['Age']}\n"
                    else:
                        if self.collapse_orders:
                            line = f"{record['Timestamp']},{record['Type']},{record['Level']},{record['Price']},{record['Volume']},{record['N Orders']}\n"
                        else:
                            line = f"{record['Timestamp']},{record['Type']},{record['Level']},{record['Price']},{record['Order ID']},{record['Volume']},{record['Order Timestamp']}\n"
                    file.write(line.encode())
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
        """Convert a single LOB snapshot to records using direct data access."""
        if not hasattr(lob, "to_records"):
            return []

        # Use the new direct data access method instead of CSV round-trip
        return lob.to_records(
            collapse_orders=self.collapse_orders,
            show_age=self.show_age,
            max_depth=self.max_depth,
        )
