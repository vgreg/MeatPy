# MeatPy


[![PyPI version](https://badge.fury.io/py/meatpy.svg)](https://badge.fury.io/py/meatpy)
[![License](https://img.shields.io/pypi/l/meatpy.svg)](https://github.com/vgreg/MeatPy/blob/main/LICENSE)
[![Documentation Status](https://img.shields.io/badge/docs-online-brightgreen.svg)](https://www.vincentgregoire.com/MeatPy)
[![codecov](https://codecov.io/gh/vgreg/MeatPy/branch/main/graph/badge.svg)](https://codecov.io/gh/vgreg/MeatPy)

<img src="docs/images/meatpy.svg" width="200" alt="MeatPy Logo"/>

MeatPy is a Python framework for processing and analyzing high-frequency financial market data, specifically designed for working with NASDAQ ITCH protocol data feeds. It provides robust tools for reconstructing limit order books and extracting key market events from historical market data files.

## 🎯 Key Features

- **📊 Limit Order Book Reconstruction**: Complete order book state tracking with proper handling of all order types and modifications
- **🏛️ NASDAQ ITCH Support**: Full implementation for ITCH 5.0 and 4.1 protocols with native message parsing
- **⚡ Event-Driven Architecture**: Flexible observer pattern for real-time event processing and analysis
- **🔒 Type Safety**: Modern Python with comprehensive type hints and generic interfaces for robust data handling
- **📁 Multiple Output Formats**: Export to CSV, Parquet, or implement custom output formats
- **🚀 Performance Optimized**: Efficiently process multi-gigabyte ITCH files with streaming capabilities
- **🔧 Extensible Design**: Easy to adapt for other market data formats and custom analysis needs

## 📊 Common Use Cases

MeatPy is designed for market microstructure research and analysis:

- **Order Book Reconstruction**: Rebuild complete limit order book state at any point in time
- **Market Event Analysis**: Extract and analyze trades, quotes, and order modifications
- **Top-of-Book Sampling**: Generate regular snapshots of best bid/ask prices and sizes

## 📦 Installation

### Quick Install

```bash
pip install meatpy
```

### With Optional Dependencies

```bash
# For Parquet file support
pip install meatpy[parquet]
```


## 🚀 Quick Start

Complete documentation is available at [https://www.vincentgregoire.com/MeatPy](https://www.vincentgregoire.com/MeatPy)


### Basic Message Reading

```python
from pathlib import Path
from meatpy.itch50 import ITCH50MessageReader

# Define the path to our sample data file
data_dir = Path("data")
file_path = data_dir / "S081321-v50.txt.gz"

# Read ITCH messages from a file
with ITCH50MessageReader(file_path) as reader:
    for i, message in enumerate(reader):
        print(f"Message {i}: {message.type} - {message}")
        if i >= 10:  # Just show first 10 messages
            break
```

### List Available Symbols

```python
symbols = set()
message_count = 0

with ITCH50MessageReader(file_path) as reader:
    for message in reader:
        message_count += 1

        # Stock Directory messages (type 'R') contain symbol information
        if message.type == b"R":
            symbol = message.stock.decode().strip()
            symbols.add(symbol)

        if message_count >= 100000:
            break
```

### Extract all Messages for Specific Symbols

```python
from pathlib import Path
from meatpy.itch50 import ITCH50MessageReader, ITCH50Writer

# Define paths
data_dir = Path("data")
input_file = data_dir / "S081321-v50.txt.gz"
output_file = data_dir / "S081321-v50-AAPL-SPY.itch50.gz"

# Symbols we want to extract
target_symbols = ["AAPL", "SPY"]

message_count = 0
with ITCH50MessageReader(input_file) as reader:
    with ITCH50Writer(output_file, symbols=target_symbols) as writer:
        for message in reader:
            message_count += 1
            writer.process_message(message)
```


### Extract Full LOB at 1-Minute Intervals

```python
from pathlib import Path
import datetime
from meatpy.itch50 import ITCH50MessageReader, ITCH50MarketProcessor
from meatpy.event_handlers.lob_recorder import LOBRecorder
from meatpy.writers.parquet_writer import ParquetWriter

# Define paths and parameters
data_dir = Path("data")

file_path = data_dir / "S081321-v50-AAPL-SPY.itch50.gz"
outfile_path = data_dir / "spy_lob.parquet"
book_date = datetime.datetime(2021, 8, 13)

with ITCH50MessageReader(file_path) as reader, ParquetWriter(outfile_path) as writer:
    processor = ITCH50MarketProcessor("SPY", book_date)

    # We only care about the top of book
    lob_recorder = LOBRecorder(writer=writer, collapse_orders=False)
    # Generate a list of timedeltas from 9:30 to 16:00 (inclusive) in 30-minute increments
    market_open = book_date + datetime.timedelta(hours=9, minutes=30)
    market_close = book_date + datetime.timedelta(hours=16, minutes=0)
    record_timestamps = [market_open + datetime.timedelta(minutes=i)
                     for i in range(int((market_close - market_open).total_seconds() // (30*60)) + 1)]
    lob_recorder.record_timestamps = record_timestamps

    # Attach the recorders to the processor
    processor.handlers.append(lob_recorder)

    for message in reader:
        processor.process_message(message)
```


## 📊 Common Use Cases

MeatPy is designed for market microstructure research and analysis:

- **Order Book Reconstruction**: Rebuild complete limit order book state at any point in time
- **Market Event Analysis**: Extract and analyze trades, quotes, and order modifications
- **Top-of-Book Sampling**: Generate regular snapshots of best bid/ask prices and sizes
- **Market Quality Metrics**: Calculate spreads, depth, and other liquidity measures
- **Academic Research**: Analyze market microstructure for research papers and studies

MeatPy is **not** suitable for real-time applications or for production use where money is at stake.

## 🎓 Academic Use

MeatPy has been used in several academic publications, including:

- Grégoire, V. and Martineau, C. (2022), [How is Earnings News Transmitted to Stock Prices?](https://doi.org/10.1111/1475-679X.12394). Journal of Accounting Research, 60: 261-297.

- Comerton-Forde, C., Grégoire, V., & Zhong, Z. (2019). [Inverted fee structures, tick size, and market quality](https://doi.org/10.1016/j.jfineco.2019.03.005). Journal of Financial Economics, 134(1), 141-164.

- Yaali, J., Grégoire, V., & Hurtut, T. (2022). [HFTViz: Visualization for the exploration of high frequency trading data](https://journals.sagepub.com/doi/full/10.1177/14738716211064921). Information Visualization, 21(2), 182-193.


## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](https://www.vincentgregoire.com/MeatPy/contributing/) for details.

## 📄 License

MeatPy is released under the permissive BSD 3-Clause License. See [LICENSE](LICENSE) file for details.

## 👥 Credits

MeatPy was created by [Vincent Grégoire](https://www.vincentgregoire.com/) and [Charles Martineau](https://www.charlesmartineau.com/). Seoin Kim and Javad YaAli provided valuable research assistance on the project.


**Acknowledgments**: MeatPy development benefited from the financial support of [IVADO](https://ivado.ca/)

## 📞 Support

- **Bug Reports**: Please use [GitHub Issues](https://github.com/vgreg/MeatPy/issues)
- **Questions & Discussions**: Use [GitHub Discussions](https://github.com/vgreg/MeatPy/discussions)

---

Made with ❤️ for the market microstructure research community
