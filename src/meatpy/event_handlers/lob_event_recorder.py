"""Event recorder for limit order book (LOB) events.

This module provides the LOBEventRecorder class, which records LOB events and
writes them to CSV files, with support for filtering by trading status and
timestamp.
"""

from io import TextIOWrapper
from pathlib import Path
from typing import Any

from ..lob import LimitOrderBook
from ..market_event_handler import MarketEventHandler
from ..market_processor import MarketProcessor
from ..timestamp import Timestamp
from ..trading_status import (
    HaltedTradingStatus,
    PostTradeTradingStatus,
    PreTradeTradingStatus,
    QuoteOnlyTradingStatus,
    TradeTradingStatus,
)

try:
    from ..writers import DataWriter

    HAS_WRITERS = True
except ImportError:
    HAS_WRITERS = False
    DataWriter = None


class LOBEventRecorder(MarketEventHandler):
    """Records limit order book events and manages data output.

    Attributes:
        records: List of recorded measures
        record_timestamps: Optional list of timestamps to record
        record_start: Optional start timestamp for recording
        record_end: Optional end timestamp for recording
        write_csv_during_recording: Whether to write CSV during recording
        output_file_name: Output file name for concurrent writing
        buffer_size: Size of the buffer for records
        first_write_done: Whether the first write has been completed
        record_always: Whether to record regardless of trading status
        record_pretrade: Whether to record during pre-trade status
        record_trading: Whether to record during trading status
        record_posttrade: Whether to record during post-trade status
        record_halted: Whether to record during halted status
        record_quoteonly: Whether to record during quote-only status
        writer: Optional data writer for pluggable output formats
    """

    def __init__(self, writer: "DataWriter"):
        """Initialize the LOBEventRecorder with default settings.

        Args:
            writer: DataWriter instance for output
        """
        self.records: list[
            list[Any]
        ] = []  # List of records, each record is a list of measures
        self.record_timestamps: list[Timestamp] | None = None
        # A stack of timestamps to record, earliest at the end or None for all
        # events
        self.record_start: Timestamp | None = None
        self.record_end: Timestamp | None = None
        # Optional timestamps indicating beginning and end of recording. These
        # are only considered if self.record_timestamps is None.
        self.write_csv_during_recording: bool = False
        # Indicates if the records need to be written while the recording is
        # being done.
        self.output_file_name: str | Path = ""
        # The file to write to if there is concurrent writing
        self.buffer_size: int = 1000
        # The size of the buffer to keep
        self.first_write_done: bool = False
        # Indicates if the first write has been done. The first write
        # overwrite existing files and adds the header
        self.record_always: bool = True
        # Indicates if the trading status should be disregarded
        self.record_pretrade: bool = False
        self.record_trading: bool = True
        self.record_posttrade: bool = False
        self.record_halted: bool = False
        self.record_quoteonly: bool = False
        # Indicates which trading status should be recorded, only matters
        # when record_always is False
        self.writer: "DataWriter" = writer
        # DataWriter instance for pluggable output formats

    def record(self, lob: LimitOrderBook, record_timestamp: bool = None):
        """Record the current state of the limit order book.

        Args:
            lob: The current limit order book
            record_timestamp: Optional timestamp to record
        """
        pass

    def skip_record(self, lob: LimitOrderBook):
        """Handle logic when skipping a record due to trading status.

        Args:
            lob: The current limit order book
        """
        """Handles what needs to be done at every lob update when not
        recording because of trade status."""
        pass

    def before_lob_update(
        self, market_processor: MarketProcessor, new_timestamp: Timestamp
    ):
        """Trigger before a book update (next event timestamp passed).

        Args:
            market_processor: The market processor instance
            new_timestamp: The new timestamp for the update
        """
        lob = market_processor.current_lob
        """Trigger before a book update (next event timestamp passed)"""

        skip = False

        if self.record_always is False:
            if market_processor.trading_status is None:
                skip = True
            elif not self.record_pretrade and isinstance(
                market_processor.trading_status, PreTradeTradingStatus
            ):
                skip = True
            elif not self.record_trading and isinstance(
                market_processor.trading_status, TradeTradingStatus
            ):
                skip = True
            elif not self.record_posttrade and isinstance(
                market_processor.trading_status, PostTradeTradingStatus
            ):
                skip = True
            elif not self.record_halted and isinstance(
                market_processor.trading_status, HaltedTradingStatus
            ):
                skip = True
            elif not self.record_quoteonly and isinstance(
                market_processor.trading_status, QuoteOnlyTradingStatus
            ):
                skip = True

        if skip:
            self.skip_record(lob)
            return

        if self.record_timestamps is None:
            if self.record_start is None or self.record_start <= new_timestamp:
                if self.record_end is None or self.record_end >= new_timestamp:
                    self.record(lob)
        else:
            while (
                len(self.record_timestamps) > 0
                and new_timestamp > self.record_timestamps[-1]
            ):
                record_timestamp = self.record_timestamps.pop()
                self.record(lob, record_timestamp)

        if self.write_csv_during_recording is True and self.buffer_size < len(
            self.records
        ):
            self.write_buffer()

        # If using a data writer, buffer records for writing
        if len(self.records) >= self.buffer_size:
            self.flush_to_writer()

    def write_buffer(self):
        """Write the buffer of records to the output file."""
        if not self.first_write_done:
            with open(self.output_file_name, "w") as file:
                self.write_csv_header(file)
            self.first_write_done = True

        with open(self.output_file_name, "a+b") as file:
            self.append_csv(file)

    def write_csv_header(self, file: TextIOWrapper):
        """Write the CSV header row to the file.

        Args:
            file: The file object to write the header to
        """
        pass

    def append_csv(self, file: TextIOWrapper):
        """Append records to the CSV file.

        Args:
            file: The file object to append records to
        """
        pass

    def flush_to_writer(self):
        """Flush records to the configured data writer."""
        if not self.first_write_done and hasattr(self, "get_schema"):
            schema = self.get_schema()
            self.writer.write_header(schema)
            self.first_write_done = True

        formatted_records = self.format_records_for_writer(self.records)
        if formatted_records:
            self.writer.append_records(formatted_records)

        self.records = []

    def get_schema(self):
        """Get schema definition for the data writer.

        Subclasses should override this method to provide format-specific schema.

        Returns:
            Schema dictionary for the writer
        """
        return {"fields": {}}

    def format_records_for_writer(self, records):
        """Format records for the data writer.

        Subclasses should override this method to format records appropriately.

        Args:
            records: List of records to format

        Returns:
            Formatted records suitable for the writer
        """
        return records

    def close_writer(self):
        """Close the data writer and flush any remaining records."""
        self.flush_to_writer()
        self.writer.close()
