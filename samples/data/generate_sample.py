"""Generate the synthetic ITCH 5.0 sample file shipped at samples/data/sample.itch50.

The output is NOT real market data. It is a hand-crafted sequence of valid
ITCH 5.0 messages for two fictional symbols (MEAT, PYTH), large enough to
exercise the common message types: system events, stock directory, add orders
on both sides, executions, a cancel, a delete, and a trade.

Run from the repository root:

    uv run python samples/data/generate_sample.py
"""

from __future__ import annotations

from pathlib import Path

from meatpy.itch50.itch50_market_message import (
    AddOrderMessage,
    ITCH50MarketMessage,
    OrderCancelMessage,
    OrderDeleteMessage,
    OrderExecutedMessage,
    StockDirectoryMessage,
    SystemEventMessage,
    TradeMessage,
)

NS_PER_SEC = 1_000_000_000
PRICE_SCALE = 10_000  # ITCH 5.0 prices are 4-decimal fixed-point integers.


def _frame(msg: ITCH50MarketMessage) -> bytes:
    return b"\x00" + bytes([msg.message_size]) + msg.to_bytes()


def _stock(symbol: str) -> bytes:
    return symbol.ljust(8).encode("ascii")


def _system_event(ts: int, code: bytes) -> SystemEventMessage:
    m = SystemEventMessage()
    m.timestamp = ts
    m.code = code
    return m


def _stock_directory(ts: int, locate: int, symbol: str) -> StockDirectoryMessage:
    m = StockDirectoryMessage()
    m.stock_locate = locate
    m.timestamp = ts
    m.stock = _stock(symbol)
    m.category = b"Q"
    m.status = b"N"
    m.lotsize = 100
    m.lotsonly = b"N"
    m.issue_class = b"C"
    m.issue_sub = b"  "
    m.authenticity = b"P"
    m.shortsale_thresh = b"N"
    m.ipo_flag = b"N"
    m.luld_ref = b"1"
    m.etp_flag = b"N"
    m.etp_leverage = 0
    m.inverse_ind = b"N"
    return m


def _add_order(
    ts: int,
    locate: int,
    symbol: str,
    order_ref: int,
    side: bytes,
    shares: int,
    price: float,
) -> AddOrderMessage:
    m = AddOrderMessage()
    m.stock_locate = locate
    m.timestamp = ts
    m.order_ref = order_ref
    m.bsindicator = side
    m.shares = shares
    m.stock = _stock(symbol)
    m.price = int(round(price * PRICE_SCALE))
    return m


def _executed(
    ts: int, locate: int, order_ref: int, shares: int, match: int
) -> OrderExecutedMessage:
    m = OrderExecutedMessage()
    m.stock_locate = locate
    m.timestamp = ts
    m.order_ref = order_ref
    m.shares = shares
    m.match = match
    return m


def _cancel(ts: int, locate: int, order_ref: int, shares: int) -> OrderCancelMessage:
    m = OrderCancelMessage()
    m.stock_locate = locate
    m.timestamp = ts
    m.order_ref = order_ref
    m.canceled_shares = shares
    return m


def _delete(ts: int, locate: int, order_ref: int) -> OrderDeleteMessage:
    m = OrderDeleteMessage()
    m.stock_locate = locate
    m.timestamp = ts
    m.order_ref = order_ref
    return m


def _trade(
    ts: int,
    locate: int,
    symbol: str,
    order_ref: int,
    side: bytes,
    shares: int,
    price: float,
    match: int,
) -> TradeMessage:
    m = TradeMessage()
    m.stock_locate = locate
    m.timestamp = ts
    m.order_ref = order_ref
    m.bsindicator = side
    m.shares = shares
    m.stock = _stock(symbol)
    m.price = int(round(price * PRICE_SCALE))
    m.match = match
    return m


def build_messages() -> list[ITCH50MarketMessage]:
    base = 9 * 3600 * NS_PER_SEC  # 09:00:00
    open_ts = base + 30 * 60 * NS_PER_SEC  # 09:30:00
    close_ts = base + 7 * 3600 * NS_PER_SEC  # 16:00:00

    MEAT, PYTH = 1, 2
    msgs: list[ITCH50MarketMessage] = [
        _system_event(base, b"O"),
        _system_event(base + 1_000_000, b"S"),
        _stock_directory(base + 2_000_000, MEAT, "MEAT"),
        _stock_directory(base + 3_000_000, PYTH, "PYTH"),
        _system_event(open_ts, b"Q"),
    ]

    t = open_ts + 1_000_000
    step = 500_000  # 0.5 ms

    msgs += [
        _add_order(t + 0 * step, MEAT, "MEAT", 1001, b"B", 200, 100.00),
        _add_order(t + 1 * step, MEAT, "MEAT", 1002, b"B", 100, 99.95),
        _add_order(t + 2 * step, MEAT, "MEAT", 1003, b"S", 150, 100.05),
        _add_order(t + 3 * step, MEAT, "MEAT", 1004, b"S", 200, 100.10),
        _add_order(t + 4 * step, PYTH, "PYTH", 2001, b"B", 50, 42.50),
        _add_order(t + 5 * step, PYTH, "PYTH", 2002, b"S", 75, 42.75),
        _executed(t + 6 * step, MEAT, 1003, 150, 9001),
        _trade(t + 6 * step, MEAT, "MEAT", 0, b"B", 150, 100.05, 9001),
        _add_order(t + 7 * step, MEAT, "MEAT", 1005, b"S", 100, 100.05),
        _cancel(t + 8 * step, MEAT, 1002, 50),
        _delete(t + 9 * step, MEAT, 1001),
        _executed(t + 10 * step, PYTH, 2002, 75, 9002),
    ]

    msgs += [
        _system_event(close_ts, b"M"),
        _system_event(close_ts + 1_000_000, b"E"),
        _system_event(close_ts + 2_000_000, b"C"),
    ]
    return msgs


def main() -> None:
    out_path = Path(__file__).parent / "sample.itch50"
    messages = build_messages()
    with out_path.open("wb") as f:
        for msg in messages:
            f.write(_frame(msg))
    print(
        f"Wrote {len(messages)} messages ({out_path.stat().st_size} bytes) to {out_path}"
    )


if __name__ == "__main__":
    main()
