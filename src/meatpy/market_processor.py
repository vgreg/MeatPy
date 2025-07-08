"""Market processor framework for reconstructing market history.

This module provides the MarketProcessor abstract base class that serves as
the core engine for processing market messages and reconstructing the limit
order book history for a specific instrument.
"""

import abc
from datetime import date, datetime
from typing import Generic

from .lob import LimitOrderBook, OrderType
from .market_event_handler import MarketEventHandler
from .message_parser import MarketMessage
from .timestamp import Timestamp
from .trading_status import TradingStatus
from .types import OrderID, Price, Qualifiers, TradeRef, Volume


class MarketProcessor(Generic[Price, Volume, OrderID, TradeRef, Qualifiers]):
    """A market engine that processes events and builds the limit order book.

    A MarketProcessor object is an engine that processes MarketMessage objects
    to build the market history for one instrument, on one day and on one
    market. The MarketProcessor keeps an up-to-date version of the limit order
    book, unless instructed not to.

    This is an abstract base class that must be subclassed for specific
    market data formats and protocols.

    Attributes:
        instrument: The instrument/symbol being processed
        book_date: The trading date for this processor
        current_lob: The current limit order book state
        track_lob: Whether to maintain the limit order book
        handlers: List of event handlers to notify of events
        trading_status: Current trading status of the market
    """

    __metaclass__ = abc.ABCMeta  # This is an abstract class

    def __init__(
        self,
        instrument: str | bytes,
        book_date: date | datetime | None,
    ) -> None:
        """Initialize a market processor for a specific instrument and date.

        Args:
            instrument: The instrument/symbol to process
            book_date: The trading date for this processor
        """
        self.instrument: str | bytes = instrument
        self.book_date: date | datetime | None = book_date
        self.current_lob: LimitOrderBook | None = None
        self.track_lob: bool = True
        self.handlers: list[MarketEventHandler] = []
        self.trading_status: TradingStatus | None = None

    @abc.abstractmethod
    def process_message(self, message: MarketMessage) -> None:
        """Process a MarketMessage.

        This is an abstract method that must be implemented by subclasses
        to handle their specific message format.

        Args:
            message: The market message to process
        """
        return

    def processing_done(self) -> None:
        """Perform cleanup when processing is complete.

        Calls end_of_day() on the current limit order book if it exists.
        """
        if self.current_lob is not None:
            self.current_lob.end_of_day()

    def before_lob_update(self, new_timestamp: Timestamp) -> None:
        """Notify handlers before a limit order book update.

        Args:
            new_timestamp: The new timestamp for the upcoming update
        """
        for x in self.handlers:
            x.before_lob_update(self.current_lob, new_timestamp)

    def message_event(self, timestamp: Timestamp, message: MarketMessage) -> None:
        """Notify handlers of a raw message event.

        Args:
            timestamp: The timestamp of the message
            message: The parsed market message
        """
        for x in self.handlers:
            x.message_event(self, timestamp, message)

    def enter_quote_event(
        self,
        timestamp: Timestamp,
        price: Price,
        volume: Volume,
        order_id: OrderID,
        order_type: OrderType | None = None,
    ) -> None:
        """Notify handlers of a quote entry event.

        Args:
            timestamp: The timestamp of the event
            price: The price of the quote
            volume: The volume of the quote
            order_id: The unique identifier for the order
            order_type: The type of order (bid/ask), if known
        """
        for x in self.handlers:
            x.enter_quote_event(self, timestamp, price, volume, order_id, order_type)

    def cancel_quote_event(
        self,
        timestamp: Timestamp,
        volume: Volume,
        order_id: OrderID,
        order_type: OrderType | None = None,
    ) -> None:
        """Notify handlers of a quote cancellation event.

        Args:
            timestamp: The timestamp of the event
            volume: The volume being cancelled
            order_id: The unique identifier for the order
            order_type: The type of order (bid/ask), if known
        """
        for x in self.handlers:
            x.cancel_quote_event(self, timestamp, volume, order_id, order_type)

    def delete_quote_event(
        self,
        timestamp: Timestamp,
        order_id: OrderID,
        order_type: OrderType | None = None,
    ) -> None:
        """Notify handlers of a quote deletion event.

        Args:
            timestamp: The timestamp of the event
            order_id: The unique identifier for the order being deleted
            order_type: The type of order (bid/ask), if known
        """
        for x in self.handlers:
            x.delete_quote_event(self, timestamp, order_id, order_type)

    def replace_quote_event(
        self,
        timestamp: Timestamp,
        orig_order_id: OrderID,
        new_order_id: OrderID,
        price: Price,
        volume: Volume,
        order_type: OrderType | None = None,
    ) -> None:
        """Notify handlers of a quote replacement event.

        Args:
            timestamp: The timestamp of the event
            orig_order_id: The original order identifier
            new_order_id: The new order identifier
            price: The new price of the quote
            volume: The new volume of the quote
            order_type: The type of order (bid/ask), if known
        """
        for x in self.handlers:
            x.replace_quote_event(
                self, timestamp, orig_order_id, new_order_id, price, volume, order_type
            )

    def execute_trade_event(
        self,
        timestamp: Timestamp,
        volume: Volume,
        order_id: OrderID,
        trade_ref: TradeRef,
        order_type: OrderType | None = None,
    ) -> None:
        """Notify handlers of a trade execution event.

        Args:
            timestamp: The timestamp of the event
            volume: The volume traded
            order_id: The unique identifier for the order
            trade_ref: The trade reference identifier
            order_type: The type of order (bid/ask), if known
        """
        for x in self.handlers:
            x.execute_trade_event(
                self, timestamp, volume, order_id, trade_ref, order_type
            )

    def execute_trade_price_event(
        self,
        timestamp: Timestamp,
        volume: Volume,
        order_id: OrderID,
        trade_ref: TradeRef,
        price: Price,
        order_type: OrderType | None = None,
    ) -> None:
        """Notify handlers of a trade execution event with price information.

        Args:
            timestamp: The timestamp of the event
            volume: The volume traded
            order_id: The unique identifier for the order
            trade_ref: The trade reference identifier
            price: The execution price
            order_type: The type of order (bid/ask), if known
        """
        for x in self.handlers:
            x.execute_trade_price_event(
                self, timestamp, volume, order_id, trade_ref, price, order_type
            )

    def auction_trade_event(
        self,
        timestamp: Timestamp,
        volume: Volume,
        price: Price,
        bid_id: OrderID,
        ask_id: OrderID,
    ) -> None:
        """Notify handlers of an auction trade event.

        Args:
            timestamp: The timestamp of the event
            volume: The volume traded
            price: The auction price
            bid_id: The bid order identifier
            ask_id: The ask order identifier
        """
        for x in self.handlers:
            x.auction_trade_event(self, timestamp, volume, price, bid_id, ask_id)

    def crossing_trade_event(
        self,
        timestamp: Timestamp,
        volume: Volume,
        price: Price,
        bid_id: OrderID,
        ask_id: OrderID,
    ) -> None:
        """Notify handlers of a crossing trade event.

        Args:
            timestamp: The timestamp of the event
            volume: The volume traded
            price: The crossing price
            bid_id: The bid order identifier
            ask_id: The ask order identifier
        """
        for x in self.handlers:
            x.crossing_trade_event(self, timestamp, volume, price, bid_id, ask_id)

    def pre_lob_event(self, timestamp: Timestamp, new_snapshot: bool = True) -> None:
        """Prepare the limit order book for a new event.

        If no current LOB exists, create one. Otherwise only create a new one
        if requested. This method manages the LOB state transitions.

        Args:
            timestamp: The timestamp for the new event
            new_snapshot: Whether to create a new snapshot (default: True)
        """
        if self.current_lob is None:
            self.current_lob = LimitOrderBook(timestamp)
            # self.snapshots.append(self.current_lob)
        elif new_snapshot is True:
            self.before_lob_update(timestamp)
            if self.current_lob.timestamp == timestamp:
                self.current_lob.timestamp_inc += 1
            else:
                self.current_lob.timestamp_inc = 0
            self.current_lob.timestamp = timestamp
