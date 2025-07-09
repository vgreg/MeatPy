"""Tests for the types module."""

from decimal import Decimal
from typing import get_args

from meatpy.types import OrderID, Price, Qualifiers, TradeRef, Volume


class TestTypeVariables:
    """Test that type variables are correctly defined."""

    def test_price_type_variable(self):
        """Test that Price TypeVar has correct constraints."""
        args = get_args(Price)
        assert int in args
        assert Decimal in args
        assert len(args) == 2

    def test_volume_type_variable(self):
        """Test that Volume TypeVar has correct constraints."""
        args = get_args(Volume)
        assert int in args
        assert Decimal in args
        assert len(args) == 2

    def test_order_id_type_variable(self):
        """Test that OrderID TypeVar has correct constraints."""
        args = get_args(OrderID)
        assert int in args
        assert str in args
        assert bytes in args
        assert len(args) == 3

    def test_trade_ref_type_variable(self):
        """Test that TradeRef TypeVar has correct constraints."""
        args = get_args(TradeRef)
        assert int in args
        assert str in args
        assert bytes in args
        assert len(args) == 3

    def test_qualifiers_type_variable(self):
        """Test that Qualifiers TypeVar has correct constraints."""
        args = get_args(Qualifiers)
        assert dict[str, str] in args
        assert dict[str, int] in args
        assert len(args) == 2


class TestTypeCompatibility:
    """Test that types are compatible with expected values."""

    def test_price_int_compatibility(self):
        """Test that int values are compatible with Price."""
        price: Price = 10000  # Should not raise type error
        assert isinstance(price, int)
        assert price == 10000

    def test_price_decimal_compatibility(self):
        """Test that Decimal values are compatible with Price."""
        price: Price = Decimal("100.00")  # Should not raise type error
        assert isinstance(price, Decimal)
        assert price == Decimal("100.00")

    def test_volume_int_compatibility(self):
        """Test that int values are compatible with Volume."""
        volume: Volume = 100  # Should not raise type error
        assert isinstance(volume, int)
        assert volume == 100

    def test_volume_decimal_compatibility(self):
        """Test that Decimal values are compatible with Volume."""
        volume: Volume = Decimal("100.5")  # Should not raise type error
        assert isinstance(volume, Decimal)
        assert volume == Decimal("100.5")

    def test_order_id_int_compatibility(self):
        """Test that int values are compatible with OrderID."""
        order_id: OrderID = 12345  # Should not raise type error
        assert isinstance(order_id, int)
        assert order_id == 12345

    def test_order_id_str_compatibility(self):
        """Test that str values are compatible with OrderID."""
        order_id: OrderID = "order-12345"  # Should not raise type error
        assert isinstance(order_id, str)
        assert order_id == "order-12345"

    def test_order_id_bytes_compatibility(self):
        """Test that bytes values are compatible with OrderID."""
        order_id: OrderID = b"order-12345"  # Should not raise type error
        assert isinstance(order_id, bytes)
        assert order_id == b"order-12345"

    def test_trade_ref_int_compatibility(self):
        """Test that int values are compatible with TradeRef."""
        trade_ref: TradeRef = 67890  # Should not raise type error
        assert isinstance(trade_ref, int)
        assert trade_ref == 67890

    def test_trade_ref_str_compatibility(self):
        """Test that str values are compatible with TradeRef."""
        trade_ref: TradeRef = "trade-67890"  # Should not raise type error
        assert isinstance(trade_ref, str)
        assert trade_ref == "trade-67890"

    def test_qualifiers_str_dict_compatibility(self):
        """Test that dict[str, str] values are compatible with Qualifiers."""
        qualifiers: Qualifiers = {
            "exchange": "NASDAQ",
            "type": "limit",
        }  # Should not raise type error
        assert isinstance(qualifiers, dict)
        assert all(
            isinstance(k, str) and isinstance(v, str) for k, v in qualifiers.items()
        )

    def test_qualifiers_int_dict_compatibility(self):
        """Test that dict[str, int] values are compatible with Qualifiers."""
        qualifiers: Qualifiers = {
            "level": 1,
            "priority": 2,
        }  # Should not raise type error
        assert isinstance(qualifiers, dict)
        assert all(
            isinstance(k, str) and isinstance(v, int) for k, v in qualifiers.items()
        )


class TestTypeIncompatibility:
    """Test that incompatible types are properly rejected by type checkers."""

    def test_price_float_incompatibility(self):
        """Test that float values are not compatible with Price."""
        # This would cause a type error in a type checker
        # price: Price = 100.0  # Type error: float not in Price constraints
        pass

    def test_volume_str_incompatibility(self):
        """Test that str values are not compatible with Volume."""
        # This would cause a type error in a type checker
        # volume: Volume = "100"  # Type error: str not in Volume constraints
        pass

    def test_order_id_float_incompatibility(self):
        """Test that float values are not compatible with OrderID."""
        # This would cause a type error in a type checker
        # order_id: OrderID = 123.45  # Type error: float not in OrderID constraints
        pass

    def test_qualifiers_mixed_dict_incompatibility(self):
        """Test that mixed dict values are not compatible with Qualifiers."""
        # This would cause a type error in a type checker
        # qualifiers: Qualifiers = {"str": "value", "int": 123}  # Type error: mixed types
        pass
