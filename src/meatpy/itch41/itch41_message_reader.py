"""ITCH 4.1 file reader with generator interface.

This module provides the ITCH41MessageReader class, which reads ITCH 4.1 market data files
and yields structured message objects one at a time using a generator interface.
"""

from __future__ import annotations

from pathlib import Path
from typing import Generator, Optional

from ..message_reader import MessageReader
from .itch41_market_message import (
    ITCH41MarketMessage,
)


class ITCH41MessageReader(MessageReader):
    """A market message reader for ITCH 4.1 data with generator interface.

    This reader reads ITCH 4.1 files and yields message objects one at a time,
    supporting automatic detection of compressed files (gzip, bzip2, xz, zip).

    Attributes:
        file_path: Path to the ITCH file to read
        _file_handle: Internal file handle when used as context manager
    """

    def __init__(
        self,
        file_path: Optional[Path | str] = None,
    ) -> None:
        """Initialize the ITCH41MessageReader.

        Args:
            file_path: Path to the ITCH file to read (optional if using read_file method)
        """
        super().__init__(file_path)

    def __iter__(self) -> Generator[ITCH41MarketMessage, None, None]:
        """Make the reader iterable when used as a context manager."""
        if self._file_handle is None:
            raise RuntimeError(
                "Reader must be used as a context manager to be iterable"
            )
        yield from self._read_messages(self._file_handle)

    def read_file(
        self, file_path: Path | str
    ) -> Generator[ITCH41MarketMessage, None, None]:
        """Parse an ITCH 4.1 file and yield messages one at a time.

        Args:
            file_path: Path to the ITCH file to read

        Yields:
            ITCH41MarketMessage objects
        """
        file_path = Path(file_path)
        with self._open_file(file_path) as file:
            yield from self._read_messages(file)

    def _read_messages(self, file) -> Generator[ITCH41MarketMessage, None, None]:
        """Internal method to read messages from an open file handle.

        Args:
            file: Open file handle to read from

        Yields:
            ITCH41MarketMessage objects
        """
        from ..message_reader import InvalidMessageFormatError

        cachesize = 1024 * 4

        data_buffer = file.read(cachesize)
        data_view = memoryview(data_buffer)
        offset = 0
        buflen = len(data_view)
        eof_reached = False

        while True:
            # Check if we need more data
            if offset + 2 > buflen:
                if eof_reached:
                    break
                new_data = file.read(cachesize)
                if not new_data:
                    eof_reached = True
                    break
                data_buffer = data_view[offset:].tobytes() + new_data
                data_view = memoryview(data_buffer)
                buflen = len(data_view)
                offset = 0
                continue

            if data_view[offset] != 0:
                raise InvalidMessageFormatError(f"Unexpected byte: {data_view[offset]}")

            message_len = data_view[offset + 1]
            message_end = offset + 2 + message_len

            # Check if we have enough data for the complete message
            if message_end > buflen:
                if eof_reached:
                    break
                new_data = file.read(cachesize)
                if not new_data:
                    eof_reached = True
                    break
                data_buffer = data_view[offset:].tobytes() + new_data
                data_view = memoryview(data_buffer)
                buflen = len(data_view)
                offset = 0
                continue

            message = ITCH41MarketMessage.from_bytes(
                data_view[offset + 2 : message_end].tobytes()
            )

            yield message
            offset = message_end

            # Check if we've reached the end of the buffer and EOF
            if offset >= buflen and eof_reached:
                break
