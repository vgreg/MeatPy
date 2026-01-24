"""Tests for ITCH 4.0 market message functionality."""

import json
import struct
import pytest

from meatpy.itch4.itch4_market_message import (
    ITCH4MarketMessage,
    SecondsMessage,
    SystemEventMessage,
    StockDirectoryMessage,
    StockTradingActionMessage,
    MarketParticipantPositionMessage,
    AddOrderMessage,
    AddOrderMPIDMessage,
    OrderExecutedMessage,
    OrderExecutedPriceMessage,
    OrderCancelMessage,
    OrderDeleteMessage,
    OrderReplaceMessage,
    TradeMessage,
    CrossTradeMessage,
    BrokenTradeMessage,
    NoiiMessage,
)
from meatpy.message_reader import UnknownMessageTypeError


class TestITCH4MarketMessage:
    """Test the base ITCH4MarketMessage class."""

    def test_from_bytes_empty_data(self):
        """Test handling of empty data."""
        with pytest.raises(ValueError, match="Empty message data"):
            ITCH4MarketMessage.from_bytes(b"")

    def test_from_bytes_unknown_type(self):
        """Test handling of unknown message types."""
        data = b"Z" + b"\x00" * 20
        with pytest.raises(UnknownMessageTypeError):
            ITCH4MarketMessage.from_bytes(data)

    def test_from_json_unknown_type(self):
        """Test handling of unknown message type in JSON."""
        json_str = json.dumps({"type": "Z", "timestamp": 12345})
        with pytest.raises(UnknownMessageTypeError):
            ITCH4MarketMessage.from_json(json_str)


class TestSecondsMessage:
    """Test SecondsMessage functionality."""

    def test_from_bytes_data(self):
        """Test creating message from bytes."""
        # Format: T(1) + seconds(4) = 5 bytes
        data = struct.pack("!cI", b"T", 12345)

        message = ITCH4MarketMessage.from_bytes(data)

        assert isinstance(message, SecondsMessage)
        assert message.seconds == 12345

    def test_to_bytes(self):
        """Test converting message to bytes."""
        message = SecondsMessage()
        message.seconds = 12345

        data = message.to_bytes()

        expected = struct.pack("!cI", b"T", 12345)
        assert data == expected

    def test_json_roundtrip(self):
        """Test JSON serialization and deserialization."""
        message = SecondsMessage()
        message.seconds = 54321

        json_str = message.to_json()
        new_message = ITCH4MarketMessage.from_json(json_str)

        assert isinstance(new_message, SecondsMessage)
        assert new_message.seconds == message.seconds


class TestSystemEventMessage:
    """Test SystemEventMessage functionality."""

    def test_from_bytes_data(self):
        """Test creating message from bytes."""
        # Format: S(1) + timestamp(4) + event_code(1) = 6 bytes
        data = struct.pack("!cIc", b"S", 12345, b"O")

        message = ITCH4MarketMessage.from_bytes(data)

        assert isinstance(message, SystemEventMessage)
        assert message.timestamp == 12345
        assert message.event_code == b"O"

    def test_to_bytes(self):
        """Test converting message to bytes."""
        message = SystemEventMessage()
        message.timestamp = 12345
        message.event_code = b"O"

        data = message.to_bytes()

        expected = struct.pack("!cIc", b"S", 12345, b"O")
        assert data == expected

    def test_json_roundtrip(self):
        """Test JSON serialization and deserialization."""
        message = SystemEventMessage()
        message.timestamp = 12345
        message.event_code = b"Q"

        json_str = message.to_json()
        data = json.loads(json_str)

        assert data["timestamp"] == 12345
        assert data["event_code"] == "Q"

        new_message = ITCH4MarketMessage.from_json(json_str)
        assert isinstance(new_message, SystemEventMessage)
        assert new_message.event_code == message.event_code


class TestStockDirectoryMessage:
    """Test StockDirectoryMessage functionality."""

    def test_from_bytes_data(self):
        """Test creating message from bytes."""
        # Format: R(1) + timestamp(4) + stock(6) + market_category(1) + financial_status(1)
        #         + round_lot_size(4) + round_lots_only(1) = 18 bytes
        data = struct.pack("!cI6sccIc", b"R", 12345, b"AAPL  ", b"Q", b"N", 100, b"Y")

        message = ITCH4MarketMessage.from_bytes(data)

        assert isinstance(message, StockDirectoryMessage)
        assert message.timestamp == 12345
        assert message.stock == b"AAPL  "
        assert message.category == b"Q"
        assert message.status == b"N"
        assert message.lotsize == 100
        assert message.lotsonly == b"Y"

    def test_to_bytes(self):
        """Test converting message to bytes."""
        message = StockDirectoryMessage()
        message.timestamp = 12345
        message.stock = b"MSFT  "
        message.category = b"G"
        message.status = b"D"
        message.lotsize = 100
        message.lotsonly = b"N"

        data = message.to_bytes()

        expected = struct.pack(
            "!cI6sccIc", b"R", 12345, b"MSFT  ", b"G", b"D", 100, b"N"
        )
        assert data == expected


