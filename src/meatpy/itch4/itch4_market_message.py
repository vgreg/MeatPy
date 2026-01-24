"""ITCH 4.0 market message types and parsing.

This module provides classes for parsing and representing ITCH 4.0 market data
messages. ITCH 4.0 is a binary format similar to ITCH 4.1 but uses 6-character
stock symbols instead of 8-character symbols.

Message Types:
- T: Seconds
- S: System Event
- R: Stock Directory
- H: Stock Trading Action
- L: Market Participant Position
- A: Add Order (no MPID)
- F: Add Order (with MPID)
- E: Order Executed
- X: Order Cancel
- D: Order Delete
- U: Order Replace
- P: Trade
"""

import json
import struct

from ..message_reader import MarketMessage


class ITCH4MarketMessage(MarketMessage):
    """A market message in ITCH 4.0 format.

    This is the base class for all ITCH 4.0 message types. ITCH 4.0 uses
    binary format with 6-character stock symbols.

    Attributes:
        timestamp: The nanosecond timestamp offset within the current second
        type: The message type identifier
        description: Human-readable description of the message type
        message_size: The size of the message in bytes
    """

    type: bytes = b"?"
    description: str = "Unknown Message"
    message_size: int = 0

    sysEventCodes = {
        b"O": "Start of Messages",
        b"S": "Start of System Hours",
        b"Q": "Start of Market Hours",
        b"M": "End of Market Hours",
        b"E": "End of System Hours",
        b"C": "End of Messages",
    }

    market = {
        b"N": "NYSE",
        b"A": "AMEX",
        b"P": "Arca",
        b"Q": "NASDAQ Global Select",
        b"G": "NASDAQ Global Market",
        b"S": "NASDAQ Capital Market",
        b"Z": "BATS",
        b" ": "Not available",
    }

    tradingStates = {
        b"H": "Halted across all U.S. equity markets / SROs",
        b"P": "Paused across all U.S. equity markets / SROs",
        b"Q": "Quotation only period for cross-SRO halt or pause",
        b"T": "Trading on NASDAQ",
    }

    primaryMarketMaker = {
        b"Y": "Primary market maker",
        b"N": "Non-primary market maker",
    }

    marketMakerModes = {
        b"N": "Normal",
        b"P": "Passive",
        b"S": "Syndicate",
        b"R": "Pre-syndicate",
        b"L": "Penalty",
    }

    marketParticipantStates = {
        b"A": "Active",
        b"E": "Excused",
        b"W": "Withdrawn",
        b"S": "Suspended",
        b"D": "Deleted",
    }

    def __init__(self) -> None:
        """Initialize an ITCH4MarketMessage."""
        self.timestamp: int = 0

    @classmethod
    def from_bytes(cls, message_data: bytes) -> "ITCH4MarketMessage":
        """Create a message object from bytes data.

        Args:
            message_data: The raw message bytes

        Returns:
            The appropriate message object based on message type
        """
        from ..message_reader import UnknownMessageTypeError

        if not message_data:
            raise ValueError("Empty message data")

        message_type = bytes([message_data[0]])

        # Message type mapping for ITCH 4.0
        message_classes = {
            b"T": SecondsMessage,
            b"S": SystemEventMessage,
            b"R": StockDirectoryMessage,
            b"H": StockTradingActionMessage,
            b"L": MarketParticipantPositionMessage,
            b"A": AddOrderMessage,
            b"F": AddOrderMPIDMessage,
            b"E": OrderExecutedMessage,
            b"C": OrderExecutedPriceMessage,
            b"X": OrderCancelMessage,
            b"D": OrderDeleteMessage,
            b"U": OrderReplaceMessage,
            b"P": TradeMessage,
            b"Q": CrossTradeMessage,
            b"B": BrokenTradeMessage,
            b"I": NoiiMessage,
        }

        message_class = message_classes.get(message_type)
        if message_class is None:
            raise UnknownMessageTypeError(f"Unknown message type: {message_type}")

        return message_class._from_bytes_data(message_data)

    @classmethod
    def _from_bytes_data(cls, message_data: bytes) -> "ITCH4MarketMessage":
        """Create a message object from bytes data."""
        raise NotImplementedError("Subclasses must implement _from_bytes_data")

    def to_bytes(self) -> bytes:
        """Convert the message to bytes."""
        raise NotImplementedError("Subclasses must implement to_bytes")

    def to_json(self) -> str:
        """Convert the message to JSON format."""
        data = {
            "timestamp": self.timestamp,
            "type": self.type.decode() if isinstance(self.type, bytes) else self.type,
            "description": self.description,
        }
        self._add_json_fields(data)
        return json.dumps(data)

    def _add_json_fields(self, data: dict) -> None:
        """Add message-specific fields to JSON data."""
        pass

    @classmethod
    def from_json(cls, json_str: str) -> "ITCH4MarketMessage":
        """Create a message object from JSON string."""
        from ..message_reader import UnknownMessageTypeError

        data = json.loads(json_str)
        message_type = data.get("type", "").encode()

        message_classes = {
            b"T": SecondsMessage,
            b"S": SystemEventMessage,
            b"R": StockDirectoryMessage,
            b"H": StockTradingActionMessage,
            b"L": MarketParticipantPositionMessage,
            b"A": AddOrderMessage,
            b"F": AddOrderMPIDMessage,
            b"E": OrderExecutedMessage,
            b"C": OrderExecutedPriceMessage,
            b"X": OrderCancelMessage,
            b"D": OrderDeleteMessage,
            b"U": OrderReplaceMessage,
            b"P": TradeMessage,
            b"Q": CrossTradeMessage,
            b"B": BrokenTradeMessage,
            b"I": NoiiMessage,
        }

        message_class = message_classes.get(message_type)
        if message_class is None:
            raise UnknownMessageTypeError(f"Unknown message type: {message_type}")

        return message_class._from_json_data(data)

    @classmethod
    def _from_json_data(cls, data: dict) -> "ITCH4MarketMessage":
        """Create a message object from JSON data."""
        raise NotImplementedError("Subclasses must implement _from_json_data")


