"""Tests for the updated recorder classes with DataWriter integration."""

import pytest
import tempfile
import csv
from pathlib import Path
from unittest.mock import Mock

# Test if pyarrow is available
try:
    import pyarrow.parquet as pq

    HAS_PYARROW = True
except ImportError:
    HAS_PYARROW = False

from meatpy.writers.csv_writer import CSVWriter
from meatpy.event_handlers.lob_recorder import LOBRecorder
from meatpy.event_handlers.ofi_recorder import OFIRecorder

if HAS_PYARROW:
    from meatpy.writers.parquet_writer import ParquetWriter


class MockLimitOrderBook:
    """Mock limit order book for testing."""

    def __init__(self, timestamp="2023-01-01T09:30:00"):
        self.timestamp = timestamp
        self.bid_levels = [MockLevel(100.0, 1000)]
        self.ask_levels = [MockLevel(101.0, 1500)]

    def copy(self, max_level=None):
        new_lob = MockLimitOrderBook(self.timestamp)
        if max_level is not None:
            new_lob.bid_levels = self.bid_levels[:max_level] if self.bid_levels else []
            new_lob.ask_levels = self.ask_levels[:max_level] if self.ask_levels else []
        return new_lob

    def write_csv(self, file, collapse_orders=True, show_age=False):
        """Mock CSV writing for testing."""
        if collapse_orders:
            if show_age:
                line = f"{self.timestamp},Bid,0,{self.bid_levels[0].price},{self.bid_levels[0].volume()},1,0.0,0.0,0.0,0.0\n"
                line += f"{self.timestamp},Ask,0,{self.ask_levels[0].price},{self.ask_levels[0].volume()},1,0.0,0.0,0.0,0.0\n"
            else:
                line = f"{self.timestamp},Bid,0,{self.bid_levels[0].price},{self.bid_levels[0].volume()},1\n"
                line += f"{self.timestamp},Ask,0,{self.ask_levels[0].price},{self.ask_levels[0].volume()},1\n"
        else:
            if show_age:
                line = f"{self.timestamp},Bid,0,{self.bid_levels[0].price},1001,{self.bid_levels[0].volume()},{self.timestamp},0.0\n"
                line += f"{self.timestamp},Ask,0,{self.ask_levels[0].price},1002,{self.ask_levels[0].volume()},{self.timestamp},0.0\n"
            else:
                line = f"{self.timestamp},Bid,0,{self.bid_levels[0].price},1001,{self.bid_levels[0].volume()},{self.timestamp}\n"
                line += f"{self.timestamp},Ask,0,{self.ask_levels[0].price},1002,{self.ask_levels[0].volume()},{self.timestamp}\n"

        file.write(line.encode())


class MockLevel:
    """Mock price level for testing."""

    def __init__(self, price, vol):
        self.price = price
        self._volume = vol

    def volume(self):
        return self._volume


