"""Tests for the API module."""

from io import BytesIO
from unittest.mock import Mock, patch

import pytest

from meatpy.api import (
    MarketDataProcessor,
    create_parser,
    create_processor,
    list_available_formats,
    register_itch50,
)
from meatpy.config import MeatPyConfig
from meatpy.market_event_handler import MarketEventHandler
from meatpy.market_processor import MarketProcessor
from meatpy.message_parser import MessageParser


class TestMarketDataProcessor:
    """Test MarketDataProcessor class."""

    def test_initialization(self):
        """Test MarketDataProcessor initialization."""
        processor = MarketDataProcessor("itch50")
        assert processor.format_name == "itch50"
        assert isinstance(processor.config, MeatPyConfig)
        assert processor.handlers == []

    def test_initialization_with_config(self):
        """Test MarketDataProcessor initialization with custom config."""
        config = MeatPyConfig()
        config.processing.track_lob = False

        processor = MarketDataProcessor("itch50", config=config)
        assert processor.config == config
        assert processor.config.processing.track_lob is False

    def test_initialization_with_handlers(self):
        """Test MarketDataProcessor initialization with handlers."""
        handler1 = Mock(spec=MarketEventHandler)
        handler2 = Mock(spec=MarketEventHandler)

        processor = MarketDataProcessor("itch50", handlers=[handler1, handler2])
        assert processor.handlers == [handler1, handler2]

    def test_initialization_invalid_format(self):
        """Test MarketDataProcessor initialization with invalid format."""
        with pytest.raises(
            ValueError, match="Format 'invalid_format' is not registered"
        ):
            MarketDataProcessor("invalid_format")

    @patch("meatpy.api.registry")
    def test_process_file(self, mock_registry):
        """Test processing a file."""
        # Setup mocks
        mock_parser = Mock(spec=MessageParser)
        mock_processor = Mock(spec=MarketProcessor)
        mock_registry.create_parser.return_value = mock_parser
        mock_registry.create_processor.return_value = mock_processor
        mock_registry.list_formats.return_value = {"itch50": "Test format"}

        # Create processor
        processor = MarketDataProcessor("itch50")

        # Process file
        result = processor.process_file("test_file.gz", "AAPL", "2024-01-01")

        # Verify calls
        mock_registry.create_parser.assert_called_once_with("itch50")
        mock_registry.create_processor.assert_called_once_with(
            "itch50", "AAPL", "2024-01-01"
        )
        mock_parser.parse_file.assert_called_once_with("test_file.gz")

        # Verify handlers were added
        assert mock_processor.handlers == processor.handlers

        # Verify processing was done
        mock_processor.processing_done.assert_called_once()

        # Verify result
        assert result == mock_processor

    @patch("meatpy.api.registry")
    def test_process_file_with_handlers(self, mock_registry):
        """Test processing a file with handlers."""
        # Setup mocks
        mock_parser = Mock(spec=MessageParser)
        mock_processor = Mock(spec=MarketProcessor)
        mock_processor.handlers = []
        mock_registry.create_parser.return_value = mock_parser
        mock_registry.create_processor.return_value = mock_processor
        mock_registry.list_formats.return_value = {"itch50": "Test format"}

        # Create handlers
        handler1 = Mock(spec=MarketEventHandler)
        handler2 = Mock(spec=MarketEventHandler)

        # Create processor with handlers
        processor = MarketDataProcessor("itch50", handlers=[handler1, handler2])

        # Process file
        processor.process_file("test_file.gz", "AAPL", "2024-01-01")

        # Verify handlers were added to processor
        assert mock_processor.handlers == [handler1, handler2]

    @patch("meatpy.api.registry")
    def test_process_stream(self, mock_registry):
        """Test processing a stream."""
        # Setup mocks
        mock_parser = Mock(spec=MessageParser)
        mock_processor = Mock(spec=MarketProcessor)
        mock_registry.create_parser.return_value = mock_parser
        mock_registry.create_processor.return_value = mock_processor
        mock_registry.list_formats.return_value = {"itch50": "Test format"}

        # Create processor
        processor = MarketDataProcessor("itch50")

        # Create mock stream
        mock_stream = BytesIO(b"test data")

        # Process stream
        result = processor.process_stream(mock_stream, "AAPL", "2024-01-01")

        # Verify calls
        mock_registry.create_parser.assert_called_once_with("itch50")
        mock_registry.create_processor.assert_called_once_with(
            "itch50", "AAPL", "2024-01-01"
        )
        mock_parser.parse_file.assert_called_once_with(mock_stream)

        # Verify result
        assert result == mock_processor

    @patch("meatpy.api.registry")
    def test_process_file_with_messages(self, mock_registry):
        """Test processing a file with actual messages."""
        # Setup mocks
        mock_parser = Mock(spec=MessageParser)
        mock_processor = Mock(spec=MarketProcessor)
        mock_message1 = Mock()
        mock_message2 = Mock()
        mock_parser.stock_messages = {
            "AAPL": mock_message1,
            "MSFT": mock_message2,
        }

        mock_registry.create_parser.return_value = mock_parser
        mock_registry.create_processor.return_value = mock_processor
        mock_registry.list_formats.return_value = {"itch50": "Test format"}

        # Create processor
        processor = MarketDataProcessor("itch50")

        # Process file
        processor.process_file("test_file.gz", "AAPL", "2024-01-01")

        # Verify messages were processed
        assert mock_processor.process_message.call_count == 2
        mock_processor.process_message.assert_any_call(mock_message1)
        mock_processor.process_message.assert_any_call(mock_message2)


