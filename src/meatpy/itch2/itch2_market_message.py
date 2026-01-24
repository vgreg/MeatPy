"""ITCH 2.0 market message types.

This module provides message classes for parsing ITCH 2.0 format market data.
ITCH 2.0 uses ASCII format with timestamps embedded in each message.

Message Types:
- S: System Event
- A: Add Order
- E: Order Executed
- X: Order Cancel
- P: Trade
- B: Broken Trade
"""

from __future__ import annotations

import json
from typing import Any

from ..message_reader import MarketMessage


class ITCH2MarketMessage(MarketMessage):
    """Base class for all ITCH 2.0 market messages.

    ITCH 2.0 messages are ASCII format with fixed-width fields.
    All messages have a timestamp as the first 8 characters (milliseconds
    from midnight), followed by a single character message type.
    """

    # Message type character to class mapping (populated by subclasses)
    _message_types: dict[bytes, type["ITCH2MarketMessage"]] = {}
    message_type: bytes = b""
    timestamp: int = 0

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Register message type when subclass is defined."""
        super().__init_subclass__(**kwargs)
        if cls.message_type:
            ITCH2MarketMessage._message_types[cls.message_type] = cls

    @classmethod
    def from_bytes(cls, data: bytes) -> "ITCH2MarketMessage":
        """Parse a message from bytes.

        Args:
            data: Raw message bytes (ASCII)

        Returns:
            Appropriate message subclass instance

        Raises:
            ValueError: If message type is unknown
        """
        if len(data) < 9:
            raise ValueError(f"Message too short: {len(data)} bytes")

        message_type = data[8:9]
        message_class = cls._message_types.get(message_type)
        if message_class is None:
            raise ValueError(f"Unknown message type: {message_type!r}")

        return message_class._from_bytes_data(data)

    @classmethod
    def _from_bytes_data(cls, data: bytes) -> "ITCH2MarketMessage":
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
    def from_json(cls, json_str: str) -> "ITCH2MarketMessage":
        """Deserialize message from JSON."""
        data = json.loads(json_str)
        message_type = data.get("message_type", "").encode()
        message_class = cls._message_types.get(message_type)
        if message_class is None:
            raise ValueError(f"Unknown message type: {message_type!r}")
        return message_class._from_json_data(data)

    @classmethod
    def _from_json_data(cls, data: dict[str, Any]) -> "ITCH2MarketMessage":
        """Create message from JSON data. Override in subclasses."""
        raise NotImplementedError


class SystemEventMessage(ITCH2MarketMessage):
    """System Event Message (S).

    Format: timestamp(8) + type(1) + event_code(1) = 10 chars

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
        message.timestamp = int(data[0:8])
        message.event_code = data[9:10]
        return message

    def to_bytes(self) -> bytes:
        return f"{self.timestamp:08d}S{self.event_code.decode()}".encode()

    def _to_json_data(self) -> dict[str, Any]:
        return {
            "message_type": self.message_type.decode(),
            "timestamp": self.timestamp,
            "event_code": self.event_code.decode(),
        }

    @classmethod
    def _from_json_data(cls, data: dict[str, Any]) -> "SystemEventMessage":
        message = cls()
        message.timestamp = data["timestamp"]
        message.event_code = data["event_code"].encode()
        return message


class AddOrderMessage(ITCH2MarketMessage):
    """Add Order Message (A).

    Format: timestamp(8) + type(1) + order_ref(9) + side(1) + shares(6)
            + stock(6) + price(10) + display(1) = 42 chars

    Price is in fixed-point format: 6 digits whole + 4 digits decimal (implied).
    """

    message_type: bytes = b"A"
    order_ref: int = 0
    side: bytes = b""
    shares: int = 0
    stock: bytes = b""
    price: int = 0  # Price in 10000ths (4 decimal places)
    display: bytes = b""

    @classmethod
    def _from_bytes_data(cls, data: bytes) -> "AddOrderMessage":
        message = cls()
        message.timestamp = int(data[0:8])
        message.order_ref = int(data[9:18])
        message.side = data[18:19]
        message.shares = int(data[19:25])
        message.stock = data[25:31]
        message.price = int(data[31:41])
        message.display = data[41:42]
        return message

    def to_bytes(self) -> bytes:
        return (
            f"{self.timestamp:08d}A{self.order_ref:9d}{self.side.decode()}"
            f"{self.shares:6d}{self.stock.decode():6s}{self.price:010d}"
            f"{self.display.decode()}"
        ).encode()

    def _to_json_data(self) -> dict[str, Any]:
        return {
            "message_type": self.message_type.decode(),
            "timestamp": self.timestamp,
            "order_ref": self.order_ref,
            "side": self.side.decode(),
            "shares": self.shares,
            "stock": self.stock.decode().rstrip(),
            "price": self.price,
            "display": self.display.decode(),
        }

    @classmethod
    def _from_json_data(cls, data: dict[str, Any]) -> "AddOrderMessage":
        message = cls()
        message.timestamp = data["timestamp"]
        message.order_ref = data["order_ref"]
        message.side = data["side"].encode()
        message.shares = data["shares"]
        message.stock = data["stock"].ljust(6).encode()
        message.price = data["price"]
        message.display = data["display"].encode()
        return message


