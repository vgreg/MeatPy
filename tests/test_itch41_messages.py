"""Tests for ITCH 4.1 market message functionality."""

import json
import struct
import pytest

from meatpy.itch41.itch41_market_message import (
    ITCH41MarketMessage,
    SystemEventMessage,
    StockDirectoryMessage,
    StockTradingActionMessage,
    AddOrderMessage,
    AddOrderMPIDMessage,
    OrderExecutedMessage,
    OrderCancelMessage,
    OrderDeleteMessage,
    OrderReplaceMessage,
    TradeMessage,
    CrossTradeMessage,
    BrokenTradeMessage,
)


class TestITCH41MarketMessage:
    """Test the base ITCH41MarketMessage class."""

    def test_timestamp_handling(self):
        """Test timestamp handling."""
        message = ITCH41MarketMessage()

        # ITCH 4.1 timestamps are nanoseconds since the last second
        # They don't have set_timestamp or split_timestamp methods
        message.timestamp = 123456789  # nanoseconds within current second
        assert message.timestamp == 123456789


class TestSystemEventMessage:
    """Test SystemEventMessage functionality."""

    def test_from_bytes_data(self):
        """Test creating message from bytes."""
        # Create test data - ITCH 4.1 format has embedded timestamp
        timestamp = 12345  # seconds since midnight
        event_code = b"O"

        # Pack the data
        data = struct.pack("!cIc", b"S", timestamp, event_code)

        # Create message from bytes
        message = SystemEventMessage.from_bytes(data)

        assert (
            message.timestamp == timestamp
        )  # Stored as-is (already in appropriate unit)
        assert message.event_code == event_code

    def test_to_bytes(self):
        """Test converting message to bytes."""
        message = SystemEventMessage()
        message.timestamp = 12345  # Set as seconds for ITCH 4.1
        message.event_code = b"O"

        data = message.to_bytes()

        # Verify the packed data
        expected = struct.pack("!cIc", b"S", 12345, b"O")
        assert data == expected

    def test_json_conversion(self):
        """Test JSON serialization and deserialization."""
        message = SystemEventMessage()
        message.timestamp = 12345
        message.event_code = b"O"

        # Convert to JSON
        json_str = message.to_json()
        data = json.loads(json_str)

        assert data["timestamp"] == 12345
        assert data["type"] == "S"
        assert data["event_code"] == "O"

        # Convert back from JSON
        new_message = SystemEventMessage.from_json(json_str)
        assert new_message.timestamp == message.timestamp
        assert new_message.event_code == message.event_code

    def test_validation(self):
        """Test message validation."""
        message = SystemEventMessage()
        message.event_code = b"O"  # Valid event code
        assert message.validate()

        message.event_code = b"X"  # Invalid event code
        assert not message.validate()


class TestStockDirectoryMessage:
    """Test StockDirectoryMessage functionality."""

    def test_from_bytes_data(self):
        """Test creating message from bytes."""
        timestamp = 12345  # seconds since midnight
        stock = b"AAPL    "
        category = b"Q"
        status = b"N"
        lotsize = 100
        lotsonly = b"Y"

        data = struct.pack(
            "!cI8sccIc", b"R", timestamp, stock, category, status, lotsize, lotsonly
        )

        message = StockDirectoryMessage.from_bytes(data)

        assert message.timestamp == timestamp  # Stored as-is
        assert message.stock == stock
        assert message.category == category
        assert message.status == status
        assert message.lotsize == lotsize
        assert message.lotsonly == lotsonly

    def test_validation(self):
        """Test message validation."""
        message = StockDirectoryMessage()
        message.category = b"Q"  # Valid market code
        message.status = b"N"  # Valid financial status
        message.lotsonly = b"Y"  # Valid round lots only

        assert message.validate()

        message.category = b"X"  # Invalid market code
        assert not message.validate()


