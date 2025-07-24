"""ITCH 5.0 top of book message recorder for limit order books.

This module provides the ITCH50TopOfBookMessageRecorder class, which records
messages that affect the top of the book (best bid/ask) from ITCH 5.0 market data.
"""

from typing import Any

from ..market_event_handler import MarketEventHandler
from .itch50_market_message import (
    AddOrderMessage,
    AddOrderMPIDMessage,
    OrderCancelMessage,
    OrderDeleteMessage,
    OrderExecutedMessage,
    OrderExecutedPriceMessage,
    OrderReplaceMessage,
    TradeMessage,
)


class ITCH50TopOfBookMessageRecorder(MarketEventHandler):
    """Records messages that affect the top of the book from ITCH 5.0 market data.

    This recorder detects and records messages that impact the best bid or ask
    prices, including order additions, executions, and hidden trades.

    Attributes:
        records: List of recorded top of book message records
    """

    def __init__(self) -> None:
        """Initialize the ITCH50TopOfBookMessageRecorder."""
        self.records: list[Any] = []

    def message_event(self, market_processor, timestamp, message) -> None:
        """Detect messages that affect the top of the book and record them.

        Args:
            market_processor: The market processor instance
            timestamp: The timestamp of the message
            message: The market message to process
        """
        lob = market_processor.current_lob
        if isinstance(message, AddOrderMessage) or isinstance(
            message, AddOrderMPIDMessage
        ):
            # Detect if top of book is affected; if so record the message
            if message.bsindicator == b"B":
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
            elif message.bsindicator == b"S":
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
            if lob.ask_order_on_book(message.order_ref):
                record = {
                    "MessageType": "Exec",
                    "Volume": message.shares,
                    "OrderID": message.order_ref,
                }
                record["Queue"] = "Ask"
                record["Price"] = lob.ask_levels[0].price
                self.records.append((timestamp, record))
            elif lob.bid_order_on_book(message.order_ref):
                record = {
                    "MessageType": "Exec",
                    "Volume": message.shares,
                    "OrderID": message.order_ref,
                }
                record["Queue"] = "Bid"
                record["Price"] = lob.bid_levels[0].price
                self.records.append((timestamp, record))
        elif isinstance(message, TradeMessage):
            if message.bsindicator == b"S":
                record = {
                    "MessageType": "ExecHid",
                    "Volume": message.shares,
                    "OrderID": -1,
                }
                record["Queue"] = "Ask"
                record["Price"] = message.price
                self.records.append((timestamp, record))
            elif message.bsindicator == b"B":
                record = {
                    "MessageType": "ExecHid",
                    "Volume": message.shares,
                    "OrderID": -1,
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
                self.records.append((timestamp, record))
        elif isinstance(message, OrderCancelMessage):
            if len(lob.ask_levels) > 0 and lob.ask_levels[0].order_on_book(
                message.order_ref
            ):
                record = {
                    "MessageType": "Cancel",
                    "Queue": "Ask",
                    "Volume": message.cancelShares,
                    "OrderID": message.order_ref,
                    "Price": lob.ask_levels[0].price,
                }
                self.records.append((timestamp, record))
            elif len(lob.bid_levels) > 0 and lob.bid_levels[0].order_on_book(
                message.order_ref
            ):
                record = {
                    "MessageType": "Cancel",
                    "Queue": "Bid",
                    "Volume": message.cancelShares,
                    "OrderID": message.order_ref,
                    "Price": lob.bid_levels[0].price,
                }
                self.records.append((timestamp, record))
        elif isinstance(message, OrderDeleteMessage):
            if len(lob.ask_levels) > 0 and lob.ask_levels[0].order_on_book(
                message.order_ref
            ):
                volume = (
                    lob.ask_levels[0]
                    .queue[lob.ask_levels[0].find_order_on_book(message.order_ref)]
                    .volume
                )
                record = {
                    "MessageType": "Delete",
                    "Queue": "Ask",
                    "Volume": volume,
                    "OrderID": message.order_ref,
                    "Price": lob.ask_levels[0].price,
                }
                self.records.append((timestamp, record))
            elif len(lob.bid_levels) > 0 and lob.bid_levels[0].order_on_book(
                message.order_ref
            ):
                volume = (
                    lob.bid_levels[0]
                    .queue[lob.bid_levels[0].find_order_on_book(message.order_ref)]
                    .volume
                )
                record = {
                    "MessageType": "Delete",
                    "Queue": "Bid",
                    "Volume": volume,
                    "OrderID": message.order_ref,
                    "Price": lob.bid_levels[0].price,
                }
                self.records.append((timestamp, record))
        elif isinstance(message, OrderReplaceMessage):
            if lob.ask_order_on_book(
                message.origorder_ref
            ):  # change to the top at same price
                if (
                    lob.ask_levels[0].order_on_book(message.origorder_ref)
                    and message.price == lob.ask_levels[0].price
                ):
                    (queue, i, j) = lob.find_order(message.origorder_ref, 0)
                    old_volume = queue[i].volume()
                    new_shares = message.shares - old_volume
                    record = {
                        "MessageType": "Replace",
                        "Queue": "Ask",
                        "Volume": new_shares,
                        "OrderID": message.neworder_ref,
                        "Price": lob.ask_levels[0].price,
                    }
                    self.records.append((timestamp, record))
                elif (
                    lob.ask_levels[0].order_on_book(message.origorder_ref)
                    and lob.ask_levels[0].price < message.price
                ):  # replace of a top order for an inferior order
                    record = {
                        "MessageType": "Replace",
                        "Queue": "Ask",
                        "Volume": message.shares * -1,
                        "OrderID": message.neworder_ref,
                        "Price": lob.ask_levels[0].price,
                    }
                    self.records.append((timestamp, record))
                elif message.price < lob.ask_levels[0].price:
                    record = {
                        "MessageType": "Replace",
                        "Queue": "Ask",
                        "Volume": message.shares,
                        "OrderID": message.neworder_ref,
                        "Price": lob.ask_levels[0].price,
                    }
                    self.records.append((timestamp, record))
                elif (
                    message.price == lob.ask_levels[0].price
                    and lob.ask_levels[0].order_on_book(message.origorder_ref) is False
                ):  # Improvement over old order
                    record = {
                        "MessageType": "Replace",
                        "Queue": "Ask",
                        "Volume": message.shares,
                        "OrderID": message.neworder_ref,
                        "Price": lob.ask_levels[0].price,
                    }
                    self.records.append((timestamp, record))
            if lob.bid_order_on_book(message.origorder_ref):
                if (
                    lob.bid_levels[0].order_on_book(message.origorder_ref)
                    and message.price == lob.bid_levels[0].price
                ):
                    (queue, i, j) = lob.find_order(message.origorder_ref, 1)
                    old_volume = queue[i].volume()
                    new_shares = message.shares - old_volume
                    record = {
                        "MessageType": "Replace",
                        "Queue": "Bid",
                        "Volume": new_shares,
                        "OrderID": message.neworder_ref,
                        "Price": lob.bid_levels[0].price,
                    }
                    self.records.append((timestamp, record))
                elif (
                    lob.bid_levels[0].order_on_book(message.origorder_ref)
                    and lob.bid_levels[0].price > message.price
                ):  # replace of a top order for an inferior order
                    record = {
                        "MessageType": "Replace",
                        "Queue": "Bid",
                        "Volume": message.shares * -1,
                        "OrderID": message.neworder_ref,
                        "Price": lob.bid_levels[0].price,
                    }
                    self.records.append((timestamp, record))
                elif (
                    message.price > lob.bid_levels[0].price
                ):  # Improvement of a top of the order_id
                    record = {
                        "MessageType": "Replace",
                        "Queue": "Bid",
                        "Volume": message.shares,
                        "OrderID": message.neworder_ref,
                        "Price": lob.bid_levels[0].price,
                    }
                    self.records.append((timestamp, record))
                elif (
                    message.price == lob.bid_levels[0].price
                    and lob.bid_levels[0].order_on_book(message.origorder_ref) is False
                ):  # Improvement over old order
                    record = {
                        "MessageType": "Replace",
                        "Queue": "Bid",
                        "Volume": message.shares,
                        "OrderID": message.neworder_ref,
                        "Price": lob.bid_levels[0].price,
                    }
                    self.records.append((timestamp, record))

    def write_csv(self, file) -> None:
        """Write recorded top of book messages to a CSV file.

        Args:
            file: File object to write to
        """
        file.write("Timestamp,MessageType,Queue,Price,Volume,OrderID\n")
        for x in self.records:
            row = f"{x[0]},{x[1]['MessageType']},{x[1]['Queue']},{x[1]['Price']},{x[1]['Volume']},{x[1]['OrderID']}\n"
            file.write(row)
