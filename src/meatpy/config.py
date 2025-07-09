"""Configuration system for MeatPy.

This module provides a configuration system for managing settings and
parameters used throughout the MeatPy library.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class ProcessingConfig:
    """Configuration for market data processing."""

    # LOB tracking settings
    track_lob: bool = True
    max_lob_depth: Optional[int] = None

    # Event handling settings
    enable_event_handlers: bool = True
    event_buffer_size: int = 1000

    # Performance settings
    batch_size: int = 1000
    enable_parallel_processing: bool = False
    num_workers: int = 1

    # Output settings
    output_directory: Path = field(default_factory=lambda: Path("output"))
    enable_csv_export: bool = True
    enable_json_export: bool = False

    # Validation settings
    strict_validation: bool = True
    skip_invalid_messages: bool = False
    log_validation_errors: bool = True


@dataclass
class FormatConfig:
    """Configuration for specific market data formats."""

    # ITCH50 specific settings
    itch50: Dict[str, Any] = field(
        default_factory=lambda: {
            "keep_message_types": None,  # None means keep all
            "skip_stock_messages": False,
            "validate_message_sequence": True,
            "handle_broken_trades": True,
        }
    )

    # Add more format-specific configurations here as needed
    # nasdaq_totalview: Dict[str, Any] = field(default_factory=dict)
    # arca_book: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LoggingConfig:
    """Configuration for logging."""

    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: Optional[Path] = None
    console: bool = True


@dataclass
class MeatPyConfig:
    """Main configuration class for MeatPy."""

    processing: ProcessingConfig = field(default_factory=ProcessingConfig)
    format: FormatConfig = field(default_factory=FormatConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)

    def __post_init__(self) -> None:
        """Ensure output directory exists."""
        self.processing.output_directory.mkdir(parents=True, exist_ok=True)
        if self.logging.file:
            self.logging.file.parent.mkdir(parents=True, exist_ok=True)


# Default configuration instance
default_config = MeatPyConfig()


def load_config_from_file(config_path: Path) -> MeatPyConfig:
    """Load configuration from a file.

    Args:
        config_path: Path to the configuration file

    Returns:
        Loaded configuration

    Raises:
        FileNotFoundError: If the config file doesn't exist
        ValueError: If the config file is invalid
    """
    # This is a placeholder for future implementation
    # Could support YAML, JSON, or TOML configuration files
    raise NotImplementedError("Configuration file loading not yet implemented")


def save_config_to_file(config: MeatPyConfig, config_path: Path) -> None:
    """Save configuration to a file.

    Args:
        config: Configuration to save
        config_path: Path where to save the configuration

    Raises:
        ValueError: If the config file format is not supported
    """
    # This is a placeholder for future implementation
    # Could support YAML, JSON, or TOML configuration files
    raise NotImplementedError("Configuration file saving not yet implemented")
