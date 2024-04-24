from typing import Optional


class TradingStatus:
    def __init__(self, details: Optional[str] = None):
        self.details: str | None = details

    def __repr__(self):
        return "Generic TradingStatus object"

    def __str__(self):
        return "N/A"


class PreTradeTradingStatus(TradingStatus):
    def __init__(self, details: Optional[str] = None):
        self.details: str | None = details

    def __repr__(self):
        return "Pre-Trade TradingStatus"

    def __str__(self):
        return "Pre-Trade"


class TradeTradingStatus(TradingStatus):
    def __init__(self, details: Optional[str] = None):
        self.details: str | None = details

    def __repr__(self):
        return "Trade TradingStatus"

    def __str__(self):
        return "Trade"


class PostTradeTradingStatus(TradingStatus):
    def __init__(self, details: Optional[str] = None):
        self.details: str | None = details

    def __repr__(self):
        return "Post-Trade TradingStatus"

    def __str__(self):
        return "Post-Trade"


class HaltedTradingStatus(TradingStatus):
    def __init__(self, details: Optional[str] = None):
        self.details: str | None = details

    def __repr__(self):
        return "Halted TradingStatus"

    def __str__(self):
        return "Halted"


class QuoteOnlyTradingStatus(TradingStatus):
    def __init__(self, details: Optional[str] = None):
        self.details: str | None = details

    def __repr__(self):
        return "QuoteOnly TradingStatus"

    def __str__(self):
        return "QuoteOnly"


class ClosingAuctionTradingStatus(TradingStatus):
    def __init__(self, details: Optional[str] = None):
        self.details: str | None = details

    def __repr__(self):
        return "Closing Auction TradingStatus"

    def __str__(self):
        return "Closing Auction"


class ClosedTradingStatus(TradingStatus):
    def __init__(self, details: Optional[str] = None):
        self.details: str | None = details

    def __repr__(self):
        return "Closed TradingStatus"

    def __str__(self):
        return "Closed"
