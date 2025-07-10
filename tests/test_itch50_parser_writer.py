"""Tests for ITCH50MessageReader and ITCH50Writer classes."""

import struct
import tempfile
from pathlib import Path

import pytest

from meatpy.itch50 import ITCH50MessageReader, ITCH50Writer, SystemEventMessage


def test_itch50_parser_initialization():
    """Test ITCH50MessageReader initialization."""
    parser = ITCH50MessageReader()
    assert parser.file_path is None

    parser = ITCH50MessageReader("test_file.itch")
    assert parser.file_path == Path("test_file.itch")


def test_itch50_writer_initialization():
    """Test ITCH50Writer initialization."""
    with tempfile.NamedTemporaryFile() as tmp:
        writer = ITCH50Writer(output_path=tmp.name)
        assert writer.symbols is None
        assert writer.output_path == Path(tmp.name)
        assert writer.message_buffer == 2000
        assert writer.compress is False
        assert writer.compression_type == "gzip"

        writer = ITCH50Writer(
            symbols=[b"AAPL   "],
            output_path=tmp.name,
            message_buffer=1000,
            compress=True,
            compression_type="bzip2",
        )
        assert writer.symbols == [b"AAPL   "]
        assert writer.message_buffer == 1000
        assert writer.compress is True
        assert writer.compression_type == "bzip2"


def test_itch50_writer_context_manager():
    """Test ITCH50Writer as context manager."""
    with tempfile.NamedTemporaryFile() as tmp:
        with ITCH50Writer(output_path=tmp.name) as writer:
            assert writer.output_path == Path(tmp.name)
            # Should not raise any exceptions


def test_itch50_writer_process_message():
    """Test ITCH50Writer message processing."""
    with tempfile.NamedTemporaryFile() as tmp:
        writer = ITCH50Writer(output_path=tmp.name)

        # Create a proper system event message
        # Format: type(1) + stock_locate(2) + tracking_number(2) + ts1(4) + ts2(4) + code(1) = 12 bytes
        payload = struct.pack("!HHHIc", 1, 2, 0, 0, b"C")
        message_data = b"S" + payload
        message = SystemEventMessage(message_data)

        # Process the message
        writer.process_message(message)
        assert writer.message_count == 1

        # Flush and close
        writer.flush()
        writer.close()


def test_itch50_parser_compression_detection():
    """Test ITCH50MessageReader compression detection."""
    parser = ITCH50MessageReader()

    # Test with a non-existent file (should not crash)
    with pytest.raises(FileNotFoundError):
        list(parser.read_file("nonexistent_file.bin"))


def test_itch50_parser_context_manager():
    """Test ITCH50MessageReader as context manager."""
    parser = ITCH50MessageReader("test_file.itch")

    # Test that context manager methods exist
    assert hasattr(parser, "__enter__")
    assert hasattr(parser, "__exit__")

    # Test context manager usage (should raise FileNotFoundError for non-existent file)
    with pytest.raises(FileNotFoundError):
        with ITCH50MessageReader("nonexistent_file.itch") as parser:
            pass


def test_itch50_parser_natural_interface():
    """Test ITCH50MessageReader natural interface with file_path in constructor."""
    # Test initialization with file path
    parser = ITCH50MessageReader("test_file.itch")
    assert parser.file_path == Path("test_file.itch")

    # Test initialization with file path (no filters in new interface)
    parser = ITCH50MessageReader("test_file.itch")
    assert parser.file_path == Path("test_file.itch")


def test_itch50_parser_natural_interface_context_manager():
    """Test ITCH50MessageReader natural interface as context manager."""
    # Test that context manager methods exist
    parser = ITCH50MessageReader("test_file.itch")
    assert hasattr(parser, "__enter__")
    assert hasattr(parser, "__exit__")
    assert hasattr(parser, "__iter__")

    # Test that it raises error when no file_path is provided
    parser_no_path = ITCH50MessageReader()
    with pytest.raises(ValueError, match="No file_path provided"):
        with parser_no_path:
            pass


def test_itch50_parser_legacy_interface():
    """Test ITCH50MessageReader legacy interface still works."""
    # Test initialization without file path
    parser = ITCH50MessageReader()
    assert parser.file_path is None

    # Test that read_file method exists
    assert hasattr(parser, "read_file")
