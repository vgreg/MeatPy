"""market_processor.py: The market engine that receives message and
re-constructs the market history."""

import abc
from datetime import date, datetime

from .lob import LimitOrderBook, OrderType
from .market_event_handler import MarketEventHandler
from .message_parser import MarketMessage
from .timestamp import Timestamp
from .trading_status import TradingStatus
from .types import OrderID, Price, TradeRef, Volume


class MarketProcessor:
    """A market engine that process events and builds the limit order book

    A MarketProcessor object is an engine that processes MarketMessage objects
    to build the market history for one instrument, on one day and on one
    market.

    The MarketProcessor keeps an up-to-date version of
    the limit order book, unless instructed not to."""

    __metaclass__ = abc.ABCMeta  # This in an abstract class

    def __init__(
        self,
        instrument: str | bytes,
        book_date: date | datetime | None,
    ) -> None:
        """Initializes an empty history for a specific instrument and date."""
        self.instrument: str | bytes = instrument
        self.book_date: date | datetime | None = book_date
        self.current_lob: LimitOrderBook | None = None
        self.track_lob: bool = True
        self.handlers: list[MarketEventHandler] = []
        self.trading_status: TradingStatus | None = None

    @abc.abstractmethod
    def process_message(self, message: MarketMessage) -> None:
        """Process a MarketMessage

        :param message: message to process
        :type message: MarketMessage
        """
        return

    def processing_done(self) -> None:
        """Clean up time"""
        if self.current_lob is not None:
            self.current_lob.end_of_day()

    def before_lob_update(self, new_timestamp: Timestamp) -> None:
        """Event to pass on to handlers..."""
        for x in self.handlers:
            x.before_lob_update(self.current_lob, new_timestamp)

    def message_event(self, timestamp: Timestamp, message: MarketMessage) -> None:
        """Event to pass on to handlers..."""
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
        """Event to pass on to handlers..."""
        for x in self.handlers:
            x.enter_quote_event(self, timestamp, price, volume, order_id, order_type)

    def cancel_quote_event(
        self,
        timestamp: Timestamp,
        volume: Volume,
        order_id: OrderID,
        order_type: OrderType | None = None,
    ) -> None:
        """Event to pass on to handlers..."""
        for x in self.handlers:
            x.cancel_quote_event(self, timestamp, volume, order_id, order_type)

    def delete_quote_event(
        self,
        timestamp: Timestamp,
        order_id: OrderID,
        order_type: OrderType | None = None,
    ) -> None:
        """Event to pass on to handlers..."""
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
        """Event to pass on to handlers..."""
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
        """Event to pass on to handlers..."""
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
        """Event to pass on to handlers..."""
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
        """Event to pass on to handlers..."""
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
        """Event to pass on to handlers..."""
        for x in self.handlers:
            x.crossing_trade_event(self, timestamp, volume, price, bid_id, ask_id)

    def pre_lob_event(self, timestamp: Timestamp, new_snapshot: bool = True) -> None:
        """Prepare the lob for a new event

        If no current LOB, create one. Otherwise only create a new one if
        requested.
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
