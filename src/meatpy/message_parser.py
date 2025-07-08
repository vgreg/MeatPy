"""Message parsing framework for market data.

This module provides abstract base classes for parsing raw market data files
and feeds into structured MarketMessage objects that can be processed by
market processors.
"""

import abc
from pathlib import Path


class MessageParser:
    """A parsing engine that reads raw files/feeds and returns parsed messages.

    This is an abstract class that should be overloaded for specific
    exchanges and file formats. Subclasses must implement the parse_file
    method to handle their specific data format.

    Attributes:
        stock_messages: Dictionary mapping symbols to MarketMessage objects
    """

    __metaclass__ = abc.ABCMeta

    def __init__(self) -> None:
        """Initialize the message parser.

        Creates an empty dictionary to store parsed messages by symbol.
        """

        self.stock_messages: dict[str | bytes, MarketMessage] = {}

    def parse_file(self, infile: Path | str | None = None) -> None:
        """Parse a file containing market messages.

        Parses a file and generates corresponding market messages.
        This is an abstract method that must be implemented by subclasses.

        Args:
            infile: The file to parse. Can be a Path object, string path,
                   or None for stdin.
        """
        pass


class MarketMessage:
    """A message that has been parsed and is ready to be processed by a market processor.

    This is an abstract class that should be overloaded for specific
    exchanges. Subclasses should contain the parsed data from raw market
    messages in a structured format.
    """

    __metaclass__ = abc.ABCMeta
    pass


class MessageParsingException(Exception):
    """Exception raised when there is an error parsing market messages.

    This exception is raised when the parser encounters invalid or
    malformed data that cannot be parsed into a valid MarketMessage.
    """

    pass
