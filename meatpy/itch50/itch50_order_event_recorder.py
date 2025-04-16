"""itch50_order_event_recorder.py: Order event recorder class for ITCH 5.0"""

__author__ = "Vincent Grégoire"
__email__ = "vincent.gregoire@gmail.com"

from meatpy.market_event_handler import MarketEventHandler
from meatpy.itch50.itch50_market_message import *



class ITCH50OrderEventRecorder(MarketEventHandler):
    def __init__(self):
        self.records = []

    def message_event(self, market_processor, timestamp, message):
        """Detect messages that involve orders and record them"""
        if not (isinstance(message, AddOrderMessage) or
                isinstance(message, AddOrderMPIDMessage) or
                isinstance(message, OrderExecutedMessage) or
                isinstance(message, OrderExecutedPriceMessage) or
                isinstance(message, OrderCancelMessage) or
                isinstance(message, OrderDeleteMessage) or
                isinstance(message, OrderReplaceMessage)):
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

        if isinstance(message, AddOrderMessage):
            record = {'orderRefNum': message.orderRefNum,
                      'bsindicator': message.bsindicator.decode(),
                      'shares': message.shares,
                      'price': message.price,
                      'newOrderRefNum': '',
                      'MessageType': 'AddOrder'}
        elif isinstance(message, AddOrderMPIDMessage):
            record = {'orderRefNum': message.orderRefNum,
                      'bsindicator': message.bsindicator.decode(),
                      'shares': message.shares,
                      'price': message.price,
                      'newOrderRefNum': '',
                      'MessageType': 'AddOrderMPID'}
        elif isinstance(message, OrderExecutedMessage):
            record = {'orderRefNum': message.orderRefNum,
                      'bsindicator': '',
                      'shares': message.shares,
                      'price': '',
                      'newOrderRefNum': '',
                      'MessageType': 'OrderExecuted'}
        elif isinstance(message, OrderExecutedPriceMessage):
            record = {'orderRefNum': message.orderRefNum,
                      'bsindicator': '',
                      'shares': message.shares,
                      'price': message.price,
                      'newOrderRefNum': '',
                      'MessageType': 'OrderExecutedPrice'}
        elif isinstance(message, OrderCancelMessage):
            record = {'orderRefNum': message.orderRefNum,
                      'bsindicator': '',
                      'shares': message.cancelShares,
                      'price': '',
                      'newOrderRefNum': '',
                      'MessageType': 'OrderCancel'}
        elif isinstance(message, OrderDeleteMessage):
            record = {'orderRefNum': message.orderRefNum,
                      'bsindicator': '',
                      'shares': '',
                      'price': '',
                      'newOrderRefNum': '',
                      'MessageType': 'OrderDelete'}
        elif isinstance(message, OrderReplaceMessage):
            record = {'orderRefNum': message.origOrderRefNum,
                      'bsindicator': '',
                      'shares': message.shares,
                      'price': message.price,
                      'newOrderRefNum': message.newOrderRefNum,
                      'MessageType': 'OrderReplace'}

        record['ask_price'] = ask_price
        record['ask_size'] = ask_size
        record['bid_price'] = bid_price
        record['bid_size'] = bid_size
        self.records.append((timestamp, record))

    def write_csv(self, file):
        """Write to a file in CSV format"""
        # Write header row
        file.write('Timestamp,MessageType,BuySellIndicator,Price,Volume,OrderID,NewOrderID,AskPrice,AskSize,BidPrice,BidSize\n'.encode())
        # Write content
        for x in self.records:
            row = (str(x[0]) + ',' + x[1]["MessageType"] + ',' +
                   x[1]["bsindicator"] + ',' + str(x[1]["price"]) + ',' +
                   str(x[1]["shares"]) + ',' + str(x[1]["orderRefNum"]) +
                   ',' + str(x[1]["newOrderRefNum"]) + ',' +
                   str(x[1]["ask_price"]) + ',' + str(x[1]["ask_size"]) + ',' +
                   str(x[1]["bid_price"]) + ',' + str(x[1]["bid_size"]) + '\n')
            file.write(row.encode())