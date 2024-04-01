"""
The goal of this project is to provide a standard framework for processing and analysing high-frequency financial data.
MeatPy can be used to process event-time data from multiple financial exchanges and formats, such as Nasdaq ITCH.

This package contains some subpackages and submodules:

**Subpackages:**

* event_handlers
* itch50

**Submodules:**

* level
* lob (Limit Order Book)
* market_event_handler
* market_processor
* message_parser
* timestamp
* trading_status

"""

from meatpy.level import (
    ExecutionPriorityException,
    Level,
    OrderOnBook,
    VolumeInconsistencyException,
)
from meatpy.lob import (
    ExecutionPriorityExceptionList,
    InexistantValueException,
    LimitOrderBook,
)
from meatpy.market_processor import MarketProcessor
from meatpy.trading_status import (
    ClosedTradingStatus,
    ClosingAuctionTradingStatus,
    HaltedTradingStatus,
    PostTradeTradingStatus,
    PreTradeTradingStatus,
    QuoteOnlyTradingStatus,
    TradeTradingStatus,
)

__all__ = [
    "ExecutionPriorityException",
    "VolumeInconsistencyException",
    "OrderOnBook",
    "Level",
    "InexistantValueException",
    "ExecutionPriorityExceptionList",
    "LimitOrderBook",
    "MarketProcessor",
    "TradeTradingStatus",
    "HaltedTradingStatus",
    "PreTradeTradingStatus",
    "PostTradeTradingStatus",
    "QuoteOnlyTradingStatus",
    "ClosingAuctionTradingStatus",
    "ClosedTradingStatus",
]
