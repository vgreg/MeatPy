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

    def _flush_buffer(self) -> None:
        """Flush the message buffer to file."""
        if not self._buffer:
            return

        with self._get_file_handle() as file_handle:
            for message in self._buffer:
                self._write_message(file_handle, message)

        self._buffer.clear()

    def _should_track_message(self, message: ITCH41MarketMessage) -> bool:
        """Determine if this message should be tracked based on symbols.

        Args:
            message: The message to check

        Returns:
            True if the message should be tracked
        """
        # Track all messages if no symbols specified
        if self._symbols is None:
            return True

        # Check if message has a stock field and if it matches our symbols
        if hasattr(message, "stock"):
            return message.stock in self._symbols

        # Track system messages and other global messages
        return message.type in [b"S"]

    def write_message(self, message: ITCH41MarketMessage) -> None:
        """Write a message to the output file (buffered).

        Args:
            message: The message to write
        """
        if not self._should_track_message(message):
            return

        self._buffer.append(message)
        self._message_count += 1

        # Flush buffer if it's full
        if len(self._buffer) >= self.message_buffer:
            self._flush_buffer()

    def finalize(self) -> None:
        """Finalize the writer by flushing any remaining buffered messages."""
        self._flush_buffer()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.finalize()
