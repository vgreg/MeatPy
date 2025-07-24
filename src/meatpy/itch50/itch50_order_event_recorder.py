"""ITCH 5.0 order event recorder for limit order books.

This module provides the ITCH50OrderEventRecorder class, which records order-related
events from ITCH 5.0 market data and exports them to CSV files.
"""

from ..market_event_handler import MarketEventHandler
from .itch50_market_message import (
    AddOrderMessage,
    AddOrderMPIDMessage,
    OrderCancelMessage,
    OrderDeleteMessage,
    OrderExecutedMessage,
    OrderExecutedPriceMessage,
    OrderReplaceMessage,
)


class ITCH50OrderEventRecorder(MarketEventHandler):
    """Records order-related events from ITCH 5.0 market data.

    This recorder detects and records various order events including additions,
    executions, cancellations, deletions, and replacements, along with the
    current state of the limit order book.

    Attributes:
        records: List of recorded order event records
    """

    def __init__(self) -> None:
        """Initialize the ITCH50OrderEventRecorder."""
        self.records = []

    def message_event(self, market_processor, timestamp, message) -> None:
        """Detect messages that involve orders and record them.

        Args:
            market_processor: The market processor instance
            timestamp: The timestamp of the message
            message: The market message to process
        """
        if not (
            isinstance(message, AddOrderMessage)
            or isinstance(message, AddOrderMPIDMessage)
            or isinstance(message, OrderExecutedMessage)
            or isinstance(message, OrderExecutedPriceMessage)
            or isinstance(message, OrderCancelMessage)
            or isinstance(message, OrderDeleteMessage)
            or isinstance(message, OrderReplaceMessage)
        ):
            return
        lob = market_processor.current_lob
        ask_price = None
        ask_size = None
        bid_price = None
        bid_size = None
        # LOB is only initialised after first event.
        if lob is not None:
            if len(lob.ask_levels) > 0:
                ask_price = lob.ask_levels[0].price
                ask_size = lob.ask_levels[0].volume()
            if len(lob.bid_levels) > 0:
                bid_price = lob.bid_levels[0].price
                bid_size = lob.bid_levels[0].volume()
        # For OrderExecuted and OrderCancel, find price of corresponding
        # limit order. For OrderDelete also find quantity.
        if (
            isinstance(message, OrderExecutedMessage)
            or isinstance(message, OrderCancelMessage)
            or isinstance(message, OrderDeleteMessage)
        ):
            price = None
            shares = None
            try:
                queue, i, j = lob.find_order(message.order_ref)
                price = queue[i].price
                shares = queue[i].queue[j].volume
            except Exception as e:
                print(
                    f"ITCH50OrderEventRecorder ::{e} for order ID {message.order_ref}"
                )
        if isinstance(message, AddOrderMessage):
            record = {
                "order_ref": message.order_ref,
                "bsindicator": message.bsindicator.decode(),
                "shares": message.shares,
                "price": message.price,
                "neworder_ref": "",
                "MessageType": "AddOrder",
            }
        elif isinstance(message, AddOrderMPIDMessage):
            record = {
                "order_ref": message.order_ref,
                "bsindicator": message.bsindicator.decode(),
                "shares": message.shares,
                "price": message.price,
                "neworder_ref": "",
                "MessageType": "AddOrderMPID",
            }
        elif isinstance(message, OrderExecutedMessage):
            record = {
                "order_ref": message.order_ref,
                "bsindicator": "",
                "shares": message.shares,
                "price": price,
                "neworder_ref": "",
                "MessageType": "OrderExecuted",
            }
        elif isinstance(message, OrderExecutedPriceMessage):
            record = {
                "order_ref": message.order_ref,
                "bsindicator": "",
                "shares": message.shares,
                "price": message.price,
                "neworder_ref": "",
                "MessageType": "OrderExecutedPrice",
            }
        elif isinstance(message, OrderCancelMessage):
            record = {
                "order_ref": message.order_ref,
                "bsindicator": "",
                "shares": message.cancelShares,
                "price": price,
                "neworder_ref": "",
                "MessageType": "OrderCancel",
            }
        elif isinstance(message, OrderDeleteMessage):
            record = {
                "order_ref": message.order_ref,
                "bsindicator": price,
                "shares": shares,
                "price": price,
                "neworder_ref": "",
                "MessageType": "OrderDelete",
            }
        elif isinstance(message, OrderReplaceMessage):
            record = {
                "order_ref": message.origorder_ref,
                "bsindicator": "",
                "shares": message.shares,
                "price": message.price,
                "neworder_ref": message.neworder_ref,
                "MessageType": "OrderReplace",
            }
        record["ask_price"] = ask_price
        record["ask_size"] = ask_size
        record["bid_price"] = bid_price
        record["bid_size"] = bid_size
        self.records.append((timestamp, record))

    def write_csv(self, file) -> None:
        """Write recorded order events to a CSV file.

        Args:
            file: File object to write to
        """
        file.write(
            "Timestamp,MessageType,BuySellIndicator,Price,Volume,OrderID,NewOrderID,AskPrice,AskSize,BidPrice,BidSize\n".encode()
        )
        for x in self.records:
            row = f"{x[0]},{x[1]['MessageType']},{x[1]['bsindicator']},{x[1]['price']},{x[1]['shares']},{x[1]['order_ref']},{x[1]['neworder_ref']},{x[1]['ask_price']},{x[1]['ask_size']},{x[1]['bid_price']},{x[1]['bid_size']}\n"
            file.write(row.encode())
