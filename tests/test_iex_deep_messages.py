"""Tests for IEX DEEP market message functionality."""

import json
import struct

import pytest

from meatpy.iex_deep.iex_deep_market_message import (
    IEXDEEPMarketMessage,
    SystemEventMessage,
    SecurityDirectoryMessage,
    TradingStatusMessage,
    PriceLevelUpdateBuySideMessage,
    PriceLevelUpdateSellSideMessage,
    TradeReportMessage,
)


class TestSystemEventMessage:
    """Test SystemEventMessage functionality."""

    def test_from_bytes(self):
        """Test creating message from bytes."""
        # IEX DEEP format: message_type(1) + system_event(1) + timestamp(8)
        timestamp = 1527599700000000000  # nanoseconds since POSIX epoch
        system_event = b"O"  # Start of messages

        # Pack the data in little endian
        data = struct.pack("<c c q", b"S", system_event, timestamp)

        # Create message from bytes
        message = IEXDEEPMarketMessage.from_bytes(data)

        assert isinstance(message, SystemEventMessage)
        assert message.timestamp == timestamp
        assert message.system_event == system_event

    def test_to_bytes(self):
        """Test converting message to bytes."""
        message = SystemEventMessage(system_event=b"O", timestamp=1527599700000000000)

        data = message.to_bytes()

        # Verify the packed data
        expected = struct.pack("<c b q", b"S", ord(b"O"), 1527599700000000000)
        assert data == expected

    def test_to_json(self):
        """Test JSON serialization."""
        message = SystemEventMessage(system_event=b"O", timestamp=1527599700000000000)

        json_str = message.to_json()
        data = json.loads(json_str)

        assert data["timestamp"] == 1527599700000000000
        assert data["message_type"] == "S"
        assert data["system_event"] == "O"


class TestSecurityDirectoryMessage:
    """Test SecurityDirectoryMessage functionality."""

    def test_from_bytes(self):
        """Test creating message from bytes."""
        # Format: message_type(1) + flags(1) + timestamp(8) + symbol(8) +
        #         round_lot_size(4) + adjusted_poc_price(8) + luld_tier(1)
        timestamp = 1527599700000000000
        flags = 0x80  # Test flag bit
        symbol = b"AAPL    "
        round_lot_size = 100
        adjusted_poc_price = 1500000  # $150.0000 (4 decimal places)
        luld_tier = 1

        data = struct.pack(
            "<c B q 8s I q B",
            b"D",
            flags,
            timestamp,
            symbol,
            round_lot_size,
            adjusted_poc_price,
            luld_tier,
        )

        message = IEXDEEPMarketMessage.from_bytes(data)

        assert isinstance(message, SecurityDirectoryMessage)
        assert message.timestamp == timestamp
        assert message.flags == flags
        assert message.symbol == symbol
        assert message.round_lot_size == round_lot_size
        assert message.adjusted_poc_price == adjusted_poc_price
        assert message.luld_tier == luld_tier


class TestPriceLevelUpdateMessage:
    """Test PriceLevelUpdate messages functionality."""

    def test_buy_side_from_bytes(self):
        """Test creating buy side price level update from bytes."""
        # Format: message_type(1) + event_flags(1) + timestamp(8) + symbol(8) +
        #         size(4) + price(8)
        timestamp = 1527599700000000000
        event_flags = 0x01
        symbol = b"SPY     "
        size = 1000
        price = 2700000  # $270.0000 (4 decimal places)

        data = struct.pack(
            "<c B q 8s I q", b"8", event_flags, timestamp, symbol, size, price
        )

        message = IEXDEEPMarketMessage.from_bytes(data)

        assert isinstance(message, PriceLevelUpdateBuySideMessage)
        assert message.timestamp == timestamp
        assert message.event_flags == event_flags
        assert message.symbol == symbol
        assert message.size == size
        assert message.price == price

    def test_sell_side_from_bytes(self):
        """Test creating sell side price level update from bytes."""
        timestamp = 1527599700000000000
        event_flags = 0x01
        symbol = b"SPY     "
        size = 500
        price = 2701000  # $270.1000

        data = struct.pack(
            "<c B q 8s I q", b"5", event_flags, timestamp, symbol, size, price
        )

        message = IEXDEEPMarketMessage.from_bytes(data)

        assert isinstance(message, PriceLevelUpdateSellSideMessage)
        assert message.timestamp == timestamp
        assert message.size == size
        assert message.price == price


class TestTradeReportMessage:
    """Test TradeReportMessage functionality."""

    def test_from_bytes(self):
        """Test creating trade report from bytes."""
        # Format: message_type(1) + sale_condition_flags(1) + timestamp(8) +
        #         symbol(8) + size(4) + price(8) + trade_id(8)
        timestamp = 1527599700000000000
        sale_condition_flags = 0x00
        symbol = b"AAPL    "
        size = 100
        price = 1850000  # $185.0000
        trade_id = 12345678

        data = struct.pack(
            "<c B q 8s I q q",
            b"T",
            sale_condition_flags,
            timestamp,
            symbol,
            size,
            price,
            trade_id,
        )

        message = IEXDEEPMarketMessage.from_bytes(data)

        assert isinstance(message, TradeReportMessage)
        assert message.timestamp == timestamp
        assert message.symbol == symbol
        assert message.size == size
        assert message.price == price
        assert message.trade_id == trade_id


class TestTradingStatusMessage:
    """Test TradingStatusMessage functionality."""

    def test_from_bytes(self):
        """Test creating trading status message from bytes."""
        # Format: message_type(1) + trading_status(1) + timestamp(8) +
        #         symbol(8) + reason(4)
        timestamp = 1527599700000000000
        trading_status = b"T"  # Trading
        symbol = b"AAPL    "
        reason = b"    "

        data = struct.pack(
            "<c c q 8s 4s", b"H", trading_status, timestamp, symbol, reason
        )

        message = IEXDEEPMarketMessage.from_bytes(data)

        assert isinstance(message, TradingStatusMessage)
        assert message.timestamp == timestamp
        assert message.trading_status == trading_status
        assert message.symbol == symbol
        assert message.reason == reason


class TestUnknownMessageType:
    """Test handling of unknown message types."""

    def test_unknown_message_type_raises(self):
        """Test that unknown message type raises UnknownMessageTypeError."""
        from meatpy.message_reader import UnknownMessageTypeError

        # Create data with invalid message type
        data = struct.pack("<c q", b"Z", 1527599700000000000)

        with pytest.raises(UnknownMessageTypeError):
            IEXDEEPMarketMessage.from_bytes(data)