class TestAddOrderMessage:
    """Test AddOrderMessage functionality."""

    def test_from_bytes_data(self):
        """Test creating message from bytes."""
        # Format: A(1) + timestamp(4) + order_ref(8) + side(1) + shares(4) + stock(6) + price(4) = 28 bytes
        data = struct.pack("!cIQcI6sI", b"A", 12345, 999, b"B", 100, b"AAPL  ", 150000)

        message = ITCH4MarketMessage.from_bytes(data)

        assert isinstance(message, AddOrderMessage)
        assert message.timestamp == 12345
        assert message.order_ref == 999
        assert message.side == b"B"
        assert message.shares == 100
        assert message.stock == b"AAPL  "
        assert message.price == 150000

    def test_to_bytes(self):
        """Test converting message to bytes."""
        message = AddOrderMessage()
        message.timestamp = 12345
        message.order_ref = 999
        message.side = b"B"
        message.shares = 100
        message.stock = b"AAPL  "
        message.price = 150000

        data = message.to_bytes()

        expected = struct.pack(
            "!cIQcI6sI", b"A", 12345, 999, b"B", 100, b"AAPL  ", 150000
        )
        assert data == expected

    def test_json_roundtrip(self):
        """Test JSON serialization and deserialization."""
        message = AddOrderMessage()
        message.timestamp = 12345
        message.order_ref = 999
        message.side = b"S"
        message.shares = 200
        message.stock = b"MSFT  "
        message.price = 250000

        json_str = message.to_json()
        data = json.loads(json_str)

        assert data["order_ref"] == 999
        assert data["side"] == "S"
        assert data["stock"] == "MSFT"

        new_message = ITCH4MarketMessage.from_json(json_str)
        assert isinstance(new_message, AddOrderMessage)
        assert new_message.order_ref == message.order_ref


class TestAddOrderMPIDMessage:
    """Test AddOrderMPIDMessage functionality."""

    def test_from_bytes_data(self):
        """Test creating message from bytes."""
        # Format: F(1) + timestamp(4) + order_ref(8) + side(1) + shares(4) + stock(6) + price(4) + mpid(4) = 32 bytes
        data = struct.pack(
            "!cIQcI6sI4s", b"F", 12345, 999, b"B", 100, b"AAPL  ", 150000, b"ABCD"
        )

        message = ITCH4MarketMessage.from_bytes(data)

        assert isinstance(message, AddOrderMPIDMessage)
        assert message.order_ref == 999
        assert message.mpid == b"ABCD"


class TestOrderExecutedMessage:
    """Test OrderExecutedMessage functionality."""

    def test_from_bytes_data(self):
        """Test creating message from bytes."""
        # Format: E(1) + timestamp(4) + order_ref(8) + shares(4) + match_number(8) = 25 bytes
        data = struct.pack("!cIQIQ", b"E", 12345, 999, 50, 12345)

        message = ITCH4MarketMessage.from_bytes(data)

        assert isinstance(message, OrderExecutedMessage)
        assert message.timestamp == 12345
        assert message.order_ref == 999
        assert message.shares == 50
        assert message.match_number == 12345

    def test_to_bytes(self):
        """Test converting message to bytes."""
        message = OrderExecutedMessage()
        message.timestamp = 12345
        message.order_ref = 999
        message.shares = 50
        message.match_number = 12345

        data = message.to_bytes()

        expected = struct.pack("!cIQIQ", b"E", 12345, 999, 50, 12345)
        assert data == expected


class TestOrderExecutedPriceMessage:
    """Test OrderExecutedPriceMessage functionality."""

    def test_from_bytes_data(self):
        """Test creating message from bytes."""
        # Format: C(1) + timestamp(4) + order_ref(8) + shares(4) + match_number(8) + printable(1) + price(4) = 30 bytes
        data = struct.pack("!cIQIQcI", b"C", 12345, 999, 50, 12345, b"Y", 150000)

        message = ITCH4MarketMessage.from_bytes(data)

        assert isinstance(message, OrderExecutedPriceMessage)
        assert message.order_ref == 999
        assert message.printable == b"Y"
        assert message.price == 150000


