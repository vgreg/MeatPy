"""Tests for the market processor module."""

from datetime import date, datetime
from unittest.mock import Mock

from meatpy.lob import LimitOrderBook, OrderType
from meatpy.market_event_handler import MarketEventHandler
from meatpy.market_processor import MarketProcessor
from meatpy.message_parser import MarketMessage
from meatpy.timestamp import Timestamp
from meatpy.types import OrderID, Price, TradeRef, Volume


class ConcreteMarketProcessor(MarketProcessor[Price, Volume, OrderID, TradeRef, dict]):
    """Concrete implementation of MarketProcessor for testing."""

    def process_message(self, message: MarketMessage) -> None:
        """Process a market message."""
        pass


class TestMarketProcessorInitialization:
    """Test market processor initialization."""

    def test_init_with_string_instrument(self):
        """Test initialization with string instrument."""
        processor = ConcreteMarketProcessor("AAPL", date(2024, 1, 1))
        assert processor.instrument == "AAPL"
        assert processor.book_date == date(2024, 1, 1)
        assert processor.current_lob is None
        assert processor.track_lob is True
        assert processor.handlers == []
        assert processor.trading_status is None

    def test_init_with_bytes_instrument(self):
        """Test initialization with bytes instrument."""
        processor = ConcreteMarketProcessor(b"AAPL", date(2024, 1, 1))
        assert processor.instrument == b"AAPL"

    def test_init_with_datetime_book_date(self):
        """Test initialization with datetime book date."""
        dt = datetime(2024, 1, 1, 9, 30, 0)
        processor = ConcreteMarketProcessor("AAPL", dt)
        assert processor.book_date == dt

    def test_init_with_none_book_date(self):
        """Test initialization with None book date."""
        processor = ConcreteMarketProcessor("AAPL", None)
        assert processor.book_date is None

    def test_default_attributes(self):
        """Test default attribute values."""
        processor = ConcreteMarketProcessor("AAPL", date(2024, 1, 1))
        assert processor.current_lob is None
        assert processor.track_lob is True
        assert processor.handlers == []
        assert processor.trading_status is None


