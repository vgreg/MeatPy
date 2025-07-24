"""Tests for ITCH 4.1 message reader functionality."""

import gzip
import tempfile
import pytest
from pathlib import Path

from meatpy.itch41.itch41_message_reader import ITCH41MessageReader
from meatpy.itch41.itch41_market_message import SystemEventMessage, AddOrderMessage


class TestITCH41MessageReader:
    """Test the ITCH41MessageReader class."""

    def create_test_data(self) -> bytes:
        """Create test ITCH data with a few messages."""
        messages_data = b""

        # Create a system event message
        system_msg = SystemEventMessage()
        system_msg.timestamp = 12345 * 1_000_000_000  # Convert to nanoseconds
        system_msg.event_code = b"O"
        system_bytes = system_msg.to_bytes()

        # Add ITCH frame (length byte + message)
        messages_data += b"\x00"  # Start byte
        messages_data += bytes([len(system_bytes)])  # Length
        messages_data += system_bytes

        # Create an add order message
        order_msg = AddOrderMessage()
        order_msg.timestamp = 12346 * 1_000_000_000  # Convert to nanoseconds
        order_msg.order_ref = 999
        order_msg.side = b"B"
        order_msg.shares = 100
        order_msg.stock = b"AAPL    "
        order_msg.price = 15000
        order_bytes = order_msg.to_bytes()

        # Add ITCH frame
        messages_data += b"\x00"  # Start byte
        messages_data += bytes([len(order_bytes)])  # Length
        messages_data += order_bytes

        return messages_data

    def test_read_file_uncompressed(self):
        """Test reading uncompressed ITCH file."""
        test_data = self.create_test_data()

        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(test_data)
            temp_file.flush()

            reader = ITCH41MessageReader()
            messages = list(reader.read_file(temp_file.name))

            assert len(messages) == 2
            assert isinstance(messages[0], SystemEventMessage)
            assert isinstance(messages[1], AddOrderMessage)

            # Check first message details
            assert messages[0].event_code == b"O"
            assert messages[0].timestamp == 12345 * 1_000_000_000

            # Check second message details
            assert messages[1].side == b"B"
            assert messages[1].shares == 100
            assert messages[1].price == 15000
            assert messages[1].timestamp == 12346 * 1_000_000_000

    def test_read_file_gzip_compressed(self):
        """Test reading gzip compressed ITCH file."""
        test_data = self.create_test_data()

        with tempfile.NamedTemporaryFile(suffix=".gz", delete=False) as temp_file:
            with gzip.open(temp_file.name, "wb") as gz_file:
                gz_file.write(test_data)

            reader = ITCH41MessageReader()
            messages = list(reader.read_file(temp_file.name))

            assert len(messages) == 2
            assert isinstance(messages[0], SystemEventMessage)
            assert isinstance(messages[1], AddOrderMessage)

    def test_context_manager_usage(self):
        """Test using the reader as a context manager."""
        test_data = self.create_test_data()

        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(test_data)
            temp_file.flush()

            messages = []
            with ITCH41MessageReader(temp_file.name) as reader:
                for message in reader:
                    messages.append(message)

            assert len(messages) == 2
            assert isinstance(messages[0], SystemEventMessage)
            assert isinstance(messages[1], AddOrderMessage)

    def test_context_manager_without_file_path(self):
        """Test context manager error when no file path provided."""
        reader = ITCH41MessageReader()

        with pytest.raises(ValueError, match="No file_path provided"):
            with reader:
                pass

    def test_iterator_without_context_manager(self):
        """Test iterator error when not used as context manager."""
        reader = ITCH41MessageReader()

        with pytest.raises(
            RuntimeError, match="Reader must be used as a context manager"
        ):
            next(iter(reader))

    def test_empty_file(self):
        """Test reading an empty file."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            # File is empty
            pass

        reader = ITCH41MessageReader()
        messages = list(reader.read_file(temp_file.name))

        assert len(messages) == 0

    def test_invalid_message_format(self):
        """Test handling of invalid message format."""
        # Create data with invalid start byte
        invalid_data = b"\x01\x10" + b"A" * 16  # Start byte should be 0x00

        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(invalid_data)
            temp_file.flush()

            reader = ITCH41MessageReader()

            with pytest.raises(Exception):  # Should raise InvalidMessageFormatError
                list(reader.read_file(temp_file.name))

    def test_large_buffer_handling(self):
        """Test reading with large amounts of data to test buffer management."""
        # Create many messages to test buffer refilling
        messages_data = b""

        for i in range(100):  # Create 100 messages
            msg = SystemEventMessage()
            msg.timestamp = (12345 + i) * 1_000_000_000  # Convert to nanoseconds
            msg.event_code = b"O"
            msg_bytes = msg.to_bytes()

            messages_data += b"\x00"
            messages_data += bytes([len(msg_bytes)])
            messages_data += msg_bytes

        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(messages_data)
            temp_file.flush()

            reader = ITCH41MessageReader()
            messages = list(reader.read_file(temp_file.name))

            assert len(messages) == 100

            # Check that all messages are correct
            for i, message in enumerate(messages):
                assert isinstance(message, SystemEventMessage)
                assert message.timestamp == (12345 + i) * 1_000_000_000
                assert message.event_code == b"O"

    def test_incomplete_message_at_end(self):
        """Test handling of incomplete message at end of file."""
        # Create one complete message followed by incomplete data
        msg = SystemEventMessage()
        msg.timestamp = 12345 * 1_000_000_000  # Convert to nanoseconds
        msg.event_code = b"O"
        msg_bytes = msg.to_bytes()

        complete_data = b"\x00" + bytes([len(msg_bytes)]) + msg_bytes
        incomplete_data = b"\x00\x10" + b"A" * 5  # Claims 16 bytes but only has 5

        test_data = complete_data + incomplete_data

        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(test_data)
            temp_file.flush()

            reader = ITCH41MessageReader()
            messages = list(reader.read_file(temp_file.name))

            # Should only get the complete message
            assert len(messages) == 1
            assert isinstance(messages[0], SystemEventMessage)

    def test_pathlib_path_support(self):
        """Test that Path objects are supported."""
        test_data = self.create_test_data()

        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(test_data)
            temp_file.flush()

            # Use Path object instead of string
            file_path = Path(temp_file.name)

            reader = ITCH41MessageReader()
            messages = list(reader.read_file(file_path))

            assert len(messages) == 2
            assert isinstance(messages[0], SystemEventMessage)
            assert isinstance(messages[1], AddOrderMessage)
