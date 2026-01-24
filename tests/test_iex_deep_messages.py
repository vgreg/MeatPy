"""Tests for IEX DEEP market message functionality."""

import json
import struct

import pytest

from meatpy.iex_deep.iex_deep_market_message import (
    IEXDEEPMarketMessage,
    SystemEventMessage,
    SecurityDirectoryMessage,
    TradingStatusMessage,
    OperationalHaltStatusMessage,
    ShortSalePriceTestStatusMessage,
    SecurityEventMessage,
    PriceLevelUpdateBuySideMessage,
    PriceLevelUpdateSellSideMessage,
    TradeReportMessage,
    OfficialPriceMessage,
    TradeBreakMessage,
    AuctionInformationMessage,
)
from meatpy.message_reader import UnknownMessageTypeError


class TestSystemEventMessage:
    """Test SystemEventMessage functionality."""

    def test_from_bytes(self):
        """Test creating message from bytes."""
        timestamp = 1527599700000000000
        system_event = b"O"

        data = struct.pack("<c c q", b"S", system_event, timestamp)
        message = IEXDEEPMarketMessage.from_bytes(data)

        assert isinstance(message, SystemEventMessage)
        assert message.timestamp == timestamp
        assert message.system_event == system_event

    def test_to_bytes(self):
        """Test converting message to bytes."""
        message = SystemEventMessage(system_event=b"O", timestamp=1527599700000000000)
        data = message.to_bytes()
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

    def test_roundtrip(self):
        """Test that from_bytes(to_bytes()) returns equivalent message."""
        original = SystemEventMessage(system_event=b"R", timestamp=1527599700000000000)
        data = original.to_bytes()
        restored = IEXDEEPMarketMessage.from_bytes(data)

        assert isinstance(restored, SystemEventMessage)
        assert restored.timestamp == original.timestamp
        assert restored.system_event == original.system_event


class TestSecurityDirectoryMessage:
    """Test SecurityDirectoryMessage functionality."""

    def test_from_bytes(self):
        """Test creating message from bytes."""
        timestamp = 1527599700000000000
        flags = 0x80
        symbol = b"AAPL    "
        round_lot_size = 100
        adjusted_poc_price = 1500000
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

    def test_to_bytes(self):
        """Test converting message to bytes."""
        message = SecurityDirectoryMessage(
            flags=0x80,
            timestamp=1527599700000000000,
            symbol=b"AAPL    ",
            round_lot_size=100,
            adjusted_poc_price=1500000,
            luld_tier=1,
        )
        data = message.to_bytes()
        restored = IEXDEEPMarketMessage.from_bytes(data)

        assert restored.symbol == message.symbol
        assert restored.round_lot_size == message.round_lot_size

    def test_to_json(self):
        """Test JSON serialization."""
        message = SecurityDirectoryMessage(
            flags=0x80,
            timestamp=1527599700000000000,
            symbol=b"AAPL    ",
            round_lot_size=100,
            adjusted_poc_price=1500000,
            luld_tier=1,
        )
        json_str = message.to_json()
        data = json.loads(json_str)

        assert data["symbol"] == "AAPL"
        assert data["round_lot_size"] == 100
        assert data["adjusted_poc_price"] == 150.0
        assert data["luld_tier"] == 1

    def test_flag_properties(self):
        """Test flag property methods."""
        # Test security flag (bit 7)
        message = SecurityDirectoryMessage(
            flags=0x80,
            timestamp=1527599700000000000,
            symbol=b"TEST    ",
            round_lot_size=100,
            adjusted_poc_price=1000000,
            luld_tier=1,
        )
        assert message.is_test_security is True
        assert message.is_when_issued is False
        assert message.is_etp is False

        # When issued flag (bit 6)
        message2 = SecurityDirectoryMessage(
            flags=0x40,
            timestamp=1527599700000000000,
            symbol=b"TEST    ",
            round_lot_size=100,
            adjusted_poc_price=1000000,
            luld_tier=1,
        )
        assert message2.is_test_security is False
        assert message2.is_when_issued is True
        assert message2.is_etp is False

        # ETP flag (bit 5)
        message3 = SecurityDirectoryMessage(
            flags=0x20,
            timestamp=1527599700000000000,
            symbol=b"SPY     ",
            round_lot_size=100,
            adjusted_poc_price=2700000,
            luld_tier=1,
        )
        assert message3.is_test_security is False
        assert message3.is_when_issued is False
        assert message3.is_etp is True


