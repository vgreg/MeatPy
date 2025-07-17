"""Tests for the limit order book module."""

from unittest.mock import Mock

import pytest

from meatpy.lob import (
    ExecutionPriorityExceptionList,
    InexistantValueException,
    InvalidOrderTypeError,
    InvalidPositionError,
    InvalidPriceTypeError,
    LimitOrderBook,
    OrderNotFoundError,
    OrderType,
)
from meatpy.timestamp import Timestamp


class TestLimitOrderBookInitialization:
    """Test limit order book initialization."""

    def test_init_with_timestamp(self):
        """Test initialization with timestamp."""
        timestamp = Timestamp(2024, 1, 1, 9, 30, 0)
        lob = LimitOrderBook(timestamp)

        assert lob.timestamp == timestamp
        assert lob.timestamp_inc == 0
        assert lob.bid_levels == []
        assert lob.ask_levels == []
        assert lob.decimals_adj is None
        assert lob.execution_errors_buffer == []

    def test_init_with_timestamp_inc(self):
        """Test initialization with timestamp increment."""
        timestamp = Timestamp(2024, 1, 1, 9, 30, 0)
        lob = LimitOrderBook(timestamp, timestamp_inc=5)

        assert lob.timestamp == timestamp
        assert lob.timestamp_inc == 5

    def test_init_default_values(self):
        """Test initialization with default values."""
        timestamp = Timestamp(2024, 1, 1, 9, 30, 0)
        lob = LimitOrderBook(timestamp)

        assert lob.bid_levels == []
        assert lob.ask_levels == []
        assert lob.decimals_adj is None
        assert lob.execution_errors_buffer == []


class TestLimitOrderBookOrderType:
    """Test OrderType enum."""

    def test_order_type_values(self):
        """Test OrderType enum values."""
        assert OrderType.ASK.value == 0
        assert OrderType.BID.value == 1

    def test_order_type_names(self):
        """Test OrderType enum names."""
        assert OrderType.ASK.name == "ASK"
        assert OrderType.BID.name == "BID"


class TestLimitOrderBookExceptions:
    """Test limit order book exceptions."""

    def test_inexistant_value_exception(self):
        """Test InexistantValueException."""
        exception = InexistantValueException("test", "message")
        assert str(exception) == "message"

    def test_execution_priority_exception_list(self):
        """Test ExecutionPriorityExceptionList."""
        exception = ExecutionPriorityExceptionList()
        assert isinstance(exception, Exception)

    def test_invalid_price_type_error(self):
        """Test InvalidPriceTypeError."""
        exception = InvalidPriceTypeError("Invalid price type")
        assert str(exception) == "Invalid price type"

    def test_order_not_found_error(self):
        """Test OrderNotFoundError."""
        exception = OrderNotFoundError("Order not found")
        assert str(exception) == "Order not found"

    def test_invalid_order_type_error(self):
        """Test InvalidOrderTypeError."""
        exception = InvalidOrderTypeError("Invalid order type")
        assert str(exception) == "Invalid order type"

    def test_invalid_position_error(self):
        """Test InvalidPositionError."""
        exception = InvalidPositionError("Invalid position")
        assert str(exception) == "Invalid position"


class TestLimitOrderBookBasicOperations:
    """Test basic limit order book operations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.timestamp = Timestamp(2024, 1, 1, 9, 30, 0)
        self.lob = LimitOrderBook(self.timestamp)

    def test_create_level_from_price(self):
        """Test create_level_from_price method."""
        price = 100
        level = self.lob.create_level_from_price(price)
        assert level.price == price

    def test_copy_empty_lob(self):
        """Test copying empty LOB."""
        copied_lob = self.lob.copy()

        assert copied_lob.timestamp == self.lob.timestamp
        assert copied_lob.timestamp_inc == self.lob.timestamp_inc
        assert copied_lob.bid_levels == []
        assert copied_lob.ask_levels == []
        assert copied_lob is not self.lob

    def test_copy_with_max_level(self):
        """Test copying LOB with max level limit."""
        # Add some levels to the original LOB
        self.lob.bid_levels = [Mock(), Mock(), Mock()]
        self.lob.ask_levels = [Mock(), Mock()]

        copied_lob = self.lob.copy(max_level=2)

        assert len(copied_lob.bid_levels) == 2
        assert len(copied_lob.ask_levels) == 2

    def test_copy_with_decimals_adj(self):
        """Test copying LOB with decimals adjustment."""
        self.lob.decimals_adj = 100
        copied_lob = self.lob.copy()

        assert copied_lob.decimals_adj == 100


class TestLimitOrderBookPriceAdjustment:
    """Test price adjustment functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.timestamp = Timestamp(2024, 1, 1, 9, 30, 0)
        self.lob = LimitOrderBook(self.timestamp)

    def test_adjust_price_no_adjustment(self):
        """Test price adjustment when decimals_adj is None."""
        price = 100
        adjusted = self.lob.adjust_price(price)
        assert adjusted == price

    def test_adjust_price_with_int_decimals_adj(self):
        """Test price adjustment with integer decimals_adj."""
        self.lob.decimals_adj = 100
        price = 10000
        adjusted = self.lob.adjust_price(price)
        assert adjusted == 100

    def test_adjust_price_with_decimal_type(self):
        """Test price adjustment with Decimal type."""
        from decimal import Decimal

        self.lob.decimals_adj = Decimal("100")
        price = Decimal("10000")
        adjusted = self.lob.adjust_price(price)
        assert adjusted == Decimal("100")

    def test_adjust_price_invalid_type(self):
        """Test price adjustment with invalid type."""
        self.lob.decimals_adj = 100
        price = "invalid"

        with pytest.raises(InvalidPriceTypeError):
            self.lob.adjust_price(price)


