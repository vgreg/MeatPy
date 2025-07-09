"""Tests for the trading status module."""

from meatpy.trading_status import (
    ClosedTradingStatus,
    ClosingAuctionTradingStatus,
    HaltedTradingStatus,
    PostTradeTradingStatus,
    PreTradeTradingStatus,
    QuoteOnlyTradingStatus,
    TradeTradingStatus,
    TradingStatus,
)


class TestTradingStatusBase:
    """Test base TradingStatus class."""

    def test_init_with_details(self):
        """Test initialization with details."""
        status = TradingStatus("Market is closed for holiday")
        assert status.details == "Market is closed for holiday"

    def test_init_without_details(self):
        """Test initialization without details."""
        status = TradingStatus()
        assert status.details is None

    def test_init_with_none_details(self):
        """Test initialization with None details."""
        status = TradingStatus(None)
        assert status.details is None

    def test_repr(self):
        """Test string representation."""
        status = TradingStatus("Test details")
        assert "Generic TradingStatus object" in repr(status)

    def test_str(self):
        """Test human-readable string."""
        status = TradingStatus("Test details")
        assert str(status) == "N/A"


class TestPreTradeTradingStatus:
    """Test PreTradeTradingStatus class."""

    def test_init_with_details(self):
        """Test initialization with details."""
        status = PreTradeTradingStatus("Pre-market session")
        assert status.details == "Pre-market session"

    def test_init_without_details(self):
        """Test initialization without details."""
        status = PreTradeTradingStatus()
        assert status.details is None

    def test_repr(self):
        """Test string representation."""
        status = PreTradeTradingStatus("Test details")
        assert "Pre-Trade TradingStatus" in repr(status)

    def test_str(self):
        """Test human-readable string."""
        status = PreTradeTradingStatus("Test details")
        assert str(status) == "Pre-Trade"


class TestTradeTradingStatus:
    """Test TradeTradingStatus class."""

    def test_init_with_details(self):
        """Test initialization with details."""
        status = TradeTradingStatus("Regular trading hours")
        assert status.details == "Regular trading hours"

    def test_init_without_details(self):
        """Test initialization without details."""
        status = TradeTradingStatus()
        assert status.details is None

    def test_repr(self):
        """Test string representation."""
        status = TradeTradingStatus("Test details")
        assert "Trade TradingStatus" in repr(status)

    def test_str(self):
        """Test human-readable string."""
        status = TradeTradingStatus("Test details")
        assert str(status) == "Trade"


class TestPostTradeTradingStatus:
    """Test PostTradeTradingStatus class."""

    def test_init_with_details(self):
        """Test initialization with details."""
        status = PostTradeTradingStatus("After-hours trading")
        assert status.details == "After-hours trading"

    def test_init_without_details(self):
        """Test initialization without details."""
        status = PostTradeTradingStatus()
        assert status.details is None

    def test_repr(self):
        """Test string representation."""
        status = PostTradeTradingStatus("Test details")
        assert "Post-Trade TradingStatus" in repr(status)

    def test_str(self):
        """Test human-readable string."""
        status = PostTradeTradingStatus("Test details")
        assert str(status) == "Post-Trade"


class TestHaltedTradingStatus:
    """Test HaltedTradingStatus class."""

    def test_init_with_details(self):
        """Test initialization with details."""
        status = HaltedTradingStatus("Trading halted due to volatility")
        assert status.details == "Trading halted due to volatility"

    def test_init_without_details(self):
        """Test initialization without details."""
        status = HaltedTradingStatus()
        assert status.details is None

    def test_repr(self):
        """Test string representation."""
        status = HaltedTradingStatus("Test details")
        assert "Halted TradingStatus" in repr(status)

    def test_str(self):
        """Test human-readable string."""
        status = HaltedTradingStatus("Test details")
        assert str(status) == "Halted"


class TestQuoteOnlyTradingStatus:
    """Test QuoteOnlyTradingStatus class."""

    def test_init_with_details(self):
        """Test initialization with details."""
        status = QuoteOnlyTradingStatus("Quotes only, no trades")
        assert status.details == "Quotes only, no trades"

    def test_init_without_details(self):
        """Test initialization without details."""
        status = QuoteOnlyTradingStatus()
        assert status.details is None

    def test_repr(self):
        """Test string representation."""
        status = QuoteOnlyTradingStatus("Test details")
        assert "QuoteOnly TradingStatus" in repr(status)

    def test_str(self):
        """Test human-readable string."""
        status = QuoteOnlyTradingStatus("Test details")
        assert str(status) == "QuoteOnly"


class TestClosingAuctionTradingStatus:
    """Test ClosingAuctionTradingStatus class."""

    def test_init_with_details(self):
        """Test initialization with details."""
        status = ClosingAuctionTradingStatus("Closing auction in progress")
        assert status.details == "Closing auction in progress"

    def test_init_without_details(self):
        """Test initialization without details."""
        status = ClosingAuctionTradingStatus()
        assert status.details is None

    def test_repr(self):
        """Test string representation."""
        status = ClosingAuctionTradingStatus("Test details")
        assert "ClosingAuction TradingStatus" in repr(status)

    def test_str(self):
        """Test human-readable string."""
        status = ClosingAuctionTradingStatus("Test details")
        assert str(status) == "ClosingAuction"


