"""Registry system for market data formats.

This module provides a registry system for managing different market data
formats and their associated processors, parsers, and message types.
"""

from typing import Any, Dict, Type

from .market_processor import MarketProcessor
from .message_parser import MessageParser


class FormatRegistry:
    """Registry for market data formats.

    This class manages the registration and retrieval of market data formats,
    their processors, parsers, and associated components.
    """

    def __init__(self) -> None:
        """Initialize the format registry."""
        self._formats: Dict[str, Dict[str, Any]] = {}

    def register_format(
        self,
        format_name: str,
        processor_class: Type[MarketProcessor],
        parser_class: Type[MessageParser],
        message_classes: Dict[str, Type] | None = None,
        description: str = "",
    ) -> None:
        """Register a new market data format.

        Args:
            format_name: Unique name for the format
            processor_class: Market processor class for this format
            parser_class: Message parser class for this format
            message_classes: Dictionary of message type names to classes
            description: Human-readable description of the format
        """
        self._formats[format_name] = {
            "processor_class": processor_class,
            "parser_class": parser_class,
            "message_classes": message_classes or {},
            "description": description,
        }

    def get_processor_class(self, format_name: str) -> Type[MarketProcessor]:
        """Get the processor class for a format.

        Args:
            format_name: Name of the format

        Returns:
            The processor class for the format

        Raises:
            KeyError: If the format is not registered
        """
        if format_name not in self._formats:
            raise KeyError(f"Format '{format_name}' is not registered")
        return self._formats[format_name]["processor_class"]

    def get_parser_class(self, format_name: str) -> Type[MessageParser]:
        """Get the parser class for a format.

        Args:
            format_name: Name of the format

        Returns:
            The parser class for the format

        Raises:
            KeyError: If the format is not registered
        """
        if format_name not in self._formats:
            raise KeyError(f"Format '{format_name}' is not registered")
        return self._formats[format_name]["parser_class"]

    def get_message_classes(self, format_name: str) -> Dict[str, Type]:
        """Get the message classes for a format.

        Args:
            format_name: Name of the format

        Returns:
            Dictionary of message type names to classes

        Raises:
            KeyError: If the format is not registered
        """
        if format_name not in self._formats:
            raise KeyError(f"Format '{format_name}' is not registered")
        return self._formats[format_name]["message_classes"]

    def list_formats(self) -> Dict[str, str]:
        """List all registered formats.

        Returns:
            Dictionary mapping format names to descriptions
        """
        return {name: info["description"] for name, info in self._formats.items()}

    def create_processor(self, format_name: str, *args, **kwargs) -> MarketProcessor:
        """Create a new processor instance for a format.

        Args:
            format_name: Name of the format
            *args: Arguments to pass to the processor constructor
            **kwargs: Keyword arguments to pass to the processor constructor

        Returns:
            A new processor instance

        Raises:
            KeyError: If the format is not registered
        """
        processor_class = self.get_processor_class(format_name)
        return processor_class(*args, **kwargs)

    def create_parser(self, format_name: str, *args, **kwargs) -> MessageParser:
        """Create a new parser instance for a format.

        Args:
            format_name: Name of the format
            *args: Arguments to pass to the parser constructor
            **kwargs: Keyword arguments to pass to the parser constructor

        Returns:
            A new parser instance

        Raises:
            KeyError: If the format is not registered
        """
        parser_class = self.get_parser_class(format_name)
        return parser_class(*args, **kwargs)


# Global registry instance
registry = FormatRegistry()
