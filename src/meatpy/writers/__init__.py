"""Data writers for exporting market data in various formats.

This module provides a common interface for writing market data to different
file formats including CSV and Parquet.
"""

from .base_writer import DataWriter
from .csv_writer import CSVWriter

__all__ = ["DataWriter", "CSVWriter"]

try:
    from .parquet_writer import ParquetWriter

    __all__.append("ParquetWriter")
except ImportError:
    # ParquetWriter requires pyarrow which is an optional dependency
    ParquetWriter = None
