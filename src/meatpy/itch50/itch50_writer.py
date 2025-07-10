"""ITCH 5.0 file writer with buffering and compression support.

This module provides the ITCH50Writer class, which writes ITCH 5.0 market data
messages to files with support for buffering and compression.
"""

from __future__ import annotations

import bz2
import gzip
import lzma
from pathlib import Path
from typing import Optional

from .itch50_market_message import ITCH50MarketMessage


class ITCH50Writer:
    """A writer for ITCH 5.0 market data files.

    This writer keeps track of messages relevant to specified symbols and
    writes them to files in ITCH format with support for buffering and compression.

    Attributes:
        symbols: List of symbols to track (None for all)
        output_path: Path to the output file
        message_buffer: Number of messages to buffer before writing
        compress: Whether to compress the output file
        compression_type: Type of compression to use ('gzip', 'bzip2', 'xz')
        order_refs: Mapping of order reference numbers to symbols
        matches: Mapping of match numbers to symbols
        system_messages: List of system messages that apply to all symbols
        stock_messages: Dictionary mapping symbols to message lists
        message_count: Total number of messages processed
    """

    def __init__(
        self,
        symbols: Optional[list[bytes]] = None,
        output_path: Optional[Path | str] = None,
        message_buffer: int = 2000,
        compress: bool = False,
        compression_type: str = "gzip",
    ) -> None:
        """Initialize the ITCH50Writer.

        Args:
            symbols: List of symbols to track (None for all)
            output_path: Path to the output file
            message_buffer: Number of messages to buffer before writing
            compress: Whether to compress the output file
            compression_type: Type of compression to use ('gzip', 'bzip2', 'xz')
        """
        self.symbols = symbols
        self.output_path = Path(output_path) if output_path else None
        self.message_buffer = message_buffer
        self.compress = compress
        self.compression_type = compression_type

        # Internal state
        self.order_refs: dict[int, bytes] = {}
        self.matches: dict[int, bytes] = {}
        self.system_messages: list[ITCH50MarketMessage] = []
        self.stock_messages: dict[bytes, list[ITCH50MarketMessage]] = {}
        self.message_count = 0

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

    def _write_message(self, file_handle, message: ITCH50MarketMessage) -> None:
        """Write a single message to the file in ITCH format.

        Args:
            file_handle: File handle to write to
            message: Message to write
        """
        file_handle.write(b"\x00")
        file_handle.write(bytes([message.message_size]))
        file_handle.write(message.pack())

    def _write_stock_messages(self, symbol: bytes, force: bool = False) -> None:
        """Write buffered messages for a symbol to the file.

        Args:
            symbol: Symbol to write messages for
            force: Whether to write regardless of buffer size
        """
        if symbol not in self.stock_messages:
            return

        messages = self.stock_messages[symbol]
        if len(messages) > self.message_buffer or force:
            with self._get_file_handle() as file_handle:
                for message in messages:
                    self._write_message(file_handle, message)
            self.stock_messages[symbol] = []

    def _append_stock_message(
        self, symbol: bytes, message: ITCH50MarketMessage
    ) -> None:
        """Append a message to the stock message buffer.

        Args:
            symbol: Symbol to append message to
            message: Message to append
        """
        if self.symbols is not None and symbol not in self.symbols:
            return

        if symbol not in self.stock_messages:
            # Initialize with system messages
            self.stock_messages[symbol] = list(self.system_messages)

        self.stock_messages[symbol].append(message)

    def process_message(self, message: ITCH50MarketMessage) -> None:
        """Process a message and add it to the appropriate buffers.

        Args:
            message: Message to process
        """
        self.message_count += 1

        # Get message type
        message_type = getattr(message.__class__, "type", None)
        if message_type is None:
            return

        # Handle different message types
        if message_type == b"R":  # Stock Directory
            if hasattr(message, "stock"):
                self._append_stock_message(message.stock, message)

        elif message_type in b"SVW":  # System messages
            # Add to all stock message buffers
            for symbol in self.stock_messages:
                self._append_stock_message(symbol, message)
            self.system_messages.append(message)

        elif message_type in b"HYQINKLJh":  # Stock-specific messages
            if hasattr(message, "stock"):
                self._append_stock_message(message.stock, message)

        elif message_type in b"AF":  # Add order messages
            if hasattr(message, "stock") and hasattr(message, "orderRefNum"):
                self.order_refs[message.orderRefNum] = message.stock
                self._append_stock_message(message.stock, message)

        elif message_type in b"ECXD":  # Order execution/cancel/delete
            if (
                hasattr(message, "orderRefNum")
                and message.orderRefNum in self.order_refs
            ):
                symbol = self.order_refs[message.orderRefNum]
                self._append_stock_message(symbol, message)
                if message_type == b"D":  # Order delete
                    del self.order_refs[message.orderRefNum]
                elif message_type in b"EC":  # Order executed
                    if hasattr(message, "match"):
                        self.matches[message.match] = symbol

        elif message_type == b"U":  # Order replace
            if (
                hasattr(message, "origOrderRefNum")
                and message.origOrderRefNum in self.order_refs
            ):
                symbol = self.order_refs[message.origOrderRefNum]
                self._append_stock_message(symbol, message)
                del self.order_refs[message.origOrderRefNum]
                if hasattr(message, "newOrderRefNum"):
                    self.order_refs[message.newOrderRefNum] = symbol

        elif message_type == b"B":  # Broken trade
            if hasattr(message, "match") and message.match in self.matches:
                symbol = self.matches[message.match]
                self._append_stock_message(symbol, message)

        elif message_type == b"P":  # Trade
            if hasattr(message, "stock"):
                self._append_stock_message(message.stock, message)
                if hasattr(message, "match"):
                    self.matches[message.match] = message.stock

    def flush(self) -> None:
        """Flush all buffered messages to the file."""
        for symbol in list(self.stock_messages.keys()):
            self._write_stock_messages(symbol, force=True)

    def close(self) -> None:
        """Close the writer and flush any remaining messages."""
        self.flush()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
