"""Tests for ITCH 2.0 market processor functionality."""

import datetime
import pytest

from meatpy.itch2.itch2_market_processor import (
    ITCH2MarketProcessor,
    InvalidBuySellIndicatorError,
)
from meatpy.itch2.itch2_market_message import (
    SystemEventMessage,
    AddOrderMessage,
    OrderExecutedMessage,
    OrderCancelMessage,
    TradeMessage,
    BrokenTradeMessage,
)
from meatpy.lob import OrderType
from meatpy.trading_status import (
    PreTradeTradingStatus,
    TradeTradingStatus,
    PostTradeTradingStatus,
)


class TestITCH2MarketProcessor:
    """Test the ITCH2MarketProcessor class."""

    def test_init(self):
        """Test processor initialization."""
        book_date = datetime.datetime(2023, 1, 15)
        processor = ITCH2MarketProcessor("AAPL", book_date)

        assert processor.instrument == "AAPL"
        assert processor.book_date == book_date
        assert processor.lob is None

    def test_adjust_timestamp(self):
        """Test timestamp adjustment from milliseconds."""
        book_date = datetime.datetime(2023, 1, 15)
        processor = ITCH2MarketProcessor("AAPL", book_date)

        # 12345678 milliseconds = 12345.678 seconds = ~3 hours 25 minutes 45.678 seconds
        timestamp = processor.adjust_timestamp(12345678)

        # Should be book_date + 12345678 milliseconds
        # Timestamp extends datetime, so compare directly
        expected = book_date + datetime.timedelta(milliseconds=12345678)
        assert timestamp.year == expected.year
        assert timestamp.month == expected.month
        assert timestamp.day == expected.day
        assert timestamp.hour == expected.hour
        assert timestamp.minute == expected.minute
        assert timestamp.second == expected.second

    def test_process_system_event_start_messages(self):
        """Test processing system event message - start of messages."""
        book_date = datetime.datetime(2023, 1, 15)
        processor = ITCH2MarketProcessor("AAPL", book_date)

        message = SystemEventMessage()
        message.timestamp = 12345678
        message.event_code = b"O"

        processor.process_message(message)

        assert processor.system_status == b"O"
        assert processor.trading_status == PostTradeTradingStatus

    def test_process_system_event_start_market(self):
        """Test processing system event message - start of market hours."""
        book_date = datetime.datetime(2023, 1, 15)
        processor = ITCH2MarketProcessor("AAPL", book_date)

        message = SystemEventMessage()
        message.timestamp = 12345678
        message.event_code = b"Q"

        processor.process_message(message)

        assert processor.system_status == b"Q"
        assert processor.trading_status == TradeTradingStatus

    def test_process_system_event_start_system(self):
        """Test processing system event message - start of system hours."""
        book_date = datetime.datetime(2023, 1, 15)
        processor = ITCH2MarketProcessor("AAPL", book_date)

        message = SystemEventMessage()
        message.timestamp = 12345678
        message.event_code = b"S"

        processor.process_message(message)

        assert processor.system_status == b"S"
        assert processor.trading_status == PreTradeTradingStatus

    def test_process_add_order_buy(self):
        """Test processing add order message - buy side."""
        book_date = datetime.datetime(2023, 1, 15)
        processor = ITCH2MarketProcessor("AAPL", book_date)

        message = AddOrderMessage()
        message.timestamp = 12345678
        message.order_ref = 1
        message.side = b"B"
        message.shares = 100
        message.stock = b"AAPL  "
        message.price = 150000
        message.display = b"Y"

        processor.process_message(message)

        assert processor.lob is not None
        order_type = processor.lob.find_order_type(1)
        assert order_type == OrderType.BID

    def test_process_add_order_sell(self):
        """Test processing add order message - sell side."""
        book_date = datetime.datetime(2023, 1, 15)
        processor = ITCH2MarketProcessor("AAPL", book_date)

        message = AddOrderMessage()
        message.timestamp = 12345678
        message.order_ref = 2
        message.side = b"S"
        message.shares = 200
        message.stock = b"AAPL  "
        message.price = 151000
        message.display = b"Y"

        processor.process_message(message)

        assert processor.lob is not None
        order_type = processor.lob.find_order_type(2)
        assert order_type == OrderType.ASK

    def test_process_add_order_invalid_side(self):
        """Test processing add order with invalid side."""
        book_date = datetime.datetime(2023, 1, 15)
        processor = ITCH2MarketProcessor("AAPL", book_date)

        message = AddOrderMessage()
        message.timestamp = 12345678
        message.order_ref = 1
        message.side = b"X"  # Invalid side
        message.shares = 100
        message.stock = b"AAPL  "
        message.price = 150000
        message.display = b"Y"

        with pytest.raises(InvalidBuySellIndicatorError):
            processor.process_message(message)

    def test_process_add_order_different_instrument(self):
        """Test that orders for different instruments are ignored."""
        book_date = datetime.datetime(2023, 1, 15)
        processor = ITCH2MarketProcessor("AAPL", book_date)

        message = AddOrderMessage()
        message.timestamp = 12345678
        message.order_ref = 1
        message.side = b"B"
        message.shares = 100
        message.stock = b"MSFT  "  # Different instrument
        message.price = 150000
        message.display = b"Y"

        processor.process_message(message)

        # LOB should not be created for different instrument
        assert processor.lob is None

    def test_process_order_executed(self):
        """Test processing order executed message."""
        book_date = datetime.datetime(2023, 1, 15)
        processor = ITCH2MarketProcessor("AAPL", book_date)

        # First add an order
        add_msg = AddOrderMessage()
        add_msg.timestamp = 12345678
        add_msg.order_ref = 1
        add_msg.side = b"B"
        add_msg.shares = 100
        add_msg.stock = b"AAPL  "
        add_msg.price = 150000
        add_msg.display = b"Y"
        processor.process_message(add_msg)

        # Then execute part of it
        exec_msg = OrderExecutedMessage()
        exec_msg.timestamp = 12345679
        exec_msg.order_ref = 1
        exec_msg.shares = 50
        exec_msg.match_number = 123
        processor.process_message(exec_msg)

        # Order should still exist with reduced quantity
        assert processor.lob is not None

    def test_process_order_executed_unknown_order(self):
        """Test processing order executed for unknown order."""
        book_date = datetime.datetime(2023, 1, 15)
        processor = ITCH2MarketProcessor("AAPL", book_date)

        # Create LOB first
        add_msg = AddOrderMessage()
        add_msg.timestamp = 12345678
        add_msg.order_ref = 1
        add_msg.side = b"B"
        add_msg.shares = 100
        add_msg.stock = b"AAPL  "
        add_msg.price = 150000
        add_msg.display = b"Y"
        processor.process_message(add_msg)

        # Try to execute unknown order - should not raise
        exec_msg = OrderExecutedMessage()
        exec_msg.timestamp = 12345679
        exec_msg.order_ref = 999  # Unknown order
        exec_msg.shares = 50
        exec_msg.match_number = 123
        processor.process_message(exec_msg)  # Should not raise

    def test_process_order_cancel(self):
        """Test processing order cancel message."""
        book_date = datetime.datetime(2023, 1, 15)
        processor = ITCH2MarketProcessor("AAPL", book_date)

        # First add an order
        add_msg = AddOrderMessage()
        add_msg.timestamp = 12345678
        add_msg.order_ref = 1
        add_msg.side = b"B"
        add_msg.shares = 100
        add_msg.stock = b"AAPL  "
        add_msg.price = 150000
        add_msg.display = b"Y"
        processor.process_message(add_msg)

        # Then cancel part of it
        cancel_msg = OrderCancelMessage()
        cancel_msg.timestamp = 12345679
        cancel_msg.order_ref = 1
        cancel_msg.shares = 25
        processor.process_message(cancel_msg)

        # Order should still exist
        assert processor.lob is not None

    def test_process_trade_message(self):
        """Test processing trade message (hidden order)."""
        book_date = datetime.datetime(2023, 1, 15)
        processor = ITCH2MarketProcessor("AAPL", book_date)

        # First add an order to create LOB
        add_msg = AddOrderMessage()
        add_msg.timestamp = 12345678
        add_msg.order_ref = 1
        add_msg.side = b"B"
        add_msg.shares = 100
        add_msg.stock = b"AAPL  "
        add_msg.price = 150000
        add_msg.display = b"Y"
        processor.process_message(add_msg)

        # Trade message for hidden order
        trade_msg = TradeMessage()
        trade_msg.timestamp = 12345679
        trade_msg.order_ref = 999
        trade_msg.side = b"S"
        trade_msg.shares = 50
        trade_msg.stock = b"AAPL  "
        trade_msg.price = 150000
        trade_msg.match_number = 123
        processor.process_message(trade_msg)  # Should not affect LOB

    def test_process_broken_trade_message(self):
        """Test processing broken trade message."""
        book_date = datetime.datetime(2023, 1, 15)
        processor = ITCH2MarketProcessor("AAPL", book_date)

        broken_msg = BrokenTradeMessage()
        broken_msg.timestamp = 12345679
        broken_msg.match_number = 123
        processor.process_message(broken_msg)  # Should not raise

    def test_process_wrong_message_type(self):
        """Test that wrong message type raises TypeError."""
        book_date = datetime.datetime(2023, 1, 15)
        processor = ITCH2MarketProcessor("AAPL", book_date)

        with pytest.raises(TypeError):
            processor.process_message("not a message")  # type: ignore

    def test_instrument_bytes(self):
        """Test processor with bytes instrument."""
        book_date = datetime.datetime(2023, 1, 15)
        processor = ITCH2MarketProcessor(b"AAPL  ", book_date)

        message = AddOrderMessage()
        message.timestamp = 12345678
        message.order_ref = 1
        message.side = b"B"
        message.shares = 100
        message.stock = b"AAPL  "
        message.price = 150000
        message.display = b"Y"

        processor.process_message(message)

        assert processor.lob is not None
