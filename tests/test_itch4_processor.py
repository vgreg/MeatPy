"""Tests for ITCH 4.0 market processor functionality."""

import datetime
import pytest

from meatpy.itch4.itch4_market_processor import (
    ITCH4MarketProcessor,
    InvalidBuySellIndicatorError,
    InvalidTradingStatusError,
)
from meatpy.itch4.itch4_market_message import (
    SecondsMessage,
    SystemEventMessage,
    StockTradingActionMessage,
    AddOrderMessage,
    AddOrderMPIDMessage,
    OrderExecutedMessage,
    OrderExecutedPriceMessage,
    OrderCancelMessage,
    OrderDeleteMessage,
    OrderReplaceMessage,
    TradeMessage,
)
from meatpy.lob import OrderType
from meatpy.trading_status import (
    PreTradeTradingStatus,
    TradeTradingStatus,
    PostTradeTradingStatus,
    HaltedTradingStatus,
    QuoteOnlyTradingStatus,
)


class TestITCH4MarketProcessor:
    """Test the ITCH4MarketProcessor class."""

    def test_init(self):
        """Test processor initialization."""
        book_date = datetime.datetime(2023, 1, 15)
        processor = ITCH4MarketProcessor("AAPL", book_date)

        assert processor.instrument == "AAPL"
        assert processor.book_date == book_date
        assert processor.lob is None
        assert processor.current_second == 0

    def test_adjust_timestamp(self):
        """Test timestamp adjustment from seconds + nanoseconds."""
        book_date = datetime.datetime(2023, 1, 15)
        processor = ITCH4MarketProcessor("AAPL", book_date)

        # 36000 seconds = 10 hours, 500000000 nanoseconds = 0.5 seconds
        timestamp = processor.adjust_timestamp(36000, 500000000)

        # Should be book_date + 36000.5 seconds
        # Timestamp extends datetime, so compare directly
        expected = book_date + datetime.timedelta(seconds=36000.5)
        assert timestamp.year == expected.year
        assert timestamp.month == expected.month
        assert timestamp.day == expected.day
        assert timestamp.hour == expected.hour
        assert timestamp.minute == expected.minute
        assert timestamp.second == expected.second

    def test_process_seconds_message(self):
        """Test processing seconds message."""
        book_date = datetime.datetime(2023, 1, 15)
        processor = ITCH4MarketProcessor("AAPL", book_date)

        message = SecondsMessage()
        message.seconds = 36000

        processor.process_message(message)

        assert processor.current_second == 36000

    def test_process_system_event_start_messages(self):
        """Test processing system event message - start of messages."""
        book_date = datetime.datetime(2023, 1, 15)
        processor = ITCH4MarketProcessor("AAPL", book_date)

        message = SystemEventMessage()
        message.timestamp = 0
        message.event_code = b"O"

        processor.process_message(message)

        assert processor.system_status == b"O"
        assert processor.trading_status == PostTradeTradingStatus

    def test_process_system_event_start_system(self):
        """Test processing system event message - start of system hours."""
        book_date = datetime.datetime(2023, 1, 15)
        processor = ITCH4MarketProcessor("AAPL", book_date)

        message = SystemEventMessage()
        message.timestamp = 0
        message.event_code = b"S"

        processor.process_message(message)

        assert processor.system_status == b"S"
        assert processor.trading_status == PreTradeTradingStatus

    def test_process_stock_trading_action(self):
        """Test processing stock trading action message."""
        book_date = datetime.datetime(2023, 1, 15)
        processor = ITCH4MarketProcessor("AAPL", book_date)

        # Start market first
        sys_msg = SystemEventMessage()
        sys_msg.timestamp = 0
        sys_msg.event_code = b"Q"
        processor.process_message(sys_msg)

        # Then set stock trading status
        action_msg = StockTradingActionMessage()
        action_msg.timestamp = 0
        action_msg.stock = b"AAPL  "
        action_msg.state = b"T"
        action_msg.reserved = b"     "
        processor.process_message(action_msg)

        assert processor.stock_status == b"T"
        assert processor.trading_status == TradeTradingStatus

    def test_process_stock_trading_action_halted(self):
        """Test processing stock trading action message - halted."""
        book_date = datetime.datetime(2023, 1, 15)
        processor = ITCH4MarketProcessor("AAPL", book_date)

        # Start market
        sys_msg = SystemEventMessage()
        sys_msg.timestamp = 0
        sys_msg.event_code = b"Q"
        processor.process_message(sys_msg)

        # Set stock as halted
        action_msg = StockTradingActionMessage()
        action_msg.timestamp = 0
        action_msg.stock = b"AAPL  "
        action_msg.state = b"H"
        action_msg.reserved = b"     "
        processor.process_message(action_msg)

        assert processor.stock_status == b"H"
        assert processor.trading_status == HaltedTradingStatus

    def test_process_stock_trading_action_quote_only(self):
        """Test processing stock trading action message - quote only."""
        book_date = datetime.datetime(2023, 1, 15)
        processor = ITCH4MarketProcessor("AAPL", book_date)

        # Start market
        sys_msg = SystemEventMessage()
        sys_msg.timestamp = 0
        sys_msg.event_code = b"Q"
        processor.process_message(sys_msg)

        # Set stock as quote only
        action_msg = StockTradingActionMessage()
        action_msg.timestamp = 0
        action_msg.stock = b"AAPL  "
        action_msg.state = b"Q"
        action_msg.reserved = b"     "
        processor.process_message(action_msg)

        assert processor.stock_status == b"Q"
        assert processor.trading_status == QuoteOnlyTradingStatus

    def test_process_stock_trading_action_different_stock(self):
        """Test that trading actions for different stocks are ignored."""
        book_date = datetime.datetime(2023, 1, 15)
        processor = ITCH4MarketProcessor("AAPL", book_date)

        action_msg = StockTradingActionMessage()
        action_msg.timestamp = 0
        action_msg.stock = b"MSFT  "
        action_msg.state = b"T"
        action_msg.reserved = b"     "
        processor.process_message(action_msg)

        # Stock status should remain empty
        assert processor.stock_status == b""

    def test_process_add_order_buy(self):
        """Test processing add order message - buy side."""
        book_date = datetime.datetime(2023, 1, 15)
        processor = ITCH4MarketProcessor("AAPL", book_date)

        message = AddOrderMessage()
        message.timestamp = 12345
        message.order_ref = 1
        message.side = b"B"
        message.shares = 100
        message.stock = b"AAPL  "
        message.price = 150000

        processor.process_message(message)

        assert processor.lob is not None
        order_type = processor.lob.find_order_type(1)
        assert order_type == OrderType.BID

    def test_process_add_order_sell(self):
        """Test processing add order message - sell side."""
        book_date = datetime.datetime(2023, 1, 15)
        processor = ITCH4MarketProcessor("AAPL", book_date)

        message = AddOrderMessage()
        message.timestamp = 12345
        message.order_ref = 2
        message.side = b"S"
        message.shares = 200
        message.stock = b"AAPL  "
        message.price = 151000

        processor.process_message(message)

        assert processor.lob is not None
        order_type = processor.lob.find_order_type(2)
        assert order_type == OrderType.ASK

    def test_process_add_order_invalid_side(self):
        """Test processing add order with invalid side."""
        book_date = datetime.datetime(2023, 1, 15)
        processor = ITCH4MarketProcessor("AAPL", book_date)

        message = AddOrderMessage()
        message.timestamp = 12345
        message.order_ref = 1
        message.side = b"X"  # Invalid side
        message.shares = 100
        message.stock = b"AAPL  "
        message.price = 150000

        with pytest.raises(InvalidBuySellIndicatorError):
            processor.process_message(message)

    def test_process_add_order_different_instrument(self):
        """Test that orders for different instruments are ignored."""
        book_date = datetime.datetime(2023, 1, 15)
        processor = ITCH4MarketProcessor("AAPL", book_date)

        message = AddOrderMessage()
        message.timestamp = 12345
        message.order_ref = 1
        message.side = b"B"
        message.shares = 100
        message.stock = b"MSFT  "
        message.price = 150000

        processor.process_message(message)

        assert processor.lob is None

    def test_process_add_order_mpid(self):
        """Test processing add order with MPID message."""
        book_date = datetime.datetime(2023, 1, 15)
        processor = ITCH4MarketProcessor("AAPL", book_date)

        message = AddOrderMPIDMessage()
        message.timestamp = 12345
        message.order_ref = 1
        message.side = b"B"
        message.shares = 100
        message.stock = b"AAPL  "
        message.price = 150000
        message.mpid = b"ABCD"

        processor.process_message(message)

        assert processor.lob is not None
        order_type = processor.lob.find_order_type(1)
        assert order_type == OrderType.BID

    def test_process_add_order_mpid_invalid_side(self):
        """Test processing add order MPID with invalid side."""
        book_date = datetime.datetime(2023, 1, 15)
        processor = ITCH4MarketProcessor("AAPL", book_date)

        message = AddOrderMPIDMessage()
        message.timestamp = 12345
        message.order_ref = 1
        message.side = b"X"  # Invalid side
        message.shares = 100
        message.stock = b"AAPL  "
        message.price = 150000
        message.mpid = b"ABCD"

        with pytest.raises(InvalidBuySellIndicatorError):
            processor.process_message(message)

    def test_process_order_executed(self):
        """Test processing order executed message."""
        book_date = datetime.datetime(2023, 1, 15)
        processor = ITCH4MarketProcessor("AAPL", book_date)

        # First add an order
        add_msg = AddOrderMessage()
        add_msg.timestamp = 12345
        add_msg.order_ref = 1
        add_msg.side = b"B"
        add_msg.shares = 100
        add_msg.stock = b"AAPL  "
        add_msg.price = 150000
        processor.process_message(add_msg)

        # Then execute part of it
        exec_msg = OrderExecutedMessage()
        exec_msg.timestamp = 12346
        exec_msg.order_ref = 1
        exec_msg.shares = 50
        exec_msg.match_number = 123
        processor.process_message(exec_msg)

    def test_process_order_executed_price(self):
        """Test processing order executed with price message."""
        book_date = datetime.datetime(2023, 1, 15)
        processor = ITCH4MarketProcessor("AAPL", book_date)

        # First add an order
        add_msg = AddOrderMessage()
        add_msg.timestamp = 12345
        add_msg.order_ref = 1
        add_msg.side = b"B"
        add_msg.shares = 100
        add_msg.stock = b"AAPL  "
        add_msg.price = 150000
        processor.process_message(add_msg)

        # Then execute with different price
        exec_msg = OrderExecutedPriceMessage()
        exec_msg.timestamp = 12346
        exec_msg.order_ref = 1
        exec_msg.shares = 50
        exec_msg.match_number = 123
        exec_msg.printable = b"Y"
        exec_msg.price = 149500
        processor.process_message(exec_msg)

    def test_process_order_cancel(self):
        """Test processing order cancel message."""
        book_date = datetime.datetime(2023, 1, 15)
        processor = ITCH4MarketProcessor("AAPL", book_date)

        # First add an order
        add_msg = AddOrderMessage()
        add_msg.timestamp = 12345
        add_msg.order_ref = 1
        add_msg.side = b"B"
        add_msg.shares = 100
        add_msg.stock = b"AAPL  "
        add_msg.price = 150000
        processor.process_message(add_msg)

        # Then cancel part of it
        cancel_msg = OrderCancelMessage()
        cancel_msg.timestamp = 12346
        cancel_msg.order_ref = 1
        cancel_msg.shares = 25
        processor.process_message(cancel_msg)

    def test_process_order_delete(self):
        """Test processing order delete message."""
        book_date = datetime.datetime(2023, 1, 15)
        processor = ITCH4MarketProcessor("AAPL", book_date)

        # First add an order
        add_msg = AddOrderMessage()
        add_msg.timestamp = 12345
        add_msg.order_ref = 1
        add_msg.side = b"B"
        add_msg.shares = 100
        add_msg.stock = b"AAPL  "
        add_msg.price = 150000
        processor.process_message(add_msg)

        # Then delete it
        delete_msg = OrderDeleteMessage()
        delete_msg.timestamp = 12346
        delete_msg.order_ref = 1
        processor.process_message(delete_msg)

    def test_process_order_replace(self):
        """Test processing order replace message."""
        book_date = datetime.datetime(2023, 1, 15)
        processor = ITCH4MarketProcessor("AAPL", book_date)

        # First add an order
        add_msg = AddOrderMessage()
        add_msg.timestamp = 12345
        add_msg.order_ref = 1
        add_msg.side = b"B"
        add_msg.shares = 100
        add_msg.stock = b"AAPL  "
        add_msg.price = 150000
        processor.process_message(add_msg)

        # Then replace it
        replace_msg = OrderReplaceMessage()
        replace_msg.timestamp = 12346
        replace_msg.original_ref = 1
        replace_msg.new_ref = 2
        replace_msg.shares = 150
        replace_msg.price = 151000
        processor.process_message(replace_msg)

        # New order should exist
        assert processor.lob is not None
        order_type = processor.lob.find_order_type(2)
        assert order_type == OrderType.BID

    def test_process_trade_message(self):
        """Test processing trade message (hidden order)."""
        book_date = datetime.datetime(2023, 1, 15)
        processor = ITCH4MarketProcessor("AAPL", book_date)

        message = TradeMessage()
        message.timestamp = 12345
        message.order_ref = 999
        message.side = b"S"
        message.shares = 50
        message.stock = b"AAPL  "
        message.price = 150000
        message.match_number = 123
        processor.process_message(message)  # Should not raise

    def test_process_wrong_message_type(self):
        """Test that wrong message type raises TypeError."""
        book_date = datetime.datetime(2023, 1, 15)
        processor = ITCH4MarketProcessor("AAPL", book_date)

        with pytest.raises(TypeError):
            processor.process_message("not a message")  # type: ignore

    def test_instrument_bytes(self):
        """Test processor with bytes instrument."""
        book_date = datetime.datetime(2023, 1, 15)
        processor = ITCH4MarketProcessor(b"AAPL  ", book_date)

        message = AddOrderMessage()
        message.timestamp = 12345
        message.order_ref = 1
        message.side = b"B"
        message.shares = 100
        message.stock = b"AAPL  "
        message.price = 150000

        processor.process_message(message)

        assert processor.lob is not None

    def test_trading_status_unknown_raises_error(self):
        """Test that unknown trading status raises error."""
        book_date = datetime.datetime(2023, 1, 15)
        processor = ITCH4MarketProcessor("AAPL", book_date)

        # Set an invalid system status
        processor.system_status = b"X"  # Unknown

        with pytest.raises(InvalidTradingStatusError):
            processor._determine_trading_status()
