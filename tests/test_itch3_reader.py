"""Tests for ITCH 3.0 message reader functionality."""

import gzip
import tempfile
import pytest
from pathlib import Path

from meatpy.itch3.itch3_message_reader import ITCH3MessageReader
from meatpy.itch3.itch3_market_message import (
    SecondsMessage,
    MillisecondsMessage,
    SystemEventMessage,
    AddOrderMessage,
)


class TestITCH3MessageReader:
    """Test the ITCH3MessageReader class."""

    def create_test_data(self) -> bytes:
        """Create test ITCH 3.0 data with a few messages."""
        lines = [
            b"T12345",  # Seconds message
            b"M123",  # Milliseconds message
            b"SO",  # System event - Start of messages
            b"A000000001B000100AAPL  0000150000",  # Add order
        ]
        return b"\n".join(lines) + b"\n"

    def test_read_file_uncompressed(self):
        """Test reading uncompressed ITCH 3.0 file."""
        test_data = self.create_test_data()

        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as temp_file:
            temp_file.write(test_data)
            temp_file.flush()

            reader = ITCH3MessageReader()
            messages = list(reader.read_file(temp_file.name))

            assert len(messages) == 4
            assert isinstance(messages[0], SecondsMessage)
            assert isinstance(messages[1], MillisecondsMessage)
            assert isinstance(messages[2], SystemEventMessage)
            assert isinstance(messages[3], AddOrderMessage)

            # Check message details
            assert messages[0].seconds == 12345
            assert messages[1].milliseconds == 123
            assert messages[2].event_code == b"O"
            assert messages[3].order_ref == 1

    def test_read_file_gzip_compressed(self):
        """Test reading gzip compressed ITCH 3.0 file."""
        test_data = self.create_test_data()

        with tempfile.NamedTemporaryFile(suffix=".gz", delete=False) as temp_file:
            with gzip.open(temp_file.name, "wb") as gz_file:
                gz_file.write(test_data)

            reader = ITCH3MessageReader()
            messages = list(reader.read_file(temp_file.name))

            assert len(messages) == 4
            assert isinstance(messages[0], SecondsMessage)

    def test_context_manager_usage(self):
        """Test using the reader as a context manager."""
        test_data = self.create_test_data()

        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as temp_file:
            temp_file.write(test_data)
            temp_file.flush()

            messages = []
            with ITCH3MessageReader(temp_file.name) as reader:
                for message in reader:
                    messages.append(message)

            assert len(messages) == 4

    def test_context_manager_without_file_path(self):
        """Test context manager error when no file path provided."""
        reader = ITCH3MessageReader()

        with pytest.raises(ValueError, match="No file_path provided"):
            with reader:
                pass

    def test_iterator_without_context_manager(self):
        """Test iterator error when not used as context manager."""
        reader = ITCH3MessageReader()

        with pytest.raises(
            RuntimeError, match="Reader must be used as a context manager"
        ):
            next(iter(reader))

    def test_empty_file(self):
        """Test reading an empty file."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as temp_file:
            pass

        reader = ITCH3MessageReader()
        messages = list(reader.read_file(temp_file.name))

        assert len(messages) == 0

    def test_skip_empty_lines(self):
        """Test that empty lines are skipped."""
        lines = [
            b"T12345",
            b"",  # Empty line
            b"M123",
            b"",  # Empty line
        ]
        test_data = b"\n".join(lines) + b"\n"

        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as temp_file:
            temp_file.write(test_data)
            temp_file.flush()

            reader = ITCH3MessageReader()
            messages = list(reader.read_file(temp_file.name))

            assert len(messages) == 2

    def test_pathlib_path_support(self):
        """Test that Path objects are supported."""
        test_data = self.create_test_data()

        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as temp_file:
            temp_file.write(test_data)
            temp_file.flush()

            file_path = Path(temp_file.name)

            reader = ITCH3MessageReader()
            messages = list(reader.read_file(file_path))

            assert len(messages) == 4

    def test_large_file_handling(self):
        """Test reading with many messages."""
        lines = []
        for i in range(100):
            lines.append(f"T{i:05d}".encode())
            lines.append(f"M{i % 1000:03d}".encode())

        test_data = b"\n".join(lines) + b"\n"

        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as temp_file:
            temp_file.write(test_data)
            temp_file.flush()

            reader = ITCH3MessageReader()
            messages = list(reader.read_file(temp_file.name))

            assert len(messages) == 200

    def test_carriage_return_handling(self):
        """Test handling of Windows-style line endings."""
        lines = [
            b"T12345",
            b"M123",
        ]
        test_data = b"\r\n".join(lines) + b"\r\n"

        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as temp_file:
            temp_file.write(test_data)
            temp_file.flush()

            reader = ITCH3MessageReader()
            messages = list(reader.read_file(temp_file.name))

            assert len(messages) == 2
