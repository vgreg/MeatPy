"""Tests for the CSVWriter class."""

import pytest
import tempfile
import gzip
import csv
from pathlib import Path

from src.meatpy.writers.csv_writer import CSVWriter


class TestCSVWriter:
    """Test cases for CSVWriter class."""

    def test_init_with_default_params(self):
        """Test CSVWriter initialization with default parameters."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            writer = CSVWriter(tmp.name)
            assert writer.output_path == Path(tmp.name)
            assert writer.buffer_size == 1000
            assert writer.compression is None
            assert writer.delimiter == ","
            assert writer.quotechar == '"'
            assert writer.lineterminator == "\n"
            assert writer._fieldnames is None

    def test_init_with_custom_params(self):
        """Test CSVWriter initialization with custom parameters."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            writer = CSVWriter(
                tmp.name,
                buffer_size=500,
                compression="gzip",
                delimiter="|",
                quotechar="'",
                lineterminator="\r\n",
            )
            assert writer.buffer_size == 500
            assert writer.compression == "gzip"
            assert writer.delimiter == "|"
            assert writer.quotechar == "'"
            assert writer.lineterminator == "\r\n"

    def test_extract_fieldnames_from_dict(self):
        """Test extracting field names from dictionary records."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            writer = CSVWriter(tmp.name)

            records = [
                {"timestamp": "2023-01-01", "price": 100.5, "volume": 1000},
                {"timestamp": "2023-01-02", "price": 101.0, "volume": 1500},
            ]

            fieldnames = writer._extract_fieldnames(records)
            assert fieldnames == ["timestamp", "price", "volume"]

    def test_extract_fieldnames_from_sequence(self):
        """Test extracting field names from sequence records."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            writer = CSVWriter(tmp.name)

            records = [("2023-01-01", 100.5, 1000), ("2023-01-02", 101.0, 1500)]

            fieldnames = writer._extract_fieldnames(records)
            assert fieldnames == ["column_0", "column_1", "column_2"]

    def test_extract_fieldnames_empty_records(self):
        """Test extracting field names from empty records."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            writer = CSVWriter(tmp.name)

            fieldnames = writer._extract_fieldnames([])
            assert fieldnames == []

    def test_record_to_dict_with_dict_input(self):
        """Test converting dictionary record to dictionary."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            writer = CSVWriter(tmp.name)

            record = {"timestamp": "2023-01-01", "price": 100.5}
            result = writer._record_to_dict(record)
            assert result == record

    def test_record_to_dict_with_sequence_input(self):
        """Test converting sequence record to dictionary."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            writer = CSVWriter(tmp.name)
            writer._fieldnames = ["timestamp", "price", "volume"]

            record = ("2023-01-01", 100.5, 1000)
            result = writer._record_to_dict(record)
            assert result == {"timestamp": "2023-01-01", "price": 100.5, "volume": 1000}

    def test_record_to_dict_with_scalar_input(self):
        """Test converting scalar record to dictionary."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            writer = CSVWriter(tmp.name)

            # Without fieldnames
            result = writer._record_to_dict(42)
            assert result == {"value": 42}

            # With fieldnames
            writer._fieldnames = ["measurement"]
            result = writer._record_to_dict(42)
            assert result == {"measurement": 42}

    def test_write_header_with_fieldnames(self):
        """Test writing header with explicit fieldnames."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as tmp:
            schema = {"fieldnames": ["timestamp", "price", "volume"]}

            writer = CSVWriter(tmp.name)
            writer.write_header(schema)

            assert writer._fieldnames == ["timestamp", "price", "volume"]
            assert writer._schema == schema

            # Verify header was written to file
            with open(tmp.name, "r") as f:
                content = f.read()
                assert content.strip() == "timestamp,price,volume"

            # Clean up
            Path(tmp.name).unlink()

    def test_write_header_with_fields(self):
        """Test writing header with fields definition."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as tmp:
            schema = {
                "fields": {"timestamp": "string", "price": "float64", "volume": "int64"}
            }

            writer = CSVWriter(tmp.name)
            writer.write_header(schema)

            assert writer._fieldnames == ["timestamp", "price", "volume"]

            # Clean up
            Path(tmp.name).unlink()

    def test_write_records_dict_format(self):
        """Test writing records in dictionary format."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as tmp:
            records = [
                {"timestamp": "2023-01-01", "price": 100.5, "volume": 1000},
                {"timestamp": "2023-01-02", "price": 101.0, "volume": 1500},
            ]

            writer = CSVWriter(tmp.name)
            writer.write_records(records)

            # Verify the file was written correctly
            with open(tmp.name, "r") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 2
                assert rows[0]["timestamp"] == "2023-01-01"
                assert rows[0]["price"] == "100.5"
                assert rows[0]["volume"] == "1000"

            # Clean up
            Path(tmp.name).unlink()

    def test_write_records_sequence_format(self):
        """Test writing records in sequence format."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as tmp:
            records = [("2023-01-01", 100.5, 1000), ("2023-01-02", 101.0, 1500)]

            writer = CSVWriter(tmp.name)
            writer.write_records(records)

            # Verify the file was written correctly
            with open(tmp.name, "r") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 2
                assert rows[0]["column_0"] == "2023-01-01"
                assert rows[0]["column_1"] == "100.5"
                assert rows[0]["column_2"] == "1000"

            # Clean up
            Path(tmp.name).unlink()

    def test_append_records(self):
        """Test appending records to existing file."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as tmp:
            records1 = [{"timestamp": "2023-01-01", "price": 100.5}]
            records2 = [{"timestamp": "2023-01-02", "price": 101.0}]

            writer = CSVWriter(tmp.name)
            writer.write_records(records1)
            writer.append_records(records2)

            # Verify both records were written
            with open(tmp.name, "r") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 2
                assert rows[0]["timestamp"] == "2023-01-01"
                assert rows[1]["timestamp"] == "2023-01-02"

            # Clean up
            Path(tmp.name).unlink()

    def test_gzip_compression(self):
        """Test writing with gzip compression."""
        with tempfile.NamedTemporaryFile(suffix=".csv.gz", delete=False) as tmp:
            records = [{"timestamp": "2023-01-01", "price": 100.5}]

            writer = CSVWriter(tmp.name, compression="gzip")
            writer.write_records(records)
            writer.close()

            # Verify the file was written and compressed
            with gzip.open(tmp.name, "rt") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 1
                assert rows[0]["timestamp"] == "2023-01-01"

            # Clean up
            Path(tmp.name).unlink()

    def test_custom_delimiter(self):
        """Test writing with custom delimiter."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as tmp:
            records = [{"timestamp": "2023-01-01", "price": 100.5}]

            writer = CSVWriter(tmp.name, delimiter="|")
            writer.write_records(records)

            # Verify the custom delimiter was used
            with open(tmp.name, "r") as f:
                content = f.read()
                assert "|" in content
                assert "," not in content.split("\n")[0]  # Header shouldn't have commas

            # Clean up
            Path(tmp.name).unlink()

    def test_buffer_and_flush(self):
        """Test buffering and flushing functionality."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as tmp:
            records = [
                {"timestamp": f"2023-01-{i:02d}", "price": 100.0 + i}
                for i in range(1, 6)
            ]

            writer = CSVWriter(tmp.name, buffer_size=3)
            for record in records:
                writer.buffer_record(record)
            writer.close()

            # Verify all records were written
            with open(tmp.name, "r") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 5

            # Clean up
            Path(tmp.name).unlink()

    def test_empty_records_handling(self):
        """Test handling of empty records."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as tmp:
            writer = CSVWriter(tmp.name)

            # Should not crash on empty records
            writer.write_records([])
            writer.append_records([])

            # File should exist but be empty (or just have headers if any were set)
            assert Path(tmp.name).exists()

            # Clean up
            Path(tmp.name).unlink()

    def test_context_manager(self):
        """Test CSVWriter as context manager."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as tmp:
            records = [{"timestamp": "2023-01-01", "price": 100.5}]

            # Use as context manager
            with CSVWriter(tmp.name) as writer:
                writer.write_records(records)

            # Verify file was written
            with open(tmp.name, "r") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 1

            # Clean up
            Path(tmp.name).unlink()

    def test_csv_header_string(self):
        """Test generating CSV header string."""
        writer = CSVWriter("dummy.csv")
        writer._fieldnames = ["timestamp", "price", "volume"]

        header = writer.write_csv_header_string()
        assert header == "timestamp,price,volume\n"

    def test_record_to_csv_string(self):
        """Test converting record to CSV string."""
        writer = CSVWriter("dummy.csv")
        writer._fieldnames = ["timestamp", "price", "volume"]

        record = {"timestamp": "2023-01-01", "price": 100.5, "volume": 1000}
        csv_string = writer.record_to_csv_string(record)
        assert csv_string == "2023-01-01,100.5,1000\n"

    def test_record_to_csv_string_with_escaping(self):
        """Test CSV string generation with special characters."""
        writer = CSVWriter("dummy.csv")
        writer._fieldnames = ["name", "description"]

        record = {"name": "Test,Name", "description": 'Contains "quotes"'}
        csv_string = writer.record_to_csv_string(record)
        # Should properly escape commas and quotes
        assert '"Test,Name"' in csv_string
        assert '""quotes""' in csv_string

    def test_set_schema_method(self):
        """Test the set_schema method."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as tmp:
            schema_def = {"fieldnames": ["timestamp", "value"]}

            writer = CSVWriter(tmp.name)
            writer.set_schema(schema_def)

            assert writer._schema == schema_def
            assert writer._header_written is True
            assert writer._fieldnames == ["timestamp", "value"]

            # Verify header was written
            with open(tmp.name, "r") as f:
                content = f.read()
                assert content.strip() == "timestamp,value"

            # Clean up
            Path(tmp.name).unlink()

    def test_append_without_initial_write(self):
        """Test that append_records fails without initial write_records call."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as tmp:
            writer = CSVWriter(tmp.name)

            with pytest.raises(RuntimeError, match="Field names not set"):
                writer.append_records([{"timestamp": "2023-01-01"}])
