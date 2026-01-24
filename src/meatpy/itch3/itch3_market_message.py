"""ITCH 3.0 market message types.

This module provides message classes for parsing ITCH 3.0 format market data.
ITCH 3.0 uses ASCII format with separate timestamp messages (T for seconds, M for milliseconds).

Message Types:
- T: Seconds (timestamp base)
- M: Milliseconds (timestamp offset)
- S: System Event
- R: Stock Directory
- H: Stock Trading Action
- L: Market Participant Position
- A: Add Order (no MPID)
- F: Add Order (with MPID)
- E: Order Executed
- C: Order Executed With Price
- X: Order Cancel
- D: Order Delete
- P: Trade (non-cross)
- Q: Cross Trade
- B: Broken Trade
- I: NOII (Net Order Imbalance Indicator)
"""

from __future__ import annotations

import json
from typing import Any

from ..message_reader import MarketMessage


class ITCH3MarketMessage(MarketMessage):
    """Base class for all ITCH 3.0 market messages.

    ITCH 3.0 messages are ASCII format with fixed-width fields.
    Timestamps are provided via separate T (seconds) and M (milliseconds) messages.
    """

    # Message type character to class mapping (populated by subclasses)
    _message_types: dict[bytes, type["ITCH3MarketMessage"]] = {}
    message_type: bytes = b""

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Register message type when subclass is defined."""
        super().__init_subclass__(**kwargs)
        if cls.message_type:
            ITCH3MarketMessage._message_types[cls.message_type] = cls

    @classmethod
    def from_bytes(cls, data: bytes) -> "ITCH3MarketMessage":
        """Parse a message from bytes.

        Args:
            data: Raw message bytes (ASCII)

        Returns:
            Appropriate message subclass instance

        Raises:
            ValueError: If message type is unknown
        """
        if len(data) < 1:
            raise ValueError(f"Message too short: {len(data)} bytes")

        message_type = data[0:1]
        message_class = cls._message_types.get(message_type)
        if message_class is None:
            raise ValueError(f"Unknown message type: {message_type!r}")

        return message_class._from_bytes_data(data)

    @classmethod
    def _from_bytes_data(cls, data: bytes) -> "ITCH3MarketMessage":
        """Parse message-specific data. Override in subclasses."""
        raise NotImplementedError

    def to_bytes(self) -> bytes:
        """Serialize message to bytes."""
        raise NotImplementedError

    def to_json(self) -> str:
        """Serialize message to JSON."""
        return json.dumps(self._to_json_data())

    def _to_json_data(self) -> dict[str, Any]:
        """Return message data as a dictionary for JSON serialization."""
        raise NotImplementedError

    @classmethod
    def from_json(cls, json_str: str) -> "ITCH3MarketMessage":
        """Deserialize message from JSON."""
        data = json.loads(json_str)
        message_type = data.get("message_type", "").encode()
        message_class = cls._message_types.get(message_type)
        if message_class is None:
            raise ValueError(f"Unknown message type: {message_type!r}")
        return message_class._from_json_data(data)

    @classmethod
    def _from_json_data(cls, data: dict[str, Any]) -> "ITCH3MarketMessage":
        """Create message from JSON data. Override in subclasses."""
        raise NotImplementedError


class SecondsMessage(ITCH3MarketMessage):
    """Seconds Message (T).

    Format: T + seconds(5) = 6 chars
    Provides the seconds component of the timestamp.
    """

    message_type: bytes = b"T"
    seconds: int = 0

    @classmethod
    def _from_bytes_data(cls, data: bytes) -> "SecondsMessage":
        message = cls()
        message.seconds = int(data[1:6])
        return message

    def to_bytes(self) -> bytes:
        return f"T{self.seconds:05d}".encode()

    def _to_json_data(self) -> dict[str, Any]:
        return {
            "message_type": self.message_type.decode(),
            "seconds": self.seconds,
        }

    @classmethod
    def _from_json_data(cls, data: dict[str, Any]) -> "SecondsMessage":
        message = cls()
        message.seconds = data["seconds"]
        return message


class MillisecondsMessage(ITCH3MarketMessage):
    """Milliseconds Message (M).

    Format: M + milliseconds(3) = 4 chars
    Provides the milliseconds offset within the current second.
    """

    message_type: bytes = b"M"
    milliseconds: int = 0

    @classmethod
    def _from_bytes_data(cls, data: bytes) -> "MillisecondsMessage":
        message = cls()
        message.milliseconds = int(data[1:4])
        return message

    def to_bytes(self) -> bytes:
        return f"M{self.milliseconds:03d}".encode()

    def _to_json_data(self) -> dict[str, Any]:
        return {
            "message_type": self.message_type.decode(),
            "milliseconds": self.milliseconds,
        }

    @classmethod
    def _from_json_data(cls, data: dict[str, Any]) -> "MillisecondsMessage":
        message = cls()
        message.milliseconds = data["milliseconds"]
        return message


class SystemEventMessage(ITCH3MarketMessage):
    """System Event Message (S).

    Format: S + event_code(1) = 2 chars

    Event codes:
    - O: Start of messages
    - S: Start of system hours
    - Q: Start of market hours
    - M: End of market hours
    - E: End of system hours
    - C: End of messages
    """

    message_type: bytes = b"S"
    event_code: bytes = b""

    @classmethod
    def _from_bytes_data(cls, data: bytes) -> "SystemEventMessage":
        message = cls()
        message.event_code = data[1:2]
        return message

    def to_bytes(self) -> bytes:
        return f"S{self.event_code.decode()}".encode()

    def _to_json_data(self) -> dict[str, Any]:
        return {
            "message_type": self.message_type.decode(),
            "event_code": self.event_code.decode(),
        }

    @classmethod
    def _from_json_data(cls, data: dict[str, Any]) -> "SystemEventMessage":
        message = cls()
        message.event_code = data["event_code"].encode()
        return message


class StockDirectoryMessage(ITCH3MarketMessage):
    """Stock Directory Message (R).

    Format: R + stock(6) + market_category(1) + financial_status(1) + round_lot_size(6) + round_lots_only(1) = 16 chars
    """

    message_type: bytes = b"R"
    stock: bytes = b""
    market_category: bytes = b""
    financial_status: bytes = b""
    round_lot_size: int = 0
    round_lots_only: bytes = b""

    @classmethod
    def _from_bytes_data(cls, data: bytes) -> "StockDirectoryMessage":
        message = cls()
        message.stock = data[1:7]
        message.market_category = data[7:8]
        message.financial_status = data[8:9]
        # round_lot_size is 6 chars, may contain spaces
        round_lot_str = data[9:15].decode().strip()
        message.round_lot_size = int(round_lot_str) if round_lot_str else 0
        message.round_lots_only = data[15:16]
        return message

    def to_bytes(self) -> bytes:
        return (
            f"R{self.stock.decode():6s}{self.market_category.decode()}"
            f"{self.financial_status.decode()}{self.round_lot_size:6d}"
            f"{self.round_lots_only.decode()}"
        ).encode()

    def _to_json_data(self) -> dict[str, Any]:
        return {
            "message_type": self.message_type.decode(),
            "stock": self.stock.decode().rstrip(),
            "market_category": self.market_category.decode(),
            "financial_status": self.financial_status.decode(),
            "round_lot_size": self.round_lot_size,
            "round_lots_only": self.round_lots_only.decode(),
        }

    @classmethod
    def _from_json_data(cls, data: dict[str, Any]) -> "StockDirectoryMessage":
        message = cls()
        message.stock = data["stock"].ljust(6).encode()
        message.market_category = data["market_category"].encode()
        message.financial_status = data["financial_status"].encode()
        message.round_lot_size = data["round_lot_size"]
        message.round_lots_only = data["round_lots_only"].encode()
        return message


class StockTradingActionMessage(ITCH3MarketMessage):
    """Stock Trading Action Message (H).

    Format: H + stock(6) + state(1) + reserved(5) = 13 chars
    """

    message_type: bytes = b"H"
    stock: bytes = b""
    state: bytes = b""
    reserved: bytes = b""

    @classmethod
    def _from_bytes_data(cls, data: bytes) -> "StockTradingActionMessage":
        message = cls()
        message.stock = data[1:7]
        message.state = data[7:8]
        message.reserved = data[8:13]
        return message

    def to_bytes(self) -> bytes:
        return (
            f"H{self.stock.decode():6s}{self.state.decode()}{self.reserved.decode():5s}"
        ).encode()

    def _to_json_data(self) -> dict[str, Any]:
        return {
            "message_type": self.message_type.decode(),
            "stock": self.stock.decode().rstrip(),
            "state": self.state.decode(),
            "reserved": self.reserved.decode().rstrip(),
        }

    @classmethod
    def _from_json_data(cls, data: dict[str, Any]) -> "StockTradingActionMessage":
        message = cls()
        message.stock = data["stock"].ljust(6).encode()
        message.state = data["state"].encode()
        message.reserved = data.get("reserved", "").ljust(5).encode()
        return message


class MarketParticipantPositionMessage(ITCH3MarketMessage):
    """Market Participant Position Message (L).

    Format: L + stock(6) + mpid(4) + primary_mm(1) + mode(1) + state(1) = 14 chars
    """

    message_type: bytes = b"L"
    stock: bytes = b""
    mpid: bytes = b""
    primary_mm: bytes = b""
    mode: bytes = b""
    state: bytes = b""

    @classmethod
    def _from_bytes_data(cls, data: bytes) -> "MarketParticipantPositionMessage":
        message = cls()
        message.stock = data[1:7]
        message.mpid = data[7:11]
        message.primary_mm = data[11:12]
        message.mode = data[12:13]
        message.state = data[13:14]
        return message

    def to_bytes(self) -> bytes:
        return (
            f"L{self.stock.decode():6s}{self.mpid.decode():4s}"
            f"{self.primary_mm.decode()}{self.mode.decode()}{self.state.decode()}"
        ).encode()

    def _to_json_data(self) -> dict[str, Any]:
        return {
            "message_type": self.message_type.decode(),
            "stock": self.stock.decode().rstrip(),
            "mpid": self.mpid.decode().rstrip(),
            "primary_mm": self.primary_mm.decode(),
            "mode": self.mode.decode(),
            "state": self.state.decode(),
        }

    @classmethod
    def _from_json_data(
        cls, data: dict[str, Any]
    ) -> "MarketParticipantPositionMessage":
        message = cls()
        message.stock = data["stock"].ljust(6).encode()
        message.mpid = data["mpid"].ljust(4).encode()
        message.primary_mm = data["primary_mm"].encode()
        message.mode = data["mode"].encode()
        message.state = data["state"].encode()
        return message


class AddOrderMessage(ITCH3MarketMessage):
    """Add Order Message (A) - no MPID.

    Format: A + order_ref(9) + side(1) + shares(6) + stock(6) + price(10) = 33 chars
    """

    message_type: bytes = b"A"
    order_ref: int = 0
    side: bytes = b""
    shares: int = 0
    stock: bytes = b""
    price: int = 0

    @classmethod
    def _from_bytes_data(cls, data: bytes) -> "AddOrderMessage":
        message = cls()
        message.order_ref = int(data[1:10])
        message.side = data[10:11]
        message.shares = int(data[11:17])
        message.stock = data[17:23]
        message.price = int(data[23:33])
        return message

    def to_bytes(self) -> bytes:
        return (
            f"A{self.order_ref:9d}{self.side.decode()}{self.shares:6d}"
            f"{self.stock.decode():6s}{self.price:010d}"
        ).encode()

    def _to_json_data(self) -> dict[str, Any]:
        return {
            "message_type": self.message_type.decode(),
            "order_ref": self.order_ref,
            "side": self.side.decode(),
            "shares": self.shares,
            "stock": self.stock.decode().rstrip(),
            "price": self.price,
        }

    @classmethod
    def _from_json_data(cls, data: dict[str, Any]) -> "AddOrderMessage":
        message = cls()
        message.order_ref = data["order_ref"]
        message.side = data["side"].encode()
        message.shares = data["shares"]
        message.stock = data["stock"].ljust(6).encode()
        message.price = data["price"]
        return message


class AddOrderMPIDMessage(ITCH3MarketMessage):
    """Add Order Message with MPID (F).

    Format: F + order_ref(9) + side(1) + shares(6) + stock(6) + price(10) + mpid(4) = 37 chars
    """

    message_type: bytes = b"F"
    order_ref: int = 0
    side: bytes = b""
    shares: int = 0
    stock: bytes = b""
    price: int = 0
    mpid: bytes = b""

    @classmethod
    def _from_bytes_data(cls, data: bytes) -> "AddOrderMPIDMessage":
        message = cls()
        message.order_ref = int(data[1:10])
        message.side = data[10:11]
        message.shares = int(data[11:17])
        message.stock = data[17:23]
        message.price = int(data[23:33])
        message.mpid = data[33:37]
        return message

    def to_bytes(self) -> bytes:
        return (
            f"F{self.order_ref:9d}{self.side.decode()}{self.shares:6d}"
            f"{self.stock.decode():6s}{self.price:010d}{self.mpid.decode():4s}"
        ).encode()

    def _to_json_data(self) -> dict[str, Any]:
        return {
            "message_type": self.message_type.decode(),
            "order_ref": self.order_ref,
            "side": self.side.decode(),
            "shares": self.shares,
            "stock": self.stock.decode().rstrip(),
            "price": self.price,
            "mpid": self.mpid.decode().rstrip(),
        }

    @classmethod
    def _from_json_data(cls, data: dict[str, Any]) -> "AddOrderMPIDMessage":
        message = cls()
        message.order_ref = data["order_ref"]
        message.side = data["side"].encode()
        message.shares = data["shares"]
        message.stock = data["stock"].ljust(6).encode()
        message.price = data["price"]
        message.mpid = data["mpid"].ljust(4).encode()
        return message


class OrderExecutedMessage(ITCH3MarketMessage):
    """Order Executed Message (E).

    Format: E + order_ref(9) + shares(6) + match_number(9) = 25 chars
    """

    message_type: bytes = b"E"
    order_ref: int = 0
    shares: int = 0
    match_number: int = 0

    @classmethod
    def _from_bytes_data(cls, data: bytes) -> "OrderExecutedMessage":
        message = cls()
        message.order_ref = int(data[1:10])
        message.shares = int(data[10:16])
        message.match_number = int(data[16:25])
        return message

    def to_bytes(self) -> bytes:
        return f"E{self.order_ref:9d}{self.shares:6d}{self.match_number:9d}".encode()

    def _to_json_data(self) -> dict[str, Any]:
        return {
            "message_type": self.message_type.decode(),
            "order_ref": self.order_ref,
            "shares": self.shares,
            "match_number": self.match_number,
        }

    @classmethod
    def _from_json_data(cls, data: dict[str, Any]) -> "OrderExecutedMessage":
        message = cls()
        message.order_ref = data["order_ref"]
        message.shares = data["shares"]
        message.match_number = data["match_number"]
        return message


class OrderExecutedPriceMessage(ITCH3MarketMessage):
    """Order Executed With Price Message (C).

    Format: C + order_ref(9) + shares(6) + match_number(9) + printable(1) + price(10) = 36 chars
    """

    message_type: bytes = b"C"
    order_ref: int = 0
    shares: int = 0
    match_number: int = 0
    printable: bytes = b""
    price: int = 0

    @classmethod
    def _from_bytes_data(cls, data: bytes) -> "OrderExecutedPriceMessage":
        message = cls()
        message.order_ref = int(data[1:10])
        message.shares = int(data[10:16])
        message.match_number = int(data[16:25])
        message.printable = data[25:26]
        message.price = int(data[26:36])
        return message

    def to_bytes(self) -> bytes:
        return (
            f"C{self.order_ref:9d}{self.shares:6d}{self.match_number:9d}"
            f"{self.printable.decode()}{self.price:010d}"
        ).encode()

    def _to_json_data(self) -> dict[str, Any]:
        return {
            "message_type": self.message_type.decode(),
            "order_ref": self.order_ref,
            "shares": self.shares,
            "match_number": self.match_number,
            "printable": self.printable.decode(),
            "price": self.price,
        }

    @classmethod
    def _from_json_data(cls, data: dict[str, Any]) -> "OrderExecutedPriceMessage":
        message = cls()
        message.order_ref = data["order_ref"]
        message.shares = data["shares"]
        message.match_number = data["match_number"]
        message.printable = data["printable"].encode()
        message.price = data["price"]
        return message


class OrderCancelMessage(ITCH3MarketMessage):
    """Order Cancel Message (X).

    Format: X + order_ref(9) + shares(6) = 16 chars
    """

    message_type: bytes = b"X"
    order_ref: int = 0
    shares: int = 0

    @classmethod
    def _from_bytes_data(cls, data: bytes) -> "OrderCancelMessage":
        message = cls()
        message.order_ref = int(data[1:10])
        message.shares = int(data[10:16])
        return message

    def to_bytes(self) -> bytes:
        return f"X{self.order_ref:9d}{self.shares:6d}".encode()

    def _to_json_data(self) -> dict[str, Any]:
        return {
            "message_type": self.message_type.decode(),
            "order_ref": self.order_ref,
            "shares": self.shares,
        }

    @classmethod
    def _from_json_data(cls, data: dict[str, Any]) -> "OrderCancelMessage":
        message = cls()
        message.order_ref = data["order_ref"]
        message.shares = data["shares"]
        return message


class OrderDeleteMessage(ITCH3MarketMessage):
    """Order Delete Message (D).

    Format: D + order_ref(9) = 10 chars
    """

    message_type: bytes = b"D"
    order_ref: int = 0

    @classmethod
    def _from_bytes_data(cls, data: bytes) -> "OrderDeleteMessage":
        message = cls()
        message.order_ref = int(data[1:10])
        return message

    def to_bytes(self) -> bytes:
        return f"D{self.order_ref:9d}".encode()

    def _to_json_data(self) -> dict[str, Any]:
        return {
            "message_type": self.message_type.decode(),
            "order_ref": self.order_ref,
        }

    @classmethod
    def _from_json_data(cls, data: dict[str, Any]) -> "OrderDeleteMessage":
        message = cls()
        message.order_ref = data["order_ref"]
        return message


class TradeMessage(ITCH3MarketMessage):
    """Trade Message (P).

    Format: P + order_ref(9) + side(1) + shares(6) + stock(6) + price(10) + match_number(9) = 42 chars
    """

    message_type: bytes = b"P"
    order_ref: int = 0
    side: bytes = b""
    shares: int = 0
    stock: bytes = b""
    price: int = 0
    match_number: int = 0

    @classmethod
    def _from_bytes_data(cls, data: bytes) -> "TradeMessage":
        message = cls()
        message.order_ref = int(data[1:10])
        message.side = data[10:11]
        message.shares = int(data[11:17])
        message.stock = data[17:23]
        message.price = int(data[23:33])
        message.match_number = int(data[33:42])
        return message

    def to_bytes(self) -> bytes:
        return (
            f"P{self.order_ref:9d}{self.side.decode()}{self.shares:6d}"
            f"{self.stock.decode():6s}{self.price:010d}{self.match_number:9d}"
        ).encode()

    def _to_json_data(self) -> dict[str, Any]:
        return {
            "message_type": self.message_type.decode(),
            "order_ref": self.order_ref,
            "side": self.side.decode(),
            "shares": self.shares,
            "stock": self.stock.decode().rstrip(),
            "price": self.price,
            "match_number": self.match_number,
        }

    @classmethod
    def _from_json_data(cls, data: dict[str, Any]) -> "TradeMessage":
        message = cls()
        message.order_ref = data["order_ref"]
        message.side = data["side"].encode()
        message.shares = data["shares"]
        message.stock = data["stock"].ljust(6).encode()
        message.price = data["price"]
        message.match_number = data["match_number"]
        return message


class CrossTradeMessage(ITCH3MarketMessage):
    """Cross Trade Message (Q).

    Format: Q + shares(9) + stock(6) + price(10) + match_number(9) + cross_type(1) = 36 chars
    """

    message_type: bytes = b"Q"
    shares: int = 0
    stock: bytes = b""
    price: int = 0
    match_number: int = 0
    cross_type: bytes = b""

    @classmethod
    def _from_bytes_data(cls, data: bytes) -> "CrossTradeMessage":
        message = cls()
        message.shares = int(data[1:10])
        message.stock = data[10:16]
        message.price = int(data[16:26])
        message.match_number = int(data[26:35])
        message.cross_type = data[35:36]
        return message

    def to_bytes(self) -> bytes:
        return (
            f"Q{self.shares:09d}{self.stock.decode():6s}{self.price:010d}"
            f"{self.match_number:9d}{self.cross_type.decode()}"
        ).encode()

    def _to_json_data(self) -> dict[str, Any]:
        return {
            "message_type": self.message_type.decode(),
            "shares": self.shares,
            "stock": self.stock.decode().rstrip(),
            "price": self.price,
            "match_number": self.match_number,
            "cross_type": self.cross_type.decode(),
        }

    @classmethod
    def _from_json_data(cls, data: dict[str, Any]) -> "CrossTradeMessage":
        message = cls()
        message.shares = data["shares"]
        message.stock = data["stock"].ljust(6).encode()
        message.price = data["price"]
        message.match_number = data["match_number"]
        message.cross_type = data["cross_type"].encode()
        return message


class BrokenTradeMessage(ITCH3MarketMessage):
    """Broken Trade Message (B).

    Format: B + match_number(9) = 10 chars
    """

    message_type: bytes = b"B"
    match_number: int = 0

    @classmethod
    def _from_bytes_data(cls, data: bytes) -> "BrokenTradeMessage":
        message = cls()
        message.match_number = int(data[1:10])
        return message

    def to_bytes(self) -> bytes:
        return f"B{self.match_number:9d}".encode()

    def _to_json_data(self) -> dict[str, Any]:
        return {
            "message_type": self.message_type.decode(),
            "match_number": self.match_number,
        }

    @classmethod
    def _from_json_data(cls, data: dict[str, Any]) -> "BrokenTradeMessage":
        message = cls()
        message.match_number = data["match_number"]
        return message


class NoiiMessage(ITCH3MarketMessage):
    """NOII Message (I) - Net Order Imbalance Indicator.

    Format: I + paired_shares(9) + imbalance_shares(9) + imbalance_direction(1)
            + stock(6) + far_price(10) + near_price(10) + ref_price(10) + cross_type(2) = 58 chars
    """

    message_type: bytes = b"I"
    paired_shares: int = 0
    imbalance_shares: int = 0
    imbalance_direction: bytes = b""
    stock: bytes = b""
    far_price: int = 0
    near_price: int = 0
    ref_price: int = 0
    cross_type: bytes = b""

    @classmethod
    def _from_bytes_data(cls, data: bytes) -> "NoiiMessage":
        message = cls()
        message.paired_shares = int(data[1:10])
        message.imbalance_shares = int(data[10:19])
        message.imbalance_direction = data[19:20]
        message.stock = data[20:26]
        message.far_price = int(data[26:36])
        message.near_price = int(data[36:46])
        message.ref_price = int(data[46:56])
        message.cross_type = data[56:58]
        return message

    def to_bytes(self) -> bytes:
        return (
            f"I{self.paired_shares:09d}{self.imbalance_shares:09d}"
            f"{self.imbalance_direction.decode()}{self.stock.decode():6s}"
            f"{self.far_price:010d}{self.near_price:010d}{self.ref_price:010d}"
            f"{self.cross_type.decode():2s}"
        ).encode()

    def _to_json_data(self) -> dict[str, Any]:
        return {
            "message_type": self.message_type.decode(),
            "paired_shares": self.paired_shares,
            "imbalance_shares": self.imbalance_shares,
            "imbalance_direction": self.imbalance_direction.decode(),
            "stock": self.stock.decode().rstrip(),
            "far_price": self.far_price,
            "near_price": self.near_price,
            "ref_price": self.ref_price,
            "cross_type": self.cross_type.decode().rstrip(),
        }

    @classmethod
    def _from_json_data(cls, data: dict[str, Any]) -> "NoiiMessage":
        message = cls()
        message.paired_shares = data["paired_shares"]
        message.imbalance_shares = data["imbalance_shares"]
        message.imbalance_direction = data["imbalance_direction"].encode()
        message.stock = data["stock"].ljust(6).encode()
        message.far_price = data["far_price"]
        message.near_price = data["near_price"]
        message.ref_price = data["ref_price"]
        message.cross_type = data["cross_type"].ljust(2).encode()
        return message
