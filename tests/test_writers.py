"""Tests for the data writers module."""

import pytest
import tempfile
import csv
import gzip
from pathlib import Path

# Test if pyarrow is available
try:
    import pyarrow as pa
    import pyarrow.parquet as pq

    HAS_PYARROW = True
except ImportError:
    HAS_PYARROW = False

from meatpy.writers.csv_writer import CSVWriter

if HAS_PYARROW:
    from meatpy.writers.parquet_writer import ParquetWriter


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

    def test_context_manager(self):
        """Test CSVWriter as context manager."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as tmp:
            records = [{"timestamp": "2023-01-01", "price": 100.5}]

            with CSVWriter(tmp.name) as writer:
                writer.write_records(records)

            # Verify file was written
            with open(tmp.name, "r") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 1

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


@pytest.mark.skipif(not HAS_PYARROW, reason="pyarrow not available")
class TestParquetWriter:
    """Test cases for ParquetWriter class."""

    def test_init_with_default_params(self):
        """Test ParquetWriter initialization with default parameters."""
        with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tmp:
            writer = ParquetWriter(tmp.name)
            assert writer.output_path == Path(tmp.name)
            assert writer.buffer_size == 1000
            assert writer.compression == "snappy"
            assert writer.write_index is True
            assert writer._writer is None
            assert writer._arrow_schema is None

    def test_write_records_dict_format(self):
        """Test writing records in dictionary format."""
        with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tmp:
            records = [
                {"timestamp": "2023-01-01", "price": 100.5, "volume": 1000},
                {"timestamp": "2023-01-02", "price": 101.0, "volume": 1500},
            ]

            with ParquetWriter(tmp.name) as writer:
                writer.write_records(records)

            # Verify the file was written correctly
            table = pq.read_table(tmp.name)
            assert len(table) == 2
            assert "timestamp" in table.column_names
            assert "price" in table.column_names
            assert "volume" in table.column_names

            # Clean up
            Path(tmp.name).unlink()

    def test_append_records(self):
        """Test appending records to existing file."""
        with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tmp:
            records1 = [{"timestamp": "2023-01-01", "price": 100.5}]
            records2 = [{"timestamp": "2023-01-02", "price": 101.0}]

            with ParquetWriter(tmp.name) as writer:
                writer.write_records(records1)
                writer.append_records(records2)

            # Verify both records were written
            table = pq.read_table(tmp.name)
            assert len(table) == 2

            # Clean up
            Path(tmp.name).unlink()

    def test_compression_types(self):
        """Test different compression types."""
        compression_types = ["snappy", "gzip", "brotli"]

        for compression in compression_types:
            with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tmp:
                records = [{"timestamp": "2023-01-01", "price": 100.5}]

                with ParquetWriter(tmp.name, compression=compression) as writer:
                    writer.write_records(records)

                # Verify the file was written
                table = pq.read_table(tmp.name)
                assert len(table) == 1

                # Clean up
                Path(tmp.name).unlink()

    def test_schema_inference(self):
        """Test automatic schema inference."""
        with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tmp:
            writer = ParquetWriter(tmp.name)

            records = [
                {
                    "timestamp": "2023-01-01",
                    "price": 100.5,
                    "volume": 1000,
                    "active": True,
                },
                {
                    "timestamp": "2023-01-02",
                    "price": 101.0,
                    "volume": 1500,
                    "active": False,
                },
            ]

            schema = writer._infer_arrow_schema(records)

            assert len(schema) == 4
            assert schema.field("timestamp").type == pa.string()
            assert schema.field("price").type == pa.float64()
            assert schema.field("volume").type == pa.int64()
            assert schema.field("active").type == pa.bool_()

    def test_explicit_schema(self):
        """Test setting explicit schema."""
        with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tmp:
            schema_def = {
                "fields": {"timestamp": "string", "price": "float64", "volume": "int64"}
            }

            writer = ParquetWriter(tmp.name)
            writer.write_header(schema_def)

            assert writer._arrow_schema is not None
            assert len(writer._arrow_schema) == 3
            assert writer._arrow_schema.field("timestamp").type == pa.string()
            assert writer._arrow_schema.field("price").type == pa.float64()
            assert writer._arrow_schema.field("volume").type == pa.int64()


class TestWriterIntegration:
    """Integration tests using writers with recorders."""

    def test_csv_writer_with_mock_data(self):
        """Test CSVWriter with mock LOB data."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as tmp:
            # Mock LOB data
            records = [
                {
                    "Timestamp": "2023-01-01T09:30:00",
                    "Type": "Bid",
                    "Level": 0,
                    "Price": 100.0,
                    "Volume": 1000,
                    "N Orders": 5,
                },
                {
                    "Timestamp": "2023-01-01T09:30:01",
                    "Type": "Ask",
                    "Level": 0,
                    "Price": 101.0,
                    "Volume": 1500,
                    "N Orders": 3,
                },
            ]

            with CSVWriter(tmp.name) as writer:
                writer.write_records(records)

            # Verify the output
            with open(tmp.name, "r") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 2
                assert rows[0]["Type"] == "Bid"
                assert rows[1]["Type"] == "Ask"
                assert float(rows[0]["Price"]) == 100.0
                assert float(rows[1]["Price"]) == 101.0

            # Clean up
            Path(tmp.name).unlink()

    @pytest.mark.skipif(not HAS_PYARROW, reason="pyarrow not available")
    def test_parquet_writer_with_mock_data(self):
        """Test ParquetWriter with mock LOB data."""
        with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tmp:
            # Mock LOB data
            records = [
                {
                    "Timestamp": "2023-01-01T09:30:00",
                    "Type": "Bid",
                    "Level": 0,
                    "Price": 100.0,
                    "Volume": 1000,
                    "N Orders": 5,
                },
                {
                    "Timestamp": "2023-01-01T09:30:01",
                    "Type": "Ask",
                    "Level": 0,
                    "Price": 101.0,
                    "Volume": 1500,
                    "N Orders": 3,
                },
            ]

            with ParquetWriter(tmp.name) as writer:
                writer.write_records(records)

            # Verify the output
            table = pq.read_table(tmp.name)
            assert len(table) == 2

            # Test using PyArrow directly
            type_col = table.column("Type").to_pylist()
            price_col = table.column("Price").to_pylist()
            assert type_col[0] == "Bid"
            assert type_col[1] == "Ask"
            assert price_col[0] == 100.0
            assert price_col[1] == 101.0

            # Clean up
            Path(tmp.name).unlink()

    @pytest.mark.skipif(not HAS_PYARROW, reason="pyarrow not available")
    def test_ofi_data_format(self):
        """Test writing OFI format data."""
        with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tmp:
            # Mock OFI data
            records = [
                {"Timestamp": "2023-01-01T09:30:00", "e_n": 100},
                {"Timestamp": "2023-01-01T09:30:01", "e_n": -50},
                {"Timestamp": "2023-01-01T09:30:02", "e_n": 75},
            ]

            with ParquetWriter(tmp.name) as writer:
                writer.write_records(records)

            # Verify the output
            table = pq.read_table(tmp.name)
            assert len(table) == 3

            # Test using PyArrow directly
            e_n_col = table.column("e_n").to_pylist()
            assert sum(e_n_col) == 125  # 100 - 50 + 75

            # Clean up
            Path(tmp.name).unlink()

    def test_buffer_functionality(self):
        """Test buffering functionality across writers."""
        buffer_size = 3

        # Test CSV buffering
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as tmp:
            records = [{"id": i, "value": i * 10} for i in range(5)]

            writer = CSVWriter(tmp.name, buffer_size=buffer_size)
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

        # Test Parquet buffering if available
        if HAS_PYARROW:
            with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tmp:
                records = [{"id": i, "value": i * 10} for i in range(5)]

                writer = ParquetWriter(tmp.name, buffer_size=buffer_size)
                for record in records:
                    writer.buffer_record(record)
                writer.close()

                # Verify all records were written
                table = pq.read_table(tmp.name)
                assert len(table) == 5

                # Clean up
                Path(tmp.name).unlink()