class TestTradingStatusMessage:
    """Test TradingStatusMessage functionality."""

    def test_from_bytes(self):
        """Test creating trading status message from bytes."""
        timestamp = 1527599700000000000
        trading_status = b"T"
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

    def test_to_bytes(self):
        """Test converting message to bytes."""
        message = TradingStatusMessage(
            trading_status=b"H",
            timestamp=1527599700000000000,
            symbol=b"AAPL    ",
            reason=b"HALT",
        )
        data = message.to_bytes()
        restored = IEXDEEPMarketMessage.from_bytes(data)

        assert restored.trading_status == message.trading_status
        assert restored.symbol == message.symbol
        assert restored.reason == message.reason

    def test_to_json(self):
        """Test JSON serialization."""
        message = TradingStatusMessage(
            trading_status=b"T",
            timestamp=1527599700000000000,
            symbol=b"AAPL    ",
            reason=b"    ",
        )
        json_str = message.to_json()
        data = json.loads(json_str)

        assert data["trading_status"] == "T"
        assert data["symbol"] == "AAPL"
        assert data["reason"] == ""


class TestOperationalHaltStatusMessage:
    """Test OperationalHaltStatusMessage functionality."""

    def test_from_bytes(self):
        """Test creating operational halt message from bytes."""
        timestamp = 1527599700000000000
        status = b"O"
        symbol = b"AAPL    "

        data = struct.pack("<c c q 8s", b"O", status, timestamp, symbol)
        message = IEXDEEPMarketMessage.from_bytes(data)

        assert isinstance(message, OperationalHaltStatusMessage)
        assert message.operational_halt_status == status
        assert message.symbol == symbol

    def test_to_bytes(self):
        """Test converting message to bytes."""
        message = OperationalHaltStatusMessage(
            operational_halt_status=b"N",
            timestamp=1527599700000000000,
            symbol=b"AAPL    ",
        )
        data = message.to_bytes()
        restored = IEXDEEPMarketMessage.from_bytes(data)

        assert restored.operational_halt_status == message.operational_halt_status
        assert restored.symbol == message.symbol

    def test_to_json(self):
        """Test JSON serialization."""
        message = OperationalHaltStatusMessage(
            operational_halt_status=b"O",
            timestamp=1527599700000000000,
            symbol=b"AAPL    ",
        )
        json_str = message.to_json()
        data = json.loads(json_str)

        assert data["operational_halt_status"] == "O"
        assert data["symbol"] == "AAPL"


class TestShortSalePriceTestStatusMessage:
    """Test ShortSalePriceTestStatusMessage functionality."""

    def test_from_bytes(self):
        """Test creating short sale message from bytes."""
        timestamp = 1527599700000000000
        status = 1  # In effect
        symbol = b"AAPL    "
        detail = b"A"

        data = struct.pack("<c B q 8s c", b"P", status, timestamp, symbol, detail)
        message = IEXDEEPMarketMessage.from_bytes(data)

        assert isinstance(message, ShortSalePriceTestStatusMessage)
        assert message.short_sale_price_test_status == status
        assert message.symbol == symbol
        assert message.detail == detail

    def test_to_bytes(self):
        """Test converting message to bytes."""
        message = ShortSalePriceTestStatusMessage(
            short_sale_price_test_status=1,
            timestamp=1527599700000000000,
            symbol=b"AAPL    ",
            detail=b"A",
        )
        data = message.to_bytes()
        restored = IEXDEEPMarketMessage.from_bytes(data)

        assert (
            restored.short_sale_price_test_status
            == message.short_sale_price_test_status
        )
        assert restored.symbol == message.symbol

    def test_to_json(self):
        """Test JSON serialization."""
        message = ShortSalePriceTestStatusMessage(
            short_sale_price_test_status=1,
            timestamp=1527599700000000000,
            symbol=b"AAPL    ",
            detail=b"A",
        )
        json_str = message.to_json()
        data = json.loads(json_str)

        assert data["short_sale_price_test_status"] == 1
        assert data["symbol"] == "AAPL"
        assert data["detail"] == "A"


