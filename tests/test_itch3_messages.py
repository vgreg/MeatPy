"""Tests for ITCH 3.0 market message functionality."""

import json
import pytest

from meatpy.itch3.itch3_market_message import (
    ITCH3MarketMessage,
    SecondsMessage,
    MillisecondsMessage,
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
    TradeMessage,
    CrossTradeMessage,
    BrokenTradeMessage,
    NoiiMessage,
)


class TestITCH3MarketMessage:
    """Test the base ITCH3MarketMessage class."""

    def test_from_bytes_unknown_type(self):
        """Test handling of unknown message types."""
        data = b"Z" + b"0" * 20
        with pytest.raises(ValueError, match="Unknown message type"):
            ITCH3MarketMessage.from_bytes(data)

    def test_from_bytes_too_short(self):
        """Test handling of message that is too short."""
        data = b""
        with pytest.raises(ValueError, match="Message too short"):
            ITCH3MarketMessage.from_bytes(data)

    def test_from_json_unknown_type(self):
        """Test handling of unknown message type in JSON."""
        json_str = json.dumps({"message_type": "Z"})
        with pytest.raises(ValueError, match="Unknown message type"):
            ITCH3MarketMessage.from_json(json_str)


class TestSecondsMessage:
    """Test SecondsMessage functionality."""

    def test_from_bytes_data(self):
        """Test creating message from bytes."""
        # Format: T + seconds(5) = 6 chars
        data = b"T12345"

        message = ITCH3MarketMessage.from_bytes(data)

        assert isinstance(message, SecondsMessage)
        assert message.seconds == 12345

    def test_to_bytes(self):
        """Test converting message to bytes."""
        message = SecondsMessage()
        message.seconds = 12345

        data = message.to_bytes()

        assert data == b"T12345"

    def test_json_roundtrip(self):
        """Test JSON serialization and deserialization."""
        message = SecondsMessage()
        message.seconds = 54321

        json_str = message.to_json()
        new_message = ITCH3MarketMessage.from_json(json_str)

        assert isinstance(new_message, SecondsMessage)
        assert new_message.seconds == message.seconds


class TestMillisecondsMessage:
    """Test MillisecondsMessage functionality."""

    def test_from_bytes_data(self):
        """Test creating message from bytes."""
        # Format: M + milliseconds(3) = 4 chars
        data = b"M123"

        message = ITCH3MarketMessage.from_bytes(data)

        assert isinstance(message, MillisecondsMessage)
        assert message.milliseconds == 123

    def test_to_bytes(self):
        """Test converting message to bytes."""
        message = MillisecondsMessage()
        message.milliseconds = 456

        data = message.to_bytes()

        assert data == b"M456"

    def test_json_roundtrip(self):
        """Test JSON serialization and deserialization."""
        message = MillisecondsMessage()
        message.milliseconds = 789

        json_str = message.to_json()
        new_message = ITCH3MarketMessage.from_json(json_str)

        assert isinstance(new_message, MillisecondsMessage)
        assert new_message.milliseconds == message.milliseconds


class TestSystemEventMessage:
    """Test SystemEventMessage functionality."""

    def test_from_bytes_data(self):
        """Test creating message from bytes."""
        # Format: S + event_code(1) = 2 chars
        data = b"SO"

        message = ITCH3MarketMessage.from_bytes(data)

        assert isinstance(message, SystemEventMessage)
        assert message.event_code == b"O"

    def test_to_bytes(self):
        """Test converting message to bytes."""
        message = SystemEventMessage()
        message.event_code = b"Q"

        data = message.to_bytes()

        assert data == b"SQ"

    def test_json_roundtrip(self):
        """Test JSON serialization and deserialization."""
        message = SystemEventMessage()
        message.event_code = b"M"

        json_str = message.to_json()
        new_message = ITCH3MarketMessage.from_json(json_str)

        assert isinstance(new_message, SystemEventMessage)
        assert new_message.event_code == message.event_code


