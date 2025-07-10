"""ITCH 5.0 file parser with generator interface.

This module provides the ITCH50Parser class, which parses ITCH 5.0 market data files
and yields structured message objects one at a time using a generator interface.
"""

from __future__ import annotations

import bz2
import gzip
import lzma
import zipfile
from pathlib import Path
from typing import Generator, Optional

from .itch50_market_message import (
    AddOrderMessage,
    AddOrderMPIDMessage,
    BrokenTradeMessage,
    CrossTradeMessage,
    DirectListingCapitalRaiseMessage,
    IPOQuotingPeriodUpdateMessage,
    ITCH50MarketMessage,
    LULDAuctionCollarMessage,
    MarketParticipantPositionMessage,
    MWCBBreachMessage,
    MWCBDeclineLevelMessage,
    NoiiMessage,
    OperationalHaltMessage,
    OrderCancelMessage,
    OrderDeleteMessage,
    OrderExecutedMessage,
    OrderExecutedPriceMessage,
    OrderReplaceMessage,
    RegSHOMessage,
    RpiiMessage,
    StockDirectoryMessage,
    StockTradingActionMessage,
    SystemEventMessage,
    TradeMessage,
)


class InvalidMessageFormatError(Exception):
    """Exception raised when a message has an invalid format.

    This exception is raised when the message format does not match
    the expected ITCH 5.0 message structure.
    """

    pass


class UnknownMessageTypeError(Exception):
    """Exception raised when an unknown message type is encountered.

    This exception is raised when the message type is not recognized
    by the ITCH 5.0 parser.
    """

    pass


class ITCH50Parser:
    """A market message parser for ITCH 5.0 data with generator interface.

    This parser reads ITCH 5.0 files and yields message objects one at a time,
    supporting automatic detection of compressed files (gzip, bzip2, xz, zip).

    Attributes:
        file_path: Path to the ITCH file to parse
        keep_message_types: Bytes of message types to keep (None for all)
        symbols: List of symbols to parse (None for all)
        _file_handle: Internal file handle when used as context manager
    """

    def __init__(
        self,
        file_path: Optional[Path | str] = None,
        keep_message_types: Optional[bytes] = None,
        symbols: Optional[list[bytes]] = None,
    ) -> None:
        """Initialize the ITCH50Parser.

        Args:
            file_path: Path to the ITCH file to parse (optional if using parse_file method)
            keep_message_types: Message types to keep (None for all)
            symbols: List of symbols to parse (None for all)
        """
        self.file_path = Path(file_path) if file_path else None
        self.keep_message_types = keep_message_types
        self.symbols = symbols
        self._file_handle = None

    def __enter__(self):
        """Context manager entry. Opens the file if file_path was provided."""
        if self.file_path is None:
            raise ValueError("No file_path provided. Use parse_file() method instead.")
        self._file_handle = self._open_file(self.file_path)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit. Closes the file handle."""
        if self._file_handle is not None:
            self._file_handle.close()
            self._file_handle = None

    def __iter__(self) -> Generator[ITCH50MarketMessage, None, None]:
        """Make the parser iterable when used as a context manager."""
        if self._file_handle is None:
            raise RuntimeError(
                "Parser must be used as a context manager to be iterable"
            )
        yield from self._parse_messages(self._file_handle)

    def parse_file(
        self, file_path: Path | str
    ) -> Generator[ITCH50MarketMessage, None, None]:
        """Parse an ITCH 5.0 file and yield messages one at a time.

        Args:
            file_path: Path to the ITCH file to parse

        Yields:
            ITCH50MarketMessage objects
        """
        file_path = Path(file_path)
        with self._open_file(file_path) as file:
            yield from self._parse_messages(file)

    def _parse_messages(self, file) -> Generator[ITCH50MarketMessage, None, None]:
        """Internal method to parse messages from an open file handle.

        Args:
            file: Open file handle to read from

        Yields:
            ITCH50MarketMessage objects
        """
        cachesize = 1024 * 4

        data_buffer = file.read(cachesize)
        data_view = memoryview(data_buffer)
        offset = 0
        buflen = len(data_view)
        have_data = True
        eof_reached = False

        while have_data:
            if offset + 2 > buflen:
                new_data = file.read(cachesize)
                if not new_data:
                    eof_reached = True
                data_buffer = data_view[offset:].tobytes() + new_data
                data_view = memoryview(data_buffer)
                buflen = len(data_view)
                offset = 0
                continue

            if data_view[offset] != 0:
                raise InvalidMessageFormatError(f"Unexpected byte: {data_view[offset]}")

            message_len = data_view[offset + 1]
            message_end = offset + 2 + message_len

            if message_end > buflen:
                new_data = file.read(cachesize)
                if not new_data:
                    eof_reached = True
                data_buffer = data_view[offset:].tobytes() + new_data
                data_view = memoryview(data_buffer)
                buflen = len(data_view)
                offset = 0
                continue

            message = self._create_message(data_view[offset + 2 : message_end])

            # Check if we should keep this message type
            if (
                self.keep_message_types is not None
                and getattr(message.__class__, "type", None)
                not in self.keep_message_types
            ):
                offset = message_end
                continue

            # Check if we should keep this symbol
            if (
                self.symbols is not None
                and hasattr(message, "stock")
                and message.stock not in self.symbols
            ):
                offset = message_end
                continue

            yield message
            offset = message_end

            if offset >= buflen and eof_reached:
                have_data = False

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

    def _create_message(self, message_data: bytes) -> ITCH50MarketMessage:
        """Create an ITCH50MarketMessage from raw message data.

        Args:
            message_data: Raw message bytes

        Returns:
            Appropriate ITCH50MarketMessage subclass instance

        Raises:
            UnknownMessageTypeError: If message type is not recognized
        """
        msgtype = chr(message_data[0])

        if msgtype == "S":
            return SystemEventMessage(message_data)
        elif msgtype == "R":
            return StockDirectoryMessage(message_data)
        elif msgtype == "H":
            return StockTradingActionMessage(message_data)
        elif msgtype == "Y":
            return RegSHOMessage(message_data)
        elif msgtype == "L":
            return MarketParticipantPositionMessage(message_data)
        elif msgtype == "V":
            return MWCBDeclineLevelMessage(message_data)
        elif msgtype == "W":
            return MWCBBreachMessage(message_data)
        elif msgtype == "K":
            return IPOQuotingPeriodUpdateMessage(message_data)
        elif msgtype == "J":
            return LULDAuctionCollarMessage(message_data)
        elif msgtype == "h":
            return OperationalHaltMessage(message_data)
        elif msgtype == "A":
            return AddOrderMessage(message_data)
        elif msgtype == "F":
            return AddOrderMPIDMessage(message_data)
        elif msgtype == "E":
            return OrderExecutedMessage(message_data)
        elif msgtype == "C":
            return OrderExecutedPriceMessage(message_data)
        elif msgtype == "X":
            return OrderCancelMessage(message_data)
        elif msgtype == "D":
            return OrderDeleteMessage(message_data)
        elif msgtype == "U":
            return OrderReplaceMessage(message_data)
        elif msgtype == "P":
            return TradeMessage(message_data)
        elif msgtype == "Q":
            return CrossTradeMessage(message_data)
        elif msgtype == "B":
            return BrokenTradeMessage(message_data)
        elif msgtype == "I":
            return NoiiMessage(message_data)
        elif msgtype == "N":
            return RpiiMessage(message_data)
        elif msgtype == "O":
            return DirectListingCapitalRaiseMessage(message_data)
        else:
            raise UnknownMessageTypeError(f"Unknown message type: {msgtype}")
