"""Example demonstrating parquet export functionality.

This example shows how to use the new ParquetWriter with LOB recorders
to export market data in Apache Parquet format.
"""

from pathlib import Path
import tempfile

try:
    from meatpy.writers import ParquetWriter, CSVWriter
    from meatpy.event_handlers.lob_recorder import LOBRecorder
    from meatpy.event_handlers.ofi_recorder import OFIRecorder

    HAS_WRITERS = True
except ImportError:
    HAS_WRITERS = False


# Mock data for demonstration
class MockLimitOrderBook:
    """Mock limit order book for demonstration."""

    def __init__(
        self, timestamp, bid_price=100.0, ask_price=101.0, bid_vol=1000, ask_vol=1500
    ):
        self.timestamp = timestamp
        self.bid_levels = [MockLevel(bid_price, bid_vol)]
        self.ask_levels = [MockLevel(ask_price, ask_vol)]

    def copy(self, max_level=None):
        return MockLimitOrderBook(
            self.timestamp,
            self.bid_levels[0].price if self.bid_levels else 0,
            self.ask_levels[0].price if self.ask_levels else 0,
            self.bid_levels[0].volume() if self.bid_levels else 0,
            self.ask_levels[0].volume() if self.ask_levels else 0,
        )

    def write_csv(self, file, collapse_orders=True, show_age=False):
        """Mock CSV writing for demonstration."""
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
    """Mock price level for demonstration."""

    def __init__(self, price, vol):
        self.price = price
        self._volume = vol

    def volume(self):
        return self._volume


def demonstrate_parquet_export():
    """Demonstrate exporting LOB data to Parquet format."""
    print("=== Parquet Export Example ===")

    if not HAS_WRITERS:
        print("Writers module not available. Please install dependencies.")
        return

    try:
        # Create a temporary directory for output files
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # 1. Basic Parquet export with LOBRecorder
            print("\n1. Basic LOB data export to Parquet:")

            parquet_file = temp_path / "lob_data.parquet"
            with ParquetWriter(parquet_file) as parquet_writer:
                lob_recorder = LOBRecorder(max_depth=5, writer=parquet_writer)

                # Simulate recording some LOB snapshots
                timestamps = [
                    "2023-01-01T09:30:00",
                    "2023-01-01T09:30:01",
                    "2023-01-01T09:30:02",
                ]
                for i, ts in enumerate(timestamps):
                    lob = MockLimitOrderBook(
                        ts,
                        100.0 + i * 0.1,
                        101.0 + i * 0.1,
                        1000 + i * 100,
                        1500 + i * 100,
                    )
                    lob_recorder.record(lob)

                # Close the recorder to flush data
                lob_recorder.close_writer()

            print(f"   ✓ Exported LOB data to {parquet_file}")
            print(f"   ✓ File size: {parquet_file.stat().st_size} bytes")

            # 2. Compare with CSV export
            print("\n2. Comparison with CSV export:")

            csv_file = temp_path / "lob_data.csv"
            with CSVWriter(csv_file) as csv_writer:
                lob_recorder_csv = LOBRecorder(max_depth=5, writer=csv_writer)

                # Record the same data
                for i, ts in enumerate(timestamps):
                    lob = MockLimitOrderBook(
                        ts,
                        100.0 + i * 0.1,
                        101.0 + i * 0.1,
                        1000 + i * 100,
                        1500 + i * 100,
                    )
                    lob_recorder_csv.record(lob)

                lob_recorder_csv.close_writer()

            print(f"   ✓ Exported LOB data to {csv_file}")
            print(f"   ✓ CSV file size: {csv_file.stat().st_size} bytes")
            print(f"   ✓ Parquet file size: {parquet_file.stat().st_size} bytes")

            # 3. OFI data export to Parquet
            print("\n3. OFI data export to Parquet:")

            ofi_parquet_file = temp_path / "ofi_data.parquet"
            with ParquetWriter(
                ofi_parquet_file, compression="snappy"
            ) as parquet_writer:
                ofi_recorder = OFIRecorder(writer=parquet_writer)

                # Simulate recording some OFI data
                for i, ts in enumerate(timestamps):
                    lob = MockLimitOrderBook(
                        ts,
                        100.0 + i * 0.1,
                        101.0 + i * 0.1,
                        1000 + i * 100,
                        1500 + i * 100,
                    )
                    ofi_recorder.record(lob)

                ofi_recorder.close_writer()

            print(f"   ✓ Exported OFI data to {ofi_parquet_file}")
            print(f"   ✓ File size: {ofi_parquet_file.stat().st_size} bytes")

            # 4. Different compression options
            print("\n4. Testing different compression options:")

            compression_types = ["snappy", "gzip", "brotli"]
            for compression in compression_types:
                try:
                    comp_file = temp_path / f"lob_data_{compression}.parquet"
                    with ParquetWriter(comp_file, compression=compression) as writer:
                        recorder = LOBRecorder(max_depth=5, writer=writer)

                        # Record sample data
                        for i, ts in enumerate(timestamps):
                            lob = MockLimitOrderBook(
                                ts,
                                100.0 + i * 0.1,
                                101.0 + i * 0.1,
                                1000 + i * 100,
                                1500 + i * 100,
                            )
                            recorder.record(lob)

                        recorder.close_writer()

                    print(f"   ✓ {compression}: {comp_file.stat().st_size} bytes")
                except Exception as e:
                    print(f"   ✗ {compression}: Failed ({e})")

            # 5. Custom schema example
            print("\n5. Custom schema example:")

            custom_schema = {
                "fields": {
                    "timestamp": "string",
                    "bid_price": "float64",
                    "ask_price": "float64",
                    "spread": "float64",
                }
            }

            custom_file = temp_path / "custom_data.parquet"
            with ParquetWriter(custom_file) as writer:
                writer.set_schema(custom_schema)

                # Manually write some custom records
                custom_records = []
                for i, ts in enumerate(timestamps):
                    bid_price = 100.0 + i * 0.1
                    ask_price = 101.0 + i * 0.1
                    spread = ask_price - bid_price

                    custom_records.append(
                        {
                            "timestamp": ts,
                            "bid_price": bid_price,
                            "ask_price": ask_price,
                            "spread": spread,
                        }
                    )

                writer.write_records(custom_records)

            print(f"   ✓ Custom schema export to {custom_file}")
            print(f"   ✓ File size: {custom_file.stat().st_size} bytes")

            print("\n=== Example completed successfully! ===")
            print("\nKey features demonstrated:")
            print("• Seamless integration with existing LOB and OFI recorders")
            print("• Multiple compression options (snappy, gzip, brotli)")
            print("• Custom schema definition")
            print("• File size comparison between CSV and Parquet")
            print("• Context manager support for automatic cleanup")

    except ImportError as e:
        print(f"Error: {e}")
        print("Please install pyarrow: pip install 'meatpy[parquet]'")
    except Exception as e:
        print(f"Unexpected error: {e}")