class TestStockDirectoryMessage:
    """Test StockDirectoryMessage functionality."""

    def test_from_bytes_data(self):
        """Test creating message from bytes."""
        # Format: R + stock(6) + market_category(1) + financial_status(1) + round_lot_size(6) + round_lots_only(1) = 16 chars
        data = b"RAAPL  QN   100Y"

        message = ITCH3MarketMessage.from_bytes(data)

        assert isinstance(message, StockDirectoryMessage)
        assert message.stock == b"AAPL  "
        assert message.market_category == b"Q"
        assert message.financial_status == b"N"
        assert message.round_lot_size == 100
        assert message.round_lots_only == b"Y"

    def test_from_bytes_with_spaces_in_lot_size(self):
        """Test handling spaces in round lot size field."""
        data = b"RAAPL  QN     1Y"  # Spaces before 1

        message = ITCH3MarketMessage.from_bytes(data)

        assert isinstance(message, StockDirectoryMessage)
        assert message.round_lot_size == 1

    def test_to_bytes(self):
        """Test converting message to bytes."""
        message = StockDirectoryMessage()
        message.stock = b"MSFT  "
        message.market_category = b"G"
        message.financial_status = b"D"
        message.round_lot_size = 100
        message.round_lots_only = b"N"

        data = message.to_bytes()

        assert data == b"RMSFT  GD   100N"

    def test_json_roundtrip(self):
        """Test JSON serialization and deserialization."""
        message = StockDirectoryMessage()
        message.stock = b"GOOG  "
        message.market_category = b"Q"
        message.financial_status = b"N"
        message.round_lot_size = 100
        message.round_lots_only = b"Y"

        json_str = message.to_json()
        new_message = ITCH3MarketMessage.from_json(json_str)

        assert isinstance(new_message, StockDirectoryMessage)
        assert new_message.stock.decode().rstrip() == "GOOG"


class TestAddOrderMessage:
    """Test AddOrderMessage functionality."""

    def test_from_bytes_data(self):
        """Test creating message from bytes."""
        # Format: A + order_ref(9) + side(1) + shares(6) + stock(6) + price(10) = 33 chars
        data = b"A000000001B000100AAPL  0000150000"

        message = ITCH3MarketMessage.from_bytes(data)

        assert isinstance(message, AddOrderMessage)
        assert message.order_ref == 1
        assert message.side == b"B"
        assert message.shares == 100
        assert message.stock == b"AAPL  "
        assert message.price == 150000

    def test_to_bytes(self):
        """Test converting message to bytes."""
        message = AddOrderMessage()
        message.order_ref = 1
        message.side = b"S"
        message.shares = 200
        message.stock = b"MSFT  "
        message.price = 250000

        data = message.to_bytes()

        assert data == b"A        1S   200MSFT  0000250000"

    def test_json_roundtrip(self):
        """Test JSON serialization and deserialization."""
        message = AddOrderMessage()
        message.order_ref = 999
        message.side = b"B"
        message.shares = 100
        message.stock = b"AAPL  "
        message.price = 150000

        json_str = message.to_json()
        new_message = ITCH3MarketMessage.from_json(json_str)

        assert isinstance(new_message, AddOrderMessage)
        assert new_message.order_ref == message.order_ref


class TestAddOrderMPIDMessage:
    """Test AddOrderMPIDMessage functionality."""

    def test_from_bytes_data(self):
        """Test creating message from bytes."""
        # Format: F + order_ref(9) + side(1) + shares(6) + stock(6) + price(10) + mpid(4) = 37 chars
        data = b"F000000001B000100AAPL  0000150000ABCD"

        message = ITCH3MarketMessage.from_bytes(data)

        assert isinstance(message, AddOrderMPIDMessage)
        assert message.order_ref == 1
        assert message.side == b"B"
        assert message.shares == 100
        assert message.stock == b"AAPL  "
        assert message.price == 150000
        assert message.mpid == b"ABCD"

    def test_to_bytes(self):
        """Test converting message to bytes."""
        message = AddOrderMPIDMessage()
        message.order_ref = 1
        message.side = b"S"
        message.shares = 200
        message.stock = b"MSFT  "
        message.price = 250000
        message.mpid = b"WXYZ"

        data = message.to_bytes()

        assert data == b"F        1S   200MSFT  0000250000WXYZ"