class SecondsMessage(ITCH4MarketMessage):
    """Seconds Message (T).

    Format: T(1) + seconds(4) = 5 bytes
    """

    type = b"T"
    description = "Seconds Message"
    message_size = 5

    def __init__(self) -> None:
        """Initialize a SecondsMessage."""
        super().__init__()
        self.seconds: int = 0

    @classmethod
    def _from_bytes_data(cls, message_data: bytes) -> "SecondsMessage":
        """Create a SecondsMessage from bytes data."""
        message = cls()
        (message.seconds,) = struct.unpack("!I", message_data[1:5])
        return message

    def to_bytes(self) -> bytes:
        return struct.pack("!cI", self.type, self.seconds)

    def _add_json_fields(self, data: dict) -> None:
        data["seconds"] = self.seconds

    @classmethod
    def _from_json_data(cls, data: dict) -> "SecondsMessage":
        message = cls()
        message.seconds = data.get("seconds", 0)
        return message


class SystemEventMessage(ITCH4MarketMessage):
    """System Event Message (S).

    Format: S(1) + timestamp(4) + event_code(1) = 6 bytes
    """

    type = b"S"
    description = "System Event Message"
    message_size = 6

    def __init__(self) -> None:
        """Initialize a SystemEventMessage."""
        super().__init__()
        self.event_code: bytes = b""

    @classmethod
    def _from_bytes_data(cls, message_data: bytes) -> "SystemEventMessage":
        """Create a SystemEventMessage from bytes data."""
        message = cls()
        message.timestamp, message.event_code = struct.unpack("!Ic", message_data[1:6])
        return message

    def to_bytes(self) -> bytes:
        return struct.pack("!cIc", self.type, self.timestamp, self.event_code)

    def _add_json_fields(self, data: dict) -> None:
        data["event_code"] = (
            self.event_code.decode()
            if isinstance(self.event_code, bytes)
            else self.event_code
        )

    @classmethod
    def _from_json_data(cls, data: dict) -> "SystemEventMessage":
        message = cls()
        message.timestamp = data.get("timestamp", 0)
        event_code = data.get("event_code", " ")
        if isinstance(event_code, str):
            event_code = event_code.encode()
        message.event_code = event_code
        return message


