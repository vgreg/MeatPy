"""IEX DEEP PCAP file reader with generator interface.

This module provides the IEXDEEPMessageReader class, which reads IEX DEEP market data
from PCAP and PCAP-NG files and yields structured message objects one at a time.

IEX DEEP data is delivered via IEX Transport Protocol (IEX-TP) encapsulated in PCAP format.
"""

from __future__ import annotations

import struct
from pathlib import Path
from typing import Generator, Optional

from ..message_reader import InvalidMessageFormatError, MessageReader
from .iex_deep_market_message import IEXDEEPMarketMessage


# PCAP file format constants
PCAP_MAGIC_NUMBER = 0xA1B2C3D4  # Standard pcap magic (microsecond resolution)
PCAP_MAGIC_NUMBER_NS = 0xA1B23C4D  # Nanosecond resolution pcap magic
PCAP_MAGIC_NUMBER_SWAPPED = 0xD4C3B2A1  # Byte-swapped standard
PCAP_MAGIC_NUMBER_NS_SWAPPED = 0x4D3CB2A1  # Byte-swapped nanosecond
PCAP_GLOBAL_HEADER_SIZE = 24
PCAP_PACKET_HEADER_SIZE = 16

# PCAP-NG format constants
PCAPNG_SECTION_HEADER_BLOCK = 0x0A0D0D0A
PCAPNG_INTERFACE_DESC_BLOCK = 0x00000001
PCAPNG_ENHANCED_PACKET_BLOCK = 0x00000006
PCAPNG_SIMPLE_PACKET_BLOCK = 0x00000003

# IEX-TP constants
IEX_TP_HEADER_SIZE = 40
IEX_DEEP_MESSAGE_PROTOCOL_ID = 0x8004


