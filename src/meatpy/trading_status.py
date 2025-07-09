"""Trading status classes for market state management.

This module defines various trading status classes that represent different
states of market trading, from pre-trade to closed states.
"""


class TradingStatus:
    """Base class for all trading status types.

    This is a generic trading status that can be used when the specific
    status is not known or not important.

    Attributes:
        details: Optional details about the trading status
    """

    def __init__(self, details: str | None = None):
        """Initialize a trading status.

        Args:
            details: Optional details about the trading status
        """
        self.details: str | None = details

    def __repr__(self):
        """Return string representation.

        Returns:
            str: Generic trading status representation
        """
        return "Generic TradingStatus object"

    def __str__(self):
        """Return human-readable string.

        Returns:
            str: "N/A" for generic status
        """
        return "N/A"


class PreTradeTradingStatus(TradingStatus):
    """Trading status indicating pre-trade period.

    This status indicates that the market is in a pre-trade state,
    typically before regular trading hours begin.
    """

    def __init__(self, details: str | None = None):
        """Initialize a pre-trade trading status.

        Args:
            details: Optional details about the pre-trade status
        """
        self.details: str | None = details

    def __repr__(self):
        """Return string representation.

        Returns:
            str: Pre-trade status representation
        """
        return "Pre-Trade TradingStatus"

    def __str__(self):
        """Return human-readable string.

        Returns:
            str: "Pre-Trade"
        """
        return "Pre-Trade"


class TradeTradingStatus(TradingStatus):
    """Trading status indicating active trading period.

    This status indicates that the market is actively trading,
    with orders being accepted and executed.
    """

    def __init__(self, details: str | None = None):
        """Initialize a trade trading status.

        Args:
            details: Optional details about the trading status
        """
        self.details: str | None = details

    def __repr__(self):
        """Return string representation.

        Returns:
            str: Trade status representation
        """
        return "Trade TradingStatus"

    def __str__(self):
        """Return human-readable string.

        Returns:
            str: "Trade"
        """
        return "Trade"


class PostTradeTradingStatus(TradingStatus):
    """Trading status indicating post-trade period.

    This status indicates that the market is in a post-trade state,
    typically after regular trading hours have ended.
    """

    def __init__(self, details: str | None = None):
        """Initialize a post-trade trading status.

        Args:
            details: Optional details about the post-trade status
        """
        self.details: str | None = details

    def __repr__(self):
        """Return string representation.

        Returns:
            str: Post-trade status representation
        """
        return "Post-Trade TradingStatus"

    def __str__(self):
        """Return human-readable string.

        Returns:
            str: "Post-Trade"
        """
        return "Post-Trade"


class HaltedTradingStatus(TradingStatus):
    """Trading status indicating halted trading.

    This status indicates that trading has been halted on the market,
    typically due to regulatory or technical issues.
    """

    def __init__(self, details: str | None = None):
        """Initialize a halted trading status.

        Args:
            details: Optional details about the halt
        """
        self.details: str | None = details

    def __repr__(self):
        """Return string representation.

        Returns:
            str: Halted status representation
        """
        return "Halted TradingStatus"

    def __str__(self):
        """Return human-readable string.

        Returns:
            str: "Halted"
        """
        return "Halted"


class QuoteOnlyTradingStatus(TradingStatus):
    """Trading status indicating quote-only period.

    This status indicates that the market is in quote-only mode,
    where quotes can be entered but trades cannot be executed.
    """

    def __init__(self, details: str | None = None):
        """Initialize a quote-only trading status.

        Args:
            details: Optional details about the quote-only status
        """
        self.details: str | None = details

    def __repr__(self):
        """Return string representation.

        Returns:
            str: Quote-only status representation
        """
        return "QuoteOnly TradingStatus"

    def __str__(self):
        """Return human-readable string.

        Returns:
            str: "QuoteOnly"
        """
        return "QuoteOnly"


class ClosingAuctionTradingStatus(TradingStatus):
    """Trading status indicating closing auction period.

    This status indicates that the market is in a closing auction,
    where orders are matched at a single price to close the trading day.
    """

    def __init__(self, details: str | None = None):
        """Initialize a closing auction trading status.

        Args:
            details: Optional details about the closing auction
        """
        self.details: str | None = details

    def __repr__(self):
        """Return string representation.

        Returns:
            str: Closing auction status representation
        """
        return "Closing Auction TradingStatus"

    def __str__(self):
        """Return human-readable string.

        Returns:
            str: "Closing Auction"
        """
        return "Closing Auction"


class ClosedTradingStatus(TradingStatus):
    """Trading status indicating closed market.

    This status indicates that the market is completely closed
    and no trading activity is possible.
    """

    def __init__(self, details: str | None = None):
        """Initialize a closed trading status.

        Args:
            details: Optional details about the closed status
        """
        self.details: str | None = details

    def __repr__(self):
        """Return string representation.

        Returns:
            str: Closed status representation
        """
        return "Closed TradingStatus"

    def __str__(self):
        """Return human-readable string.

        Returns:
            str: "Closed"
        """
        return "Closed"