class OrderExecutedMessage(ITCH2MarketMessage):
    """Order Executed Message (E).

    Format: timestamp(8) + type(1) + order_ref(9) + shares(6) + match_number(9) = 33 chars
    """

    message_type: bytes = b"E"
    order_ref: int = 0
    shares: int = 0
    match_number: int = 0

    @classmethod
    def _from_bytes_data(cls, data: bytes) -> "OrderExecutedMessage":
        message = cls()
        message.timestamp = int(data[0:8])
        message.order_ref = int(data[9:18])
        message.shares = int(data[18:24])
        message.match_number = int(data[24:33])
        return message

    def to_bytes(self) -> bytes:
        return (
            f"{self.timestamp:08d}E{self.order_ref:9d}"
            f"{self.shares:6d}{self.match_number:9d}"
        ).encode()

    def _to_json_data(self) -> dict[str, Any]:
        return {
            "message_type": self.message_type.decode(),
            "timestamp": self.timestamp,
            "order_ref": self.order_ref,
            "shares": self.shares,
            "match_number": self.match_number,
        }

    @classmethod
    def _from_json_data(cls, data: dict[str, Any]) -> "OrderExecutedMessage":
        message = cls()
        message.timestamp = data["timestamp"]
        message.order_ref = data["order_ref"]
        message.shares = data["shares"]
        message.match_number = data["match_number"]
        return message


class OrderCancelMessage(ITCH2MarketMessage):
    """Order Cancel Message (X).

    Format: timestamp(8) + type(1) + order_ref(9) + shares(6) = 24 chars
    """

    message_type: bytes = b"X"
    order_ref: int = 0
    shares: int = 0

    @classmethod
    def _from_bytes_data(cls, data: bytes) -> "OrderCancelMessage":
        message = cls()
        message.timestamp = int(data[0:8])
        message.order_ref = int(data[9:18])
        message.shares = int(data[18:24])
        return message

    def to_bytes(self) -> bytes:
        return f"{self.timestamp:08d}X{self.order_ref:9d}{self.shares:6d}".encode()

    def _to_json_data(self) -> dict[str, Any]:
        return {
            "message_type": self.message_type.decode(),
            "timestamp": self.timestamp,
            "order_ref": self.order_ref,
            "shares": self.shares,
        }

    @classmethod
    def _from_json_data(cls, data: dict[str, Any]) -> "OrderCancelMessage":
        message = cls()
        message.timestamp = data["timestamp"]
        message.order_ref = data["order_ref"]
        message.shares = data["shares"]
        return message


class TradeMessage(ITCH2MarketMessage):
    """Trade Message (P).

    Format: timestamp(8) + type(1) + order_ref(9) + side(1) + shares(6)
            + stock(6) + price(10) + match_number(9) = 50 chars
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
        message.timestamp = int(data[0:8])
        message.order_ref = int(data[9:18])
        message.side = data[18:19]
        message.shares = int(data[19:25])
        message.stock = data[25:31]
        message.price = int(data[31:41])
        message.match_number = int(data[41:50])
        return message

    def to_bytes(self) -> bytes:
        return (
            f"{self.timestamp:08d}P{self.order_ref:9d}{self.side.decode()}"
            f"{self.shares:6d}{self.stock.decode():6s}{self.price:010d}"
            f"{self.match_number:9d}"
        ).encode()

    def _to_json_data(self) -> dict[str, Any]:
        return {
            "message_type": self.message_type.decode(),
            "timestamp": self.timestamp,
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
        message.timestamp = data["timestamp"]
        message.order_ref = data["order_ref"]
        message.side = data["side"].encode()
        message.shares = data["shares"]
        message.stock = data["stock"].ljust(6).encode()
        message.price = data["price"]
        message.match_number = data["match_number"]
        return message


class BrokenTradeMessage(ITCH2MarketMessage):
    """Broken Trade Message (B).

    Format: timestamp(8) + type(1) + match_number(9) = 18 chars
    """

    message_type: bytes = b"B"
    match_number: int = 0

    @classmethod
    def _from_bytes_data(cls, data: bytes) -> "BrokenTradeMessage":
        message = cls()
        message.timestamp = int(data[0:8])
        message.match_number = int(data[9:18])
        return message

    def to_bytes(self) -> bytes:
        return f"{self.timestamp:08d}B{self.match_number:9d}".encode()

    def _to_json_data(self) -> dict[str, Any]:
        return {
            "message_type": self.message_type.decode(),
            "timestamp": self.timestamp,
            "match_number": self.match_number,
        }

    @classmethod
    def _from_json_data(cls, data: dict[str, Any]) -> "BrokenTradeMessage":
        message = cls()
        message.timestamp = data["timestamp"]
        message.match_number = data["match_number"]
        return message
