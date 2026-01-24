"""IEX DEEP market message types.

This module provides message classes for IEX DEEP format market data.
All messages use little endian byte order and timestamps are nanoseconds
since POSIX (Epoch) time UTC.
"""

from __future__ import annotations

import abc
import json
import struct
from typing import Any

from ..message_reader import MarketMessage, UnknownMessageTypeError


class IEXDEEPMarketMessage(MarketMessage):
    """Base class for IEX DEEP market messages.

    All IEX DEEP messages share common characteristics:
    - Little endian byte order
    - Timestamps in nanoseconds since POSIX epoch UTC
    - Message type as first byte
    """

    __metaclass__ = abc.ABCMeta

    # Message type byte for this message class
    message_type: bytes = b""

    # Expected message length (excluding message type byte)
    message_length: int = 0

    def __init__(self, timestamp: int) -> None:
        """Initialize the message with a timestamp.

        Args:
            timestamp: Nanoseconds since POSIX epoch UTC
        """
        self.timestamp = timestamp

    @classmethod
    def from_bytes(cls, data: bytes) -> "IEXDEEPMarketMessage":
        """Parse a message from bytes.

        Args:
            data: Raw message bytes (including message type byte)

        Returns:
            Parsed message object

        Raises:
            UnknownMessageTypeError: If message type is not recognized
        """
        if len(data) < 1:
            raise ValueError("Message data is empty")

        message_type = data[0:1]

        # Map message types to classes
        message_classes: dict[bytes, type[IEXDEEPMarketMessage]] = {
            b"S": SystemEventMessage,
            b"D": SecurityDirectoryMessage,
            b"H": TradingStatusMessage,
            b"O": OperationalHaltStatusMessage,
            b"P": ShortSalePriceTestStatusMessage,
            b"E": SecurityEventMessage,
            b"8": PriceLevelUpdateBuySideMessage,
            b"5": PriceLevelUpdateSellSideMessage,
            b"T": TradeReportMessage,
            b"X": OfficialPriceMessage,
            b"B": TradeBreakMessage,
            b"A": AuctionInformationMessage,
        }

        if message_type not in message_classes:
            raise UnknownMessageTypeError(
                f"Unknown IEX DEEP message type: {message_type!r}"
            )

        return message_classes[message_type]._from_bytes(data)

    @classmethod
    @abc.abstractmethod
    def _from_bytes(cls, data: bytes) -> "IEXDEEPMarketMessage":
        """Internal method to parse message from bytes.

        Args:
            data: Raw message bytes

        Returns:
            Parsed message object
        """
        pass

    @abc.abstractmethod
    def to_bytes(self) -> bytes:
        """Serialize message to bytes.

        Returns:
            Raw message bytes
        """
        pass

    def to_json(self) -> str:
        """Serialize message to JSON string.

        Returns:
            JSON string representation
        """
        d: dict[str, Any] = {
            "message_type": self.message_type.decode("ascii"),
            "timestamp": self.timestamp,
        }
        self._add_json_fields(d)
        return json.dumps(d)

    def _add_json_fields(self, d: dict[str, Any]) -> None:
        """Add message-specific fields to JSON dict.

        Args:
            d: Dictionary to add fields to
        """
        pass


class SystemEventMessage(IEXDEEPMarketMessage):
    """System Event Message (S, 0x53).

    Used to indicate events that apply to the market or data feed.
    Total message length: 10 bytes.

    System Events:
    - 'O' (0x4f): Start of Messages
    - 'S' (0x53): Start of System Hours
    - 'R' (0x52): Start of Regular Market Hours
    - 'M' (0x4d): End of Regular Market Hours
    - 'E' (0x45): End of System Hours
    - 'C' (0x43): End of Messages
    """

    message_type = b"S"
    message_length = 10

    def __init__(self, system_event: bytes, timestamp: int) -> None:
        super().__init__(timestamp)
        self.system_event = system_event

    @classmethod
    def _from_bytes(cls, data: bytes) -> "SystemEventMessage":
        # Format: message_type(1) + system_event(1) + timestamp(8)
        # Little endian: <
        system_event, timestamp = struct.unpack("<xbq", data[:10])
        return cls(
            system_event=bytes([system_event]),
            timestamp=timestamp,
        )

    def to_bytes(self) -> bytes:
        return struct.pack(
            "<cbq",
            self.message_type,
            self.system_event[0],
            self.timestamp,
        )

    def _add_json_fields(self, d: dict[str, Any]) -> None:
        d["system_event"] = self.system_event.decode("ascii")


