"""Type definitions for the MeatPy library.

This module defines the core types used throughout the MeatPy library
for representing market data with proper type safety.
"""

from decimal import Decimal
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    pass

# Generic type variables for market data
# These ensure type consistency within a single MarketProcessor instance
Price = TypeVar("Price", int, Decimal)
Volume = TypeVar("Volume", int, Decimal)
OrderID = TypeVar("OrderID", int, str, bytes)
TradeRef = TypeVar("TradeRef", int, str, bytes)
Qualifiers = TypeVar("Qualifiers", dict[str, str], dict[str, int])


# Note: Event classes are not defined here to avoid complicating the generic type system.
# Instead, use the existing event handler system in market_event_handler.py for type-safe event handling.
# The MarketProcessor class already provides type-safe event methods with proper generic typing.
