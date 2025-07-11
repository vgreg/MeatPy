"""Market event handler framework.

This module provides the MarketEventHandler base class that defines the interface
for handling various market events during processing.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .lob import LimitOrderBook, OrderType
from .message_reader import MarketMessage
from .timestamp import Timestamp
from .types import OrderID, Price, TradeRef, Volume

if TYPE_CHECKING:
    from .market_processor import MarketProcessor


class MarketEventHandler:
    """A handler for market events.

    The handler gets triggered whenever there is a market event and
    handles the event accordingly. This is a base class that provides
    empty implementations for all event methods. Subclasses should
    override the methods they want to handle.
    """

    def before_lob_update(
        self, lob: LimitOrderBook | None, new_timestamp: Timestamp
    ) -> None:
        """Handle event before a limit order book update.

        This method is called before the LOB is updated with a new timestamp.

        Args:
            lob: The current limit order book, or None if not available
            new_timestamp: The new timestamp for the upcoming update
        """
        pass

    def message_event(
        self,
        market_processor: MarketProcessor,
        timestamp: Timestamp,
        message: MarketMessage,
    ) -> None:
        """Handle a raw market message event.

        Args:
            market_processor: The market processor that received the message
            timestamp: The timestamp of the message
            message: The parsed market message
        """
        pass

    def enter_quote_event(
        self,
        market_processor: MarketProcessor,
        timestamp: Timestamp,
        price: Price,
        volume: Volume,
        order_id: OrderID,
        order_type: OrderType | None = None,
    ) -> None:
        """Handle a quote entry event.

        Args:
            market_processor: The market processor that processed the event
            timestamp: The timestamp of the event
            price: The price of the quote
            volume: The volume of the quote
            order_id: The unique identifier for the order
            order_type: The type of order (bid/ask), if known
        """
        pass

    def cancel_quote_event(
        self,
        market_processor: MarketProcessor,
        timestamp: Timestamp,
        volume: Volume,
        order_id: OrderID,
        order_type: OrderType | None = None,
    ) -> None:
        """Handle a quote cancellation event.

        Args:
            market_processor: The market processor that processed the event
            timestamp: The timestamp of the event
            volume: The volume being cancelled
            order_id: The unique identifier for the order
            order_type: The type of order (bid/ask), if known
        """
        pass

    def delete_quote_event(
        self,
        market_processor: MarketProcessor,
        timestamp: Timestamp,
        order_id: OrderID,
        order_type: OrderType | None = None,
    ) -> None:
        """Handle a quote deletion event.

        Args:
            market_processor: The market processor that processed the event
            timestamp: The timestamp of the event
            order_id: The unique identifier for the order being deleted
            order_type: The type of order (bid/ask), if known
        """
        pass

    def replace_quote_event(
        self,
        market_processor: MarketProcessor,
        timestamp: Timestamp,
        orig_order_id: OrderID,
        new_order_id: OrderID,
        price: Price,
        volume: Volume,
        order_type: OrderType | None = None,
    ) -> None:
        """Handle a quote replacement event.

        Args:
            market_processor: The market processor that processed the event
            timestamp: The timestamp of the event
            orig_order_id: The original order identifier
            new_order_id: The new order identifier
            price: The new price of the quote
            volume: The new volume of the quote
            order_type: The type of order (bid/ask), if known
        """
        pass

    def execute_trade_event(
        self,
        market_processor: MarketProcessor,
        timestamp: Timestamp,
        volume: Volume,
        order_id: OrderID,
        trade_ref: TradeRef,
        order_type: OrderType | None = None,
    ) -> None:
        """Handle a trade execution event.

        Args:
            market_processor: The market processor that processed the event
            timestamp: The timestamp of the event
            volume: The volume traded
            order_id: The unique identifier for the order
            trade_ref: The trade reference identifier
            order_type: The type of order (bid/ask), if known
        """
        pass

    def execute_trade_price_event(
        self,
        market_processor: MarketProcessor,
        timestamp: Timestamp,
        volume: Volume,
        order_id: OrderID,
        trade_ref: TradeRef,
        price: Price,
        order_type: OrderType | None = None,
    ) -> None:
        """Handle a trade execution event with price information.

        Args:
            market_processor: The market processor that processed the event
            timestamp: The timestamp of the event
            volume: The volume traded
            order_id: The unique identifier for the order
            trade_ref: The trade reference identifier
            price: The execution price
            order_type: The type of order (bid/ask), if known
        """
        pass

    def auction_trade_event(
        self,
        market_processor: MarketProcessor,
        timestamp: Timestamp,
        volume: Volume,
        price: Price,
        bid_id: OrderID,
        ask_id: OrderID,
    ) -> None:
        """Handle an auction trade event.

        Args:
            market_processor: The market processor that processed the event
            timestamp: The timestamp of the event
            volume: The volume traded
            price: The auction price
            bid_id: The bid order identifier
            ask_id: The ask order identifier
        """
        pass

    def crossing_trade_event(
        self,
        market_processor: MarketProcessor,
        timestamp: Timestamp,
        volume: Volume,
        price: Price,
        bid_id: OrderID,
        ask_id: OrderID,
    ) -> None:
        """Handle a crossing trade event.

        Args:
            market_processor: The market processor that processed the event
            timestamp: The timestamp of the event
            volume: The volume traded
            price: The crossing price
            bid_id: The bid order identifier
            ask_id: The ask order identifier
        """
        pass