class StockDirectoryMessage(ITCH4MarketMessage):
    """Stock Directory Message (R).

    Format: R(1) + timestamp(4) + stock(6) + market_category(1) + financial_status(1)
            + round_lot_size(4) + round_lots_only(1) = 18 bytes
    """

    type = b"R"
    description = "Stock Directory Message"
    message_size = 18

    def __init__(self) -> None:
        """Initialize a StockDirectoryMessage."""
        super().__init__()
        self.stock: bytes = b""
        self.category: bytes = b""
        self.status: bytes = b""
        self.lotsize: int = 0
        self.lotsonly: bytes = b""

    @classmethod
    def _from_bytes_data(cls, message_data: bytes) -> "StockDirectoryMessage":
        """Create a StockDirectoryMessage from bytes data."""
        message = cls()
        (
            message.timestamp,
            message.stock,
            message.category,
            message.status,
            message.lotsize,
            message.lotsonly,
        ) = struct.unpack("!I6sccIc", message_data[1:18])
        return message

    def to_bytes(self) -> bytes:
        return struct.pack(
            "!cI6sccIc",
            self.type,
            self.timestamp,
            self.stock,
            self.category,
            self.status,
            self.lotsize,
            self.lotsonly,
        )

    def _add_json_fields(self, data: dict) -> None:
        data.update(
            {
                "stock": self.stock.decode().rstrip()
                if isinstance(self.stock, bytes)
                else self.stock,
                "category": self.category.decode()
                if isinstance(self.category, bytes)
                else self.category,
                "status": self.status.decode()
                if isinstance(self.status, bytes)
                else self.status,
                "lotsize": self.lotsize,
                "lotsonly": self.lotsonly.decode()
                if isinstance(self.lotsonly, bytes)
                else self.lotsonly,
            }
        )

    @classmethod
    def _from_json_data(cls, data: dict) -> "StockDirectoryMessage":
        message = cls()
        message.timestamp = data.get("timestamp", 0)
        stock = data.get("stock", "")
        if isinstance(stock, str):
            stock = stock.ljust(6).encode()
        message.stock = stock
        message.lotsize = data.get("lotsize", 0)
        for field_name in ["category", "status", "lotsonly"]:
            value = data.get(field_name, " ")
            if isinstance(value, str):
                value = value.encode()
            setattr(message, field_name, value)
        return message


class StockTradingActionMessage(ITCH4MarketMessage):
    """Stock Trading Action Message (H).

    Format: H(1) + timestamp(4) + stock(6) + state(1) + reserved(5) = 17 bytes
    """

    type = b"H"
    description = "Stock Trading Action Message"
    message_size = 17

    def __init__(self) -> None:
        """Initialize a StockTradingActionMessage."""
        super().__init__()
        self.stock: bytes = b""
        self.state: bytes = b""
        self.reserved: bytes = b""

    @classmethod
    def _from_bytes_data(cls, message_data: bytes) -> "StockTradingActionMessage":
        """Create a StockTradingActionMessage from bytes data."""
        message = cls()
        (
            message.timestamp,
            message.stock,
            message.state,
            message.reserved,
        ) = struct.unpack("!I6sc5s", message_data[1:17])
        return message

    def to_bytes(self) -> bytes:
        return struct.pack(
            "!cI6sc5s",
            self.type,
            self.timestamp,
            self.stock,
            self.state,
            self.reserved,
        )

    def _add_json_fields(self, data: dict) -> None:
        data.update(
            {
                "stock": self.stock.decode().rstrip()
                if isinstance(self.stock, bytes)
                else self.stock,
                "state": self.state.decode()
                if isinstance(self.state, bytes)
                else self.state,
            }
        )

    @classmethod
    def _from_json_data(cls, data: dict) -> "StockTradingActionMessage":
        message = cls()
        message.timestamp = data.get("timestamp", 0)
        stock = data.get("stock", "")
        if isinstance(stock, str):
            stock = stock.ljust(6).encode()
        message.stock = stock
        state = data.get("state", " ")
        if isinstance(state, str):
            state = state.encode()
        message.state = state
        message.reserved = b"     "
        return message


