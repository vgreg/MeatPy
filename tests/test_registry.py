"""Tests for the registry module."""

from unittest.mock import Mock

import pytest

from meatpy.market_processor import MarketProcessor
from meatpy.message_parser import MessageParser
from meatpy.registry import FormatRegistry, registry


class TestFormatRegistry:
    """Test FormatRegistry class."""

    def test_initialization(self):
        """Test registry initialization."""
        reg = FormatRegistry()
        assert reg._formats == {}

    def test_register_format(self):
        """Test registering a format."""
        reg = FormatRegistry()

        # Create mock classes
        mock_processor = Mock(spec=MarketProcessor)
        mock_parser = Mock(spec=MessageParser)
        mock_message_classes = {"TestMessage": Mock()}

        reg.register_format(
            format_name="test_format",
            processor_class=mock_processor,
            parser_class=mock_parser,
            message_classes=mock_message_classes,
            description="Test format for testing",
        )

        assert "test_format" in reg._formats
        assert reg._formats["test_format"]["processor_class"] == mock_processor
        assert reg._formats["test_format"]["parser_class"] == mock_parser
        assert reg._formats["test_format"]["message_classes"] == mock_message_classes
        assert reg._formats["test_format"]["description"] == "Test format for testing"

    def test_register_format_without_message_classes(self):
        """Test registering a format without message classes."""
        reg = FormatRegistry()

        mock_processor = Mock(spec=MarketProcessor)
        mock_parser = Mock(spec=MessageParser)

        reg.register_format(
            format_name="test_format",
            processor_class=mock_processor,
            parser_class=mock_parser,
            description="Test format",
        )

        assert reg._formats["test_format"]["message_classes"] == {}

    def test_get_processor_class(self):
        """Test getting processor class."""
        reg = FormatRegistry()
        mock_processor = Mock(spec=MarketProcessor)

        reg.register_format(
            format_name="test_format",
            processor_class=mock_processor,
            parser_class=Mock(spec=MessageParser),
        )

        result = reg.get_processor_class("test_format")
        assert result == mock_processor

    def test_get_processor_class_not_found(self):
        """Test getting processor class for non-existent format."""
        reg = FormatRegistry()

        with pytest.raises(KeyError, match="Format 'nonexistent' is not registered"):
            reg.get_processor_class("nonexistent")

    def test_get_parser_class(self):
        """Test getting parser class."""
        reg = FormatRegistry()
        mock_parser = Mock(spec=MessageParser)

        reg.register_format(
            format_name="test_format",
            processor_class=Mock(spec=MarketProcessor),
            parser_class=mock_parser,
        )

        result = reg.get_parser_class("test_format")
        assert result == mock_parser

    def test_get_parser_class_not_found(self):
        """Test getting parser class for non-existent format."""
        reg = FormatRegistry()

        with pytest.raises(KeyError, match="Format 'nonexistent' is not registered"):
            reg.get_parser_class("nonexistent")

    def test_get_message_classes(self):
        """Test getting message classes."""
        reg = FormatRegistry()
        mock_message_classes = {"TestMessage": Mock()}

        reg.register_format(
            format_name="test_format",
            processor_class=Mock(spec=MarketProcessor),
            parser_class=Mock(spec=MessageParser),
            message_classes=mock_message_classes,
        )

        result = reg.get_message_classes("test_format")
        assert result == mock_message_classes

    def test_get_message_classes_not_found(self):
        """Test getting message classes for non-existent format."""
        reg = FormatRegistry()

        with pytest.raises(KeyError, match="Format 'nonexistent' is not registered"):
            reg.get_message_classes("nonexistent")

    def test_list_formats(self):
        """Test listing registered formats."""
        reg = FormatRegistry()

        reg.register_format(
            format_name="format1",
            processor_class=Mock(spec=MarketProcessor),
            parser_class=Mock(spec=MessageParser),
            description="First format",
        )

        reg.register_format(
            format_name="format2",
            processor_class=Mock(spec=MarketProcessor),
            parser_class=Mock(spec=MessageParser),
            description="Second format",
        )

        result = reg.list_formats()
        assert result == {
            "format1": "First format",
            "format2": "Second format",
        }

    def test_list_formats_empty(self):
        """Test listing formats when registry is empty."""
        reg = FormatRegistry()
        result = reg.list_formats()
        assert result == {}

    def test_create_processor(self):
        """Test creating a processor instance."""
        reg = FormatRegistry()
        mock_processor_class = Mock(spec=MarketProcessor)
        mock_processor_instance = Mock()
        mock_processor_class.return_value = mock_processor_instance

        reg.register_format(
            format_name="test_format",
            processor_class=mock_processor_class,
            parser_class=Mock(spec=MessageParser),
        )

        result = reg.create_processor("test_format", "AAPL", "2024-01-01")

        mock_processor_class.assert_called_once_with("AAPL", "2024-01-01")
        assert result == mock_processor_instance

    def test_create_processor_with_kwargs(self):
        """Test creating a processor instance with keyword arguments."""
        reg = FormatRegistry()
        mock_processor_class = Mock(spec=MarketProcessor)
        mock_processor_instance = Mock()
        mock_processor_class.return_value = mock_processor_instance

        reg.register_format(
            format_name="test_format",
            processor_class=mock_processor_class,
            parser_class=Mock(spec=MessageParser),
        )

        result = reg.create_processor(
            "test_format", "AAPL", "2024-01-01", track_lob=False, max_depth=10
        )

        mock_processor_class.assert_called_once_with(
            "AAPL", "2024-01-01", track_lob=False, max_depth=10
        )
        assert result == mock_processor_instance

    def test_create_parser(self):
        """Test creating a parser instance."""
        reg = FormatRegistry()
        mock_parser_class = Mock(spec=MessageParser)
        mock_parser_instance = Mock()
        mock_parser_class.return_value = mock_parser_instance

        reg.register_format(
            format_name="test_format",
            processor_class=Mock(spec=MarketProcessor),
            parser_class=mock_parser_class,
        )

        result = reg.create_parser("test_format")

        mock_parser_class.assert_called_once_with()
        assert result == mock_parser_instance

    def test_create_parser_with_kwargs(self):
        """Test creating a parser instance with keyword arguments."""
        reg = FormatRegistry()
        mock_parser_class = Mock(spec=MessageParser)
        mock_parser_instance = Mock()
        mock_parser_class.return_value = mock_parser_instance

        reg.register_format(
            format_name="test_format",
            processor_class=Mock(spec=MarketProcessor),
            parser_class=mock_parser_class,
        )

        result = reg.create_parser("test_format", skip_stock_messages=True)

        mock_parser_class.assert_called_once_with(skip_stock_messages=True)
        assert result == mock_parser_instance

    def test_create_processor_not_found(self):
        """Test creating processor for non-existent format."""
        reg = FormatRegistry()

        with pytest.raises(KeyError, match="Format 'nonexistent' is not registered"):
            reg.create_processor("nonexistent", "AAPL", "2024-01-01")

    def test_create_parser_not_found(self):
        """Test creating parser for non-existent format."""
        reg = FormatRegistry()

        with pytest.raises(KeyError, match="Format 'nonexistent' is not registered"):
            reg.create_parser("nonexistent")


