"""Tests for ITCH 2.0 message reader functionality."""

import gzip
import tempfile
import pytest
from pathlib import Path

from meatpy.itch2.itch2_message_reader import ITCH2MessageReader
from meatpy.itch2.itch2_market_message import (
    SystemEventMessage,
    AddOrderMessage,
    OrderExecutedMessage,
)


class TestITCH2MessageReader:
    """Test the ITCH2MessageReader class."""

    def create_test_data(self) -> bytes:
        """Create test ITCH 2.0 data with a few messages."""
        lines = [
            b"12345678SO",  # System event - Start of messages
            b"12345679A000000001B000100AAPL  0000150000Y",  # Add order
            b"12345680E000000001000050000000001",  # Order executed
        ]
        return b"\n".join(lines) + b"\n"

    def test_read_file_uncompressed(self):
        """Test reading uncompressed ITCH 2.0 file."""
        test_data = self.create_test_data()

        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as temp_file:
            temp_file.write(test_data)
            temp_file.flush()

            reader = ITCH2MessageReader()
            messages = list(reader.read_file(temp_file.name))

            assert len(messages) == 3
            assert isinstance(messages[0], SystemEventMessage)
            assert isinstance(messages[1], AddOrderMessage)
            assert isinstance(messages[2], OrderExecutedMessage)

            # Check first message details
            assert messages[0].event_code == b"O"
            assert messages[0].timestamp == 12345678

            # Check second message details
            assert messages[1].side == b"B"
            assert messages[1].shares == 100
            assert messages[1].price == 150000

    def test_read_file_gzip_compressed(self):
        """Test reading gzip compressed ITCH 2.0 file."""
        test_data = self.create_test_data()

        with tempfile.NamedTemporaryFile(suffix=".gz", delete=False) as temp_file:
            with gzip.open(temp_file.name, "wb") as gz_file:
                gz_file.write(test_data)

            reader = ITCH2MessageReader()
            messages = list(reader.read_file(temp_file.name))

            assert len(messages) == 3
            assert isinstance(messages[0], SystemEventMessage)
            assert isinstance(messages[1], AddOrderMessage)

    def test_context_manager_usage(self):
        """Test using the reader as a context manager."""
        test_data = self.create_test_data()

        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as temp_file:
            temp_file.write(test_data)
            temp_file.flush()

            messages = []
            with ITCH2MessageReader(temp_file.name) as reader:
                for message in reader:
                    messages.append(message)

            assert len(messages) == 3

    def test_context_manager_without_file_path(self):
        """Test context manager error when no file path provided."""
        reader = ITCH2MessageReader()

        with pytest.raises(ValueError, match="No file_path provided"):
            with reader:
                pass

    def test_iterator_without_context_manager(self):
        """Test iterator error when not used as context manager."""
        reader = ITCH2MessageReader()

        with pytest.raises(
            RuntimeError, match="Reader must be used as a context manager"
        ):
            next(iter(reader))

    def test_empty_file(self):
        """Test reading an empty file."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as temp_file:
            pass

        reader = ITCH2MessageReader()
        messages = list(reader.read_file(temp_file.name))

        assert len(messages) == 0

    def test_skip_empty_lines(self):
        """Test that empty lines are skipped."""
        lines = [
            b"12345678SO",
            b"",  # Empty line
            b"12345679A000000001B000100AAPL  0000150000Y",
            b"",  # Empty line
        ]
        test_data = b"\n".join(lines) + b"\n"

        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as temp_file:
            temp_file.write(test_data)
            temp_file.flush()

            reader = ITCH2MessageReader()
            messages = list(reader.read_file(temp_file.name))

            assert len(messages) == 2

    def test_pathlib_path_support(self):
        """Test that Path objects are supported."""
        test_data = self.create_test_data()

        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as temp_file:
            temp_file.write(test_data)
            temp_file.flush()

            file_path = Path(temp_file.name)

            reader = ITCH2MessageReader()
            messages = list(reader.read_file(file_path))

            assert len(messages) == 3

    def test_large_file_handling(self):
        """Test reading with many messages."""
        lines = []
        for i in range(100):
            timestamp = 12345678 + i
            lines.append(f"{timestamp:08d}SO".encode())

        test_data = b"\n".join(lines) + b"\n"

        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as temp_file:
            temp_file.write(test_data)
            temp_file.flush()

            reader = ITCH2MessageReader()
            messages = list(reader.read_file(temp_file.name))

            assert len(messages) == 100
            for i, msg in enumerate(messages):
                assert msg.timestamp == 12345678 + i

    def test_carriage_return_handling(self):
        """Test handling of Windows-style line endings."""
        lines = [
            b"12345678SO",
            b"12345679A000000001B000100AAPL  0000150000Y",
        ]
        test_data = b"\r\n".join(lines) + b"\r\n"

        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as temp_file:
            temp_file.write(test_data)
            temp_file.flush()

            reader = ITCH2MessageReader()
            messages = list(reader.read_file(temp_file.name))

            assert len(messages) == 2
