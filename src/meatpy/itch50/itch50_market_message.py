"""ITCH 5.0 market message types and parsing.

This module provides classes for parsing and representing ITCH 5.0 market data
messages. It includes all message types defined in the ITCH 5.0 specification,
from system events to order and trade messages.
"""

import json
import struct

from ..message_reader import MarketMessage


class ITCH50MarketMessage(MarketMessage):
    """A market message in ITCH 5.0 format.

    This is the base class for all ITCH 5.0 message types. It provides
    common functionality for timestamp handling and message formatting.

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
        b"V": "Investors' Exchange",
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
        b"C": "Creations and/or Redemptions Suspended for Exchange Traded Product",
        b"N": "Normal (Default): Issuer Is NOT Deficient, Delinquent, or Bankrupt",
        b" ": "Not available. Firms should refer to SIAC feeds for code if needed",
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

    interestDescriptions = {
        b"B": "RPI orders avail on buy side",
        b"S": "RPI orders avail on sell side",
        b"A": "RPI orders avail on both sides",
        b"N": "No RPI orders avail",
    }

    crossTypeDescriptions = {
        b"O": "NASDAQ Opening Cross",
        b"C": "NASDAQ Closing Cross",
        b"H": "Cross for IPO and Halted Securities",
        b"I": "NASDAQ Cross Network: Intraday Cross and Post-Close Cross",
    }

    def print_out(self, indent):
        """Print the message description with indentation.

        Args:
            indent: Indentation string for formatting
        """
        print(indent + self.description)

    def set_timestamp(self, ts1, ts2):
        """Set the timestamp from two 32-bit components.

        Args:
            ts1: High 32 bits of the timestamp
            ts2: Low 32 bits of the timestamp
        """
        self.timestamp = ts2 | (ts1 << 32)

    def split_timestamp(self):
        """Split the timestamp into two 32-bit components.

        Returns:
            tuple: (high_32_bits, low_32_bits)
        """
        ts1 = self.timestamp >> 32
        ts2 = self.timestamp - (ts1 << 32)
        return (ts1, ts2)

    def to_json(self) -> str:
        """Convert the message to a JSON string.

        Returns:
            JSON string representation of the message
        """
        data = {
            "type": self.type.decode() if isinstance(self.type, bytes) else self.type,
            "description": self.description,
            "timestamp": self.timestamp,
        }

        # Add message-specific fields
        self._add_json_fields(data)

        return json.dumps(data, indent=2)

    def to_bytes(self) -> bytes:
        """Convert the message to bytes.

        Returns:
            Bytes representation of the message
        """
        raise NotImplementedError(
            f"to_bytes not implemented for {self.__class__.__name__}"
        )

    def _add_json_fields(self, data: dict) -> None:
        """Add message-specific fields to the JSON data.

        This method should be overridden by subclasses to add their specific fields.

        Args:
            data: Dictionary to add fields to
        """
        pass

    @classmethod
    def validate_code(cls, code: bytes, code_dict: dict) -> bool:
        """Validate that a code exists in the given code dictionary.

        Args:
            code: The code to validate
            code_dict: Dictionary containing valid codes

        Returns:
            True if code is valid, False otherwise
        """
        return code in code_dict

    @classmethod
    def get_code_description(cls, code: bytes, code_dict: dict) -> str:
        """Get the description for a given code.

        Args:
            code: The code to look up
            code_dict: Dictionary containing codes and descriptions

        Returns:
            Description string, or 'Unknown' if code not found
        """
        return code_dict.get(code, "Unknown")

    @classmethod
    def validate_system_event_code(cls, code: bytes) -> bool:
        """Validate a system event code."""
        return cls.validate_code(code, cls.sysEventCodes)

    @classmethod
    def validate_market_code(cls, code: bytes) -> bool:
        """Validate a market code."""
        return cls.validate_code(code, cls.market)

    @classmethod
    def validate_financial_status_indicator(cls, code: bytes) -> bool:
        """Validate a financial status indicator."""
        return cls.validate_code(code, cls.finStatusbsindicators)

    @classmethod
    def validate_trading_state(cls, code: bytes) -> bool:
        """Validate a trading state code."""
        return cls.validate_code(code, cls.tradingStates)

    @classmethod
    def validate_market_maker_mode(cls, code: bytes) -> bool:
        """Validate a market maker mode code."""
        return cls.validate_code(code, cls.marketMakerModes)

    @classmethod
    def validate_market_participant_state(cls, code: bytes) -> bool:
        """Validate a market participant state code."""
        return cls.validate_code(code, cls.marketParticipantStates)

    @classmethod
    def validate_interest_description(cls, code: bytes) -> bool:
        """Validate an interest description code."""
        return cls.validate_code(code, cls.interestDescriptions)

    @classmethod
    def validate_cross_type(cls, code: bytes) -> bool:
        """Validate a cross type code."""
        return cls.validate_code(code, cls.crossTypeDescriptions)

    def validate(self) -> bool:
        """Validate all codes in this message.

        This method should be overridden by subclasses to validate their specific codes.

        Returns:
            True if all codes are valid, False otherwise
        """
        return True

    @classmethod
    def from_json(cls, json_str: str) -> "ITCH50MarketMessage":
        """Create a message from a JSON string.

        Args:
            json_str: JSON string representation of the message

        Returns:
            ITCH50MarketMessage instance

        Raises:
            ValueError: If the JSON is invalid or missing required fields
        """
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")

        if "type" not in data:
            raise ValueError("Missing 'type' field in JSON")

        # Create the appropriate message class based on type
        message_type = data["type"]
        if isinstance(message_type, str):
            message_type = message_type.encode()

        # Map message types to classes
        message_classes = {
            b"S": SystemEventMessage,
            b"R": StockDirectoryMessage,
            b"H": StockTradingActionMessage,
            b"Y": RegSHOMessage,
            b"L": MarketParticipantPositionMessage,
            b"V": MWCBDeclineLevelMessage,
            b"W": MWCBBreachMessage,
            b"K": IPOQuotingPeriodUpdateMessage,
            b"J": LULDAuctionCollarMessage,
            b"h": OperationalHaltMessage,
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
            b"N": RpiiMessage,
            b"O": DirectListingCapitalRaiseMessage,
        }

        if message_type not in message_classes:
            raise ValueError(f"Unknown message type: {message_type}")

        message_class = message_classes[message_type]
        return message_class._from_json_data(data)  # type: ignore

    @classmethod
    def from_bytes(cls, message_data: bytes) -> "ITCH50MarketMessage":
        """Create a message from raw bytes data.

        Args:
            message_data: Raw message bytes

        Returns:
            ITCH50MarketMessage instance

        Raises:
            ValueError: If message type is not recognized
        """
        if not message_data:
            raise ValueError("Empty message data")

        msgtype = message_data[0:1]

        # Map message types to classes
        message_classes = {
            b"S": SystemEventMessage,
            b"R": StockDirectoryMessage,
            b"H": StockTradingActionMessage,
            b"Y": RegSHOMessage,
            b"L": MarketParticipantPositionMessage,
            b"V": MWCBDeclineLevelMessage,
            b"W": MWCBBreachMessage,
            b"K": IPOQuotingPeriodUpdateMessage,
            b"J": LULDAuctionCollarMessage,
            b"h": OperationalHaltMessage,
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
            b"N": RpiiMessage,
            b"O": DirectListingCapitalRaiseMessage,
        }

        if msgtype not in message_classes:
            raise ValueError(
                f"Unknown message type: {msgtype.decode() if isinstance(msgtype, bytes) else msgtype}"
            )

        message_class = message_classes[msgtype]
        return message_class._from_bytes_data(message_data)  # type: ignore

    @classmethod
    def _from_bytes_data(cls, message_data: bytes) -> "ITCH50MarketMessage":
        """Create a message from bytes data.

        This method should be overridden by subclasses to handle their specific fields.

        Args:
            message_data: Raw message bytes

        Returns:
            ITCH50MarketMessage instance
        """
        raise NotImplementedError(
            f"_from_bytes_data not implemented for {cls.__name__}"
        )

    @classmethod
    def _from_json_data(cls, data: dict) -> "ITCH50MarketMessage":
        """Create a message from JSON data.

        This method should be overridden by subclasses to handle their specific fields.

        Args:
            data: Dictionary containing message data

        Returns:
            ITCH50MarketMessage instance
        """
        raise NotImplementedError(f"from_json not implemented for {cls.__name__}")


class SystemEventMessage(ITCH50MarketMessage):
    type = b"S"
    description = "System Event Message"
    message_size = struct.calcsize("!HHHIc") + 1

    def __init__(self) -> None:
        """Initialize a SystemEventMessage."""
        self.stock_locate: int = 0
        self.tracking_number: int = 0
        self.code: bytes = b""

    @classmethod
    def _from_bytes_data(cls, message_data: bytes) -> "SystemEventMessage":
        """Create a SystemEventMessage from bytes data."""
        message = cls()
        (message.stock_locate, message.tracking_number, ts1, ts2, message.code) = (
            struct.unpack("!HHHIc", message_data[1:])
        )
        message.set_timestamp(ts1, ts2)
        return message

    def to_bytes(self) -> bytes:
        (ts1, ts2) = self.split_timestamp()
        return struct.pack(
            "!cHHHIc",
            self.type,
            self.stock_locate,
            self.tracking_number,
            ts1,
            ts2,
            self.code,
        )

    def _add_json_fields(self, data: dict) -> None:
        """Add SystemEventMessage-specific fields to JSON data."""
        data.update(
            {
                "stock_locate": self.stock_locate,
                "tracking_number": self.tracking_number,
                "code": self.code.decode()
                if isinstance(self.code, bytes)
                else self.code,
            }
        )

    @classmethod
    def _from_json_data(cls, data: dict) -> "SystemEventMessage":
        """Create a SystemEventMessage from JSON data."""
        message = cls()

        # Set the fields from JSON data
        message.stock_locate = data.get("stock_locate", 0)
        message.tracking_number = data.get("tracking_number", 0)
        message.timestamp = data.get("timestamp", 0)

        code = data.get("code", " ")
        if isinstance(code, str):
            code = code.encode()
        message.code = code

        return message

    def validate(self) -> bool:
        """Validate all codes in this SystemEventMessage."""
        return self.validate_system_event_code(self.code)


class StockDirectoryMessage(ITCH50MarketMessage):
    type = b"R"
    description = "Stock Directory Message"
    message_size = struct.calcsize("!HHHI8sccIcc2scccccIc") + 1

    def __init__(self) -> None:
        self.stock_locate: int = 0
        self.tracking_number: int = 0
        self.stock: bytes = b""
        self.category: bytes = b""
        self.status: bytes = b""
        self.lotsize: int = 0
        self.lotsonly: bytes = b""
        self.issue_class: bytes = b""
        self.issue_sub: bytes = b""
        self.authenticity: bytes = b""
        self.shortsale_thresh: bytes = b""
        self.ipo_flag: bytes = b""
        self.luld_ref: bytes = b""
        self.etp_flag: bytes = b""
        self.etp_leverage: int = 0
        self.inverse_ind: bytes = b""

    @classmethod
    def _from_bytes_data(cls, message_data: bytes) -> "StockDirectoryMessage":
        message = cls()
        (
            message.stock_locate,
            message.tracking_number,
            ts1,
            ts2,
            message.stock,
            message.category,
            message.status,
            message.lotsize,
            message.lotsonly,
            message.issue_class,
            message.issue_sub,
            message.authenticity,
            message.shortsale_thresh,
            message.ipo_flag,
            message.luld_ref,
            message.etp_flag,
            message.etp_leverage,
            message.inverse_ind,
        ) = struct.unpack("!HHHI8sccIcc2scccccIc", message_data[1:])
        message.set_timestamp(ts1, ts2)
        return message

    def to_bytes(self) -> bytes:
        (ts1, ts2) = self.split_timestamp()
        return struct.pack(
            "!cHHHI8sccIcc2scccccIc",
            self.type,
            self.stock_locate,
            self.tracking_number,
            ts1,
            ts2,
            self.stock,
            self.category,
            self.status,
            self.lotsize,
            self.lotsonly,
            self.issue_class,
            self.issue_sub,
            self.authenticity,
            self.shortsale_thresh,
            self.ipo_flag,
            self.luld_ref,
            self.etp_flag,
            self.etp_leverage,
            self.inverse_ind,
        )

    def _add_json_fields(self, data: dict) -> None:
        """Add StockDirectoryMessage-specific fields to JSON data."""
        data.update(
            {
                "stock_locate": self.stock_locate,
                "tracking_number": self.tracking_number,
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
                "issue_class": self.issue_class.decode()
                if isinstance(self.issue_class, bytes)
                else self.issue_class,
                "issue_sub": self.issue_sub.decode()
                if isinstance(self.issue_sub, bytes)
                else self.issue_sub,
                "authenticity": self.authenticity.decode()
                if isinstance(self.authenticity, bytes)
                else self.authenticity,
                "shortsale_thresh": self.shortsale_thresh.decode()
                if isinstance(self.shortsale_thresh, bytes)
                else self.shortsale_thresh,
                "ipo_flag": self.ipo_flag.decode()
                if isinstance(self.ipo_flag, bytes)
                else self.ipo_flag,
                "luld_ref": self.luld_ref.decode()
                if isinstance(self.luld_ref, bytes)
                else self.luld_ref,
                "etp_flag": self.etp_flag.decode()
                if isinstance(self.etp_flag, bytes)
                else self.etp_flag,
                "etp_leverage": self.etp_leverage,
                "inverse_ind": self.inverse_ind.decode()
                if isinstance(self.inverse_ind, bytes)
                else self.inverse_ind,
            }
        )

    @classmethod
    def _from_json_data(cls, data: dict) -> "StockDirectoryMessage":
        message = cls()
        message.stock_locate = data.get("stock_locate", 0)
        message.tracking_number = data.get("tracking_number", 0)
        message.timestamp = data.get("timestamp", 0)
        for field_name in [
            "stock",
            "category",
            "status",
            "lotsonly",
            "issue_class",
            "issue_sub",
            "authenticity",
            "ipo_flag",
            "etp_flag",
            "inverse_ind",
        ]:
            value = data.get(
                field_name, b"" if field_name in ["stock", "issue_sub"] else " "
            )
            if isinstance(value, str):
                if field_name == "stock":
                    value = value.ljust(8).encode()
                elif field_name == "issue_sub":
                    value = value.ljust(2).encode()
                else:
                    value = value.encode()
            setattr(message, field_name, value)
        for field_name in ["lotsize", "etp_leverage"]:
            setattr(message, field_name, data.get(field_name, 0))
        for field_name in ["shortsale_thresh", "luld_ref"]:
            value = data.get(field_name, " ")
            if isinstance(value, str):
                value = value.encode()
            setattr(message, field_name, value)
        return message

    def validate(self) -> bool:
        """Validate all codes in this StockDirectoryMessage."""
        return (
            self.validate_market_code(self.category)
            and self.validate_financial_status_indicator(self.status)
            and self.validate_code(self.lotsonly, self.roundLotsOnly)
        )


class StockTradingActionMessage(ITCH50MarketMessage):
    type = b"H"
    description = "Stock Trading Message"
    message_size = struct.calcsize("!HHHI8scc4s") + 1

    def __init__(self) -> None:
        """Initialize a StockTradingActionMessage."""
        self.stock_locate: int = 0
        self.tracking_number: int = 0
        self.stock: bytes = b""
        self.state: bytes = b""
        self.reserved: bytes = b""
        self.reason: bytes = b""

    @classmethod
    def _from_bytes_data(cls, message_data: bytes) -> "StockTradingActionMessage":
        """Create a StockTradingActionMessage from bytes data."""
        message = cls()
        (
            message.stock_locate,
            message.tracking_number,
            ts1,
            ts2,
            message.stock,
            message.state,
            message.reserved,
            message.reason,
        ) = struct.unpack("!HHHI8scc4s", message_data[1:])
        message.set_timestamp(ts1, ts2)
        return message

    def to_bytes(self) -> bytes:
        (ts1, ts2) = self.split_timestamp()
        return struct.pack(
            "!cHHHI8scc4s",
            self.type,
            self.stock_locate,
            self.tracking_number,
            ts1,
            ts2,
            self.stock,
            self.state,
            self.reserved,
            self.reason,
        )

    def _add_json_fields(self, data: dict) -> None:
        """Add StockTradingActionMessage-specific fields to JSON data."""
        data.update(
            {
                "stock_locate": self.stock_locate,
                "tracking_number": self.tracking_number,
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

        # Set the fields from JSON data
        message.stock_locate = data.get("stock_locate", 0)
        message.tracking_number = data.get("tracking_number", 0)
        message.timestamp = data.get("timestamp", 0)

        # Handle string fields
        stock = data.get("stock", "")
        if isinstance(stock, str):
            stock = stock.ljust(8).encode()
        message.stock = stock

        for field_name in ["state", "reserved"]:
            value = data.get(field_name, " ")
            if isinstance(value, str):
                value = value.encode()
            setattr(message, field_name, value)

        reason = data.get("reason", "")
        if isinstance(reason, str):
            reason = reason.ljust(4).encode()
        message.reason = reason

        return message

    def validate(self) -> bool:
        """Validate all codes in this StockTradingActionMessage."""
        return self.validate_trading_state(self.state)


class RegSHOMessage(ITCH50MarketMessage):
    type = b"Y"
    description = "Reg SHO Short Sale Message"
    message_size = struct.calcsize("!HHHI8sc") + 1

    def __init__(self) -> None:
        """Initialize a RegSHOMessage."""
        self.stock_locate: int = 0
        self.tracking_number: int = 0
        self.stock: bytes = b""
        self.action: bytes = b""

    @classmethod
    def _from_bytes_data(cls, message_data: bytes) -> "RegSHOMessage":
        """Create a RegSHOMessage from bytes data."""
        message = cls()
        (
            message.stock_locate,
            message.tracking_number,
            ts1,
            ts2,
            message.stock,
            message.action,
        ) = struct.unpack("!HHHI8sc", message_data[1:])
        message.set_timestamp(ts1, ts2)
        return message

    def to_bytes(self) -> bytes:
        (ts1, ts2) = self.split_timestamp()
        return struct.pack(
            "!cHHHI8sc",
            self.type,
            self.stock_locate,
            self.tracking_number,
            ts1,
            ts2,
            self.stock,
            self.action,
        )

    def _add_json_fields(self, data: dict) -> None:
        """Add RegSHOMessage-specific fields to JSON data."""
        data.update(
            {
                "stock_locate": self.stock_locate,
                "tracking_number": self.tracking_number,
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

        # Set the fields from JSON data
        message.stock_locate = data.get("stock_locate", 0)
        message.tracking_number = data.get("tracking_number", 0)
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


class MarketParticipantPositionMessage(ITCH50MarketMessage):
    type = b"L"
    description = "Market Participant Message"
    message_size = struct.calcsize("!HHHI4s8sccc") + 1

    def __init__(self) -> None:
        """Initialize a MarketParticipantPositionMessage."""
        self.stock_locate: int = 0
        self.tracking_number: int = 0
        self.mpid: bytes = b""
        self.stock: bytes = b""
        self.primary_market_maker: bytes = b""
        self.market_maker_mode: bytes = b""
        self.state: bytes = b""

    @classmethod
    def _from_bytes_data(
        cls, message_data: bytes
    ) -> "MarketParticipantPositionMessage":
        """Create a MarketParticipantPositionMessage from bytes data."""
        message = cls()
        (
            message.stock_locate,
            message.tracking_number,
            ts1,
            ts2,
            message.mpid,
            message.stock,
            message.primary_market_maker,
            message.market_maker_mode,
            message.state,
        ) = struct.unpack("!HHHI4s8sccc", message_data[1:])
        message.set_timestamp(ts1, ts2)
        return message

    def to_bytes(self) -> bytes:
        (ts1, ts2) = self.split_timestamp()
        return struct.pack(
            "!cHHHI4s8sccc",
            self.type,
            self.stock_locate,
            self.tracking_number,
            ts1,
            ts2,
            self.mpid,
            self.stock,
            self.primary_market_maker,
            self.market_maker_mode,
            self.state,
        )

    def _add_json_fields(self, data: dict) -> None:
        """Add MarketParticipantPositionMessage-specific fields to JSON data."""
        data.update(
            {
                "stock_locate": self.stock_locate,
                "tracking_number": self.tracking_number,
                "mpid": self.mpid.decode().rstrip()
                if isinstance(self.mpid, bytes)
                else self.mpid,
                "stock": self.stock.decode().rstrip()
                if isinstance(self.stock, bytes)
                else self.stock,
                "primaryMarketMaker": self.primary_market_maker.decode()
                if isinstance(self.primary_market_maker, bytes)
                else self.primary_market_maker,
                "marketMakermode": self.market_maker_mode.decode()
                if isinstance(self.market_maker_mode, bytes)
                else self.market_maker_mode,
                "state": self.state.decode()
                if isinstance(self.state, bytes)
                else self.state,
            }
        )

    @classmethod
    def _from_json_data(cls, data: dict) -> "MarketParticipantPositionMessage":
        """Create a MarketParticipantPositionMessage from JSON data."""
        message = cls()

        # Set the fields from JSON data
        message.stock_locate = data.get("stock_locate", 0)
        message.tracking_number = data.get("tracking_number", 0)
        message.timestamp = data.get("timestamp", 0)

        # Handle string fields
        mpid = data.get("mpid", "")
        if isinstance(mpid, str):
            mpid = mpid.ljust(4).encode()
        message.mpid = mpid

        stock = data.get("stock", "")
        if isinstance(stock, str):
            stock = stock.ljust(8).encode()
        message.stock = stock

        for field_name in ["primaryMarketMaker", "marketMakermode", "state"]:
            value = data.get(field_name, " ")
            if isinstance(value, str):
                value = value.encode()
            if field_name == "primaryMarketMaker":
                message.primary_market_maker = value
            elif field_name == "marketMakermode":
                message.market_maker_mode = value
            else:
                message.state = value

        return message

    def validate(self) -> bool:
        """Validate all codes in this MarketParticipantPositionMessage."""
        return (
            self.validate_code(self.primary_market_maker, self.primaryMarketMaker)
            and self.validate_market_maker_mode(self.market_maker_mode)
            and self.validate_market_participant_state(self.state)
        )


class AddOrderMessage(ITCH50MarketMessage):
    type = b"A"
    description = "Add Order Message"
    message_size = struct.calcsize("!HHHIQcI8sI") + 1

    def __init__(self) -> None:
        self.stock_locate: int = 0
        self.tracking_number: int = 0
        self.order_ref: int = 0
        self.bsindicator: bytes = b""
        self.shares: int = 0
        self.stock: bytes = b""
        self.price: int = 0

    @classmethod
    def _from_bytes_data(cls, message_data: bytes) -> "AddOrderMessage":
        message = cls()
        (
            message.stock_locate,
            message.tracking_number,
            ts1,
            ts2,
            message.order_ref,
            message.bsindicator,
            message.shares,
            message.stock,
            message.price,
        ) = struct.unpack("!HHHIQcI8sI", message_data[1:])
        message.set_timestamp(ts1, ts2)
        return message

    def to_bytes(self) -> bytes:
        (ts1, ts2) = self.split_timestamp()
        return struct.pack(
            "!cHHHIQcI8sI",
            self.type,
            self.stock_locate,
            self.tracking_number,
            ts1,
            ts2,
            self.order_ref,
            self.bsindicator,
            self.shares,
            self.stock,
            self.price,
        )

    def _add_json_fields(self, data: dict) -> None:
        """Add AddOrderMessage-specific fields to JSON data."""
        data.update(
            {
                "stock_locate": self.stock_locate,
                "tracking_number": self.tracking_number,
                "orderRefNum": self.order_ref,
                "bsindicator": self.bsindicator.decode()
                if isinstance(self.bsindicator, bytes)
                else self.bsindicator,
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
        message.stock_locate = data.get("stock_locate", 0)
        message.tracking_number = data.get("tracking_number", 0)
        message.timestamp = data.get("timestamp", 0)
        message.order_ref = data.get("orderRefNum", 0)
        message.shares = data.get("shares", 0)
        message.price = data.get("price", 0)
        bsindicator = data.get("bsindicator", " ")
        if isinstance(bsindicator, str):
            bsindicator = bsindicator.encode()
        message.bsindicator = bsindicator
        stock = data.get("stock", "")
        if isinstance(stock, str):
            stock = stock.ljust(8).encode()
        message.stock = stock
        return message


class AddOrderMPIDMessage(ITCH50MarketMessage):
    type = b"F"
    description = "Add Order w/ MPID Message"
    message_size = struct.calcsize("!HHHIQcI8sI4s") + 1

    def __init__(self) -> None:
        """Initialize an AddOrderMPIDMessage."""
        self.stock_locate: int = 0
        self.tracking_number: int = 0
        self.order_ref: int = 0
        self.bsindicator: bytes = b""
        self.shares: int = 0
        self.stock: bytes = b""
        self.price: int = 0
        self.attribution: bytes = b""

    @classmethod
    def _from_bytes_data(cls, message_data: bytes) -> "AddOrderMPIDMessage":
        """Create an AddOrderMPIDMessage from bytes data."""
        message = cls()
        (
            message.stock_locate,
            message.tracking_number,
            ts1,
            ts2,
            message.order_ref,
            message.bsindicator,
            message.shares,
            message.stock,
            message.price,
            message.attribution,
        ) = struct.unpack("!HHHIQcI8sI4s", message_data[1:])
        message.set_timestamp(ts1, ts2)
        return message

    def to_bytes(self) -> bytes:
        (ts1, ts2) = self.split_timestamp()
        return struct.pack(
            "!cHHHIQcI8sI4s",
            self.type,
            self.stock_locate,
            self.tracking_number,
            ts1,
            ts2,
            self.order_ref,
            self.bsindicator,
            self.shares,
            self.stock,
            self.price,
            self.attribution,
        )

    def _add_json_fields(self, data: dict) -> None:
        """Add AddOrderMPIDMessage-specific fields to JSON data."""
        data.update(
            {
                "stock_locate": self.stock_locate,
                "tracking_number": self.tracking_number,
                "orderRefNum": self.order_ref,
                "bsindicator": self.bsindicator.decode()
                if isinstance(self.bsindicator, bytes)
                else self.bsindicator,
                "shares": self.shares,
                "stock": self.stock.decode().rstrip()
                if isinstance(self.stock, bytes)
                else self.stock,
                "price": self.price,
                "attribution": self.attribution.decode().rstrip()
                if isinstance(self.attribution, bytes)
                else self.attribution,
            }
        )

    @classmethod
    def _from_json_data(cls, data: dict) -> "AddOrderMPIDMessage":
        """Create an AddOrderMPIDMessage from JSON data."""
        message = cls()

        # Set the fields from JSON data
        message.stock_locate = data.get("stock_locate", 0)
        message.tracking_number = data.get("tracking_number", 0)
        message.timestamp = data.get("timestamp", 0)
        message.order_ref = data.get("orderRefNum", 0)
        message.shares = data.get("shares", 0)
        message.price = data.get("price", 0)

        # Handle string fields
        bsindicator = data.get("bsindicator", " ")
        if isinstance(bsindicator, str):
            bsindicator = bsindicator.encode()
        message.bsindicator = bsindicator

        stock = data.get("stock", "")
        if isinstance(stock, str):
            stock = stock.ljust(8).encode()
        message.stock = stock

        attribution = data.get("attribution", "")
        if isinstance(attribution, str):
            attribution = attribution.ljust(4).encode()
        message.attribution = attribution

        return message


class OrderExecutedMessage(ITCH50MarketMessage):
    type = b"E"
    description = "Order Executed Message"
    message_size = struct.calcsize("!HHHIQIQ") + 1

    def __init__(self) -> None:
        """Initialize an OrderExecutedMessage."""
        self.stock_locate: int = 0
        self.tracking_number: int = 0
        self.order_ref: int = 0
        self.shares: int = 0
        self.match: int = 0

    @classmethod
    def _from_bytes_data(cls, message_data: bytes) -> "OrderExecutedMessage":
        """Create an OrderExecutedMessage from bytes data."""
        message = cls()
        (
            message.stock_locate,
            message.tracking_number,
            ts1,
            ts2,
            message.order_ref,
            message.shares,
            message.match,
        ) = struct.unpack("!HHHIQIQ", message_data[1:])
        message.set_timestamp(ts1, ts2)
        return message

    def to_bytes(self) -> bytes:
        (ts1, ts2) = self.split_timestamp()
        return struct.pack(
            "!cHHHIQIQ",
            self.type,
            self.stock_locate,
            self.tracking_number,
            ts1,
            ts2,
            self.order_ref,
            self.shares,
            self.match,
        )

    def _add_json_fields(self, data: dict) -> None:
        """Add OrderExecutedMessage-specific fields to JSON data."""
        data.update(
            {
                "stock_locate": self.stock_locate,
                "tracking_number": self.tracking_number,
                "orderRefNum": self.order_ref,
                "executedShares": self.shares,
                "matchNumber": self.match,
            }
        )

    @classmethod
    def _from_json_data(cls, data: dict) -> "OrderExecutedMessage":
        """Create an OrderExecutedMessage from JSON data."""
        message = cls()

        # Set the fields from JSON data
        message.stock_locate = data.get("stock_locate", 0)
        message.tracking_number = data.get("tracking_number", 0)
        message.timestamp = data.get("timestamp", 0)
        message.order_ref = data.get("orderRefNum", 0)
        message.shares = data.get("executedShares", 0)
        message.match = data.get("matchNumber", 0)

        return message


class OrderExecutedPriceMessage(ITCH50MarketMessage):
    type = b"C"
    description = "Order Executed w/ Price Message"
    message_size = struct.calcsize("!HHHIQIQcI") + 1

    def __init__(self) -> None:
        """Initialize an OrderExecutedPriceMessage."""
        self.stock_locate: int = 0
        self.tracking_number: int = 0
        self.order_ref: int = 0
        self.shares: int = 0
        self.match: int = 0
        self.printable: bytes = b""
        self.execution_price: int = 0

    @classmethod
    def _from_bytes_data(cls, message_data: bytes) -> "OrderExecutedPriceMessage":
        """Create an OrderExecutedPriceMessage from bytes data."""
        message = cls()
        (
            message.stock_locate,
            message.tracking_number,
            ts1,
            ts2,
            message.order_ref,
            message.shares,
            message.match,
            message.printable,
            message.execution_price,
        ) = struct.unpack("!HHHIQIQcI", message_data[1:])
        message.set_timestamp(ts1, ts2)
        return message

    def to_bytes(self) -> bytes:
        (ts1, ts2) = self.split_timestamp()
        return struct.pack(
            "!cHHHIQIQcI",
            self.type,
            self.stock_locate,
            self.tracking_number,
            ts1,
            ts2,
            self.order_ref,
            self.shares,
            self.match,
            self.printable,
            self.execution_price,
        )

    def _add_json_fields(self, data: dict) -> None:
        """Add OrderExecutedPriceMessage-specific fields to JSON data."""
        data.update(
            {
                "stock_locate": self.stock_locate,
                "tracking_number": self.tracking_number,
                "orderRefNum": self.order_ref,
                "executedShares": self.shares,
                "matchNumber": self.match,
                "printable": self.printable.decode()
                if isinstance(self.printable, bytes)
                else self.printable,
                "executionPrice": self.execution_price,
            }
        )

    @classmethod
    def _from_json_data(cls, data: dict) -> "OrderExecutedPriceMessage":
        """Create an OrderExecutedPriceMessage from JSON data."""
        message = cls()

        # Set the fields from JSON data
        message.stock_locate = data.get("stock_locate", 0)
        message.tracking_number = data.get("tracking_number", 0)
        message.timestamp = data.get("timestamp", 0)
        message.order_ref = data.get("orderRefNum", 0)
        message.shares = data.get("executedShares", 0)
        message.match = data.get("matchNumber", 0)
        message.execution_price = data.get("executionPrice", 0)

        printable = data.get("printable", " ")
        if isinstance(printable, str):
            printable = printable.encode()
        message.printable = printable

        return message


class OrderCancelMessage(ITCH50MarketMessage):
    type = b"X"
    description = "Order Cancel Message"
    message_size = struct.calcsize("!HHHIQI") + 1

    def __init__(self) -> None:
        """Initialize an OrderCancelMessage."""
        self.stock_locate: int = 0
        self.tracking_number: int = 0
        self.order_ref: int = 0
        self.canceled_shares: int = 0

    @classmethod
    def _from_bytes_data(cls, message_data: bytes) -> "OrderCancelMessage":
        """Create an OrderCancelMessage from bytes data."""
        message = cls()
        (
            message.stock_locate,
            message.tracking_number,
            ts1,
            ts2,
            message.order_ref,
            message.canceled_shares,
        ) = struct.unpack("!HHHIQI", message_data[1:])
        message.set_timestamp(ts1, ts2)
        return message

    def to_bytes(self) -> bytes:
        (ts1, ts2) = self.split_timestamp()
        return struct.pack(
            "!cHHHIQI",
            self.type,
            self.stock_locate,
            self.tracking_number,
            ts1,
            ts2,
            self.order_ref,
            self.canceled_shares,
        )

    def _add_json_fields(self, data: dict) -> None:
        """Add OrderCancelMessage-specific fields to JSON data."""
        data.update(
            {
                "stock_locate": self.stock_locate,
                "tracking_number": self.tracking_number,
                "orderRefNum": self.order_ref,
                "canceledShares": self.canceled_shares,
            }
        )

    @classmethod
    def _from_json_data(cls, data: dict) -> "OrderCancelMessage":
        """Create an OrderCancelMessage from JSON data."""
        message = cls()

        # Set the fields from JSON data
        message.stock_locate = data.get("stock_locate", 0)
        message.tracking_number = data.get("tracking_number", 0)
        message.timestamp = data.get("timestamp", 0)
        message.order_ref = data.get("orderRefNum", 0)
        message.canceled_shares = data.get("canceledShares", 0)

        return message


class OrderDeleteMessage(ITCH50MarketMessage):
    type = b"D"
    description = "Order Delete Message"
    message_size = struct.calcsize("!HHHIQ") + 1

    def __init__(self) -> None:
        """Initialize an OrderDeleteMessage."""
        self.stock_locate: int = 0
        self.tracking_number: int = 0
        self.order_ref: int = 0

    @classmethod
    def _from_bytes_data(cls, message_data: bytes) -> "OrderDeleteMessage":
        """Create an OrderDeleteMessage from bytes data."""
        message = cls()
        (
            message.stock_locate,
            message.tracking_number,
            ts1,
            ts2,
            message.order_ref,
        ) = struct.unpack("!HHHIQ", message_data[1:])
        message.set_timestamp(ts1, ts2)
        return message

    def to_bytes(self) -> bytes:
        (ts1, ts2) = self.split_timestamp()
        return struct.pack(
            "!cHHHIQ",
            self.type,
            self.stock_locate,
            self.tracking_number,
            ts1,
            ts2,
            self.order_ref,
        )

    def _add_json_fields(self, data: dict) -> None:
        """Add OrderDeleteMessage-specific fields to JSON data."""
        data.update(
            {
                "stock_locate": self.stock_locate,
                "tracking_number": self.tracking_number,
                "orderRefNum": self.order_ref,
            }
        )

    @classmethod
    def _from_json_data(cls, data: dict) -> "OrderDeleteMessage":
        """Create an OrderDeleteMessage from JSON data."""
        message = cls()

        # Set the fields from JSON data
        message.stock_locate = data.get("stock_locate", 0)
        message.tracking_number = data.get("tracking_number", 0)
        message.timestamp = data.get("timestamp", 0)
        message.order_ref = data.get("orderRefNum", 0)

        return message


class OrderReplaceMessage(ITCH50MarketMessage):
    type = b"U"
    description = "Order Replaced Message"
    message_size = struct.calcsize("!HHHIQQII") + 1

    def __init__(self) -> None:
        self.stock_locate: int = 0
        self.tracking_number: int = 0
        self.original_ref: int = 0
        self.new_ref: int = 0
        self.shares: int = 0
        self.price: int = 0

    @classmethod
    def _from_bytes_data(cls, message_data: bytes) -> "OrderReplaceMessage":
        message = cls()
        (
            message.stock_locate,
            message.tracking_number,
            ts1,
            ts2,
            message.original_ref,
            message.new_ref,
            message.shares,
            message.price,
        ) = struct.unpack("!HHHIQQII", message_data[1:])
        message.set_timestamp(ts1, ts2)
        return message

    def to_bytes(self) -> bytes:
        (ts1, ts2) = self.split_timestamp()
        return struct.pack(
            "!cHHHIQQII",
            self.type,
            self.stock_locate,
            self.tracking_number,
            ts1,
            ts2,
            self.original_ref,
            self.new_ref,
            self.shares,
            self.price,
        )

    def _add_json_fields(self, data: dict) -> None:
        """Add OrderReplaceMessage-specific fields to JSON data."""
        data.update(
            {
                "stock_locate": self.stock_locate,
                "tracking_number": self.tracking_number,
                "originalOrderRefNum": self.original_ref,
                "newOrderRefNum": self.new_ref,
                "shares": self.shares,
                "price": self.price,
            }
        )

    @classmethod
    def _from_json_data(cls, data: dict) -> "OrderReplaceMessage":
        """Create an OrderReplaceMessage from JSON data."""
        message = cls()

        # Set the fields from JSON data
        message.stock_locate = data.get("stock_locate", 0)
        message.tracking_number = data.get("tracking_number", 0)
        message.timestamp = data.get("timestamp", 0)
        message.original_ref = data.get("originalOrderRefNum", 0)
        message.new_ref = data.get("newOrderRefNum", 0)
        message.shares = data.get("shares", 0)
        message.price = data.get("price", 0)

        return message


class TradeMessage(ITCH50MarketMessage):
    type = b"P"
    description = "Trade Message"
    message_size = struct.calcsize("!HHHIQcI8sIQ") + 1

    def __init__(self) -> None:
        self.stock_locate: int = 0
        self.tracking_number: int = 0
        self.order_ref: int = 0
        self.bsindicator: bytes = b""
        self.shares: int = 0
        self.stock: bytes = b""
        self.price: int = 0
        self.match: int = 0

    @classmethod
    def _from_bytes_data(cls, message_data: bytes) -> "TradeMessage":
        message = cls()
        (
            message.stock_locate,
            message.tracking_number,
            ts1,
            ts2,
            message.order_ref,
            message.bsindicator,
            message.shares,
            message.stock,
            message.price,
            message.match,
        ) = struct.unpack("!HHHIQcI8sIQ", message_data[1:])
        message.set_timestamp(ts1, ts2)
        return message

    def to_bytes(self) -> bytes:
        (ts1, ts2) = self.split_timestamp()
        return struct.pack(
            "!cHHHIQcI8sIQ",
            self.type,
            self.stock_locate,
            self.tracking_number,
            ts1,
            ts2,
            self.order_ref,
            self.bsindicator,
            self.shares,
            self.stock,
            self.price,
            self.match,
        )

    def _add_json_fields(self, data: dict) -> None:
        """Add TradeMessage-specific fields to JSON data."""
        data.update(
            {
                "stock_locate": self.stock_locate,
                "tracking_number": self.tracking_number,
                "orderRefNum": self.order_ref,
                "bsindicator": self.bsindicator.decode()
                if isinstance(self.bsindicator, bytes)
                else self.bsindicator,
                "shares": self.shares,
                "stock": self.stock.decode().rstrip()
                if isinstance(self.stock, bytes)
                else self.stock,
                "price": self.price,
                "matchNumber": self.match,
            }
        )

    @classmethod
    def _from_json_data(cls, data: dict) -> "TradeMessage":
        message = cls()
        message.stock_locate = data.get("stock_locate", 0)
        message.tracking_number = data.get("tracking_number", 0)
        message.timestamp = data.get("timestamp", 0)
        message.order_ref = data.get("orderRefNum", 0)
        message.shares = data.get("shares", 0)
        message.price = data.get("price", 0)
        message.match = data.get("matchNumber", 0)
        bsindicator = data.get("bsindicator", " ")
        if isinstance(bsindicator, str):
            bsindicator = bsindicator.encode()
        message.bsindicator = bsindicator
        stock = data.get("stock", "")
        if isinstance(stock, str):
            stock = stock.ljust(8).encode()
        message.stock = stock
        return message


class CrossTradeMessage(ITCH50MarketMessage):
    type = b"Q"
    description = "Cross Trade Message"
    message_size = struct.calcsize("!HHHIQ8sIQc") + 1

    def __init__(self) -> None:
        """Initialize a CrossTradeMessage."""
        self.stock_locate: int = 0
        self.tracking_number: int = 0
        self.shares: int = 0
        self.stock: bytes = b""
        self.cross_price: int = 0
        self.match: int = 0
        self.cross_type: bytes = b""

    @classmethod
    def _from_bytes_data(cls, message_data: bytes) -> "CrossTradeMessage":
        """Create a CrossTradeMessage from bytes data."""
        message = cls()
        (
            message.stock_locate,
            message.tracking_number,
            ts1,
            ts2,
            message.shares,
            message.stock,
            message.cross_price,
            message.match,
            message.cross_type,
        ) = struct.unpack("!HHHIQ8sIQc", message_data[1:])
        message.set_timestamp(ts1, ts2)
        return message

    def to_bytes(self) -> bytes:
        (ts1, ts2) = self.split_timestamp()
        return struct.pack(
            "!cHHHIQ8sIQc",
            self.type,
            self.stock_locate,
            self.tracking_number,
            ts1,
            ts2,
            self.shares,
            self.stock,
            self.cross_price,
            self.match,
            self.cross_type,
        )

    def _add_json_fields(self, data: dict) -> None:
        """Add CrossTradeMessage-specific fields to JSON data."""
        data.update(
            {
                "stock_locate": self.stock_locate,
                "tracking_number": self.tracking_number,
                "shares": self.shares,
                "stock": self.stock.decode().rstrip()
                if isinstance(self.stock, bytes)
                else self.stock,
                "crossPrice": self.cross_price,
                "matchNumber": self.match,
                "crossType": self.cross_type.decode()
                if isinstance(self.cross_type, bytes)
                else self.cross_type,
            }
        )

    @classmethod
    def _from_json_data(cls, data: dict) -> "CrossTradeMessage":
        """Create a CrossTradeMessage from JSON data."""
        message = cls()

        # Set the fields from JSON data
        message.stock_locate = data.get("stock_locate", 0)
        message.tracking_number = data.get("tracking_number", 0)
        message.timestamp = data.get("timestamp", 0)
        message.shares = data.get("shares", 0)
        message.cross_price = data.get("crossPrice", 0)
        message.match = data.get("matchNumber", 0)

        # Handle string fields
        stock = data.get("stock", "")
        if isinstance(stock, str):
            stock = stock.ljust(8).encode()
        message.stock = stock

        crossType = data.get("crossType", " ")
        if isinstance(crossType, str):
            crossType = crossType.encode()
        message.cross_type = crossType

        return message

    def validate(self) -> bool:
        """Validate all codes in this CrossTradeMessage."""
        return self.validate_cross_type(self.cross_type)


class BrokenTradeMessage(ITCH50MarketMessage):
    type = b"B"
    description = "Broken Trade Message"
    message_size = struct.calcsize("!HHHIQ") + 1

    def __init__(self) -> None:
        self.stock_locate: int = 0
        self.tracking_number: int = 0
        self.match: int = 0

    @classmethod
    def _from_bytes_data(cls, message_data: bytes) -> "BrokenTradeMessage":
        message = cls()
        (
            message.stock_locate,
            message.tracking_number,
            ts1,
            ts2,
            message.match,
        ) = struct.unpack("!HHHIQ", message_data[1:])
        message.set_timestamp(ts1, ts2)
        return message

    def to_bytes(self) -> bytes:
        (ts1, ts2) = self.split_timestamp()
        return struct.pack(
            "!cHHHIQ",
            self.type,
            self.stock_locate,
            self.tracking_number,
            ts1,
            ts2,
            self.match,
        )

    def _add_json_fields(self, data: dict) -> None:
        """Add BrokenTradeMessage-specific fields to JSON data."""
        data.update(
            {
                "stock_locate": self.stock_locate,
                "tracking_number": self.tracking_number,
                "matchNumber": self.match,
            }
        )

    @classmethod
    def _from_json_data(cls, data: dict) -> "BrokenTradeMessage":
        """Create a BrokenTradeMessage from JSON data."""
        message = cls()

        # Set the fields from JSON data
        message.stock_locate = data.get("stock_locate", 0)
        message.tracking_number = data.get("tracking_number", 0)
        message.timestamp = data.get("timestamp", 0)
        message.match = data.get("matchNumber", 0)

        return message


class NoiiMessage(ITCH50MarketMessage):
    type = b"I"
    description = "NOII Message"
    message_size = struct.calcsize("!HHHIQQc8sIIIcc") + 1

    def __init__(self) -> None:
        """Initialize a NoiiMessage."""
        self.stock_locate: int = 0
        self.tracking_number: int = 0
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
            message.stock_locate,
            message.tracking_number,
            ts1,
            ts2,
            message.paired_shares,
            message.imbalance_shares,
            message.imbalance_direction,
            message.stock,
            message.far_price,
            message.near_price,
            message.current_ref_price,
            message.cross_type,
            message.price_variation_indicator,
        ) = struct.unpack("!HHHIQQc8sIIIcc", message_data[1:])
        message.set_timestamp(ts1, ts2)
        return message

    def to_bytes(self) -> bytes:
        (ts1, ts2) = self.split_timestamp()
        return struct.pack(
            "!cHHHIQQc8sIIIcc",
            self.type,
            self.stock_locate,
            self.tracking_number,
            ts1,
            ts2,
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
        """Add NoiiMessage-specific fields to JSON data."""
        data.update(
            {
                "stock_locate": self.stock_locate,
                "tracking_number": self.tracking_number,
                "pairedShares": self.paired_shares,
                "imbalanceShares": self.imbalance_shares,
                "imbalanceDirection": self.imbalance_direction.decode()
                if isinstance(self.imbalance_direction, bytes)
                else self.imbalance_direction,
                "stock": self.stock.decode().rstrip()
                if isinstance(self.stock, bytes)
                else self.stock,
                "farPrice": self.far_price,
                "nearPrice": self.near_price,
                "currentReferencePrice": self.current_ref_price,
                "crossType": self.cross_type.decode()
                if isinstance(self.cross_type, bytes)
                else self.cross_type,
                "priceVariationIndicator": self.price_variation_indicator.decode()
                if isinstance(self.price_variation_indicator, bytes)
                else self.price_variation_indicator,
            }
        )

    @classmethod
    def _from_json_data(cls, data: dict) -> "NoiiMessage":
        """Create a NoiiMessage from JSON data."""
        message = cls()

        # Set the fields from JSON data
        message.stock_locate = data.get("stock_locate", 0)
        message.tracking_number = data.get("tracking_number", 0)
        message.timestamp = data.get("timestamp", 0)
        message.paired_shares = data.get("pairedShares", 0)
        message.imbalance_shares = data.get("imbalanceShares", 0)
        message.far_price = data.get("farPrice", 0)
        message.near_price = data.get("nearPrice", 0)
        message.current_ref_price = data.get("currentReferencePrice", 0)

        # Handle string fields
        for field_name in [
            "imbalanceDirection",
            "crossType",
            "priceVariationIndicator",
        ]:
            value = data.get(field_name, " ")
            if isinstance(value, str):
                value = value.encode()
            setattr(message, field_name, value)

        stock = data.get("stock", "")
        if isinstance(stock, str):
            stock = stock.ljust(8).encode()
        message.stock = stock

        return message

    def validate(self) -> bool:
        """Validate all codes in this NoiiMessage."""
        return self.validate_cross_type(self.cross_type)


class RpiiMessage(ITCH50MarketMessage):
    type = b"N"
    description = "Retail Price Improvement Message"
    message_size = struct.calcsize("!HHHI8sc") + 1

    def __init__(self) -> None:
        """Initialize a RpiiMessage."""
        self.stock_locate: int = 0
        self.tracking_number: int = 0
        self.stock: bytes = b""
        self.interest: bytes = b""

    @classmethod
    def _from_bytes_data(cls, message_data: bytes) -> "RpiiMessage":
        """Create a RpiiMessage from bytes data."""
        message = cls()
        (
            message.stock_locate,
            message.tracking_number,
            ts1,
            ts2,
            message.stock,
            message.interest,
        ) = struct.unpack("!HHHI8sc", message_data[1:])
        message.set_timestamp(ts1, ts2)
        return message

    def to_bytes(self) -> bytes:
        (ts1, ts2) = self.split_timestamp()
        return struct.pack(
            "!cHHHI8sc",
            self.type,
            self.stock_locate,
            self.tracking_number,
            ts1,
            ts2,
            self.stock,
            self.interest,
        )

    def _add_json_fields(self, data: dict) -> None:
        """Add RpiiMessage-specific fields to JSON data."""
        data.update(
            {
                "stock_locate": self.stock_locate,
                "tracking_number": self.tracking_number,
                "stock": self.stock.decode().rstrip()
                if isinstance(self.stock, bytes)
                else self.stock,
                "interest": self.interest.decode()
                if isinstance(self.interest, bytes)
                else self.interest,
            }
        )

    @classmethod
    def _from_json_data(cls, data: dict) -> "RpiiMessage":
        """Create a RpiiMessage from JSON data."""
        message = cls()

        # Set the fields from JSON data
        message.stock_locate = data.get("stock_locate", 0)
        message.tracking_number = data.get("tracking_number", 0)
        message.timestamp = data.get("timestamp", 0)

        stock = data.get("stock", "")
        if isinstance(stock, str):
            stock = stock.ljust(8).encode()
        message.stock = stock

        interest = data.get("interest", " ")
        if isinstance(interest, str):
            interest = interest.encode()
        message.interest = interest

        return message

    def validate(self) -> bool:
        """Validate all codes in this RpiiMessage."""
        return self.validate_interest_description(self.interest)


class MWCBDeclineLevelMessage(ITCH50MarketMessage):
    type = b"V"
    description = "MWCB Decline Level Message"
    message_size = struct.calcsize("!HHHIQQQ") + 1

    def __init__(self) -> None:
        """Initialize a MWCBDeclineLevelMessage."""
        self.stock_locate: int = 0
        self.tracking_number: int = 0
        self.level1: int = 0
        self.level2: int = 0
        self.level3: int = 0

    @classmethod
    def _from_bytes_data(cls, message_data: bytes) -> "MWCBDeclineLevelMessage":
        """Create a MWCBDeclineLevelMessage from bytes data."""
        message = cls()
        (
            message.stock_locate,
            message.tracking_number,
            ts1,
            ts2,
            message.level1,
            message.level2,
            message.level3,
        ) = struct.unpack("!HHHIQQQ", message_data[1:])
        message.set_timestamp(ts1, ts2)
        return message

    def to_bytes(self) -> bytes:
        (ts1, ts2) = self.split_timestamp()
        return struct.pack(
            "!cHHHIQQQ",
            self.type,
            self.stock_locate,
            self.tracking_number,
            ts1,
            ts2,
            self.level1,
            self.level2,
            self.level3,
        )

    def _add_json_fields(self, data: dict) -> None:
        """Add MWCBDeclineLevelMessage-specific fields to JSON data."""
        data.update(
            {
                "stock_locate": self.stock_locate,
                "tracking_number": self.tracking_number,
                "level1": self.level1,
                "level2": self.level2,
                "level3": self.level3,
            }
        )

    @classmethod
    def _from_json_data(cls, data: dict) -> "MWCBDeclineLevelMessage":
        """Create a MWCBDeclineLevelMessage from JSON data."""
        message = cls()

        # Set the fields from JSON data
        message.stock_locate = data.get("stock_locate", 0)
        message.tracking_number = data.get("tracking_number", 0)
        message.timestamp = data.get("timestamp", 0)
        message.level1 = data.get("level1", 0)
        message.level2 = data.get("level2", 0)
        message.level3 = data.get("level3", 0)

        return message


class MWCBBreachMessage(ITCH50MarketMessage):
    type = b"W"
    description = "MWCB Breach Message"
    message_size = struct.calcsize("!HHHIc") + 1

    def __init__(self) -> None:
        """Initialize a MWCBBreachMessage."""
        self.stock_locate: int = 0
        self.tracking_number: int = 0
        self.breached_level: bytes = b""

    @classmethod
    def _from_bytes_data(cls, message_data: bytes) -> "MWCBBreachMessage":
        """Create a MWCBBreachMessage from bytes data."""
        message = cls()
        (
            message.stock_locate,
            message.tracking_number,
            ts1,
            ts2,
            message.breached_level,
        ) = struct.unpack("!HHHIc", message_data[1:])
        message.set_timestamp(ts1, ts2)
        return message

    def to_bytes(self) -> bytes:
        (ts1, ts2) = self.split_timestamp()
        return struct.pack(
            "!cHHHIc",
            self.type,
            self.stock_locate,
            self.tracking_number,
            ts1,
            ts2,
            self.breached_level,
        )

    def _add_json_fields(self, data: dict) -> None:
        """Add MWCBBreachMessage-specific fields to JSON data."""
        data.update(
            {
                "stock_locate": self.stock_locate,
                "tracking_number": self.tracking_number,
                "breachedLevel": self.breached_level.decode()
                if isinstance(self.breached_level, bytes)
                else self.breached_level,
            }
        )

    @classmethod
    def _from_json_data(cls, data: dict) -> "MWCBBreachMessage":
        """Create a MWCBBreachMessage from JSON data."""
        message = cls()

        # Set the fields from JSON data
        message.stock_locate = data.get("stock_locate", 0)
        message.tracking_number = data.get("tracking_number", 0)
        message.timestamp = data.get("timestamp", 0)

        breachedLevel = data.get("breachedLevel", " ")
        if isinstance(breachedLevel, str):
            breachedLevel = breachedLevel.encode()
        message.breached_level = breachedLevel

        return message


class IPOQuotingPeriodUpdateMessage(ITCH50MarketMessage):
    type = b"K"
    description = "IPO Quoting Period Update Message"
    message_size = struct.calcsize("!HHHI8sIcI") + 1

    def __init__(self) -> None:
        """Initialize an IPOQuotingPeriodUpdateMessage."""
        self.stock_locate: int = 0
        self.tracking_number: int = 0
        self.stock: bytes = b""
        self.ipo_quotation_release_time: int = 0
        self.ipo_quotation_release_qualifier: bytes = b""
        self.ipo_price: int = 0

    @classmethod
    def _from_bytes_data(cls, message_data: bytes) -> "IPOQuotingPeriodUpdateMessage":
        """Create an IPOQuotingPeriodUpdateMessage from bytes data."""
        message = cls()
        (
            message.stock_locate,
            message.tracking_number,
            ts1,
            ts2,
            message.stock,
            message.ipo_quotation_release_time,
            message.ipo_quotation_release_qualifier,
            message.ipo_price,
        ) = struct.unpack("!HHHI8sIcI", message_data[1:])
        message.set_timestamp(ts1, ts2)
        return message

    def to_bytes(self) -> bytes:
        (ts1, ts2) = self.split_timestamp()
        return struct.pack(
            "!cHHHI8sIcI",
            self.type,
            self.stock_locate,
            self.tracking_number,
            ts1,
            ts2,
            self.stock,
            self.ipo_quotation_release_time,
            self.ipo_quotation_release_qualifier,
            self.ipo_price,
        )

    def _add_json_fields(self, data: dict) -> None:
        """Add IPOQuotingPeriodUpdateMessage-specific fields to JSON data."""
        data.update(
            {
                "stock_locate": self.stock_locate,
                "tracking_number": self.tracking_number,
                "stock": self.stock.decode().rstrip()
                if isinstance(self.stock, bytes)
                else self.stock,
                "ipoQuotationReleaseTime": self.ipo_quotation_release_time,
                "ipoQuotationReleaseQualifier": self.ipo_quotation_release_qualifier.decode()
                if isinstance(self.ipo_quotation_release_qualifier, bytes)
                else self.ipo_quotation_release_qualifier,
                "ipoPrice": self.ipo_price,
            }
        )

    @classmethod
    def _from_json_data(cls, data: dict) -> "IPOQuotingPeriodUpdateMessage":
        """Create an IPOQuotingPeriodUpdateMessage from JSON data."""
        message = cls()

        # Set the fields from JSON data
        message.stock_locate = data.get("stock_locate", 0)
        message.tracking_number = data.get("tracking_number", 0)
        message.timestamp = data.get("timestamp", 0)
        message.ipo_quotation_release_time = data.get("ipoQuotationReleaseTime", 0)
        message.ipo_price = data.get("ipoPrice", 0)

        stock = data.get("stock", "")
        if isinstance(stock, str):
            stock = stock.ljust(8).encode()
        message.stock = stock

        ipoQuotationReleaseQualifier = data.get("ipoQuotationReleaseQualifier", " ")
        if isinstance(ipoQuotationReleaseQualifier, str):
            ipoQuotationReleaseQualifier = ipoQuotationReleaseQualifier.encode()
        message.ipo_quotation_release_qualifier = ipoQuotationReleaseQualifier

        return message


class LULDAuctionCollarMessage(ITCH50MarketMessage):
    type = b"J"
    description = "LULD Auction Collar Message"
    message_size = struct.calcsize("!HHHI8sIIII") + 1

    def __init__(self) -> None:
        """Initialize a LULDAuctionCollarMessage."""
        self.stock_locate: int = 0
        self.tracking_number: int = 0
        self.stock: bytes = b""
        self.auction_collar_ref_price: int = 0
        self.upper_auction_collar_price: int = 0
        self.lower_auction_collar_price: int = 0
        self.auction_collar_extension: int = 0

    @classmethod
    def _from_bytes_data(cls, message_data: bytes) -> "LULDAuctionCollarMessage":
        """Create a LULDAuctionCollarMessage from bytes data."""
        message = cls()
        (
            message.stock_locate,
            message.tracking_number,
            ts1,
            ts2,
            message.stock,
            message.auction_collar_ref_price,
            message.upper_auction_collar_price,
            message.lower_auction_collar_price,
            message.auction_collar_extension,
        ) = struct.unpack("!HHHI8sIIII", message_data[1:])
        message.set_timestamp(ts1, ts2)
        return message

    def to_bytes(self) -> bytes:
        (ts1, ts2) = self.split_timestamp()
        return struct.pack(
            "!cHHHI8sIIII",
            self.type,
            self.stock_locate,
            self.tracking_number,
            ts1,
            ts2,
            self.stock,
            self.auction_collar_ref_price,
            self.upper_auction_collar_price,
            self.lower_auction_collar_price,
            self.auction_collar_extension,
        )

    def _add_json_fields(self, data: dict) -> None:
        """Add LULDAuctionCollarMessage-specific fields to JSON data."""
        data.update(
            {
                "stock_locate": self.stock_locate,
                "tracking_number": self.tracking_number,
                "stock": self.stock.decode().rstrip()
                if isinstance(self.stock, bytes)
                else self.stock,
                "auctionCollarReferencePrice": self.auction_collar_ref_price,
                "upperAuctionCollarPrice": self.upper_auction_collar_price,
                "lowerAuctionCollarPrice": self.lower_auction_collar_price,
                "auctionCollarExtension": self.auction_collar_extension,
            }
        )

    @classmethod
    def _from_json_data(cls, data: dict) -> "LULDAuctionCollarMessage":
        """Create a LULDAuctionCollarMessage from JSON data."""
        message = cls()

        # Set the fields from JSON data
        message.stock_locate = data.get("stock_locate", 0)
        message.tracking_number = data.get("tracking_number", 0)
        message.timestamp = data.get("timestamp", 0)
        message.auction_collar_ref_price = data.get("auctionCollarReferencePrice", 0)
        message.upper_auction_collar_price = data.get("upperAuctionCollarPrice", 0)
        message.lower_auction_collar_price = data.get("lowerAuctionCollarPrice", 0)
        message.auction_collar_extension = data.get("auctionCollarExtension", 0)

        stock = data.get("stock", "")
        if isinstance(stock, str):
            stock = stock.ljust(8).encode()
        message.stock = stock

        return message


class OperationalHaltMessage(ITCH50MarketMessage):
    type = b"h"
    description = "Operational Halt Message"
    message_size = struct.calcsize("!HHHI8scc") + 1

    def __init__(self) -> None:
        """Initialize an OperationalHaltMessage."""
        self.stock_locate: int = 0
        self.tracking_number: int = 0
        self.stock: bytes = b""
        self.halt_status: bytes = b""
        self.halt_reason: bytes = b""

    @classmethod
    def _from_bytes_data(cls, message_data: bytes) -> "OperationalHaltMessage":
        """Create an OperationalHaltMessage from bytes data."""
        message = cls()
        (
            message.stock_locate,
            message.tracking_number,
            ts1,
            ts2,
            message.stock,
            message.halt_status,
            message.halt_reason,
        ) = struct.unpack("!HHHI8scc", message_data[1:])
        message.set_timestamp(ts1, ts2)
        return message

    def to_bytes(self) -> bytes:
        (ts1, ts2) = self.split_timestamp()
        return struct.pack(
            "!cHHHI8scc",
            self.type,
            self.stock_locate,
            self.tracking_number,
            ts1,
            ts2,
            self.stock,
            self.halt_status,
            self.halt_reason,
        )

    def _add_json_fields(self, data: dict) -> None:
        """Add OperationalHaltMessage-specific fields to JSON data."""
        data.update(
            {
                "stock_locate": self.stock_locate,
                "tracking_number": self.tracking_number,
                "stock": self.stock.decode().rstrip()
                if isinstance(self.stock, bytes)
                else self.stock,
                "haltStatus": self.halt_status.decode()
                if isinstance(self.halt_status, bytes)
                else self.halt_status,
                "haltReason": self.halt_reason.decode()
                if isinstance(self.halt_reason, bytes)
                else self.halt_reason,
            }
        )

    @classmethod
    def _from_json_data(cls, data: dict) -> "OperationalHaltMessage":
        """Create an OperationalHaltMessage from JSON data."""
        message = cls()

        # Set the fields from JSON data
        message.stock_locate = data.get("stock_locate", 0)
        message.tracking_number = data.get("tracking_number", 0)
        message.timestamp = data.get("timestamp", 0)

        stock = data.get("stock", "")
        if isinstance(stock, str):
            stock = stock.ljust(8).encode()
        message.stock = stock

        for field_name in ["haltStatus", "haltReason"]:
            value = data.get(field_name, " ")
            if isinstance(value, str):
                value = value.encode()
            setattr(message, field_name, value)

        return message


class DirectListingCapitalRaiseMessage(ITCH50MarketMessage):
    type = b"O"
    description = "Direct Listing with Capital Raise (DLCR) Message"
    message_size = struct.calcsize("!HHHI8scIIIIQII") + 1  # +1 for message type byte

    def __init__(self) -> None:
        """Initialize a DirectListingCapitalRaiseMessage."""
        self.stock_locate: int = 0
        self.tracking_number: int = 0
        self.stock: bytes = b""
        self.dlcr_event_type: bytes = b""
        self.ref_price: int = 0
        self.upper_price_limit: int = 0
        self.lower_price_limit: int = 0
        self.max_price_variation: int = 0
        self.quantity: int = 0
        self.quantity_limit: int = 0
        self.quantity_limit_type: int = 0

    @classmethod
    def _from_bytes_data(
        cls, message_data: bytes
    ) -> "DirectListingCapitalRaiseMessage":
        """Create a DirectListingCapitalRaiseMessage from bytes data."""
        message = cls()
        (
            message.stock_locate,
            message.tracking_number,
            ts1,
            ts2,
            message.stock,
            message.dlcr_event_type,
            message.ref_price,
            message.upper_price_limit,
            message.lower_price_limit,
            message.max_price_variation,
            message.quantity,
            message.quantity_limit,
            message.quantity_limit_type,
        ) = struct.unpack("!HHHI8scIIIIQII", message_data[1:])
        message.set_timestamp(ts1, ts2)
        return message

    def to_bytes(self) -> bytes:
        (ts1, ts2) = self.split_timestamp()
        return struct.pack(
            "!cHHHI8scIIIIQII",
            self.type,
            self.stock_locate,
            self.tracking_number,
            ts1,
            ts2,
            self.stock,
            self.dlcr_event_type,
            self.ref_price,
            self.upper_price_limit,
            self.lower_price_limit,
            self.max_price_variation,
            self.quantity,
            self.quantity_limit,
            self.quantity_limit_type,
        )

    def _add_json_fields(self, data: dict) -> None:
        """Add DirectListingCapitalRaiseMessage-specific fields to JSON data."""
        data.update(
            {
                "stock_locate": self.stock_locate,
                "tracking_number": self.tracking_number,
                "stock": self.stock.decode().rstrip()
                if isinstance(self.stock, bytes)
                else self.stock,
                "dlcrEventType": self.dlcr_event_type.decode()
                if isinstance(self.dlcr_event_type, bytes)
                else self.dlcr_event_type,
                "referencePrice": self.ref_price,
                "upperPriceLimit": self.upper_price_limit,
                "lowerPriceLimit": self.lower_price_limit,
                "maxPriceVariation": self.max_price_variation,
                "quantity": self.quantity,
                "quantityLimit": self.quantity_limit,
                "quantityLimitType": self.quantity_limit_type,
            }
        )

    @classmethod
    def _from_json_data(cls, data: dict) -> "DirectListingCapitalRaiseMessage":
        """Create a DirectListingCapitalRaiseMessage from JSON data."""
        message = cls()

        # Set the fields from JSON data
        message.stock_locate = data.get("stock_locate", 0)
        message.tracking_number = data.get("tracking_number", 0)
        message.timestamp = data.get("timestamp", 0)
        message.ref_price = data.get("referencePrice", 0)
        message.upper_price_limit = data.get("upperPriceLimit", 0)
        message.lower_price_limit = data.get("lowerPriceLimit", 0)
        message.max_price_variation = data.get("maxPriceVariation", 0)
        message.quantity = data.get("quantity", 0)
        message.quantity_limit = data.get("quantityLimit", 0)
        message.quantity_limit_type = data.get("quantityLimitType", 0)

        stock = data.get("stock", "")
        if isinstance(stock, str):
            stock = stock.ljust(8).encode()
        message.stock = stock

        dlcrEventType = data.get("dlcrEventType", " ")
        if isinstance(dlcrEventType, str):
            dlcrEventType = dlcrEventType.encode()
        message.dlcr_event_type = dlcrEventType

        return message
