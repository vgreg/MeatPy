"""ITCH 5.0 message parser for market data files.

This module provides the ITCH50MessageParser class, which parses ITCH 5.0 market data files and produces structured message objects for further processing.
"""

from datetime import datetime

import meatpy.itch50.itch50_market_message
from meatpy.message_parser import MessageParser


class InvalidMessageFormatError(Exception):
    """Exception raised when a message has an invalid format.

    This exception is raised when the message format does not match
    the expected ITCH 5.0 message structure.
    """

    pass


class UnknownMessageTypeError(Exception):
    """Exception raised when an unknown message type is encountered.

    This exception is raised when the message type is not recognized
    by the ITCH 5.0 parser.
    """

    pass


class ITCH50MessageParser(MessageParser):
    """A market message parser for ITCH 5.0 data.

    Attributes:
        keep_messages_types: Bytes of message types to keep
        skip_stock_messages: Whether to skip stock messages
        order_refs: Mapping of order reference numbers to stocks
        stocks: List of stocks to parse (None for all)
        matches: Mapping of match numbers to stocks
        counter: Message counter
        stock_directory: List of stock directory messages
        system_messages: List of system messages
        output_prefix: Prefix for output files
        message_buffer: Per-stock buffer size
        global_write_trigger: Number of messages before writing buffers
    """

    def __init__(self) -> None:
        """Initialize the ITCH50MessageParser."""
        self.keep_messages_types = b"SAFECXDUBHRYPQINLVWKJh"
        self.skip_stock_messages = False
        self.order_refs = {}
        self.stocks = None
        self.matches = {}
        self.counter = 0
        self.stock_directory = []
        self.system_messages = []
        self.output_prefix = ""
        self.message_buffer = 2000
        self.global_write_trigger = 1000000
        super(ITCH50MessageParser, self).__init__()

    def write_file(self, file, in_messages=None) -> None:
        """Write messages to a CSV file in a compatible format.

        Args:
            file: File object to write to
            in_messages: Optional list of messages to output
        """
        if in_messages is None:
            messages = self.stock_directory
        else:
            messages = in_messages
        for x in messages:
            file.write(b"\x00")
            file.write(chr(x.message_size))
            file.write(x.pack())

    def parse_file(self, file, write=False) -> None:
        """Parse the content of the file to generate ITCH50MarketMessage objects.

        Args:
            file: File object to read from
            write: Whether to write output during parsing
        """
        # Init containers
        self.counter = 0
        self.order_refs = {}
        self.stock_messages = {}
        self.matches = {}
        self.stock_directory = []
        self.system_messages = []
        self.latest_timestamp = None
        cachesize = 1024 * 4
        haveData = True
        EOFreached = False
        dataBuffer = file.read(cachesize)
        data_view = memoryview(dataBuffer)
        offset = 0
        buflen = len(data_view)
        while haveData:
            if offset + 2 > buflen:
                newData = file.read(cachesize)
                if not newData:
                    EOFreached = True
                dataBuffer = data_view[offset:].tobytes() + newData
                data_view = memoryview(dataBuffer)
                buflen = len(data_view)
                offset = 0
                continue
            if data_view[offset] != 0:
                raise InvalidMessageFormatError(f"Unexpected byte: {data_view[offset]}")
            messageLen = data_view[offset + 1]
            messageEnd = offset + 2 + messageLen
            if messageEnd > buflen:
                newData = file.read(cachesize)
                if not newData:
                    EOFreached = True
                dataBuffer = data_view[offset:].tobytes() + newData
                data_view = memoryview(dataBuffer)
                buflen = len(data_view)
                offset = 0
                continue
            message = self.ITCH_factory(data_view[offset + 2 : messageEnd])
            keep_messages_bool = self.process_message(message)
            if not keep_messages_bool:
                offset = messageEnd
                continue
            if message.type == b"S" and message.code == b"C":
                break
            if write and self.counter % self.global_write_trigger == 0:
                for x in self.stock_messages:
                    self.write_stock(x)
            offset = messageEnd
            if offset >= buflen and EOFreached:
                haveData = False
        if write:
            for x in self.stock_messages:
                self.write_stock(stock=x, overlook_buffer=True)

    def write_stock(self, stock, overlook_buffer=False) -> None:
        """Write buffered messages for a stock to a file.

        Args:
            stock: Stock symbol
            overlook_buffer: Whether to write regardless of buffer size
        """
        if len(self.stock_messages[stock]) > self.message_buffer or overlook_buffer:
            stock_str = stock.decode()
            with open(
                f"{self.output_prefix}{stock_str.strip().replace('*', '8')}.txt", "a+b"
            ) as file:
                for x in self.stock_messages[stock]:
                    file.write(b"\x00")
                    file.write(bytes([x.message_size]))
                    file.write(x.pack())
                self.stock_messages[stock] = []

    def append_stock_message(self, stock, message) -> None:
        """Append a message to the stock message queue.

        Args:
            stock: Stock symbol
            message: Message object to append
        """
        if self.stocks is None or stock in self.stocks:
            if self.skip_stock_messages:
                return
            if stock not in self.stock_messages:
                self.stock_messages[stock] = list(self.system_messages)
                self.stock_messages[stock].append(message)
                return

    def process_message(self, message) -> None:
        """Process a message and decide what to do with it.

        Args:
            message: The message object to process
        """
        self.counter += 1
        if self.counter % 1000000 == 0:
            print(f"[{datetime.now()}] Processed {self.counter} messages", flush=True)
        if message.type not in self.keep_messages_types:
            return False
        if message.type in b"R":
            self.stock_directory.append(message)
            self.append_stock_message(message.stock, message)
        elif message.type in b"SVW":
            for x in self.stock_messages:
                self.append_stock_message(x, message)
            self.system_messages.append(message)
        elif message.type in b"HYQINKLJh":
            if self.stocks is None or message.stock in self.stocks:
                self.append_stock_message(message.stock, message)
        elif message.type in b"AF":
            if self.stocks is None or message.stock in self.stocks:
                self.order_refs[message.orderRefNum] = message.stock
                self.append_stock_message(message.stock, message)
        elif message.type in b"ECXD":
            if message.orderRefNum in self.order_refs:
                stock = self.order_refs[message.orderRefNum]
                self.append_stock_message(stock, message)
                if message.type in b"D":
                    del self.order_refs[message.orderRefNum]
                elif message.type in b"EC":
                    self.matches[message.match] = stock
        elif message.type in b"U":
            if message.origOrderRefNum in self.order_refs:
                stock = self.order_refs[message.origOrderRefNum]
                self.append_stock_message(stock, message)
                del self.order_refs[message.origOrderRefNum]
                self.order_refs[message.newOrderRefNum] = stock
        elif message.type in b"B":
            if message.match in self.matches:
                stock = self.matches[message.match]
                self.append_stock_message(stock, message)
        elif message.type in b"P":
            if self.stocks is None or message.stock in self.stocks:
                self.append_stock_message(message.stock, message)
                self.matches[message.match] = message.stock

        return True

    def ITCH_factory(self, message) -> None:
        """
        Pass this factory an entire bytearray and you will be
        given the appropriate ITCH message
        """
        msgtype = chr(message[0])
        if msgtype == "S":
            return meatpy.itch50.itch50_market_message.SystemEventMessage(message)
        elif msgtype == "R":
            return meatpy.itch50.itch50_market_message.StockDirectoryMessage(message)
        elif msgtype == "H":
            return meatpy.itch50.itch50_market_message.StockTradingActionMessage(
                message
            )
        elif msgtype == "Y":
            return meatpy.itch50.itch50_market_message.RegSHOMessage(message)
        elif msgtype == "L":
            return meatpy.itch50.itch50_market_message.MarketParticipantPositionMessage(
                message
            )
        elif msgtype == "V":
            return meatpy.itch50.itch50_market_message.MWCBDeclineLevelMessage(message)
        elif msgtype == "W":
            return meatpy.itch50.itch50_market_message.MWCBBreachMessage(message)
        elif msgtype == "K":
            return meatpy.itch50.itch50_market_message.IPOQuotingPeriodUpdateMessage(
                message
            )
        elif msgtype == "J":
            return meatpy.itch50.itch50_market_message.LULDAuctionCollarMessage(message)
        elif msgtype == "h":
            return meatpy.itch50.itch50_market_message.OperationalHaltMessage(message)
        elif msgtype == "A":
            return meatpy.itch50.itch50_market_message.AddOrderMessage(message)
        elif msgtype == "F":
            return meatpy.itch50.itch50_market_message.AddOrderMPIDMessage(message)
        elif msgtype == "E":
            return meatpy.itch50.itch50_market_message.OrderExecutedMessage(message)
        elif msgtype == "C":
            return meatpy.itch50.itch50_market_message.OrderExecutedPriceMessage(
                message
            )
        elif msgtype == "X":
            return meatpy.itch50.itch50_market_message.OrderCancelMessage(message)
        elif msgtype == "D":
            return meatpy.itch50.itch50_market_message.OrderDeleteMessage(message)
        elif msgtype == "U":
            return meatpy.itch50.itch50_market_message.OrderReplaceMessage(message)
        elif msgtype == "P":
            return meatpy.itch50.itch50_market_message.TradeMessage(message)
        elif msgtype == "Q":
            return meatpy.itch50.itch50_market_message.CrossTradeMessage(message)
        elif msgtype == "B":
            return meatpy.itch50.itch50_market_message.BrokenTradeMessage(message)
        elif msgtype == "I":
            return meatpy.itch50.itch50_market_message.NoiiMessage(message)
        elif msgtype == "N":
            return meatpy.itch50.itch50_market_message.RpiiMessage(message)
        elif msgtype == "O":
            return meatpy.itch50.itch50_market_message.DirectListingCapitalRaiseMessage(
                message
            )
        else:
            raise UnknownMessageTypeError(f"Unknown message type: {msgtype}")
