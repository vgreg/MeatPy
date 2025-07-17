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
    """

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

    def copy(self) -> "Timestamp":
        """Create a deep copy of this timestamp.

        Returns:
            Timestamp: A new Timestamp instance with identical values
        """
        return deepcopy(self)

    @classmethod
    def from_datetime(cls, dt: datetime) -> "Timestamp":
        """Create a Timestamp from a datetime object.

        Args:
            dt: The datetime object to convert

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
        )