class TestOrderCancelMessage:
    """Test OrderCancelMessage functionality."""

    def test_from_bytes_data(self):
        """Test creating message from bytes."""
        # Format: X(1) + timestamp(4) + order_ref(8) + shares(4) = 17 bytes
        data = struct.pack("!cIQI", b"X", 12345, 999, 25)

        message = ITCH4MarketMessage.from_bytes(data)

        assert isinstance(message, OrderCancelMessage)
        assert message.timestamp == 12345
        assert message.order_ref == 999
        assert message.shares == 25


class TestOrderDeleteMessage:
    """Test OrderDeleteMessage functionality."""

    def test_from_bytes_data(self):
        """Test creating message from bytes."""
        # Format: D(1) + timestamp(4) + order_ref(8) = 13 bytes
        data = struct.pack("!cIQ", b"D", 12345, 999)

        message = ITCH4MarketMessage.from_bytes(data)

        assert isinstance(message, OrderDeleteMessage)
        assert message.timestamp == 12345
        assert message.order_ref == 999


class TestOrderReplaceMessage:
    """Test OrderReplaceMessage functionality."""

    def test_from_bytes_data(self):
        """Test creating message from bytes."""
        # Format: U(1) + timestamp(4) + original_ref(8) + new_ref(8) + shares(4) + price(4) = 29 bytes
        data = struct.pack("!cIQQII", b"U", 12345, 999, 1000, 100, 150000)

        message = ITCH4MarketMessage.from_bytes(data)

        assert isinstance(message, OrderReplaceMessage)
        assert message.timestamp == 12345
        assert message.original_ref == 999
        assert message.new_ref == 1000
        assert message.shares == 100
        assert message.price == 150000

    def test_to_bytes(self):
        """Test converting message to bytes."""
        message = OrderReplaceMessage()
        message.timestamp = 12345
        message.original_ref = 999
        message.new_ref = 1000
        message.shares = 100
        message.price = 150000

        data = message.to_bytes()

        expected = struct.pack("!cIQQII", b"U", 12345, 999, 1000, 100, 150000)
        assert data == expected


class TestTradeMessage:
    """Test TradeMessage functionality."""

    def test_from_bytes_data(self):
        """Test creating message from bytes."""
        # Format: P(1) + timestamp(4) + order_ref(8) + side(1) + shares(4) + stock(6) + price(4) + match_number(8) = 36 bytes
        data = struct.pack(
            "!cIQcI6sIQ", b"P", 12345, 999, b"S", 100, b"AAPL  ", 150000, 12345
        )

        message = ITCH4MarketMessage.from_bytes(data)

        assert isinstance(message, TradeMessage)
        assert message.order_ref == 999
        assert message.side == b"S"
        assert message.shares == 100
        assert message.price == 150000


class TestCrossTradeMessage:
    """Test CrossTradeMessage functionality."""

    def test_from_bytes_data(self):
        """Test creating message from bytes."""
        # Format: Q(1) + timestamp(4) + shares(8) + stock(6) + price(4) + match_number(8) + cross_type(1) = 32 bytes
        data = struct.pack(
            "!cIQ6sIQc", b"Q", 12345, 1000, b"AAPL  ", 150000, 12345, b"O"
        )

        message = ITCH4MarketMessage.from_bytes(data)

        assert isinstance(message, CrossTradeMessage)
        assert message.shares == 1000
        assert message.cross_type == b"O"


class TestBrokenTradeMessage:
    """Test BrokenTradeMessage functionality."""

    def test_from_bytes_data(self):
        """Test creating message from bytes."""
        # Format: B(1) + timestamp(4) + match_number(8) = 13 bytes
        data = struct.pack("!cIQ", b"B", 12345, 12345)

        message = ITCH4MarketMessage.from_bytes(data)

        assert isinstance(message, BrokenTradeMessage)
        assert message.timestamp == 12345
        assert message.match_number == 12345


