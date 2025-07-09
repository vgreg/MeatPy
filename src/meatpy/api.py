"""High-level API for MeatPy.

This module provides simplified interfaces for common market data processing
operations, making it easier to use MeatPy for typical use cases.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .config import MeatPyConfig, default_config
from .market_event_handler import MarketEventHandler
from .market_processor import MarketProcessor
from .message_parser import MessageParser
from .registry import registry


class MarketDataProcessor:
    """High-level interface for processing market data.

    This class provides a simplified interface for processing market data
    files and streams, handling the setup and configuration automatically.
    """

    def __init__(
        self,
        format_name: str,
        config: Optional[MeatPyConfig] = None,
        handlers: Optional[List[MarketEventHandler]] = None,
    ) -> None:
        """Initialize the market data processor.

        Args:
            format_name: Name of the market data format (e.g., 'itch50')
            config: Configuration settings (uses default if None)
            handlers: List of event handlers to use
        """
        self.format_name = format_name
        self.config = config or default_config
        self.handlers = handlers or []

        # Validate format is registered
        if format_name not in registry.list_formats():
            raise ValueError(f"Format '{format_name}' is not registered")

    def process_file(
        self,
        file_path: Union[str, Path],
        instrument: str,
        book_date: Optional[str] = None,
    ) -> MarketProcessor:
        """Process a market data file.

        Args:
            file_path: Path to the market data file
            instrument: Instrument/symbol to process
            book_date: Trading date (optional)

        Returns:
            The market processor with processed data
        """
        # Create parser and processor
        parser = registry.create_parser(self.format_name)
        processor = registry.create_processor(self.format_name, instrument, book_date)

        # Add handlers
        for handler in self.handlers:
            processor.handlers.append(handler)

        # Parse and process
        parser.parse_file(file_path)

        # Process messages
        for message in parser.stock_messages.values():
            processor.process_message(message)

        processor.processing_done()
        return processor

    def process_stream(
        self,
        stream,
        instrument: str,
        book_date: Optional[str] = None,
    ) -> MarketProcessor:
        """Process a market data stream.

        Args:
            stream: File-like object containing market data
            instrument: Instrument/symbol to process
            book_date: Trading date (optional)

        Returns:
            The market processor with processed data
        """
        # Create parser and processor
        parser = registry.create_parser(self.format_name)
        processor = registry.create_processor(self.format_name, instrument, book_date)

        # Add handlers
        for handler in self.handlers:
            processor.handlers.append(handler)

        # Parse and process stream
        parser.parse_file(stream)

        # Process messages
        for message in parser.stock_messages.values():
            processor.process_message(message)

        processor.processing_done()
        return processor


def register_itch50() -> None:
    """Register the ITCH50 format with the registry.

    This function registers the ITCH50 format components with the global
    registry for easy access.
    """
    try:
        from .itch50 import (
            AddOrderMessage,
            ITCH50MarketProcessor,
            ITCH50MessageParser,
            OrderCancelMessage,
            OrderDeleteMessage,
            OrderExecutedMessage,
            OrderReplaceMessage,
        )

        message_classes = {
            "AddOrder": AddOrderMessage,
            "OrderExecuted": OrderExecutedMessage,
            "OrderCancel": OrderCancelMessage,
            "OrderDelete": OrderDeleteMessage,
            "OrderReplace": OrderReplaceMessage,
        }

        registry.register_format(
            format_name="itch50",
            processor_class=ITCH50MarketProcessor,
            parser_class=ITCH50MessageParser,
            message_classes=message_classes,
            description="NASDAQ ITCH 5.0 market data format",
        )
    except ImportError:
        # ITCH50 module not available
        pass


def list_available_formats() -> Dict[str, str]:
    """List all available market data formats.

    Returns:
        Dictionary mapping format names to descriptions
    """
    return registry.list_formats()


def create_processor(
    format_name: str,
    instrument: str,
    book_date: Optional[str] = None,
    **kwargs: Any,
) -> MarketProcessor:
    """Create a market processor for a specific format.

    Args:
        format_name: Name of the market data format
        instrument: Instrument/symbol to process
        book_date: Trading date (optional)
        **kwargs: Additional arguments for the processor

    Returns:
        A configured market processor

    Raises:
        KeyError: If the format is not registered
    """
    return registry.create_processor(format_name, instrument, book_date, **kwargs)


def create_parser(format_name: str, **kwargs: Any) -> MessageParser:
    """Create a message parser for a specific format.

    Args:
        format_name: Name of the market data format
        **kwargs: Additional arguments for the parser

    Returns:
        A configured message parser

    Raises:
        KeyError: If the format is not registered
    """
    return registry.create_parser(format_name, **kwargs)


# Auto-register available formats
# register_itch50()  # Temporarily disabled due to circular import issues
