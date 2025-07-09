"""Tests for the level module."""

from decimal import Decimal

import pytest

from meatpy.level import (
    ExecutionPriorityException,
    Level,
    OrderOnBook,
    VolumeInconsistencyException,
)


class TestOrderOnBook:
    """Test OrderOnBook class."""

    def test_initialization(self):
        """Test OrderOnBook initialization."""
        order = OrderOnBook(
            order_id=12345,
            volume=100,
            timestamp="2024-01-01 09:30:00",
            qualifiers={"exchange": "NASDAQ"},
        )

        assert order.order_id == 12345
        assert order.volume == 100
        assert str(order.timestamp) == "2024-01-01 09:30:00"
        assert order.qualifiers == {"exchange": "NASDAQ"}

    def test_initialization_without_qualifiers(self):
        """Test OrderOnBook initialization without qualifiers."""
        order = OrderOnBook(order_id=12345, volume=100, timestamp="2024-01-01 09:30:00")

        assert order.order_id == 12345
        assert order.volume == 100
        assert order.qualifiers == {}

    def test_equality(self):
        """Test OrderOnBook equality."""
        order1 = OrderOnBook(12345, 100, "2024-01-01 09:30:00")
        order2 = OrderOnBook(12345, 100, "2024-01-01 09:30:00")
        order3 = OrderOnBook(67890, 100, "2024-01-01 09:30:00")

        assert order1 == order2
        assert order1 != order3

    def test_str_representation(self):
        """Test OrderOnBook string representation."""
        order = OrderOnBook(12345, 100, "2024-01-01 09:30:00")
        assert "12345" in str(order)
        assert "100" in str(order)

    def test_repr_representation(self):
        """Test OrderOnBook repr representation."""
        order = OrderOnBook(12345, 100, "2024-01-01 09:30:00")
        assert "OrderOnBook" in repr(order)
        assert "12345" in repr(order)


class TestLevel:
    """Test Level class."""

    def test_initialization(self):
        """Test Level initialization."""
        level = Level(price=10000)  # $100.00

        assert level.price == 10000
        assert level.orders == []
        assert level.total_volume == 0
        assert level.n_orders == 0

    def test_add_order(self):
        """Test adding an order to a level."""
        level = Level(price=10000)
        order = OrderOnBook(12345, 100, "2024-01-01 09:30:00")

        level.add_order(order)

        assert len(level.orders) == 1
        assert level.orders[0] == order
        assert level.total_volume == 100
        assert level.n_orders == 1

    def test_add_multiple_orders(self):
        """Test adding multiple orders to a level."""
        level = Level(price=10000)
        order1 = OrderOnBook(12345, 100, "2024-01-01 09:30:00")
        order2 = OrderOnBook(67890, 50, "2024-01-01 09:31:00")

        level.add_order(order1)
        level.add_order(order2)

        assert len(level.orders) == 2
        assert level.total_volume == 150
        assert level.n_orders == 2

    def test_remove_order(self):
        """Test removing an order from a level."""
        level = Level(price=10000)
        order = OrderOnBook(12345, 100, "2024-01-01 09:30:00")

        level.add_order(order)
        level.remove_order(order)

        assert len(level.orders) == 0
        assert level.total_volume == 0
        assert level.n_orders == 0

    def test_remove_order_not_found(self):
        """Test removing an order that doesn't exist."""
        level = Level(price=10000)
        order1 = OrderOnBook(12345, 100, "2024-01-01 09:30:00")
        order2 = OrderOnBook(67890, 50, "2024-01-01 09:31:00")

        level.add_order(order1)

        with pytest.raises(ValueError):
            level.remove_order(order2)

    def test_update_order_volume(self):
        """Test updating order volume."""
        level = Level(price=10000)
        order = OrderOnBook(12345, 100, "2024-01-01 09:30:00")

        level.add_order(order)
        level.update_order_volume(order, 75)

        assert order.volume == 75
        assert level.total_volume == 75

    def test_update_order_volume_not_found(self):
        """Test updating volume for order that doesn't exist."""
        level = Level(price=10000)
        order1 = OrderOnBook(12345, 100, "2024-01-01 09:30:00")
        order2 = OrderOnBook(67890, 50, "2024-01-01 09:31:00")

        level.add_order(order1)

        with pytest.raises(ValueError):
            level.update_order_volume(order2, 75)

    def test_find_order(self):
        """Test finding an order by ID."""
        level = Level(price=10000)
        order = OrderOnBook(12345, 100, "2024-01-01 09:30:00")

        level.add_order(order)
        found_order = level.find_order(12345)

        assert found_order == order

    def test_find_order_not_found(self):
        """Test finding an order that doesn't exist."""
        level = Level(price=10000)
        order = OrderOnBook(12345, 100, "2024-01-01 09:30:00")

        level.add_order(order)
        found_order = level.find_order(67890)

        assert found_order is None

    def test_has_order(self):
        """Test checking if level has an order."""
        level = Level(price=10000)
        order = OrderOnBook(12345, 100, "2024-01-01 09:30:00")

        level.add_order(order)

        assert level.has_order(12345) is True
        assert level.has_order(67890) is False

    def test_clear(self):
        """Test clearing all orders from a level."""
        level = Level(price=10000)
        order1 = OrderOnBook(12345, 100, "2024-01-01 09:30:00")
        order2 = OrderOnBook(67890, 50, "2024-01-01 09:31:00")

        level.add_order(order1)
        level.add_order(order2)
        level.clear()

        assert len(level.orders) == 0
        assert level.total_volume == 0
        assert level.n_orders == 0

    def test_is_empty(self):
        """Test checking if level is empty."""
        level = Level(price=10000)
        assert level.is_empty() is True

        order = OrderOnBook(12345, 100, "2024-01-01 09:30:00")
        level.add_order(order)
        assert level.is_empty() is False

    def test_str_representation(self):
        """Test Level string representation."""
        level = Level(price=10000)
        order = OrderOnBook(12345, 100, "2024-01-01 09:30:00")
        level.add_order(order)

        level_str = str(level)
        assert "10000" in level_str
        assert "100" in level_str
        assert "1" in level_str  # n_orders

    def test_repr_representation(self):
        """Test Level repr representation."""
        level = Level(price=10000)
        assert "Level" in repr(level)
        assert "10000" in repr(level)

    def test_copy(self):
        """Test copying a level."""
        level = Level(price=10000)
        order = OrderOnBook(12345, 100, "2024-01-01 09:30:00")
        level.add_order(order)

        copied_level = level.copy()

        assert copied_level.price == level.price
        assert len(copied_level.orders) == len(level.orders)
        assert copied_level.total_volume == level.total_volume
        assert copied_level.n_orders == level.n_orders

        # Verify it's a deep copy
        assert copied_level.orders[0] is not level.orders[0]

    def test_order_priority(self):
        """Test order priority (time-based)."""
        level = Level(price=10000)
        order1 = OrderOnBook(12345, 100, "2024-01-01 09:30:00")
        order2 = OrderOnBook(67890, 50, "2024-01-01 09:31:00")

        # Add orders in reverse time order
        level.add_order(order2)
        level.add_order(order1)

        # First order should be the earliest one
        assert level.orders[0] == order1
        assert level.orders[1] == order2