class SecurityDirectoryMessage(IEXDEEPMarketMessage):
    """Security Directory Message (D, 0x44).

    Provides security information for IEX-listed securities.
    Total message length: 31 bytes.
    """

    message_type = b"D"
    message_length = 31

    def __init__(
        self,
        flags: int,
        timestamp: int,
        symbol: bytes,
        round_lot_size: int,
        adjusted_poc_price: int,
        luld_tier: int,
    ) -> None:
        super().__init__(timestamp)
        self.flags = flags
        self.symbol = symbol
        self.round_lot_size = round_lot_size
        self.adjusted_poc_price = adjusted_poc_price
        self.luld_tier = luld_tier

    @classmethod
    def _from_bytes(cls, data: bytes) -> "SecurityDirectoryMessage":
        # Format: type(1) + flags(1) + timestamp(8) + symbol(8) + round_lot(4) + poc_price(8) + luld(1)
        flags, timestamp, symbol, round_lot_size, adjusted_poc_price, luld_tier = (
            struct.unpack("<xBq8sIqB", data[:31])
        )
        return cls(
            flags=flags,
            timestamp=timestamp,
            symbol=symbol,
            round_lot_size=round_lot_size,
            adjusted_poc_price=adjusted_poc_price,
            luld_tier=luld_tier,
        )

    def to_bytes(self) -> bytes:
        return struct.pack(
            "<cBq8sIqB",
            self.message_type,
            self.flags,
            self.timestamp,
            self.symbol,
            self.round_lot_size,
            self.adjusted_poc_price,
            self.luld_tier,
        )

    def _add_json_fields(self, d: dict[str, Any]) -> None:
        d["flags"] = self.flags
        d["symbol"] = self.symbol.decode("ascii").strip()
        d["round_lot_size"] = self.round_lot_size
        d["adjusted_poc_price"] = self.adjusted_poc_price / 10000.0
        d["luld_tier"] = self.luld_tier

    @property
    def is_test_security(self) -> bool:
        """Check if this is a test security (bit 7)."""
        return bool(self.flags & 0x80)

    @property
    def is_when_issued(self) -> bool:
        """Check if this is a when issued security (bit 6)."""
        return bool(self.flags & 0x40)

    @property
    def is_etp(self) -> bool:
        """Check if this is an ETP (bit 5)."""
        return bool(self.flags & 0x20)


class TradingStatusMessage(IEXDEEPMarketMessage):
    """Trading Status Message (H, 0x48).

    Indicates current trading status of a security.
    Total message length: 22 bytes.

    Trading Status:
    - 'H' (0x48): Trading halted
    - 'O' (0x4f): Order Acceptance Period
    - 'P' (0x50): Trading Paused
    - 'T' (0x54): Trading on IEX
    """

    message_type = b"H"
    message_length = 22

    def __init__(
        self,
        trading_status: bytes,
        timestamp: int,
        symbol: bytes,
        reason: bytes,
    ) -> None:
        super().__init__(timestamp)
        self.trading_status = trading_status
        self.symbol = symbol
        self.reason = reason

    @classmethod
    def _from_bytes(cls, data: bytes) -> "TradingStatusMessage":
        # Format: type(1) + status(1) + timestamp(8) + symbol(8) + reason(4)
        trading_status, timestamp, symbol, reason = struct.unpack("<xbq8s4s", data[:22])
        return cls(
            trading_status=bytes([trading_status]),
            timestamp=timestamp,
            symbol=symbol,
            reason=reason,
        )

    def to_bytes(self) -> bytes:
        return struct.pack(
            "<cbq8s4s",
            self.message_type,
            self.trading_status[0],
            self.timestamp,
            self.symbol,
            self.reason,
        )

    def _add_json_fields(self, d: dict[str, Any]) -> None:
        d["trading_status"] = self.trading_status.decode("ascii")
        d["symbol"] = self.symbol.decode("ascii").strip()
        d["reason"] = self.reason.decode("ascii").strip()


