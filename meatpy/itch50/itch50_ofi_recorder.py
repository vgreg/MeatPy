"""itch50_ofi_recorder.py: A recorder for the changes in OFI adapted to ITCH 5.0

See Equations (4) and (10) of
Cont, R., et al. (2013). "The Price Impact of Order Book Events."
Journal of Financial Econometrics 12(1): 47-88.

The recorder follows equation (10) but accounts for trades against
hidden orders as well.
"""

__author__ = "Vincent Grégoire"
__email__ = "vincent.gregoire@gmail.com"

# -*- coding: utf-8 -*-
from meatpy.event_handlers.ofi_recorder import OFIRecorder
from meatpy.itch50.itch50_market_message import TradeMessage


class ITCH50OFIRecorder(OFIRecorder):
    def __init__(self):
        self.records = []  # List of records, each record is a list of measures
        self.previous_lob = None
        OFIRecorder.__init__(self)

    def message_event(self, market_processor, timestamp, message):
        """Detect trades against hidden orders"""
        # For an hidden order toexecute, it must be first in line
        # (in front of first level), so we record ALL trades againts hidden
        # orders.
        if isinstance(message, TradeMessage):
            volume = message.shares
            # OFI decreases when a trade is execute against a hidden bid.
            if message.bsindicator == b'B':
                sign = -1
            elif message.bsindicator == b'S':
                sign = 1
            e_n = sign*volume
            self.records.append((timestamp, e_n))
