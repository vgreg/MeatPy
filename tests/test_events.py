"""Tests for the events module."""

from meatpy.events import (
    BaseEventHandler,
    MarketEventHandler,
)
from meatpy.lob import LimitOrderBook, OrderType
from meatpy.market_processor import MarketProcessor
from meatpy.message_parser import MarketMessage
from meatpy.timestamp import Timestamp


class TestMarketEventHandler:
    """Test MarketEventHandler protocol."""

    def test_protocol_definition(self):
        """Test that MarketEventHandler is a runtime checkable protocol."""
        assert hasattr(MarketEventHandler, "__runtime_checkable__")
        assert MarketEventHandler.__runtime_checkable__ is True


class TestBaseEventHandler:
    """Test BaseEventHandler class."""

    def test_initialization(self):
        """Test BaseEventHandler initialization."""
        handler = BaseEventHandler()
        assert handler is not None

    def test_before_lob_update(self):
        """Test before_lob_update method."""
        handler = BaseEventHandler()
        lob = LimitOrderBook(Timestamp("2024-01-01 09:30:00"))
        new_timestamp = Timestamp("2024-01-01 09:31:00")

        # Should not raise any exceptions
        handler.before_lob_update(lob, new_timestamp)
        handler.before_lob_update(None, new_timestamp)

    def test_message_event(self):
        """Test message_event method."""
        handler = BaseEventHandler()
        processor = MarketProcessor("AAPL", "2024-01-01")
        timestamp = Timestamp("2024-01-01 09:30:00")
        message = MarketMessage()

        # Should not raise any exceptions
        handler.message_event(processor, timestamp, message)

    def test_enter_quote_event(self):
        """Test enter_quote_event method."""
        handler = BaseEventHandler()
        processor = MarketProcessor("AAPL", "2024-01-01")
        timestamp = Timestamp("2024-01-01 09:30:00")
        price = 10000
        volume = 100
        order_id = 12345

        # Should not raise any exceptions
        handler.enter_quote_event(processor, timestamp, price, volume, order_id)
        handler.enter_quote_event(
            processor, timestamp, price, volume, order_id, OrderType.BID
        )

    def test_cancel_quote_event(self):
        """Test cancel_quote_event method."""
        handler = BaseEventHandler()
        processor = MarketProcessor("AAPL", "2024-01-01")
        timestamp = Timestamp("2024-01-01 09:30:00")
        volume = 50
        order_id = 12345

        # Should not raise any exceptions
        handler.cancel_quote_event(processor, timestamp, volume, order_id)
        handler.cancel_quote_event(
            processor, timestamp, volume, order_id, OrderType.ASK
        )

    def test_delete_quote_event(self):
        """Test delete_quote_event method."""
        handler = BaseEventHandler()
        processor = MarketProcessor("AAPL", "2024-01-01")
        timestamp = Timestamp("2024-01-01 09:30:00")
        order_id = 12345

        # Should not raise any exceptions
        handler.delete_quote_event(processor, timestamp, order_id)
        handler.delete_quote_event(processor, timestamp, order_id, OrderType.BID)

    def test_replace_quote_event(self):
        """Test replace_quote_event method."""
        handler = BaseEventHandler()
        processor = MarketProcessor("AAPL", "2024-01-01")
        timestamp = Timestamp("2024-01-01 09:30:00")
        orig_order_id = 12345
        new_order_id = 12346
        price = 10000
        volume = 100

        # Should not raise any exceptions
        handler.replace_quote_event(
            processor, timestamp, orig_order_id, new_order_id, price, volume
        )
        handler.replace_quote_event(
            processor,
            timestamp,
            orig_order_id,
            new_order_id,
            price,
            volume,
            OrderType.ASK,
        )

    def test_execute_trade_event(self):
        """Test execute_trade_event method."""
        handler = BaseEventHandler()
        processor = MarketProcessor("AAPL", "2024-01-01")
        timestamp = Timestamp("2024-01-01 09:30:00")
        volume = 50
        order_id = 12345
        trade_ref = "trade-123"

        # Should not raise any exceptions
        handler.execute_trade_event(processor, timestamp, volume, order_id, trade_ref)
        handler.execute_trade_event(
            processor, timestamp, volume, order_id, trade_ref, OrderType.BID
        )

    def test_execute_trade_price_event(self):
        """Test execute_trade_price_event method."""
        handler = BaseEventHandler()
        processor = MarketProcessor("AAPL", "2024-01-01")
        timestamp = Timestamp("2024-01-01 09:30:00")
        volume = 50
        order_id = 12345
        trade_ref = "trade-123"
        price = 10000

        # Should not raise any exceptions
        handler.execute_trade_price_event(
            processor, timestamp, volume, order_id, trade_ref, price
        )
        handler.execute_trade_price_event(
            processor, timestamp, volume, order_id, trade_ref, price, OrderType.ASK
        )

    def test_auction_trade_event(self):
        """Test auction_trade_event method."""
        handler = BaseEventHandler()
        processor = MarketProcessor("AAPL", "2024-01-01")
        timestamp = Timestamp("2024-01-01 09:30:00")
        volume = 100
        price = 10000
        bid_id = 12345
        ask_id = 12346

        # Should not raise any exceptions
        handler.auction_trade_event(processor, timestamp, volume, price, bid_id, ask_id)

    def test_crossing_trade_event(self):
        """Test crossing_trade_event method."""
        handler = BaseEventHandler()
        processor = MarketProcessor("AAPL", "2024-01-01")
        timestamp = Timestamp("2024-01-01 09:30:00")
        volume = 100
        price = 10000
        bid_id = 12345
        ask_id = 12346

        # Should not raise any exceptions
        handler.crossing_trade_event(
            processor, timestamp, volume, price, bid_id, ask_id
        )