class TestClosedTradingStatus:
    """Test ClosedTradingStatus class."""

    def test_init_with_details(self):
        """Test initialization with details."""
        status = ClosedTradingStatus("Market closed for the day")
        assert status.details == "Market closed for the day"

    def test_init_without_details(self):
        """Test initialization without details."""
        status = ClosedTradingStatus()
        assert status.details is None

    def test_repr(self):
        """Test string representation."""
        status = ClosedTradingStatus("Test details")
        assert "Closed TradingStatus" in repr(status)

    def test_str(self):
        """Test human-readable string."""
        status = ClosedTradingStatus("Test details")
        assert str(status) == "Closed"


class TestTradingStatusInheritance:
    """Test trading status inheritance relationships."""

    def test_all_statuses_inherit_from_base(self):
        """Test that all status classes inherit from TradingStatus."""
        statuses = [
            PreTradeTradingStatus(),
            TradeTradingStatus(),
            PostTradeTradingStatus(),
            HaltedTradingStatus(),
            QuoteOnlyTradingStatus(),
            ClosingAuctionTradingStatus(),
            ClosedTradingStatus(),
        ]

        for status in statuses:
            assert isinstance(status, TradingStatus)

    def test_status_types_are_different(self):
        """Test that different status types are distinct."""
        pre_trade = PreTradeTradingStatus()
        trade = TradeTradingStatus()
        post_trade = PostTradeTradingStatus()
        halted = HaltedTradingStatus()
        quote_only = QuoteOnlyTradingStatus()
        closing_auction = ClosingAuctionTradingStatus()
        closed = ClosedTradingStatus()

        # All should be different types
        assert type(pre_trade) is not type(trade)
        assert type(trade) is not type(post_trade)
        assert type(post_trade) is not type(halted)
        assert type(halted) is not type(quote_only)
        assert type(quote_only) is not type(closing_auction)
        assert type(closing_auction) is not type(closed)


class TestTradingStatusComparison:
    """Test trading status comparison and equality."""

    def test_same_status_equality(self):
        """Test that same status types are equal."""
        status1 = TradeTradingStatus("Regular trading")
        status2 = TradeTradingStatus("Regular trading")
        assert status1 == status2

    def test_different_status_inequality(self):
        """Test that different status types are not equal."""
        pre_trade = PreTradeTradingStatus()
        trade = TradeTradingStatus()
        assert pre_trade != trade

    def test_same_status_different_details(self):
        """Test that same status types with different details are equal."""
        status1 = TradeTradingStatus("Regular trading")
        status2 = TradeTradingStatus("Normal hours")
        assert status1 == status2

    def test_status_with_and_without_details(self):
        """Test that status with and without details are equal."""
        status1 = TradeTradingStatus("Regular trading")
        status2 = TradeTradingStatus()
        assert status1 == status2


class TestTradingStatusEdgeCases:
    """Test trading status edge cases."""

    def test_empty_string_details(self):
        """Test status with empty string details."""
        status = TradingStatus("")
        assert status.details == ""

    def test_unicode_details(self):
        """Test status with unicode details."""
        status = TradingStatus("Trading halted due to 波动性")
        assert status.details == "Trading halted due to 波动性"

    def test_long_details(self):
        """Test status with very long details."""
        long_details = "A" * 1000
        status = TradingStatus(long_details)
        assert status.details == long_details

    def test_special_characters_details(self):
        """Test status with special characters in details."""
        special_details = "Trading halted due to @#$%^&*()_+-=[]{}|;':\",./<>?"
        status = TradingStatus(special_details)
        assert status.details == special_details


class TestTradingStatusUsage:
    """Test trading status usage patterns."""

    def test_status_transition_sequence(self):
        """Test a typical trading day status sequence."""
        pre_trade = PreTradeTradingStatus("Pre-market session")
        trade = TradeTradingStatus("Regular trading hours")
        closing_auction = ClosingAuctionTradingStatus("Closing auction")
        closed = ClosedTradingStatus("Market closed")

        # Verify all are different status types
        assert type(pre_trade) is not type(trade)
        assert type(trade) is not type(closing_auction)
        assert type(closing_auction) is not type(closed)

        # Verify string representations
        assert str(pre_trade) == "Pre-Trade"
        assert str(trade) == "Trade"
        assert str(closing_auction) == "ClosingAuction"
        assert str(closed) == "Closed"

    def test_halt_scenario(self):
        """Test trading halt scenario."""
        trade = TradeTradingStatus("Regular trading")
        halted = HaltedTradingStatus("Circuit breaker triggered")
        trade_resumed = TradeTradingStatus("Trading resumed")

        # Verify status changes
        assert type(trade) is type(trade_resumed)
        assert type(trade) is not type(halted)

    def test_quote_only_scenario(self):
        """Test quote-only scenario."""
        trade = TradeTradingStatus("Regular trading")
        quote_only = QuoteOnlyTradingStatus("Quotes only during volatility")
        trade_resumed = TradeTradingStatus("Trading resumed")

        # Verify status changes
        assert type(trade) is type(trade_resumed)
        assert type(trade) is not type(quote_only)