class TestOrderExecutedMessage:
    """Test OrderExecutedMessage functionality."""

    def test_from_bytes_data(self):
        """Test creating message from bytes."""
        # Format: E + order_ref(9) + shares(6) + match_number(9) = 25 chars
        data = b"E000000001000050000000123"

        message = ITCH3MarketMessage.from_bytes(data)

        assert isinstance(message, OrderExecutedMessage)
        assert message.order_ref == 1
        assert message.shares == 50
        assert message.match_number == 123

    def test_to_bytes(self):
        """Test converting message to bytes."""
        message = OrderExecutedMessage()
        message.order_ref = 1
        message.shares = 50
        message.match_number = 123

        data = message.to_bytes()

        assert data == b"E        1    50      123"


class TestOrderExecutedPriceMessage:
    """Test OrderExecutedPriceMessage functionality."""

    def test_from_bytes_data(self):
        """Test creating message from bytes."""
        # Format: C + order_ref(9) + shares(6) + match_number(9) + printable(1) + price(10) = 36 chars
        data = b"C000000001000050000000123Y0000150000"

        message = ITCH3MarketMessage.from_bytes(data)

        assert isinstance(message, OrderExecutedPriceMessage)
        assert message.order_ref == 1
        assert message.shares == 50
        assert message.match_number == 123
        assert message.printable == b"Y"
        assert message.price == 150000

    def test_to_bytes(self):
        """Test converting message to bytes."""
        message = OrderExecutedPriceMessage()
        message.order_ref = 1
        message.shares = 50
        message.match_number = 123
        message.printable = b"Y"
        message.price = 150000

        data = message.to_bytes()

        assert data == b"C        1    50      123Y0000150000"


class TestOrderCancelMessage:
    """Test OrderCancelMessage functionality."""

    def test_from_bytes_data(self):
        """Test creating message from bytes."""
        # Format: X + order_ref(9) + shares(6) = 16 chars
        data = b"X000000001000025"

        message = ITCH3MarketMessage.from_bytes(data)

        assert isinstance(message, OrderCancelMessage)
        assert message.order_ref == 1
        assert message.shares == 25

    def test_to_bytes(self):
        """Test converting message to bytes."""
        message = OrderCancelMessage()
        message.order_ref = 1
        message.shares = 25

        data = message.to_bytes()

        assert data == b"X        1    25"


class TestOrderDeleteMessage:
    """Test OrderDeleteMessage functionality."""

    def test_from_bytes_data(self):
        """Test creating message from bytes."""
        # Format: D + order_ref(9) = 10 chars
        data = b"D000000001"

        message = ITCH3MarketMessage.from_bytes(data)

        assert isinstance(message, OrderDeleteMessage)
        assert message.order_ref == 1

    def test_to_bytes(self):
        """Test converting message to bytes."""
        message = OrderDeleteMessage()
        message.order_ref = 999

        data = message.to_bytes()

        assert data == b"D      999"


class TestTradeMessage:
    """Test TradeMessage functionality."""

    def test_from_bytes_data(self):
        """Test creating message from bytes."""
        # Format: P + order_ref(9) + side(1) + shares(6) + stock(6) + price(10) + match_number(9) = 42 chars
        data = b"P000000001S000100AAPL  0000150000000000123"

        message = ITCH3MarketMessage.from_bytes(data)

        assert isinstance(message, TradeMessage)
        assert message.order_ref == 1
        assert message.side == b"S"
        assert message.shares == 100
        assert message.stock == b"AAPL  "
        assert message.price == 150000
        assert message.match_number == 123


class TestCrossTradeMessage:
    """Test CrossTradeMessage functionality."""

    def test_from_bytes_data(self):
        """Test creating message from bytes."""
        # Format: Q + shares(9) + stock(6) + price(10) + match_number(9) + cross_type(1) = 36 chars
        data = b"Q000001000AAPL  0000150000000000123O"

        message = ITCH3MarketMessage.from_bytes(data)

        assert isinstance(message, CrossTradeMessage)
        assert message.shares == 1000
        assert message.stock == b"AAPL  "
        assert message.price == 150000
        assert message.match_number == 123
        assert message.cross_type == b"O"


