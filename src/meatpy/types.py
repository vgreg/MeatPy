from decimal import Decimal

Volume = int | Decimal
Price = int | Decimal
OrderID = int | str | bytes
TradeRef = int | str | bytes
Qualifiers = dict[str, str | int | float | Decimal]
