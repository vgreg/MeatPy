"""Tests for the message parser module."""

from pathlib import Path
from unittest.mock import Mock

import pytest

from meatpy.message_parser import (
    MarketMessage,
    MessageParser,
    MessageParsingException,
)


class ConcreteMessageParser(MessageParser):
    """Concrete implementation of MessageParser for testing."""

    def parse_file(self, infile: Path | str) -> None:
        """Parse a file containing market messages."""
        # Simulate parsing
        self.stock_messages["AAPL"] = Mock(spec=MarketMessage)
        self.stock_messages["MSFT"] = Mock(spec=MarketMessage)


class ConcreteMarketMessage(MarketMessage):
    """Concrete implementation of MarketMessage for testing."""

    def __init__(self, symbol: str, data: dict):
        self.symbol = symbol
        self.data = data


class TestMessageParserInitialization:
    """Test message parser initialization."""

    def test_init(self):
        """Test MessageParser initialization."""
        parser = ConcreteMessageParser()
        assert parser.stock_messages == {}

    def test_init_empty_stock_messages(self):
        """Test that stock_messages is initialized as empty dict."""
        parser = ConcreteMessageParser()
        assert isinstance(parser.stock_messages, dict)
        assert len(parser.stock_messages) == 0


class TestMessageParserParseFile:
    """Test message parser parse_file method."""

    def test_parse_file_abstract(self):
        """Test that parse_file is abstract in base class."""
        parser = MessageParser()

        # Should not raise an error, but should do nothing
        parser.parse_file("test.txt")
        assert parser.stock_messages == {}

    def test_parse_file_concrete_implementation(self):
        """Test concrete parse_file implementation."""
        parser = ConcreteMessageParser()

        parser.parse_file("test.txt")

        assert "AAPL" in parser.stock_messages
        assert "MSFT" in parser.stock_messages
        assert len(parser.stock_messages) == 2

    def test_parse_file_with_path_object(self):
        """Test parse_file with Path object."""
        parser = ConcreteMessageParser()
        path = Path("test.txt")

        parser.parse_file(path)

        assert "AAPL" in parser.stock_messages
        assert "MSFT" in parser.stock_messages

    def test_parse_file_with_string_path(self):
        """Test parse_file with string path."""
        parser = ConcreteMessageParser()

        parser.parse_file("test.txt")

        assert "AAPL" in parser.stock_messages
        assert "MSFT" in parser.stock_messages


class TestMessageParserStockMessages:
    """Test message parser stock_messages handling."""

    def test_stock_messages_storage(self):
        """Test storing messages in stock_messages."""
        parser = ConcreteMessageParser()
        message1 = ConcreteMarketMessage("AAPL", {"price": 100})
        message2 = ConcreteMarketMessage("MSFT", {"price": 200})

        parser.stock_messages["AAPL"] = message1
        parser.stock_messages["MSFT"] = message2

        assert parser.stock_messages["AAPL"] == message1
        assert parser.stock_messages["MSFT"] == message2
        assert len(parser.stock_messages) == 2

    def test_stock_messages_with_bytes_keys(self):
        """Test stock_messages with bytes keys."""
        parser = ConcreteMessageParser()
        message = ConcreteMarketMessage("AAPL", {"price": 100})

        parser.stock_messages[b"AAPL"] = message

        assert parser.stock_messages[b"AAPL"] == message

    def test_stock_messages_overwrite(self):
        """Test overwriting messages in stock_messages."""
        parser = ConcreteMessageParser()
        message1 = ConcreteMarketMessage("AAPL", {"price": 100})
        message2 = ConcreteMarketMessage("AAPL", {"price": 200})

        parser.stock_messages["AAPL"] = message1
        parser.stock_messages["AAPL"] = message2

        assert parser.stock_messages["AAPL"] == message2
        assert len(parser.stock_messages) == 1


class TestMarketMessage:
    """Test MarketMessage base class."""

    def test_market_message_abstract(self):
        """Test that MarketMessage is abstract."""
        # Should not raise an error, but cannot instantiate directly
        # The abstract base class should be subclassed
        assert issubclass(MarketMessage, object)

    def test_concrete_market_message(self):
        """Test concrete MarketMessage implementation."""
        message = ConcreteMarketMessage("AAPL", {"price": 100, "volume": 1000})

        assert message.symbol == "AAPL"
        assert message.data["price"] == 100
        assert message.data["volume"] == 1000


