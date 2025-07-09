"""Pytest configuration and common fixtures for MeatPy tests."""

from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from meatpy import MeatPyConfig
from meatpy.event_handlers import LOBRecorder
from meatpy.lob import LimitOrderBook, OrderType
from meatpy.timestamp import Timestamp


@pytest.fixture
def sample_timestamp():
    """Provide a sample timestamp for testing."""
    return Timestamp(datetime(2024, 1, 1, 9, 30, 0))


@pytest.fixture
def sample_date():
    """Provide a sample date for testing."""
    return date(2024, 1, 1)


@pytest.fixture
def sample_datetime():
    """Provide a sample datetime for testing."""
    return datetime(2024, 1, 1, 9, 30, 0)


@pytest.fixture
def sample_config():
    """Provide a sample configuration for testing."""
    config = MeatPyConfig()
    config.processing.track_lob = True
    config.processing.max_lob_depth = 5
    config.processing.output_directory = Path("test_output")
    return config


@pytest.fixture
def sample_lob(sample_timestamp):
    """Provide a sample limit order book for testing."""
    return LimitOrderBook(sample_timestamp)


@pytest.fixture
def sample_lob_with_orders(sample_timestamp):
    """Provide a sample limit order book with some orders for testing."""
    lob = LimitOrderBook(sample_timestamp)

    # Add some test orders
    lob.enter_quote(
        timestamp=sample_timestamp,
        price=10000,  # $100.00
        volume=100,
        order_id=1,
        order_type=OrderType.BID,
    )

    lob.enter_quote(
        timestamp=sample_timestamp,
        price=10001,  # $100.01
        volume=50,
        order_id=2,
        order_type=OrderType.ASK,
    )

    return lob


@pytest.fixture
def sample_lob_recorder():
    """Provide a sample LOB recorder for testing."""
    return LOBRecorder(max_depth=5)


@pytest.fixture
def temp_output_dir(tmp_path):
    """Provide a temporary output directory for testing."""
    output_dir = tmp_path / "test_output"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def sample_price_int():
    """Provide a sample integer price for testing."""
    return 10000  # $100.00 in cents


@pytest.fixture
def sample_price_decimal():
    """Provide a sample decimal price for testing."""
    return Decimal("100.00")


@pytest.fixture
def sample_volume_int():
    """Provide a sample integer volume for testing."""
    return 100


@pytest.fixture
def sample_volume_decimal():
    """Provide a sample decimal volume for testing."""
    return Decimal("100.5")


@pytest.fixture
def sample_order_id_int():
    """Provide a sample integer order ID for testing."""
    return 12345


@pytest.fixture
def sample_order_id_str():
    """Provide a sample string order ID for testing."""
    return "order-12345"


@pytest.fixture
def sample_trade_ref_int():
    """Provide a sample integer trade reference for testing."""
    return 67890


@pytest.fixture
def sample_trade_ref_str():
    """Provide a sample string trade reference for testing."""
    return "trade-67890"
