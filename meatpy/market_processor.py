"""market_processor.py: The market engine that receives message and
re-constructs the market history."""

__author__ = "Vincent Grégoire"
__email__ = "vincent.gregoire@gmail.com"

import abc
from meatpy.lob import LimitOrderBook


class MarketProcessor:
    """A market engine that process events and builds the limit order book

    A MarketProcessor object is an engine that processes MarketMessage objects
    to build the market history for one instrument, on one day and on one
    market.

    The MarketProcessor keeps an up-to-date version of
    the limit order book, unless instructed not to."""

    __metaclass__ = abc.ABCMeta  # This in an abstract class

    def __init__(self, instrument, book_date):
        """Initializes an empty history for a specific instrument and date."""
        self.instrument = instrument
        self.book_date = book_date
        self.current_lob = None
        self.track_lob = True
        self.handlers = []
        self.trading_status = None

    # Common type definitions. Note: Also redefined in LOB.
    ask_type = 0
    bid_type = 1

    @abc.abstractmethod
    def process_message(self, message):
        """Process a MarketMessage

        :param message: message to process
        :type message: MarketMessage
        """
        return

    def processing_done(self):
        """Clean up time"""
        if self.current_lob is not None:
            self.current_lob.end_of_day()

    def before_lob_update(self, new_timestamp):
        """Event to pass on to handlers..."""
        for x in self.handlers:
            x.before_lob_update(self, new_timestamp)

    def message_event(self, timestamp, message):
        """Event to pass on to handlers..."""
        for x in self.handlers:
            x.message_event(self, timestamp, message)

    def enter_quote_event(self, timestamp, price, volume, order_id, order_type=None):
        """Event to pass on to handlers..."""
        for x in self.handlers:
            x.enter_quote_event(self, timestamp, price, volume, order_id, order_type)

    def cancel_quote_event(self, timestamp, volume, order_id, order_type=None):
        """Event to pass on to handlers..."""
        for x in self.handlers:
            x.cancel_quote_event(self, timestamp, volume, order_id, order_type)

    def delete_quote_event(self, timestamp, order_id, order_type=None):
        """Event to pass on to handlers..."""
        for x in self.handlers:
            x.delete_quote_event(self, timestamp, order_id, order_type)

    def replace_quote_event(
        self, timestamp, orig_order_id, new_order_id, price, volume, order_type=None
    ):
        """Event to pass on to handlers..."""
        for x in self.handlers:
            x.replace_quote_event(
                self, timestamp, orig_order_id, new_order_id, price, volume, order_type
            )

    def execute_trade_event(
        self, timestamp, volume, order_id, trade_ref, order_type=None
    ):
        """Event to pass on to handlers..."""
        for x in self.handlers:
            x.execute_trade_event(
                self, timestamp, volume, order_id, trade_ref, order_type
            )

    def execute_trade_price_event(
        self, timestamp, volume, order_id, trade_ref, price, order_type=None
    ):
        """Event to pass on to handlers..."""
        for x in self.handlers:
            x.execute_trade_price_event(
                self, timestamp, volume, order_id, trade_ref, price, order_type
            )

    def auction_trade_event(self, timestamp, volume, price, bid_id, ask_id):
        """Event to pass on to handlers..."""
        for x in self.handlers:
            x.auction_trade_event(self, timestamp, volume, price, bid_id, ask_id)

    def crossing_trade_event(self, timestamp, volume, price, bid_id, ask_id):
        """Event to pass on to handlers..."""
        for x in self.handlers:
            x.crossing_trade_event(self, timestamp, volume, price, bid_id, ask_id)

    def pre_lob_event(self, timestamp, new_snapshot=True):
        """Prepare the lob for a new event

        If no current LOB, create one. Otherwise only create a new one if
        requested.
        """
        if self.current_lob is None:
            self.current_lob = LimitOrderBook(timestamp)
            # self.snapshots.append(self.current_lob)
        elif new_snapshot is True:
            self.before_lob_update(timestamp)
            if self.current_lob.timestamp == timestamp:
                self.current_lob.timestamp_inc += 1
            else:
                self.current_lob.timestamp_inc = 0
            self.current_lob.timestamp = timestamp