class TestNoiiMessage:
    """Test NoiiMessage functionality."""

    def test_from_bytes_data(self):
        """Test creating message from bytes."""
        # Format: I(1) + timestamp(4) + paired_shares(8) + imbalance_shares(8) + imbalance_direction(1)
        #         + stock(6) + far_price(4) + near_price(4) + current_ref_price(4) + cross_type(1) + price_var(1) = 42 bytes
        data = struct.pack(
            "!cIQQc6sIIIcc",
            b"I",
            12345,
            10000,
            5000,
            b"B",
            b"AAPL  ",
            150000,
            150000,
            150000,
            b"O",
            b" ",
        )

        message = ITCH4MarketMessage.from_bytes(data)

        assert isinstance(message, NoiiMessage)
        assert message.paired_shares == 10000
        assert message.imbalance_shares == 5000
        assert message.imbalance_direction == b"B"


class TestStockTradingActionMessage:
    """Test StockTradingActionMessage functionality."""

    def test_from_bytes_data(self):
        """Test creating message from bytes."""
        # Format: H(1) + timestamp(4) + stock(6) + state(1) + reserved(5) = 17 bytes
        data = struct.pack("!cI6sc5s", b"H", 12345, b"AAPL  ", b"T", b"     ")

        message = ITCH4MarketMessage.from_bytes(data)

        assert isinstance(message, StockTradingActionMessage)
        assert message.stock == b"AAPL  "
        assert message.state == b"T"


class TestMarketParticipantPositionMessage:
    """Test MarketParticipantPositionMessage functionality."""

    def test_from_bytes_data(self):
        """Test creating message from bytes."""
        # Format: L(1) + timestamp(4) + mpid(4) + stock(6) + primary(1) + mode(1) + state(1) = 18 bytes
        data = struct.pack(
            "!cI4s6sccc", b"L", 12345, b"ABCD", b"AAPL  ", b"Y", b"N", b"A"
        )

        message = ITCH4MarketMessage.from_bytes(data)

        assert isinstance(message, MarketParticipantPositionMessage)
        assert message.mpid == b"ABCD"
        assert message.stock == b"AAPL  "
        assert message.primary == b"Y"


class TestMessageTypeMappings:
    """Test that all message types are properly mapped."""

    def test_all_message_types(self):
        """Verify all message types can be parsed."""
        test_cases = [
            (struct.pack("!cI", b"T", 12345), SecondsMessage),
            (struct.pack("!cIc", b"S", 12345, b"O"), SystemEventMessage),
            (
                struct.pack("!cI6sccIc", b"R", 12345, b"AAPL  ", b"Q", b"N", 100, b"Y"),
                StockDirectoryMessage,
            ),
            (
                struct.pack("!cI6sc5s", b"H", 12345, b"AAPL  ", b"T", b"     "),
                StockTradingActionMessage,
            ),
            (
                struct.pack(
                    "!cI4s6sccc", b"L", 12345, b"ABCD", b"AAPL  ", b"Y", b"N", b"A"
                ),
                MarketParticipantPositionMessage,
            ),
            (
                struct.pack(
                    "!cIQcI6sI", b"A", 12345, 999, b"B", 100, b"AAPL  ", 150000
                ),
                AddOrderMessage,
            ),
            (
                struct.pack(
                    "!cIQcI6sI4s",
                    b"F",
                    12345,
                    999,
                    b"B",
                    100,
                    b"AAPL  ",
                    150000,
                    b"ABCD",
                ),
                AddOrderMPIDMessage,
            ),
            (struct.pack("!cIQIQ", b"E", 12345, 999, 50, 12345), OrderExecutedMessage),
            (
                struct.pack("!cIQIQcI", b"C", 12345, 999, 50, 12345, b"Y", 150000),
                OrderExecutedPriceMessage,
            ),
            (struct.pack("!cIQI", b"X", 12345, 999, 25), OrderCancelMessage),
            (struct.pack("!cIQ", b"D", 12345, 999), OrderDeleteMessage),
            (
                struct.pack("!cIQQII", b"U", 12345, 999, 1000, 100, 150000),
                OrderReplaceMessage,
            ),
            (
                struct.pack(
                    "!cIQcI6sIQ", b"P", 12345, 999, b"S", 100, b"AAPL  ", 150000, 12345
                ),
                TradeMessage,
            ),
            (
                struct.pack(
                    "!cIQ6sIQc", b"Q", 12345, 1000, b"AAPL  ", 150000, 12345, b"O"
                ),
                CrossTradeMessage,
            ),
            (struct.pack("!cIQ", b"B", 12345, 12345), BrokenTradeMessage),
        ]

        for data, expected_class in test_cases:
            message = ITCH4MarketMessage.from_bytes(data)
            assert isinstance(message, expected_class), (
                f"Failed for {expected_class.__name__}"
            )
