"""Tests for the configuration module."""

from pathlib import Path

import pytest

from meatpy.config import (
    FormatConfig,
    LoggingConfig,
    MeatPyConfig,
    ProcessingConfig,
    default_config,
    load_config_from_file,
    save_config_to_file,
)


class TestProcessingConfig:
    """Test ProcessingConfig class."""

    def test_default_values(self):
        """Test default values for ProcessingConfig."""
        config = ProcessingConfig()
        assert config.track_lob is True
        assert config.max_lob_depth is None
        assert config.enable_event_handlers is True
        assert config.event_buffer_size == 1000
        assert config.batch_size == 1000
        assert config.enable_parallel_processing is False
        assert config.num_workers == 1
        assert config.enable_csv_export is True
        assert config.enable_json_export is False
        assert config.strict_validation is True
        assert config.skip_invalid_messages is False
        assert config.log_validation_errors is True

    def test_custom_values(self):
        """Test custom values for ProcessingConfig."""
        config = ProcessingConfig(
            track_lob=False,
            max_lob_depth=10,
            event_buffer_size=500,
            batch_size=500,
            enable_parallel_processing=True,
            num_workers=4,
            enable_csv_export=False,
            enable_json_export=True,
            strict_validation=False,
            skip_invalid_messages=True,
            log_validation_errors=False,
        )

        assert config.track_lob is False
        assert config.max_lob_depth == 10
        assert config.event_buffer_size == 500
        assert config.batch_size == 500
        assert config.enable_parallel_processing is True
        assert config.num_workers == 4
        assert config.enable_csv_export is False
        assert config.enable_json_export is True
        assert config.strict_validation is False
        assert config.skip_invalid_messages is True
        assert config.log_validation_errors is False

    def test_output_directory(self):
        """Test output directory handling."""
        test_dir = Path("/tmp/test_output")
        config = ProcessingConfig(output_directory=test_dir)
        assert config.output_directory == test_dir


class TestFormatConfig:
    """Test FormatConfig class."""

    def test_default_values(self):
        """Test default values for FormatConfig."""
        config = FormatConfig()
        assert config.itch50["keep_message_types"] is None
        assert config.itch50["skip_stock_messages"] is False
        assert config.itch50["validate_message_sequence"] is True
        assert config.itch50["handle_broken_trades"] is True

    def test_custom_itch50_config(self):
        """Test custom ITCH50 configuration."""
        itch_config = {
            "keep_message_types": b"AS",
            "skip_stock_messages": True,
            "validate_message_sequence": False,
            "handle_broken_trades": False,
        }
        config = FormatConfig(itch50=itch_config)

        assert config.itch50["keep_message_types"] == b"AS"
        assert config.itch50["skip_stock_messages"] is True
        assert config.itch50["validate_message_sequence"] is False
        assert config.itch50["handle_broken_trades"] is False

    def test_add_new_format_config(self):
        """Test adding configuration for new formats."""
        config = FormatConfig()

        # Add new format configuration
        config.nasdaq_totalview = {
            "include_mpid": True,
            "max_levels": 10,
        }

        assert config.nasdaq_totalview["include_mpid"] is True
        assert config.nasdaq_totalview["max_levels"] == 10


class TestLoggingConfig:
    """Test LoggingConfig class."""

    def test_default_values(self):
        """Test default values for LoggingConfig."""
        config = LoggingConfig()
        assert config.level == "INFO"
        assert config.format == "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        assert config.file is None
        assert config.console is True

    def test_custom_values(self):
        """Test custom values for LoggingConfig."""
        log_file = Path("/tmp/test.log")
        config = LoggingConfig(
            level="DEBUG",
            format="%(levelname)s: %(message)s",
            file=log_file,
            console=False,
        )

        assert config.level == "DEBUG"
        assert config.format == "%(levelname)s: %(message)s"
        assert config.file == log_file
        assert config.console is False

    def test_invalid_log_level(self):
        """Test handling of invalid log level."""
        # This should work since we're not validating log levels in the dataclass
        config = LoggingConfig(level="INVALID_LEVEL")
        assert config.level == "INVALID_LEVEL"


class TestMeatPyConfig:
    """Test MeatPyConfig class."""

    def test_default_values(self):
        """Test default values for MeatPyConfig."""
        config = MeatPyConfig()
        assert isinstance(config.processing, ProcessingConfig)
        assert isinstance(config.format, FormatConfig)
        assert isinstance(config.logging, LoggingConfig)

    def test_custom_values(self):
        """Test custom values for MeatPyConfig."""
        processing = ProcessingConfig(track_lob=False)
        format_config = FormatConfig()
        logging = LoggingConfig(level="DEBUG")

        config = MeatPyConfig(
            processing=processing,
            format=format_config,
            logging=logging,
        )

        assert config.processing.track_lob is False
        assert config.logging.level == "DEBUG"

    def test_post_init_output_directory_creation(self, tmp_path):
        """Test that output directory is created in __post_init__."""
        output_dir = tmp_path / "test_output"
        config = MeatPyConfig()
        config.processing.output_directory = output_dir

        # The directory should be created
        assert output_dir.exists()
        assert output_dir.is_dir()

    def test_post_init_log_file_directory_creation(self, tmp_path):
        """Test that log file directory is created in __post_init__."""
        log_dir = tmp_path / "logs"
        log_file = log_dir / "test.log"
        config = MeatPyConfig()
        config.logging.file = log_file

        # The directory should be created
        assert log_dir.exists()
        assert log_dir.is_dir()