class TestSecurityEventMessage:
    """Test SecurityEventMessage functionality."""

    def test_from_bytes(self):
        """Test creating security event message from bytes."""
        timestamp = 1527599700000000000
        event = b"O"  # Opening Process Complete
        symbol = b"AAPL    "

        data = struct.pack("<c c q 8s", b"E", event, timestamp, symbol)
        message = IEXDEEPMarketMessage.from_bytes(data)

        assert isinstance(message, SecurityEventMessage)
        assert message.security_event == event
        assert message.symbol == symbol

    def test_to_bytes(self):
        """Test converting message to bytes."""
        message = SecurityEventMessage(
            security_event=b"C",  # Closing Process Complete
            timestamp=1527599700000000000,
            symbol=b"AAPL    ",
        )
        data = message.to_bytes()
        restored = IEXDEEPMarketMessage.from_bytes(data)

        assert restored.security_event == message.security_event
        assert restored.symbol == message.symbol

    def test_to_json(self):
        """Test JSON serialization."""
        message = SecurityEventMessage(
            security_event=b"O",
            timestamp=1527599700000000000,
            symbol=b"AAPL    ",
        )
        json_str = message.to_json()
        data = json.loads(json_str)

        assert data["security_event"] == "O"
        assert data["symbol"] == "AAPL"


class TestPriceLevelUpdateMessage:
    """Test PriceLevelUpdate messages functionality."""

    def test_buy_side_from_bytes(self):
        """Test creating buy side price level update from bytes."""
        timestamp = 1527599700000000000
        event_flags = 0x01
        symbol = b"SPY     "
        size = 1000
        price = 2700000

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
        price = 2701000

        data = struct.pack(
            "<c B q 8s I q", b"5", event_flags, timestamp, symbol, size, price
        )

        message = IEXDEEPMarketMessage.from_bytes(data)

        assert isinstance(message, PriceLevelUpdateSellSideMessage)
        assert message.timestamp == timestamp
        assert message.size == size
        assert message.price == price

    def test_buy_side_to_bytes(self):
        """Test converting buy side message to bytes."""
        message = PriceLevelUpdateBuySideMessage(
            event_flags=0x01,
            timestamp=1527599700000000000,
            symbol=b"SPY     ",
            size=1000,
            price=2700000,
        )
        data = message.to_bytes()
        restored = IEXDEEPMarketMessage.from_bytes(data)

        assert isinstance(restored, PriceLevelUpdateBuySideMessage)
        assert restored.price == message.price
        assert restored.size == message.size

    def test_sell_side_to_bytes(self):
        """Test converting sell side message to bytes."""
        message = PriceLevelUpdateSellSideMessage(
            event_flags=0x01,
            timestamp=1527599700000000000,
            symbol=b"SPY     ",
            size=500,
            price=2701000,
        )
        data = message.to_bytes()
        restored = IEXDEEPMarketMessage.from_bytes(data)

        assert isinstance(restored, PriceLevelUpdateSellSideMessage)
        assert restored.price == message.price
        assert restored.size == message.size

    def test_to_json(self):
        """Test JSON serialization."""
        message = PriceLevelUpdateBuySideMessage(
            event_flags=0x01,
            timestamp=1527599700000000000,
            symbol=b"SPY     ",
            size=1000,
            price=2700000,
        )
        json_str = message.to_json()
        data = json.loads(json_str)

        assert data["symbol"] == "SPY"
        assert data["size"] == 1000
        assert data["price"] == 270.0


