"""Tests for IEX DEEP market processor functionality."""

import struct


from meatpy.iex_deep.iex_deep_market_processor import IEXDEEPMarketProcessor
from meatpy.iex_deep.iex_deep_market_message import (
    IEXDEEPMarketMessage,
)


def make_buy_price_level(
    symbol: bytes, price: int, size: int, timestamp: int = 1527599700000000000
):
    """Helper to create a buy price level update message."""
    data = struct.pack("<c B q 8s I q", b"8", 0x01, timestamp, symbol, size, price)
    return IEXDEEPMarketMessage.from_bytes(data)


def make_sell_price_level(
    symbol: bytes, price: int, size: int, timestamp: int = 1527599700000000000
):
    """Helper to create a sell price level update message."""
    data = struct.pack("<c B q 8s I q", b"5", 0x01, timestamp, symbol, size, price)
    return IEXDEEPMarketMessage.from_bytes(data)


def make_trade(
    symbol: bytes,
    price: int,
    size: int,
    trade_id: int,
    timestamp: int = 1527599700000000000,
):
    """Helper to create a trade report message."""
    data = struct.pack(
        "<c B q 8s I q q", b"T", 0x00, timestamp, symbol, size, price, trade_id
    )
    return IEXDEEPMarketMessage.from_bytes(data)


def make_system_event(system_event: bytes, timestamp: int = 1527599700000000000):
    """Helper to create a system event message."""
    data = struct.pack("<c c q", b"S", system_event, timestamp)
    return IEXDEEPMarketMessage.from_bytes(data)


def make_trading_status(
    symbol: bytes, status: bytes, timestamp: int = 1527599700000000000
):
    """Helper to create a trading status message."""
    data = struct.pack("<c c q 8s 4s", b"H", status, timestamp, symbol, b"    ")
    return IEXDEEPMarketMessage.from_bytes(data)


class TestIEXDEEPMarketProcessor:
    """Test the IEXDEEPMarketProcessor class."""

    def test_initialization(self):
        """Test processor initialization."""
        processor = IEXDEEPMarketProcessor("AAPL")
        assert processor.instrument == b"AAPL    "
        assert processor._bid_levels == {}
        assert processor._ask_levels == {}
        assert processor.track_lob is False

    def test_initialization_with_bytes_symbol(self):
        """Test processor initialization with bytes symbol."""
        processor = IEXDEEPMarketProcessor(b"SPY     ")
        assert processor.instrument == b"SPY     "

    def test_price_level_update_bid(self):
        """Test processing bid price level update."""
        processor = IEXDEEPMarketProcessor("AAPL")

        message = make_buy_price_level(b"AAPL    ", 1850000, 1000)
        processor.process_message(message)

        assert 1850000 in processor._bid_levels
        assert processor._bid_levels[1850000] == 1000

    def test_price_level_update_ask(self):
        """Test processing ask price level update."""
        processor = IEXDEEPMarketProcessor("AAPL")

        message = make_sell_price_level(b"AAPL    ", 1851000, 500)
        processor.process_message(message)

        assert 1851000 in processor._ask_levels
        assert processor._ask_levels[1851000] == 500

    def test_price_level_removal(self):
        """Test that size=0 removes a price level."""
        processor = IEXDEEPMarketProcessor("AAPL")

        # Add a price level
        message1 = make_buy_price_level(b"AAPL    ", 1850000, 1000)
        processor.process_message(message1)

        assert 1850000 in processor._bid_levels

        # Remove the price level with size=0
        message2 = make_buy_price_level(b"AAPL    ", 1850000, 0)
        processor.process_message(message2)

        assert 1850000 not in processor._bid_levels

    def test_get_best_bid(self):
        """Test getting best bid."""
        processor = IEXDEEPMarketProcessor("AAPL")

        # Add multiple bid levels
        for price, size in [(1850000, 1000), (1849000, 500), (1851000, 200)]:
            message = make_buy_price_level(b"AAPL    ", price, size)
            processor.process_message(message)

        best_bid = processor.get_best_bid()
        assert best_bid is not None
        assert best_bid[0] == 1851000  # Highest bid price
        assert best_bid[1] == 200

    def test_get_best_ask(self):
        """Test getting best ask."""
        processor = IEXDEEPMarketProcessor("AAPL")

        # Add multiple ask levels
        for price, size in [(1852000, 1000), (1853000, 500), (1851000, 200)]:
            message = make_sell_price_level(b"AAPL    ", price, size)
            processor.process_message(message)

        best_ask = processor.get_best_ask()
        assert best_ask is not None
        assert best_ask[0] == 1851000  # Lowest ask price
        assert best_ask[1] == 200

    def test_get_bbo(self):
        """Test getting best bid and offer."""
        processor = IEXDEEPMarketProcessor("AAPL")

        # Add bid level
        bid_msg = make_buy_price_level(b"AAPL    ", 1850000, 1000)
        processor.process_message(bid_msg)

        # Add ask level
        ask_msg = make_sell_price_level(b"AAPL    ", 1851000, 500)
        processor.process_message(ask_msg)

        bbo = processor.get_bbo()
        assert bbo[0] == (1850000, 1000)  # Best bid
        assert bbo[1] == (1851000, 500)  # Best ask

    def test_trade_processing(self):
        """Test processing trade messages."""
        processor = IEXDEEPMarketProcessor("AAPL")

        message = make_trade(b"AAPL    ", 1850000, 100, 12345)
        processor.process_message(message)

        assert 12345 in processor._trade_ids

    def test_ignores_other_symbols(self):
        """Test that processor ignores messages for other symbols."""
        processor = IEXDEEPMarketProcessor("AAPL")

        # Create message for different symbol
        message = make_buy_price_level(b"GOOG    ", 1500000, 100)
        processor.process_message(message)

        # Should not be processed
        assert len(processor._bid_levels) == 0

    def test_timestamp_adjustment(self):
        """Test timestamp conversion."""
        processor = IEXDEEPMarketProcessor("AAPL")

        # May 29, 2018 12:00:00 UTC in nanoseconds since epoch
        raw_timestamp = 1527595200000000000

        ts = processor.adjust_timestamp(raw_timestamp)

        # Timestamp is a subclass of datetime, so it has year/month/day properties
        assert ts.year == 2018
        assert ts.month == 5
        assert ts.day == 29

    def test_system_event_processing(self):
        """Test processing system event messages."""
        processor = IEXDEEPMarketProcessor("AAPL")

        message = make_system_event(b"O")
        processor.process_message(message)

        assert processor.system_status == b"O"

    def test_trading_status_processing(self):
        """Test processing trading status messages."""
        processor = IEXDEEPMarketProcessor("AAPL")

        message = make_trading_status(b"AAPL    ", b"T")
        processor.process_message(message)

        assert processor.trading_status_code == b"T"

    def test_empty_book_returns_none(self):
        """Test that empty book returns None for BBO."""
        processor = IEXDEEPMarketProcessor("AAPL")

        assert processor.get_best_bid() is None
        assert processor.get_best_ask() is None
        bbo = processor.get_bbo()
        assert bbo == (None, None)
