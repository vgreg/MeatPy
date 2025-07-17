# MeatPy

MeatPy is a Python framework for processing financial market data, specifically designed for limit order book reconstruction and analysis. It provides efficient tools for handling high-frequency trading data formats like NASDAQ ITCH 5.0.

## Key Features

- **Limit Order Book Processing**: Complete reconstruction and analysis of limit order books
- **ITCH 5.0 Support**: Full implementation for NASDAQ ITCH 5.0 format
- **Event-Driven Architecture**: Extensible framework for real-time market data processing
- **Type Safety**: Modern Python typing for robust financial data handling
- **Multiple Output Formats**: Support for CSV, Parquet, and custom formats

## Who is it for?

MeatPy was originally developed for academic research in high-frequency trading. It is also suitable for backtesting trading strategies and learning about market microstructure. The framework is designed to be flexible and extensible, making it a good fit for both researchers and developers working with other limit order book data formats.

## What is it not for?

MeatPy is not a trading platform or a high-frequency trading engine. Instead, it focuses on the processing and analysis of historical market data. Also, it is not intended for use in production systems without further development and testing. In any case, you probably would not want to use it for real-time application as it is not fast enough for that purpose.

## Architecture Overview

MeatPy is built around several core components:

- **MarketProcessor**: Abstract base class for processing market messages
- **LimitOrderBook**: Core data structure representing the order book state
- **MessageReader**: Interface for reading different market data formats
- **Event Handlers**: Observer pattern for handling market events and recording data


## What's Next?

- Check out the [Installation Guide](installation.md) to get started
- Read the [User Guide](guide/getting-started.md) for usage instructions
- See [Contributing](contributing.md) if you want to contribute to the project

## Academic Papers using MeatPy

- Grégoire, V. and Martineau, C. (2022), [How is Earnings News Transmitted to Stock Prices?](https://doi.org/10.1111/1475-679X.12394). Journal of Accounting Research, 60: 261-297.

- Comerton-Forde, C., Grégoire, V., & Zhong, Z. (2019). [Inverted fee structures, tick size, and market quality](https://doi.org/10.1016/j.jfineco.2019.03.005). Journal of Financial Economics, 134(1), 141-164.

- Yaali, J., Grégoire, V., & Hurtut, T. (2022). [HFTViz: Visualization for the exploration of high frequency trading data](https://journals.sagepub.com/doi/full/10.1177/14738716211064921). Information Visualization, 21(2), 182-193.


## Credits

MeatPy was created by [Vincent Grégoire](https://www.vincentgregoire.com/) and [Charles Martineau](https://www.charlesmartineau.com/). Seoin Kim and Javad YaAli provided valuable research assistance on the project.

## Funding
MeatPy development benefited from the financial support of [IVADO](https://ivado.ca/)
