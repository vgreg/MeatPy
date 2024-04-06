"""lob_event_recorder.py: A generic lob event recorder"""

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


class LOBEventRecorder(MarketEventHandler):
    def __init__(self):
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

    def record(self, lob: LimitOrderBook, record_timestamp: bool = None):
        pass

    def skip_record(self, lob: LimitOrderBook):
        """Handles what needs to be done at every lob update when not
        recording because of trade status."""
        pass

    def before_lob_update(
        self, market_processor: MarketProcessor, new_timestamp: Timestamp
    ):
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

    def write_buffer(self):
        if not self.first_write_done:
            with open(self.output_file_name, "w") as file:
                self.write_csv_header(file)
            self.first_write_done = True

        with open(self.output_file_name, "a+b") as file:
            self.append_csv(file)

    def write_csv_header(self, file: TextIOWrapper):
        pass

    def append_csv(self, file: TextIOWrapper):
        pass
