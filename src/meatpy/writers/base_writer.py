"""Base writer interface for exporting market data.

This module provides the abstract base class for all data writers, defining
a common interface for writing market data to various file formats.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


class DataWriter(ABC):
    """Abstract base class for data writers.

    This class defines the common interface that all data writers must implement
    for writing market data to various file formats.

    Attributes:
        output_path: Path to the output file
        buffer_size: Number of records to buffer before writing
        compression: Compression type to use (format-specific)
    """

    def __init__(
        self,
        output_path: Union[Path, str],
        buffer_size: int = 1000,
        compression: Optional[str] = None,
    ):
        """Initialize the data writer.

        Args:
            output_path: Path to the output file
            buffer_size: Number of records to buffer before writing
            compression: Compression type to use (format-specific)
        """
        self.output_path = Path(output_path)
        self.buffer_size = buffer_size
        self.compression = compression
        self._buffer: List[Any] = []
        self._schema: Optional[Dict[str, Any]] = None
        self._header_written = False

    @abstractmethod
    def write_header(self, schema: Dict[str, Any]) -> None:
        """Write the header/schema information to the file.

        Args:
            schema: Schema definition for the data
        """
        pass

    @abstractmethod
    def write_records(self, records: List[Any]) -> None:
        """Write a batch of records to the file.

        Args:
            records: List of records to write
        """
        pass

    @abstractmethod
    def append_records(self, records: List[Any]) -> None:
        """Append records to an existing file.

        Args:
            records: List of records to append
        """
        pass

    def buffer_record(self, record: Any) -> None:
        """Add a record to the buffer and write if buffer is full.

        Args:
            record: Record to buffer
        """
        self._buffer.append(record)
        if len(self._buffer) >= self.buffer_size:
            self.flush()

    def flush(self) -> None:
        """Flush all buffered records to the file."""
        if self._buffer:
            if self._header_written:
                self.append_records(self._buffer)
            else:
                self.write_records(self._buffer)
            self._buffer.clear()

    def close(self) -> None:
        """Close the writer and flush any remaining records."""
        self.flush()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def set_schema(self, schema: Dict[str, Any]) -> None:
        """Set the schema for the writer.

        Args:
            schema: Schema definition for the data
        """
        self._schema = schema
        if not self._header_written:
            self.write_header(schema)
            self._header_written = True