class MarketParticipantPositionMessage(ITCH4MarketMessage):
    """Market Participant Position Message (L).

    Format: L(1) + timestamp(4) + mpid(4) + stock(6) + primary(1) + mode(1) + state(1) = 18 bytes
    """

    type = b"L"
    description = "Market Participant Position Message"
    message_size = 18

    def __init__(self) -> None:
        """Initialize a MarketParticipantPositionMessage."""
        super().__init__()
        self.mpid: bytes = b""
        self.stock: bytes = b""
        self.primary: bytes = b""
        self.mode: bytes = b""
        self.state: bytes = b""

    @classmethod
    def _from_bytes_data(
        cls, message_data: bytes
    ) -> "MarketParticipantPositionMessage":
        """Create a MarketParticipantPositionMessage from bytes data."""
        message = cls()
        (
            message.timestamp,
            message.mpid,
            message.stock,
            message.primary,
            message.mode,
            message.state,
        ) = struct.unpack("!I4s6sccc", message_data[1:18])
        return message

    def to_bytes(self) -> bytes:
        return struct.pack(
            "!cI4s6sccc",
            self.type,
            self.timestamp,
            self.mpid,
            self.stock,
            self.primary,
            self.mode,
            self.state,
        )

    def _add_json_fields(self, data: dict) -> None:
        data.update(
            {
                "mpid": self.mpid.decode().rstrip()
                if isinstance(self.mpid, bytes)
                else self.mpid,
                "stock": self.stock.decode().rstrip()
                if isinstance(self.stock, bytes)
                else self.stock,
                "primary": self.primary.decode()
                if isinstance(self.primary, bytes)
                else self.primary,
                "mode": self.mode.decode()
                if isinstance(self.mode, bytes)
                else self.mode,
                "state": self.state.decode()
                if isinstance(self.state, bytes)
                else self.state,
            }
        )

    @classmethod
    def _from_json_data(cls, data: dict) -> "MarketParticipantPositionMessage":
        message = cls()
        message.timestamp = data.get("timestamp", 0)
        stock = data.get("stock", "")
        if isinstance(stock, str):
            stock = stock.ljust(6).encode()
        message.stock = stock
        mpid = data.get("mpid", "")
        if isinstance(mpid, str):
            mpid = mpid.ljust(4).encode()
        message.mpid = mpid
        for field_name in ["primary", "mode", "state"]:
            value = data.get(field_name, " ")
            if isinstance(value, str):
                value = value.encode()
            setattr(message, field_name, value)
        return message


class AddOrderMessage(ITCH4MarketMessage):
    """Add Order Message (A) - no MPID.

    Format: A(1) + timestamp(4) + order_ref(8) + side(1) + shares(4) + stock(6) + price(4) = 28 bytes
    """

    type = b"A"
    description = "Add Order Message"
    message_size = 28

    def __init__(self) -> None:
        """Initialize an AddOrderMessage."""
        super().__init__()
        self.order_ref: int = 0
        self.side: bytes = b""
        self.shares: int = 0
        self.stock: bytes = b""
        self.price: int = 0

    @classmethod
    def _from_bytes_data(cls, message_data: bytes) -> "AddOrderMessage":
        """Create an AddOrderMessage from bytes data."""
        message = cls()
        (
            message.timestamp,
            message.order_ref,
            message.side,
            message.shares,
            message.stock,
            message.price,
        ) = struct.unpack("!IQcI6sI", message_data[1:28])
        return message

    def to_bytes(self) -> bytes:
        return struct.pack(
            "!cIQcI6sI",
            self.type,
            self.timestamp,
            self.order_ref,
            self.side,
            self.shares,
            self.stock,
            self.price,
        )

    def _add_json_fields(self, data: dict) -> None:
        data.update(
            {
                "order_ref": self.order_ref,
                "side": self.side.decode()
                if isinstance(self.side, bytes)
                else self.side,
                "shares": self.shares,
                "stock": self.stock.decode().rstrip()
                if isinstance(self.stock, bytes)
                else self.stock,
                "price": self.price,
            }
        )

    @classmethod
    def _from_json_data(cls, data: dict) -> "AddOrderMessage":
        message = cls()
        message.timestamp = data.get("timestamp", 0)
        message.order_ref = data.get("order_ref", 0)
        message.shares = data.get("shares", 0)
        message.price = data.get("price", 0)
        side = data.get("side", " ")
        if isinstance(side, str):
            side = side.encode()
        message.side = side
        stock = data.get("stock", "")
        if isinstance(stock, str):
            stock = stock.ljust(6).encode()
        message.stock = stock
        return message


