"""ITCH 3.0 market processor for limit order book reconstruction.

This module provides the ITCH3MarketProcessor class, which processes ITCH 3.0
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
    QuoteOnlyTradingStatus,
    TradeTradingStatus,
)
from .itch3_market_message import (
    AddOrderMessage,
    AddOrderMPIDMessage,
    BrokenTradeMessage,
    CrossTradeMessage,
    ITCH3MarketMessage,
    MillisecondsMessage,
    NoiiMessage,
    OrderCancelMessage,
    OrderDeleteMessage,
    OrderExecutedMessage,
    OrderExecutedPriceMessage,
    SecondsMessage,
    StockDirectoryMessage,
    StockTradingActionMessage,
    SystemEventMessage,
    TradeMessage,
)


class InvalidBuySellIndicatorError(Exception):
    """Exception raised when an invalid buy/sell indicator is encountered.

    This exception is raised when the buy/sell indicator value is not
    recognized by the ITCH 3.0 processor.
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
    recognized by the ITCH 3.0 processor.
    """

    pass


class ITCH3MarketProcessor(MarketProcessor[int, int, int, int, dict[str, str]]):
    """A market processor for ITCH 3.0 format.

    This processor handles ITCH 3.0 market messages and reconstructs the limit
    order book. It processes order additions, executions, cancellations, and
    trading status updates.

    ITCH 3.0 is ASCII format with separate T (seconds) and M (milliseconds)
    timestamp messages.

    Attributes:
        system_status: Current system status code
        stock_status: Current stock trading status code
        current_second: Current second from T message
        current_millisecond: Current millisecond from M message
    """

    def __init__(self, instrument: str | bytes, book_date: datetime.datetime) -> None:
        """Initialize the ITCH3MarketProcessor.

        Args:
            instrument: The instrument symbol to process
            book_date: The date for the limit order book
        """
        super().__init__(instrument, book_date)
        self.current_second: int = 0
        self.current_millisecond: int = 0
        self.system_status: bytes = b""
        self.stock_status: bytes = b""
        self.lob: LimitOrderBook[int, int, int, int, dict[str, str]] | None = None

    def adjust_timestamp(self) -> Timestamp:
        """Adjust the raw timestamp to a datetime object for ITCH 3.0.

        In ITCH 3.0, timestamps are assembled from:
        - current_second: from the latest SecondsMessage (T)
        - current_millisecond: from the latest MillisecondsMessage (M)

        Returns:
            A Timestamp object representing the adjusted time
        """
        # Convert seconds and milliseconds to nanoseconds
        total_milliseconds = (self.current_second * 1000) + self.current_millisecond
        total_nanoseconds = total_milliseconds * 1_000_000

        return Timestamp.from_datetime(
            self.book_date + datetime.timedelta(milliseconds=total_milliseconds),
            nanoseconds=total_nanoseconds,
        )

    def process_message(self, message: MarketMessage) -> None:
        """Process a market message and update the limit order book.

        Args:
            message: The market message to process

        Raises:
            TypeError: If the message is not an ITCH3MarketMessage
        """
        if not isinstance(message, ITCH3MarketMessage):
            raise TypeError(f"Expected ITCH3MarketMessage, got {type(message)}")

        # Handle timestamp messages
        if isinstance(message, SecondsMessage):
            self.current_second = message.seconds
            self.current_timestamp = self.adjust_timestamp()
            self.message_event(self.current_timestamp, message)
            return

        if isinstance(message, MillisecondsMessage):
            self.current_millisecond = message.milliseconds
            self.current_timestamp = self.adjust_timestamp()
            self.message_event(self.current_timestamp, message)
            return

        # Update current timestamp for all other messages
        self.current_timestamp = self.adjust_timestamp()

        # Process based on message type
        if isinstance(message, SystemEventMessage):
            self._process_system_event(message)
        elif isinstance(message, StockDirectoryMessage):
            self._process_stock_directory(message)
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
        elif isinstance(message, TradeMessage):
            self._process_trade(message)
        elif isinstance(message, CrossTradeMessage):
            self._process_cross_trade(message)
        elif isinstance(message, BrokenTradeMessage):
            self._process_broken_trade(message)
        elif isinstance(message, NoiiMessage):
            self._process_noii(message)

        # Notify handlers after processing
        self.message_event(self.current_timestamp, message)

    def _process_system_event(self, message: SystemEventMessage) -> None:
        """Process a system event message."""
        self.system_status = message.event_code

        # Update trading status when system status changes
        self._update_trading_status()

    def _process_stock_directory(self, message: StockDirectoryMessage) -> None:
        """Process a stock directory message.

        Stock directory messages provide information about tradeable stocks.
        """
        pass  # Informational only

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

    def _process_add_order_mpid(self, message: AddOrderMPIDMessage) -> None:
        """Process an add order with MPID message."""
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

        # Add order to the book (MPID is ignored for book reconstruction)
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
            return

        # Check if order exists in our book
        try:
            order_type = self.lob.find_order_type(message.order_ref)
        except OrderNotFoundError:
            return

        self.lob.execute_trade(
            timestamp=self.current_timestamp,
            volume=message.shares,
            order_id=message.order_ref,
            order_type=order_type,
        )

    def _process_order_executed_price(self, message: OrderExecutedPriceMessage) -> None:
        """Process an order executed with price message."""
        if self.lob is None:
            return

        # Check if order exists in our book
        try:
            order_type = self.lob.find_order_type(message.order_ref)
        except OrderNotFoundError:
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
            return

        # Check if order exists in our book
        try:
            order_type = self.lob.find_order_type(message.order_ref)
        except OrderNotFoundError:
            return

        self.lob.cancel_quote(
            volume=message.shares,
            order_id=message.order_ref,
            order_type=order_type,
        )

    def _process_order_delete(self, message: OrderDeleteMessage) -> None:
        """Process an order delete message."""
        if self.lob is None:
            return

        # Check if order exists in our book
        try:
            order_type = self.lob.find_order_type(message.order_ref)
        except OrderNotFoundError:
            return

        self.lob.delete_quote(
            order_id=message.order_ref,
            order_type=order_type,
        )

    def _process_trade(self, message: TradeMessage) -> None:
        """Process a trade message.

        Trade messages are for non-displayed orders and don't affect
        the visible order book.
        """
        pass

    def _process_cross_trade(self, message: CrossTradeMessage) -> None:
        """Process a cross trade message.

        Cross trade messages don't affect the order book.
        """
        pass

    def _process_broken_trade(self, message: BrokenTradeMessage) -> None:
        """Process a broken trade message.

        Broken trade messages indicate a previously reported trade has been
        cancelled. This is informational only and doesn't affect the LOB.
        """
        pass

    def _process_noii(self, message: NoiiMessage) -> None:
        """Process a NOII message.

        NOII messages provide information about order imbalances
        during cross events.
        """
        pass

    def _update_trading_status(self) -> None:
        """Update the trading status based on system and stock status."""
        new_status = self._determine_trading_status()
        if new_status != self.trading_status:
            self.trading_status = new_status

    def _determine_trading_status(self) -> type:
        """Determine the trading status from system and stock status codes.

        Returns:
            The appropriate trading status class
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
            return HaltedTradingStatus
