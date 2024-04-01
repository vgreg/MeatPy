"""itch50_market_processor.py: Market processor and order event classes for ITCH5.0"""

__author__ = "Vincent Grégoire"
__email__ = "vincent.gregoire@gmail.com"

from meatpy.market_processor import MarketProcessor
from meatpy.itch50.itch50_market_message import *
from meatpy.trading_status import *


class ITCH50MarketProcessor(MarketProcessor):
    """An MarketProcessor for ITCH 5.0 format

    For now only process LOB.

    Note that for efficiency, no check is done on the stock, it is assumed
    that all messages relate to the same stock.

    """

    def __init__(self, instrument, book_date):
        super(ITCH50MarketProcessor, self).__init__(instrument, book_date)
        self.system_status = b""
        self.stock_status = b""
        self.emc_status = b""

    def process_message(self, message, new_snapshot=True):
        """Process a MarketMessage

        :param message: message to process
        :type message: ITCH50MarketMessage
        """

        timestamp = message.timestamp

        self.message_event(timestamp, message)

        if isinstance(message, AddOrderMessage) or isinstance(
            message, AddOrderMPIDMessage
        ):
            if self.track_lob:
                if message.bsindicator == b"B":
                    order_type = 1
                elif message.bsindicator == b"S":
                    order_type = 0
                else:
                    raise Exception(
                        "ITCH50MarketProcessor:process_message",
                        "Wrong value for bsindicator: " + str(message.bsindicator),
                    )
                self.pre_lob_event(timestamp)
                self.enter_quote(
                    timestamp=timestamp,
                    price=message.price,
                    volume=message.shares,
                    order_id=message.orderRefNum,
                    order_type=order_type,
                )
        elif isinstance(message, OrderExecutedMessage):
            if self.track_lob:
                self.pre_lob_event(timestamp)
                self.execute_trade(
                    timestamp=timestamp,
                    volume=message.shares,
                    order_id=message.orderRefNum,
                    trade_ref=message.match,
                )
        elif isinstance(message, OrderExecutedPriceMessage):
            if self.track_lob:
                self.pre_lob_event(timestamp)
                self.execute_trade_price(
                    timestamp=timestamp,
                    volume=message.shares,
                    order_id=message.orderRefNum,
                    trade_ref=message.match,
                    price=message.price,
                )
        elif isinstance(message, OrderCancelMessage):
            if self.track_lob:
                self.pre_lob_event(timestamp)
                self.cancel_quote(
                    timestamp=timestamp,
                    volume=message.cancelShares,
                    order_id=message.orderRefNum,
                )
        elif isinstance(message, OrderDeleteMessage):
            if self.track_lob:
                self.pre_lob_event(timestamp)
                self.delete_quote(timestamp=timestamp, order_id=message.orderRefNum)
        elif isinstance(message, OrderReplaceMessage):
            if self.track_lob:
                self.pre_lob_event(timestamp)
                if self.current_lob.ask_order_on_book(message.origOrderRefNum):
                    order_type = 0
                elif self.current_lob.bid_order_on_book(message.origOrderRefNum):
                    order_type = 1
                else:
                    raise Exception(
                        "ITCH50MarketProcessor:process_message",
                        "Replacing missing order.",
                    )
                self.replace_quote(
                    timestamp=timestamp,
                    orig_order_id=message.origOrderRefNum,
                    new_order_id=message.newOrderRefNum,
                    price=message.price,
                    volume=message.shares,
                    order_type=order_type,
                )
        elif isinstance(message, SystemEventMessage):
            self.process_system_message(message.code, timestamp, new_snapshot)
        elif isinstance(message, StockTradingActionMessage):
            self.process_trading_action_message(message.state, timestamp, new_snapshot)

    def process_system_message(self, code, timestamp, new_snapshot=True):
        """Process a system message"""
        if code in b"OSQMEC":
            self.system_status = code
        elif code in b"ARB":
            self.emc_status = code
        else:
            raise Exception(
                "ITCH50MarketProcessor:process_system_message",
                "Unknown system message: " + str(code),
            )
        self.update_trading_status()

    def process_trading_action_message(self, state, timestamp, new_snapshot=True):
        """Process a stock trading action message"""
        if state in b"HPQT":
            self.stock_status = state
        else:
            raise Exception(
                "ITCH50MarketProcessor:process_trading_action_message",
                "Unknown trading state: " + str(state),
            )
        self.update_trading_status()

    def update_trading_status(self):
        """Update the current trading status"""
        if self.emc_status == b"A" or self.stock_status in b"HP":
            # Halted
            self.trading_status = HaltedTradingStatus()
        elif self.emc_status == b"R" or self.stock_status == b"Q":
            # Quote-only
            self.trading_status = QuoteOnlyTradingStatus()
        elif self.system_status in b"OS":
            # Pre-Trade
            self.trading_status = PreTradeTradingStatus()
        elif self.system_status in b"MEC":
            # Post-Trade
            self.trading_status = PostTradeTradingStatus()
        elif self.system_status == b"Q" and self.stock_status == b"T":
            # Trading
            self.trading_status = TradeTradingStatus()
        else:
            raise Exception(
                "ITCH50MarketProcessor:update_trading_status",
                "Could not determine trading status: "
                + str(self.system_status)
                + "/"
                + str(self.emc_status)
                + "/"
                + str(self.stock_status),
            )

    def enter_quote(self, timestamp, price, volume, order_id, order_type):
        """Enter a new quote in the LOB"""
        # Order_type == 1 for bid, 0 for ask
        self.enter_quote_event(timestamp, price, volume, order_id, order_type)
        self.current_lob.enter_quote(timestamp, price, volume, order_id, order_type)

    def cancel_quote(self, timestamp, volume, order_id):
        """Cancel a quote from the LOB."""
        # Cancel order from new snapshot, so the snapshot can apply
        # the appropriate ranking according to rules
        self.cancel_quote_event(timestamp, volume, order_id)
        self.current_lob.cancel_quote(volume, order_id)

    def delete_quote(self, timestamp, order_id):
        """Delete a quote from the LOB."""
        #
        # Delete order from new snapshot, so the snapshot can apply
        # the appropriate ranking according to rules
        self.delete_quote_event(timestamp, order_id)
        self.current_lob.delete_quote(order_id)

    def replace_quote(
        self, timestamp, orig_order_id, new_order_id, price, volume, order_type
    ):
        """Replace a quote in the LOB."""
        #
        # Replace an order, so basilly remov previous instance and introduce
        # new one.
        self.replace_quote_event(
            timestamp, orig_order_id, new_order_id, price, volume, order_type
        )
        self.current_lob.delete_quote(orig_order_id)
        self.current_lob.enter_quote(timestamp, price, volume, new_order_id, order_type)

    def execute_trade(self, timestamp, volume, order_id, trade_ref):
        """Execute a on-market trade."""
        #
        # Execute order from new snapshot, so the snapshot can apply
        # the appropriate ranking according to rules
        self.execute_trade_event(timestamp, volume, order_id, trade_ref)
        self.current_lob.execute_trade(timestamp, volume, order_id)

    def execute_trade_price(self, timestamp, volume, order_id, trade_ref, price):
        """Execute a on-market trade, bypassing piority."""
        #
        # TODO: Figure out what to do with non-printable executions
        #
        # Execute order from new snapshot, so the snapshot can apply
        # the appropriate ranking according to rules
        self.execute_trade_price_event(timestamp, volume, order_id, trade_ref, price)
        self.current_lob.execute_trade_price(timestamp, volume, order_id)