class OperationalHaltStatusMessage(IEXDEEPMarketMessage):
    """Operational Halt Status Message (O, 0x4f).

    Indicates operational halt status for a security.
    Total message length: 18 bytes.

    Operational Halt Status:
    - 'O' (0x4f): IEX specific operational halt
    - 'N' (0x4e): Not operationally halted on IEX
    """

    message_type = b"O"
    message_length = 18

    def __init__(
        self,
        operational_halt_status: bytes,
        timestamp: int,
        symbol: bytes,
    ) -> None:
        super().__init__(timestamp)
        self.operational_halt_status = operational_halt_status
        self.symbol = symbol

    @classmethod
    def _from_bytes(cls, data: bytes) -> "OperationalHaltStatusMessage":
        # Format: type(1) + status(1) + timestamp(8) + symbol(8)
        status, timestamp, symbol = struct.unpack("<xbq8s", data[:18])
        return cls(
            operational_halt_status=bytes([status]),
            timestamp=timestamp,
            symbol=symbol,
        )

    def to_bytes(self) -> bytes:
        return struct.pack(
            "<cbq8s",
            self.message_type,
            self.operational_halt_status[0],
            self.timestamp,
            self.symbol,
        )

    def _add_json_fields(self, d: dict[str, Any]) -> None:
        d["operational_halt_status"] = self.operational_halt_status.decode("ascii")
        d["symbol"] = self.symbol.decode("ascii").strip()


class ShortSalePriceTestStatusMessage(IEXDEEPMarketMessage):
    """Short Sale Price Test Status Message (P, 0x50).

    Indicates Reg SHO short sale price test restriction status.
    Total message length: 19 bytes.

    Status:
    - 0 (0x0): Short Sale Price Test Not in Effect
    - 1 (0x1): Short Sale Price Test in Effect

    Detail:
    - ' ' (0x20): No price test in place
    - 'A' (0x41): Activated
    - 'C' (0x43): Continued
    - 'D' (0x44): Deactivated
    - 'N' (0x4e): Detail Not Available
    """

    message_type = b"P"
    message_length = 19

    def __init__(
        self,
        short_sale_price_test_status: int,
        timestamp: int,
        symbol: bytes,
        detail: bytes,
    ) -> None:
        super().__init__(timestamp)
        self.short_sale_price_test_status = short_sale_price_test_status
        self.symbol = symbol
        self.detail = detail

    @classmethod
    def _from_bytes(cls, data: bytes) -> "ShortSalePriceTestStatusMessage":
        # Format: type(1) + status(1) + timestamp(8) + symbol(8) + detail(1)
        status, timestamp, symbol, detail = struct.unpack("<xBq8sb", data[:19])
        return cls(
            short_sale_price_test_status=status,
            timestamp=timestamp,
            symbol=symbol,
            detail=bytes([detail]),
        )

    def to_bytes(self) -> bytes:
        return struct.pack(
            "<cBq8sb",
            self.message_type,
            self.short_sale_price_test_status,
            self.timestamp,
            self.symbol,
            self.detail[0],
        )

    def _add_json_fields(self, d: dict[str, Any]) -> None:
        d["short_sale_price_test_status"] = self.short_sale_price_test_status
        d["symbol"] = self.symbol.decode("ascii").strip()
        d["detail"] = self.detail.decode("ascii")


class SecurityEventMessage(IEXDEEPMarketMessage):
    """Security Event Message (E, 0x45).

    Indicates events that apply to a security.
    Total message length: 18 bytes.

    Security Events:
    - 'O' (0x4f): Opening Process Complete
    - 'C' (0x43): Closing Process Complete
    """

    message_type = b"E"
    message_length = 18

    def __init__(
        self,
        security_event: bytes,
        timestamp: int,
        symbol: bytes,
    ) -> None:
        super().__init__(timestamp)
        self.security_event = security_event
        self.symbol = symbol

    @classmethod
    def _from_bytes(cls, data: bytes) -> "SecurityEventMessage":
        # Format: type(1) + event(1) + timestamp(8) + symbol(8)
        event, timestamp, symbol = struct.unpack("<xbq8s", data[:18])
        return cls(
            security_event=bytes([event]),
            timestamp=timestamp,
            symbol=symbol,
        )

    def to_bytes(self) -> bytes:
        return struct.pack(
            "<cbq8s",
            self.message_type,
            self.security_event[0],
            self.timestamp,
            self.symbol,
        )

    def _add_json_fields(self, d: dict[str, Any]) -> None:
        d["security_event"] = self.security_event.decode("ascii")
        d["symbol"] = self.symbol.decode("ascii").strip()