class AddOrderMPIDMessage(ITCH4MarketMessage):
    """Add Order Message with MPID (F).

    Format: F(1) + timestamp(4) + order_ref(8) + side(1) + shares(4) + stock(6) + price(4) + mpid(4) = 32 bytes
    """

    type = b"F"
    description = "Add Order MPID Message"
    message_size = 32

    def __init__(self) -> None:
        """Initialize an AddOrderMPIDMessage."""
        super().__init__()
        self.order_ref: int = 0
        self.side: bytes = b""
        self.shares: int = 0
        self.stock: bytes = b""
        self.price: int = 0
        self.mpid: bytes = b""

    @classmethod
    def _from_bytes_data(cls, message_data: bytes) -> "AddOrderMPIDMessage":
        """Create an AddOrderMPIDMessage from bytes data."""
        message = cls()
        (
            message.timestamp,
            message.order_ref,
            message.side,
            message.shares,
            message.stock,
            message.price,
            message.mpid,
        ) = struct.unpack("!IQcI6sI4s", message_data[1:32])
        return message

    def to_bytes(self) -> bytes:
        return struct.pack(
            "!cIQcI6sI4s",
            self.type,
            self.timestamp,
            self.order_ref,
            self.side,
            self.shares,
            self.stock,
            self.price,
            self.mpid,
        )

    def _add_json_fields(self, data: dict) -> None:
        data.update(
            {
                "order_ref": self.order_ref,
                "side": self.side.decode()
                if isinstance(self.side, bytes)
                else self.side,
                "shares": self.shares,
                "stock": self.stock.decode().rstrip()
                if isinstance(self.stock, bytes)
                else self.stock,
                "price": self.price,
                "mpid": self.mpid.decode().rstrip()
                if isinstance(self.mpid, bytes)
                else self.mpid,
            }
        )

    @classmethod
    def _from_json_data(cls, data: dict) -> "AddOrderMPIDMessage":
        message = cls()
        message.timestamp = data.get("timestamp", 0)
        message.order_ref = data.get("order_ref", 0)
        message.shares = data.get("shares", 0)
        message.price = data.get("price", 0)
        side = data.get("side", " ")
        if isinstance(side, str):
            side = side.encode()
        message.side = side
        stock = data.get("stock", "")
        if isinstance(stock, str):
            stock = stock.ljust(6).encode()
        message.stock = stock
        mpid = data.get("mpid", "")
        if isinstance(mpid, str):
            mpid = mpid.ljust(4).encode()
        message.mpid = mpid
        return message


class OrderExecutedMessage(ITCH4MarketMessage):
    """Order Executed Message (E).

    Format: E(1) + timestamp(4) + order_ref(8) + shares(4) + match_number(8) = 25 bytes
    """

    type = b"E"
    description = "Order Executed Message"
    message_size = 25

    def __init__(self) -> None:
        """Initialize an OrderExecutedMessage."""
        super().__init__()
        self.order_ref: int = 0
        self.shares: int = 0
        self.match_number: int = 0

    @classmethod
    def _from_bytes_data(cls, message_data: bytes) -> "OrderExecutedMessage":
        """Create an OrderExecutedMessage from bytes data."""
        message = cls()
        (
            message.timestamp,
            message.order_ref,
            message.shares,
            message.match_number,
        ) = struct.unpack("!IQIQ", message_data[1:25])
        return message

    def to_bytes(self) -> bytes:
        return struct.pack(
            "!cIQIQ",
            self.type,
            self.timestamp,
            self.order_ref,
            self.shares,
            self.match_number,
        )

    def _add_json_fields(self, data: dict) -> None:
        data.update(
            {
                "order_ref": self.order_ref,
                "shares": self.shares,
                "match_number": self.match_number,
            }
        )

    @classmethod
    def _from_json_data(cls, data: dict) -> "OrderExecutedMessage":
        message = cls()
        message.timestamp = data.get("timestamp", 0)
        message.order_ref = data.get("order_ref", 0)
        message.shares = data.get("shares", 0)
        message.match_number = data.get("match_number", 0)
        return message


class OrderExecutedPriceMessage(ITCH4MarketMessage):
    """Order Executed With Price Message (C).

    Format: C(1) + timestamp(4) + order_ref(8) + shares(4) + match_number(8) + printable(1) + price(4) = 30 bytes
    """

    type = b"C"
    description = "Order Executed With Price Message"
    message_size = 30

    def __init__(self) -> None:
        """Initialize an OrderExecutedPriceMessage."""
        super().__init__()
        self.order_ref: int = 0
        self.shares: int = 0
        self.match_number: int = 0
        self.printable: bytes = b""
        self.price: int = 0

    @classmethod
    def _from_bytes_data(cls, message_data: bytes) -> "OrderExecutedPriceMessage":
        """Create an OrderExecutedPriceMessage from bytes data."""
        message = cls()
        (
            message.timestamp,
            message.order_ref,
            message.shares,
            message.match_number,
            message.printable,
            message.price,
        ) = struct.unpack("!IQIQcI", message_data[1:30])
        return message

    def to_bytes(self) -> bytes:
        return struct.pack(
            "!cIQIQcI",
            self.type,
            self.timestamp,
            self.order_ref,
            self.shares,
            self.match_number,
            self.printable,
            self.price,
        )

    def _add_json_fields(self, data: dict) -> None:
        data.update(
            {
                "order_ref": self.order_ref,
                "shares": self.shares,
                "match_number": self.match_number,
                "printable": self.printable.decode()
                if isinstance(self.printable, bytes)
                else self.printable,
                "price": self.price,
            }
        )

    @classmethod
    def _from_json_data(cls, data: dict) -> "OrderExecutedPriceMessage":
        message = cls()
        message.timestamp = data.get("timestamp", 0)
        message.order_ref = data.get("order_ref", 0)
        message.shares = data.get("shares", 0)
        message.match_number = data.get("match_number", 0)
        message.price = data.get("price", 0)
        printable = data.get("printable", " ")
        if isinstance(printable, str):
            printable = printable.encode()
        message.printable = printable
        return message


