"""IEX DEEP market processor for price level-based order book reconstruction.

This module provides the IEXDEEPMarketProcessor class, which processes IEX DEEP
market messages to reconstruct the limit order book based on price level updates.

Unlike ITCH 5.0 which provides individual orders, IEX DEEP provides aggregated
price level updates, so the processor works with price levels directly.
"""

from __future__ import annotations

import datetime
from typing import Optional

from ..lob import LimitOrderBook, OrderType
from ..market_processor import MarketProcessor
from ..message_reader import MarketMessage
from ..timestamp import Timestamp
from ..trading_status import (
    HaltedTradingStatus,
    PostTradeTradingStatus,
    PreTradeTradingStatus,
    TradeTradingStatus,
)
from ..types import Price, TradeRef, Volume
from .iex_deep_market_message import (
    AuctionInformationMessage,
    IEXDEEPMarketMessage,
    OperationalHaltStatusMessage,
    OfficialPriceMessage,
    PriceLevelUpdateBuySideMessage,
    PriceLevelUpdateSellSideMessage,
    SecurityDirectoryMessage,
    SecurityEventMessage,
    ShortSalePriceTestStatusMessage,
    SystemEventMessage,
    TradeBreakMessage,
    TradeReportMessage,
    TradingStatusMessage,
)


class InvalidMessageTypeError(Exception):
    """Exception raised when an invalid message type is encountered."""

    pass