class TestLimitOrderBookOrderManagement:
    """Test order management operations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.timestamp = Timestamp(2024, 1, 1, 9, 30, 0)
        self.lob = LimitOrderBook(self.timestamp)

    def test_enter_quote_bid(self):
        """Test entering a bid quote."""
        price = 100
        volume = 1000
        order_id = 12345

        self.lob.enter_quote(self.timestamp, price, volume, order_id, OrderType.BID)

        # Should create a bid level
        assert len(self.lob.bid_levels) == 1
        assert self.lob.bid_levels[0].price == price

    def test_enter_quote_ask(self):
        """Test entering an ask quote."""
        price = 101
        volume = 1000
        order_id = 12346

        self.lob.enter_quote(self.timestamp, price, volume, order_id, OrderType.ASK)

        # Should create an ask level
        assert len(self.lob.ask_levels) == 1
        assert self.lob.ask_levels[0].price == price

    def test_enter_quote_with_qualifiers(self):
        """Test entering a quote with qualifiers."""
        price = 100
        volume = 1000
        order_id = 12345
        qualifiers = {"display": "Y", "time_in_force": "DAY"}

        self.lob.enter_quote(
            self.timestamp, price, volume, order_id, OrderType.BID, qualifiers
        )

        # Should not raise an exception
        assert len(self.lob.bid_levels) == 1

    def test_cancel_quote(self):
        """Test canceling a quote."""
        # First enter a quote
        price = 100
        volume = 1000
        order_id = 12345

        self.lob.enter_quote(self.timestamp, price, volume, order_id, OrderType.BID)

        # Then cancel part of it
        cancel_volume = 500
        self.lob.cancel_quote(cancel_volume, order_id, OrderType.BID)

        # Should not raise an exception
        assert len(self.lob.bid_levels) == 1

    def test_delete_quote(self):
        """Test deleting a quote."""
        # First enter a quote
        price = 100
        volume = 1000
        order_id = 12345

        self.lob.enter_quote(self.timestamp, price, volume, order_id, OrderType.BID)

        # Then delete it
        self.lob.delete_quote(order_id, OrderType.BID)

        # Should not raise an exception
        assert len(self.lob.bid_levels) == 1

    def test_execute_trade(self):
        """Test executing a trade."""
        # First enter a quote
        price = 100
        volume = 1000
        order_id = 12345

        self.lob.enter_quote(self.timestamp, price, volume, order_id, OrderType.BID)

        # Then execute a trade
        trade_volume = 500
        self.lob.execute_trade(self.timestamp, trade_volume, order_id, OrderType.BID)

        # Should not raise an exception
        assert len(self.lob.bid_levels) == 1


class TestLimitOrderBookOrderQueries:
    """Test order query operations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.timestamp = Timestamp(2024, 1, 1, 9, 30, 0)
        self.lob = LimitOrderBook(self.timestamp)

    def test_order_on_book_bid(self):
        """Test checking if bid order is on book."""
        # First enter a bid quote
        price = 100
        volume = 1000
        order_id = 12345

        self.lob.enter_quote(self.timestamp, price, volume, order_id, OrderType.BID)

        # Check if order is on book
        assert self.lob.order_on_book(order_id, OrderType.BID) is True
        assert self.lob.order_on_book(order_id) is True

    def test_order_on_book_ask(self):
        """Test checking if ask order is on book."""
        # First enter an ask quote
        price = 101
        volume = 1000
        order_id = 12346

        self.lob.enter_quote(self.timestamp, price, volume, order_id, OrderType.ASK)

        # Check if order is on book
        assert self.lob.order_on_book(order_id, OrderType.ASK) is True
        assert self.lob.order_on_book(order_id) is True

    def test_order_not_on_book(self):
        """Test checking if order is not on book."""
        order_id = 99999
        assert self.lob.order_on_book(order_id, OrderType.BID) is False
        assert self.lob.order_on_book(order_id, OrderType.ASK) is False
        assert self.lob.order_on_book(order_id) is False

    def test_ask_order_on_book(self):
        """Test ask_order_on_book method."""
        # First enter an ask quote
        price = 101
        volume = 1000
        order_id = 12346

        self.lob.enter_quote(self.timestamp, price, volume, order_id, OrderType.ASK)

        assert self.lob.ask_order_on_book(order_id) is True

    def test_bid_order_on_book(self):
        """Test bid_order_on_book method."""
        # First enter a bid quote
        price = 100
        volume = 1000
        order_id = 12345

        self.lob.enter_quote(self.timestamp, price, volume, order_id, OrderType.BID)

        assert self.lob.bid_order_on_book(order_id) is True

    def test_find_order_type(self):
        """Test find_order_type method."""
        # First enter quotes
        self.lob.enter_quote(self.timestamp, 100, 1000, 12345, OrderType.BID)
        self.lob.enter_quote(self.timestamp, 101, 1000, 12346, OrderType.ASK)

        assert self.lob.find_order_type(12345) == OrderType.BID
        assert self.lob.find_order_type(12346) == OrderType.ASK

    def test_find_order(self):
        """Test find_order method."""
        # First enter a quote
        price = 100
        volume = 1000
        order_id = 12345

        self.lob.enter_quote(self.timestamp, price, volume, order_id, OrderType.BID)

        levels, level_index, order_index = self.lob.find_order(order_id, OrderType.BID)

        assert levels == self.lob.bid_levels
        assert level_index == 0
        assert order_index >= 0