class TestEventHandlerInheritance:
    """Test event handler inheritance and protocol compliance."""

    def test_base_handler_implements_protocol(self):
        """Test that BaseEventHandler implements MarketEventHandler protocol."""
        handler = BaseEventHandler()
        assert isinstance(handler, MarketEventHandler)

    def test_custom_handler_implements_protocol(self):
        """Test that custom handlers can implement the protocol."""

        class CustomHandler:
            def before_lob_update(self, lob, new_timestamp):
                pass

            def message_event(self, market_processor, timestamp, message):
                pass

            def enter_quote_event(
                self,
                market_processor,
                timestamp,
                price,
                volume,
                order_id,
                order_type=None,
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
                self,
                market_processor,
                timestamp,
                volume,
                order_id,
                trade_ref,
                order_type=None,
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

        handler = CustomHandler()
        assert isinstance(handler, MarketEventHandler)


class TestEventHandlerEdgeCases:
    """Test event handler edge cases."""

    def test_none_values(self):
        """Test event handlers with None values."""
        handler = BaseEventHandler()
        processor = MarketProcessor("AAPL", "2024-01-01")
        timestamp = Timestamp("2024-01-01 09:30:00")

        # Should not raise any exceptions
        handler.before_lob_update(None, timestamp)
        handler.message_event(processor, timestamp, None)

    def test_zero_values(self):
        """Test event handlers with zero values."""
        handler = BaseEventHandler()
        processor = MarketProcessor("AAPL", "2024-01-01")
        timestamp = Timestamp("2024-01-01 09:30:00")

        # Should not raise any exceptions
        handler.enter_quote_event(processor, timestamp, 0, 0, 0)
        handler.cancel_quote_event(processor, timestamp, 0, 0)
        handler.execute_trade_event(processor, timestamp, 0, 0, "trade-0")

    def test_negative_values(self):
        """Test event handlers with negative values."""
        handler = BaseEventHandler()
        processor = MarketProcessor("AAPL", "2024-01-01")
        timestamp = Timestamp("2024-01-01 09:30:00")

        # Should not raise any exceptions
        handler.enter_quote_event(processor, timestamp, -100, -50, -1)
        handler.cancel_quote_event(processor, timestamp, -50, -1)
        handler.execute_trade_event(processor, timestamp, -50, -1, "trade-neg")


class TestEventHandlerPerformance:
    """Test event handler performance."""

    def test_rapid_event_handling(self):
        """Test rapid event handling performance."""
        handler = BaseEventHandler()
        processor = MarketProcessor("AAPL", "2024-01-01")
        timestamp = Timestamp("2024-01-01 09:30:00")

        # Process many events rapidly
        for i in range(1000):
            handler.enter_quote_event(processor, timestamp, 10000 + i, 100, i)
            handler.cancel_quote_event(processor, timestamp, 50, i)
            handler.execute_trade_event(processor, timestamp, 50, i, f"trade-{i}")

    def test_large_volume_handling(self):
        """Test handling of large volume values."""
        handler = BaseEventHandler()
        processor = MarketProcessor("AAPL", "2024-01-01")
        timestamp = Timestamp("2024-01-01 09:30:00")

        # Large volume values
        large_volume = 1000000000
        handler.enter_quote_event(processor, timestamp, 10000, large_volume, 12345)
        handler.cancel_quote_event(processor, timestamp, large_volume, 12345)
        handler.execute_trade_event(
            processor, timestamp, large_volume, 12345, "trade-large"
        )