class TestLevelEdgeCases:
    """Test Level edge cases."""

    def test_zero_volume_order(self):
        """Test handling orders with zero volume."""
        level = Level(price=10000)
        order = OrderOnBook(12345, 0, "2024-01-01 09:30:00")

        level.add_order(order)

        assert len(level.orders) == 1
        assert level.total_volume == 0
        assert level.n_orders == 1

    def test_negative_volume_order(self):
        """Test handling orders with negative volume."""
        level = Level(price=10000)
        order = OrderOnBook(12345, -50, "2024-01-01 09:30:00")

        level.add_order(order)

        assert len(level.orders) == 1
        assert level.total_volume == -50
        assert level.n_orders == 1

    def test_decimal_price(self):
        """Test level with decimal price."""
        level = Level(price=Decimal("100.50"))

        assert level.price == Decimal("100.50")

    def test_decimal_volume(self):
        """Test level with decimal volume."""
        level = Level(price=10000)
        order = OrderOnBook(12345, Decimal("100.5"), "2024-01-01 09:30:00")

        level.add_order(order)

        assert level.total_volume == Decimal("100.5")

    def test_string_order_id(self):
        """Test level with string order ID."""
        level = Level(price=10000)
        order = OrderOnBook("order-12345", 100, "2024-01-01 09:30:00")

        level.add_order(order)

        assert level.has_order("order-12345") is True
        assert level.find_order("order-12345") == order

    def test_bytes_order_id(self):
        """Test level with bytes order ID."""
        level = Level(price=10000)
        order = OrderOnBook(b"order-12345", 100, "2024-01-01 09:30:00")

        level.add_order(order)

        assert level.has_order(b"order-12345") is True
        assert level.find_order(b"order-12345") == order


class TestLevelPerformance:
    """Test Level performance characteristics."""

    def test_large_number_of_orders(self):
        """Test level with many orders."""
        level = Level(price=10000)

        # Add many orders
        for i in range(1000):
            order = OrderOnBook(i, 100, "2024-01-01 09:30:00")
            level.add_order(order)

        assert len(level.orders) == 1000
        assert level.total_volume == 100000
        assert level.n_orders == 1000

        # Test finding orders
        found_order = level.find_order(500)
        assert found_order.order_id == 500

    def test_order_removal_performance(self):
        """Test performance of order removal."""
        level = Level(price=10000)

        # Add many orders
        orders = []
        for i in range(100):
            order = OrderOnBook(i, 100, "2024-01-01 09:30:00")
            level.add_order(order)
            orders.append(order)

        # Remove orders in reverse order
        for order in reversed(orders):
            level.remove_order(order)

        assert level.is_empty() is True


class TestExceptions:
    """Test custom exceptions."""

    def test_execution_priority_exception(self):
        """Test ExecutionPriorityException."""
        exception = ExecutionPriorityException("Test message")
        assert str(exception) == "Test message"

    def test_volume_inconsistency_exception(self):
        """Test VolumeInconsistencyException."""
        exception = VolumeInconsistencyException("Test message")
        assert str(exception) == "Test message"