class TestMarketProcessorEventHandling:
    """Test market processor event handling methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.processor = ConcreteMarketProcessor("AAPL", date(2024, 1, 1))
        self.handler = Mock(spec=MarketEventHandler)
        self.processor.handlers = [self.handler]
        self.timestamp = Timestamp(2024, 1, 1, 9, 30, 0)
        self.lob = Mock(spec=LimitOrderBook)
        self.lob.timestamp = self.timestamp
        self.lob.timestamp_inc = 0
        self.processor.current_lob = self.lob

    def test_before_lob_update(self):
        """Test before_lob_update method."""
        self.processor.before_lob_update(self.timestamp)
        self.handler.before_lob_update.assert_called_once_with(self.lob, self.timestamp)

    def test_before_lob_update_with_no_lob(self):
        """Test before_lob_update method with no LOB."""
        self.processor.current_lob = None
        self.processor.before_lob_update(self.timestamp)
        self.handler.before_lob_update.assert_called_once_with(None, self.timestamp)

    def test_message_event(self):
        """Test message_event method."""
        message = Mock(spec=MarketMessage)
        self.processor.message_event(self.timestamp, message)
        self.handler.message_event.assert_called_once_with(
            self.processor, self.timestamp, message
        )

    def test_enter_quote_event(self):
        """Test enter_quote_event method."""
        price = 100
        volume = 1000
        order_id = 12345
        order_type = OrderType.BID

        self.processor.enter_quote_event(
            self.timestamp, price, volume, order_id, order_type
        )
        self.handler.enter_quote_event.assert_called_once_with(
            self.processor, self.timestamp, price, volume, order_id, order_type
        )

    def test_enter_quote_event_without_order_type(self):
        """Test enter_quote_event method without order type."""
        price = 100
        volume = 1000
        order_id = 12345

        self.processor.enter_quote_event(self.timestamp, price, volume, order_id)
        self.handler.enter_quote_event.assert_called_once_with(
            self.processor, self.timestamp, price, volume, order_id, None
        )

    def test_cancel_quote_event(self):
        """Test cancel_quote_event method."""
        volume = 500
        order_id = 12345
        order_type = OrderType.ASK

        self.processor.cancel_quote_event(self.timestamp, volume, order_id, order_type)
        self.handler.cancel_quote_event.assert_called_once_with(
            self.processor, self.timestamp, volume, order_id, order_type
        )

    def test_delete_quote_event(self):
        """Test delete_quote_event method."""
        order_id = 12345
        order_type = OrderType.BID

        self.processor.delete_quote_event(self.timestamp, order_id, order_type)
        self.handler.delete_quote_event.assert_called_once_with(
            self.processor, self.timestamp, order_id, order_type
        )

    def test_replace_quote_event(self):
        """Test replace_quote_event method."""
        orig_order_id = 12345
        new_order_id = 12346
        price = 101
        volume = 1000
        order_type = OrderType.ASK

        self.processor.replace_quote_event(
            self.timestamp, orig_order_id, new_order_id, price, volume, order_type
        )
        self.handler.replace_quote_event.assert_called_once_with(
            self.processor,
            self.timestamp,
            orig_order_id,
            new_order_id,
            price,
            volume,
            order_type,
        )

    def test_execute_trade_event(self):
        """Test execute_trade_event method."""
        volume = 100
        order_id = 12345
        trade_ref = 67890
        order_type = OrderType.BID

        self.processor.execute_trade_event(
            self.timestamp, volume, order_id, trade_ref, order_type
        )
        self.handler.execute_trade_event.assert_called_once_with(
            self.processor, self.timestamp, volume, order_id, trade_ref, order_type
        )

    def test_execute_trade_price_event(self):
        """Test execute_trade_price_event method."""
        volume = 100
        order_id = 12345
        trade_ref = 67890
        price = 100
        order_type = OrderType.ASK

        self.processor.execute_trade_price_event(
            self.timestamp, volume, order_id, trade_ref, price, order_type
        )
        self.handler.execute_trade_price_event.assert_called_once_with(
            self.processor,
            self.timestamp,
            volume,
            order_id,
            trade_ref,
            price,
            order_type,
        )

    def test_auction_trade_event(self):
        """Test auction_trade_event method."""
        volume = 100
        price = 100
        bid_id = 12345
        ask_id = 12346

        self.processor.auction_trade_event(
            self.timestamp, volume, price, bid_id, ask_id
        )
        self.handler.auction_trade_event.assert_called_once_with(
            self.processor, self.timestamp, volume, price, bid_id, ask_id
        )

    def test_crossing_trade_event(self):
        """Test crossing_trade_event method."""
        volume = 100
        price = 100
        bid_id = 12345
        ask_id = 12346

        self.processor.crossing_trade_event(
            self.timestamp, volume, price, bid_id, ask_id
        )
        self.handler.crossing_trade_event.assert_called_once_with(
            self.processor, self.timestamp, volume, price, bid_id, ask_id
        )

    def test_pre_lob_event(self):
        """Test pre_lob_event method."""
        self.processor.pre_lob_event(self.timestamp)
        # This method should call before_lob_update on handlers
        self.handler.before_lob_update.assert_called_once_with(self.lob, self.timestamp)

    def test_pre_lob_event_with_new_snapshot(self):
        """Test pre_lob_event method with new snapshot flag."""
        self.processor.pre_lob_event(self.timestamp, new_snapshot=True)
        self.handler.before_lob_update.assert_called_once_with(self.lob, self.timestamp)


class TestMarketProcessorCleanup:
    """Test market processor cleanup methods."""

    def test_processing_done_with_lob(self):
        """Test processing_done method with LOB."""
        processor = ConcreteMarketProcessor("AAPL", date(2024, 1, 1))
        lob = Mock(spec=LimitOrderBook)
        processor.current_lob = lob

        processor.processing_done()
        lob.end_of_day.assert_called_once()

    def test_processing_done_without_lob(self):
        """Test processing_done method without LOB."""
        processor = ConcreteMarketProcessor("AAPL", date(2024, 1, 1))
        processor.current_lob = None

        # Should not raise an exception
        processor.processing_done()


class TestMarketProcessorMultipleHandlers:
    """Test market processor with multiple handlers."""

    def test_multiple_handlers(self):
        """Test that all handlers are notified."""
        processor = ConcreteMarketProcessor("AAPL", date(2024, 1, 1))
        handler1 = Mock(spec=MarketEventHandler)
        handler2 = Mock(spec=MarketEventHandler)
        processor.handlers = [handler1, handler2]

        timestamp = Timestamp(2024, 1, 1, 9, 30, 0)
        message = Mock(spec=MarketMessage)

        processor.message_event(timestamp, message)

        handler1.message_event.assert_called_once_with(processor, timestamp, message)
        handler2.message_event.assert_called_once_with(processor, timestamp, message)


class TestMarketProcessorAbstractMethods:
    """Test market processor abstract methods."""

    def test_process_message_abstract(self):
        """Test that process_message is abstract."""
        # MarketProcessor is abstract, but Python's ABC doesn't prevent instantiation
        # unless the abstract method is called. We test that the method exists but
        # raises NotImplementedError when called.
        processor = ConcreteMarketProcessor("AAPL", date(2024, 1, 1))
        # The concrete implementation should not raise an error
        processor.process_message(Mock(spec=MarketMessage))


class TestMarketProcessorTypeSafety:
    """Test market processor type safety."""

    def test_generic_type_parameters(self):
        """Test that generic type parameters work correctly."""
        # This should work without type errors
        processor = ConcreteMarketProcessor("AAPL", date(2024, 1, 1))
        assert isinstance(processor, MarketProcessor)

    def test_type_consistency(self):
        """Test that types are consistent within a processor instance."""
        processor = ConcreteMarketProcessor("AAPL", date(2024, 1, 1))

        # Test with consistent types
        price: Price = 100
        volume: Volume = 1000
        order_id: OrderID = 12345
        trade_ref: TradeRef = 67890

        # These should work without type errors
        processor.enter_quote_event(
            Timestamp(2024, 1, 1, 9, 30, 0), price, volume, order_id
        )
        processor.execute_trade_event(
            Timestamp(2024, 1, 1, 9, 30, 0), volume, order_id, trade_ref
        )