class TestFactoryFunctions:
    """Test factory functions."""

    @patch("meatpy.api.registry")
    def test_create_processor(self, mock_registry):
        """Test create_processor function."""
        mock_processor = Mock(spec=MarketProcessor)
        mock_registry.create_processor.return_value = mock_processor

        result = create_processor("itch50", "AAPL", "2024-01-01", track_lob=False)

        mock_registry.create_processor.assert_called_once_with(
            "itch50", "AAPL", "2024-01-01", track_lob=False
        )
        assert result == mock_processor

    @patch("meatpy.api.registry")
    def test_create_parser(self, mock_registry):
        """Test create_parser function."""
        mock_parser = Mock(spec=MessageParser)
        mock_registry.create_parser.return_value = mock_parser

        result = create_parser("itch50", skip_stock_messages=True)

        mock_registry.create_parser.assert_called_once_with(
            "itch50", skip_stock_messages=True
        )
        assert result == mock_parser

    @patch("meatpy.api.registry")
    def test_list_available_formats(self, mock_registry):
        """Test list_available_formats function."""
        mock_formats = {
            "itch50": "NASDAQ ITCH 5.0",
            "nasdaq_totalview": "NASDAQ TotalView",
        }
        mock_registry.list_formats.return_value = mock_formats

        result = list_available_formats()

        mock_registry.list_formats.assert_called_once()
        assert result == mock_formats


class TestRegisterITCH50:
    """Test register_itch50 function."""

    @patch("meatpy.api.registry")
    @patch("meatpy.api.ITCH50MarketProcessor")
    @patch("meatpy.api.ITCH50MessageParser")
    @patch("meatpy.api.AddOrderMessage")
    @patch("meatpy.api.OrderExecutedMessage")
    @patch("meatpy.api.OrderCancelMessage")
    @patch("meatpy.api.OrderDeleteMessage")
    @patch("meatpy.api.OrderReplaceMessage")
    def test_register_itch50_success(
        self,
        mock_order_replace,
        mock_order_delete,
        mock_order_cancel,
        mock_order_executed,
        mock_add_order,
        mock_parser,
        mock_processor,
        mock_registry,
    ):
        """Test successful ITCH50 registration."""
        # Call the function
        register_itch50()

        # Verify registry was called with correct parameters
        mock_registry.register_format.assert_called_once()
        call_args = mock_registry.register_format.call_args

        assert call_args[1]["format_name"] == "itch50"
        assert call_args[1]["processor_class"] == mock_processor
        assert call_args[1]["parser_class"] == mock_parser
        assert call_args[1]["description"] == "NASDAQ ITCH 5.0"

        # Verify message classes
        message_classes = call_args[1]["message_classes"]
        assert message_classes["AddOrder"] == mock_add_order
        assert message_classes["OrderExecuted"] == mock_order_executed
        assert message_classes["OrderCancel"] == mock_order_cancel
        assert message_classes["OrderDelete"] == mock_order_delete
        assert message_classes["OrderReplace"] == mock_order_replace

    @patch("meatpy.api.registry")
    def test_register_itch50_import_error(self, mock_registry):
        """Test ITCH50 registration when import fails."""
        # Mock import error
        with patch("meatpy.api.ITCH50MarketProcessor", side_effect=ImportError):
            register_itch50()

            # Registry should not be called
            mock_registry.register_format.assert_not_called()


