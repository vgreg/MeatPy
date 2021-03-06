"""message_parser.py: The parsing engine that reads raw files/feeds and returns
parsed messages."""

__author__ = "Vincent Grégoire"
__email__ = "vincent.gregoire@gmail.com"

import abc


class MessageParser:
    """A parsing engine that reads raw files/feeds and returns
    parsed messages.

    This is an abstract class that should be overloaded for specific
    exchanges and file formats."""
    __metaclass__ = abc.ABCMeta  # This in an abstract class

    def __init__(self):
        # Messages is a Symbol-based dict of lists of MarketMessage
        self.stock_messages = {}

    def parse_file(self, infile=None):
        """Parses a file containing market messages.

        Parses a file and generate corresponding market messages.

        :param infile: the file to parse
        :type infile: file
        """
        pass

class MarketMessage:
    """A messages that has been parsed and ready to be processed by
    a market history.

    This is an abstract class that should be overloaded for specific
    exchanges."""
    __metaclass__ = abc.ABCMeta  # This in an abstract class
    pass

class MessageParsingException(Exception):
    pass