class TestBrokenTradeMessage:
    """Test BrokenTradeMessage functionality."""

    def test_from_bytes_data(self):
        """Test creating message from bytes."""
        # Format: B + match_number(9) = 10 chars
        data = b"B000000123"

        message = ITCH3MarketMessage.from_bytes(data)

        assert isinstance(message, BrokenTradeMessage)
        assert message.match_number == 123

    def test_to_bytes(self):
        """Test converting message to bytes."""
        message = BrokenTradeMessage()
        message.match_number = 456

        data = message.to_bytes()

        assert data == b"B      456"


class TestNoiiMessage:
    """Test NoiiMessage functionality."""

    def test_from_bytes_data(self):
        """Test creating message from bytes."""
        # Format: I + paired_shares(9) + imbalance_shares(9) + imbalance_direction(1)
        #         + stock(6) + far_price(10) + near_price(10) + ref_price(10) + cross_type(2) = 58 chars
        data = b"I000010000000005000BAAPL  000015000000001500000000150000OC"

        message = ITCH3MarketMessage.from_bytes(data)

        assert isinstance(message, NoiiMessage)
        assert message.paired_shares == 10000
        assert message.imbalance_shares == 5000
        assert message.imbalance_direction == b"B"
        assert message.stock == b"AAPL  "
        assert message.far_price == 150000
        assert message.near_price == 150000
        assert message.ref_price == 150000
        assert message.cross_type == b"OC"


class TestStockTradingActionMessage:
    """Test StockTradingActionMessage functionality."""

    def test_from_bytes_data(self):
        """Test creating message from bytes."""
        # Format: H + stock(6) + state(1) + reserved(5) = 13 chars
        data = b"HAAPL  T     "

        message = ITCH3MarketMessage.from_bytes(data)

        assert isinstance(message, StockTradingActionMessage)
        assert message.stock == b"AAPL  "
        assert message.state == b"T"


class TestMarketParticipantPositionMessage:
    """Test MarketParticipantPositionMessage functionality."""

    def test_from_bytes_data(self):
        """Test creating message from bytes."""
        # Format: L + stock(6) + mpid(4) + primary_mm(1) + mode(1) + state(1) = 14 chars
        data = b"LAAPL  ABCDYNA"

        message = ITCH3MarketMessage.from_bytes(data)

        assert isinstance(message, MarketParticipantPositionMessage)
        assert message.stock == b"AAPL  "
        assert message.mpid == b"ABCD"
        assert message.primary_mm == b"Y"
        assert message.mode == b"N"
        assert message.state == b"A"


class TestMessageTypeMappings:
    """Test that all message types are properly mapped."""

    def test_all_message_types_registered(self):
        """Verify all message types can be parsed."""
        test_cases = [
            (b"T12345", SecondsMessage),
            (b"M123", MillisecondsMessage),
            (b"SO", SystemEventMessage),
            (b"RAAPL  QN   100Y", StockDirectoryMessage),
            (b"HAAPL  T     ", StockTradingActionMessage),
            (b"LAAPL  ABCDYNA", MarketParticipantPositionMessage),
            (b"A000000001B000100AAPL  0000150000", AddOrderMessage),
            (b"F000000001B000100AAPL  0000150000ABCD", AddOrderMPIDMessage),
            (b"E000000001000050000000123", OrderExecutedMessage),
            (b"C000000001000050000000123Y0000150000", OrderExecutedPriceMessage),
            (b"X000000001000025", OrderCancelMessage),
            (b"D000000001", OrderDeleteMessage),
            (b"P000000001S000100AAPL  0000150000000000123", TradeMessage),
            (b"Q000001000AAPL  0000150000000000123O", CrossTradeMessage),
            (b"B000000123", BrokenTradeMessage),
            (
                b"I000010000000005000BAAPL  000015000000001500000000150000OC",
                NoiiMessage,
            ),
        ]

        for data, expected_class in test_cases:
            message = ITCH3MarketMessage.from_bytes(data)
            assert isinstance(message, expected_class), (
                f"Failed for {expected_class.__name__}"
            )
