"""IEX DEEP market data subpackage.

This package provides message types, parsers, processors, and readers for handling
IEX DEEP market data in MeatPy.

IEX DEEP provides real-time depth of book quotations and last sale information from
the Investors Exchange (IEX). Unlike ITCH 5.0, IEX DEEP provides aggregated price
level updates rather than individual orders.

Key differences from ITCH 5.0:
- Little endian byte order (vs big endian for ITCH)
- Timestamps are nanoseconds since POSIX epoch (vs nanoseconds since midnight)
- Price levels are aggregated (vs individual orders)
- Data is delivered in PCAP files with IEX-TP transport protocol
"""

from .iex_deep_market_message import (
    AuctionInformationMessage,
    IEXDEEPMarketMessage,
    OperationalHaltStatusMessage,
    OfficialPriceMessage,
    PriceLevelUpdateBuySideMessage,
    PriceLevelUpdateMessage,
    PriceLevelUpdateSellSideMessage,
    SecurityDirectoryMessage,
    SecurityEventMessage,
    ShortSalePriceTestStatusMessage,
    SystemEventMessage,
    TradeBreakMessage,
    TradeReportMessage,
    TradingStatusMessage,
)
from .iex_deep_market_processor import IEXDEEPMarketProcessor
from .iex_deep_message_reader import IEXDEEPMessageReader

__all__ = [
    # Main classes
    "IEXDEEPMarketMessage",
    "IEXDEEPMarketProcessor",
    "IEXDEEPMessageReader",
    # Message types
    "AuctionInformationMessage",
    "OperationalHaltStatusMessage",
    "OfficialPriceMessage",
    "PriceLevelUpdateBuySideMessage",
    "PriceLevelUpdateMessage",
    "PriceLevelUpdateSellSideMessage",
    "SecurityDirectoryMessage",
    "SecurityEventMessage",
    "ShortSalePriceTestStatusMessage",
    "SystemEventMessage",
    "TradeBreakMessage",
    "TradeReportMessage",
    "TradingStatusMessage",
]
