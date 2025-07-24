"""ITCH 4.1 market processor for limit order book reconstruction.

This module provides the ITCH41MarketProcessor class, which processes ITCH 4.1
market messages to reconstruct the limit order book and handle trading status updates.
"""

import datetime

from ..lob import LimitOrderBook, OrderType
from ..market_processor import MarketProcessor
from ..message_reader import MarketMessage
from ..timestamp import Timestamp
from ..trading_status import (
    HaltedTradingStatus,
    PostTradeTradingStatus,
    PreTradeTradingStatus,
    QuoteOnlyTradingStatus,
    TradeTradingStatus,
)
from .itch41_market_message import (
    AddOrderMessage,
    AddOrderMPIDMessage,
    ITCH41MarketMessage,
    OrderCancelMessage,
    OrderDeleteMessage,
    OrderExecutedMessage,
    OrderExecutedPriceMessage,
    OrderReplaceMessage,
    SecondsMessage,
    StockTradingActionMessage,
    SystemEventMessage,
)


class InvalidBuySellIndicatorError(Exception):
    """Exception raised when an invalid buy/sell indicator is encountered.

    This exception is raised when the buy/sell indicator value is not
    recognized by the ITCH 4.1 processor.
    """

    pass


class MissingLOBError(Exception):
    """Exception raised when attempting to perform operations without a LOB.

    This exception is raised when trying to cancel, delete, or replace
    orders when no limit order book is available.
    """

    pass


class UnknownSystemMessageError(Exception):
    """Exception raised when an unknown system message is encountered.

    This exception is raised when the system message code is not
    recognized by the ITCH 4.1 processor.
    """

    pass


class UnknownTradingStateError(Exception):
    """Exception raised when an unknown trading state is encountered.

    This exception is raised when the trading state code is not
    recognized by the ITCH 4.1 processor.
    """

    pass


class InvalidTradingStatusError(Exception):
    """Exception raised when the trading status cannot be determined.

    This exception is raised when the combination of system status,
    EMC status, and stock status does not correspond to a valid
    trading status.
    """

    pass


