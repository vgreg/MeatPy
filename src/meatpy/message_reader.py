"""Abstract base class for market message readers.

This module provides the MessageReader abstract base class, which defines
the interface and common functionality for reading market data files
and yielding structured message objects.
"""

from __future__ import annotations

import abc
import bz2
import gzip
import lzma
import zipfile
from pathlib import Path
from typing import Generator, Optional

from .message_parser import MarketMessage


class InvalidMessageFormatError(Exception):
    """Exception raised when a message has an invalid format.

    This exception is raised when the message format does not match
    the expected message structure.
    """

    pass


class UnknownMessageTypeError(Exception):
    """Exception raised when an unknown message type is encountered.

    This exception is raised when the message type is not recognized
    by the message reader.
    """

    pass


class MessageReader(abc.ABC):
    """Abstract base class for market message readers with generator interface.

    This abstract class provides the foundation for reading market data files
    and yielding message objects one at a time, supporting automatic detection
    of compressed files (gzip, bzip2, xz, zip).

    Attributes:
        file_path: Path to the market data file to read
        _file_handle: Internal file handle when used as context manager
    """

    def __init__(
        self,
        file_path: Optional[Path | str] = None,
    ) -> None:
        """Initialize the MessageReader.

        Args:
            file_path: Path to the market data file to read (optional if using read_file method)
        """
        self.file_path = Path(file_path) if file_path else None
        self._file_handle = None

    def __enter__(self):
        """Context manager entry. Opens the file if file_path was provided."""
        if self.file_path is None:
            raise ValueError("No file_path provided. Use read_file() method instead.")
        self._file_handle = self._open_file(self.file_path)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit. Closes the file handle."""
        if self._file_handle is not None:
            self._file_handle.close()
            self._file_handle = None

    def __iter__(self) -> Generator[MarketMessage, None, None]:
        """Make the reader iterable when used as a context manager."""
        if self._file_handle is None:
            raise RuntimeError(
                "Reader must be used as a context manager to be iterable"
            )
        yield from self._read_messages(self._file_handle)

    def read_file(self, file_path: Path | str) -> Generator[MarketMessage, None, None]:
        """Parse a market data file and yield messages one at a time.

        Args:
            file_path: Path to the market data file to read

        Yields:
            MarketMessage objects
        """
        file_path = Path(file_path)
        with self._open_file(file_path) as file:
            yield from self._read_messages(file)

    @abc.abstractmethod
    def _read_messages(self, file) -> Generator[MarketMessage, None, None]:
        """Internal method to read messages from an open file handle.

        This is an abstract method that must be implemented by subclasses
        to handle their specific message format and parsing logic.

        Args:
            file: Open file handle to read from

        Yields:
            MarketMessage objects
        """
        pass

    @abc.abstractmethod
    def _create_message(self, message_data: bytes) -> MarketMessage:
        """Create a MarketMessage from raw message data.

        This is an abstract method that must be implemented by subclasses
        to handle their specific message format and create appropriate
        MarketMessage instances.

        Args:
            message_data: Raw message bytes

        Returns:
            Appropriate MarketMessage subclass instance

        Raises:
            UnknownMessageTypeError: If message type is not recognized
        """
        pass

    def _detect_compression(self, file_path: Path) -> tuple[bool, str]:
        """Detect if a file is compressed and determine the compression type.

        Args:
            file_path: Path to the file to check

        Returns:
            Tuple of (is_compressed, compression_type)
        """
        with open(file_path, "rb") as f:
            magic_bytes = f.read(4)

        if magic_bytes.startswith(b"\x1f\x8b"):
            return True, "gzip"
        elif magic_bytes.startswith(b"BZ"):
            return True, "bzip2"
        elif magic_bytes.startswith(b"\xfd7zXZ"):
            return True, "xz"
        elif magic_bytes.startswith(b"PK"):
            return True, "zip"
        else:
            return False, "none"

    def _open_file(self, file_path: Path):
        """Open a file with appropriate decompression if needed.

        Args:
            file_path: Path to the file to open

        Returns:
            File-like object for reading
        """
        is_compressed, compression_type = self._detect_compression(file_path)

        if not is_compressed:
            return open(file_path, "rb")
        elif compression_type == "gzip":
            return gzip.open(file_path, "rb")
        elif compression_type == "bzip2":
            return bz2.open(file_path, "rb")
        elif compression_type == "xz":
            return lzma.open(file_path, "rb")
        elif compression_type == "zip":
            # For zip files, we need to handle them differently
            # Assume single file in zip or use the first file
            with zipfile.ZipFile(file_path, "r") as zip_file:
                if len(zip_file.namelist()) == 0:
                    raise ValueError("Zip file is empty")
                # Return a file-like object for the first file in the zip
                return zip_file.open(zip_file.namelist()[0], "r")
        else:
            raise ValueError(f"Unsupported compression type: {compression_type}")
