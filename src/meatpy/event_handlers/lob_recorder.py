"""Recorder for limit order book (LOB) snapshots and CSV export.

This module provides the LOBRecorder class, which records LOB snapshots and
exports them to CSV files, supporting both aggregate and detailed order data.
"""

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
        self._max_depth: int | None = max_depth
        self._collapse_orders: bool = collapse_orders
        self._show_age: bool = show_age

        LOBEventRecorder.__init__(self, writer=writer)

        # Set the schema based on current parameters
        self._set_writer_schema()

    @property
    def max_depth(self) -> int | None:
        """Maximum depth of the book to record."""
        return self._max_depth

    @max_depth.setter
    def max_depth(self, value: int | None) -> None:
        """Set maximum depth of the book to record."""
        if self._max_depth != value:
            self._max_depth = value
            self._update_writer_schema()

    @property
    def collapse_orders(self) -> bool:
        """Whether to aggregate orders by level."""
        return self._collapse_orders

    @collapse_orders.setter
    def collapse_orders(self, value: bool) -> None:
        """Set whether to aggregate orders by level."""
        if self._collapse_orders != value:
            self._collapse_orders = value
            self._update_writer_schema()

    @property
    def show_age(self) -> bool:
        """Whether to include order age in output."""
        return self._show_age

    @show_age.setter
    def show_age(self, value: bool) -> None:
        """Set whether to include order age in output."""
        if self._show_age != value:
            self._show_age = value
            self._update_writer_schema()

    def _set_writer_schema(self) -> None:
        """Set the writer schema based on current recording parameters."""
        schema = self.get_schema()
        self.writer.set_schema(schema)

    def _update_writer_schema(self) -> None:
        """Update the writer schema if not locked, otherwise raise warning."""
        if not self.writer.is_schema_locked():
            self._set_writer_schema()
        else:
            import warnings

            warnings.warn(
                "Cannot update schema after writing has begun. "
                "Schema changes will take effect for new writers only.",
                UserWarning,
                stacklevel=3,
            )

    def record(self, lob: LimitOrderBook, record_timestamp=None):
        """Record a snapshot of the limit order book.

        Args:
            lob: The current limit order book
            record_timestamp: Optional timestamp to override
        """
        # Create a copy of the LOB for recording
        new_record = lob.copy(max_level=self.max_depth)
        if record_timestamp is not None:
            new_record.timestamp = record_timestamp

        # Convert to structured records and write directly to the writer
        records = new_record.to_records(
            collapse_orders=self.collapse_orders,
            show_age=self.show_age,
            max_depth=self.max_depth,
        )

        # Write each record to the writer
        for record in records:
            self.writer.buffer_record(record)

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