class TestGlobalRegistry:
    """Test the global registry instance."""

    def test_global_registry_instance(self):
        """Test that global registry is a FormatRegistry instance."""
        assert isinstance(registry, FormatRegistry)

    def test_global_registry_starts_empty(self):
        """Test that global registry starts empty."""
        # Clear any existing registrations
        registry._formats.clear()
        assert registry.list_formats() == {}


class TestRegistryIntegration:
    """Test registry integration scenarios."""

    def test_register_multiple_formats(self):
        """Test registering multiple formats."""
        reg = FormatRegistry()

        # Register multiple formats
        reg.register_format(
            format_name="itch50",
            processor_class=Mock(spec=MarketProcessor),
            parser_class=Mock(spec=MessageParser),
            description="NASDAQ ITCH 5.0",
        )

        reg.register_format(
            format_name="nasdaq_totalview",
            processor_class=Mock(spec=MarketProcessor),
            parser_class=Mock(spec=MessageParser),
            description="NASDAQ TotalView",
        )

        reg.register_format(
            format_name="arca_book",
            processor_class=Mock(spec=MarketProcessor),
            parser_class=Mock(spec=MessageParser),
            description="ARCA Book",
        )

        # Verify all formats are registered
        formats = reg.list_formats()
        assert "itch50" in formats
        assert "nasdaq_totalview" in formats
        assert "arca_book" in formats
        assert formats["itch50"] == "NASDAQ ITCH 5.0"
        assert formats["nasdaq_totalview"] == "NASDAQ TotalView"
        assert formats["arca_book"] == "ARCA Book"

    def test_format_overwrite(self):
        """Test that registering the same format twice overwrites the first."""
        reg = FormatRegistry()

        # Register format first time
        processor1 = Mock(spec=MarketProcessor)
        parser1 = Mock(spec=MessageParser)
        reg.register_format(
            format_name="test_format",
            processor_class=processor1,
            parser_class=parser1,
            description="First registration",
        )

        # Register same format second time
        processor2 = Mock(spec=MarketProcessor)
        parser2 = Mock(spec=MessageParser)
        reg.register_format(
            format_name="test_format",
            processor_class=processor2,
            parser_class=parser2,
            description="Second registration",
        )

        # Verify second registration overwrote first
        assert reg.get_processor_class("test_format") == processor2
        assert reg.get_parser_class("test_format") == parser2
        assert reg.list_formats()["test_format"] == "Second registration"

    def test_format_with_message_classes(self):
        """Test format registration with message classes."""
        reg = FormatRegistry()

        message_classes = {
            "AddOrder": Mock(),
            "OrderExecuted": Mock(),
            "OrderCancel": Mock(),
            "OrderDelete": Mock(),
        }

        reg.register_format(
            format_name="test_format",
            processor_class=Mock(spec=MarketProcessor),
            parser_class=Mock(spec=MessageParser),
            message_classes=message_classes,
        )

        result = reg.get_message_classes("test_format")
        assert result == message_classes
        assert "AddOrder" in result
        assert "OrderExecuted" in result
        assert "OrderCancel" in result
        assert "OrderDelete" in result