class OrderCancelMessage(ITCH4MarketMessage):
    """Order Cancel Message (X).

    Format: X(1) + timestamp(4) + order_ref(8) + shares(4) = 17 bytes
    """

    type = b"X"
    description = "Order Cancel Message"
    message_size = 17

    def __init__(self) -> None:
        """Initialize an OrderCancelMessage."""
        super().__init__()
        self.order_ref: int = 0
        self.shares: int = 0

    @classmethod
    def _from_bytes_data(cls, message_data: bytes) -> "OrderCancelMessage":
        """Create an OrderCancelMessage from bytes data."""
        message = cls()
        (
            message.timestamp,
            message.order_ref,
            message.shares,
        ) = struct.unpack("!IQI", message_data[1:17])
        return message

    def to_bytes(self) -> bytes:
        return struct.pack(
            "!cIQI",
            self.type,
            self.timestamp,
            self.order_ref,
            self.shares,
        )

    def _add_json_fields(self, data: dict) -> None:
        data.update(
            {
                "order_ref": self.order_ref,
                "shares": self.shares,
            }
        )

    @classmethod
    def _from_json_data(cls, data: dict) -> "OrderCancelMessage":
        message = cls()
        message.timestamp = data.get("timestamp", 0)
        message.order_ref = data.get("order_ref", 0)
        message.shares = data.get("shares", 0)
        return message


class OrderDeleteMessage(ITCH4MarketMessage):
    """Order Delete Message (D).

    Format: D(1) + timestamp(4) + order_ref(8) = 13 bytes
    """

    type = b"D"
    description = "Order Delete Message"
    message_size = 13

    def __init__(self) -> None:
        """Initialize an OrderDeleteMessage."""
        super().__init__()
        self.order_ref: int = 0

    @classmethod
    def _from_bytes_data(cls, message_data: bytes) -> "OrderDeleteMessage":
        """Create an OrderDeleteMessage from bytes data."""
        message = cls()
        (
            message.timestamp,
            message.order_ref,
        ) = struct.unpack("!IQ", message_data[1:13])
        return message

    def to_bytes(self) -> bytes:
        return struct.pack(
            "!cIQ",
            self.type,
            self.timestamp,
            self.order_ref,
        )

    def _add_json_fields(self, data: dict) -> None:
        data["order_ref"] = self.order_ref

    @classmethod
    def _from_json_data(cls, data: dict) -> "OrderDeleteMessage":
        message = cls()
        message.timestamp = data.get("timestamp", 0)
        message.order_ref = data.get("order_ref", 0)
        return message


class OrderReplaceMessage(ITCH4MarketMessage):
    """Order Replace Message (U).

    Format: U(1) + timestamp(4) + original_ref(8) + new_ref(8) + shares(4) + price(4) = 29 bytes
    """

    type = b"U"
    description = "Order Replace Message"
    message_size = 29

    def __init__(self) -> None:
        """Initialize an OrderReplaceMessage."""
        super().__init__()
        self.original_ref: int = 0
        self.new_ref: int = 0
        self.shares: int = 0
        self.price: int = 0

    @classmethod
    def _from_bytes_data(cls, message_data: bytes) -> "OrderReplaceMessage":
        """Create an OrderReplaceMessage from bytes data."""
        message = cls()
        (
            message.timestamp,
            message.original_ref,
            message.new_ref,
            message.shares,
            message.price,
        ) = struct.unpack("!IQQII", message_data[1:29])
        return message

    def to_bytes(self) -> bytes:
        return struct.pack(
            "!cIQQII",
            self.type,
            self.timestamp,
            self.original_ref,
            self.new_ref,
            self.shares,
            self.price,
        )

    def _add_json_fields(self, data: dict) -> None:
        data.update(
            {
                "original_ref": self.original_ref,
                "new_ref": self.new_ref,
                "shares": self.shares,
                "price": self.price,
            }
        )

    @classmethod
    def _from_json_data(cls, data: dict) -> "OrderReplaceMessage":
        message = cls()
        message.timestamp = data.get("timestamp", 0)
        message.original_ref = data.get("original_ref", 0)
        message.new_ref = data.get("new_ref", 0)
        message.shares = data.get("shares", 0)
        message.price = data.get("price", 0)
        return message


