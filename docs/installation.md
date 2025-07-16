# Installation

## Requirements

MeatPy requires Python 3.11 or higher.

## Install from PyPI

The easiest way to install MeatPy is using pip:

```bash
pip install meatpy
```

For Parquet output support, install with the parquet extra:

```bash
pip install meatpy[parquet]
```

## Install from Source

To install the latest development version from GitHub:

```bash
git clone https://github.com/vgreg/MeatPy.git
cd MeatPy
pip install -e .
```

## Development Installation

For development, we recommend using `uv` for dependency management:

```bash
git clone https://github.com/vgreg/MeatPy.git
cd MeatPy
uv sync
```

This will create a virtual environment and install all dependencies including development tools.

## Verify Installation

You can verify your installation by running:

```python
import meatpy
print(meatpy.__version__)
```

## Optional Dependencies

- **pyarrow**: Required for Parquet output format support
- **jupyter** and **pandas**: For running example notebooks
- **pytest**: For running tests if you're contributing