class PriceLevelUpdateMessage(IEXDEEPMarketMessage):
    """Base class for Price Level Update Messages.

    Price level updates provide aggregated size at a price level.
    Total message length: 30 bytes.

    Event Flags:
    - 0 (0x0): Order Book is processing (in transition)
    - 1 (0x1): Event processing complete
    """

    message_length = 30

    def __init__(
        self,
        event_flags: int,
        timestamp: int,
        symbol: bytes,
        size: int,
        price: int,
    ) -> None:
        super().__init__(timestamp)
        self.event_flags = event_flags
        self.symbol = symbol
        self.size = size
        self.price = price

    @classmethod
    def _from_bytes(cls, data: bytes) -> "PriceLevelUpdateMessage":
        # Format: type(1) + flags(1) + timestamp(8) + symbol(8) + size(4) + price(8)
        event_flags, timestamp, symbol, size, price = struct.unpack(
            "<xBq8sIq", data[:30]
        )
        return cls(
            event_flags=event_flags,
            timestamp=timestamp,
            symbol=symbol,
            size=size,
            price=price,
        )

    def to_bytes(self) -> bytes:
        return struct.pack(
            "<cBq8sIq",
            self.message_type,
            self.event_flags,
            self.timestamp,
            self.symbol,
            self.size,
            self.price,
        )

    def _add_json_fields(self, d: dict[str, Any]) -> None:
        d["event_flags"] = self.event_flags
        d["symbol"] = self.symbol.decode("ascii").strip()
        d["size"] = self.size
        d["price"] = self.price / 10000.0

    @property
    def is_event_complete(self) -> bool:
        """Check if this update completes an atomic event."""
        return self.event_flags == 1


class PriceLevelUpdateBuySideMessage(PriceLevelUpdateMessage):
    """Price Level Update on the Buy Side (8, 0x38)."""

    message_type = b"8"


class PriceLevelUpdateSellSideMessage(PriceLevelUpdateMessage):
    """Price Level Update on the Sell Side (5, 0x35)."""

    message_type = b"5"


class TradeReportMessage(IEXDEEPMarketMessage):
    """Trade Report Message (T, 0x54).

    Sent when an order on IEX is executed.
    Total message length: 38 bytes.

    Sale Condition Flags (bits):
    - Bit 7: Intermarket Sweep (ISO)
    - Bit 6: Extended Hours (Form T)
    - Bit 5: Odd Lot
    - Bit 4: Trade Through Exempt
    - Bit 3: Single-price Cross Trade
    """

    message_type = b"T"
    message_length = 38

    def __init__(
        self,
        sale_condition_flags: int,
        timestamp: int,
        symbol: bytes,
        size: int,
        price: int,
        trade_id: int,
    ) -> None:
        super().__init__(timestamp)
        self.sale_condition_flags = sale_condition_flags
        self.symbol = symbol
        self.size = size
        self.price = price
        self.trade_id = trade_id

    @classmethod
    def _from_bytes(cls, data: bytes) -> "TradeReportMessage":
        # Format: type(1) + flags(1) + timestamp(8) + symbol(8) + size(4) + price(8) + trade_id(8)
        flags, timestamp, symbol, size, price, trade_id = struct.unpack(
            "<xBq8sIqq", data[:38]
        )
        return cls(
            sale_condition_flags=flags,
            timestamp=timestamp,
            symbol=symbol,
            size=size,
            price=price,
            trade_id=trade_id,
        )

    def to_bytes(self) -> bytes:
        return struct.pack(
            "<cBq8sIqq",
            self.message_type,
            self.sale_condition_flags,
            self.timestamp,
            self.symbol,
            self.size,
            self.price,
            self.trade_id,
        )

    def _add_json_fields(self, d: dict[str, Any]) -> None:
        d["sale_condition_flags"] = self.sale_condition_flags
        d["symbol"] = self.symbol.decode("ascii").strip()
        d["size"] = self.size
        d["price"] = self.price / 10000.0
        d["trade_id"] = self.trade_id

    @property
    def is_intermarket_sweep(self) -> bool:
        """Check if trade resulted from an ISO."""
        return bool(self.sale_condition_flags & 0x80)

    @property
    def is_extended_hours(self) -> bool:
        """Check if trade occurred outside regular market session."""
        return bool(self.sale_condition_flags & 0x40)

    @property
    def is_odd_lot(self) -> bool:
        """Check if trade is less than one round lot."""
        return bool(self.sale_condition_flags & 0x20)

    @property
    def is_trade_through_exempt(self) -> bool:
        """Check if trade is exempt from Rule 611."""
        return bool(self.sale_condition_flags & 0x10)

    @property
    def is_single_price_cross(self) -> bool:
        """Check if trade resulted from a single-price cross."""
        return bool(self.sale_condition_flags & 0x08)


