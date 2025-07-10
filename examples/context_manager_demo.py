"""Demonstration of context manager usage with ITCH50MessageReader and ITCH50Writer.

This script shows how to use the context manager protocol to ensure proper
resource cleanup when working with ITCH 5.0 files.
"""

import struct
import tempfile
from pathlib import Path

from meatpy.itch50 import ITCH50MessageReader, ITCH50Writer


def create_test_itch_file(file_path: Path) -> None:
    """Create a simple test ITCH file with a few messages."""
    with open(file_path, "wb") as f:
        # Create a system event message
        payload = struct.pack("!HHHIc", 1, 1, 0, 0, b"S")
        message_data = b"S" + payload
        f.write(b"\x00")
        f.write(bytes([len(message_data)]))
        f.write(message_data)

        # Create another system event message
        payload = struct.pack("!HHHIc", 2, 2, 0, 0, b"E")
        message_data = b"S" + payload
        f.write(b"\x00")
        f.write(bytes([len(message_data)]))
        f.write(message_data)


def demo_natural_interface():
    """Demonstrate the new natural interface."""
    print("=== Natural Interface ===")

    with tempfile.NamedTemporaryFile(suffix=".itch", delete=False) as tmp_file:
        test_file = Path(tmp_file.name)

    try:
        # Create a test file
        create_test_itch_file(test_file)

        # Use the natural interface - file path in constructor
        with ITCH50MessageReader(test_file) as parser:
            message_count = 0
            for message in parser:  # Direct iteration
                message_count += 1
                print(
                    f"  Processed message {message_count}: {message.__class__.__name__}"
                )

            print(f"  Total messages processed: {message_count}")

        print("✓ Natural interface completed successfully")

    finally:
        # Clean up test files
        test_file.unlink(missing_ok=True)


def demo_nested_context_managers():
    """Demonstrate nested context managers with natural interface."""
    print("\n=== Nested Context Managers (Natural Interface) ===")

    with tempfile.NamedTemporaryFile(suffix=".itch", delete=False) as tmp_file:
        test_file = Path(tmp_file.name)

    try:
        # Create a test file
        create_test_itch_file(test_file)

        # Use nested context managers with natural interface
        with ITCH50MessageReader(test_file) as parser:
            with ITCH50Writer(
                output_path=test_file.with_suffix(".output.itch")
            ) as writer:
                message_count = 0
                for message in parser:  # Direct iteration
                    writer.process_message(message)
                    message_count += 1
                    print(
                        f"  Processed message {message_count}: {message.__class__.__name__}"
                    )

                print(f"  Total messages processed: {message_count}")
                print(f"  Messages written to writer: {writer.message_count}")

        print("✓ Nested context managers completed successfully")

    finally:
        # Clean up test files
        test_file.unlink(missing_ok=True)
        test_file.with_suffix(".output.itch").unlink(missing_ok=True)


def demo_separate_context_managers():
    """Demonstrate separate context managers with natural interface."""
    print("\n=== Separate Context Managers (Natural Interface) ===")

    with tempfile.NamedTemporaryFile(suffix=".itch", delete=False) as tmp_file:
        test_file = Path(tmp_file.name)

    try:
        # Create a test file
        create_test_itch_file(test_file)

        # Use separate context managers with natural interface
        with ITCH50Writer(output_path=test_file.with_suffix(".output2.itch")) as writer:
            with ITCH50MessageReader(test_file) as parser:
                message_count = 0
                for message in parser:  # Direct iteration
                    writer.process_message(message)
                    message_count += 1
                    print(
                        f"  Processed message {message_count}: {message.__class__.__name__}"
                    )

                print(f"  Total messages processed: {message_count}")
                print(f"  Messages written to writer: {writer.message_count}")

        print("✓ Separate context managers completed successfully")

    finally:
        # Clean up test files
        test_file.unlink(missing_ok=True)
        test_file.with_suffix(".output2.itch").unlink(missing_ok=True)