class TestRegistryErrorHandling:
    """Test registry error handling."""

    def test_register_with_invalid_processor_class(self):
        """Test registering with invalid processor class."""
        reg = FormatRegistry()

        # This should work since we're not validating class types
        reg.register_format(
            format_name="test_format",
            processor_class=object,  # Not a MarketProcessor
            parser_class=Mock(spec=MessageParser),
        )

        # But creating an instance should fail
        with pytest.raises(TypeError):
            reg.create_processor("test_format", "AAPL", "2024-01-01")

    def test_register_with_invalid_parser_class(self):
        """Test registering with invalid parser class."""
        reg = FormatRegistry()

        # This should work since we're not validating class types
        reg.register_format(
            format_name="test_format",
            processor_class=Mock(spec=MarketProcessor),
            parser_class=object,  # Not a MessageParser
        )

        # But creating an instance should fail
        with pytest.raises(TypeError):
            reg.create_parser("test_format")

    def test_register_with_empty_format_name(self):
        """Test registering with empty format name."""
        reg = FormatRegistry()

        reg.register_format(
            format_name="",
            processor_class=Mock(spec=MarketProcessor),
            parser_class=Mock(spec=MessageParser),
        )

        # This should work, but might not be desired
        assert "" in reg.list_formats()

    def test_register_with_none_format_name(self):
        """Test registering with None format name."""
        reg = FormatRegistry()

        with pytest.raises(TypeError):
            reg.register_format(
                format_name=None,
                processor_class=Mock(spec=MarketProcessor),
                parser_class=Mock(spec=MessageParser),
            )
