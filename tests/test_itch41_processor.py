"""Tests for ITCH 4.1 market processor functionality."""

import pytest
from datetime import datetime

from meatpy.itch41.itch41_market_processor import ITCH41MarketProcessor
from meatpy.itch41.itch41_market_message import (
    SystemEventMessage,
    StockTradingActionMessage,
    AddOrderMessage,
    OrderExecutedMessage,
    OrderCancelMessage,
    OrderDeleteMessage,
    OrderReplaceMessage,
)
from meatpy.trading_status import (
    PreTradeTradingStatus,
    TradeTradingStatus,
    HaltedTradingStatus,
)


class TestITCH41MarketProcessor:
    """Test the ITCH41MarketProcessor class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.instrument = "AAPL    "
        self.book_date = datetime(2012, 8, 30)
        self.processor = ITCH41MarketProcessor(self.instrument, self.book_date)

    def test_initialization(self):
        """Test processor initialization."""
        assert self.processor.instrument == self.instrument
        assert self.processor.book_date == self.book_date
        assert self.processor.lob is None
        assert self.processor.system_status == b""
        assert self.processor.stock_status == b""

    def test_system_event_processing(self):
        """Test processing system event messages."""
        message = SystemEventMessage()
        message.event_code = b"S"  # Start of System Hours
        message.timestamp = 12345

        self.processor.process_message(message)

        assert self.processor.system_status == b"S"
        assert self.processor.current_timestamp.nanoseconds == 12345

    def test_stock_trading_action_processing(self):
        """Test processing stock trading action messages."""
        # First set system status
        system_msg = SystemEventMessage()
        system_msg.event_code = b"Q"  # Start of Market Hours
        system_msg.timestamp = 12340
        self.processor.process_message(system_msg)

        # Then process stock trading action
        message = StockTradingActionMessage()
        message.stock = b"AAPL    "
        message.state = b"T"  # Trading
        message.timestamp = 12345

        self.processor.process_message(message)

        assert self.processor.stock_status == b"T"

    def test_stock_trading_action_different_stock(self):
        """Test that trading action for different stock is ignored."""
        message = StockTradingActionMessage()
        message.stock = b"MSFT    "  # Different stock
        message.state = b"T"
        message.timestamp = 12345

        initial_status = self.processor.stock_status
        self.processor.process_message(message)

        assert self.processor.stock_status == initial_status  # Should not change

    def test_add_order_buy(self):
        """Test processing add order message for buy side."""
        message = AddOrderMessage()
        message.order_ref = 999
        message.side = b"B"
        message.shares = 100
        message.price = 15000
        message.timestamp = 12345

        self.processor.process_message(message)

        # LOB should be created
        assert self.processor.lob is not None

        # Check that order was added to bid side
        assert len(self.processor.lob.bid_levels) == 1
        assert self.processor.lob.bid_levels[0].price == 15000
        assert self.processor.lob.bid_levels[0].volume == 100

    def test_add_order_sell(self):
        """Test processing add order message for sell side."""
        message = AddOrderMessage()
        message.order_ref = 999
        message.side = b"S"
        message.shares = 50
        message.price = 15100
        message.timestamp = 12345

        self.processor.process_message(message)

        # Check that order was added to ask side
        assert len(self.processor.lob.ask_levels) == 1
        assert self.processor.lob.ask_levels[0].price == 15100
        assert self.processor.lob.ask_levels[0].volume == 50

    def test_add_order_invalid_side(self):
        """Test processing add order with invalid side indicator."""
        message = AddOrderMessage()
        message.order_ref = 999
        message.side = b"X"  # Invalid side
        message.shares = 100
        message.price = 15000
        message.timestamp = 12345

        with pytest.raises(Exception):  # Should raise InvalidBuySellIndicatorError
            self.processor.process_message(message)

    def test_order_execution(self):
        """Test order execution processing."""
        # First add an order
        add_message = AddOrderMessage()
        add_message.order_ref = 999
        add_message.side = b"B"
        add_message.shares = 100
        add_message.price = 15000
        add_message.timestamp = 12345

        self.processor.process_message(add_message)

        # Then execute part of it
        exec_message = OrderExecutedMessage()
        exec_message.order_ref = 999
        exec_message.shares = 30
        exec_message.timestamp = 12346

        self.processor.process_message(exec_message)

        # Check remaining volume
        assert self.processor.lob.bid_levels[0].volume == 70

    def test_order_execution_without_lob(self):
        """Test order execution without LOB raises error."""
        exec_message = OrderExecutedMessage()
        exec_message.order_ref = 999
        exec_message.shares = 30
        exec_message.timestamp = 12345

        with pytest.raises(Exception):  # Should raise MissingLOBError
            self.processor.process_message(exec_message)

    def test_order_execution_missing_order(self):
        """Test order execution for non-existent order."""
        # Create LOB with an order
        add_message = AddOrderMessage()
        add_message.order_ref = 999
        add_message.side = b"B"
        add_message.shares = 100
        add_message.price = 15000
        add_message.timestamp = 12345

        self.processor.process_message(add_message)

        # Try to execute different order
        exec_message = OrderExecutedMessage()
        exec_message.order_ref = 888  # Different order
        exec_message.shares = 30
        exec_message.timestamp = 12346

        # Should raise OrderNotFoundError for missing order
        from meatpy.lob import OrderNotFoundError

        with pytest.raises(OrderNotFoundError):
            self.processor.process_message(exec_message)

    def test_order_cancellation(self):
        """Test order cancellation processing."""
        # First add an order
        add_message = AddOrderMessage()
        add_message.order_ref = 999
        add_message.side = b"B"
        add_message.shares = 100
        add_message.price = 15000
        add_message.timestamp = 12345

        self.processor.process_message(add_message)

        # Then cancel part of it
        cancel_message = OrderCancelMessage()
        cancel_message.order_ref = 999
        cancel_message.shares = 40
        cancel_message.timestamp = 12346

        self.processor.process_message(cancel_message)

        # Check remaining volume
        assert self.processor.lob.bid_levels[0].volume == 60

    def test_order_deletion(self):
        """Test order deletion processing."""
        # First add an order
        add_message = AddOrderMessage()
        add_message.order_ref = 999
        add_message.side = b"B"
        add_message.shares = 100
        add_message.price = 15000
        add_message.timestamp = 12345

        self.processor.process_message(add_message)

        # Then delete it
        delete_message = OrderDeleteMessage()
        delete_message.order_ref = 999
        delete_message.timestamp = 12346

        self.processor.process_message(delete_message)

        # Check that order is gone
        assert len(self.processor.lob.bid_levels) == 0

    def test_order_replacement(self):
        """Test order replacement processing."""
        # First add an order
        add_message = AddOrderMessage()
        add_message.order_ref = 999
        add_message.side = b"B"
        add_message.shares = 100
        add_message.price = 15000
        add_message.timestamp = 12345

        self.processor.process_message(add_message)

        # Then replace it
        replace_message = OrderReplaceMessage()
        replace_message.original_ref = 999
        replace_message.new_ref = 1000
        replace_message.shares = 150
        replace_message.price = 15050
        replace_message.timestamp = 12346

        self.processor.process_message(replace_message)

        # Check that new order exists with new parameters
        assert self.processor.lob.bid_levels[0].price == 15050
        assert self.processor.lob.bid_levels[0].volume == 150

    def test_trading_status_determination(self):
        """Test trading status determination logic."""
        # Test start of system -> PreTrade
        system_msg = SystemEventMessage()
        system_msg.event_code = b"S"
        system_msg.timestamp = 12345
        self.processor.process_message(system_msg)

        assert isinstance(self.processor.trading_status(), PreTradeTradingStatus)

        # Test start of market -> need stock status
        system_msg.event_code = b"Q"
        self.processor.process_message(system_msg)

        # Add stock trading status
        stock_msg = StockTradingActionMessage()
        stock_msg.stock = b"AAPL    "
        stock_msg.state = b"T"
        stock_msg.timestamp = 12346
        self.processor.process_message(stock_msg)

        assert isinstance(self.processor.trading_status(), TradeTradingStatus)

        # Test halted status
        stock_msg.state = b"H"
        self.processor.process_message(stock_msg)

        assert isinstance(self.processor.trading_status(), HaltedTradingStatus)

    def test_invalid_message_type(self):
        """Test processing invalid message type."""
        # Create a message that's not an ITCH41MarketMessage
        invalid_message = "not a market message"

        with pytest.raises(TypeError):
            self.processor.process_message(invalid_message)

    def test_multiple_orders_same_price(self):
        """Test adding multiple orders at the same price level."""
        # Add first order
        message1 = AddOrderMessage()
        message1.order_ref = 999
        message1.side = b"B"
        message1.shares = 100
        message1.price = 15000
        message1.timestamp = 12345

        self.processor.process_message(message1)

        # Add second order at same price
        message2 = AddOrderMessage()
        message2.order_ref = 1000
        message2.side = b"B"
        message2.shares = 50
        message2.price = 15000
        message2.timestamp = 12346

        self.processor.process_message(message2)

        # Should have one price level with total volume
        assert len(self.processor.lob.bid_levels) == 1
        assert self.processor.lob.bid_levels[0].price == 15000
        assert self.processor.lob.bid_levels[0].volume == 150