class TradeMessage(ITCH4MarketMessage):
    """Trade Message (P).

    Format: P(1) + timestamp(4) + order_ref(8) + side(1) + shares(4) + stock(6) + price(4) + match_number(8) = 36 bytes
    """

    type = b"P"
    description = "Trade Message"
    message_size = 36

    def __init__(self) -> None:
        """Initialize a TradeMessage."""
        super().__init__()
        self.order_ref: int = 0
        self.side: bytes = b""
        self.shares: int = 0
        self.stock: bytes = b""
        self.price: int = 0
        self.match_number: int = 0

    @classmethod
    def _from_bytes_data(cls, message_data: bytes) -> "TradeMessage":
        """Create a TradeMessage from bytes data."""
        message = cls()
        (
            message.timestamp,
            message.order_ref,
            message.side,
            message.shares,
            message.stock,
            message.price,
            message.match_number,
        ) = struct.unpack("!IQcI6sIQ", message_data[1:36])
        return message

    def to_bytes(self) -> bytes:
        return struct.pack(
            "!cIQcI6sIQ",
            self.type,
            self.timestamp,
            self.order_ref,
            self.side,
            self.shares,
            self.stock,
            self.price,
            self.match_number,
        )

    def _add_json_fields(self, data: dict) -> None:
        data.update(
            {
                "order_ref": self.order_ref,
                "side": self.side.decode()
                if isinstance(self.side, bytes)
                else self.side,
                "shares": self.shares,
                "stock": self.stock.decode().rstrip()
                if isinstance(self.stock, bytes)
                else self.stock,
                "price": self.price,
                "match_number": self.match_number,
            }
        )

    @classmethod
    def _from_json_data(cls, data: dict) -> "TradeMessage":
        message = cls()
        message.timestamp = data.get("timestamp", 0)
        message.order_ref = data.get("order_ref", 0)
        message.shares = data.get("shares", 0)
        message.price = data.get("price", 0)
        message.match_number = data.get("match_number", 0)
        side = data.get("side", " ")
        if isinstance(side, str):
            side = side.encode()
        message.side = side
        stock = data.get("stock", "")
        if isinstance(stock, str):
            stock = stock.ljust(6).encode()
        message.stock = stock
        return message


class BrokenTradeMessage(ITCH4MarketMessage):
    """Broken Trade Message (B).

    Format: B(1) + timestamp(4) + match_number(8) = 13 bytes
    """

    type = b"B"
    description = "Broken Trade Message"
    message_size = 13

    def __init__(self) -> None:
        """Initialize a BrokenTradeMessage."""
        super().__init__()
        self.match_number: int = 0

    @classmethod
    def _from_bytes_data(cls, message_data: bytes) -> "BrokenTradeMessage":
        """Create a BrokenTradeMessage from bytes data."""
        message = cls()
        (
            message.timestamp,
            message.match_number,
        ) = struct.unpack("!IQ", message_data[1:13])
        return message

    def to_bytes(self) -> bytes:
        return struct.pack(
            "!cIQ",
            self.type,
            self.timestamp,
            self.match_number,
        )

    def _add_json_fields(self, data: dict) -> None:
        data["match_number"] = self.match_number

    @classmethod
    def _from_json_data(cls, data: dict) -> "BrokenTradeMessage":
        message = cls()
        message.timestamp = data.get("timestamp", 0)
        message.match_number = data.get("match_number", 0)
        return message


