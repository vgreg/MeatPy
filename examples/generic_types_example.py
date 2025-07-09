"""Example demonstrating the generic type system in MeatPy.

This example shows how different market data formats can use different
data types while maintaining type safety within each format.
"""

from decimal import Decimal

from meatpy import create_processor


def demonstrate_itch50_types():
    """Demonstrate ITCH50's integer-based types."""
    print("=== ITCH50 Type System ===")

    # ITCH50 uses integers for all numeric fields
    _ = create_processor("itch50", "AAPL", "2024-01-01")

    # Type checking ensures these are all integers
    price: int = 10000  # ITCH50 price in cents
    volume: int = 100  # ITCH50 volume in shares
    order_id: int = 12345  # ITCH50 order ID
    trade_ref: int = 67890  # ITCH50 trade reference

    print("ITCH50 types:")
    print(f"  Price: {type(price).__name__} = {price}")
    print(f"  Volume: {type(volume).__name__} = {volume}")
    print(f"  OrderID: {type(order_id).__name__} = {order_id}")
    print(f"  TradeRef: {type(trade_ref).__name__} = {trade_ref}")
    print()


def demonstrate_future_format_types():
    """Demonstrate how future formats might use different types."""
    print("=== Future Format Type System ===")

    # Example: A crypto exchange format might use Decimal for precision
    # This is just a conceptual example - not implemented yet

    # Crypto format might use:
    # - Decimal for prices (for precision)
    # - Decimal for volumes (fractional shares)
    # - str for order IDs (UUIDs)
    # - str for trade refs (UUIDs)

    crypto_price: Decimal = Decimal("123.456789")
    crypto_volume: Decimal = Decimal("0.123456")
    crypto_order_id: str = "order-12345-abcde"
    crypto_trade_ref: str = "trade-67890-fghij"

    print("Future crypto format types:")
    print(f"  Price: {type(crypto_price).__name__} = {crypto_price}")
    print(f"  Volume: {type(crypto_volume).__name__} = {crypto_volume}")
    print(f"  OrderID: {type(crypto_order_id).__name__} = {crypto_order_id}")
    print(f"  TradeRef: {type(crypto_trade_ref).__name__} = {crypto_trade_ref}")
    print()


def demonstrate_type_consistency():
    """Demonstrate why type consistency matters within a format."""
    print("=== Type Consistency ===")

    # Within ITCH50, all prices must be integers
    # This prevents mixing int and Decimal prices in the same processor

    _ = create_processor("itch50", "AAPL", "2024-01-01")

    # This would be type-safe (all integers)
    _ = [10000, 10001, 10002]  # All int

    # This would cause type errors (mixing int and Decimal)
    # invalid_prices = [10000, Decimal("100.01"), 10002]  # Mixed types

    print("Type consistency ensures:")
    print("  - All prices in ITCH50 are integers")
    print("  - All volumes in ITCH50 are integers")
    print("  - No mixing of int and Decimal within the same processor")
    print("  - Compile-time type checking catches errors")
    print()


def demonstrate_generic_benefits():
    """Demonstrate the benefits of the generic type system."""
    print("=== Generic Type Benefits ===")

    # The generic type system provides:

    # 1. Type safety across different formats
    print("1. Type Safety:")
    print("   - Each format can specify its exact data types")
    print("   - Type checking prevents mixing incompatible types")
    print("   - IDE provides accurate autocomplete and error detection")

    # 2. Format-specific optimization
    print("\n2. Format-Specific Optimization:")
    print("   - ITCH50 can use fast integer arithmetic")
    print("   - Crypto formats can use precise Decimal arithmetic")
    print("   - String-based formats can use efficient string operations")

    # 3. Clear documentation
    print("\n3. Clear Documentation:")
    print("   - Type annotations serve as documentation")
    print("   - Easy to understand what types each format uses")
    print("   - Self-documenting code")

    # 4. Extensibility
    print("\n4. Extensibility:")
    print("   - Easy to add new formats with different type requirements")
    print("   - No need to change existing code")
    print("   - Type system adapts to new requirements")
    print()


if __name__ == "__main__":
    demonstrate_itch50_types()
    demonstrate_future_format_types()
    demonstrate_type_consistency()
    demonstrate_generic_benefits()
