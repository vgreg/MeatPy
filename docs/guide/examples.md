# Examples

This page provides an overview of practical examples for common MeatPy use cases. Each example is available as an interactive Jupyter notebook that you can run with your own data.

!!! note "Sample Data Required"
    The notebooks reference sample ITCH 5.0 data files that should be placed in the `docs/guide/data/` directory. These files are not included in the repository due to size constraints but are commonly available from financial data providers.

## Available Example Notebooks

### 1. [Listing Symbols](01_listing_symbols.ipynb)
**Extract all available symbols from an ITCH 5.0 file**

This notebook demonstrates how to:
- Read ITCH 5.0 files efficiently
- Extract symbol information from Stock Directory messages
- Handle large files with early termination for performance

**Key Use Cases:**
- Understanding what symbols are available in a dataset
- Creating symbol lists for further analysis
- Data exploration and validation

---

### 2. [Extracting Specific Symbols](02_extracting_symbols.ipynb)
**Create filtered ITCH files containing only specific symbols**

This notebook shows how to:
- Filter large ITCH files to specific symbols of interest
- Maintain proper file structure with system messages
- Achieve significant file size reductions (often 90%+ smaller)

**Key Use Cases:**
- Reducing file sizes for faster processing
- Creating focused datasets for specific securities
- Preprocessing data for analysis pipelines

---

### 3. [Top of Book Snapshots](03_top_of_book_snapshots.ipynb)
**Capture best bid and ask prices at regular intervals**

This notebook demonstrates:
- Real-time order book processing
- Time-based snapshot extraction
- Calculating spreads and mid-prices
- Exporting data for further analysis

**Key Use Cases:**
- Creating time series of price data
- Analyzing bid-ask spreads over time
- Building datasets for machine learning models
- Market microstructure research

---

### 4. [Full LOB Snapshots](04_full_lob_snapshots.ipynb)
**Capture complete limit order book depth at regular intervals**

This comprehensive notebook covers:
- Multi-level order book capture
- Volume and order count analysis
- Market depth visualization
- Order book imbalance calculations

**Key Use Cases:**
- Liquidity analysis and market depth studies
- Developing market making algorithms
- Academic research on market microstructure
- Risk management and execution optimization

## Getting Started

1. **Setup Your Environment:**
   ```bash
   # Install dependencies
   uv sync --group docs

   # Start Jupyter
   uv run jupyter lab
   ```

2. **Prepare Your Data:**
   - Place ITCH 5.0 files in `docs/guide/data/`
   - Files can be compressed (.gz) or uncompressed
   - Common filename format: `S081321-v50.txt.gz`

3. **Run the Notebooks:**
   - Open any notebook and run all cells
   - Modify parameters (symbols, intervals, etc.) as needed
   - Save outputs for further analysis

## Data Requirements

The notebooks expect ITCH 5.0 format files with the following characteristics:

- **Format:** NASDAQ ITCH 5.0 specification
- **Compression:** Gzip compression supported and recommended
- **Size:** Files can be several GB; notebooks are optimized for large datasets
- **Content:** Must include Stock Directory messages and order/trade data

## Performance Tips

- **Symbol Filtering:** Use the extraction notebook first to create smaller, focused datasets
- **Interval Selection:** Longer intervals = faster processing but less granular data
- **Memory Management:** The notebooks are designed to handle large files efficiently
- **Parallel Processing:** Run multiple notebooks simultaneously for different symbol sets

## Common Workflow

1. **Explore** → Start with [Listing Symbols](01_listing_symbols.ipynb) to understand your data
2. **Filter** → Use [Extracting Symbols](02_extracting_symbols.ipynb) to create focused datasets
3. **Analyze** → Choose between [Top of Book](03_top_of_book_snapshots.ipynb) or [Full LOB](04_full_lob_snapshots.ipynb) based on your needs
4. **Export** → Save results as CSV/Parquet for further analysis in other tools

## Extending the Examples

The notebooks serve as starting points that you can customize:

- **Add More Symbols:** Modify the symbol lists in each notebook
- **Change Intervals:** Adjust snapshot timing from seconds to hours
- **Custom Metrics:** Add your own calculations and analysis
- **Different Outputs:** Export to different formats (Parquet, HDF5, etc.)
- **Visualization:** Add charts and plots for your specific use case

## Error Handling

All notebooks include proper error handling for common issues:
- Missing data files
- Invalid file formats
- Memory limitations
- Processing interruptions

## Next Steps

After working through the examples:
- Explore the API Reference for advanced usage
- Check the [Contributing Guide](../contributing.md) to add your own examples
- Review the [Getting Started Guide](getting-started.md) for additional features