class TestTradeReportMessage:
    """Test TradeReportMessage functionality."""

    def test_from_bytes(self):
        """Test creating trade report from bytes."""
        timestamp = 1527599700000000000
        sale_condition_flags = 0x00
        symbol = b"AAPL    "
        size = 100
        price = 1850000
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

    def test_to_bytes(self):
        """Test converting message to bytes."""
        message = TradeReportMessage(
            sale_condition_flags=0x00,
            timestamp=1527599700000000000,
            symbol=b"AAPL    ",
            size=100,
            price=1850000,
            trade_id=12345678,
        )
        data = message.to_bytes()
        restored = IEXDEEPMarketMessage.from_bytes(data)

        assert restored.trade_id == message.trade_id
        assert restored.price == message.price

    def test_to_json(self):
        """Test JSON serialization."""
        message = TradeReportMessage(
            sale_condition_flags=0x00,
            timestamp=1527599700000000000,
            symbol=b"AAPL    ",
            size=100,
            price=1850000,
            trade_id=12345678,
        )
        json_str = message.to_json()
        data = json.loads(json_str)

        assert data["symbol"] == "AAPL"
        assert data["size"] == 100
        assert data["price"] == 185.0
        assert data["trade_id"] == 12345678

    def test_sale_condition_flags(self):
        """Test sale condition flag properties."""
        # ISO flag (bit 7)
        message = TradeReportMessage(
            sale_condition_flags=0x80,
            timestamp=1527599700000000000,
            symbol=b"AAPL    ",
            size=100,
            price=1850000,
            trade_id=12345678,
        )
        assert message.is_intermarket_sweep is True
        assert message.is_extended_hours is False
        assert message.is_odd_lot is False
        assert message.is_trade_through_exempt is False
        assert message.is_single_price_cross is False

        # Extended hours (bit 6)
        message2 = TradeReportMessage(
            sale_condition_flags=0x40,
            timestamp=1527599700000000000,
            symbol=b"AAPL    ",
            size=100,
            price=1850000,
            trade_id=12345678,
        )
        assert message2.is_extended_hours is True

        # Odd lot (bit 5)
        message3 = TradeReportMessage(
            sale_condition_flags=0x20,
            timestamp=1527599700000000000,
            symbol=b"AAPL    ",
            size=50,
            price=1850000,
            trade_id=12345678,
        )
        assert message3.is_odd_lot is True

        # Trade through exempt (bit 4)
        message4 = TradeReportMessage(
            sale_condition_flags=0x10,
            timestamp=1527599700000000000,
            symbol=b"AAPL    ",
            size=100,
            price=1850000,
            trade_id=12345678,
        )
        assert message4.is_trade_through_exempt is True

        # Single price cross (bit 3)
        message5 = TradeReportMessage(
            sale_condition_flags=0x08,
            timestamp=1527599700000000000,
            symbol=b"AAPL    ",
            size=100,
            price=1850000,
            trade_id=12345678,
        )
        assert message5.is_single_price_cross is True


class TestOfficialPriceMessage:
    """Test OfficialPriceMessage functionality."""

    def test_from_bytes(self):
        """Test creating official price message from bytes."""
        timestamp = 1527599700000000000
        price_type = b"Q"  # Opening price
        symbol = b"AAPL    "
        price = 1850000

        data = struct.pack("<c c q 8s q", b"X", price_type, timestamp, symbol, price)
        message = IEXDEEPMarketMessage.from_bytes(data)

        assert isinstance(message, OfficialPriceMessage)
        assert message.price_type == price_type
        assert message.symbol == symbol
        assert message.official_price == price

    def test_to_bytes(self):
        """Test converting message to bytes."""
        message = OfficialPriceMessage(
            price_type=b"M",  # Closing price
            timestamp=1527599700000000000,
            symbol=b"AAPL    ",
            official_price=1855000,
        )
        data = message.to_bytes()
        restored = IEXDEEPMarketMessage.from_bytes(data)

        assert restored.price_type == message.price_type
        assert restored.official_price == message.official_price

    def test_to_json(self):
        """Test JSON serialization."""
        message = OfficialPriceMessage(
            price_type=b"Q",
            timestamp=1527599700000000000,
            symbol=b"AAPL    ",
            official_price=1850000,
        )
        json_str = message.to_json()
        data = json.loads(json_str)

        assert data["price_type"] == "Q"
        assert data["symbol"] == "AAPL"
        assert data["official_price"] == 185.0