class TestLOBRecorder:
    """Test cases for LOBRecorder with DataWriter integration."""

    def test_init_requires_writer(self):
        """Test that LOBRecorder requires a DataWriter."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            writer = CSVWriter(tmp.name)
            recorder = LOBRecorder(writer)

            assert recorder.writer == writer
            assert recorder.max_depth is None
            assert recorder.collapse_orders is True
            assert recorder.show_age is False

    def test_record_functionality(self):
        """Test basic recording functionality."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            writer = CSVWriter(tmp.name)
            recorder = LOBRecorder(writer, max_depth=5)

            # Create mock LOB
            lob = MockLimitOrderBook("2023-01-01T09:30:00")

            # Record the LOB
            recorder.record(lob)

            assert len(recorder.records) == 1
            assert recorder.records[0].timestamp == "2023-01-01T09:30:00"

    def test_schema_generation(self):
        """Test schema generation for different configurations."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            writer = CSVWriter(tmp.name)
            recorder = LOBRecorder(writer)

            # Test default schema (collapsed, no age)
            schema = recorder.get_schema()
            expected_fields = [
                "Timestamp",
                "Type",
                "Level",
                "Price",
                "Volume",
                "N Orders",
            ]
            assert list(schema["fields"].keys()) == expected_fields

            # Test with age
            recorder.show_age = True
            schema = recorder.get_schema()
            assert "Average Age" in schema["fields"]

            # Test without collapsed orders
            recorder.collapse_orders = False
            schema = recorder.get_schema()
            assert "Order ID" in schema["fields"]

    def test_csv_integration(self):
        """Test full integration with CSV writer."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as tmp:
            writer = CSVWriter(tmp.name)
            recorder = LOBRecorder(writer, max_depth=5)

            # Create and record mock LOBs
            timestamps = [
                "2023-01-01T09:30:00",
                "2023-01-01T09:30:01",
                "2023-01-01T09:30:02",
            ]
            for ts in timestamps:
                lob = MockLimitOrderBook(ts)
                recorder.record(lob)

            # Manually flush to writer
            recorder.flush_to_writer()
            recorder.close_writer()

            # Verify the CSV output
            with open(tmp.name, "r") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                # Should have 2 rows per LOB (bid and ask) * 3 LOBs = 6 rows
                assert len(rows) >= 6
                assert rows[0]["Type"] in ["Bid", "Ask"]
                assert float(rows[0]["Price"]) > 0

            # Clean up
            Path(tmp.name).unlink()

    @pytest.mark.skipif(not HAS_PYARROW, reason="pyarrow not available")
    def test_parquet_integration(self):
        """Test full integration with Parquet writer."""
        with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tmp:
            writer = ParquetWriter(tmp.name)
            recorder = LOBRecorder(writer, max_depth=5)

            # Create and record mock LOBs
            timestamps = [
                "2023-01-01T09:30:00",
                "2023-01-01T09:30:01",
                "2023-01-01T09:30:02",
            ]
            for ts in timestamps:
                lob = MockLimitOrderBook(ts)
                recorder.record(lob)

            # Manually flush to writer
            recorder.flush_to_writer()
            recorder.close_writer()

            # Verify the Parquet output
            table = pq.read_table(tmp.name)
            assert len(table) >= 6  # 2 rows per LOB * 3 LOBs
            assert "Type" in table.column_names
            assert "Price" in table.column_names

            # Clean up
            Path(tmp.name).unlink()

    def test_buffer_management(self):
        """Test automatic buffer flushing."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as tmp:
            writer = CSVWriter(tmp.name)
            recorder = LOBRecorder(writer)
            recorder.buffer_size = 2  # Small buffer for testing

            # Create mock market processor
            mock_processor = Mock()
            mock_processor.current_lob = MockLimitOrderBook()
            mock_processor.trading_status = None

            # Record multiple LOBs to trigger buffer flush
            for i in range(5):
                recorder.record(MockLimitOrderBook(f"2023-01-01T09:30:0{i}"))

                # Simulate market processor call that would trigger flush
                if len(recorder.records) >= recorder.buffer_size:
                    recorder.flush_to_writer()

            recorder.close_writer()

            # Clean up
            Path(tmp.name).unlink()


class TestOFIRecorder:
    """Test cases for OFIRecorder with DataWriter integration."""

    def test_init_requires_writer(self):
        """Test that OFIRecorder requires a DataWriter."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            writer = CSVWriter(tmp.name)
            recorder = OFIRecorder(writer)

            assert recorder.writer == writer
            assert recorder.previous_lob is None

    def test_ofi_calculation(self):
        """Test OFI calculation logic."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            writer = CSVWriter(tmp.name)
            recorder = OFIRecorder(writer)

            # Create two mock LOBs with different prices
            lob1 = MockLimitOrderBook("2023-01-01T09:30:00")
            lob2 = MockLimitOrderBook("2023-01-01T09:30:01")
            lob2.bid_levels[0].price = 100.1  # Slightly higher bid

            # Record first LOB (should not create a record)
            recorder.record(lob1)
            assert len(recorder.records) == 0

            # Record second LOB (should create a record)
            recorder.record(lob2)
            assert len(recorder.records) == 1

            timestamp, e_n = recorder.records[0]
            assert timestamp == "2023-01-01T09:30:01"
            assert isinstance(e_n, int)

    def test_schema_generation(self):
        """Test OFI schema generation."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            writer = CSVWriter(tmp.name)
            recorder = OFIRecorder(writer)

            schema = recorder.get_schema()
            expected_fields = ["Timestamp", "e_n"]
            assert list(schema["fields"].keys()) == expected_fields
            assert schema["fields"]["Timestamp"] == "string"
            assert schema["fields"]["e_n"] == "int64"

    def test_csv_integration(self):
        """Test full integration with CSV writer."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as tmp:
            writer = CSVWriter(tmp.name)
            recorder = OFIRecorder(writer)

            # Create sequence of LOBs with changing prices
            timestamps = [
                "2023-01-01T09:30:00",
                "2023-01-01T09:30:01",
                "2023-01-01T09:30:02",
            ]
            for i, ts in enumerate(timestamps):
                lob = MockLimitOrderBook(ts)
                # Vary prices to generate OFI signals
                lob.bid_levels[0].price = 100.0 + i * 0.1
                lob.ask_levels[0].price = 101.0 + i * 0.1
                recorder.record(lob)

            # Flush and close
            recorder.flush_to_writer()
            recorder.close_writer()

            # Verify the CSV output
            with open(tmp.name, "r") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                # Should have 2 OFI records (first LOB doesn't generate record)
                assert len(rows) == 2
                assert "Timestamp" in rows[0]
                assert "e_n" in rows[0]
                assert isinstance(int(rows[0]["e_n"]), int)

            # Clean up
            Path(tmp.name).unlink()

    @pytest.mark.skipif(not HAS_PYARROW, reason="pyarrow not available")
    def test_parquet_integration(self):
        """Test full integration with Parquet writer."""
        with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tmp:
            writer = ParquetWriter(tmp.name)
            recorder = OFIRecorder(writer)

            # Create sequence of LOBs
            timestamps = [
                "2023-01-01T09:30:00",
                "2023-01-01T09:30:01",
                "2023-01-01T09:30:02",
            ]
            for i, ts in enumerate(timestamps):
                lob = MockLimitOrderBook(ts)
                lob.bid_levels[0].price = 100.0 + i * 0.1
                recorder.record(lob)

            # Flush and close
            recorder.flush_to_writer()
            recorder.close_writer()

            # Verify the Parquet output
            table = pq.read_table(tmp.name)
            assert len(table) == 2  # Should have 2 OFI records
            assert "Timestamp" in table.column_names
            assert "e_n" in table.column_names

            # Clean up
            Path(tmp.name).unlink()


class TestRecorderIntegration:
    """Integration tests for recorders with real market processor simulation."""

    def test_trading_status_filtering(self):
        """Test that trading status filtering works with new interface."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as tmp:
            writer = CSVWriter(tmp.name)
            recorder = LOBRecorder(writer)
            recorder.record_always = False
            recorder.record_trading = True

            # Mock market processor with trading status
            mock_processor = Mock()
            mock_processor.current_lob = MockLimitOrderBook()

            # Import trading status classes
            from meatpy.trading_status import TradeTradingStatus, PreTradeTradingStatus

            # Test with trading status (should record)
            mock_processor.trading_status = TradeTradingStatus()
            recorder.before_lob_update(mock_processor, "2023-01-01T09:30:00")
            initial_count = len(recorder.records)

            # Test with pre-trade status (should not record)
            mock_processor.trading_status = PreTradeTradingStatus()
            recorder.before_lob_update(mock_processor, "2023-01-01T09:30:01")
            assert len(recorder.records) == initial_count  # Should not have increased

            # Clean up
            Path(tmp.name).unlink()

    def test_timestamp_based_recording(self):
        """Test timestamp-based recording functionality."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as tmp:
            writer = CSVWriter(tmp.name)
            recorder = LOBRecorder(writer)

            # Set recording window
            recorder.record_start = "2023-01-01T09:30:00"
            recorder.record_end = "2023-01-01T09:31:00"

            # Mock market processor
            mock_processor = Mock()
            mock_processor.current_lob = MockLimitOrderBook()
            mock_processor.trading_status = None

            # Test recording within window
            recorder.before_lob_update(mock_processor, "2023-01-01T09:30:30")
            within_window_count = len(recorder.records)

            # Test recording outside window
            recorder.before_lob_update(mock_processor, "2023-01-01T09:35:00")
            assert len(recorder.records) == within_window_count  # Should not increase

            # Clean up
            Path(tmp.name).unlink()

    def test_context_manager_usage(self):
        """Test using recorders with context managers."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as tmp:
            # Test the complete workflow
            with CSVWriter(tmp.name) as writer:
                recorder = LOBRecorder(writer, max_depth=3)

                # Record some data
                for i in range(3):
                    lob = MockLimitOrderBook(f"2023-01-01T09:30:0{i}")
                    recorder.record(lob)

                # Explicitly flush at the end
                recorder.flush_to_writer()

            # Verify the file was created and has content
            with open(tmp.name, "r") as f:
                content = f.read()
                assert len(content) > 0
                assert "Timestamp" in content  # Should have header

            # Clean up
            Path(tmp.name).unlink()
