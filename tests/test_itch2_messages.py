"""Tests for ITCH 2.0 market message functionality."""

import json
import pytest

from meatpy.itch2.itch2_market_message import (
    ITCH2MarketMessage,
    SystemEventMessage,
    AddOrderMessage,
    OrderExecutedMessage,
    OrderCancelMessage,
    TradeMessage,
    BrokenTradeMessage,
)


class TestITCH2MarketMessage:
    """Test the base ITCH2MarketMessage class."""

    def test_from_bytes_unknown_type(self):
        """Test handling of unknown message types."""
        data = b"12345678Z" + b"0" * 20
        with pytest.raises(ValueError, match="Unknown message type"):
            ITCH2MarketMessage.from_bytes(data)

    def test_from_bytes_too_short(self):
        """Test handling of message that is too short."""
        data = b"1234"
        with pytest.raises(ValueError, match="Message too short"):
            ITCH2MarketMessage.from_bytes(data)

    def test_from_json_unknown_type(self):
        """Test handling of unknown message type in JSON."""
        json_str = json.dumps({"message_type": "Z", "timestamp": 12345})
        with pytest.raises(ValueError, match="Unknown message type"):
            ITCH2MarketMessage.from_json(json_str)


class TestSystemEventMessage:
    """Test SystemEventMessage functionality."""

    def test_from_bytes_data(self):
        """Test creating message from bytes."""
        # Format: timestamp(8) + type(1) + event_code(1) = 10 chars
        data = b"12345678SO"  # timestamp=12345678, type=S, event_code=O

        message = ITCH2MarketMessage.from_bytes(data)

        assert isinstance(message, SystemEventMessage)
        assert message.timestamp == 12345678
        assert message.event_code == b"O"

    def test_to_bytes(self):
        """Test converting message to bytes."""
        message = SystemEventMessage()
        message.timestamp = 12345678
        message.event_code = b"O"

        data = message.to_bytes()

        assert data == b"12345678SO"

    def test_json_roundtrip(self):
        """Test JSON serialization and deserialization."""
        message = SystemEventMessage()
        message.timestamp = 12345678
        message.event_code = b"Q"

        json_str = message.to_json()
        data = json.loads(json_str)

        assert data["timestamp"] == 12345678
        assert data["message_type"] == "S"
        assert data["event_code"] == "Q"

        # Roundtrip
        new_message = ITCH2MarketMessage.from_json(json_str)
        assert isinstance(new_message, SystemEventMessage)
        assert new_message.timestamp == message.timestamp
        assert new_message.event_code == message.event_code

    def test_all_event_codes(self):
        """Test all valid event codes."""
        event_codes = [b"O", b"S", b"Q", b"M", b"E", b"C"]
        for code in event_codes:
            data = f"12345678S{code.decode()}".encode()
            message = ITCH2MarketMessage.from_bytes(data)
            assert message.event_code == code


class TestAddOrderMessage:
    """Test AddOrderMessage functionality."""

    def test_from_bytes_data(self):
        """Test creating message from bytes."""
        # Format: timestamp(8) + type(1) + order_ref(9) + side(1) + shares(6)
        #         + stock(6) + price(10) + display(1) = 42 chars
        data = b"12345678A000000001B000100AAPL  0000150000Y"

        message = ITCH2MarketMessage.from_bytes(data)

        assert isinstance(message, AddOrderMessage)
        assert message.timestamp == 12345678
        assert message.order_ref == 1
        assert message.side == b"B"
        assert message.shares == 100
        assert message.stock == b"AAPL  "
        assert message.price == 150000
        assert message.display == b"Y"

    def test_to_bytes(self):
        """Test converting message to bytes."""
        message = AddOrderMessage()
        message.timestamp = 12345678
        message.order_ref = 1
        message.side = b"B"
        message.shares = 100
        message.stock = b"AAPL  "
        message.price = 150000
        message.display = b"Y"

        data = message.to_bytes()

        assert data == b"12345678A        1B   100AAPL  0000150000Y"

    def test_json_roundtrip(self):
        """Test JSON serialization and deserialization."""
        message = AddOrderMessage()
        message.timestamp = 12345678
        message.order_ref = 999
        message.side = b"S"
        message.shares = 200
        message.stock = b"MSFT  "
        message.price = 250000
        message.display = b"N"

        json_str = message.to_json()
        data = json.loads(json_str)

        assert data["order_ref"] == 999
        assert data["side"] == "S"
        assert data["shares"] == 200
        assert data["stock"] == "MSFT"
        assert data["price"] == 250000

        # Roundtrip
        new_message = ITCH2MarketMessage.from_json(json_str)
        assert isinstance(new_message, AddOrderMessage)
        assert new_message.order_ref == message.order_ref


class TestOrderExecutedMessage:
    """Test OrderExecutedMessage functionality."""

    def test_from_bytes_data(self):
        """Test creating message from bytes."""
        # Format: timestamp(8) + type(1) + order_ref(9) + shares(6) + match_number(9) = 33 chars
        data = b"12345678E000000001000050000000123"

        message = ITCH2MarketMessage.from_bytes(data)

        assert isinstance(message, OrderExecutedMessage)
        assert message.timestamp == 12345678
        assert message.order_ref == 1
        assert message.shares == 50
        assert message.match_number == 123

    def test_to_bytes(self):
        """Test converting message to bytes."""
        message = OrderExecutedMessage()
        message.timestamp = 12345678
        message.order_ref = 1
        message.shares = 50
        message.match_number = 123

        data = message.to_bytes()

        assert data == b"12345678E        1    50      123"

    def test_json_roundtrip(self):
        """Test JSON serialization and deserialization."""
        message = OrderExecutedMessage()
        message.timestamp = 12345678
        message.order_ref = 999
        message.shares = 100
        message.match_number = 456

        json_str = message.to_json()
        new_message = ITCH2MarketMessage.from_json(json_str)

        assert isinstance(new_message, OrderExecutedMessage)
        assert new_message.order_ref == message.order_ref
        assert new_message.shares == message.shares
        assert new_message.match_number == message.match_number


