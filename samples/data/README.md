# Sample data

This directory ships a tiny synthetic ITCH 5.0 file so the examples and tests
in this repository can be run without access to a Nasdaq subscription.

## `sample.itch50`

A 590-byte binary ITCH 5.0 file built from `generate_sample.py`. It contains
20 messages for two fictional symbols, **MEAT** and **PYTH**:

- System events bracketing the trading day (`O`, `S`, `Q`, `M`, `E`, `C`)
- Stock directory entries for both symbols
- Add Order, Order Executed, Order Cancel, Order Delete, and Trade messages
  exercising both sides of the book

The data is **not** real market data. It exists purely so that you can run the
parser, processor, and writers end-to-end with a self-contained input.

## Regenerating

```bash
uv run python samples/data/generate_sample.py
```