def demonstrate_backward_compatibility():
    """Demonstrate that existing CSV functionality still works."""
    print("\n=== Backward Compatibility Example ===")

    if not HAS_WRITERS:
        print("Writers module not available.")
        return

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Traditional CSV export (no writer parameter)
            print("\n1. Traditional CSV export (backward compatible):")

            lob_recorder = LOBRecorder(max_depth=5)  # No writer parameter

            # Record some data
            timestamps = ["2023-01-01T09:30:00", "2023-01-01T09:30:01"]
            for i, ts in enumerate(timestamps):
                lob = MockLimitOrderBook(
                    ts, 100.0 + i * 0.1, 101.0 + i * 0.1, 1000, 1500
                )
                lob_recorder.record(lob)

            # Traditional CSV export method
            csv_file = temp_path / "traditional_export.csv"
            with open(csv_file, "wb") as f:
                lob_recorder.write_csv(f)

            print(f"   ✓ Traditional CSV export to {csv_file}")
            print(f"   ✓ File size: {csv_file.stat().st_size} bytes")

            # New CSV writer approach
            print("\n2. New CSV writer approach:")

            csv_file2 = temp_path / "new_csv_export.csv"
            with CSVWriter(csv_file2) as csv_writer:
                lob_recorder2 = LOBRecorder(max_depth=5, writer=csv_writer)

                # Record the same data
                for i, ts in enumerate(timestamps):
                    lob = MockLimitOrderBook(
                        ts, 100.0 + i * 0.1, 101.0 + i * 0.1, 1000, 1500
                    )
                    lob_recorder2.record(lob)

                lob_recorder2.close_writer()

            print(f"   ✓ New CSV writer export to {csv_file2}")
            print(f"   ✓ File size: {csv_file2.stat().st_size} bytes")

            print("\n=== Backward compatibility maintained! ===")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    demonstrate_parquet_export()
    demonstrate_backward_compatibility()

    print("\n" + "=" * 50)
    print("USAGE SUMMARY")
    print("=" * 50)
    print()
    print("# Basic Parquet export:")
    print("from meatpy.writers import ParquetWriter")
    print("from meatpy.event_handlers.lob_recorder import LOBRecorder")
    print()
    print("with ParquetWriter('output.parquet') as writer:")
    print("    recorder = LOBRecorder(writer=writer)")
    print("    # ... record data ...")
    print("    recorder.close_writer()")
    print()
    print("# With compression:")
    print("writer = ParquetWriter('output.parquet', compression='snappy')")
    print()
    print("# CSV export (same interface):")
    print("from meatpy.writers import CSVWriter")
    print("with CSVWriter('output.csv') as writer:")
    print("    recorder = LOBRecorder(writer=writer)")
    print("    # ... record data ...")
    print("    recorder.close_writer()")
