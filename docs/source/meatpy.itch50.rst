meatpy.itch50 package
=====================

Package contents
------------------

.. automodule:: meatpy.itch50
   :members:
   :undoc-members:
   :show-inheritance:

About
-----

This package adds support for the Nasdaq TotalView-ITCH 5.0 file format. For more details, see the `format specification
<http://www.nasdaqtrader.com/content/technicalsupport/specifications/dataproducts/NQTVITCHSpecification.pdf/>`_.

Known issues
------------

Two message types are not supported yet:

- LULD Auction collars message (introduced September 6, 2017)
- Operational Haltmessage (introduced March 3, 2018)

Daily files after those dates might not process properly. We are planning to add support for these messages soon.

Submodules
----------

meatpy.itch50.itch50\_exec\_trade\_recorder module
***************************************************

.. automodule:: meatpy.itch50.itch50_exec_trade_recorder
   :members:
   :undoc-members:
   :show-inheritance:

meatpy.itch50.itch50\_market\_message module
***************************************************

.. automodule:: meatpy.itch50.itch50_market_message
   :members:
   :undoc-members:
   :show-inheritance:

meatpy.itch50.itch50\_market\_processor module
***************************************************

.. automodule:: meatpy.itch50.itch50_market_processor
   :members:
   :undoc-members:
   :show-inheritance:

meatpy.itch50.itch50\_message\_parser module
***************************************************

.. automodule:: meatpy.itch50.itch50_message_parser
   :members:
   :undoc-members:
   :show-inheritance:

meatpy.itch50.itch50\_ofi\_recorder module
***************************************************

.. automodule:: meatpy.itch50.itch50_ofi_recorder
   :members:
   :undoc-members:
   :show-inheritance:

meatpy.itch50.itch50\_order\_event\_recorder module
******************************************************

.. automodule:: meatpy.itch50.itch50_order_event_recorder
   :members:
   :undoc-members:
   :show-inheritance:

meatpy.itch50.itch50\_top\_of\_book\_message\_recorder module
**************************************************************

.. automodule:: meatpy.itch50.itch50_top_of_book_message_recorder
   :members:
   :undoc-members:
   :show-inheritance:



