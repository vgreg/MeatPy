from .lob import LimitOrderBook, OrderType
from .market_processor import MarketProcessor, OrderID, Price, TradeRef, Volume
from .message_parser import MarketMessage
from .timestamp import Timestamp


class MarketEventHandler:
    """A handler for market events.

    The handler gets triggered whenever there is a market event and
    handles the event accordingly.
    """

    def before_lob_update(self, lob: LimitOrderBook, new_timestamp: Timestamp):
        """Trigger before a book update (next event timestamp passed)"""
        pass

    def message_event(
        self,
        market_processor: MarketProcessor,
        timestamp: Timestamp,
        message: MarketMessage,
    ):
        pass

    def enter_quote_event(
        self,
        market_processor: MarketProcessor,
        timestamp: Timestamp,
        price: Price,
        volume: Volume,
        order_id: OrderID,
        order_type: OrderType = None,
    ):
        pass

    def cancel_quote_event(
        self,
        market_processor: MarketProcessor,
        timestamp: Timestamp,
        volume: Volume,
        order_id: OrderID,
        order_type: OrderType = None,
    ):
        pass

    def delete_quote_event(
        self,
        market_processor: MarketProcessor,
        timestamp: Timestamp,
        order_id: OrderID,
        order_type: OrderType = None,
    ):
        pass

    def replace_quote_event(
        self,
        market_processor: MarketProcessor,
        timestamp: Timestamp,
        orig_order_id: OrderID,
        new_order_id: OrderID,
        price: Price,
        volume: Volume,
        order_type: OrderType = None,
    ):
        pass

    def execute_trade_event(
        self,
        market_processor: MarketProcessor,
        timestamp: Timestamp,
        volume: Volume,
        order_id: OrderID,
        trade_ref: TradeRef,
        order_type: OrderType = None,
    ):
        pass

    def execute_trade_price_event(
        self,
        market_processor: MarketProcessor,
        timestamp: Timestamp,
        volume: Volume,
        order_id: OrderID,
        trade_ref: TradeRef,
        price: Price,
        order_type: OrderType = None,
    ):
        pass

    def auction_trade_event(
        self,
        market_processor: MarketProcessor,
        timestamp: Timestamp,
        volume: Volume,
        price: Price,
        bid_id: OrderID,
        ask_id: OrderID,
    ):
        pass

    def crossing_trade_event(
        self,
        market_processor: MarketProcessor,
        timestamp: Timestamp,
        volume: Volume,
        price: Price,
        bid_id: OrderID,
        ask_id: OrderID,
    ):
        pass
