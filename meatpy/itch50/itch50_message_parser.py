"""itch50_message_parser.py: Message parser class for ITCH 5.0"""

__author__ = "Vincent Grégoire"
__email__ = "vincent.gregoire@gmail.com"

from copy import deepcopy
import meatpy.itch50.itch50_market_message
from meatpy.message_parser import MessageParser


class ITCH50MessageParser(MessageParser):
    """A market message parser for ITCH 5.0 data.

    """
    def __init__(self):
        self.keep_messages_types = b'SAFECXDUBHRYPQINLVWK'
        self.skip_stock_messages = False
        self.order_refs = {}
        self.stocks = None
        self.matches = {}
        self.counter = 0
        self.stock_directory = []
        self.system_messages = []

        # Output settings
        self.output_prefix = ''
        self.message_buffer = 2000  # Per stock buffer size
        self.global_write_trigger = 1000000  # Check if buffers exceeded
        super(ITCH50MessageParser, self).__init__()

    def write_file(self, file, in_messages=None):
        """Write the messages to a  csv file in a compatible format

        The messages are written to a file that could be again parsed by
        the parser. In no messages are provided, the current message queue
        is used.

        :param file: file to write to
        :type file: file
        :param in_messages: messages to output
        :type in_messages: list of ITCH50MarketMessage
        """
        if in_messages is None:
            messages = self.stock_directory
        else:
            messages = in_messages

        for x in messages:
            file.write(b'\x00')
            file.write(chr(x.message_size))
            file.write(x.pack())

    def parse_file(self, file, write=False):
        """Parse the content of the file to generate ITCH50MarketMessage
        objects.

        Flag indicates if parsing output is written at the same time instead
        of kept in memory.
        """
        # Init containers
        self.counter = 0
        self.order_refs = {}
        self.stock_messages = {}
        self.matches = {}
        self.stock_messages = {}
        self.stock_directory = []
        self.system_messages = []
        self.latest_timestamp = None

        maxMessageSize = 52  # Largest possible message in ITCH
        cachesize = 1024*4
        haveData = True
        EOFreached = False
        dataBuffer = file.read(cachesize)
        buflen = len(dataBuffer)
        
        while haveData is True:
            # Process next message
            byte = dataBuffer[0:1]
            if byte != b'\x00':
                raise Exception('ITCH50MessageParser:ITCH_factory',
                                'Unexpected byte: ' + str(byte))
            messageLen = ord(dataBuffer[1:2])
            message = self.ITCH_factory(dataBuffer[2:2+messageLen])
            self.process_message(message)

            if message.type == b'S':  # System message
                if message.code == b'C':  # End of messages
                    break

            # Check if we need to write the cache for the stock
            if write and self.counter % self.global_write_trigger == 0:
                for x in self.stock_messages:
                    self.write_stock(x)

            # Remove the message from buffer
            dataBuffer = dataBuffer[2+messageLen:]
            buflen = len(dataBuffer)
            
            if EOFreached and (buflen == 0):
                haveData = False

            # If we don't have enough, read more
            if buflen < maxMessageSize and not EOFreached:
                newData = file.read(cachesize)
                if newData == b'':
                    EOFreached = True
                    if buflen == 0:
                        haveData = False
                else:
                    dataBuffer = dataBuffer + newData
                    buflen = len(dataBuffer)

        # Write all unempty buffers
        if write:
            for x in self.stock_messages:
                self.write_stock(stock=x, overlook_buffer=True)

    def write_stock(self, stock, overlook_buffer=False):
        if (len(self.stock_messages[stock]) > self.message_buffer or
                overlook_buffer):
            stock_str = stock.decode()
            with open(self.output_prefix +
                      stock_str.strip().replace('*', '8')+'.txt', 'a+b') as file:
                        # * in stock symbols replaced by 8
                for x in self.stock_messages[stock]:
                    file.write(b'\x00')
                    file.write(bytes([x.message_size]))
                    file.write(x.pack())
                self.stock_messages[stock] = []

    def append_stock_message(self, stock, message):
        """Append the message to the stock message queue

        Initialises the queue if empty"""
        if self.stocks is None or stock in self.stocks:
	        if self.skip_stock_messages:
	            return
	        if stock not in self.stock_messages:
	            self.stock_messages[stock] = deepcopy(self.system_messages)
	        self.stock_messages[stock].append(message)

    def process_message(self, message):
        """
            Looks at the message and decides what to do with it.

            Could be keep, discard, send to file, etc.
        """
        self.counter += 1

        if self.counter % 1000000 == 0:
            print( "Processing message no " + str(self.counter))

        if message.type not in self.keep_messages_types:
            return

        if message.type in b'R':
            self.stock_directory.append(message)
            self.append_stock_message(message.stock, message)
        elif message.type in b'SVW':
            # Pass-through all system messages
            for x in self.stock_messages:
                self.append_stock_message(x, message)
            self.system_messages.append(message)
        elif message.type in b'HYQINK':
            if self.stocks is None or message.stock in self.stocks:
                self.append_stock_message(message.stock, message)
        elif message.type in b'AF':
            if self.stocks is None or message.stock in self.stocks:
                self.order_refs[message.orderRefNum] = message.stock
                self.append_stock_message(message.stock, message)
        elif message.type in b'ECXD':
            if message.orderRefNum in self.order_refs:
                stock = self.order_refs[message.orderRefNum]
                self.append_stock_message(stock, message)
                if message.type in b'D':
                    del self.order_refs[message.orderRefNum]
                elif message.type in b'EC':
                    self.matches[message.match] = stock
        elif message.type in b'U':
            if message.origOrderRefNum in self.order_refs:
                stock = self.order_refs[message.origOrderRefNum]
                self.append_stock_message(stock, message)
                del self.order_refs[message.origOrderRefNum]
                self.order_refs[message.newOrderRefNum] = stock
        elif message.type in b'B':
            if message.match in self.matches:
                stock = self.matches[message.match]
                self.append_stock_message(stock, message)
        elif message.type in b'P':
            if self.stocks is None or message.stock in self.stocks:
                self.append_stock_message(message.stock, message)
                self.matches[message.match] = message.stock

    def ITCH_factory(self, message):
        '''
            Pass this factory an entire bytearray and you will be
            given the appropriate ITCH message
        '''
        msgtype = chr(message[0])
        if msgtype == 'S':
            return meatpy.itch50.itch50_market_message.SystemEventMessage(message)
        elif msgtype == 'R':
            return meatpy.itch50.itch50_market_message.StockDirectoryMessage(message)
        elif msgtype == 'H':
            return meatpy.itch50.itch50_market_message.StockTradingActionMessage(message)
        elif msgtype == 'Y':
            return meatpy.itch50.itch50_market_message.RegSHOMessage(message)
        elif msgtype == 'L':
            return meatpy.itch50.itch50_market_message.MarketParticipantPositionMessage(message)
        elif msgtype == 'V':
            return meatpy.itch50.itch50_market_message.MWCBDeclineLevelMessage(message)
        elif msgtype == 'W':
            return meatpy.itch50.itch50_market_message.MWCBBreachMessage(message)
        elif msgtype == 'K':
            return meatpy.itch50.itch50_market_message.IPOQuotingPeriodUpdateMessage(message)
        elif msgtype == 'A':
            return meatpy.itch50.itch50_market_message.AddOrderMessage(message)
        elif msgtype == 'F':
            return meatpy.itch50.itch50_market_message.AddOrderMPIDMessage(message)
        elif msgtype == 'E':
            return meatpy.itch50.itch50_market_message.OrderExecutedMessage(message)
        elif msgtype == 'C':
            return meatpy.itch50.itch50_market_message.OrderExecutedPriceMessage(message)
        elif msgtype == 'X':
            return meatpy.itch50.itch50_market_message.OrderCancelMessage(message)
        elif msgtype == 'D':
            return meatpy.itch50.itch50_market_message.OrderDeleteMessage(message)
        elif msgtype == 'U':
            return meatpy.itch50.itch50_market_message.OrderReplaceMessage(message)
        elif msgtype == 'P':
            return meatpy.itch50.itch50_market_message.TradeMessage(message)
        elif msgtype == 'Q':
            return meatpy.itch50.itch50_market_message.CrossTradeMessage(message)
        elif msgtype == 'B':
            return meatpy.itch50.itch50_market_message.BrokenTradeMessage(message)
        elif msgtype == 'I':
            return meatpy.itch50.itch50_market_message.NoiiMessage(message)
        elif msgtype == 'N':
            return meatpy.itch50.itch50_market_message.RpiiMessage(message)
        else:
            raise Exception('ITCH50MessageParser:ITCH_factory',
                            'Unknown message type: '+ str(msgtype))
