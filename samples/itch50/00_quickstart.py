"""End-to-end quickstart against the bundled synthetic ITCH 5.0 sample.

Reads samples/data/sample.itch50, summarises message counts, and prints the
top of book for each symbol after replaying every message through the
ITCH 5.0 processor.

Run from the repository root:

    uv run python samples/itch50/00_quickstart.py
"""

from __future__ import annotations

import datetime
from collections import Counter
from pathlib import Path

from meatpy.itch50 import ITCH50MarketProcessor, ITCH50MessageReader

SAMPLE = Path(__file__).resolve().parents[1] / "data" / "sample.itch50"
BOOK_DATE = datetime.datetime(2026, 1, 1)


def replay(symbol: str) -> ITCH50MarketProcessor:
    processor = ITCH50MarketProcessor(symbol, BOOK_DATE)
    with ITCH50MessageReader(SAMPLE) as reader:
        for message in reader:
            processor.process_message(message)
    return processor


def main() -> None:
    counts: Counter[str] = Counter()
    with ITCH50MessageReader(SAMPLE) as reader:
        for message in reader:
            counts[type(message).__name__] += 1

    print(f"Messages in {SAMPLE.name}: {sum(counts.values())}")
    for name, n in counts.most_common():
        print(f"  {n:>3}  {name}")

    for symbol in ("MEAT", "PYTH"):
        processor = replay(symbol)
        lob = processor.current_lob
        print(f"\n{symbol} top of book:")
        if lob is None:
            print("  (no book state)")
            continue
        bid = lob.bid_levels[0] if lob.bid_levels else None
        ask = lob.ask_levels[0] if lob.ask_levels else None
        print(f"  bid: {bid}")
        print(f"  ask: {ask}")


if __name__ == "__main__":
    main()
