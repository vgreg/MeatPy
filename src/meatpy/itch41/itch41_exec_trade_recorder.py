"""ITCH 4.1 execution trade recorder for limit order books.

This module provides the ITCH41ExecTradeRecorder class, which records trade
executions from ITCH 4.1 market data and exports them to CSV files.
"""

from typing import Any

from ..market_event_handler import MarketEventHandler
from .itch41_market_message import (
    OrderExecutedMessage,
    OrderExecutedPriceMessage,
    TradeMessage,
)


class ITCH41ExecTradeRecorder(MarketEventHandler):
    """Records trade executions from ITCH 4.1 market data.

    This recorder detects and records trade executions, including both
    visible and hidden trades, and exports them to CSV format.

    Attributes:
        records: List of recorded trade execution records
    """

    def __init__(self) -> None:
        """Initialize the ITCH41ExecTradeRecorder."""
        self.records: list[Any] = []

    def message_event(
        self,
        market_processor,
        timestamp,
        message,
    ) -> None:
        """Detect messages that represent trade executions and record them.

        Args:
            market_processor: The market processor instance
            timestamp: The timestamp of the message
            message: The market message to process
        """
        lob = market_processor.lob
        if lob is None:
            return

        if isinstance(message, OrderExecutedMessage):
            # An executed order will ALWAYS be against top of book
            # because of price priority, so record.
            if lob.ask_order_on_book(message.order_ref):
                record = {
                    "MessageType": "Exec",
                    "Volume": message.shares,
                    "OrderID": message.order_ref,
                }
                record["Queue"] = "Ask"
                record["Price"] = lob.ask_levels[0].price
                try:
                    (queue, i, j) = lob.find_order(message.order_ref)
                    record["OrderTimestamp"] = queue[i].queue[j].timestamp
                except Exception:
                    record["OrderTimestamp"] = ""
                self.records.append((timestamp, record))
            elif lob.bid_order_on_book(message.order_ref):
                record = {
                    "MessageType": "Exec",
                    "Volume": message.shares,
                    "OrderID": message.order_ref,
                }
                record["Queue"] = "Bid"
                record["Price"] = lob.bid_levels[0].price
                try:
                    (queue, i, j) = lob.find_order(message.order_ref)
                    record["OrderTimestamp"] = queue[i].queue[j].timestamp
                except Exception:
                    record["OrderTimestamp"] = ""
                self.records.append((timestamp, record))
        elif isinstance(message, TradeMessage):
            if message.side == b"S":
                record = {
                    "MessageType": "ExecHid",
                    "Volume": message.shares,
                    "OrderID": "",
                    "OrderTimestamp": "",
                }
                record["Queue"] = "Ask"
                record["Price"] = message.price
                self.records.append((timestamp, record))
            elif message.side == b"B":
                record = {
                    "MessageType": "ExecHid",
                    "Volume": message.shares,
                    "OrderID": "",
                    "OrderTimestamp": "",
                }
                record["Queue"] = "Bid"
                record["Price"] = message.price
                self.records.append((timestamp, record))
        elif isinstance(message, OrderExecutedPriceMessage):
            if len(lob.ask_levels) > 0 and lob.ask_levels[0].order_on_book(
                message.order_ref
            ):
                record = {
                    "MessageType": "ExecPrice",
                    "Queue": "Ask",
                    "Volume": message.shares,
                    "OrderID": message.order_ref,
                    "Price": message.price,
                }
                try:
                    (queue, i, j) = lob.find_order(message.order_ref)
                    record["OrderTimestamp"] = queue[i].queue[j].timestamp
                except Exception:
                    record["OrderTimestamp"] = ""
                self.records.append((timestamp, record))
            elif len(lob.bid_levels) > 0 and lob.bid_levels[0].order_on_book(
                message.order_ref
            ):
                record = {
                    "MessageType": "ExecPrice",
                    "Queue": "Bid",
                    "Volume": message.shares,
                    "OrderID": message.order_ref,
                    "Price": message.price,
                }
                try:
                    (queue, i, j) = lob.find_order(message.order_ref)
                    record["OrderTimestamp"] = queue[i].queue[j].timestamp
                except Exception:
                    record["OrderTimestamp"] = ""
                self.records.append((timestamp, record))
