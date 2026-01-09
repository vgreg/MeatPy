"""ITCH 5.0 execution trade recorder for limit order books.

This module provides the ITCH50ExecTradeRecorder class, which records trade
executions from ITCH 5.0 market data and exports them to CSV files.
"""

from typing import Any

from ..market_event_handler import MarketEventHandler
from .itch50_market_message import (
    OrderExecutedMessage,
    OrderExecutedPriceMessage,
    TradeMessage,
)


class ITCH50ExecTradeRecorder(MarketEventHandler):
    """Records trade executions from ITCH 5.0 market data.

    This recorder detects and records trade executions, including both
    visible and hidden trades, and exports them to CSV format.

    Attributes:
        records: List of recorded trade execution records
    """

    def __init__(self) -> None:
        """Initialize the ITCH50ExecTradeRecorder."""
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
        lob = market_processor.current_lob
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
                (queue, i, j) = lob.find_order(message.order_ref)
                record["OrderTimestamp"] = queue[i].queue[j].timestamp
                self.records.append((timestamp, record))
            elif lob.bid_order_on_book(message.order_ref):
                record = {
                    "MessageType": "Exec",
                    "Volume": message.shares,
                    "OrderID": message.order_ref,
                }
                record["Queue"] = "Bid"
                record["Price"] = lob.bid_levels[0].price
                (queue, i, j) = lob.find_order(message.order_ref)
                record["OrderTimestamp"] = queue[i].queue[j].timestamp
                self.records.append((timestamp, record))
        elif isinstance(message, TradeMessage):
            if message.bsindicator == b"S":
                record = {
                    "MessageType": "ExecHid",
                    "Volume": message.shares,
                    "OrderID": "",
                    "OrderTimestamp": "",
                }
                record["Queue"] = "Ask"
                record["Price"] = message.price
                self.records.append((timestamp, record))
            elif message.bsindicator == b"B":
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
                    "Price": message.execution_price,
                }
                (queue, i, j) = lob.find_order(message.order_ref)
                record["OrderTimestamp"] = queue[i].queue[j].timestamp
                self.records.append((timestamp, record))
            elif len(lob.bid_levels) > 0 and lob.bid_levels[0].order_on_book(
                message.order_ref
            ):
                record = {
                    "MessageType": "ExecPrice",
                    "Queue": "Bid",
                    "Volume": message.shares,
                    "OrderID": message.order_ref,
                    "Price": message.execution_price,
                }
                (queue, i, j) = lob.find_order(message.order_ref)
                record["OrderTimestamp"] = queue[i].queue[j].timestamp
                self.records.append((timestamp, record))

    def write_csv(self, file) -> None:
        """Write recorded trade executions to a CSV file.

        Args:
            file: File object to write to
        """
        file.write(
            "Timestamp,MessageType,Queue,Price,Volume,OrderID,OrderTimestamp\n".encode()
        )
        for x in self.records:
            row = f"{x[0]},{x[1]['MessageType']},{x[1]['Queue']},{x[1]['Price']},{x[1]['Volume']},{x[1]['OrderID']},{x[1]['OrderTimestamp']}\n"
            file.write(row.encode())