class TestDefaultConfig:
    """Test default_config instance."""

    def test_default_config_instance(self):
        """Test that default_config is a valid MeatPyConfig instance."""
        assert isinstance(default_config, MeatPyConfig)
        assert isinstance(default_config.processing, ProcessingConfig)
        assert isinstance(default_config.format, FormatConfig)
        assert isinstance(default_config.logging, LoggingConfig)

    def test_default_config_values(self):
        """Test that default_config has expected default values."""
        assert default_config.processing.track_lob is True
        assert default_config.processing.max_lob_depth is None
        assert default_config.logging.level == "INFO"
        assert default_config.logging.console is True


class TestConfigFileOperations:
    """Test configuration file loading and saving."""

    def test_load_config_from_file_not_implemented(self):
        """Test that load_config_from_file raises NotImplementedError."""
        with pytest.raises(NotImplementedError):
            load_config_from_file(Path("test.yaml"))

    def test_save_config_to_file_not_implemented(self):
        """Test that save_config_to_file raises NotImplementedError."""
        config = MeatPyConfig()
        with pytest.raises(NotImplementedError):
            save_config_to_file(config, Path("test.yaml"))


class TestConfigIntegration:
    """Test configuration integration scenarios."""

    def test_config_for_itch50_processing(self):
        """Test configuration setup for ITCH50 processing."""
        config = MeatPyConfig()

        # Configure for ITCH50 processing
        config.processing.track_lob = True
        config.processing.max_lob_depth = 10
        config.processing.batch_size = 1000
        config.format.itch50["skip_stock_messages"] = True
        config.format.itch50["keep_message_types"] = b"AS"
        config.logging.level = "INFO"
        config.logging.file = Path("itch50_processing.log")

        # Verify configuration
        assert config.processing.track_lob is True
        assert config.processing.max_lob_depth == 10
        assert config.format.itch50["skip_stock_messages"] is True
        assert config.format.itch50["keep_message_types"] == b"AS"
        assert config.logging.level == "INFO"

    def test_config_for_high_frequency_processing(self):
        """Test configuration setup for high-frequency processing."""
        config = MeatPyConfig()

        # Configure for high-frequency processing
        config.processing.enable_parallel_processing = True
        config.processing.num_workers = 8
        config.processing.batch_size = 100
        config.processing.event_buffer_size = 10000
        config.processing.strict_validation = False
        config.processing.skip_invalid_messages = True
        config.logging.level = "WARNING"

        # Verify configuration
        assert config.processing.enable_parallel_processing is True
        assert config.processing.num_workers == 8
        assert config.processing.batch_size == 100
        assert config.processing.event_buffer_size == 10000
        assert config.processing.strict_validation is False
        assert config.processing.skip_invalid_messages is True
        assert config.logging.level == "WARNING"

    def test_config_for_debug_mode(self):
        """Test configuration setup for debug mode."""
        config = MeatPyConfig()

        # Configure for debug mode
        config.processing.track_lob = True
        config.processing.max_lob_depth = None  # Track all levels
        config.processing.strict_validation = True
        config.processing.skip_invalid_messages = False
        config.processing.log_validation_errors = True
        config.logging.level = "DEBUG"
        config.logging.console = True
        config.logging.file = Path("debug.log")

        # Verify configuration
        assert config.processing.track_lob is True
        assert config.processing.max_lob_depth is None
        assert config.processing.strict_validation is True
        assert config.processing.skip_invalid_messages is False
        assert config.processing.log_validation_errors is True
        assert config.logging.level == "DEBUG"
        assert config.logging.console is True
        assert config.logging.file == Path("debug.log")


class TestConfigValidation:
    """Test configuration validation scenarios."""

    def test_negative_values(self):
        """Test handling of negative values."""
        # These should work since dataclasses don't validate ranges
        config = ProcessingConfig(
            event_buffer_size=-1,
            batch_size=-100,
            num_workers=-5,
            max_lob_depth=-10,
        )

        assert config.event_buffer_size == -1
        assert config.batch_size == -100
        assert config.num_workers == -5
        assert config.max_lob_depth == -10

    def test_zero_values(self):
        """Test handling of zero values."""
        config = ProcessingConfig(
            event_buffer_size=0,
            batch_size=0,
            num_workers=0,
            max_lob_depth=0,
        )

        assert config.event_buffer_size == 0
        assert config.batch_size == 0
        assert config.num_workers == 0
        assert config.max_lob_depth == 0