class TestAPIErrorHandling:
    """Test API error handling."""

    @patch("meatpy.api.registry")
    def test_create_processor_not_found(self, mock_registry):
        """Test create_processor with non-existent format."""
        mock_registry.create_processor.side_effect = KeyError(
            "Format 'nonexistent' is not registered"
        )

        with pytest.raises(KeyError, match="Format 'nonexistent' is not registered"):
            create_processor("nonexistent", "AAPL", "2024-01-01")

    @patch("meatpy.api.registry")
    def test_create_parser_not_found(self, mock_registry):
        """Test create_parser with non-existent format."""
        mock_registry.create_parser.side_effect = KeyError(
            "Format 'nonexistent' is not registered"
        )

        with pytest.raises(KeyError, match="Format 'nonexistent' is not registered"):
            create_parser("nonexistent")

    @patch("meatpy.api.registry")
    def test_process_file_parser_error(self, mock_registry):
        """Test process_file when parser fails."""
        mock_parser = Mock(spec=MessageParser)
        mock_processor = Mock(spec=MarketProcessor)
        mock_registry.create_parser.return_value = mock_parser
        mock_registry.create_processor.return_value = mock_processor
        mock_registry.list_formats.return_value = {"itch50": "Test format"}

        # Make parser raise an exception
        mock_parser.parse_file.side_effect = Exception("Parser error")

        processor = MarketDataProcessor("itch50")

        with pytest.raises(Exception, match="Parser error"):
            processor.process_file("test_file.gz", "AAPL", "2024-01-01")


class TestAPIIntegration:
    """Test API integration scenarios."""

    @patch("meatpy.api.registry")
    def test_full_processing_workflow(self, mock_registry):
        """Test a complete processing workflow."""
        # Setup mocks
        mock_parser = Mock(spec=MessageParser)
        mock_processor = Mock(spec=MarketProcessor)
        mock_handler = Mock(spec=MarketEventHandler)

        mock_parser.stock_messages = {"AAPL": Mock()}
        mock_registry.create_parser.return_value = mock_parser
        mock_registry.create_processor.return_value = mock_processor
        mock_registry.list_formats.return_value = {"itch50": "Test format"}

        # Create processor with handler
        processor = MarketDataProcessor("itch50", handlers=[mock_handler])

        # Process file
        result = processor.process_file("test_file.gz", "AAPL", "2024-01-01")

        # Verify complete workflow
        assert mock_registry.create_parser.called
        assert mock_registry.create_processor.called
        assert mock_parser.parse_file.called
        assert mock_processor.process_message.called
        assert mock_processor.processing_done.called
        assert mock_handler in mock_processor.handlers
        assert result == mock_processor

    @patch("meatpy.api.registry")
    def test_multiple_formats_workflow(self, mock_registry):
        """Test working with multiple formats."""
        # Setup registry to return multiple formats
        mock_registry.list_formats.return_value = {
            "itch50": "NASDAQ ITCH 5.0",
            "nasdaq_totalview": "NASDAQ TotalView",
            "arca_book": "ARCA Book",
        }

        # Test that we can list formats
        formats = list_available_formats()
        assert "itch50" in formats
        assert "nasdaq_totalview" in formats
        assert "arca_book" in formats

        # Test creating processors for different formats
        mock_processor = Mock(spec=MarketProcessor)
        mock_registry.create_processor.return_value = mock_processor

        for format_name in ["itch50", "nasdaq_totalview", "arca_book"]:
            processor = create_processor(format_name, "AAPL", "2024-01-01")
            assert processor == mock_processor
            mock_registry.create_processor.assert_called_with(
                format_name, "AAPL", "2024-01-01"
            )


class TestAPIConfiguration:
    """Test API configuration scenarios."""

    def test_processor_with_custom_config(self):
        """Test processor with custom configuration."""
        with patch("meatpy.api.registry") as mock_registry:
            mock_registry.list_formats.return_value = {"itch50": "Test format"}

            # Create custom config
            config = MeatPyConfig()
            config.processing.track_lob = False
            config.processing.max_lob_depth = 5
            config.logging.level = "DEBUG"

            # Create processor with custom config
            processor = MarketDataProcessor("itch50", config=config)

            assert processor.config == config
            assert processor.config.processing.track_lob is False
            assert processor.config.processing.max_lob_depth == 5
            assert processor.config.logging.level == "DEBUG"

    def test_processor_with_multiple_handlers(self):
        """Test processor with multiple handlers."""
        with patch("meatpy.api.registry") as mock_registry:
            mock_registry.list_formats.return_value = {"itch50": "Test format"}

            # Create multiple handlers
            handler1 = Mock(spec=MarketEventHandler)
            handler2 = Mock(spec=MarketEventHandler)
            handler3 = Mock(spec=MarketEventHandler)

            # Create processor with multiple handlers
            processor = MarketDataProcessor(
                "itch50", handlers=[handler1, handler2, handler3]
            )

            assert len(processor.handlers) == 3
            assert handler1 in processor.handlers
            assert handler2 in processor.handlers
            assert handler3 in processor.handlers
