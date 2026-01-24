"""Tests for IEX DEEP market processor functionality."""

import struct

from meatpy.iex_deep.iex_deep_market_processor import (
    IEXDEEPMarketProcessor,
    InvalidMessageTypeError,
)
from meatpy.iex_deep.iex_deep_market_message import IEXDEEPMarketMessage
from meatpy.trading_status import (
    HaltedTradingStatus,
    PreTradeTradingStatus,
    TradeTradingStatus,
    PostTradeTradingStatus,
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


def make_trade_break(
    symbol: bytes,
    price: int,
    size: int,
    trade_id: int,
    timestamp: int = 1527599700000000000,
):
    """Helper to create a trade break message."""
    data = struct.pack(
        "<c B q 8s I q q", b"B", 0x00, timestamp, symbol, size, price, trade_id
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


def make_operational_halt(
    symbol: bytes, status: bytes, timestamp: int = 1527599700000000000
):
    """Helper to create an operational halt message."""
    data = struct.pack("<c c q 8s", b"O", status, timestamp, symbol)
    return IEXDEEPMarketMessage.from_bytes(data)


def make_short_sale_status(
    symbol: bytes, status: int, timestamp: int = 1527599700000000000
):
    """Helper to create a short sale status message."""
    data = struct.pack("<c B q 8s c", b"P", status, timestamp, symbol, b"A")
    return IEXDEEPMarketMessage.from_bytes(data)


def make_security_event(
    symbol: bytes, event: bytes, timestamp: int = 1527599700000000000
):
    """Helper to create a security event message."""
    data = struct.pack("<c c q 8s", b"E", event, timestamp, symbol)
    return IEXDEEPMarketMessage.from_bytes(data)


def make_official_price(
    symbol: bytes, price_type: bytes, price: int, timestamp: int = 1527599700000000000
):
    """Helper to create an official price message."""
    data = struct.pack("<c c q 8s q", b"X", price_type, timestamp, symbol, price)
    return IEXDEEPMarketMessage.from_bytes(data)


def make_security_directory(symbol: bytes, timestamp: int = 1527599700000000000):
    """Helper to create a security directory message."""
    data = struct.pack(
        "<c B q 8s I q B",
        b"D",
        0x00,  # flags
        timestamp,
        symbol,
        100,  # round_lot_size
        1500000,  # adjusted_poc_price
        1,  # luld_tier
    )
    return IEXDEEPMarketMessage.from_bytes(data)


def make_auction_info(
    symbol: bytes, auction_type: bytes, timestamp: int = 1527599700000000000
):
    """Helper to create an auction information message."""
    data = struct.pack(
        "<c c q 8s I q q I c B I q q q q",
        b"A",
        auction_type,
        timestamp,
        symbol,
        1000,  # paired_shares
        1850000,  # reference_price
        1851000,  # indicative_clearing_price
        200,  # imbalance_shares
        b"B",  # imbalance_side
        0,  # extension_number
        34200,  # scheduled_auction_time
        1850500,  # auction_book_clearing_price
        1850000,  # collar_reference_price
        1840000,  # lower_auction_collar
        1860000,  # upper_auction_collar
    )
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

    def test_ask_level_removal(self):
        """Test that size=0 removes an ask price level."""
        processor = IEXDEEPMarketProcessor("AAPL")

        # Add an ask level
        message1 = make_sell_price_level(b"AAPL    ", 1851000, 500)
        processor.process_message(message1)
        assert 1851000 in processor._ask_levels

        # Remove with size=0
        message2 = make_sell_price_level(b"AAPL    ", 1851000, 0)
        processor.process_message(message2)
        assert 1851000 not in processor._ask_levels

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

    def test_trade_break_processing(self):
        """Test processing trade break messages."""
        processor = IEXDEEPMarketProcessor("AAPL")

        # First add a trade
        trade_msg = make_trade(b"AAPL    ", 1850000, 100, 12345)
        processor.process_message(trade_msg)
        assert 12345 in processor._trade_ids

        # Then break it
        break_msg = make_trade_break(b"AAPL    ", 1850000, 100, 12345)
        processor.process_message(break_msg)
        assert 12345 not in processor._trade_ids

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

    def test_trading_status_halted(self):
        """Test trading status transitions to halted."""
        processor = IEXDEEPMarketProcessor("AAPL")

        # Trading halted status
        message = make_trading_status(b"AAPL    ", b"H")
        processor.process_message(message)

        assert isinstance(processor.trading_status, HaltedTradingStatus)

    def test_trading_status_paused(self):
        """Test trading status transitions to paused (halted)."""
        processor = IEXDEEPMarketProcessor("AAPL")

        message = make_trading_status(b"AAPL    ", b"P")
        processor.process_message(message)

        assert isinstance(processor.trading_status, HaltedTradingStatus)

    def test_trading_status_order_acceptance(self):
        """Test trading status transitions to order acceptance (pre-trade)."""
        processor = IEXDEEPMarketProcessor("AAPL")

        message = make_trading_status(b"AAPL    ", b"O")
        processor.process_message(message)

        assert isinstance(processor.trading_status, PreTradeTradingStatus)

    def test_trading_status_trading(self):
        """Test trading status transitions to trading."""
        processor = IEXDEEPMarketProcessor("AAPL")

        message = make_trading_status(b"AAPL    ", b"T")
        processor.process_message(message)

        assert isinstance(processor.trading_status, TradeTradingStatus)

    def test_operational_halt_processing(self):
        """Test processing operational halt messages."""
        processor = IEXDEEPMarketProcessor("AAPL")

        message = make_operational_halt(b"AAPL    ", b"O")
        processor.process_message(message)

        assert processor.operational_halt_status == b"O"
        assert isinstance(processor.trading_status, HaltedTradingStatus)

    def test_operational_halt_cleared(self):
        """Test operational halt cleared."""
        processor = IEXDEEPMarketProcessor("AAPL")

        # First halt
        halt_msg = make_operational_halt(b"AAPL    ", b"O")
        processor.process_message(halt_msg)
        assert isinstance(processor.trading_status, HaltedTradingStatus)

        # Then clear
        clear_msg = make_operational_halt(b"AAPL    ", b"N")
        processor.process_message(clear_msg)
        assert processor.operational_halt_status == b"N"

    def test_short_sale_status_processing(self):
        """Test processing short sale status messages."""
        processor = IEXDEEPMarketProcessor("AAPL")

        message = make_short_sale_status(b"AAPL    ", 1)
        processor.process_message(message)

        assert processor.short_sale_status == 1

    def test_security_event_processing(self):
        """Test processing security event messages."""
        processor = IEXDEEPMarketProcessor("AAPL")

        # Opening process complete
        message = make_security_event(b"AAPL    ", b"O")
        processor.process_message(message)
        # Security events are processed but don't change state directly

    def test_official_price_processing(self):
        """Test processing official price messages."""
        processor = IEXDEEPMarketProcessor("AAPL")

        # Opening price
        message = make_official_price(b"AAPL    ", b"Q", 1850000)
        processor.process_message(message)
        # Official prices trigger events for handlers

    def test_auction_info_processing(self):
        """Test processing auction information messages."""
        processor = IEXDEEPMarketProcessor("AAPL")

        message = make_auction_info(b"AAPL    ", b"O")
        processor.process_message(message)
        # Auction info triggers events for handlers

    def test_security_directory_processing(self):
        """Test processing security directory messages."""
        processor = IEXDEEPMarketProcessor("AAPL")

        message = make_security_directory(b"AAPL    ")
        processor.process_message(message)
        # Security directory is processed for matching symbols

    def test_security_directory_other_symbol(self):
        """Test security directory for non-matching symbol is ignored."""
        processor = IEXDEEPMarketProcessor("AAPL")

        message = make_security_directory(b"GOOG    ")
        processor.process_message(message)
        # Should not affect processor state

    def test_system_event_start_of_messages(self):
        """Test system event start of messages sets pre-trade status."""
        processor = IEXDEEPMarketProcessor("AAPL")

        message = make_system_event(b"O")
        processor.process_message(message)

        assert processor.system_status == b"O"
        assert isinstance(processor.trading_status, PreTradeTradingStatus)

    def test_system_event_start_of_system_hours(self):
        """Test system event start of system hours."""
        processor = IEXDEEPMarketProcessor("AAPL")

        message = make_system_event(b"S")
        processor.process_message(message)

        assert processor.system_status == b"S"
        assert isinstance(processor.trading_status, PreTradeTradingStatus)

    def test_system_event_start_of_regular_hours(self):
        """Test system event start of regular market hours."""
        processor = IEXDEEPMarketProcessor("AAPL")

        message = make_system_event(b"R")
        processor.process_message(message)

        assert processor.system_status == b"R"
        assert isinstance(processor.trading_status, TradeTradingStatus)

    def test_system_event_end_of_regular_hours(self):
        """Test system event end of regular market hours."""
        processor = IEXDEEPMarketProcessor("AAPL")

        message = make_system_event(b"M")
        processor.process_message(message)

        assert processor.system_status == b"M"
        assert isinstance(processor.trading_status, PostTradeTradingStatus)

    def test_system_event_end_of_system_hours(self):
        """Test system event end of system hours."""
        processor = IEXDEEPMarketProcessor("AAPL")

        message = make_system_event(b"E")
        processor.process_message(message)

        assert processor.system_status == b"E"
        assert isinstance(processor.trading_status, PostTradeTradingStatus)

    def test_system_event_end_of_messages(self):
        """Test system event end of messages."""
        processor = IEXDEEPMarketProcessor("AAPL")

        message = make_system_event(b"C")
        processor.process_message(message)

        assert processor.system_status == b"C"
        assert isinstance(processor.trading_status, PostTradeTradingStatus)

    def test_invalid_message_type(self):
        """Test that non-IEX DEEP messages raise error."""
        processor = IEXDEEPMarketProcessor("AAPL")

        # Create a mock message that's not an IEXDEEPMarketMessage
        class FakeMessage:
            pass

        try:
            processor.process_message(FakeMessage())
            assert False, "Should have raised InvalidMessageTypeError"
        except InvalidMessageTypeError:
            pass

    def test_messages_for_other_symbols_ignored(self):
        """Test that all message types for other symbols are ignored."""
        processor = IEXDEEPMarketProcessor("AAPL")

        # Try various message types for wrong symbol
        processor.process_message(make_trading_status(b"GOOG    ", b"T"))
        processor.process_message(make_operational_halt(b"GOOG    ", b"O"))
        processor.process_message(make_short_sale_status(b"GOOG    ", 1))
        processor.process_message(make_security_event(b"GOOG    ", b"O"))
        processor.process_message(make_official_price(b"GOOG    ", b"Q", 1000000))
        processor.process_message(make_trade(b"GOOG    ", 1000000, 100, 999))
        processor.process_message(make_trade_break(b"GOOG    ", 1000000, 100, 999))
        processor.process_message(make_auction_info(b"GOOG    ", b"O"))

        # None should affect AAPL processor state
        assert processor.trading_status_code == b""
        assert processor.operational_halt_status == b""
        assert processor.short_sale_status == 0
        assert len(processor._trade_ids) == 0

    def test_price_level_update_size(self):
        """Test price level size updates."""
        processor = IEXDEEPMarketProcessor("AAPL")

        # Add initial level
        processor.process_message(make_buy_price_level(b"AAPL    ", 1850000, 1000))
        assert processor._bid_levels[1850000] == 1000

        # Update size
        processor.process_message(make_buy_price_level(b"AAPL    ", 1850000, 1500))
        assert processor._bid_levels[1850000] == 1500

        # Update size again
        processor.process_message(make_buy_price_level(b"AAPL    ", 1850000, 500))
        assert processor._bid_levels[1850000] == 500
