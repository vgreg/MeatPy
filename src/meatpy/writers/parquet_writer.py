"""Parquet writer for exporting market data in Apache Parquet format.

This module provides the ParquetWriter class for writing market data to
Parquet files with support for schema definition, compression, and buffering.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

try:
    import pyarrow as pa
    import pyarrow.parquet as pq

    HAS_PYARROW = True
except ImportError:
    HAS_PYARROW = False
    pa = None
    pq = None

from .base_writer import DataWriter


class ParquetWriter(DataWriter):
    """Writer for Apache Parquet format files.

    This writer converts market data records to columnar format and writes
    them to Parquet files with support for compression and schema validation.

    Attributes:
        output_path: Path to the output Parquet file
        buffer_size: Number of records to buffer before writing
        compression: Compression algorithm ('snappy', 'gzip', 'brotli', 'lz4', 'zstd')
        write_index: Whether to write row group indices
    """

    def __init__(
        self,
        output_path: Union[Path, str],
        buffer_size: int = 1000,
        compression: Optional[str] = "snappy",
        write_index: bool = True,
    ):
        """Initialize the ParquetWriter.

        Args:
            output_path: Path to the output Parquet file
            buffer_size: Number of records to buffer before writing
            compression: Compression algorithm to use
            write_index: Whether to write row group indices

        Raises:
            ImportError: If pyarrow is not installed
        """
        if not HAS_PYARROW:
            raise ImportError(
                "pyarrow is required for ParquetWriter. "
                "Install it with: pip install 'meatpy[parquet]'"
            )

        super().__init__(output_path, buffer_size, compression)
        self.write_index = write_index
        self._writer = None
        self._arrow_schema = None

    def _infer_arrow_schema(self, records: List[Any]):
        """Infer Arrow schema from sample records.

        Args:
            records: Sample records to infer schema from

        Returns:
            Arrow schema for the data
        """
        if not HAS_PYARROW:
            raise ImportError("pyarrow is required for schema inference")
        if not records:
            raise ValueError("Cannot infer schema from empty records")

        sample_record = records[0]

        if isinstance(sample_record, dict):
            return self._infer_schema_from_dict(sample_record)
        elif isinstance(sample_record, (list, tuple)):
            return self._infer_schema_from_sequence(sample_record)
        else:
            raise TypeError(f"Unsupported record type: {type(sample_record)}")

    def _infer_schema_from_dict(self, sample_dict: Dict[str, Any]):
        """Infer schema from dictionary record.

        Args:
            sample_dict: Sample dictionary record

        Returns:
            Arrow schema
        """
        fields = []
        for key, value in sample_dict.items():
            if isinstance(
                value, bool
            ):  # Check bool first since bool is subclass of int
                arrow_type = pa.bool_()
            elif isinstance(value, int):
                arrow_type = pa.int64()
            elif isinstance(value, float):
                arrow_type = pa.float64()
            elif isinstance(value, str):
                arrow_type = pa.string()
            else:
                arrow_type = pa.string()  # Default to string

            fields.append(pa.field(key, arrow_type))

        return pa.schema(fields)

    def _infer_schema_from_sequence(self, sample_sequence: Union[List, tuple]):
        """Infer schema from sequence record.

        Args:
            sample_sequence: Sample sequence record

        Returns:
            Arrow schema
        """
        fields = []
        for i, value in enumerate(sample_sequence):
            if isinstance(
                value, bool
            ):  # Check bool first since bool is subclass of int
                arrow_type = pa.bool_()
            elif isinstance(value, int):
                arrow_type = pa.int64()
            elif isinstance(value, float):
                arrow_type = pa.float64()
            elif isinstance(value, str):
                arrow_type = pa.string()
            else:
                arrow_type = pa.string()  # Default to string

            fields.append(pa.field(f"column_{i}", arrow_type))

        return pa.schema(fields)

    def _records_to_table(self, records: List[Any]):
        """Convert records to Arrow table.

        Args:
            records: List of records to convert

        Returns:
            Arrow table
        """
        if not records:
            return pa.table([], schema=self._arrow_schema)

        if isinstance(records[0], dict):
            return self._dict_records_to_table(records)
        elif isinstance(records[0], (list, tuple)):
            return self._sequence_records_to_table(records)
        else:
            raise TypeError(f"Unsupported record type: {type(records[0])}")

    def _dict_records_to_table(self, records: List[Dict[str, Any]]):
        """Convert dictionary records to Arrow table.

        Args:
            records: List of dictionary records

        Returns:
            Arrow table
        """
        columns = {}
        for field in self._arrow_schema:
            column_name = field.name
            column_data = [record.get(column_name) for record in records]
            columns[column_name] = column_data

        return pa.table(columns, schema=self._arrow_schema)

    def _sequence_records_to_table(self, records: List[Union[List, tuple]]):
        """Convert sequence records to Arrow table.

        Args:
            records: List of sequence records

        Returns:
            Arrow table
        """
        num_columns = len(self._arrow_schema)
        columns = {}

        for i in range(num_columns):
            column_name = self._arrow_schema[i].name
            column_data = [record[i] if i < len(record) else None for record in records]
            columns[column_name] = column_data

        return pa.table(columns, schema=self._arrow_schema)

    def write_header(self, schema: Dict[str, Any]) -> None:
        """Write the header/schema information to the file.

        Args:
            schema: Schema definition for the data
        """
        if "arrow_schema" in schema:
            self._arrow_schema = schema["arrow_schema"]
        elif "fields" in schema:
            fields = []
            for field_name, field_type in schema["fields"].items():
                if field_type == "int64":
                    arrow_type = pa.int64()
                elif field_type == "float64":
                    arrow_type = pa.float64()
                elif field_type == "string":
                    arrow_type = pa.string()
                elif field_type == "bool":
                    arrow_type = pa.bool_()
                else:
                    arrow_type = pa.string()
                fields.append(pa.field(field_name, arrow_type))
            self._arrow_schema = pa.schema(fields)
        else:
            raise ValueError("Schema must contain 'arrow_schema' or 'fields'")

        self._schema = schema

    def write_records(self, records: List[Any]) -> None:
        """Write a batch of records to the file.

        Args:
            records: List of records to write
        """
        if not records:
            return

        if self._arrow_schema is None:
            self._arrow_schema = self._infer_arrow_schema(records)

        table = self._records_to_table(records)

        if self._writer is None:
            self._writer = pq.ParquetWriter(
                self.output_path,
                self._arrow_schema,
                compression=self.compression,
                write_statistics=True,
                use_dictionary=True,
                write_page_index=self.write_index,
            )

        self._writer.write_table(table)

    def append_records(self, records: List[Any]) -> None:
        """Append records to an existing file.

        Args:
            records: List of records to append
        """
        if not records:
            return

        table = self._records_to_table(records)

        if self._writer is None:
            raise RuntimeError("Writer not initialized. Call write_records first.")

        self._writer.write_table(table)

    def close(self) -> None:
        """Close the writer and flush any remaining records."""
        super().close()
        if self._writer is not None:
            self._writer.close()
            self._writer = None
