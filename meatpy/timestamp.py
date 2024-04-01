"""timestamp.py: A standard timestamp."""

from copy import deepcopy
from datetime import datetime

TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S.%f"


class Timestamp(datetime):
    """Basic timestamp derived form datetime

    The timestamp is derived from the standard datetime class. The main
    is that precision is limited to microseconds.
    Timestamps need to be comparable (<, <=, ==, !=, >=, >) and
    need to have a __str__() method.

    """

    def __str__(self):
        return self.strftime(TIMESTAMP_FORMAT)

    def __repr__(self):
        return "Timestamp: " + self.__str__()

    def copy(self):
        return deepcopy(self)

    @classmethod
    def from_datetime(cls, dt):
        return Timestamp(
            year=dt.year,
            month=dt.month,
            day=dt.day,
            hour=dt.hour,
            minute=dt.minute,
            microsecond=dt.microsecond,
        )