class TestTradeBreakMessage:
    """Test TradeBreakMessage functionality."""

    def test_from_bytes(self):
        """Test creating trade break message from bytes."""
        timestamp = 1527599700000000000
        flags = 0x00
        symbol = b"AAPL    "
        size = 100
        price = 1850000
        trade_id = 12345678

        data = struct.pack(
            "<c B q 8s I q q", b"B", flags, timestamp, symbol, size, price, trade_id
        )
        message = IEXDEEPMarketMessage.from_bytes(data)

        assert isinstance(message, TradeBreakMessage)
        assert message.symbol == symbol
        assert message.size == size
        assert message.price == price
        assert message.trade_id == trade_id

    def test_to_bytes(self):
        """Test converting message to bytes."""
        message = TradeBreakMessage(
            sale_condition_flags=0x00,
            timestamp=1527599700000000000,
            symbol=b"AAPL    ",
            size=100,
            price=1850000,
            trade_id=12345678,
        )
        data = message.to_bytes()
        restored = IEXDEEPMarketMessage.from_bytes(data)

        assert restored.trade_id == message.trade_id
        assert restored.price == message.price

    def test_to_json(self):
        """Test JSON serialization."""
        message = TradeBreakMessage(
            sale_condition_flags=0x00,
            timestamp=1527599700000000000,
            symbol=b"AAPL    ",
            size=100,
            price=1850000,
            trade_id=12345678,
        )
        json_str = message.to_json()
        data = json.loads(json_str)

        assert data["symbol"] == "AAPL"
        assert data["trade_id"] == 12345678


class TestAuctionInformationMessage:
    """Test AuctionInformationMessage functionality."""

    def test_from_bytes(self):
        """Test creating auction info message from bytes."""
        timestamp = 1527599700000000000
        auction_type = b"O"  # Opening
        symbol = b"AAPL    "
        paired_shares = 1000
        reference_price = 1850000
        indicative_clearing_price = 1851000
        imbalance_shares = 200
        imbalance_side = b"B"
        extension_number = 0
        scheduled_auction_time = 34200
        auction_book_clearing_price = 1850500
        collar_reference_price = 1850000
        lower_auction_collar = 1840000
        upper_auction_collar = 1860000

        data = struct.pack(
            "<c c q 8s I q q I c B I q q q q",
            b"A",
            auction_type,
            timestamp,
            symbol,
            paired_shares,
            reference_price,
            indicative_clearing_price,
            imbalance_shares,
            imbalance_side,
            extension_number,
            scheduled_auction_time,
            auction_book_clearing_price,
            collar_reference_price,
            lower_auction_collar,
            upper_auction_collar,
        )
        message = IEXDEEPMarketMessage.from_bytes(data)

        assert isinstance(message, AuctionInformationMessage)
        assert message.auction_type == auction_type
        assert message.symbol == symbol
        assert message.paired_shares == paired_shares
        assert message.imbalance_side == imbalance_side

    def test_to_bytes(self):
        """Test converting message to bytes."""
        message = AuctionInformationMessage(
            auction_type=b"C",  # Closing
            timestamp=1527599700000000000,
            symbol=b"AAPL    ",
            paired_shares=1000,
            reference_price=1850000,
            indicative_clearing_price=1851000,
            imbalance_shares=200,
            imbalance_side=b"S",
            extension_number=0,
            scheduled_auction_time=57600,
            auction_book_clearing_price=1850500,
            collar_reference_price=1850000,
            lower_auction_collar=1840000,
            upper_auction_collar=1860000,
        )
        data = message.to_bytes()
        restored = IEXDEEPMarketMessage.from_bytes(data)

        assert restored.auction_type == message.auction_type
        assert restored.paired_shares == message.paired_shares

    def test_to_json(self):
        """Test JSON serialization."""
        message = AuctionInformationMessage(
            auction_type=b"O",
            timestamp=1527599700000000000,
            symbol=b"AAPL    ",
            paired_shares=1000,
            reference_price=1850000,
            indicative_clearing_price=1851000,
            imbalance_shares=200,
            imbalance_side=b"B",
            extension_number=0,
            scheduled_auction_time=34200,
            auction_book_clearing_price=1850500,
            collar_reference_price=1850000,
            lower_auction_collar=1840000,
            upper_auction_collar=1860000,
        )
        json_str = message.to_json()
        data = json.loads(json_str)

        assert data["auction_type"] == "O"
        assert data["symbol"] == "AAPL"
        assert data["paired_shares"] == 1000
        assert data["reference_price"] == 185.0


class TestUnknownMessageType:
    """Test handling of unknown message types."""

    def test_unknown_message_type_raises(self):
        """Test that unknown message type raises UnknownMessageTypeError."""
        data = struct.pack("<c q", b"Z", 1527599700000000000)

        with pytest.raises(UnknownMessageTypeError):
            IEXDEEPMarketMessage.from_bytes(data)

    def test_empty_data_raises(self):
        """Test that empty data raises ValueError."""
        with pytest.raises(ValueError):
            IEXDEEPMarketMessage.from_bytes(b"")