class OfficialPriceMessage(IEXDEEPMarketMessage):
    """Official Price Message (X, 0x58).

    Indicates IEX Official Opening or Closing Price.
    Total message length: 26 bytes.

    Price Type:
    - 'Q' (0x51): IEX Official Opening Price
    - 'M' (0x4d): IEX Official Closing Price
    """

    message_type = b"X"
    message_length = 26

    def __init__(
        self,
        price_type: bytes,
        timestamp: int,
        symbol: bytes,
        official_price: int,
    ) -> None:
        super().__init__(timestamp)
        self.price_type = price_type
        self.symbol = symbol
        self.official_price = official_price

    @classmethod
    def _from_bytes(cls, data: bytes) -> "OfficialPriceMessage":
        # Format: type(1) + price_type(1) + timestamp(8) + symbol(8) + price(8)
        price_type, timestamp, symbol, price = struct.unpack("<xbq8sq", data[:26])
        return cls(
            price_type=bytes([price_type]),
            timestamp=timestamp,
            symbol=symbol,
            official_price=price,
        )

    def to_bytes(self) -> bytes:
        return struct.pack(
            "<cbq8sq",
            self.message_type,
            self.price_type[0],
            self.timestamp,
            self.symbol,
            self.official_price,
        )

    def _add_json_fields(self, d: dict[str, Any]) -> None:
        d["price_type"] = self.price_type.decode("ascii")
        d["symbol"] = self.symbol.decode("ascii").strip()
        d["official_price"] = self.official_price / 10000.0


class TradeBreakMessage(IEXDEEPMarketMessage):
    """Trade Break Message (B, 0x42).

    Sent when an execution on IEX is broken.
    Total message length: 38 bytes.
    """

    message_type = b"B"
    message_length = 38

    def __init__(
        self,
        sale_condition_flags: int,
        timestamp: int,
        symbol: bytes,
        size: int,
        price: int,
        trade_id: int,
    ) -> None:
        super().__init__(timestamp)
        self.sale_condition_flags = sale_condition_flags
        self.symbol = symbol
        self.size = size
        self.price = price
        self.trade_id = trade_id

    @classmethod
    def _from_bytes(cls, data: bytes) -> "TradeBreakMessage":
        # Format: type(1) + flags(1) + timestamp(8) + symbol(8) + size(4) + price(8) + trade_id(8)
        flags, timestamp, symbol, size, price, trade_id = struct.unpack(
            "<xBq8sIqq", data[:38]
        )
        return cls(
            sale_condition_flags=flags,
            timestamp=timestamp,
            symbol=symbol,
            size=size,
            price=price,
            trade_id=trade_id,
        )

    def to_bytes(self) -> bytes:
        return struct.pack(
            "<cBq8sIqq",
            self.message_type,
            self.sale_condition_flags,
            self.timestamp,
            self.symbol,
            self.size,
            self.price,
            self.trade_id,
        )

    def _add_json_fields(self, d: dict[str, Any]) -> None:
        d["sale_condition_flags"] = self.sale_condition_flags
        d["symbol"] = self.symbol.decode("ascii").strip()
        d["size"] = self.size
        d["price"] = self.price / 10000.0
        d["trade_id"] = self.trade_id


