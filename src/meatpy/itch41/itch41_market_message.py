"""ITCH 4.1 market message types and parsing.

This module provides classes for parsing and representing ITCH 4.1 market data
messages. It includes message types defined in the ITCH 4.1 specification,
adapted from ITCH 5.0 with simplifications for the older format.
"""

import json
import struct

from ..message_reader import MarketMessage


class ITCH41MarketMessage(MarketMessage):
    """A market message in ITCH 4.1 format.

    This is the base class for all ITCH 4.1 message types. It provides
    common functionality for timestamp handling and message formatting.
    ITCH 4.1 generally has simpler structure than ITCH 5.0.

    Attributes:
        timestamp: The timestamp of the message
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

    finStatusbsindicators = {
        b"D": "Deficient",
        b"E": "Delinquent",
        b"Q": "Bankrupt",
        b"S": "Suspended",
        b"G": "Deficient and Bankrupt",
        b"H": "Deficient and Delinquent",
        b"J": "Delinquent and Bankrupt",
        b"K": "Deficient, Delinquent and Bankrupt",
        b"N": "Normal (Default): Issuer Is NOT Deficient, Delinquent, or Bankrupt",
        b" ": "Not available",
    }

    roundLotsOnly = {b"Y": "Only round lots", b"N": "Odd and Mixed lots"}

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

    priceVariationIndicator = {
        b"L": "Less",
        b"1": "1-199",
        b"2": "200-299",
        b"3": "300-399",
        b"4": "400-499",
        b"5": "500-599",
        b"6": "600-699",
        b"7": "700-799",
        b"8": "800-899",
        b"9": "900-999",
        b"A": "1000-1999",
        b"B": "2000-2999",
        b"C": "3000-3999",
        b"D": "4000-4999",
        b"E": "5000-5999",
        b"F": "6000-6999",
        b"G": "7000-7999",
        b"H": "8000-8999",
        b"I": "9000-9999",
        b"J": "10000 or greater",
        b" ": "No Calculation",
    }

    crossTradeTypes = {
        b"O": "Opening Cross",
        b"C": "Closing Cross",
        b"H": "Cross for IPO and Halted / Paused Securities",
        b"I": "NASDAQ Cross Network",
    }

    def __init__(self) -> None:
        """Initialize an ITCH41MarketMessage."""
        self.timestamp: int = 0

    def set_timestamp(self, ts1: int, ts2: int) -> None:
        """Set the timestamp from two integers."""
        self.timestamp = (ts1 << 32) | ts2

    def split_timestamp(self) -> tuple[int, int]:
        """Split the timestamp into two integers."""
        ts1 = self.timestamp >> 32
        ts2 = self.timestamp & 0xFFFFFFFF
        return ts1, ts2

    @classmethod
    def from_bytes(cls, message_data: bytes) -> "ITCH41MarketMessage":
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

        # Message type mapping for ITCH 4.1
        message_classes = {
            b"T": SecondsMessage,
            b"S": SystemEventMessage,
            b"R": StockDirectoryMessage,
            b"H": StockTradingActionMessage,
            b"Y": RegSHOMessage,
            # b"L": MarketParticipantPositionMessage,  # Temporarily disabled for debugging
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
        }

        message_class = message_classes.get(message_type)
        if message_class is None:
            raise UnknownMessageTypeError(f"Unknown message type: {message_type}")

        return message_class._from_bytes_data(message_data)

    @classmethod
    def _from_bytes_data(cls, message_data: bytes) -> "ITCH41MarketMessage":
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
        # Default implementation - subclasses should override
        pass

    @classmethod
    def from_json(cls, json_str: str) -> "ITCH41MarketMessage":
        """Create a message object from JSON string."""
        data = json.loads(json_str)
        return cls._from_json_data(data)

    @classmethod
    def _from_json_data(cls, data: dict) -> "ITCH41MarketMessage":
        """Create a message object from JSON data."""
        raise NotImplementedError("Subclasses must implement _from_json_data")

    def validate_code(self, code: bytes, code_dict: dict) -> bool:
        """Validate a code against a dictionary of valid codes."""
        return code in code_dict

    def validate_market_code(self, market_code: bytes) -> bool:
        """Validate a market code."""
        return self.validate_code(market_code, self.market)

    def validate_financial_status_indicator(self, fsi: bytes) -> bool:
        """Validate a financial status indicator."""
        return self.validate_code(fsi, self.finStatusbsindicators)

    def validate(self) -> bool:
        """Validate all codes in this message."""
        # Default implementation - subclasses should override with specific validation
        return True


class SecondsMessage(ITCH41MarketMessage):
    type = b"T"
    description = "Seconds Message"
    message_size = struct.calcsize("!I") + 1

    def __init__(self) -> None:
        """Initialize a SecondsMessage."""
        super().__init__()
        self.seconds: int = 0

    @classmethod
    def _from_bytes_data(cls, message_data: bytes) -> "SecondsMessage":
        """Create a SecondsMessage from bytes data."""
        message = cls()
        (message.seconds,) = struct.unpack("!I", message_data[1:])
        # For seconds messages, set timestamp to seconds value in nanoseconds
        message.timestamp = message.seconds * 1_000_000_000
        return message

    def to_bytes(self) -> bytes:
        return struct.pack("!cI", self.type, self.seconds)

    def _add_json_fields(self, data: dict) -> None:
        """Add SecondsMessage-specific fields to JSON data."""
        data.update({"seconds": self.seconds})

    @classmethod
    def _from_json_data(cls, data: dict) -> "SecondsMessage":
        """Create a SecondsMessage from JSON data."""
        message = cls()
        message.seconds = data.get("seconds", 0)
        message.timestamp = message.seconds * 1_000_000_000
        return message


class SystemEventMessage(ITCH41MarketMessage):
    type = b"S"
    description = "System Event Message"
    message_size = struct.calcsize("!Ic") + 1

    def __init__(self) -> None:
        """Initialize a SystemEventMessage."""
        super().__init__()
        self.event_code: bytes = b""

    @classmethod
    def _from_bytes_data(cls, message_data: bytes) -> "SystemEventMessage":
        """Create a SystemEventMessage from bytes data."""
        message = cls()
        (
            timestamp,
            message.event_code,
        ) = struct.unpack("!Ic", message_data[1:])
        message.timestamp = timestamp * 1_000_000_000  # Convert to nanoseconds
        return message

    def to_bytes(self) -> bytes:
        return struct.pack(
            "!cIc",
            self.type,
            self.timestamp // 1_000_000_000,  # Convert to seconds
            self.event_code,
        )

    def _add_json_fields(self, data: dict) -> None:
        """Add SystemEventMessage-specific fields to JSON data."""
        data.update(
            {
                "event_code": self.event_code.decode()
                if isinstance(self.event_code, bytes)
                else self.event_code,
            }
        )

    @classmethod
    def _from_json_data(cls, data: dict) -> "SystemEventMessage":
        """Create a SystemEventMessage from JSON data."""
        message = cls()
        message.timestamp = data.get("timestamp", 0)
        event_code = data.get("event_code", " ")
        if isinstance(event_code, str):
            event_code = event_code.encode()
        message.event_code = event_code
        return message

    def validate(self) -> bool:
        """Validate all codes in this SystemEventMessage."""
        return self.validate_code(self.event_code, self.sysEventCodes)


class StockDirectoryMessage(ITCH41MarketMessage):
    type = b"R"
    description = "Stock Directory Message"
    message_size = struct.calcsize("!I8sccIc") + 1

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
            timestamp,
            message.stock,
            message.category,
            message.status,
            message.lotsize,
            message.lotsonly,
        ) = struct.unpack("!I8sccIc", message_data[1:])
        message.timestamp = timestamp * 1_000_000_000  # Convert to nanoseconds
        return message

    def to_bytes(self) -> bytes:
        return struct.pack(
            "!cI8sccIc",
            self.type,
            self.timestamp // 1_000_000_000,  # Convert to seconds
            self.stock,
            self.category,
            self.status,
            self.lotsize,
            self.lotsonly,
        )

    def _add_json_fields(self, data: dict) -> None:
        """Add StockDirectoryMessage-specific fields to JSON data."""
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
        for field_name in [
            "stock",
            "category",
            "status",
            "lotsonly",
        ]:
            value = data.get(field_name, b"" if field_name == "stock" else " ")
            if isinstance(value, str):
                if field_name == "stock":
                    value = value.ljust(8).encode()
                else:
                    value = value.encode()
            setattr(message, field_name, value)
        message.lotsize = data.get("lotsize", 0)
        return message

    def validate(self) -> bool:
        """Validate all codes in this StockDirectoryMessage."""
        return (
            self.validate_market_code(self.category)
            and self.validate_financial_status_indicator(self.status)
            and self.validate_code(self.lotsonly, self.roundLotsOnly)
        )


class StockTradingActionMessage(ITCH41MarketMessage):
    type = b"H"
    description = "Stock Trading Action Message"
    message_size = struct.calcsize("!I8scc4s") + 1

    def __init__(self) -> None:
        """Initialize a StockTradingActionMessage."""
        super().__init__()
        self.stock: bytes = b""
        self.state: bytes = b""
        self.reserved: bytes = b""
        self.reason: bytes = b""

    @classmethod
    def _from_bytes_data(cls, message_data: bytes) -> "StockTradingActionMessage":
        """Create a StockTradingActionMessage from bytes data."""
        message = cls()
        (
            timestamp,
            message.stock,
            message.state,
            message.reserved,
            message.reason,
        ) = struct.unpack("!I8scc4s", message_data[1:])
        message.timestamp = timestamp * 1_000_000_000  # Convert to nanoseconds
        return message

    def to_bytes(self) -> bytes:
        return struct.pack(
            "!cI8scc4s",
            self.type,
            self.timestamp // 1_000_000_000,  # Convert to seconds
            self.stock,
            self.state,
            self.reserved,
            self.reason,
        )

    def _add_json_fields(self, data: dict) -> None:
        """Add StockTradingActionMessage-specific fields to JSON data."""
        data.update(
            {
                "stock": self.stock.decode().rstrip()
                if isinstance(self.stock, bytes)
                else self.stock,
                "state": self.state.decode()
                if isinstance(self.state, bytes)
                else self.state,
                "reserved": self.reserved.decode()
                if isinstance(self.reserved, bytes)
                else self.reserved,
                "reason": self.reason.decode().rstrip()
                if isinstance(self.reason, bytes)
                else self.reason,
            }
        )

    @classmethod
    def _from_json_data(cls, data: dict) -> "StockTradingActionMessage":
        """Create a StockTradingActionMessage from JSON data."""
        message = cls()
        message.timestamp = data.get("timestamp", 0)
        for field_name in ["stock", "state", "reserved", "reason"]:
            value = data.get(field_name, "")
            if isinstance(value, str):
                if field_name in ["stock", "reason"]:
                    value = value.ljust(8 if field_name == "stock" else 4).encode()
                else:
                    value = value.encode()
            setattr(message, field_name, value)
        return message

    def validate(self) -> bool:
        """Validate all codes in this StockTradingActionMessage."""
        return self.validate_code(self.state, self.tradingStates)


class RegSHOMessage(ITCH41MarketMessage):
    type = b"Y"
    description = "Reg SHO Restriction Message"
    message_size = struct.calcsize("!I8sc") + 1

    def __init__(self) -> None:
        """Initialize a RegSHOMessage."""
        super().__init__()
        self.stock: bytes = b""
        self.action: bytes = b""

    @classmethod
    def _from_bytes_data(cls, message_data: bytes) -> "RegSHOMessage":
        """Create a RegSHOMessage from bytes data."""
        message = cls()
        (
            timestamp,
            message.stock,
            message.action,
        ) = struct.unpack("!I8sc", message_data[1:])
        message.timestamp = timestamp * 1_000_000_000  # Convert to nanoseconds
        return message

    def to_bytes(self) -> bytes:
        return struct.pack(
            "!cI8sc",
            self.type,
            self.timestamp // 1_000_000_000,  # Convert to seconds
            self.stock,
            self.action,
        )

    def _add_json_fields(self, data: dict) -> None:
        """Add RegSHOMessage-specific fields to JSON data."""
        data.update(
            {
                "stock": self.stock.decode().rstrip()
                if isinstance(self.stock, bytes)
                else self.stock,
                "action": self.action.decode()
                if isinstance(self.action, bytes)
                else self.action,
            }
        )

    @classmethod
    def _from_json_data(cls, data: dict) -> "RegSHOMessage":
        """Create a RegSHOMessage from JSON data."""
        message = cls()
        message.timestamp = data.get("timestamp", 0)
        stock = data.get("stock", "")
        if isinstance(stock, str):
            stock = stock.ljust(8).encode()
        message.stock = stock
        action = data.get("action", " ")
        if isinstance(action, str):
            action = action.encode()
        message.action = action
        return message


class MarketParticipantPositionMessage(ITCH41MarketMessage):
    type = b"L"
    description = "Market Participant Position Message"
    message_size = struct.calcsize("!I4s8sccc") + 1

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
            timestamp,
            message.mpid,
            message.stock,
            message.primary,
            message.mode,
            message.state,
        ) = struct.unpack("!I4s8sccc", message_data[1:])
        message.timestamp = timestamp * 1_000_000_000  # Convert to nanoseconds
        return message

    def to_bytes(self) -> bytes:
        return struct.pack(
            "!cI4s8sccc",
            self.type,
            self.timestamp // 1_000_000_000,  # Convert to seconds
            self.mpid,
            self.stock,
            self.primary,
            self.mode,
            self.state,
        )

    def _add_json_fields(self, data: dict) -> None:
        """Add MarketParticipantPositionMessage-specific fields to JSON data."""
        data.update(
            {
                "stock": self.stock.decode().rstrip()
                if isinstance(self.stock, bytes)
                else self.stock,
                "mpid": self.mpid.decode().rstrip()
                if isinstance(self.mpid, bytes)
                else self.mpid,
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
        """Create a MarketParticipantPositionMessage from JSON data."""
        message = cls()
        message.timestamp = data.get("timestamp", 0)
        stock = data.get("stock", "")
        if isinstance(stock, str):
            stock = stock.ljust(8).encode()
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

    def validate(self) -> bool:
        """Validate all codes in this MarketParticipantPositionMessage."""
        return (
            self.validate_code(self.primary, self.primaryMarketMaker)
            and self.validate_code(self.mode, self.marketMakerModes)
            and self.validate_code(self.state, self.marketParticipantStates)
        )


class AddOrderMessage(ITCH41MarketMessage):
    type = b"A"
    description = "Add Order Message"
    message_size = struct.calcsize("!IQcI8sI") + 1

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
            timestamp,
            message.order_ref,
            message.side,
            message.shares,
            message.stock,
            message.price,
        ) = struct.unpack("!IQcI8sI", message_data[1:])
        message.timestamp = timestamp * 1_000_000_000  # Convert to nanoseconds
        return message

    def to_bytes(self) -> bytes:
        return struct.pack(
            "!cIQcI8sI",
            self.type,
            self.timestamp // 1_000_000_000,  # Convert to seconds
            self.order_ref,
            self.side,
            self.shares,
            self.stock,
            self.price,
        )

    def _add_json_fields(self, data: dict) -> None:
        """Add AddOrderMessage-specific fields to JSON data."""
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
        """Create an AddOrderMessage from JSON data."""
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
            stock = stock.ljust(8).encode()
        message.stock = stock
        return message


class AddOrderMPIDMessage(ITCH41MarketMessage):
    type = b"F"
    description = "Add Order MPID Message"
    message_size = struct.calcsize("!IQcI8sI4s") + 1

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
            timestamp,
            message.order_ref,
            message.side,
            message.shares,
            message.stock,
            message.price,
            message.mpid,
        ) = struct.unpack("!IQcI8sI4s", message_data[1:])
        message.timestamp = timestamp * 1_000_000_000  # Convert to nanoseconds
        return message

    def to_bytes(self) -> bytes:
        return struct.pack(
            "!cIQcI8sI4s",
            self.type,
            self.timestamp // 1_000_000_000,  # Convert to seconds
            self.order_ref,
            self.side,
            self.shares,
            self.stock,
            self.price,
            self.mpid,
        )

    def _add_json_fields(self, data: dict) -> None:
        """Add AddOrderMPIDMessage-specific fields to JSON data."""
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
        """Create an AddOrderMPIDMessage from JSON data."""
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
            stock = stock.ljust(8).encode()
        message.stock = stock
        mpid = data.get("mpid", "")
        if isinstance(mpid, str):
            mpid = mpid.ljust(4).encode()
        message.mpid = mpid
        return message


class OrderExecutedMessage(ITCH41MarketMessage):
    type = b"E"
    description = "Order Executed Message"
    message_size = struct.calcsize("!IQIQ") + 1

    def __init__(self) -> None:
        """Initialize an OrderExecutedMessage."""
        super().__init__()
        self.order_ref: int = 0
        self.shares: int = 0
        self.match_num: int = 0

    @classmethod
    def _from_bytes_data(cls, message_data: bytes) -> "OrderExecutedMessage":
        """Create an OrderExecutedMessage from bytes data."""
        message = cls()
        (
            timestamp,
            message.order_ref,
            message.shares,
            message.match_num,
        ) = struct.unpack("!IQIQ", message_data[1:])
        message.timestamp = timestamp * 1_000_000_000  # Convert to nanoseconds
        return message

    def to_bytes(self) -> bytes:
        return struct.pack(
            "!cIQIQ",
            self.type,
            self.timestamp // 1_000_000_000,  # Convert to seconds
            self.order_ref,
            self.shares,
            self.match_num,
        )

    def _add_json_fields(self, data: dict) -> None:
        """Add OrderExecutedMessage-specific fields to JSON data."""
        data.update(
            {
                "order_ref": self.order_ref,
                "shares": self.shares,
                "match_num": self.match_num,
            }
        )

    @classmethod
    def _from_json_data(cls, data: dict) -> "OrderExecutedMessage":
        """Create an OrderExecutedMessage from JSON data."""
        message = cls()
        message.timestamp = data.get("timestamp", 0)
        message.order_ref = data.get("order_ref", 0)
        message.shares = data.get("shares", 0)
        message.match_num = data.get("match_num", 0)
        return message


class OrderExecutedPriceMessage(ITCH41MarketMessage):
    type = b"C"
    description = "Order Executed with Price Message"
    message_size = struct.calcsize("!IQIQcI") + 1

    def __init__(self) -> None:
        """Initialize an OrderExecutedPriceMessage."""
        super().__init__()
        self.order_ref: int = 0
        self.shares: int = 0
        self.match_num: int = 0
        self.printable: bytes = b""
        self.price: int = 0

    @classmethod
    def _from_bytes_data(cls, message_data: bytes) -> "OrderExecutedPriceMessage":
        """Create an OrderExecutedPriceMessage from bytes data."""
        message = cls()
        (
            timestamp,
            message.order_ref,
            message.shares,
            message.match_num,
            message.printable,
            message.price,
        ) = struct.unpack("!IQIQcI", message_data[1:])
        message.timestamp = timestamp * 1_000_000_000  # Convert to nanoseconds
        return message

    def to_bytes(self) -> bytes:
        return struct.pack(
            "!cIQIQcI",
            self.type,
            self.timestamp // 1_000_000_000,  # Convert to seconds
            self.order_ref,
            self.shares,
            self.match_num,
            self.printable,
            self.price,
        )

    def _add_json_fields(self, data: dict) -> None:
        """Add OrderExecutedPriceMessage-specific fields to JSON data."""
        data.update(
            {
                "order_ref": self.order_ref,
                "shares": self.shares,
                "match_num": self.match_num,
                "printable": self.printable.decode()
                if isinstance(self.printable, bytes)
                else self.printable,
                "price": self.price,
            }
        )

    @classmethod
    def _from_json_data(cls, data: dict) -> "OrderExecutedPriceMessage":
        """Create an OrderExecutedPriceMessage from JSON data."""
        message = cls()
        message.timestamp = data.get("timestamp", 0)
        message.order_ref = data.get("order_ref", 0)
        message.shares = data.get("shares", 0)
        message.match_num = data.get("match_num", 0)
        message.price = data.get("price", 0)
        printable = data.get("printable", " ")
        if isinstance(printable, str):
            printable = printable.encode()
        message.printable = printable
        return message


class OrderCancelMessage(ITCH41MarketMessage):
    type = b"X"
    description = "Order Cancel Message"
    message_size = struct.calcsize("!IQI") + 1

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
            timestamp,
            message.order_ref,
            message.shares,
        ) = struct.unpack("!IQI", message_data[1:])
        message.timestamp = timestamp * 1_000_000_000  # Convert to nanoseconds
        return message

    def to_bytes(self) -> bytes:
        return struct.pack(
            "!cIQI",
            self.type,
            self.timestamp // 1_000_000_000,  # Convert to seconds
            self.order_ref,
            self.shares,
        )

    def _add_json_fields(self, data: dict) -> None:
        """Add OrderCancelMessage-specific fields to JSON data."""
        data.update(
            {
                "order_ref": self.order_ref,
                "shares": self.shares,
            }
        )

    @classmethod
    def _from_json_data(cls, data: dict) -> "OrderCancelMessage":
        """Create an OrderCancelMessage from JSON data."""
        message = cls()
        message.timestamp = data.get("timestamp", 0)
        message.order_ref = data.get("order_ref", 0)
        message.shares = data.get("shares", 0)
        return message


class OrderDeleteMessage(ITCH41MarketMessage):
    type = b"D"
    description = "Order Delete Message"
    message_size = struct.calcsize("!IQ") + 1

    def __init__(self) -> None:
        """Initialize an OrderDeleteMessage."""
        super().__init__()
        self.order_ref: int = 0

    @classmethod
    def _from_bytes_data(cls, message_data: bytes) -> "OrderDeleteMessage":
        """Create an OrderDeleteMessage from bytes data."""
        message = cls()
        (
            timestamp,
            message.order_ref,
        ) = struct.unpack("!IQ", message_data[1:])
        message.timestamp = timestamp * 1_000_000_000  # Convert to nanoseconds
        return message

    def to_bytes(self) -> bytes:
        return struct.pack(
            "!cIQ",
            self.type,
            self.timestamp // 1_000_000_000,  # Convert to seconds
            self.order_ref,
        )

    def _add_json_fields(self, data: dict) -> None:
        """Add OrderDeleteMessage-specific fields to JSON data."""
        data.update(
            {
                "order_ref": self.order_ref,
            }
        )

    @classmethod
    def _from_json_data(cls, data: dict) -> "OrderDeleteMessage":
        """Create an OrderDeleteMessage from JSON data."""
        message = cls()
        message.timestamp = data.get("timestamp", 0)
        message.order_ref = data.get("order_ref", 0)
        return message


class OrderReplaceMessage(ITCH41MarketMessage):
    type = b"U"
    description = "Order Replace Message"
    message_size = struct.calcsize("!IQQII") + 1

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
            timestamp,
            message.original_ref,
            message.new_ref,
            message.shares,
            message.price,
        ) = struct.unpack("!IQQII", message_data[1:])
        message.timestamp = timestamp * 1_000_000_000  # Convert to nanoseconds
        return message

    def to_bytes(self) -> bytes:
        return struct.pack(
            "!cIQQII",
            self.type,
            self.timestamp // 1_000_000_000,  # Convert to seconds
            self.original_ref,
            self.new_ref,
            self.shares,
            self.price,
        )

    def _add_json_fields(self, data: dict) -> None:
        """Add OrderReplaceMessage-specific fields to JSON data."""
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
        """Create an OrderReplaceMessage from JSON data."""
        message = cls()
        message.timestamp = data.get("timestamp", 0)
        message.original_ref = data.get("original_ref", 0)
        message.new_ref = data.get("new_ref", 0)
        message.shares = data.get("shares", 0)
        message.price = data.get("price", 0)
        return message


class TradeMessage(ITCH41MarketMessage):
    type = b"P"
    description = "Trade Message"
    message_size = struct.calcsize("!IQcI8sIQ") + 1

    def __init__(self) -> None:
        """Initialize a TradeMessage."""
        super().__init__()
        self.order_ref: int = 0
        self.side: bytes = b""
        self.shares: int = 0
        self.stock: bytes = b""
        self.price: int = 0
        self.match_num: int = 0

    @classmethod
    def _from_bytes_data(cls, message_data: bytes) -> "TradeMessage":
        """Create a TradeMessage from bytes data."""
        message = cls()
        (
            timestamp,
            message.order_ref,
            message.side,
            message.shares,
            message.stock,
            message.price,
            message.match_num,
        ) = struct.unpack("!IQcI8sIQ", message_data[1:])
        message.timestamp = timestamp * 1_000_000_000  # Convert to nanoseconds
        return message

    def to_bytes(self) -> bytes:
        return struct.pack(
            "!cIQcI8sIQ",
            self.type,
            self.timestamp // 1_000_000_000,  # Convert to seconds
            self.order_ref,
            self.side,
            self.shares,
            self.stock,
            self.price,
            self.match_num,
        )

    def _add_json_fields(self, data: dict) -> None:
        """Add TradeMessage-specific fields to JSON data."""
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
                "match_num": self.match_num,
            }
        )

    @classmethod
    def _from_json_data(cls, data: dict) -> "TradeMessage":
        """Create a TradeMessage from JSON data."""
        message = cls()
        message.timestamp = data.get("timestamp", 0)
        message.order_ref = data.get("order_ref", 0)
        message.shares = data.get("shares", 0)
        message.price = data.get("price", 0)
        message.match_num = data.get("match_num", 0)
        side = data.get("side", " ")
        if isinstance(side, str):
            side = side.encode()
        message.side = side
        stock = data.get("stock", "")
        if isinstance(stock, str):
            stock = stock.ljust(8).encode()
        message.stock = stock
        return message


class CrossTradeMessage(ITCH41MarketMessage):
    type = b"Q"
    description = "Cross Trade Message"
    message_size = struct.calcsize("!IQ8sIQc") + 1

    def __init__(self) -> None:
        """Initialize a CrossTradeMessage."""
        super().__init__()
        self.shares: int = 0
        self.stock: bytes = b""
        self.price: int = 0
        self.match_num: int = 0
        self.cross_type: bytes = b""

    @classmethod
    def _from_bytes_data(cls, message_data: bytes) -> "CrossTradeMessage":
        """Create a CrossTradeMessage from bytes data."""
        message = cls()
        (
            timestamp,
            message.shares,
            message.stock,
            message.price,
            message.match_num,
            message.cross_type,
        ) = struct.unpack("!IQ8sIQc", message_data[1:])
        message.timestamp = timestamp * 1_000_000_000  # Convert to nanoseconds
        return message

    def to_bytes(self) -> bytes:
        return struct.pack(
            "!cIQ8sIQc",
            self.type,
            self.timestamp // 1_000_000_000,  # Convert to seconds
            self.shares,
            self.stock,
            self.price,
            self.match_num,
            self.cross_type,
        )

    def _add_json_fields(self, data: dict) -> None:
        """Add CrossTradeMessage-specific fields to JSON data."""
        data.update(
            {
                "shares": self.shares,
                "stock": self.stock.decode().rstrip()
                if isinstance(self.stock, bytes)
                else self.stock,
                "price": self.price,
                "match_num": self.match_num,
                "cross_type": self.cross_type.decode()
                if isinstance(self.cross_type, bytes)
                else self.cross_type,
            }
        )

    @classmethod
    def _from_json_data(cls, data: dict) -> "CrossTradeMessage":
        """Create a CrossTradeMessage from JSON data."""
        message = cls()
        message.timestamp = data.get("timestamp", 0)
        message.shares = data.get("shares", 0)
        message.price = data.get("price", 0)
        message.match_num = data.get("match_num", 0)
        stock = data.get("stock", "")
        if isinstance(stock, str):
            stock = stock.ljust(8).encode()
        message.stock = stock
        cross_type = data.get("cross_type", " ")
        if isinstance(cross_type, str):
            cross_type = cross_type.encode()
        message.cross_type = cross_type
        return message

    def validate(self) -> bool:
        """Validate all codes in this CrossTradeMessage."""
        return self.validate_code(self.cross_type, self.crossTradeTypes)


class BrokenTradeMessage(ITCH41MarketMessage):
    type = b"B"
    description = "Broken Trade Message"
    message_size = struct.calcsize("!IQ") + 1

    def __init__(self) -> None:
        """Initialize a BrokenTradeMessage."""
        super().__init__()
        self.match_num: int = 0

    @classmethod
    def _from_bytes_data(cls, message_data: bytes) -> "BrokenTradeMessage":
        """Create a BrokenTradeMessage from bytes data."""
        message = cls()
        (
            timestamp,
            message.match_num,
        ) = struct.unpack("!IQ", message_data[1:])
        message.timestamp = timestamp * 1_000_000_000  # Convert to nanoseconds
        return message

    def to_bytes(self) -> bytes:
        return struct.pack(
            "!cIQ",
            self.type,
            self.timestamp // 1_000_000_000,  # Convert to seconds
            self.match_num,
        )

    def _add_json_fields(self, data: dict) -> None:
        """Add BrokenTradeMessage-specific fields to JSON data."""
        data.update(
            {
                "match_num": self.match_num,
            }
        )

    @classmethod
    def _from_json_data(cls, data: dict) -> "BrokenTradeMessage":
        """Create a BrokenTradeMessage from JSON data."""
        message = cls()
        message.timestamp = data.get("timestamp", 0)
        message.match_num = data.get("match_num", 0)
        return message
