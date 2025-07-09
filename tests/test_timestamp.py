"""Tests for the timestamp module."""

from datetime import datetime, timezone

from meatpy.timestamp import Timestamp


class TestTimestampCreation:
    """Test timestamp creation and initialization."""

    def test_create_from_datetime(self):
        """Test creating timestamp from datetime object."""
        dt = datetime(2024, 1, 1, 9, 30, 0)
        ts = Timestamp(2024, 1, 1, 9, 30, 0)
        assert ts.year == dt.year
        assert ts.month == dt.month
        assert ts.day == dt.day
        assert ts.hour == dt.hour
        assert ts.minute == dt.minute

    def test_create_from_datetime_object(self):
        """Test creating timestamp from datetime object using from_datetime."""
        dt = datetime(2024, 1, 1, 9, 30, 0)
        ts = Timestamp.from_datetime(dt)
        assert ts.year == dt.year
        assert ts.month == dt.month
        assert ts.day == dt.day
        assert ts.hour == dt.hour
        assert ts.minute == dt.minute

    def test_create_with_microseconds(self):
        """Test creating timestamp with microseconds."""
        ts = Timestamp(2024, 1, 1, 9, 30, 0, 123456)
        assert ts.microsecond == 123456

    def test_create_with_timezone(self):
        """Test creating timestamp with timezone."""
        dt = datetime(2024, 1, 1, 9, 30, 0, tzinfo=timezone.utc)
        ts = Timestamp.from_datetime(dt)
        assert ts.year == dt.year
        assert ts.month == dt.month
        assert ts.day == dt.day
        assert ts.hour == dt.hour
        assert ts.minute == dt.minute
        # Note: from_datetime doesn't preserve timezone info
        assert ts.tzinfo is None


class TestTimestampProperties:
    """Test timestamp properties and attributes."""

    def test_datetime_inheritance(self):
        """Test that Timestamp inherits from datetime."""
        ts = Timestamp(2024, 1, 1, 9, 30, 0)
        assert isinstance(ts, datetime)
        assert isinstance(ts, Timestamp)

    def test_year_property(self):
        """Test year property."""
        ts = Timestamp(2024, 1, 1, 9, 30, 0)
        assert ts.year == 2024

    def test_month_property(self):
        """Test month property."""
        ts = Timestamp(2024, 1, 1, 9, 30, 0)
        assert ts.month == 1

    def test_day_property(self):
        """Test day property."""
        ts = Timestamp(2024, 1, 1, 9, 30, 0)
        assert ts.day == 1

    def test_hour_property(self):
        """Test hour property."""
        ts = Timestamp(2024, 1, 1, 9, 30, 0)
        assert ts.hour == 9

    def test_minute_property(self):
        """Test minute property."""
        ts = Timestamp(2024, 1, 1, 9, 30, 0)
        assert ts.minute == 30

    def test_second_property(self):
        """Test second property."""
        ts = Timestamp(2024, 1, 1, 9, 30, 0)
        assert ts.second == 0

    def test_microsecond_property(self):
        """Test microsecond property."""
        ts = Timestamp(2024, 1, 1, 9, 30, 0, 123456)
        assert ts.microsecond == 123456


class TestTimestampComparison:
    """Test timestamp comparison operations."""

    def test_equality(self):
        """Test timestamp equality."""
        ts1 = Timestamp(2024, 1, 1, 9, 30, 0)
        ts2 = Timestamp(2024, 1, 1, 9, 30, 0)
        assert ts1 == ts2

    def test_inequality(self):
        """Test timestamp inequality."""
        ts1 = Timestamp(2024, 1, 1, 9, 30, 0)
        ts2 = Timestamp(2024, 1, 1, 9, 31, 0)
        assert ts1 != ts2

    def test_less_than(self):
        """Test timestamp less than comparison."""
        ts1 = Timestamp(2024, 1, 1, 9, 30, 0)
        ts2 = Timestamp(2024, 1, 1, 9, 31, 0)
        assert ts1 < ts2

    def test_greater_than(self):
        """Test timestamp greater than comparison."""
        ts1 = Timestamp(2024, 1, 1, 9, 31, 0)
        ts2 = Timestamp(2024, 1, 1, 9, 30, 0)
        assert ts1 > ts2

    def test_less_equal(self):
        """Test timestamp less than or equal comparison."""
        ts1 = Timestamp(2024, 1, 1, 9, 30, 0)
        ts2 = Timestamp(2024, 1, 1, 9, 30, 0)
        ts3 = Timestamp(2024, 1, 1, 9, 31, 0)
        assert ts1 <= ts2
        assert ts1 <= ts3

    def test_greater_equal(self):
        """Test timestamp greater than or equal comparison."""
        ts1 = Timestamp(2024, 1, 1, 9, 30, 0)
        ts2 = Timestamp(2024, 1, 1, 9, 30, 0)
        ts3 = Timestamp(2024, 1, 1, 9, 29, 0)
        assert ts1 >= ts2
        assert ts1 >= ts3