class IEXDEEPMessageReader(MessageReader):
    """A market message reader for IEX DEEP data in PCAP/PCAP-NG format.

    This reader reads IEX DEEP PCAP or PCAP-NG files and yields message objects
    one at a time, supporting automatic detection of compressed files
    (gzip, bzip2, xz, zip).

    The PCAP files contain IEX-TP transport protocol packets with IEX DEEP messages.

    Attributes:
        file_path: Path to the PCAP file to read
        _file_handle: Internal file handle when used as context manager
    """

    def __init__(
        self,
        file_path: Optional[Path | str] = None,
    ) -> None:
        """Initialize the IEXDEEPMessageReader.

        Args:
            file_path: Path to the PCAP file to read (optional if using read_file method)
        """
        super().__init__(file_path)

    def __iter__(self) -> Generator[IEXDEEPMarketMessage, None, None]:
        """Make the reader iterable when used as a context manager."""
        if self._file_handle is None:
            raise RuntimeError(
                "Reader must be used as a context manager to be iterable"
            )
        yield from self._read_messages(self._file_handle)

    def read_file(
        self, file_path: Path | str
    ) -> Generator[IEXDEEPMarketMessage, None, None]:
        """Parse an IEX DEEP PCAP file and yield messages one at a time.

        Args:
            file_path: Path to the PCAP file to read

        Yields:
            IEXDEEPMarketMessage objects
        """
        file_path = Path(file_path)
        with self._open_file(file_path) as file:
            yield from self._read_messages(file)

    def _read_messages(self, file) -> Generator[IEXDEEPMarketMessage, None, None]:
        """Internal method to read messages from an open file handle.

        Args:
            file: Open file handle to read from

        Yields:
            IEXDEEPMarketMessage objects
        """
        # Read first 4 bytes to determine file format
        magic_bytes = file.read(4)
        if len(magic_bytes) < 4:
            raise InvalidMessageFormatError("File too short")

        magic_number = struct.unpack("<I", magic_bytes)[0]

        # Check for PCAP-NG format (Section Header Block)
        if magic_number == PCAPNG_SECTION_HEADER_BLOCK:
            # Seek back and read as PCAP-NG
            file.seek(0)
            yield from self._read_pcapng(file)
        elif magic_number in (
            PCAP_MAGIC_NUMBER,
            PCAP_MAGIC_NUMBER_NS,
            PCAP_MAGIC_NUMBER_SWAPPED,
            PCAP_MAGIC_NUMBER_NS_SWAPPED,
        ):
            # Seek back and read as standard PCAP
            file.seek(0)
            yield from self._read_pcap(file)
        else:
            raise InvalidMessageFormatError(
                f"Unknown file format, magic number: {magic_number:#x}"
            )

    def _read_pcap(self, file) -> Generator[IEXDEEPMarketMessage, None, None]:
        """Read standard PCAP format.

        Args:
            file: Open file handle

        Yields:
            IEXDEEPMarketMessage objects
        """
        # Read global header
        global_header = file.read(PCAP_GLOBAL_HEADER_SIZE)
        if len(global_header) < PCAP_GLOBAL_HEADER_SIZE:
            raise InvalidMessageFormatError("PCAP file too short for global header")

        magic_number = struct.unpack("<I", global_header[0:4])[0]

        # Determine byte order
        if magic_number in (PCAP_MAGIC_NUMBER, PCAP_MAGIC_NUMBER_NS):
            byte_order = "<"
        else:
            byte_order = ">"

        # Read packets
        while True:
            packet_header = file.read(PCAP_PACKET_HEADER_SIZE)
            if len(packet_header) < PCAP_PACKET_HEADER_SIZE:
                break

            ts_sec, ts_usec, incl_len, orig_len = struct.unpack(
                f"{byte_order}IIII", packet_header
            )

            packet_data = file.read(incl_len)
            if len(packet_data) < incl_len:
                break

            yield from self._parse_packet(packet_data)

    def _read_pcapng(self, file) -> Generator[IEXDEEPMarketMessage, None, None]:
        """Read PCAP-NG format.

        Args:
            file: Open file handle

        Yields:
            IEXDEEPMarketMessage objects
        """
        byte_order = "<"  # Will be determined from Section Header Block

        while True:
            # Read block header: type(4) + length(4)
            block_header = file.read(8)
            if len(block_header) < 8:
                break

            block_type, block_length = struct.unpack(f"{byte_order}II", block_header)

            # Handle Section Header Block (determines byte order)
            if block_type == PCAPNG_SECTION_HEADER_BLOCK:
                # Read the rest of the minimum block (need byte order magic)
                # Block: type(4) + length(4) + byte_order_magic(4) + version(4) + section_len(8)
                shb_data = file.read(block_length - 8)
                if len(shb_data) < 12:
                    break

                byte_order_magic = struct.unpack("<I", shb_data[0:4])[0]
                if byte_order_magic == 0x1A2B3C4D:
                    byte_order = "<"
                elif byte_order_magic == 0x4D3C2B1A:
                    byte_order = ">"
                continue

            # Read the rest of the block
            remaining = block_length - 8
            if remaining <= 0:
                continue

            block_data = file.read(remaining)
            if len(block_data) < remaining:
                break

            # Handle Enhanced Packet Block
            if block_type == PCAPNG_ENHANCED_PACKET_BLOCK:
                # EPB format: interface_id(4) + timestamp_high(4) + timestamp_low(4) +
                #             captured_len(4) + original_len(4) + packet_data + padding + block_length(4)
                if len(block_data) < 20:
                    continue

                interface_id, ts_high, ts_low, captured_len, original_len = (
                    struct.unpack(f"{byte_order}IIIII", block_data[:20])
                )

                packet_data = block_data[20 : 20 + captured_len]
                if len(packet_data) >= captured_len:
                    yield from self._parse_packet(packet_data)

            # Handle Simple Packet Block
            elif block_type == PCAPNG_SIMPLE_PACKET_BLOCK:
                # SPB format: original_len(4) + packet_data + padding + block_length(4)
                if len(block_data) < 4:
                    continue

                _ = struct.unpack(f"{byte_order}I", block_data[:4])[0]  # original_len
                # Captured length = block_length - 16 (headers) - padding
                packet_data = block_data[4:-4]  # Exclude trailing block_length
                if len(packet_data) > 0:
                    yield from self._parse_packet(packet_data)

    def _parse_packet(
        self, packet_data: bytes
    ) -> Generator[IEXDEEPMarketMessage, None, None]:
        """Parse IEX DEEP messages from a network packet.

        Args:
            packet_data: Raw packet data

        Yields:
            IEXDEEPMarketMessage objects
        """
        # Try to find IEX-TP header in the packet
        iex_tp_offset = self._find_iex_tp_header(packet_data)
        if iex_tp_offset < 0:
            return  # Not an IEX DEEP packet

        # Parse IEX-TP header
        iex_tp_data = packet_data[iex_tp_offset:]
        if len(iex_tp_data) < IEX_TP_HEADER_SIZE:
            return  # Truncated IEX-TP header

        # IEX-TP header format (40 bytes, little endian):
        # version(1) + reserved(1) + message_protocol_id(2) + channel_id(4) +
        # session_id(4) + payload_length(2) + message_count(2) +
        # stream_offset(8) + first_message_seq_num(8) + send_time(8)
        (
            version,
            reserved,
            message_protocol_id,
            channel_id,
            session_id,
            payload_length,
            message_count,
            stream_offset,
            first_message_seq_num,
            send_time,
        ) = struct.unpack("<BBHIIHHQQQ", iex_tp_data[:IEX_TP_HEADER_SIZE])

        # Verify this is IEX DEEP
        if message_protocol_id != IEX_DEEP_MESSAGE_PROTOCOL_ID:
            return

        # Parse messages from payload
        payload = iex_tp_data[IEX_TP_HEADER_SIZE:]
        offset = 0

        for _ in range(message_count):
            if offset + 2 > len(payload):
                break

            # Each message is prefixed with 2-byte length
            msg_len = struct.unpack("<H", payload[offset : offset + 2])[0]
            offset += 2

            if offset + msg_len > len(payload):
                break

            msg_data = payload[offset : offset + msg_len]
            offset += msg_len

            if len(msg_data) > 0:
                try:
                    message = IEXDEEPMarketMessage.from_bytes(msg_data)
                    yield message
                except Exception:
                    # Skip malformed messages
                    continue

    def _find_iex_tp_header(self, packet_data: bytes) -> int:
        """Find the offset of the IEX-TP header in packet data.

        Args:
            packet_data: Raw packet data

        Returns:
            Offset to IEX-TP header, or -1 if not found
        """
        # Common offsets to check:
        # - 42: Ethernet(14) + IP(20) + UDP(8)
        # - 0: Raw IEX-TP (no encapsulation)
        # - 14: Ethernet only
        # - 34: Ethernet + IP (no UDP)

        offsets_to_try = [42, 0, 14, 34]

        for offset in offsets_to_try:
            if offset + IEX_TP_HEADER_SIZE <= len(packet_data):
                try:
                    protocol_id = struct.unpack(
                        "<H", packet_data[offset + 2 : offset + 4]
                    )[0]
                    if protocol_id == IEX_DEEP_MESSAGE_PROTOCOL_ID:
                        return offset
                except Exception:
                    continue

        return -1
