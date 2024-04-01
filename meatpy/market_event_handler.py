"""market_event_handler.py: Base class for market event handlers."""


class MarketEventHandler:
    """A handler for market events.

    The handler gets triggered whenever there is a market event and
    handles the event accordingly.
    """

    def before_lob_update(self, lob, new_timestamp):
        """Trigger before a book update (next event timestamp passed)"""
        pass

    def message_event(self, market_processor, timestamp, message):
        pass

    def enter_quote_event(
        self, market_processor, timestamp, price, volume, order_id, order_type=None
    ):
        pass

    def cancel_quote_event(
        self, market_processor, timestamp, volume, order_id, order_type=None
    ):
        pass

    def delete_quote_event(
        self, market_processor, timestamp, order_id, order_type=None
    ):
        pass

    def replace_quote_event(
        self,
        market_processor,
        timestamp,
        orig_order_id,
        new_order_id,
        price,
        volume,
        order_type=None,
    ):
        pass

    def execute_trade_event(
        self, market_processor, timestamp, volume, order_id, trade_ref, order_type=None
    ):
        pass

    def execute_trade_price_event(
        self,
        market_processor,
        timestamp,
        volume,
        order_id,
        trade_ref,
        price,
        order_type=None,
    ):
        pass

    def auction_trade_event(
        self, market_processor, timestamp, volume, price, bid_id, ask_id
    ):
        pass

    def crossing_trade_event(
        self, market_processor, timestamp, volume, price, bid_id, ask_id
    ):
        pass