def demo_multiple_writers():
    """Demonstrate multiple writers with natural interface."""
    print("\n=== Multiple Writers (Natural Interface) ===")

    with tempfile.NamedTemporaryFile(suffix=".itch", delete=False) as tmp_file:
        test_file = Path(tmp_file.name)

    try:
        # Create a test file
        create_test_itch_file(test_file)

        # Use multiple writers with natural interface
        with ITCH50MessageReader(test_file) as parser:
            with ITCH50Writer(
                output_path=test_file.with_suffix(".system.itch")
            ) as system_writer:
                with ITCH50Writer(
                    output_path=test_file.with_suffix(".all.itch")
                ) as all_writer:
                    message_count = 0
                    for message in parser:  # Direct iteration
                        # Send to both writers
                        system_writer.process_message(message)
                        all_writer.process_message(message)
                        message_count += 1
                        print(
                            f"  Processed message {message_count}: {message.__class__.__name__}"
                        )

                    print(f"  Total messages processed: {message_count}")
                    print(f"  System writer messages: {system_writer.message_count}")
                    print(f"  All writer messages: {all_writer.message_count}")

        print("✓ Multiple writers completed successfully")

    finally:
        # Clean up test files
        test_file.unlink(missing_ok=True)
        test_file.with_suffix(".system.itch").unlink(missing_ok=True)
        test_file.with_suffix(".all.itch").unlink(missing_ok=True)


def demo_compression():
    """Demonstrate compression with natural interface."""
    print("\n=== Compression with Natural Interface ===")

    with tempfile.NamedTemporaryFile(suffix=".itch", delete=False) as tmp_file:
        test_file = Path(tmp_file.name)

    try:
        # Create a test file
        create_test_itch_file(test_file)

        # Use compression with natural interface
        with ITCH50MessageReader(test_file) as parser:
            with ITCH50Writer(
                output_path=test_file.with_suffix(".compressed.gz"),
                compress=True,
                compression_type="gzip",
            ) as writer:
                message_count = 0
                for message in parser:  # Direct iteration
                    writer.process_message(message)
                    message_count += 1
                    print(
                        f"  Processed message {message_count}: {message.__class__.__name__}"
                    )

                print(f"  Total messages processed: {message_count}")
                print(f"  Messages written to compressed file: {writer.message_count}")

        # Check that compressed file was created
        compressed_file = test_file.with_suffix(".compressed.gz")
        if compressed_file.exists():
            print(f"✓ Compressed file created: {compressed_file}")

        print("✓ Compression with natural interface completed successfully")

    finally:
        # Clean up test files
        test_file.unlink(missing_ok=True)
        test_file.with_suffix(".compressed.gz").unlink(missing_ok=True)


def demo_legacy_interface():
    """Demonstrate the legacy interface still works."""
    print("\n=== Legacy Interface (Still Supported) ===")

    with tempfile.NamedTemporaryFile(suffix=".itch", delete=False) as tmp_file:
        test_file = Path(tmp_file.name)

    try:
        # Create a test file
        create_test_itch_file(test_file)

        # Use the legacy interface
        parser = ITCH50MessageReader()  # No file path in constructor
        message_count = 0
        for message in parser.parse_file(test_file):  # Use parse_file method
            message_count += 1
            print(f"  Processed message {message_count}: {message.__class__.__name__}")

        print(f"  Total messages processed: {message_count}")
        print("✓ Legacy interface completed successfully")

    finally:
        # Clean up test files
        test_file.unlink(missing_ok=True)


def main():
    """Run all demonstrations."""
    print("ITCH 5.0 Context Manager Demonstrations")
    print("=" * 50)

    demo_natural_interface()
    demo_nested_context_managers()
    demo_separate_context_managers()
    demo_multiple_writers()
    demo_compression()
    demo_legacy_interface()

    print("\n" + "=" * 50)
    print("All demonstrations completed successfully!")
    print("\nKey benefits of the new natural interface:")
    print("- More intuitive: file path in constructor")
    print("- Direct iteration: for message in parser:")
    print("- Automatic resource cleanup")
    print("- Exception-safe file handling")
    print("- Cleaner, more readable code")
    print("- Legacy interface still supported for backward compatibility")


if __name__ == "__main__":
    main()
