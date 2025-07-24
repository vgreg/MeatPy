"""ITCH 4.1 file writer with buffering and compression support.

This module provides the ITCH41Writer class, which writes ITCH 4.1 market data
messages to files with support for buffering and compression.
"""

from __future__ import annotations

import bz2
import gzip
import lzma
from pathlib import Path
from typing import Optional

from .itch41_market_message import ITCH41MarketMessage


class ITCH41Writer:
    """A writer for ITCH 4.1 market data files.

    This writer keeps track of messages relevant to specified symbols and
    writes them to files in ITCH format with support for buffering and compression.

    Attributes:
        symbols: List of symbols to track (None for all)
        output_path: Path to the output file
        message_buffer: Number of messages to buffer before writing
        compress: Whether to compress the output file
        compression_type: Type of compression to use ('gzip', 'bzip2', 'xz')
    """

    def __init__(
        self,
        output_path: Optional[Path | str] = None,
        symbols: Optional[list[bytes | str]] = None,
        message_buffer: int = 2000,
        compress: bool = False,
        compression_type: str = "gzip",
    ) -> None:
        """Initialize the ITCH41Writer.

        Args:
            symbols: List of symbols to track (None for all)
            output_path: Path to the output file
            message_buffer: Number of messages to buffer before writing
            compress: Whether to compress the output file
            compression_type: Type of compression to use ('gzip', 'bzip2', 'xz')
        """
        self._symbols = (
            [
                f"{symbol:<8}".encode("ascii") if isinstance(symbol, str) else symbol
                for symbol in symbols
            ]
            if symbols
            else None
        )
        self.output_path = Path(output_path) if output_path else None
        self.message_buffer = message_buffer
        self.compress = compress
        self.compression_type = compression_type

        # Internal state
        self._order_refs: set[int] = set()
        self._matches: set[int] = set()
        self._buffer: list[ITCH41MarketMessage] = []
        self._message_count = 0

    def _get_file_handle(self, mode: str = "ab"):
        """Get a file handle with appropriate compression if needed.

        Args:
            mode: File open mode

        Returns:
            File-like object for writing
        """
        if not self.output_path:
            raise ValueError("No output path specified")

        if not self.compress:
            return open(self.output_path, mode)
        elif self.compression_type == "gzip":
            return gzip.open(self.output_path, mode)
        elif self.compression_type == "bzip2":
            return bz2.open(self.output_path, mode)
        elif self.compression_type == "xz":
            return lzma.open(self.output_path, mode)
        else:
            raise ValueError(f"Unsupported compression type: {self.compression_type}")

    def _write_message(self, file_handle, message: ITCH41MarketMessage) -> None:
        """Write a single message to the file in ITCH format.

        Args:
            file_handle: File handle to write to
            message: Message to write
        """
        file_handle.write(b"\x00")
        file_handle.write(bytes([message.message_size]))
        file_handle.write(message.to_bytes())

    def _write_messages(self, force: bool = False) -> None:
        """Write buffered messages to the file.

        Args:
            force: Whether to write regardless of buffer size
        """
        if len(self._buffer) > self.message_buffer or force:
            with self._get_file_handle() as file_handle:
                for message in self._buffer:
                    self._write_message(file_handle, message)
            self._buffer = []

    def _append_message(self, message: ITCH41MarketMessage) -> None:
        """Append a message to the stock message buffer.

        Args:
            message: Message to append
        """
        self._buffer.append(message)
        self._write_messages()

    def _validate_symbol(self, symbol: bytes) -> bool:
        """Validate a symbol.

        Args:
            symbol: Symbol to validate

        Returns:
            True if the symbol is valid, False otherwise
        """
        if self._symbols is None:
            return True
        return symbol in self._symbols

    def process_message(self, message: ITCH41MarketMessage) -> None:
        """Process a message and add it to the appropriate buffers.

        Args:
            message: Message to process
        """
        self._message_count += 1

        # Get message type
        message_type = getattr(message.__class__, "type", None)
        if message_type is None:
            return

        # Handle different message types
        if message_type == b"R":  # Stock Directory
            if hasattr(message, "stock") and self._validate_symbol(message.stock):
                self._append_message(message)

        elif message_type in b"ST":  # System messages (Seconds, System Event)
            # Add to all stock message buffers
            self._append_message(message)

        elif (
            message_type in b"HYL"
        ):  # Stock-specific messages (Trading Action, RegSHO, Market Participant Position)
            if hasattr(message, "stock") and self._validate_symbol(message.stock):
                self._append_message(message)

        elif message_type in b"AF":  # Add order messages
            if (
                hasattr(message, "stock")
                and hasattr(message, "order_ref")
                and self._validate_symbol(message.stock)
            ):
                self._order_refs.add(message.order_ref)
                self._append_message(message)

        elif message_type in b"ECXD":  # Order execution/cancel/delete
            if hasattr(message, "order_ref") and message.order_ref in self._order_refs:
                self._append_message(message)
                if message_type == b"D":  # Order delete
                    self._order_refs.remove(message.order_ref)
                elif message_type in b"EC":  # Order executed
                    if hasattr(message, "match"):
                        self._matches.add(message.match)

        elif message_type == b"U":  # Order replace
            if (
                hasattr(message, "original_ref")
                and message.original_ref in self._order_refs
            ):
                self._append_message(message)
                self._order_refs.remove(message.original_ref)
                if hasattr(message, "new_ref"):
                    self._order_refs.add(message.new_ref)

        elif message_type == b"B":  # Broken trade
            if hasattr(message, "match") and message.match in self._matches:
                self._append_message(message)

        elif message_type in b"PQ":  # Trade messages (Trade, Cross Trade)
            if hasattr(message, "stock") and self._validate_symbol(message.stock):
                self._append_message(message)
                if hasattr(message, "match"):
                    self._matches.add(message.match)

        elif message_type in b"IN":  # NOII and RPII messages
            if hasattr(message, "stock") and self._validate_symbol(message.stock):
                self._append_message(message)

    def flush(self) -> None:
        """Flush all buffered messages to the file."""
        self._write_messages(force=True)

    def close(self) -> None:
        """Close the writer and flush any remaining messages."""
        self.flush()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
