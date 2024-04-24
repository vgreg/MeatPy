from ..market_event_handler import MarketEventHandler
from .itch50_market_message import (
    OrderExecutedMessage,
    OrderExecutedPriceMessage,
    TradeMessage,
)


class ITCH50ExecTradeRecorder(MarketEventHandler):
    def __init__(self):
        self.records = []

    def message_event(self, market_processor, timestamp, message):
        """Detect messages that affect th top of the book and record them"""
        lob = market_processor.current_lob
        if isinstance(message, OrderExecutedMessage):
            # An executed order will ALWAYS be against top of book
            # because of price priority, so record.
            if lob.ask_order_on_book(message.orderRefNum):
                record = {
                    "MessageType": "Exec",
                    "Volume": message.shares,
                    "OrderID": message.orderRefNum,
                }
                record["Queue"] = "Ask"
                record["Price"] = lob.ask_levels[0].price
                (queue, i, j) = lob.find_order(message.orderRefNum)
                record["OrderTimestamp"] = queue[i].queue[j].timestamp

                self.records.append((timestamp, record))
            elif lob.bid_order_on_book(message.orderRefNum):
                record = {
                    "MessageType": "Exec",
                    "Volume": message.shares,
                    "OrderID": message.orderRefNum,
                }
                record["Queue"] = "Bid"
                record["Price"] = lob.bid_levels[0].price
                (queue, i, j) = lob.find_order(message.orderRefNum)
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
                message.orderRefNum
            ):
                record = {
                    "MessageType": "ExecPrice",
                    "Queue": "Ask",
                    "Volume": message.shares,
                    "OrderID": message.orderRefNum,
                    "Price": message.price,
                }
                (queue, i, j) = lob.find_order(message.orderRefNum)
                record["OrderTimestamp"] = queue[i].queue[j].timestamp
                self.records.append((timestamp, record))
            elif len(lob.bid_levels) > 0 and lob.bid_levels[0].order_on_book(
                message.orderRefNum
            ):
                record = {
                    "MessageType": "ExecPrice",
                    "Queue": "Bid",
                    "Volume": message.shares,
                    "OrderID": message.orderRefNum,
                    "Price": message.price,
                }
                (queue, i, j) = lob.find_order(message.orderRefNum)
                record["OrderTimestamp"] = queue[i].queue[j].timestamp
                self.records.append((timestamp, record))

    def write_csv(self, file):
        """Write to a file in CSV format"""
        # Write header row
        file.write(
            "Timestamp,MessageType,Queue,Price,Volume,OrderID,OrderTimestamp\n".encode()
        )
        # Write content
        for x in self.records:
            row = (
                str(x[0])
                + ","
                + x[1]["MessageType"]
                + ","
                + x[1]["Queue"]
                + ","
                + str(x[1]["Price"])
                + ","
                + str(x[1]["Volume"])
                + ","
                + str(x[1]["OrderID"])
                + ","
                + str(x[1]["OrderTimestamp"])
                + "\n"
            )
            file.write(row.encode())
