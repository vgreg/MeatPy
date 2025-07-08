"""ITCH 5.0 market processor for limit order book reconstruction.

This module provides the ITCH50MarketProcessor class, which processes ITCH 5.0
market messages to reconstruct the limit order book and handle trading status updates.
"""

import datetime

from ..lob import OrderType
from ..market_processor import MarketProcessor
from ..message_parser import MarketMessage
from ..timestamp import Timestamp
from ..trading_status import (
    HaltedTradingStatus,
    PostTradeTradingStatus,
    PreTradeTradingStatus,
    QuoteOnlyTradingStatus,
    TradeTradingStatus,
)
from ..types import OrderID, Price, TradeRef, Volume
from .itch50_market_message import (
    AddOrderMessage,
    AddOrderMPIDMessage,
    ITCH50MarketMessage,
    OrderCancelMessage,
    OrderDeleteMessage,
    OrderExecutedMessage,
    OrderExecutedPriceMessage,
    OrderReplaceMessage,
    StockTradingActionMessage,
    SystemEventMessage,
)


class ITCH50MarketProcessor(MarketProcessor[int, int, int, int, dict[str, str]]):
    """A market processor for ITCH 5.0 format.

    This processor handles ITCH 5.0 market messages and reconstructs the limit
    order book. It processes order additions, executions, cancellations, and
    trading status updates.

    Attributes:
        system_status: Current system status code
        stock_status: Current stock trading status code
        emc_status: Current EMC status code
    """

    def __init__(
        self, instrument: str | bytes, book_date: datetime.date | datetime.datetime
    ) -> None:
        """Initialize the ITCH50MarketProcessor.

        Args:
            instrument: The instrument/symbol to process
            book_date: The trading date for this processor
        """
        super(ITCH50MarketProcessor, self).__init__(instrument, book_date)
        self.system_status: bytes = b""
        self.stock_status: bytes = b""
        self.emc_status: bytes = b""

    def process_message(
        self, message: MarketMessage, new_snapshot: bool = True
    ) -> None:
        """Process an ITCH 5.0 market message.

        Args:
            message: The market message to process
            new_snapshot: Whether to create a new LOB snapshot
        """
        if not isinstance(message, ITCH50MarketMessage):
            raise ValueError(
                "ITCH50MarketProcessor:process_message",
                f"Message is not an ITCH50MarketMessage: {type(message)}",
            )
        timestamp = message.timestamp
        self.message_event(timestamp, message)
        if isinstance(message, AddOrderMessage) or isinstance(
            message, AddOrderMPIDMessage
        ):
            if self.track_lob:
                if message.bsindicator == b"B":
                    order_type = OrderType.BID
                elif message.bsindicator == b"S":
                    order_type = OrderType.ASK
                else:
                    raise Exception(
                        "ITCH50MarketProcessor:process_message",
                        f"Wrong value for bsindicator: {message.bsindicator}",
                    )
                self.pre_lob_event(timestamp)
                self.enter_quote(
                    timestamp=timestamp,
                    price=message.price,
                    volume=message.shares,
                    order_id=message.orderRefNum,
                    order_type=order_type,
                )
        elif isinstance(message, OrderExecutedMessage):
            if self.track_lob:
                self.pre_lob_event(timestamp)
                self.execute_trade(
                    timestamp=timestamp,
                    volume=message.shares,
                    order_id=message.orderRefNum,
                    trade_ref=message.match,
                )
        elif isinstance(message, OrderExecutedPriceMessage):
            if self.track_lob:
                self.pre_lob_event(timestamp)
                self.execute_trade_price(
                    timestamp=timestamp,
                    volume=message.shares,
                    order_id=message.orderRefNum,
                    trade_ref=message.match,
                    price=message.price,
                )
        elif isinstance(message, OrderCancelMessage):
            if self.track_lob:
                self.pre_lob_event(timestamp)
                if self.current_lob is None:
                    raise Exception(
                        "ITCH50MarketProcessor:process_message",
                        "Cancelling order without LOB.",
                    )
                if self.current_lob.ask_order_on_book(message.orderRefNum):
                    order_type = OrderType.ASK
                elif self.current_lob.bid_order_on_book(message.orderRefNum):
                    order_type = OrderType.BID
                else:
                    raise Exception(
                        "ITCH50MarketProcessor:process_message",
                        "Cancelling missing order.",
                    )
                self.cancel_quote(
                    timestamp=timestamp,
                    volume=message.cancelShares,
                    order_id=message.orderRefNum,
                    order_type=order_type,
                )
        elif isinstance(message, OrderDeleteMessage):
            if self.track_lob:
                self.pre_lob_event(timestamp)
                if self.current_lob is None:
                    raise Exception(
                        "ITCH50MarketProcessor:process_message",
                        "Deleting order without LOB.",
                    )
                if self.current_lob.ask_order_on_book(message.orderRefNum):
                    order_type = OrderType.ASK
                elif self.current_lob.bid_order_on_book(message.orderRefNum):
                    order_type = OrderType.BID
                else:
                    raise Exception(
                        "ITCH50MarketProcessor:process_message",
                        "Deleting missing order.",
                    )
                self.delete_quote(
                    timestamp=timestamp,
                    order_id=message.orderRefNum,
                    order_type=order_type,
                )
        elif isinstance(message, OrderReplaceMessage):
            if self.track_lob:
                self.pre_lob_event(timestamp)
                if self.current_lob is None:
                    raise Exception(
                        "ITCH50MarketProcessor:process_message",
                        "Replacing order without LOB.",
                    )
                if self.current_lob.ask_order_on_book(message.origOrderRefNum):
                    order_type = OrderType.ASK
                elif self.current_lob.bid_order_on_book(message.origOrderRefNum):
                    order_type = OrderType.BID
                else:
                    raise Exception(
                        "ITCH50MarketProcessor:process_message",
                        "Replacing missing order.",
                    )
                self.replace_quote(
                    timestamp=timestamp,
                    orig_order_id=message.origOrderRefNum,
                    new_order_id=message.newOrderRefNum,
                    price=message.price,
                    volume=message.shares,
                    order_type=order_type,
                )
        elif isinstance(message, SystemEventMessage):
            self.process_system_message(message.code, timestamp, new_snapshot)
        elif isinstance(message, StockTradingActionMessage):
            self.process_trading_action_message(message.state, timestamp, new_snapshot)

    def process_system_message(
        self, code: bytes, timestamp: Timestamp, new_snapshot: bool = True
    ) -> None:
        """Process a system event message.

        Args:
            code: The system event code
            timestamp: The timestamp of the event
            new_snapshot: Whether to create a new LOB snapshot
        """
        if code in b"OSQMEC":
            self.system_status = code
        elif code in b"ARB":
            self.emc_status = code
        else:
            raise Exception(
                "ITCH50MarketProcessor:process_system_message",
                f"Unknown system message: {code}",
            )
        self.update_trading_status()

    def process_trading_action_message(
        self, state: bytes, timestamp: Timestamp, new_snapshot: bool = True
    ) -> None:
        """Process a stock trading action message.

        Args:
            state: The trading state code
            timestamp: The timestamp of the event
            new_snapshot: Whether to create a new LOB snapshot
        """
        if state in b"HPQT":
            self.stock_status = state
        else:
            raise Exception(
                "ITCH50MarketProcessor:process_trading_action_message",
                f"Unknown trading state: {state}",
            )
        self.update_trading_status()

    def update_trading_status(self) -> None:
        """Update the current trading status based on system and stock status."""
        if self.emc_status == b"A" or self.stock_status in b"HP":
            self.trading_status = HaltedTradingStatus()
        elif self.emc_status == b"R" or self.stock_status == b"Q":
            self.trading_status = QuoteOnlyTradingStatus()
        elif self.system_status in b"OS":
            self.trading_status = PreTradeTradingStatus()
        elif self.system_status in b"MEC":
            self.trading_status = PostTradeTradingStatus()
        elif self.system_status == b"Q" and self.stock_status == b"T":
            self.trading_status = TradeTradingStatus()
        else:
            raise Exception(
                "ITCH50MarketProcessor:update_trading_status",
                f"Could not determine trading status: {self.system_status}/{self.emc_status}/{self.stock_status}",
            )

    def enter_quote(
        self,
        timestamp: Timestamp,
        price: Price,
        volume: Volume,
        order_id: OrderID,
        order_type: OrderType | None = None,
    ) -> None:
        """Enter a new quote into the limit order book.

        Args:
            timestamp: The timestamp of the quote
            price: The price of the quote
            volume: The volume of the quote
            order_id: The order identifier
            order_type: The type of order (bid/ask)
        """
        self.enter_quote_event(timestamp, price, volume, order_id, order_type)
        if self.current_lob is not None:
            self.current_lob.enter_quote(timestamp, volume, order_id)

    def cancel_quote(
        self,
        timestamp: Timestamp,
        volume: Volume,
        order_id: OrderID,
        order_type: OrderType | None = None,
    ) -> None:
        """Cancel a portion of an existing quote.

        Args:
            timestamp: The timestamp of the cancellation
            volume: The volume to cancel
            order_id: The order identifier
            order_type: The type of order (bid/ask)
        """
        self.cancel_quote_event(timestamp, volume, order_id, order_type)
        if self.current_lob is not None:
            self.current_lob.cancel_quote(order_id, volume)

    def delete_quote(
        self,
        timestamp: Timestamp,
        order_id: OrderID,
        order_type: OrderType | None = None,
    ) -> None:
        """Delete an entire quote from the limit order book.

        Args:
            timestamp: The timestamp of the deletion
            order_id: The order identifier
            order_type: The type of order (bid/ask)
        """
        self.delete_quote_event(timestamp, order_id, order_type)
        if self.current_lob is not None:
            self.current_lob.delete_quote(order_id)

    def replace_quote(
        self,
        timestamp: Timestamp,
        orig_order_id: OrderID,
        new_order_id: OrderID,
        price: Price,
        volume: Volume,
        order_type: OrderType | None = None,
    ) -> None:
        """Replace an existing quote with a new one.

        Args:
            timestamp: The timestamp of the replacement
            orig_order_id: The original order identifier
            new_order_id: The new order identifier
            price: The new price
            volume: The new volume
            order_type: The type of order (bid/ask)
        """
        self.replace_quote_event(
            timestamp, orig_order_id, new_order_id, price, volume, order_type
        )
        if self.current_lob is not None:
            self.current_lob.delete_quote(orig_order_id)
            self.current_lob.enter_quote(timestamp, volume, new_order_id)

    def execute_trade(
        self,
        timestamp: Timestamp,
        volume: Volume,
        order_id: OrderID,
        trade_ref: TradeRef,
    ) -> None:
        """Execute a trade against the limit order book.

        Args:
            timestamp: The timestamp of the trade
            volume: The volume traded
            order_id: The order identifier
            trade_ref: The trade reference
        """
        self.execute_trade_event(timestamp, volume, order_id, trade_ref)
        if self.current_lob is not None:
            self.current_lob.execute_trade(timestamp, volume, order_id)

    def execute_trade_price(
        self,
        timestamp: Timestamp,
        volume: Volume,
        order_id: OrderID,
        trade_ref: TradeRef,
        price: Price,
    ) -> None:
        """Execute a trade with price information.

        Args:
            timestamp: The timestamp of the trade
            volume: The volume traded
            order_id: The order identifier
            trade_ref: The trade reference
            price: The execution price
        """
        self.execute_trade_price_event(timestamp, volume, order_id, trade_ref, price)
        if self.current_lob is not None:
            self.current_lob.execute_trade_price(timestamp, volume, order_id)