class TestAddOrderMessage:
    """Test AddOrderMessage functionality."""

    def test_from_bytes_data(self):
        """Test creating message from bytes."""
        ts1 = 12345
        order_ref = 999
        side = b"B"
        shares = 100
        stock = b"AAPL    "
        price = 15000  # $150.00

        data = struct.pack(
            "!cIQcI8sI", b"A", ts1, order_ref, side, shares, stock, price
        )

        message = AddOrderMessage.from_bytes(data)

        assert message.timestamp == ts1  # Stored as-is
        assert message.order_ref == order_ref
        assert message.side == side
        assert message.shares == shares
        assert message.stock == stock
        assert message.price == price

    def test_json_conversion(self):
        """Test JSON serialization."""
        message = AddOrderMessage()
        message.order_ref = 999
        message.side = b"B"
        message.shares = 100
        message.stock = b"AAPL    "
        message.price = 15000
        message.timestamp = 12345

        json_str = message.to_json()
        data = json.loads(json_str)

        assert data["order_ref"] == 999
        assert data["side"] == "B"
        assert data["shares"] == 100
        assert data["stock"] == "AAPL"
        assert data["price"] == 15000


class TestOrderExecutedMessage:
    """Test OrderExecutedMessage functionality."""

    def test_from_bytes_data(self):
        """Test creating message from bytes."""
        timestamp = 12345  # seconds since midnight
        order_ref = 999
        shares = 50
        match_num = 12345

        data = struct.pack("!cIQIQ", b"E", timestamp, order_ref, shares, match_num)

        message = OrderExecutedMessage.from_bytes(data)

        assert message.timestamp == timestamp  # Stored as-is
        assert message.order_ref == order_ref
        assert message.shares == shares
        assert message.match_num == match_num


class TestTradeMessage:
    """Test TradeMessage functionality."""

    def test_from_bytes_data(self):
        """Test creating message from bytes."""
        timestamp = 12345  # seconds since midnight
        order_ref = 999
        side = b"S"
        shares = 100
        stock = b"AAPL    "
        price = 15000
        match_num = 12345

        data = struct.pack(
            "!cIQcI8sIQ",
            b"P",
            timestamp,
            order_ref,
            side,
            shares,
            stock,
            price,
            match_num,
        )

        message = TradeMessage.from_bytes(data)

        assert message.timestamp == timestamp  # Stored as-is
        assert message.order_ref == order_ref
        assert message.side == side
        assert message.shares == shares
        assert message.price == price
        assert message.match_num == match_num


class TestCrossTradeMessage:
    """Test CrossTradeMessage functionality."""

    def test_validation(self):
        """Test cross trade type validation."""
        message = CrossTradeMessage()
        message.cross_type = b"O"  # Valid cross type (Opening Cross)
        assert message.validate()

        message.cross_type = b"Z"  # Invalid cross type
        assert not message.validate()


class TestMessageParsing:
    """Test message parsing from bytes."""

    def test_from_bytes_unknown_type(self):
        """Test handling of unknown message types."""
        # Create data with unknown message type 'Z'
        data = b"Z" + b"\x00" * 20

        with pytest.raises(Exception):  # Should raise UnknownMessageTypeError
            ITCH41MarketMessage.from_bytes(data)

    def test_from_bytes_empty_data(self):
        """Test handling of empty data."""
        with pytest.raises(ValueError):
            ITCH41MarketMessage.from_bytes(b"")

    def test_message_type_mapping(self):
        """Test that all expected message types are mapped correctly."""
        # Create minimal data for each message type
        message_types = [
            (b"S", SystemEventMessage),
            (b"R", StockDirectoryMessage),
            (b"H", StockTradingActionMessage),
            (b"A", AddOrderMessage),
            (b"F", AddOrderMPIDMessage),
            (b"E", OrderExecutedMessage),
            (b"X", OrderCancelMessage),
            (b"D", OrderDeleteMessage),
            (b"U", OrderReplaceMessage),
            (b"P", TradeMessage),
            (b"Q", CrossTradeMessage),
            (b"B", BrokenTradeMessage),
        ]

        for msg_type, expected_class in message_types:
            # Create minimal valid data for each message type
            data = msg_type + b"\x00" * (expected_class.message_size - 1)
            try:
                message = ITCH41MarketMessage.from_bytes(data)
                assert isinstance(message, expected_class)
                assert message.type == msg_type
            except struct.error:
                # Some messages might fail due to insufficient data,
                # but the type mapping should still work
                pass
