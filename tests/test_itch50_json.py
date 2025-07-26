"""Tests for ITCH 5.0 message JSON serialization and deserialization."""

import json
import struct

import pytest

from src.meatpy.itch50.itch50_market_message import (
    AddOrderMessage,
    ITCH50MarketMessage,
    StockDirectoryMessage,
    SystemEventMessage,
    TradeMessage,
)


class TestITCH50JSON:
    """Test JSON serialization and deserialization for ITCH 5.0 messages."""

    def test_system_event_message_json(self):
        """Test SystemEventMessage JSON serialization and deserialization."""
        # Format: !HHHIc (stock_locate, tracking_number, ts1, ts2, code)
        binary_data = b"S" + struct.pack("!HHHIc", 1, 2, 3, 4, b"O")
        message = ITCH50MarketMessage.from_bytes(binary_data)

        # Convert to JSON
        json_str = message.to_json()
        json_data = json.loads(json_str)

        # Verify JSON structure
        assert json_data["type"] == "S"
        assert json_data["description"] == "System Event Message"
        assert json_data["stock_locate"] == 1
        assert json_data["tracking_number"] == 2
        assert json_data["code"] == "O"

        # Convert back from JSON
        reconstructed = ITCH50MarketMessage.from_json(json_str)

        # Verify the reconstructed message matches the original
        assert isinstance(reconstructed, SystemEventMessage)
        assert reconstructed.timestamp == message.timestamp
        assert reconstructed.stock_locate == message.stock_locate
        assert reconstructed.tracking_number == message.tracking_number
        assert reconstructed.code == message.code

        # Verify binary representation matches
        assert reconstructed.to_bytes() == message.to_bytes()

    def test_add_order_message_json(self):
        """Test AddOrderMessage JSON serialization and deserialization."""
        # Format: !HHHIQcI8sI (stock_locate, tracking_number, ts1, ts2, order_ref, bsindicator, shares, stock, price)
        binary_data = b"A" + struct.pack(
            "!HHHIQcI8sI", 1, 2, 3, 4, 5, b"B", 6, b"AAPL    ", 100
        )
        message = ITCH50MarketMessage.from_bytes(binary_data)

        # Convert to JSON
        json_str = message.to_json()
        json_data = json.loads(json_str)

        # Verify JSON structure
        assert json_data["type"] == "A"
        assert json_data["description"] == "Add Order Message"
        assert json_data["stock_locate"] == 1
        assert json_data["tracking_number"] == 2
        assert json_data["orderRefNum"] == 5
        assert json_data["bsindicator"] == "B"
        assert json_data["shares"] == 6
        assert json_data["stock"] == "AAPL"
        assert json_data["price"] == 100

        # Convert back from JSON
        reconstructed = ITCH50MarketMessage.from_json(json_str)

        # Verify the reconstructed message matches the original
        assert isinstance(reconstructed, AddOrderMessage)
        assert reconstructed.timestamp == message.timestamp
        assert reconstructed.stock_locate == message.stock_locate
        assert reconstructed.tracking_number == message.tracking_number
        assert reconstructed.order_ref == message.order_ref
        assert reconstructed.bsindicator == message.bsindicator
        assert reconstructed.shares == message.shares
        assert reconstructed.stock == message.stock
        assert reconstructed.price == message.price

        # Verify binary representation matches
        assert reconstructed.to_bytes() == message.to_bytes()

    def test_trade_message_json(self):
        """Test TradeMessage JSON serialization and deserialization."""
        # Format: !HHHIQcI8sIQ (stock_locate, tracking_number, ts1, ts2, order_ref, bsindicator, shares, stock, price, matchNumber)
        binary_data = b"P" + struct.pack(
            "!HHHIQcI8sIQ", 1, 2, 3, 4, 5, b"B", 6, b"AAPL    ", 100, 7
        )
        message = ITCH50MarketMessage.from_bytes(binary_data)

        # Convert to JSON
        json_str = message.to_json()
        json_data = json.loads(json_str)

        # Verify JSON structure
        assert json_data["type"] == "P"
        assert json_data["description"] == "Trade Message"
        assert json_data["stock_locate"] == 1
        assert json_data["tracking_number"] == 2
        assert json_data["orderRefNum"] == 5
        assert json_data["bsindicator"] == "B"
        assert json_data["shares"] == 6
        assert json_data["stock"] == "AAPL"
        assert json_data["price"] == 100
        assert json_data["matchNumber"] == 7

        # Convert back from JSON
        reconstructed = ITCH50MarketMessage.from_json(json_str)

        # Verify the reconstructed message matches the original
        assert isinstance(reconstructed, TradeMessage)
        assert reconstructed.timestamp == message.timestamp
        assert reconstructed.stock_locate == message.stock_locate
        assert reconstructed.tracking_number == message.tracking_number
        assert reconstructed.order_ref == message.order_ref
        assert reconstructed.bsindicator == message.bsindicator
        assert reconstructed.shares == message.shares
        assert reconstructed.stock == message.stock
        assert reconstructed.price == message.price
        assert reconstructed.match == message.match

        # Verify binary representation matches
        assert reconstructed.to_bytes() == message.to_bytes()

    def test_stock_directory_message_json(self):
        """Test StockDirectoryMessage JSON serialization and deserialization."""
        # Format: !HHHI8sccIcc2scccccIc (18 items)
        args = [
            1,  # stock_locate (H)
            2,  # tracking_number (H)
            3,  # ts1 (I)
            4,  # ts2 (I)
            b"AAPL    ",  # stock (8s)
            b"Q",  # category (c)
            b"N",  # status (c)
            100,  # lotsize (I)
            b"Y",  # lotsonly (c)
            b"Q",  # issue_class (c)
            b"  ",  # issue_sub (2s)
            b"Y",  # authenticity (c)
            b"Y",  # shortsale_thresh (c)
            b"N",  # ipo_flag (c)
            b"1",  # luld_ref (c)
            b"N",  # etp_flag (c)
            2,  # etp_leverage (I)
            b" ",  # inverse_ind (c)
        ]
        packed = struct.pack("!HHHI8sccIcc2scccccIc", *args)
        binary_data = b"R" + packed
        message = ITCH50MarketMessage.from_bytes(binary_data)

        # Convert to JSON
        json_str = message.to_json()
        json_data = json.loads(json_str)

        # Verify JSON structure
        assert json_data["type"] == "R"
        assert json_data["description"] == "Stock Directory Message"
        assert json_data["stock_locate"] == 1
        assert json_data["tracking_number"] == 2
        assert json_data["stock"].strip() == "AAPL"
        assert json_data["category"] == "Q"
        assert json_data["status"] == "N"
        assert json_data["lotsize"] == 100
        assert json_data["lotsonly"] == "Y"
        assert json_data["issue_class"] == "Q"
        assert json_data["issue_sub"].strip() == ""
        assert json_data["authenticity"] == "Y"
        assert json_data["shortsale_thresh"] == "Y"
        assert json_data["ipo_flag"] == "N"
        assert json_data["luld_ref"] == "1"
        assert json_data["etp_flag"] == "N"
        assert json_data["etp_leverage"] == 2
        assert json_data["inverse_ind"] == " "

        # Convert back from JSON
        reconstructed = ITCH50MarketMessage.from_json(json_str)

        # Verify the reconstructed message matches the original
        assert isinstance(reconstructed, StockDirectoryMessage)
        assert reconstructed.timestamp == message.timestamp
        assert reconstructed.stock_locate == message.stock_locate
        assert reconstructed.tracking_number == message.tracking_number
        assert reconstructed.stock == message.stock
        assert reconstructed.category == message.category
        assert reconstructed.status == message.status
        assert reconstructed.lotsize == message.lotsize
        assert reconstructed.lotsonly == message.lotsonly
        assert reconstructed.issue_class == message.issue_class
        assert reconstructed.issue_sub == message.issue_sub
        assert reconstructed.authenticity == message.authenticity
        assert reconstructed.shortsale_thresh == message.shortsale_thresh
        assert reconstructed.ipo_flag == message.ipo_flag
        assert reconstructed.luld_ref == message.luld_ref
        assert reconstructed.etp_flag == message.etp_flag
        assert reconstructed.etp_leverage == message.etp_leverage
        assert reconstructed.inverse_ind == message.inverse_ind

        # Verify binary representation matches
        assert reconstructed.to_bytes() == message.to_bytes()

    def test_invalid_json(self):
        """Test that invalid JSON raises a ValueError."""
        with pytest.raises(ValueError):
            ITCH50MarketMessage.from_json("not a json string")

    def test_all_message_types_json_roundtrip(self):
        """Test roundtrip JSON serialization/deserialization for all message types."""
        # This test is a placeholder and should be expanded for all message types
        message_classes = [SystemEventMessage, AddOrderMessage, TradeMessage]
        for message_class in message_classes:
            if message_class == SystemEventMessage:
                binary_data = b"S" + struct.pack("!HHHIc", 1, 2, 3, 4, b"O")
            elif message_class == AddOrderMessage:
                binary_data = b"A" + struct.pack(
                    "!HHHIQcI8sI", 1, 2, 3, 4, 5, b"B", 6, b"AAPL    ", 100
                )
            elif message_class == TradeMessage:
                binary_data = b"P" + struct.pack(
                    "!HHHIQcI8sIQ", 1, 2, 3, 4, 5, b"B", 6, b"AAPL    ", 100, 7
                )
            else:
                continue
            message = ITCH50MarketMessage.from_bytes(binary_data)
            json_str = message.to_json()
            reconstructed = ITCH50MarketMessage.from_json(json_str)
            assert isinstance(reconstructed, message_class)
            assert reconstructed.to_bytes() == message.to_bytes()
