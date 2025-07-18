"""ITCH 4.1 top of book message recorder for limit order books.

This module provides the ITCH41TopOfBookMessageRecorder class, which records
messages that affect the top of the book (best bid/ask) from ITCH 4.1 market data.
"""

from typing import Any

from ..market_event_handler import MarketEventHandler
from .itch41_market_message import (
    AddOrderMessage,
    AddOrderMPIDMessage,
    OrderCancelMessage,
    OrderDeleteMessage,
    OrderExecutedMessage,
    OrderExecutedPriceMessage,
    OrderReplaceMessage,
    TradeMessage,
)


class ITCH41TopOfBookMessageRecorder(MarketEventHandler):
    """Records messages that affect the top of the book from ITCH 4.1 market data.

    This recorder detects and records messages that impact the best bid or ask
    prices, including order additions, executions, and hidden trades.

    Attributes:
        records: List of recorded top of book message records
    """

    def __init__(self) -> None:
        """Initialize the ITCH41TopOfBookMessageRecorder."""
        self.records: list[Any] = []

    def message_event(self, market_processor, timestamp, message) -> None:
        """Detect messages that affect the top of the book and record them.

        Args:
            market_processor: The market processor instance
            timestamp: The timestamp of the message
            message: The market message to process
        """
        lob = market_processor.lob
        if isinstance(message, AddOrderMessage) or isinstance(
            message, AddOrderMPIDMessage
        ):
            # Detect if top of book is affected; if so record the message
            if message.side == b"B":
                if (
                    lob is None
                    or 0 == len(lob.bid_levels)
                    or message.price >= lob.bid_levels[0].price
                ):
                    record = {
                        "MessageType": "Add",
                        "Queue": "Bid",
                        "Price": message.price,
                        "Volume": message.shares,
                        "OrderID": message.order_ref,
                    }
                    self.records.append((timestamp, record))
            elif message.side == b"S":
                if (
                    lob is None
                    or 0 == len(lob.ask_levels)
                    or message.price <= lob.ask_levels[0].price
                ):
                    record = {
                        "MessageType": "Add",
                        "Queue": "Ask",
                        "Price": message.price,
                        "Volume": message.shares,
                        "OrderID": message.order_ref,
                    }
                    self.records.append((timestamp, record))
        elif isinstance(message, OrderExecutedMessage):
            # An executed order will ALWAYS be against top of book
            # because of price priority, so record.
            if lob and lob.ask_order_on_book(message.order_ref):
                record = {
                    "MessageType": "Exec",
                    "Volume": message.shares,
                    "OrderID": message.order_ref,
                }
                record["Queue"] = "Ask"
                record["Price"] = lob.ask_levels[0].price
                self.records.append((timestamp, record))
            elif lob and lob.bid_order_on_book(message.order_ref):
                record = {
                    "MessageType": "Exec",
                    "Volume": message.shares,
                    "OrderID": message.order_ref,
                }
                record["Queue"] = "Bid"
                record["Price"] = lob.bid_levels[0].price
                self.records.append((timestamp, record))
        elif isinstance(message, TradeMessage):
            if message.side == b"S":
                record = {
                    "MessageType": "ExecHid",
                    "Volume": message.shares,
                    "OrderID": "",
                }
                record["Queue"] = "Ask"
                record["Price"] = message.price
                self.records.append((timestamp, record))
            elif message.side == b"B":
                record = {
                    "MessageType": "ExecHid",
                    "Volume": message.shares,
                    "OrderID": "",
                }
                record["Queue"] = "Bid"
                record["Price"] = message.price
                self.records.append((timestamp, record))
        elif isinstance(message, OrderExecutedPriceMessage):
            if (
                lob
                and len(lob.ask_levels) > 0
                and lob.ask_levels[0].order_on_book(message.order_ref)
            ):
                record = {
                    "MessageType": "ExecPrice",
                    "Queue": "Ask",
                    "Volume": message.shares,
                    "OrderID": message.order_ref,
                    "Price": message.price,
                }
                self.records.append((timestamp, record))
            elif (
                lob
                and len(lob.bid_levels) > 0
                and lob.bid_levels[0].order_on_book(message.order_ref)
            ):
                record = {
                    "MessageType": "ExecPrice",
                    "Queue": "Bid",
                    "Volume": message.shares,
                    "OrderID": message.order_ref,
                    "Price": message.price,
                }
                self.records.append((timestamp, record))
        elif isinstance(message, OrderCancelMessage):
            # Order cancel will only affect top of book if at top of book
            if lob and lob.ask_order_on_book(message.order_ref):
                record = {
                    "MessageType": "Cancel",
                    "Queue": "Ask",
                    "Volume": message.shares,
                    "OrderID": message.order_ref,
                    "Price": lob.ask_levels[0].price,
                }
                self.records.append((timestamp, record))
            elif lob and lob.bid_order_on_book(message.order_ref):
                record = {
                    "MessageType": "Cancel",
                    "Queue": "Bid",
                    "Volume": message.shares,
                    "OrderID": message.order_ref,
                    "Price": lob.bid_levels[0].price,
                }
                self.records.append((timestamp, record))
        elif isinstance(message, OrderDeleteMessage):
            # Order delete will only affect top of book if at top of book
            if lob and lob.ask_order_on_book(message.order_ref):
                record = {
                    "MessageType": "Delete",
                    "Queue": "Ask",
                    "Volume": 0,  # Unknown volume for delete
                    "OrderID": message.order_ref,
                    "Price": lob.ask_levels[0].price,
                }
                self.records.append((timestamp, record))
            elif lob and lob.bid_order_on_book(message.order_ref):
                record = {
                    "MessageType": "Delete",
                    "Queue": "Bid",
                    "Volume": 0,  # Unknown volume for delete
                    "OrderID": message.order_ref,
                    "Price": lob.bid_levels[0].price,
                }
                self.records.append((timestamp, record))
        elif isinstance(message, OrderReplaceMessage):
            # Order replace affects top of book only if original order is at top
            if lob and lob.ask_order_on_book(message.original_ref):
                record = {
                    "MessageType": "Replace",
                    "Queue": "Ask",
                    "Volume": message.shares,
                    "OrderID": message.new_ref,
                    "Price": message.price,
                }
                self.records.append((timestamp, record))
            elif lob and lob.bid_order_on_book(message.original_ref):
                record = {
                    "MessageType": "Replace",
                    "Queue": "Bid",
                    "Volume": message.shares,
                    "OrderID": message.new_ref,
                    "Price": message.price,
                }
                self.records.append((timestamp, record))
