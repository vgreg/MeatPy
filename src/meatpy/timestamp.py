"""Timestamp utilities for market data processing.

This module provides a Timestamp class that extends datetime with
microsecond precision and standardized formatting for market data.
"""

from copy import deepcopy
from datetime import datetime

TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S.%f"


class Timestamp(datetime):
    """A timestamp class derived from datetime with microsecond precision.

    The timestamp is derived from the standard datetime class with the main
    feature that precision is limited to microseconds. Timestamps need to be
    comparable (<, <=, ==, !=, >=, >) and have a __str__() method.

    Attributes:
        year: Year of the timestamp
        month: Month of the timestamp
        day: Day of the timestamp
        hour: Hour of the timestamp
        minute: Minute of the timestamp
        second: Second of the timestamp
        microsecond: Microsecond of the timestamp
        nanoseconds: Original nanosecond timestamp (if available)
    """

    def __new__(
        cls,
        year=None,
        month=None,
        day=None,
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
        tzinfo=None,
        *,
        fold=0,
        nanoseconds=None,
    ):
        """Create a new Timestamp instance with optional nanoseconds storage."""
        instance = super().__new__(
            cls, year, month, day, hour, minute, second, microsecond, tzinfo, fold=fold
        )
        instance._nanoseconds = nanoseconds
        return instance

    def __str__(self) -> str:
        """Return string representation in standard format.

        Returns:
            str: Timestamp formatted as 'YYYY-MM-DD HH:MM:SS.microseconds'
        """
        return self.strftime(TIMESTAMP_FORMAT)

    def __repr__(self) -> str:
        """Return detailed string representation.

        Returns:
            str: Timestamp with 'Timestamp:' prefix
        """
        return "Timestamp: " + self.__str__()

    @property
    def nanoseconds(self) -> int | None:
        """Get the original nanosecond timestamp if available.

        Returns:
            int: The original nanosecond timestamp, or None if not set
        """
        return getattr(self, "_nanoseconds", None)

    def __reduce_ex__(self, protocol):
        """Custom pickling support for Timestamp.

        This ensures that the Timestamp can be properly pickled/unpickled
        with its custom _nanoseconds attribute.
        """
        # Get the constructor arguments
        args = (
            self.year,
            self.month,
            self.day,
            self.hour,
            self.minute,
            self.second,
            self.microsecond,
            self.tzinfo,
        )
        # Get the state (custom attributes)
        state = {"_nanoseconds": getattr(self, "_nanoseconds", None), "fold": self.fold}
        # Return (callable, args, state)
        return (self.__class__, args, state)

    def __setstate__(self, state):
        """Set state for unpickling."""
        if isinstance(state, dict):
            self._nanoseconds = state.get("_nanoseconds")
            if "fold" in state:
                # Can't set fold directly, it's read-only
                pass

    def copy(self) -> "Timestamp":
        """Create a deep copy of this timestamp.

        Returns:
            Timestamp: A new Timestamp instance with identical values
        """
        return deepcopy(self)

    @classmethod
    def from_datetime(cls, dt: datetime, nanoseconds: int | None = None) -> "Timestamp":
        """Create a Timestamp from a datetime object.

        Args:
            dt: The datetime object to convert
            nanoseconds: Optional original nanosecond timestamp to preserve

        Returns:
            Timestamp: A new Timestamp instance with the datetime values
        """
        return Timestamp(
            year=dt.year,
            month=dt.month,
            day=dt.day,
            hour=dt.hour,
            minute=dt.minute,
            microsecond=dt.microsecond,
            nanoseconds=nanoseconds,
        )