class TestLimitOrderBookEdgeCases:
    """Test limit order book edge cases."""

    def setup_method(self):
        """Set up test fixtures."""
        self.timestamp = Timestamp(2024, 1, 1, 9, 30, 0)
        self.lob = LimitOrderBook(self.timestamp)

    def test_zero_volume_quote(self):
        """Test entering quote with zero volume."""
        price = 100
        volume = 0
        order_id = 12345

        # Should not raise an exception
        self.lob.enter_quote(self.timestamp, price, volume, order_id, OrderType.BID)

    def test_zero_price_quote(self):
        """Test entering quote with zero price."""
        price = 0
        volume = 1000
        order_id = 12345

        # Should not raise an exception
        self.lob.enter_quote(self.timestamp, price, volume, order_id, OrderType.BID)

    def test_negative_values(self):
        """Test with negative values."""
        price = -100
        volume = -1000
        order_id = -12345

        # Should not raise an exception
        self.lob.enter_quote(self.timestamp, price, volume, order_id, OrderType.BID)

    def test_large_values(self):
        """Test with very large values."""
        price = 999999999
        volume = 999999999
        order_id = 999999999

        # Should not raise an exception
        self.lob.enter_quote(self.timestamp, price, volume, order_id, OrderType.BID)

    def test_none_order_type(self):
        """Test operations with None order type."""
        price = 100
        volume = 1000
        order_id = 12345

        # Should not raise an exception
        self.lob.enter_quote(self.timestamp, price, volume, order_id, None)


class TestLimitOrderBookIntegration:
    """Test limit order book integration scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        self.timestamp = Timestamp(2024, 1, 1, 9, 30, 0)
        self.lob = LimitOrderBook(self.timestamp)

    def test_full_trade_cycle(self):
        """Test a full trade cycle: enter, execute, cancel, delete."""
        price = 100
        volume = 1000
        order_id = 12345

        # Enter quote
        self.lob.enter_quote(self.timestamp, price, volume, order_id, OrderType.BID)
        assert self.lob.order_on_book(order_id, OrderType.BID)

        # Execute partial trade
        self.lob.execute_trade(self.timestamp, 500, order_id, OrderType.BID)
        assert self.lob.order_on_book(order_id, OrderType.BID)

        # Cancel remaining
        self.lob.cancel_quote(400, order_id, OrderType.BID)
        assert self.lob.order_on_book(order_id, OrderType.BID)

        # Delete order
        self.lob.delete_quote(order_id, OrderType.BID)
        assert not self.lob.order_on_book(order_id, OrderType.BID)

    def test_multiple_orders_same_price(self):
        """Test multiple orders at the same price level."""
        price = 100
        order_ids = [12345, 12346, 12347]

        for order_id in order_ids:
            self.lob.enter_quote(self.timestamp, price, 1000, order_id, OrderType.BID)

        # All orders should be on book
        for order_id in order_ids:
            assert self.lob.order_on_book(order_id, OrderType.BID)

    def test_bid_ask_spread(self):
        """Test bid-ask spread calculation."""
        # Add bid and ask
        self.lob.enter_quote(self.timestamp, 100, 1000, 12345, OrderType.BID)
        self.lob.enter_quote(self.timestamp, 101, 1000, 12346, OrderType.ASK)

        # Should be able to calculate spread
        spread = self.lob.bid_ask_spread
        assert spread == 1

    def test_mid_quote(self):
        """Test mid quote calculation."""
        # Add bid and ask
        self.lob.enter_quote(self.timestamp, 100, 1000, 12345, OrderType.BID)
        self.lob.enter_quote(self.timestamp, 102, 1000, 12346, OrderType.ASK)

        # Should be able to calculate mid quote
        mid = self.lob.mid_quote
        assert mid == 101
