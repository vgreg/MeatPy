"""Event system for market data processing.

This module provides a protocol-based event system for handling market events
in a type-safe and extensible manner.
"""

from typing import Protocol, runtime_checkable

from .lob import LimitOrderBook, OrderType
from .market_processor import MarketProcessor
from .message_reader import MarketMessage
from .timestamp import Timestamp
from .types import OrderID, Price, TradeRef, Volume


@runtime_checkable
class MarketEventHandler(Protocol):
    """Protocol for market event handlers.

    This protocol defines the interface that all market event handlers
    must implement. Handlers can choose to implement only the events
    they care about.
    """

    def before_lob_update(
        self, lob: LimitOrderBook | None, new_timestamp: Timestamp
    ) -> None:
        """Handle event before a limit order book update."""
        ...

    def message_event(
        self,
        market_processor: MarketProcessor,
        timestamp: Timestamp,
        message: MarketMessage,
    ) -> None:
        """Handle a raw market message event."""
        ...

    def enter_quote_event(
        self,
        market_processor: MarketProcessor,
        timestamp: Timestamp,
        price: Price,
        volume: Volume,
        order_id: OrderID,
        order_type: OrderType | None = None,
    ) -> None:
        """Handle a quote entry event."""
        ...

    def cancel_quote_event(
        self,
        market_processor: MarketProcessor,
        timestamp: Timestamp,
        volume: Volume,
        order_id: OrderID,
        order_type: OrderType | None = None,
    ) -> None:
        """Handle a quote cancellation event."""
        ...

    def delete_quote_event(
        self,
        market_processor: MarketProcessor,
        timestamp: Timestamp,
        order_id: OrderID,
        order_type: OrderType | None = None,
    ) -> None:
        """Handle a quote deletion event."""
        ...

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
        """Handle a quote replacement event."""
        ...

    def execute_trade_event(
        self,
        market_processor: MarketProcessor,
        timestamp: Timestamp,
        volume: Volume,
        order_id: OrderID,
        trade_ref: TradeRef,
        order_type: OrderType | None = None,
    ) -> None:
        """Handle a trade execution event."""
        ...

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
        """Handle a trade execution event with price information."""
        ...

    def auction_trade_event(
        self,
        market_processor: MarketProcessor,
        timestamp: Timestamp,
        volume: Volume,
        price: Price,
        bid_id: OrderID,
        ask_id: OrderID,
    ) -> None:
        """Handle an auction trade event."""
        ...

    def crossing_trade_event(
        self,
        market_processor: MarketProcessor,
        timestamp: Timestamp,
        volume: Volume,
        price: Price,
        bid_id: OrderID,
        ask_id: OrderID,
    ) -> None:
        """Handle a crossing trade event."""
        ...


class BaseEventHandler:
    """Base class for market event handlers with empty implementations.

    This class provides empty implementations for all event methods.
    Subclasses can override only the methods they need to handle.
    """

    def before_lob_update(
        self, lob: LimitOrderBook | None, new_timestamp: Timestamp
    ) -> None:
        """Handle event before a limit order book update."""
        pass

    def message_event(
        self,
        market_processor: MarketProcessor,
        timestamp: Timestamp,
        message: MarketMessage,
    ) -> None:
        """Handle a raw market message event."""
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
        """Handle a quote entry event."""
        pass

    def cancel_quote_event(
        self,
        market_processor: MarketProcessor,
        timestamp: Timestamp,
        volume: Volume,
        order_id: OrderID,
        order_type: OrderType | None = None,
    ) -> None:
        """Handle a quote cancellation event."""
        pass

    def delete_quote_event(
        self,
        market_processor: MarketProcessor,
        timestamp: Timestamp,
        order_id: OrderID,
        order_type: OrderType | None = None,
    ) -> None:
        """Handle a quote deletion event."""
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
        """Handle a quote replacement event."""
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
        """Handle a trade execution event."""
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
        """Handle a trade execution event with price information."""
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
        """Handle an auction trade event."""
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
        """Handle a crossing trade event."""
        pass