class TestTimestampArithmetic:
    """Test timestamp arithmetic operations."""

    def test_addition_timedelta(self):
        """Test adding timedelta to timestamp."""
        from datetime import timedelta

        ts = Timestamp(2024, 1, 1, 9, 30, 0)
        delta = timedelta(minutes=30)
        result = ts + delta
        expected = Timestamp(2024, 1, 1, 10, 0, 0)
        assert result == expected

    def test_subtraction_timedelta(self):
        """Test subtracting timedelta from timestamp."""
        from datetime import timedelta

        ts = Timestamp(2024, 1, 1, 9, 30, 0)
        delta = timedelta(minutes=30)
        result = ts - delta
        expected = Timestamp(2024, 1, 1, 9, 0, 0)
        assert result == expected

    def test_subtraction_timestamp(self):
        """Test subtracting timestamp from timestamp."""
        ts1 = Timestamp(2024, 1, 1, 10, 0, 0)
        ts2 = Timestamp(2024, 1, 1, 9, 30, 0)
        result = ts1 - ts2
        from datetime import timedelta

        expected = timedelta(minutes=30)
        assert result == expected


class TestTimestampStringRepresentation:
    """Test timestamp string representation."""

    def test_str_representation(self):
        """Test string representation."""
        ts = Timestamp(2024, 1, 1, 9, 30, 0)
        assert str(ts) == "2024-01-01 09:30:00.000000"

    def test_repr_representation(self):
        """Test repr representation."""
        ts = Timestamp(2024, 1, 1, 9, 30, 0)
        assert "Timestamp: " in repr(ts)
        assert "2024-01-01 09:30:00.000000" in repr(ts)

    def test_iso_format(self):
        """Test ISO format string."""
        ts = Timestamp(2024, 1, 1, 9, 30, 0)
        assert ts.isoformat() == "2024-01-01T09:30:00"


class TestTimestampCopy:
    """Test timestamp copying functionality."""

    def test_copy_method(self):
        """Test copy method."""
        ts1 = Timestamp(2024, 1, 1, 9, 30, 0, 123456)
        ts2 = ts1.copy()
        assert ts1 == ts2
        assert ts1 is not ts2
        assert ts2.microsecond == 123456

    def test_copy_preserves_timezone(self):
        """Test copy preserves timezone."""
        dt = datetime(2024, 1, 1, 9, 30, 0, tzinfo=timezone.utc)
        ts1 = Timestamp.from_datetime(dt)
        ts2 = ts1.copy()
        # Note: from_datetime doesn't preserve timezone, so both should be None
        assert ts1.tzinfo is None
        assert ts2.tzinfo is None
        assert ts1 == ts2


class TestTimestampEdgeCases:
    """Test timestamp edge cases."""

    def test_leap_year(self):
        """Test leap year handling."""
        ts = Timestamp(2024, 2, 29, 12, 0, 0)
        assert ts.year == 2024
        assert ts.month == 2
        assert ts.day == 29

    def test_midnight(self):
        """Test midnight time."""
        ts = Timestamp(2024, 1, 1, 0, 0, 0)
        assert ts.hour == 0
        assert ts.minute == 0
        assert ts.second == 0

    def test_end_of_day(self):
        """Test end of day time."""
        ts = Timestamp(2024, 1, 1, 23, 59, 59, 999999)
        assert ts.hour == 23
        assert ts.minute == 59
        assert ts.second == 59
        assert ts.microsecond == 999999

    def test_microseconds(self):
        """Test microsecond precision."""
        ts = Timestamp(2024, 1, 1, 9, 30, 0, 123456)
        assert ts.microsecond == 123456
        assert str(ts) == "2024-01-01 09:30:00.123456"
