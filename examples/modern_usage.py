"""Modern usage example for MeatPy.

This example demonstrates how to use the new high-level API and improved
architecture for processing market data.
"""

from pathlib import Path

from meatpy import (
    MarketDataProcessor,
    create_processor,
    default_config,
    list_available_formats,
)
from meatpy.event_handlers import LOBRecorder


def main():
    """Demonstrate modern MeatPy usage."""

    # 1. Check available formats
    print("Available formats:")
    for name, description in list_available_formats().items():
        print(f"  - {name}: {description}")
    print()

    # 2. Create a custom configuration
    config = default_config
    config.processing.track_lob = True
    config.processing.max_lob_depth = 10
    config.processing.output_directory = Path("output")

    # 3. Create event handlers
    lob_recorder = LOBRecorder(max_depth=5)

    # 4. Create a high-level processor
    processor = MarketDataProcessor(
        format_name="itch50",
        config=config,
        handlers=[lob_recorder],
    )

    # 5. Process a file (example with gzip)
    sample_file = Path("sample_data/20190530.BX_ITCH_50.gz")

    if sample_file.exists():
        print(f"Processing {sample_file}...")

        # Process a specific instrument
        _ = processor.process_file(
            file_path=sample_file,
            instrument="AAPL",
            book_date="2019-05-30",
        )

        print(f"Processed {len(lob_recorder.records)} LOB snapshots")

        # Export to CSV
        output_file = config.processing.output_directory / "lob_snapshots.csv"
        with open(output_file, "w") as f:
            lob_recorder.write_csv(f)

        print(f"Exported LOB data to {output_file}")

    else:
        print(f"Sample file {sample_file} not found. Creating a simple example...")

        # Alternative: Create processor directly
        itch_processor = create_processor(
            format_name="itch50",
            instrument="AAPL",
            book_date="2024-01-01",
        )

        print("Created ITCH50 processor for AAPL")
        print(f"Current LOB: {itch_processor.current_lob}")


def demonstrate_format_registry():
    """Demonstrate the format registry system."""
    print("\n=== Format Registry Demo ===")

    # List all registered formats
    formats = list_available_formats()
    print(f"Registered formats: {list(formats.keys())}")


if __name__ == "__main__":
    main()
    demonstrate_format_registry()