class AuctionInformationMessage(IEXDEEPMarketMessage):
    """Auction Information Message (A, 0x41).

    Provides auction information for IEX-listed securities.
    Total message length: 80 bytes.

    Auction Type:
    - 'O' (0x4f): Opening Auction
    - 'C' (0x43): Closing Auction
    - 'I' (0x49): IPO Auction
    - 'H' (0x48): Halt Auction
    - 'V' (0x56): Volatility Auction

    Imbalance Side:
    - 'B' (0x42): Buy-side imbalance
    - 'S' (0x53): Sell-side imbalance
    - 'N' (0x4e): No imbalance
    """

    message_type = b"A"
    message_length = 80

    def __init__(
        self,
        auction_type: bytes,
        timestamp: int,
        symbol: bytes,
        paired_shares: int,
        reference_price: int,
        indicative_clearing_price: int,
        imbalance_shares: int,
        imbalance_side: bytes,
        extension_number: int,
        scheduled_auction_time: int,
        auction_book_clearing_price: int,
        collar_reference_price: int,
        lower_auction_collar: int,
        upper_auction_collar: int,
    ) -> None:
        super().__init__(timestamp)
        self.auction_type = auction_type
        self.symbol = symbol
        self.paired_shares = paired_shares
        self.reference_price = reference_price
        self.indicative_clearing_price = indicative_clearing_price
        self.imbalance_shares = imbalance_shares
        self.imbalance_side = imbalance_side
        self.extension_number = extension_number
        self.scheduled_auction_time = scheduled_auction_time
        self.auction_book_clearing_price = auction_book_clearing_price
        self.collar_reference_price = collar_reference_price
        self.lower_auction_collar = lower_auction_collar
        self.upper_auction_collar = upper_auction_collar

    @classmethod
    def _from_bytes(cls, data: bytes) -> "AuctionInformationMessage":
        # Format: type(1) + auction_type(1) + timestamp(8) + symbol(8) +
        #         paired_shares(4) + reference_price(8) + indicative_clearing_price(8) +
        #         imbalance_shares(4) + imbalance_side(1) + extension_number(1) +
        #         scheduled_auction_time(4) + auction_book_clearing_price(8) +
        #         collar_reference_price(8) + lower_auction_collar(8) + upper_auction_collar(8)
        (
            auction_type,
            timestamp,
            symbol,
            paired_shares,
            reference_price,
            indicative_clearing_price,
            imbalance_shares,
            imbalance_side,
            extension_number,
            scheduled_auction_time,
            auction_book_clearing_price,
            collar_reference_price,
            lower_auction_collar,
            upper_auction_collar,
        ) = struct.unpack("<xbq8sIqqIbBIqqqq", data[:80])
        return cls(
            auction_type=bytes([auction_type]),
            timestamp=timestamp,
            symbol=symbol,
            paired_shares=paired_shares,
            reference_price=reference_price,
            indicative_clearing_price=indicative_clearing_price,
            imbalance_shares=imbalance_shares,
            imbalance_side=bytes([imbalance_side]),
            extension_number=extension_number,
            scheduled_auction_time=scheduled_auction_time,
            auction_book_clearing_price=auction_book_clearing_price,
            collar_reference_price=collar_reference_price,
            lower_auction_collar=lower_auction_collar,
            upper_auction_collar=upper_auction_collar,
        )

    def to_bytes(self) -> bytes:
        return struct.pack(
            "<cbq8sIqqIbBIqqqq",
            self.message_type,
            self.auction_type[0],
            self.timestamp,
            self.symbol,
            self.paired_shares,
            self.reference_price,
            self.indicative_clearing_price,
            self.imbalance_shares,
            self.imbalance_side[0],
            self.extension_number,
            self.scheduled_auction_time,
            self.auction_book_clearing_price,
            self.collar_reference_price,
            self.lower_auction_collar,
            self.upper_auction_collar,
        )

    def _add_json_fields(self, d: dict[str, Any]) -> None:
        d["auction_type"] = self.auction_type.decode("ascii")
        d["symbol"] = self.symbol.decode("ascii").strip()
        d["paired_shares"] = self.paired_shares
        d["reference_price"] = self.reference_price / 10000.0
        d["indicative_clearing_price"] = self.indicative_clearing_price / 10000.0
        d["imbalance_shares"] = self.imbalance_shares
        d["imbalance_side"] = self.imbalance_side.decode("ascii")
        d["extension_number"] = self.extension_number
        d["scheduled_auction_time"] = self.scheduled_auction_time
        d["auction_book_clearing_price"] = self.auction_book_clearing_price / 10000.0
        d["collar_reference_price"] = self.collar_reference_price / 10000.0
        d["lower_auction_collar"] = self.lower_auction_collar / 10000.0
        d["upper_auction_collar"] = self.upper_auction_collar / 10000.0
