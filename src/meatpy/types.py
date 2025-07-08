"""Type definitions for the MeatPy library.

This module defines the core type variables used throughout the MeatPy library
for representing market data types with flexibility for different numeric and
identifier formats.
"""

from decimal import Decimal
from typing import TypeVar

# Type variables for market data
Price = TypeVar("Price", int, Decimal)

Volume = TypeVar("Volume", int, Decimal)

OrderID = TypeVar("OrderID", int, str, bytes)

TradeRef = TypeVar("TradeRef", int, str, bytes)

Qualifiers = TypeVar("Qualifiers", dict[str, str], dict[str, int])
