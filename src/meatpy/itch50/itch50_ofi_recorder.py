"""ITCH 5.0 Order Flow Imbalance (OFI) recorder for limit order books.

This module provides the ITCH50OFIRecorder class, which records order flow
imbalance metrics adapted for ITCH 5.0 data, including trades against hidden orders.

See Equations (4) and (10) of
Cont, R., et al. (2013). "The Price Impact of Order Book Events."
Journal of Financial Econometrics 12(1): 47-88.

The recorder follows equation (10) but accounts for trades against
hidden orders as well.
"""

from typing import Any

from ..event_handlers.ofi_recorder import OFIRecorder
from .itch50_market_message import TradeMessage


class ITCH50OFIRecorder(OFIRecorder):
    """Records order flow imbalance (OFI) metrics for ITCH 5.0 data.

    This recorder extends the base OFIRecorder to handle ITCH 5.0 specific
    features, including trades against hidden orders that are not captured
    in the standard limit order book.

    Attributes:
        records: List of recorded OFI measures
        previous_lob: The previous limit order book snapshot
    """

    def __init__(self) -> None:
        """Initialize the ITCH50OFIRecorder."""
        self.records: list[Any] = []
        self.previous_lob = None
        OFIRecorder.__init__(self)

    def message_event(self, market_processor, timestamp, message) -> None:
        """Detect trades against hidden orders and record OFI metrics.

        Args:
            market_processor: The market processor instance
            timestamp: The timestamp of the message
            message: The market message to process
        """
        # For a hidden order to execute, it must be first in line
        # (in front of first level), so we record ALL trades against hidden
        # orders.
        if isinstance(message, TradeMessage):
            volume = message.shares
            # OFI decreases when a trade is executed against a hidden bid.
            if message.bsindicator == b"B":
                sign = -1
            elif message.bsindicator == b"S":
                sign = 1
            e_n = sign * volume
            self.records.append((timestamp, e_n))
