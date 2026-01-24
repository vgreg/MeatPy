"""ITCH 2.0 file reader with generator interface.

This module provides the ITCH2MessageReader class, which reads ITCH 2.0 market data files
and yields structured message objects one at a time using a generator interface.

ITCH 2.0 uses ASCII format with newline-delimited messages.
"""

from __future__ import annotations

from pathlib import Path
from typing import Generator, Optional

from ..message_reader import MessageReader
from .itch2_market_message import ITCH2MarketMessage


class ITCH2MessageReader(MessageReader):
    """A market message reader for ITCH 2.0 data with generator interface.

    This reader reads ITCH 2.0 ASCII files and yields message objects one at a time,
    supporting automatic detection of compressed files (gzip, bzip2, xz, zip).

    Attributes:
        file_path: Path to the ITCH file to read
        _file_handle: Internal file handle when used as context manager
    """

    def __init__(
        self,
        file_path: Optional[Path | str] = None,
    ) -> None:
        """Initialize the ITCH2MessageReader.

        Args:
            file_path: Path to the ITCH file to read (optional if using read_file method)
        """
        super().__init__(file_path)

    def __iter__(self) -> Generator[ITCH2MarketMessage, None, None]:
        """Make the reader iterable when used as a context manager."""
        if self._file_handle is None:
            raise RuntimeError(
                "Reader must be used as a context manager to be iterable"
            )
        yield from self._read_messages(self._file_handle)

    def read_file(
        self, file_path: Path | str
    ) -> Generator[ITCH2MarketMessage, None, None]:
        """Parse an ITCH 2.0 file and yield messages one at a time.

        Args:
            file_path: Path to the ITCH file to read

        Yields:
            ITCH2MarketMessage objects
        """
        file_path = Path(file_path)
        with self._open_file(file_path) as file:
            yield from self._read_messages(file)

    def _read_messages(self, file) -> Generator[ITCH2MarketMessage, None, None]:
        """Internal method to read messages from an open file handle.

        ITCH 2.0 format is ASCII with newline-delimited messages.

        Args:
            file: Open file handle to read from

        Yields:
            ITCH2MarketMessage objects
        """
        for line in file:
            # Handle both bytes and str (depending on file type)
            if isinstance(line, str):
                line = line.encode("latin-1")

            # Strip trailing newline/carriage return
            line = line.rstrip(b"\r\n")

            # Skip empty lines
            if not line:
                continue

            message = ITCH2MarketMessage.from_bytes(line)
            yield message
