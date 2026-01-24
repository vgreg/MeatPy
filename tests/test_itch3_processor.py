"""Tests for ITCH 3.0 market processor functionality."""

import datetime
import pytest

from meatpy.itch3.itch3_market_processor import (
    ITCH3MarketProcessor,
    InvalidBuySellIndicatorError,
)
from meatpy.itch3.itch3_market_message import (
    SecondsMessage,
    MillisecondsMessage,
    SystemEventMessage,
    StockDirectoryMessage,
    StockTradingActionMessage,
    AddOrderMessage,
    AddOrderMPIDMessage,
    OrderExecutedMessage,
    OrderExecutedPriceMessage,
    OrderCancelMessage,
    OrderDeleteMessage,
    TradeMessage,
    CrossTradeMessage,
    BrokenTradeMessage,
    NoiiMessage,
)
from meatpy.lob import OrderType
from meatpy.trading_status import (
    TradeTradingStatus,
    PostTradeTradingStatus,
    HaltedTradingStatus,
    QuoteOnlyTradingStatus,
)


class TestITCH3MarketProcessor:
    """Test the ITCH3MarketProcessor class."""

    def test_init(self):
        """Test processor initialization."""
        book_date = datetime.datetime(2023, 1, 15)
        processor = ITCH3MarketProcessor("AAPL", book_date)

        assert processor.instrument == "AAPL"
        assert processor.book_date == book_date
        assert processor.lob is None
        assert processor.current_second == 0
        assert processor.current_millisecond == 0

    def test_adjust_timestamp(self):
        """Test timestamp adjustment from seconds + milliseconds."""
        book_date = datetime.datetime(2023, 1, 15)
        processor = ITCH3MarketProcessor("AAPL", book_date)

        processor.current_second = 36000  # 10 hours
        processor.current_millisecond = 500

        timestamp = processor.adjust_timestamp()

        # Should be book_date + 36000500 milliseconds
        # Timestamp extends datetime, so compare directly
        expected = book_date + datetime.timedelta(milliseconds=36000500)
        assert timestamp.year == expected.year
        assert timestamp.month == expected.month
        assert timestamp.day == expected.day
        assert timestamp.hour == expected.hour
        assert timestamp.minute == expected.minute
        assert timestamp.second == expected.second

    def test_process_seconds_message(self):
        """Test processing seconds message."""
        book_date = datetime.datetime(2023, 1, 15)
        processor = ITCH3MarketProcessor("AAPL", book_date)

        message = SecondsMessage()
        message.seconds = 36000

        processor.process_message(message)

        assert processor.current_second == 36000

    def test_process_milliseconds_message(self):
        """Test processing milliseconds message."""
        book_date = datetime.datetime(2023, 1, 15)
        processor = ITCH3MarketProcessor("AAPL", book_date)

        message = MillisecondsMessage()
        message.milliseconds = 500

        processor.process_message(message)

        assert processor.current_millisecond == 500

    def test_process_system_event_start_messages(self):
        """Test processing system event message - start of messages."""
        book_date = datetime.datetime(2023, 1, 15)
        processor = ITCH3MarketProcessor("AAPL", book_date)

        message = SystemEventMessage()
        message.event_code = b"O"

        processor.process_message(message)

        assert processor.system_status == b"O"
        assert processor.trading_status == PostTradeTradingStatus

    def test_process_system_event_start_market(self):
        """Test processing system event message - start of market hours."""
        book_date = datetime.datetime(2023, 1, 15)
        processor = ITCH3MarketProcessor("AAPL", book_date)

        # Start system first
        sys_msg = SystemEventMessage()
        sys_msg.event_code = b"Q"
        processor.process_message(sys_msg)

        assert processor.system_status == b"Q"

    def test_process_stock_trading_action(self):
        """Test processing stock trading action message."""
        book_date = datetime.datetime(2023, 1, 15)
        processor = ITCH3MarketProcessor("AAPL", book_date)

        # Start system first
        sys_msg = SystemEventMessage()
        sys_msg.event_code = b"Q"
        processor.process_message(sys_msg)

        # Then set stock trading status
        action_msg = StockTradingActionMessage()
        action_msg.stock = b"AAPL  "
        action_msg.state = b"T"
        action_msg.reserved = b"     "
        processor.process_message(action_msg)

        assert processor.stock_status == b"T"
        assert processor.trading_status == TradeTradingStatus

    def test_process_stock_trading_action_halted(self):
        """Test processing stock trading action message - halted."""
        book_date = datetime.datetime(2023, 1, 15)
        processor = ITCH3MarketProcessor("AAPL", book_date)

        # Start market
        sys_msg = SystemEventMessage()
        sys_msg.event_code = b"Q"
        processor.process_message(sys_msg)

        # Set stock as halted
        action_msg = StockTradingActionMessage()
        action_msg.stock = b"AAPL  "
        action_msg.state = b"H"
        action_msg.reserved = b"     "
        processor.process_message(action_msg)

        assert processor.stock_status == b"H"
        assert processor.trading_status == HaltedTradingStatus

    def test_process_stock_trading_action_quote_only(self):
        """Test processing stock trading action message - quote only."""
        book_date = datetime.datetime(2023, 1, 15)
        processor = ITCH3MarketProcessor("AAPL", book_date)

        # Start market
        sys_msg = SystemEventMessage()
        sys_msg.event_code = b"Q"
        processor.process_message(sys_msg)

        # Set stock as quote only
        action_msg = StockTradingActionMessage()
        action_msg.stock = b"AAPL  "
        action_msg.state = b"Q"
        action_msg.reserved = b"     "
        processor.process_message(action_msg)

        assert processor.stock_status == b"Q"
        assert processor.trading_status == QuoteOnlyTradingStatus

    def test_process_stock_trading_action_different_stock(self):
        """Test that trading actions for different stocks are ignored."""
        book_date = datetime.datetime(2023, 1, 15)
        processor = ITCH3MarketProcessor("AAPL", book_date)

        action_msg = StockTradingActionMessage()
        action_msg.stock = b"MSFT  "
        action_msg.state = b"T"
        action_msg.reserved = b"     "
        processor.process_message(action_msg)

        # Stock status should remain empty
        assert processor.stock_status == b""

    def test_process_stock_directory(self):
        """Test processing stock directory message."""
        book_date = datetime.datetime(2023, 1, 15)
        processor = ITCH3MarketProcessor("AAPL", book_date)

        message = StockDirectoryMessage()
        message.stock = b"AAPL  "
        message.market_category = b"Q"
        message.financial_status = b"N"
        message.round_lot_size = 100
        message.round_lots_only = b"Y"

        # Should not raise
        processor.process_message(message)

    def test_process_add_order_buy(self):
        """Test processing add order message - buy side."""
        book_date = datetime.datetime(2023, 1, 15)
        processor = ITCH3MarketProcessor("AAPL", book_date)

        message = AddOrderMessage()
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
        processor = ITCH3MarketProcessor("AAPL", book_date)

        message = AddOrderMessage()
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
        processor = ITCH3MarketProcessor("AAPL", book_date)

        message = AddOrderMessage()
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
        processor = ITCH3MarketProcessor("AAPL", book_date)

        message = AddOrderMessage()
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
        processor = ITCH3MarketProcessor("AAPL", book_date)

        message = AddOrderMPIDMessage()
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
        processor = ITCH3MarketProcessor("AAPL", book_date)

        message = AddOrderMPIDMessage()
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
        processor = ITCH3MarketProcessor("AAPL", book_date)

        # First add an order
        add_msg = AddOrderMessage()
        add_msg.order_ref = 1
        add_msg.side = b"B"
        add_msg.shares = 100
        add_msg.stock = b"AAPL  "
        add_msg.price = 150000
        processor.process_message(add_msg)

        # Then execute part of it
        exec_msg = OrderExecutedMessage()
        exec_msg.order_ref = 1
        exec_msg.shares = 50
        exec_msg.match_number = 123
        processor.process_message(exec_msg)

    def test_process_order_executed_price(self):
        """Test processing order executed with price message."""
        book_date = datetime.datetime(2023, 1, 15)
        processor = ITCH3MarketProcessor("AAPL", book_date)

        # First add an order
        add_msg = AddOrderMessage()
        add_msg.order_ref = 1
        add_msg.side = b"B"
        add_msg.shares = 100
        add_msg.stock = b"AAPL  "
        add_msg.price = 150000
        processor.process_message(add_msg)

        # Then execute with different price
        exec_msg = OrderExecutedPriceMessage()
        exec_msg.order_ref = 1
        exec_msg.shares = 50
        exec_msg.match_number = 123
        exec_msg.printable = b"Y"
        exec_msg.price = 149500
        processor.process_message(exec_msg)

    def test_process_order_cancel(self):
        """Test processing order cancel message."""
        book_date = datetime.datetime(2023, 1, 15)
        processor = ITCH3MarketProcessor("AAPL", book_date)

        # First add an order
        add_msg = AddOrderMessage()
        add_msg.order_ref = 1
        add_msg.side = b"B"
        add_msg.shares = 100
        add_msg.stock = b"AAPL  "
        add_msg.price = 150000
        processor.process_message(add_msg)

        # Then cancel part of it
        cancel_msg = OrderCancelMessage()
        cancel_msg.order_ref = 1
        cancel_msg.shares = 25
        processor.process_message(cancel_msg)

    def test_process_order_delete(self):
        """Test processing order delete message."""
        book_date = datetime.datetime(2023, 1, 15)
        processor = ITCH3MarketProcessor("AAPL", book_date)

        # First add an order
        add_msg = AddOrderMessage()
        add_msg.order_ref = 1
        add_msg.side = b"B"
        add_msg.shares = 100
        add_msg.stock = b"AAPL  "
        add_msg.price = 150000
        processor.process_message(add_msg)

        # Then delete it
        delete_msg = OrderDeleteMessage()
        delete_msg.order_ref = 1
        processor.process_message(delete_msg)

    def test_process_trade_message(self):
        """Test processing trade message (hidden order)."""
        book_date = datetime.datetime(2023, 1, 15)
        processor = ITCH3MarketProcessor("AAPL", book_date)

        message = TradeMessage()
        message.order_ref = 999
        message.side = b"S"
        message.shares = 50
        message.stock = b"AAPL  "
        message.price = 150000
        message.match_number = 123
        processor.process_message(message)  # Should not raise

    def test_process_cross_trade_message(self):
        """Test processing cross trade message."""
        book_date = datetime.datetime(2023, 1, 15)
        processor = ITCH3MarketProcessor("AAPL", book_date)

        message = CrossTradeMessage()
        message.shares = 1000
        message.stock = b"AAPL  "
        message.price = 150000
        message.match_number = 123
        message.cross_type = b"O"
        processor.process_message(message)  # Should not raise

    def test_process_broken_trade_message(self):
        """Test processing broken trade message."""
        book_date = datetime.datetime(2023, 1, 15)
        processor = ITCH3MarketProcessor("AAPL", book_date)

        message = BrokenTradeMessage()
        message.match_number = 123
        processor.process_message(message)  # Should not raise

    def test_process_noii_message(self):
        """Test processing NOII message."""
        book_date = datetime.datetime(2023, 1, 15)
        processor = ITCH3MarketProcessor("AAPL", book_date)

        message = NoiiMessage()
        message.paired_shares = 10000
        message.imbalance_shares = 5000
        message.imbalance_direction = b"B"
        message.stock = b"AAPL  "
        message.far_price = 150000
        message.near_price = 150000
        message.ref_price = 150000
        message.cross_type = b"OC"
        processor.process_message(message)  # Should not raise

    def test_process_wrong_message_type(self):
        """Test that wrong message type raises TypeError."""
        book_date = datetime.datetime(2023, 1, 15)
        processor = ITCH3MarketProcessor("AAPL", book_date)

        with pytest.raises(TypeError):
            processor.process_message("not a message")  # type: ignore

    def test_instrument_bytes(self):
        """Test processor with bytes instrument."""
        book_date = datetime.datetime(2023, 1, 15)
        processor = ITCH3MarketProcessor(b"AAPL  ", book_date)

        message = AddOrderMessage()
        message.order_ref = 1
        message.side = b"B"
        message.shares = 100
        message.stock = b"AAPL  "
        message.price = 150000

        processor.process_message(message)

        assert processor.lob is not None
