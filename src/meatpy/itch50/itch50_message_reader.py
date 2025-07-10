"""ITCH 5.0 file reader with generator interface.

This module provides the ITCH50MessageReader class, which reads ITCH 5.0 market data files
and yields structured message objects one at a time using a generator interface.
"""

from __future__ import annotations

from pathlib import Path
from typing import Generator, Optional

from ..message_reader import MessageReader
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


class ITCH50MessageReader(MessageReader):
    """A market message reader for ITCH 5.0 data with generator interface.

    This reader reads ITCH 5.0 files and yields message objects one at a time,
    supporting automatic detection of compressed files (gzip, bzip2, xz, zip).

    Attributes:
        file_path: Path to the ITCH file to read
        _file_handle: Internal file handle when used as context manager
    """

    def __init__(
        self,
        file_path: Optional[Path | str] = None,
    ) -> None:
        """Initialize the ITCH50MessageReader.

        Args:
            file_path: Path to the ITCH file to read (optional if using read_file method)
        """
        super().__init__(file_path)

    def __iter__(self) -> Generator[ITCH50MarketMessage, None, None]:
        """Make the reader iterable when used as a context manager."""
        if self._file_handle is None:
            raise RuntimeError(
                "Reader must be used as a context manager to be iterable"
            )
        yield from self._read_messages(self._file_handle)

    def read_file(
        self, file_path: Path | str
    ) -> Generator[ITCH50MarketMessage, None, None]:
        """Parse an ITCH 5.0 file and yield messages one at a time.

        Args:
            file_path: Path to the ITCH file to read

        Yields:
            ITCH50MarketMessage objects
        """
        file_path = Path(file_path)
        with self._open_file(file_path) as file:
            yield from self._read_messages(file)

    def _read_messages(self, file) -> Generator[ITCH50MarketMessage, None, None]:
        """Internal method to read messages from an open file handle.

        Args:
            file: Open file handle to read from

        Yields:
            ITCH50MarketMessage objects
        """
        from ..message_reader import InvalidMessageFormatError

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

            yield message
            offset = message_end

            if offset >= buflen and eof_reached:
                have_data = False

    def _create_message(self, message_data: bytes) -> ITCH50MarketMessage:
        """Create an ITCH50MarketMessage from raw message data.

        Args:
            message_data: Raw message bytes

        Returns:
            Appropriate ITCH50MarketMessage subclass instance

        Raises:
            UnknownMessageTypeError: If message type is not recognized
        """
        from ..message_reader import UnknownMessageTypeError

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
