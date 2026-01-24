"""Tests for ITCH 4.0 message reader functionality."""

import gzip
import struct
import tempfile
import pytest
from pathlib import Path

from meatpy.itch4.itch4_message_reader import ITCH4MessageReader
from meatpy.itch4.itch4_market_message import (
    SecondsMessage,
    SystemEventMessage,
    AddOrderMessage,
)


class TestITCH4MessageReader:
    """Test the ITCH4MessageReader class."""

    def create_test_data(self) -> bytes:
        """Create test ITCH 4.0 data with a few messages."""
        messages_data = b""

        # Create a seconds message: T(1) + seconds(4) = 5 bytes
        seconds_msg = struct.pack("!cI", b"T", 12345)
        messages_data += b"\x00"  # Start byte
        messages_data += bytes([len(seconds_msg)])  # Length
        messages_data += seconds_msg

        # Create a system event message: S(1) + timestamp(4) + event_code(1) = 6 bytes
        system_msg = struct.pack("!cIc", b"S", 12346, b"O")
        messages_data += b"\x00"  # Start byte
        messages_data += bytes([len(system_msg)])  # Length
        messages_data += system_msg

        # Create an add order message: A(1) + timestamp(4) + order_ref(8) + side(1) + shares(4) + stock(6) + price(4) = 28 bytes
        add_msg = struct.pack(
            "!cIQcI6sI", b"A", 12347, 999, b"B", 100, b"AAPL  ", 150000
        )
        messages_data += b"\x00"  # Start byte
        messages_data += bytes([len(add_msg)])  # Length
        messages_data += add_msg

        return messages_data

    def test_read_file_uncompressed(self):
        """Test reading uncompressed ITCH 4.0 file."""
        test_data = self.create_test_data()

        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(test_data)
            temp_file.flush()

            reader = ITCH4MessageReader()
            messages = list(reader.read_file(temp_file.name))

            assert len(messages) == 3
            assert isinstance(messages[0], SecondsMessage)
            assert isinstance(messages[1], SystemEventMessage)
            assert isinstance(messages[2], AddOrderMessage)

            # Check first message details
            assert messages[0].seconds == 12345

            # Check second message details
            assert messages[1].event_code == b"O"
            assert messages[1].timestamp == 12346

            # Check third message details
            assert messages[2].side == b"B"
            assert messages[2].shares == 100
            assert messages[2].price == 150000

    def test_read_file_gzip_compressed(self):
        """Test reading gzip compressed ITCH 4.0 file."""
        test_data = self.create_test_data()

        with tempfile.NamedTemporaryFile(suffix=".gz", delete=False) as temp_file:
            with gzip.open(temp_file.name, "wb") as gz_file:
                gz_file.write(test_data)

            reader = ITCH4MessageReader()
            messages = list(reader.read_file(temp_file.name))

            assert len(messages) == 3
            assert isinstance(messages[0], SecondsMessage)
            assert isinstance(messages[1], SystemEventMessage)

    def test_context_manager_usage(self):
        """Test using the reader as a context manager."""
        test_data = self.create_test_data()

        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(test_data)
            temp_file.flush()

            messages = []
            with ITCH4MessageReader(temp_file.name) as reader:
                for message in reader:
                    messages.append(message)

            assert len(messages) == 3
            assert isinstance(messages[0], SecondsMessage)
            assert isinstance(messages[1], SystemEventMessage)
            assert isinstance(messages[2], AddOrderMessage)

    def test_context_manager_without_file_path(self):
        """Test context manager error when no file path provided."""
        reader = ITCH4MessageReader()

        with pytest.raises(ValueError, match="No file_path provided"):
            with reader:
                pass

    def test_iterator_without_context_manager(self):
        """Test iterator error when not used as context manager."""
        reader = ITCH4MessageReader()

        with pytest.raises(
            RuntimeError, match="Reader must be used as a context manager"
        ):
            next(iter(reader))

    def test_empty_file(self):
        """Test reading an empty file."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            pass

        reader = ITCH4MessageReader()
        messages = list(reader.read_file(temp_file.name))

        assert len(messages) == 0

    def test_invalid_message_format(self):
        """Test handling of invalid message format."""
        # Create data with invalid start byte
        invalid_data = b"\x01\x10" + b"A" * 16  # Start byte should be 0x00

        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(invalid_data)
            temp_file.flush()

            reader = ITCH4MessageReader()

            with pytest.raises(Exception):  # Should raise InvalidMessageFormatError
                list(reader.read_file(temp_file.name))

    def test_large_buffer_handling(self):
        """Test reading with large amounts of data to test buffer management."""
        messages_data = b""

        for i in range(100):  # Create 100 messages
            msg = struct.pack("!cI", b"T", 12345 + i)
            messages_data += b"\x00"
            messages_data += bytes([len(msg)])
            messages_data += msg

        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(messages_data)
            temp_file.flush()

            reader = ITCH4MessageReader()
            messages = list(reader.read_file(temp_file.name))

            assert len(messages) == 100

            # Check that all messages are correct
            for i, message in enumerate(messages):
                assert isinstance(message, SecondsMessage)
                assert message.seconds == 12345 + i

    def test_incomplete_message_at_end(self):
        """Test handling of incomplete message at end of file."""
        # Create one complete message followed by incomplete data
        complete_msg = struct.pack("!cI", b"T", 12345)
        complete_data = b"\x00" + bytes([len(complete_msg)]) + complete_msg
        incomplete_data = b"\x00\x10" + b"A" * 5  # Claims 16 bytes but only has 5

        test_data = complete_data + incomplete_data

        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(test_data)
            temp_file.flush()

            reader = ITCH4MessageReader()
            messages = list(reader.read_file(temp_file.name))

            # Should only get the complete message
            assert len(messages) == 1
            assert isinstance(messages[0], SecondsMessage)

    def test_pathlib_path_support(self):
        """Test that Path objects are supported."""
        test_data = self.create_test_data()

        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(test_data)
            temp_file.flush()

            # Use Path object instead of string
            file_path = Path(temp_file.name)

            reader = ITCH4MessageReader()
            messages = list(reader.read_file(file_path))

            assert len(messages) == 3
            assert isinstance(messages[0], SecondsMessage)
            assert isinstance(messages[1], SystemEventMessage)
            assert isinstance(messages[2], AddOrderMessage)
