from decimal import Decimal
from typing import Union

Volume = Union[int, Decimal]
Price = Union[int, Decimal]
OrderID = Union[int, str, bytes]
TradeRef = Union[int, str, bytes]
