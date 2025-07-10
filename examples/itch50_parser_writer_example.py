"""Example usage of ITCH50MessageReader and ITCH50Writer.

This example demonstrates how to use the decoupled parser and writer classes
to process ITCH 5.0 market data files.
"""

from pathlib import Path

from meatpy.itch50 import ITCH50MessageReader, ITCH50Writer


def main():
    """Example of using ITCH50MessageReader and ITCH50Writer together."""

    # Replace with your actual ITCH file path
    itch_file = "path/to/your/itch50_file.bin"

    # Example 1: Parse all messages from a file (new natural interface)
    print("Example 1: Parsing all messages from a file (natural interface)")

    if Path(itch_file).exists():
        message_count = 0
        with ITCH50MessageReader(itch_file) as parser:
            for message in parser:
                message_count += 1
                if message_count <= 5:  # Print first 5 messages
                    print(f"Message {message_count}: {message.__class__.__name__}")

        print(f"Total messages processed: {message_count}")

    # Example 2: Parse only specific message types (natural interface)
    print("\nExample 2: Parsing only specific message types (natural interface)")

    if Path(itch_file).exists():
        message_count = 0
        with ITCH50MessageReader(
            itch_file, keep_message_types=b"RAP"
        ) as parser:  # Only stock directory, add order, and trade messages
            for message in parser:
                message_count += 1
                if message_count <= 5:
                    print(f"Message {message_count}: {message.__class__.__name__}")

        print(f"Total messages processed: {message_count}")

    # Example 3: Parse only specific symbols (natural interface)
    print("\nExample 3: Parsing only specific symbols (natural interface)")
    symbols = [b"AAPL   ", b"MSFT   "]  # Note: ITCH symbols are 8-byte padded

    if Path(itch_file).exists():
        message_count = 0
        with ITCH50MessageReader(itch_file, symbols=symbols) as parser:
            for message in parser:
                message_count += 1
                if message_count <= 5:
                    print(f"Message {message_count}: {message.__class__.__name__}")

        print(f"Total messages processed: {message_count}")

    # Example 4: Using parser with writer (natural interface)
    print("\nExample 4: Using parser with writer (natural interface)")

    if Path(itch_file).exists():
        with ITCH50MessageReader(itch_file) as parser:
            with ITCH50Writer(
                symbols=[b"AAPL   ", b"MSFT   "],
                output_path="output_symbols.itch",
                message_buffer=1000,
                compress=True,
                compression_type="gzip",
            ) as writer:
                message_count = 0
                for message in parser:
                    writer.process_message(message)
                    message_count += 1

                    # Print progress every 100,000 messages
                    if message_count % 100000 == 0:
                        print(f"Processed {message_count} messages")

                print(f"Total messages processed: {message_count}")
                print(f"Messages written to writer: {writer.message_count}")

    # Example 5: Multiple writers for different purposes (natural interface)
    print("\nExample 5: Multiple writers for different purposes (natural interface)")

    if Path(itch_file).exists():
        with ITCH50MessageReader(itch_file, keep_message_types=b"AFECXDP") as parser:
            with ITCH50Writer(
                output_path="orders.itch", message_buffer=500, compress=True
            ) as order_writer:
                with ITCH50Writer(
                    output_path="trades.itch", message_buffer=500, compress=True
                ) as trade_writer:
                    message_count = 0
                    for message in parser:
                        # Send to both writers
                        order_writer.process_message(message)
                        trade_writer.process_message(message)
                        message_count += 1

                        if message_count % 100000 == 0:
                            print(f"Processed {message_count} messages")

                    print(f"Total messages processed: {message_count}")

    # Example 6: Legacy interface (still supported)
    print("\nExample 6: Legacy interface (still supported)")

    if Path(itch_file).exists():
        # Create parser without file path
        parser = ITCH50MessageReader(keep_message_types=b"RAP")

        # Use parse_file method
        message_count = 0
        for message in parser.parse_file(itch_file):
            message_count += 1
            if message_count <= 5:
                print(f"Message {message_count}: {message.__class__.__name__}")

        print(f"Total messages processed: {message_count}")

    # Example 7: Using context managers with separate parser and writer
    print("\nExample 7: Using context managers with separate parser and writer")

    if Path(itch_file).exists():
        # Create writer first
        with ITCH50Writer(
            symbols=[b"AAPL   "], output_path="aapl_only.itch", compress=True
        ) as writer:
            # Then create parser and process
            with ITCH50MessageReader(itch_file) as parser:
                message_count = 0
                for message in parser:
                    writer.process_message(message)
                    message_count += 1

                    if message_count % 100000 == 0:
                        print(f"Processed {message_count} messages")

                print(f"Total messages processed: {message_count}")
                # Both parser and writer automatically close on exit


if __name__ == "__main__":
    main()
