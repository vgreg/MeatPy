Overview of MeatPy
============================================

The Market Exchange Analysis Toolbox for Python (MeatPy) is a Python module aimed at researchers studying high-frequency market data feeds, focusing on full limit order book data. 
MeatPy aims to provide a set of standard, user-friendly open-source tools to lower the bar to entry into advanced empirical market microstructure research.
The documentation is available on `Read the Docs <https://meatpy.readthedocs.io/en/latest/index.html>`_ and the source code is available on `GitHub <https://github.com/vgreg/MeatPy>`_.


The three building blocks of the MeatPy workflow are the parser, the market processor, and the recorders.


Parser
--------------------------

The parser is in charge of reading the data files to extract messages. It can be used to convert message files in a different format, 
to split full market data files into symbol-specific files and to feed messages to the market processor.

MeatPy implements a parser for Nasdaq ITCH 5.0:

1. ``ITCH50MessageParser``

Reads and writes Nasdaq ITCH 5.0 binary files. It can split full market data files into symbol-specific files and read messages to feed to the market processor. For more details on messages, see
the `Nasdaq TotalView-ITCH 5.0 Specification <http://www.nasdaqtrader.com/content/technicalsupport/specifications/dataproducts/NQTVITCHSpecification.pdf>`_.


Market Processor
-----------------------------------

The market processor is the engine that allows processing for one symbol/day. It receives messages one at a time and replays the day's events, keeping track of the limit order book's state.


MeatPy implements a market processor for Nasdaq ITCH 5.0:

1. ``ITCH50MarketProcessor``

Handles messages according to the Nasdaq ITCH 5.0 specification.


Recorders
-----------------------------------

The market processor does not generate any output. Instead, attached recorders are used to record the desired output. 
This allows for efficient processing and flexibility in what data is generated.

Once a recorder is attached to a market processor, it can react to events (e.g., trade messages, trading status changes, limit order book updates, etc.) and record the desired data.
Some recorders can be set to record only during specific market states (e.g., regular trading) or at specific timestamps (e.g. every one minute).

MeatPy implements six types of recorders:

1. ``SpotMeasuresRecorder``

Records certain metrics, such as best quotes and Kyle's lambda.

2. ``LOBRecorder``

Records snapshots of the limit order book. It supports parameters for limiting the recorder depth and level of detail.

3. ``ITCH50TopOfBookMessageRecorder``

Records all messages that affect the top of the order book.

4. ``ITCH50OrderEventRecorder``

Records order-related events, such as order additions, order executions, order cancelations, and order replacements.

5. ``ITCH50ExecTradeRecorder``

Records executions and trades, including information about the executed limit order.

6. ``ITCH50OFIRecorder``

Records the order flow imbalance. 

    See Equations (4) and (10) of
    Cont, R., et al. (2013). "The Price Impact of Order Book Events."
    Journal of Financial Econometrics 12(1): 47-88.

    The recorder follows equation (10) but accounts for trades against
    hidden orders as well.
