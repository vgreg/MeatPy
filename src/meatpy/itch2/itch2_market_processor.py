"""ITCH 2.0 market processor for limit order book reconstruction.

This module provides the ITCH2MarketProcessor class, which processes ITCH 2.0
market messages to reconstruct the limit order book and handle trading status updates.
"""

import datetime

from ..lob import LimitOrderBook, OrderNotFoundError, OrderType
from ..market_processor import MarketProcessor
from ..message_reader import MarketMessage
from ..timestamp import Timestamp
from ..trading_status import (
    HaltedTradingStatus,
    PostTradeTradingStatus,
    PreTradeTradingStatus,
    TradeTradingStatus,
)
from .itch2_market_message import (
    AddOrderMessage,
    BrokenTradeMessage,
    ITCH2MarketMessage,
    OrderCancelMessage,
    OrderExecutedMessage,
    SystemEventMessage,
    TradeMessage,
)


class InvalidBuySellIndicatorError(Exception):
    """Exception raised when an invalid buy/sell indicator is encountered.

    This exception is raised when the buy/sell indicator value is not
    recognized by the ITCH 2.0 processor.
    """

    pass


class MissingLOBError(Exception):
    """Exception raised when attempting to perform operations without a LOB.

    This exception is raised when trying to cancel, execute, or modify
    orders when no limit order book is available.
    """

    pass


class UnknownSystemMessageError(Exception):
    """Exception raised when an unknown system message is encountered.

    This exception is raised when the system message code is not
    recognized by the ITCH 2.0 processor.
    """

    pass


class ITCH2MarketProcessor(MarketProcessor[int, int, int, int, dict[str, str]]):
    """A market processor for ITCH 2.0 format.

    This processor handles ITCH 2.0 market messages and reconstructs the limit
    order book. It processes order additions, executions, cancellations, and
    trading status updates.

    ITCH 2.0 is ASCII format with timestamps in milliseconds embedded in each message.

    Attributes:
        system_status: Current system status code
    """

    def __init__(self, instrument: str | bytes, book_date: datetime.datetime) -> None:
        """Initialize the ITCH2MarketProcessor.

        Args:
            instrument: The instrument symbol to process
            book_date: The date for the limit order book
        """
        super().__init__(instrument, book_date)
        self.system_status: bytes = b""
        self.lob: LimitOrderBook[int, int, int, int, dict[str, str]] | None = None

    def adjust_timestamp(self, message_timestamp: int) -> Timestamp:
        """Adjust the raw timestamp to a datetime object for ITCH 2.0.

        In ITCH 2.0, timestamps are milliseconds from midnight.

        Args:
            message_timestamp: The message timestamp in milliseconds from midnight

        Returns:
            A Timestamp object representing the adjusted time
        """
        # Convert milliseconds to nanoseconds
        total_nanoseconds = message_timestamp * 1_000_000

        return Timestamp.from_datetime(
            self.book_date + datetime.timedelta(milliseconds=message_timestamp),
            nanoseconds=total_nanoseconds,
        )

    def process_message(self, message: MarketMessage) -> None:
        """Process a market message and update the limit order book.

        Args:
            message: The market message to process

        Raises:
            TypeError: If the message is not an ITCH2MarketMessage
        """
        if not isinstance(message, ITCH2MarketMessage):
            raise TypeError(f"Expected ITCH2MarketMessage, got {type(message)}")

        # Calculate timestamp from message
        self.current_timestamp = self.adjust_timestamp(message.timestamp)

        # Process based on message type
        if isinstance(message, SystemEventMessage):
            self._process_system_event(message)
        elif isinstance(message, AddOrderMessage):
            self._process_add_order(message)
        elif isinstance(message, OrderExecutedMessage):
            self._process_order_executed(message)
        elif isinstance(message, OrderCancelMessage):
            self._process_order_cancel(message)
        elif isinstance(message, TradeMessage):
            self._process_trade(message)
        elif isinstance(message, BrokenTradeMessage):
            self._process_broken_trade(message)

        # Notify handlers after processing
        self.message_event(self.current_timestamp, message)

    def _process_system_event(self, message: SystemEventMessage) -> None:
        """Process a system event message."""
        self.system_status = message.event_code

        # Update trading status when system status changes
        self._update_trading_status()

    def _process_add_order(self, message: AddOrderMessage) -> None:
        """Process an add order message."""
        # Check if this message is for our instrument
        stock_symbol = message.stock.decode().rstrip()
        if isinstance(self.instrument, bytes):
            instrument_str = self.instrument.decode().rstrip()
        else:
            instrument_str = self.instrument.rstrip()

        if stock_symbol != instrument_str:
            return

        if self.lob is None:
            self.lob = LimitOrderBook[int, int, int, int, dict[str, str]](
                self.current_timestamp
            )

        # Determine order type from side indicator
        if message.side == b"B":
            order_type = OrderType.BID
        elif message.side == b"S":
            order_type = OrderType.ASK
        else:
            raise InvalidBuySellIndicatorError(f"Invalid side: {message.side}")

        # Add order to the book
        self.lob.enter_quote(
            timestamp=self.current_timestamp,
            price=message.price,
            volume=message.shares,
            order_id=message.order_ref,
            order_type=order_type,
        )

    def _process_order_executed(self, message: OrderExecutedMessage) -> None:
        """Process an order executed message."""
        if self.lob is None:
            # Order may not be for our instrument
            return

        # Check if order exists in our book
        try:
            order_type = self.lob.find_order_type(message.order_ref)
        except OrderNotFoundError:
            # Order not in our book (different instrument)
            return

        self.lob.execute_trade(
            timestamp=self.current_timestamp,
            volume=message.shares,
            order_id=message.order_ref,
            order_type=order_type,
        )

    def _process_order_cancel(self, message: OrderCancelMessage) -> None:
        """Process an order cancel message."""
        if self.lob is None:
            # Order may not be for our instrument
            return

        # Check if order exists in our book
        try:
            order_type = self.lob.find_order_type(message.order_ref)
        except OrderNotFoundError:
            # Order not in our book (different instrument)
            return

        self.lob.cancel_quote(
            volume=message.shares,
            order_id=message.order_ref,
            order_type=order_type,
        )

    def _process_trade(self, message: TradeMessage) -> None:
        """Process a trade message.

        Trade messages in ITCH 2.0 are for non-displayed orders and
        don't affect the visible order book.
        """
        # Trade messages don't affect the LOB directly
        # They represent hidden order executions
        pass

    def _process_broken_trade(self, message: BrokenTradeMessage) -> None:
        """Process a broken trade message.

        Broken trade messages indicate a previously reported trade has been
        cancelled. This is informational only and doesn't affect the LOB.
        """
        pass

    def _update_trading_status(self) -> None:
        """Update the trading status based on system status."""
        new_status = self._determine_trading_status()
        if new_status != self.trading_status:
            self.trading_status = new_status

    def _determine_trading_status(self) -> type:
        """Determine the trading status from system status code.

        Returns:
            The appropriate trading status class
        """
        # System status mapping for ITCH 2.0
        system_map = {
            b"O": "start_messages",
            b"S": "start_system",
            b"Q": "start_market",
            b"M": "end_market",
            b"E": "end_system",
            b"C": "end_messages",
        }

        system_status = system_map.get(self.system_status, "unknown")

        # Determine status based on system events
        if system_status in ["start_messages", "end_messages", "end_system"]:
            return PostTradeTradingStatus
        elif system_status == "start_system":
            return PreTradeTradingStatus
        elif system_status in ["start_market", "end_market"]:
            return TradeTradingStatus
        else:
            return HaltedTradingStatus