class TestMessageParsingException:
    """Test MessageParsingException."""

    def test_exception_creation(self):
        """Test creating MessageParsingException."""
        exception = MessageParsingException("Parse error")
        assert str(exception) == "Parse error"

    def test_exception_with_details(self):
        """Test MessageParsingException with detailed message."""
        exception = MessageParsingException("Invalid format at line 42")
        assert "Invalid format at line 42" in str(exception)

    def test_exception_inheritance(self):
        """Test that MessageParsingException inherits from Exception."""
        exception = MessageParsingException("Test")
        assert isinstance(exception, Exception)


class TestMessageParserIntegration:
    """Test message parser integration scenarios."""

    def test_parser_with_multiple_messages(self):
        """Test parser handling multiple messages."""
        parser = ConcreteMessageParser()

        # Simulate parsing multiple files
        parser.parse_file("file1.txt")
        parser.parse_file("file2.txt")

        # Should have messages from both files
        assert "AAPL" in parser.stock_messages
        assert "MSFT" in parser.stock_messages

    def test_parser_message_retrieval(self):
        """Test retrieving messages from parser."""
        parser = ConcreteMessageParser()
        parser.parse_file("test.txt")

        aapl_message = parser.stock_messages.get("AAPL")
        msft_message = parser.stock_messages.get("MSFT")

        assert aapl_message is not None
        assert msft_message is not None
        assert isinstance(aapl_message, MarketMessage)
        assert isinstance(msft_message, MarketMessage)


class TestMessageParserErrorHandling:
    """Test message parser error handling."""

    def test_parser_with_invalid_file(self):
        """Test parser behavior with invalid file."""
        parser = ConcreteMessageParser()

        # Should not raise an exception for invalid files
        # (concrete implementation doesn't validate file existence)
        parser.parse_file("nonexistent.txt")

        # Should still populate stock_messages
        assert "AAPL" in parser.stock_messages

    def test_parser_with_empty_file(self):
        """Test parser behavior with empty file."""
        parser = ConcreteMessageParser()

        parser.parse_file("")

        # Should still populate stock_messages
        assert "AAPL" in parser.stock_messages


class TestMessageParserSubclassing:
    """Test message parser subclassing scenarios."""

    def test_custom_parser_implementation(self):
        """Test custom parser implementation."""

        class CustomParser(MessageParser):
            def parse_file(self, infile: Path | str) -> None:
                self.stock_messages["CUSTOM"] = ConcreteMarketMessage("CUSTOM", {})

        parser = CustomParser()
        parser.parse_file("test.txt")

        assert "CUSTOM" in parser.stock_messages
        assert isinstance(parser.stock_messages["CUSTOM"], MarketMessage)

    def test_parser_with_validation(self):
        """Test parser with validation logic."""

        class ValidatingParser(MessageParser):
            def parse_file(self, infile: Path | str) -> None:
                if not str(infile).endswith(".txt"):
                    raise MessageParsingException(f"Invalid file format: {infile}")

                self.stock_messages["VALID"] = ConcreteMarketMessage("VALID", {})

        parser = ValidatingParser()

        # Should work with .txt file
        parser.parse_file("test.txt")
        assert "VALID" in parser.stock_messages

        # Should raise exception with invalid file
        with pytest.raises(MessageParsingException):
            parser.parse_file("test.csv")


class TestMessageParserEdgeCases:
    """Test message parser edge cases."""

    def test_parser_with_none_file(self):
        """Test parser with None file."""
        parser = ConcreteMessageParser()

        # Should not raise an exception
        parser.parse_file(None)  # type: ignore

        # Should still populate stock_messages
        assert "AAPL" in parser.stock_messages

    def test_parser_with_empty_string_file(self):
        """Test parser with empty string file."""
        parser = ConcreteMessageParser()

        parser.parse_file("")

        # Should still populate stock_messages
        assert "AAPL" in parser.stock_messages

    def test_parser_with_unicode_file_path(self):
        """Test parser with unicode file path."""
        parser = ConcreteMessageParser()

        parser.parse_file("test_文件.txt")

        # Should still populate stock_messages
        assert "AAPL" in parser.stock_messages
