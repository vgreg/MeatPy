"""Tests for the ParquetWriter class."""

import pytest
import tempfile
from pathlib import Path

# Test if pyarrow is available
try:
    import pyarrow as pa
    import pyarrow.parquet as pq

    HAS_PYARROW = True
except ImportError:
    HAS_PYARROW = False

from src.meatpy.writers.parquet_writer import ParquetWriter


@pytest.mark.skipif(not HAS_PYARROW, reason="pyarrow not available")
class TestParquetWriter:
    """Test cases for ParquetWriter class."""

    def test_init_without_pyarrow(self, monkeypatch):
        """Test that ParquetWriter raises ImportError when pyarrow is not available."""
        # Mock pyarrow as unavailable
        monkeypatch.setattr("src.meatpy.writers.parquet_writer.HAS_PYARROW", False)

        with pytest.raises(ImportError, match="pyarrow is required"):
            ParquetWriter("test.parquet")

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

    def test_init_with_custom_params(self):
        """Test ParquetWriter initialization with custom parameters."""
        with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tmp:
            writer = ParquetWriter(
                tmp.name, buffer_size=500, compression="gzip", write_index=False
            )
            assert writer.buffer_size == 500
            assert writer.compression == "gzip"
            assert writer.write_index is False

    def test_infer_schema_from_dict_records(self):
        """Test schema inference from dictionary records."""
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

    def test_infer_schema_from_sequence_records(self):
        """Test schema inference from sequence records."""
        with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tmp:
            writer = ParquetWriter(tmp.name)

            records = [("2023-01-01", 100.5, 1000), ("2023-01-02", 101.0, 1500)]

            schema = writer._infer_arrow_schema(records)

            assert len(schema) == 3
            assert schema.field("column_0").type == pa.string()
            assert schema.field("column_1").type == pa.float64()
            assert schema.field("column_2").type == pa.int64()

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

    def test_write_records_sequence_format(self):
        """Test writing records in sequence format."""
        with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tmp:
            records = [("2023-01-01", 100.5, 1000), ("2023-01-02", 101.0, 1500)]

            with ParquetWriter(tmp.name) as writer:
                writer.write_records(records)

            # Verify the file was written correctly
            table = pq.read_table(tmp.name)
            assert len(table) == 2
            assert "column_0" in table.column_names
            assert "column_1" in table.column_names
            assert "column_2" in table.column_names

            # Clean up
            Path(tmp.name).unlink()

    def test_write_header_with_explicit_schema(self):
        """Test setting schema explicitly via write_header."""
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

    def test_buffer_and_flush(self):
        """Test buffering and flushing functionality."""
        with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tmp:
            records = [
                {"timestamp": f"2023-01-{i:02d}", "price": 100.0 + i} for i in range(5)
            ]

            with ParquetWriter(tmp.name, buffer_size=3) as writer:
                for record in records:
                    writer.buffer_record(record)

            # Verify all records were written
            table = pq.read_table(tmp.name)
            assert len(table) == 5

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

    def test_empty_records_handling(self):
        """Test handling of empty records."""
        with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tmp:
            writer = ParquetWriter(tmp.name)

            # Should not crash on empty records
            writer.write_records([])
            writer.append_records([])

            assert writer._writer is None

    def test_invalid_record_type(self):
        """Test handling of invalid record types."""
        with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tmp:
            writer = ParquetWriter(tmp.name)

            # Should raise TypeError for unsupported record types
            with pytest.raises(TypeError):
                writer.write_records([42])  # Integer is not supported

    def test_context_manager(self):
        """Test ParquetWriter as context manager."""
        with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tmp:
            records = [{"timestamp": "2023-01-01", "price": 100.5}]

            # Use as context manager
            with ParquetWriter(tmp.name) as writer:
                writer.write_records(records)
                assert writer._writer is not None

            # Writer should be closed after exiting context
            assert writer._writer is None

            # Verify file was written
            table = pq.read_table(tmp.name)
            assert len(table) == 1

            # Clean up
            Path(tmp.name).unlink()

    def test_set_schema_method(self):
        """Test the set_schema method."""
        with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tmp:
            schema_def = {"fields": {"timestamp": "string", "value": "float64"}}

            writer = ParquetWriter(tmp.name)
            writer.set_schema(schema_def)

            assert writer._schema == schema_def
            assert writer._header_written is True
            assert writer._arrow_schema is not None