class CrossTradeMessage(ITCH4MarketMessage):
    """Cross Trade Message (Q).

    Format: Q(1) + timestamp(4) + shares(8) + stock(6) + price(4) + match_number(8) + cross_type(1) = 32 bytes
    """

    type = b"Q"
    description = "Cross Trade Message"
    message_size = 32

    def __init__(self) -> None:
        """Initialize a CrossTradeMessage."""
        super().__init__()
        self.shares: int = 0
        self.stock: bytes = b""
        self.price: int = 0
        self.match_number: int = 0
        self.cross_type: bytes = b""

    @classmethod
    def _from_bytes_data(cls, message_data: bytes) -> "CrossTradeMessage":
        """Create a CrossTradeMessage from bytes data."""
        message = cls()
        (
            message.timestamp,
            message.shares,
            message.stock,
            message.price,
            message.match_number,
            message.cross_type,
        ) = struct.unpack("!IQ6sIQc", message_data[1:32])
        return message

    def to_bytes(self) -> bytes:
        return struct.pack(
            "!cIQ6sIQc",
            self.type,
            self.timestamp,
            self.shares,
            self.stock,
            self.price,
            self.match_number,
            self.cross_type,
        )

    def _add_json_fields(self, data: dict) -> None:
        data.update(
            {
                "shares": self.shares,
                "stock": self.stock.decode().rstrip()
                if isinstance(self.stock, bytes)
                else self.stock,
                "price": self.price,
                "match_number": self.match_number,
                "cross_type": self.cross_type.decode()
                if isinstance(self.cross_type, bytes)
                else self.cross_type,
            }
        )

    @classmethod
    def _from_json_data(cls, data: dict) -> "CrossTradeMessage":
        message = cls()
        message.timestamp = data.get("timestamp", 0)
        message.shares = data.get("shares", 0)
        message.price = data.get("price", 0)
        message.match_number = data.get("match_number", 0)
        stock = data.get("stock", "")
        if isinstance(stock, str):
            stock = stock.ljust(6).encode()
        message.stock = stock
        cross_type = data.get("cross_type", " ")
        if isinstance(cross_type, str):
            cross_type = cross_type.encode()
        message.cross_type = cross_type
        return message


class NoiiMessage(ITCH4MarketMessage):
    """NOII Message (I) - Net Order Imbalance Indicator.

    Format: I(1) + timestamp(4) + paired_shares(8) + imbalance_shares(8) + imbalance_direction(1)
            + stock(6) + far_price(4) + near_price(4) + current_ref_price(4) + cross_type(1) + price_var(1) = 42 bytes
    """

    type = b"I"
    description = "NOII Message"
    message_size = 42

    def __init__(self) -> None:
        """Initialize a NoiiMessage."""
        super().__init__()
        self.paired_shares: int = 0
        self.imbalance_shares: int = 0
        self.imbalance_direction: bytes = b""
        self.stock: bytes = b""
        self.far_price: int = 0
        self.near_price: int = 0
        self.current_ref_price: int = 0
        self.cross_type: bytes = b""
        self.price_variation_indicator: bytes = b""

    @classmethod
    def _from_bytes_data(cls, message_data: bytes) -> "NoiiMessage":
        """Create a NoiiMessage from bytes data."""
        message = cls()
        (
            message.timestamp,
            message.paired_shares,
            message.imbalance_shares,
            message.imbalance_direction,
            message.stock,
            message.far_price,
            message.near_price,
            message.current_ref_price,
            message.cross_type,
            message.price_variation_indicator,
        ) = struct.unpack("!IQQc6sIIIcc", message_data[1:42])
        return message

    def to_bytes(self) -> bytes:
        return struct.pack(
            "!cIQQc6sIIIcc",
            self.type,
            self.timestamp,
            self.paired_shares,
            self.imbalance_shares,
            self.imbalance_direction,
            self.stock,
            self.far_price,
            self.near_price,
            self.current_ref_price,
            self.cross_type,
            self.price_variation_indicator,
        )

    def _add_json_fields(self, data: dict) -> None:
        data.update(
            {
                "paired_shares": self.paired_shares,
                "imbalance_shares": self.imbalance_shares,
                "imbalance_direction": self.imbalance_direction.decode()
                if isinstance(self.imbalance_direction, bytes)
                else self.imbalance_direction,
                "stock": self.stock.decode().rstrip()
                if isinstance(self.stock, bytes)
                else self.stock,
                "far_price": self.far_price,
                "near_price": self.near_price,
                "current_ref_price": self.current_ref_price,
                "cross_type": self.cross_type.decode()
                if isinstance(self.cross_type, bytes)
                else self.cross_type,
                "price_variation_indicator": self.price_variation_indicator.decode()
                if isinstance(self.price_variation_indicator, bytes)
                else self.price_variation_indicator,
            }
        )

    @classmethod
    def _from_json_data(cls, data: dict) -> "NoiiMessage":
        message = cls()
        message.timestamp = data.get("timestamp", 0)
        message.paired_shares = data.get("paired_shares", 0)
        message.imbalance_shares = data.get("imbalance_shares", 0)
        message.far_price = data.get("far_price", 0)
        message.near_price = data.get("near_price", 0)
        message.current_ref_price = data.get("current_ref_price", 0)
        stock = data.get("stock", "")
        if isinstance(stock, str):
            stock = stock.ljust(6).encode()
        message.stock = stock
        for field_name in [
            "imbalance_direction",
            "cross_type",
            "price_variation_indicator",
        ]:
            value = data.get(field_name, " ")
            if isinstance(value, str):
                value = value.encode()
            setattr(message, field_name, value)
        return message