class IEXDEEPMarketProcessor(MarketProcessor[int, int, int, int, dict[str, str]]):
    """A market processor for IEX DEEP format.

    This processor handles IEX DEEP market messages and reconstructs the limit
    order book based on price level updates. Unlike ITCH 5.0, IEX DEEP provides
    aggregated price levels directly rather than individual orders.

    Attributes:
        system_status: Current system event status
        trading_status_code: Current trading status code for the instrument
        operational_halt_status: Current operational halt status
        short_sale_status: Current short sale price test status
    """

    def __init__(
        self,
        instrument: str | bytes,
        book_date: Optional[datetime.datetime] = None,
        track_lob: bool = False,
    ) -> None:
        """Initialize the IEXDEEPMarketProcessor.

        Args:
            instrument: The instrument/symbol to process (8 chars, space-padded)
            book_date: The trading date for this processor (optional for IEX DEEP
                       since timestamps are absolute)
            track_lob: Whether to track the full LOB (default False for IEX DEEP
                       since it uses price-level data, not individual orders)
        """
        # book_date is optional for IEX DEEP since timestamps are POSIX epoch
        if book_date is None:
            book_date = datetime.datetime.now(datetime.timezone.utc)

        super(IEXDEEPMarketProcessor, self).__init__(instrument, book_date)
        # IEX DEEP doesn't use order-level LOB tracking by default
        self.track_lob = track_lob

        # Override instrument to store as bytes with proper formatting
        self.instrument: bytes = (
            f"{instrument:<8}".encode("ascii")
            if isinstance(instrument, str)
            else instrument
        )
        self.book_date: datetime.datetime = book_date
        self.system_status: bytes = b""
        self.trading_status_code: bytes = b""
        self.operational_halt_status: bytes = b""
        self.short_sale_status: int = 0

        self._trade_ids: set[int] = set()
        # Track price levels: {price: size}
        self._bid_levels: dict[int, int] = {}
        self._ask_levels: dict[int, int] = {}

    def adjust_timestamp(self, raw_timestamp: int) -> Timestamp:
        """Convert raw timestamp to a Timestamp object.

        IEX DEEP timestamps are nanoseconds since POSIX epoch UTC.

        Args:
            raw_timestamp: The raw timestamp in nanoseconds since POSIX epoch

        Returns:
            A Timestamp object representing the adjusted time
        """
        # Convert nanoseconds since POSIX epoch to datetime
        seconds = raw_timestamp // 1_000_000_000
        nanoseconds = raw_timestamp % 1_000_000_000
        dt = datetime.datetime.fromtimestamp(seconds, tz=datetime.timezone.utc)
        dt = dt.replace(microsecond=nanoseconds // 1000)
        return Timestamp.from_datetime(dt)

    def process_message(
        self, message: MarketMessage, new_snapshot: bool = True
    ) -> None:
        """Process an IEX DEEP market message.

        Args:
            message: The market message to process
            new_snapshot: Whether to create a new LOB snapshot
        """
        if not isinstance(message, IEXDEEPMarketMessage):
            raise InvalidMessageTypeError(
                f"Message is not an IEXDEEPMarketMessage: {type(message)}"
            )

        timestamp = self.adjust_timestamp(message.timestamp)
        self.message_event(timestamp, message)

        if isinstance(message, SystemEventMessage):
            self.process_system_message(message, timestamp, new_snapshot)

        elif isinstance(message, SecurityDirectoryMessage):
            # Security directory - only process for our instrument
            if message.symbol != self.instrument:
                return
            # Store security info if needed
            pass

        elif isinstance(message, TradingStatusMessage):
            if message.symbol != self.instrument:
                return
            self.process_trading_status_message(message, timestamp, new_snapshot)

        elif isinstance(message, OperationalHaltStatusMessage):
            if message.symbol != self.instrument:
                return
            self.process_operational_halt_message(message, timestamp, new_snapshot)

        elif isinstance(message, ShortSalePriceTestStatusMessage):
            if message.symbol != self.instrument:
                return
            self.short_sale_status = message.short_sale_price_test_status

        elif isinstance(message, SecurityEventMessage):
            if message.symbol != self.instrument:
                return
            # Security events (opening/closing complete) - can trigger status updates
            pass

        elif isinstance(message, PriceLevelUpdateBuySideMessage):
            if message.symbol != self.instrument:
                return
            self.update_price_level(
                timestamp=timestamp,
                price=message.price,
                size=message.size,
                side=OrderType.BID,
            )

        elif isinstance(message, PriceLevelUpdateSellSideMessage):
            if message.symbol != self.instrument:
                return
            self.update_price_level(
                timestamp=timestamp,
                price=message.price,
                size=message.size,
                side=OrderType.ASK,
            )

        elif isinstance(message, TradeReportMessage):
            if message.symbol != self.instrument:
                return
            self._trade_ids.add(message.trade_id)
            self.trade_event(
                timestamp=timestamp,
                price=message.price,
                volume=message.size,
                trade_ref=message.trade_id,
            )

        elif isinstance(message, TradeBreakMessage):
            if message.symbol != self.instrument:
                return
            # Trade break - remove from trade set if present
            self._trade_ids.discard(message.trade_id)
            self.trade_break_event(
                timestamp=timestamp,
                price=message.price,
                volume=message.size,
                trade_ref=message.trade_id,
            )

        elif isinstance(message, OfficialPriceMessage):
            if message.symbol != self.instrument:
                return
            self.official_price_event(
                timestamp=timestamp,
                price_type=message.price_type,
                price=message.official_price,
            )

        elif isinstance(message, AuctionInformationMessage):
            if message.symbol != self.instrument:
                return
            self.auction_event(timestamp=timestamp, message=message)

    def process_system_message(
        self,
        message: SystemEventMessage,
        timestamp: Timestamp,
        new_snapshot: bool = True,
    ) -> None:
        """Process a system event message.

        Args:
            message: The system event message
            timestamp: The timestamp of the event
            new_snapshot: Whether to create a new LOB snapshot
        """
        self.system_status = message.system_event
        self.update_trading_status()

    def process_trading_status_message(
        self,
        message: TradingStatusMessage,
        timestamp: Timestamp,
        new_snapshot: bool = True,
    ) -> None:
        """Process a trading status message.

        Args:
            message: The trading status message
            timestamp: The timestamp of the event
            new_snapshot: Whether to create a new LOB snapshot
        """
        self.trading_status_code = message.trading_status
        self.update_trading_status()

    def process_operational_halt_message(
        self,
        message: OperationalHaltStatusMessage,
        timestamp: Timestamp,
        new_snapshot: bool = True,
    ) -> None:
        """Process an operational halt status message.

        Args:
            message: The operational halt status message
            timestamp: The timestamp of the event
            new_snapshot: Whether to create a new LOB snapshot
        """
        self.operational_halt_status = message.operational_halt_status
        self.update_trading_status()

    def update_trading_status(self) -> None:
        """Update the current trading status based on system and trading status."""
        # Check for operational halt first
        if self.operational_halt_status == b"O":
            self.trading_status = HaltedTradingStatus()
            return

        # Check trading status
        if self.trading_status_code == b"H":
            self.trading_status = HaltedTradingStatus()
        elif self.trading_status_code == b"P":
            # Trading paused - treat as halted
            self.trading_status = HaltedTradingStatus()
        elif self.trading_status_code == b"O":
            # Order acceptance period - pre-trade
            self.trading_status = PreTradeTradingStatus()
        elif self.trading_status_code == b"T":
            self.trading_status = TradeTradingStatus()
        elif self.system_status in (b"O", b"S"):
            # Start of messages or start of system hours
            self.trading_status = PreTradeTradingStatus()
        elif self.system_status in (b"M", b"E", b"C"):
            # End of regular market hours, end of system hours, end of messages
            self.trading_status = PostTradeTradingStatus()
        elif self.system_status == b"R":
            # Start of regular market hours
            self.trading_status = TradeTradingStatus()

    def update_price_level(
        self,
        timestamp: Timestamp,
        price: Price,
        size: Volume,
        side: OrderType,
    ) -> None:
        """Update a price level in the order book.

        For IEX DEEP, we receive the new total size at each price level.
        A size of 0 means the price level should be removed.

        Args:
            timestamp: The timestamp of the update
            price: The price level
            size: The new total size at this price level
            side: BID or ASK
        """
        # Update internal tracking
        if side == OrderType.BID:
            if size == 0:
                self._bid_levels.pop(price, None)
            else:
                self._bid_levels[price] = size
        else:
            if size == 0:
                self._ask_levels.pop(price, None)
            else:
                self._ask_levels[price] = size

        # Fire event for handlers
        self.price_level_update_event(timestamp, price, size, side)

    def trade_event(
        self,
        timestamp: Timestamp,
        price: Price,
        volume: Volume,
        trade_ref: TradeRef,
    ) -> None:
        """Record a trade event.

        Args:
            timestamp: The timestamp of the trade
            price: The trade price
            volume: The trade volume
            trade_ref: The trade reference ID
        """
        # Fire trade event to handlers
        for handler in self.handlers:
            if hasattr(handler, "on_trade"):
                handler.on_trade(timestamp, price, volume, trade_ref)

    def trade_break_event(
        self,
        timestamp: Timestamp,
        price: Price,
        volume: Volume,
        trade_ref: TradeRef,
    ) -> None:
        """Record a trade break event.

        Args:
            timestamp: The timestamp of the trade break
            price: The trade price
            volume: The trade volume
            trade_ref: The trade reference ID
        """
        # Fire trade break event to handlers
        for handler in self.handlers:
            if hasattr(handler, "on_trade_break"):
                handler.on_trade_break(timestamp, price, volume, trade_ref)

    def official_price_event(
        self,
        timestamp: Timestamp,
        price_type: bytes,
        price: Price,
    ) -> None:
        """Record an official price event.

        Args:
            timestamp: The timestamp of the official price
            price_type: 'Q' for opening, 'M' for closing
            price: The official price
        """
        # Fire official price event to handlers
        for handler in self.handlers:
            if hasattr(handler, "on_official_price"):
                handler.on_official_price(timestamp, price_type, price)

    def auction_event(
        self,
        timestamp: Timestamp,
        message: AuctionInformationMessage,
    ) -> None:
        """Record an auction information event.

        Args:
            timestamp: The timestamp of the auction info
            message: The auction information message
        """
        # Fire auction event to handlers
        for handler in self.handlers:
            if hasattr(handler, "on_auction"):
                handler.on_auction(timestamp, message)

    def price_level_update_event(
        self,
        timestamp: Timestamp,
        price: Price,
        size: Volume,
        side: OrderType,
    ) -> None:
        """Fire a price level update event to handlers.

        Args:
            timestamp: The timestamp of the update
            price: The price level
            size: The new size at this level
            side: BID or ASK
        """
        for handler in self.handlers:
            if hasattr(handler, "on_price_level_update"):
                handler.on_price_level_update(timestamp, price, size, side)

    def create_lob(self, timestamp: Timestamp) -> None:
        """Create a new limit order book.

        Args:
            timestamp: The timestamp for the new limit order book
        """
        super().create_lob(timestamp)
        if isinstance(self.current_lob, LimitOrderBook):
            # IEX DEEP prices have 4 decimal places (divide by 10000)
            self.current_lob.decimals_adj = 10000
        else:
            raise RuntimeError(
                "IEXDEEPMarketProcessor:create_lob",
                "Post-creation LOB is not a LimitOrderBook instance.",
            )

    def get_best_bid(self) -> tuple[Price, Volume] | None:
        """Get the best bid price and size.

        Returns:
            Tuple of (price, size) or None if no bids
        """
        if not self._bid_levels:
            return None
        best_price = max(self._bid_levels.keys())
        return (best_price, self._bid_levels[best_price])

    def get_best_ask(self) -> tuple[Price, Volume] | None:
        """Get the best ask price and size.

        Returns:
            Tuple of (price, size) or None if no asks
        """
        if not self._ask_levels:
            return None
        best_price = min(self._ask_levels.keys())
        return (best_price, self._ask_levels[best_price])

    def get_bbo(
        self,
    ) -> tuple[tuple[Price, Volume] | None, tuple[Price, Volume] | None]:
        """Get the best bid and offer.

        Returns:
            Tuple of (best_bid, best_ask) where each is (price, size) or None
        """
        return (self.get_best_bid(), self.get_best_ask())