class TestOrderCancelMessage:
    """Test OrderCancelMessage functionality."""

    def test_from_bytes_data(self):
        """Test creating message from bytes."""
        # Format: timestamp(8) + type(1) + order_ref(9) + shares(6) = 24 chars
        data = b"12345678X000000001000025"

        message = ITCH2MarketMessage.from_bytes(data)

        assert isinstance(message, OrderCancelMessage)
        assert message.timestamp == 12345678
        assert message.order_ref == 1
        assert message.shares == 25

    def test_to_bytes(self):
        """Test converting message to bytes."""
        message = OrderCancelMessage()
        message.timestamp = 12345678
        message.order_ref = 1
        message.shares = 25

        data = message.to_bytes()

        assert data == b"12345678X        1    25"

    def test_json_roundtrip(self):
        """Test JSON serialization and deserialization."""
        message = OrderCancelMessage()
        message.timestamp = 12345678
        message.order_ref = 999
        message.shares = 50

        json_str = message.to_json()
        new_message = ITCH2MarketMessage.from_json(json_str)

        assert isinstance(new_message, OrderCancelMessage)
        assert new_message.order_ref == message.order_ref
        assert new_message.shares == message.shares


class TestTradeMessage:
    """Test TradeMessage functionality."""

    def test_from_bytes_data(self):
        """Test creating message from bytes."""
        # Format: timestamp(8) + type(1) + order_ref(9) + side(1) + shares(6)
        #         + stock(6) + price(10) + match_number(9) = 50 chars
        data = b"12345678P000000001S000100AAPL  0000150000000000123"

        message = ITCH2MarketMessage.from_bytes(data)

        assert isinstance(message, TradeMessage)
        assert message.timestamp == 12345678
        assert message.order_ref == 1
        assert message.side == b"S"
        assert message.shares == 100
        assert message.stock == b"AAPL  "
        assert message.price == 150000
        assert message.match_number == 123

    def test_to_bytes(self):
        """Test converting message to bytes."""
        message = TradeMessage()
        message.timestamp = 12345678
        message.order_ref = 1
        message.side = b"S"
        message.shares = 100
        message.stock = b"AAPL  "
        message.price = 150000
        message.match_number = 123

        data = message.to_bytes()

        assert data == b"12345678P        1S   100AAPL  0000150000      123"

    def test_json_roundtrip(self):
        """Test JSON serialization and deserialization."""
        message = TradeMessage()
        message.timestamp = 12345678
        message.order_ref = 999
        message.side = b"B"
        message.shares = 200
        message.stock = b"MSFT  "
        message.price = 250000
        message.match_number = 456

        json_str = message.to_json()
        new_message = ITCH2MarketMessage.from_json(json_str)

        assert isinstance(new_message, TradeMessage)
        assert new_message.order_ref == message.order_ref
        assert new_message.side == message.side


class TestBrokenTradeMessage:
    """Test BrokenTradeMessage functionality."""

    def test_from_bytes_data(self):
        """Test creating message from bytes."""
        # Format: timestamp(8) + type(1) + match_number(9) = 18 chars
        data = b"12345678B000000123"

        message = ITCH2MarketMessage.from_bytes(data)

        assert isinstance(message, BrokenTradeMessage)
        assert message.timestamp == 12345678
        assert message.match_number == 123

    def test_to_bytes(self):
        """Test converting message to bytes."""
        message = BrokenTradeMessage()
        message.timestamp = 12345678
        message.match_number = 123

        data = message.to_bytes()

        assert data == b"12345678B      123"

    def test_json_roundtrip(self):
        """Test JSON serialization and deserialization."""
        message = BrokenTradeMessage()
        message.timestamp = 12345678
        message.match_number = 456

        json_str = message.to_json()
        new_message = ITCH2MarketMessage.from_json(json_str)

        assert isinstance(new_message, BrokenTradeMessage)
        assert new_message.match_number == message.match_number


class TestMessageTypeMappings:
    """Test that message type mappings work correctly."""

    def test_all_message_types_registered(self):
        """Verify all message types are properly registered."""
        # Create minimal data for each type
        test_cases = [
            (b"12345678SO", SystemEventMessage),
            (b"12345678A000000001B000100AAPL  0000150000Y", AddOrderMessage),
            (b"12345678E000000001000050000000123", OrderExecutedMessage),
            (b"12345678X000000001000025", OrderCancelMessage),
            (b"12345678P000000001S000100AAPL  0000150000000000123", TradeMessage),
            (b"12345678B000000123", BrokenTradeMessage),
        ]

        for data, expected_class in test_cases:
            message = ITCH2MarketMessage.from_bytes(data)
            assert isinstance(message, expected_class), (
                f"Failed for {expected_class.__name__}"
            )
