"""CSV writer for exporting market data in CSV format.

This module provides the CSVWriter class for writing market data to
CSV files with support for custom delimiters, headers, and compression.
"""

import csv
import gzip
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, TextIO

from .base_writer import DataWriter


class CSVWriter(DataWriter):
    """Writer for CSV format files.

    This writer converts market data records to CSV format with support
    for custom delimiters, headers, and compression.

    Attributes:
        output_path: Path to the output CSV file
        buffer_size: Number of records to buffer before writing
        compression: Whether to use gzip compression
        delimiter: Field delimiter character
        quotechar: Character used to quote fields
        lineterminator: Line terminator string
    """

    def __init__(
        self,
        output_path: Union[Path, str],
        buffer_size: int = 1000,
        compression: Optional[str] = None,
        delimiter: str = ",",
        quotechar: str = '"',
        lineterminator: str = "\n",
    ):
        """Initialize the CSVWriter.

        Args:
            output_path: Path to the output CSV file
            buffer_size: Number of records to buffer before writing
            compression: Compression type ('gzip' or None)
            delimiter: Field delimiter character
            quotechar: Character used to quote fields
            lineterminator: Line terminator string
        """
        super().__init__(output_path, buffer_size, compression)
        self.delimiter = delimiter
        self.quotechar = quotechar
        self.lineterminator = lineterminator
        self._fieldnames: Optional[List[str]] = None

    def _get_file_handle(self, mode: str = "w") -> TextIO:
        """Get a file handle with appropriate compression if needed.

        Args:
            mode: File open mode

        Returns:
            File-like object for writing
        """
        if self.compression == "gzip":
            return gzip.open(self.output_path, mode + "t", encoding="utf-8")
        else:
            return open(self.output_path, mode, encoding="utf-8")

    def _extract_fieldnames(self, records: List[Any]) -> List[str]:
        """Extract field names from sample records.

        Args:
            records: Sample records to extract field names from

        Returns:
            List of field names
        """
        if not records:
            return []

        sample_record = records[0]

        if isinstance(sample_record, dict):
            return list(sample_record.keys())
        elif isinstance(sample_record, (list, tuple)):
            return [f"column_{i}" for i in range(len(sample_record))]
        else:
            return ["value"]

    def _record_to_dict(self, record: Any) -> Dict[str, Any]:
        """Convert a record to dictionary format.

        Args:
            record: Record to convert

        Returns:
            Dictionary representation of the record
        """
        if isinstance(record, dict):
            return record
        elif isinstance(record, (list, tuple)):
            if self._fieldnames is None:
                raise ValueError("Field names not set for sequence records")
            return dict(zip(self._fieldnames, record))
        else:
            if self._fieldnames is None:
                return {"value": record}
            else:
                return {self._fieldnames[0]: record}

    def write_header(self, schema: Dict[str, Any]) -> None:
        """Write the header/schema information to the file.

        Args:
            schema: Schema definition for the data
        """
        if "fieldnames" in schema:
            self._fieldnames = schema["fieldnames"]
        elif "fields" in schema:
            self._fieldnames = list(schema["fields"].keys())
        else:
            raise ValueError("Schema must contain 'fieldnames' or 'fields'")

        self._schema = schema

        with self._get_file_handle("w") as file:
            writer = csv.DictWriter(
                file,
                fieldnames=self._fieldnames,
                delimiter=self.delimiter,
                quotechar=self.quotechar,
                lineterminator=self.lineterminator,
            )
            writer.writeheader()

    def write_records(self, records: List[Any]) -> None:
        """Write a batch of records to the file.

        Args:
            records: List of records to write
        """
        if not records:
            return

        if self._fieldnames is None:
            self._fieldnames = self._extract_fieldnames(records)

        with self._get_file_handle("w") as file:
            writer = csv.DictWriter(
                file,
                fieldnames=self._fieldnames,
                delimiter=self.delimiter,
                quotechar=self.quotechar,
                lineterminator=self.lineterminator,
            )

            if not self._header_written:
                writer.writeheader()
                self._header_written = True

            for record in records:
                dict_record = self._record_to_dict(record)
                writer.writerow(dict_record)

    def append_records(self, records: List[Any]) -> None:
        """Append records to an existing file.

        Args:
            records: List of records to append
        """
        if not records:
            return

        if self._fieldnames is None:
            raise RuntimeError("Field names not set. Call write_records first.")

        with self._get_file_handle("a") as file:
            writer = csv.DictWriter(
                file,
                fieldnames=self._fieldnames,
                delimiter=self.delimiter,
                quotechar=self.quotechar,
                lineterminator=self.lineterminator,
            )

            for record in records:
                dict_record = self._record_to_dict(record)
                writer.writerow(dict_record)

    def write_csv_header_string(self) -> str:
        """Get the CSV header as a string.

        Returns:
            CSV header string
        """
        if self._fieldnames is None:
            raise RuntimeError("Field names not set")

        return self.delimiter.join(self._fieldnames) + self.lineterminator

    def record_to_csv_string(self, record: Any) -> str:
        """Convert a record to CSV string format.

        Args:
            record: Record to convert

        Returns:
            CSV string representation of the record
        """
        dict_record = self._record_to_dict(record)

        if self._fieldnames is None:
            raise RuntimeError("Field names not set")

        values = []
        for fieldname in self._fieldnames:
            value = dict_record.get(fieldname, "")
            # Simple CSV escaping
            if isinstance(value, str) and (
                self.delimiter in value or self.quotechar in value or "\n" in value
            ):
                value = (
                    self.quotechar
                    + value.replace(self.quotechar, self.quotechar + self.quotechar)
                    + self.quotechar
                )
            values.append(str(value))

        return self.delimiter.join(values) + self.lineterminator
