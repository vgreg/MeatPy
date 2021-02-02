Getting Started
============================================

This section presents sample code for common use cases. The suggested workflow is the following:

- ``Step0_ExtractSymbols.py`` Extracting symbols from a Nasdaq ITCH file.
- ``Step1_Parsing.py`` Splitting Nasdaq ITCH files into per symbol individual ITCH files.
- ``Step2_Processing.py`` Process individual symbols.

Data
----

Sample Nasdaq ITCH files are available at `<ftp://emi.nasdaq.com/ITCH/>`_. The following examples are based on the file ``20190530.BX_ITCH_50.gz``, 
which contains Nasdaq BX messages from May 30, 2019. The message format for Nasdaq BX is the same as for the main Nasdaq exchange,
but the files are smaller and thus more suited for examples.

Sample code files are located in the ``samples`` directory. The sample data file should be placed in the ``sample_data`` directory.


Extracting symbols from a Nasdaq ITCH file
------------------------------------------

This program uses a ``ITCH50MessageParser`` to parse an individual Nasdaq ITCH 5.0 file and extract all the traded symbols from stock directory messages. This can be useful to list
all the symbols that are present in the file.

.. literalinclude:: ../../samples/itch50/Step0_ExtractSymbols.py
  :language: Python

The first few lines of the output file look like this:

.. csv-table:: Symbols_20190530_BX_ITCH.txt
   :header-rows: 0

    A       
    AA      
    AAAU    
    AABA    
    AAC     
    AADR    
    AAL     
    AAMC    
    AAME    
    AAN     
    AAOI    
    AAON    
    AAP     
    AAPL    
    AAT     


Splitting Nasdaq ITCH files
---------------------------


This program uses a ``ITCH50MessageParser`` to parse an individual Nasdaq ITCH 5.0 file and split the aggregate daily Nasdaq file into symbol-specific valid Nasdaq ICTH 5.0 files for the desired symbols. 
The resulting files are smaller, so it is more efficient for archival if only some symbols are needed. This makes parallel processing much easier because symbol-specific files can be processed in parallel
on one computer using multiple cores or on computing clusters. Reading and writing ITCH files in binary format is also much faster than using human-readable formats
such as CSV.

.. literalinclude:: ../../samples/itch50/Step1_Parsing.py
  :language: Python


Processing Nasdaq ITCH files
----------------------------

This program processes a symbol-specific ICTH 5.0 file to extract limit order book snapshots and data related to order book events and executions.

While MeatPy does not have built-in multiprocessing support, multiple instances of this code can be executed in parallel using Python's ``multiprocessing`` package.


.. literalinclude:: ../../samples/itch50/Step2_Processing.py
  :language: Python



The first few lines of each output file look like this:

.. csv-table:: lob.csv (lob recorder, full book)
   :header-rows: 1

    Timestamp,Type,Level,Price,Order ID,Volume,Order Timestamp
    34130000000000,Ask,1,3010100,656801,400,34052727737823
    34130000000000,Bid,1,2942000,669949,200,34085725901583
    34190000000000,Ask,1,3010100,656801,400,34052727737823
    34190000000000,Bid,1,2942000,669949,200,34085725901583
    34250000000000,Ask,1,3010100,656801,400,34052727737823
    34250000000000,Ask,2,3040000,845161,30,34202154392271
    34250000000000,Ask,3,3142000,783433,100,34200414784684
    34250000000000,Ask,4,3471000,774589,100,34200317659936
    34250000000000,Bid,1,2958900,837589,200,34201826545548
    34250000000000,Bid,2,2829900,783425,100,34200414765177
    34250000000000,Bid,3,2502200,774585,100,34200317644668
    34310000000000,Ask,1,3040000,845161,30,34202154392271
    34310000000000,Ask,2,3142000,783433,100,34200414784684
    34310000000000,Ask,3,3471000,774589,100,34200317659936



.. csv-table:: or.csv (order event recorder)
   :header-rows: 1

    Timestamp,MessageType,BuySellIndicator,Price,Volume,OrderID,NewOrderID,AskPrice,AskSize,BidPrice,BidSize
    34052727727406,AddOrder,B,2954000,400,656797,,None,None,None,None
    34052727737823,AddOrder,S,3010100,400,656801,,None,None,2954000,400
    34084825837342,OrderDelete,,,,656797,,3010100,400,2954000,400
    34085725901583,AddOrder,B,2942000,200,669949,,3010100,400,None,None
    34200317644668,AddOrderMPID,B,2502200,100,774585,,3010100,400,2942000,200
    34200317659936,AddOrderMPID,S,3471000,100,774589,,3010100,400,2942000,200
    34200414765177,AddOrderMPID,B,2829900,100,783425,,3010100,400,2942000,200
    34200414784684,AddOrderMPID,S,3142000,100,783433,,3010100,400,2942000,200
    34200777056480,OrderDelete,,,,669949,,3010100,400,2942000,200
    34201826545548,AddOrder,B,2958900,200,837589,,3010100,400,2829900,100
    34202154392271,AddOrder,S,3040000,30,845161,,3010100,400,2958900,200
    34272871221455,OrderDelete,,,,837589,,3010100,400,2958900,200
    34272871225602,OrderDelete,,,,656801,,3010100,400,2829900,100
    34471992679916,AddOrder,B,2992600,3,2939241,,3040000,30,2829900,100



.. csv-table:: tob.csv (lob recorder, top of book only)
   :header-rows: 1

    Timestamp,Type,Level,Price,Volume,N Orders
    34052727727406,Bid,1,2954000,400,1
    34052727737823,Ask,1,3010100,400,1
    34052727737823,Bid,1,2954000,400,1
    34084825837342,Ask,1,3010100,400,1
    34085725901583,Ask,1,3010100,400,1
    34085725901583,Bid,1,2942000,200,1
    34200317644668,Ask,1,3010100,400,1
    34200317644668,Bid,1,2942000,200,1
    34200317659936,Ask,1,3010100,400,1
    34200317659936,Bid,1,2942000,200,1
    34200414765177,Ask,1,3010100,400,1
    34200414765177,Bid,1,2942000,200,1
    34200414784684,Ask,1,3010100,400,1
    34200414784684,Bid,1,2942000,200,1




.. csv-table:: tr.csv (trade recorder)
   :header-rows: 1

    Timestamp,MessageType,Queue,Price,Volume,OrderID,OrderTimestamp
    34703242608927,Exec,Ask,3008000,31,4426365,34692733984765
    34703242648024,Exec,Ask,3008000,60,4426365,34692733984765
    34729950074550,Exec,Bid,3017000,4,4635649,34729950038510
    35149267156862,ExecHid,Bid,3025000,100,,
    35290544186992,ExecHid,Bid,3026200,100,,
    35290544190321,ExecHid,Bid,3026200,100,,
    35290544574482,ExecHid,Bid,3026200,100,,
    35401142766421,ExecHid,Bid,3027100,100,,
    35518105042925,ExecHid,Bid,3035200,75,,
    35518105042925,ExecHid,Bid,3035000,25,,
    35574799640110,ExecHid,Bid,3032500,75,,
    35574799640110,ExecHid,Bid,3032500,25,,
    35703478335449,Exec,Bid,3024500,17,7939453,35327271048191
    35778872267499,ExecHid,Bid,3023500,100,,