class ITCH41MarketProcessor(MarketProcessor[int, int, int, int, dict[str, str]]):
    """A market processor for ITCH 4.1 format.

    This processor handles ITCH 4.1 market messages and reconstructs the limit
    order book. It processes order additions, executions, cancellations, and
    trading status updates.

    Attributes:
        system_status: Current system status code
        stock_status: Current stock trading status code
    """

    def __init__(self, instrument: str | bytes, book_date: datetime.datetime) -> None:
        """Initialize the ITCH41MarketProcessor.

        Args:
            instrument: The instrument symbol to process
            book_date: The date for the limit order book
        """
        super().__init__(instrument, book_date)
        self.current_second: int = 0
        self.system_status: bytes = b""
        self.stock_status: bytes = b""
        self.lob: LimitOrderBook[int, int, int, int, dict[str, str]] | None = None

    def adjust_timestamp(
        self, current_second: int, message_timestamp: int
    ) -> Timestamp:
        """Adjust the raw timestamp to a datetime object for ITCH 4.1.

        In ITCH 4.1, timestamps are assembled from:
        - current_second: from the latest SecondsMessage
        - message_timestamp: offset within that second (in nanoseconds)

        Args:
            current_second: The current second from SecondsMessage
            message_timestamp: The message timestamp offset in nanoseconds

        Returns:
            A Timestamp object representing the adjusted time
        """
        # Combine second and nanosecond offset
        total_nanoseconds = (current_second * 1_000_000_000) + message_timestamp

        return Timestamp.from_datetime(
            self.book_date + datetime.timedelta(microseconds=total_nanoseconds // 1000),
            nanoseconds=total_nanoseconds,
        )

    def process_message(self, message: MarketMessage) -> None:
        """Process a market message and update the limit order book.

        Args:
            message: The market message to process

        Raises:
            TypeError: If the message is not an ITCH41MarketMessage
        """
        if not isinstance(message, ITCH41MarketMessage):
            raise TypeError(f"Expected ITCH41MarketMessage, got {type(message)}")

        # Handle SecondsMessage specially - it updates current_second
        if isinstance(message, SecondsMessage):
            self.current_second = message.seconds
            # For SecondsMessage, timestamp is just the seconds converted to nanoseconds
            self.current_timestamp = self.adjust_timestamp(message.seconds, 0)
            self.message_event(self.current_timestamp, message)
            return

        # For all other messages, assemble timestamp from current_second and message timestamp
        self.current_timestamp = self.adjust_timestamp(
            self.current_second, message.timestamp
        )

        # Process based on message type
        if isinstance(message, SystemEventMessage):
            self._process_system_event(message)
        elif isinstance(message, StockTradingActionMessage):
            self._process_stock_trading_action(message)
        elif isinstance(message, AddOrderMessage):
            self._process_add_order(message)
        elif isinstance(message, AddOrderMPIDMessage):
            self._process_add_order_mpid(message)
        elif isinstance(message, OrderExecutedMessage):
            self._process_order_executed(message)
        elif isinstance(message, OrderExecutedPriceMessage):
            self._process_order_executed_price(message)
        elif isinstance(message, OrderCancelMessage):
            self._process_order_cancel(message)
        elif isinstance(message, OrderDeleteMessage):
            self._process_order_delete(message)
        elif isinstance(message, OrderReplaceMessage):
            self._process_order_replace(message)

        # Notify handlers after processing
        self.message_event(self.current_timestamp, message)

    def _process_system_event(self, message: SystemEventMessage) -> None:
        """Process a system event message."""
        self.system_status = message.event_code

        # Update trading status when system status changes
        self._update_trading_status()

    def _process_stock_trading_action(self, message: StockTradingActionMessage) -> None:
        """Process a stock trading action message."""
        # Check if this message is for our instrument
        stock_symbol = message.stock.decode().rstrip()
        if isinstance(self.instrument, bytes):
            instrument_str = self.instrument.decode().rstrip()
        else:
            instrument_str = self.instrument.rstrip()

        if stock_symbol != instrument_str:
            return

        self.stock_status = message.state

        # Update trading status when stock status changes
        self._update_trading_status()

    def _process_add_order(self, message: AddOrderMessage) -> None:
        """Process an add order message."""
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

    def _process_add_order_mpid(self, message: AddOrderMPIDMessage) -> None:
        """Process an add order with MPID message."""
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

        # Add order to the book (MPID is ignored for book reconstruction)
        self.lob.enter_quote(
            order_id=message.order_ref,
            order_type=order_type,
            price=message.price,
            volume=message.shares,
            timestamp=self.current_timestamp,
        )

    def _process_order_executed(self, message: OrderExecutedMessage) -> None:
        """Process an order executed message."""
        if self.lob is None:
            raise MissingLOBError("Cannot execute order without LOB")

        # Find the order type to properly execute the trade
        order_type = self.lob.find_order_type(message.order_ref)
        self.lob.execute_trade(
            timestamp=self.current_timestamp,
            volume=message.shares,
            order_id=message.order_ref,
            order_type=order_type,
        )

    def _process_order_executed_price(self, message: OrderExecutedPriceMessage) -> None:
        """Process an order executed with price message."""
        if self.lob is None:
            raise MissingLOBError("Cannot execute order without LOB")

        # Find the order type to properly execute the trade
        order_type = self.lob.find_order_type(message.order_ref)
        self.lob.execute_trade(
            timestamp=self.current_timestamp,
            volume=message.shares,
            order_id=message.order_ref,
            order_type=order_type,
        )

    def _process_order_cancel(self, message: OrderCancelMessage) -> None:
        """Process an order cancel message."""
        if self.lob is None:
            raise MissingLOBError("Cannot cancel order without LOB")

        # Find the order type to properly cancel the quote
        order_type = self.lob.find_order_type(message.order_ref)
        self.lob.cancel_quote(
            volume=message.shares,
            order_id=message.order_ref,
            order_type=order_type,
        )

    def _process_order_delete(self, message: OrderDeleteMessage) -> None:
        """Process an order delete message."""
        if self.lob is None:
            raise MissingLOBError("Cannot delete order without LOB")

        # Find the order type to properly delete the quote
        order_type = self.lob.find_order_type(message.order_ref)
        self.lob.delete_quote(
            order_id=message.order_ref,
            order_type=order_type,
        )

    def _process_order_replace(self, message: OrderReplaceMessage) -> None:
        """Process an order replace message."""
        if self.lob is None:
            raise MissingLOBError("Cannot replace order without LOB")

        # Find the order type of the original order
        order_type = self.lob.find_order_type(message.original_ref)

        # Delete the original order
        self.lob.delete_quote(message.original_ref, order_type)

        # Add the new order
        self.lob.enter_quote(
            timestamp=self.current_timestamp,
            price=message.price,
            volume=message.shares,
            order_id=message.new_ref,
            order_type=order_type,
        )

    def _update_trading_status(self) -> None:
        """Update the trading status based on system and stock status."""
        new_status = self._determine_trading_status()
        if new_status != self.trading_status:
            self.trading_status = new_status

    def _determine_trading_status(self) -> type:
        """Determine the trading status from system and stock status codes.

        Returns:
            The appropriate trading status class

        Raises:
            InvalidTradingStatusError: If status cannot be determined
        """
        # System status mapping
        system_map = {
            b"O": "start_messages",
            b"S": "start_system",
            b"Q": "start_market",
            b"M": "end_market",
            b"E": "end_system",
            b"C": "end_messages",
        }

        # Stock status mapping
        stock_map = {
            b"H": "halted",
            b"P": "paused",
            b"Q": "quotation_only",
            b"T": "trading",
        }

        system_status = system_map.get(self.system_status, "unknown")
        stock_status = stock_map.get(self.stock_status, "unknown")

        # Determine combined status
        if system_status in ["start_messages", "end_messages", "end_system"]:
            return PostTradeTradingStatus
        elif system_status == "start_system":
            return PreTradeTradingStatus
        elif system_status in ["start_market", "end_market"]:
            if stock_status == "trading":
                return TradeTradingStatus
            elif stock_status in ["halted", "paused"]:
                return HaltedTradingStatus
            elif stock_status == "quotation_only":
                return QuoteOnlyTradingStatus
            else:
                return PreTradeTradingStatus
        else:
            raise InvalidTradingStatusError(
                f"Cannot determine status from system={system_status}, stock={stock_status}"
            )
