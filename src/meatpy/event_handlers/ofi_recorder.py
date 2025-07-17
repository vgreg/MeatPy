"""Order Flow Imbalance (OFI) event recorder for limit order books.

This module provides the OFIRecorder class, which records order flow imbalance
metrics as described in Cont et al. (2013) and exports them to CSV files.

See Equation (10) of
Cont, R., et al. (2013). "The Price Impact of Order Book Events."
Journal of Financial Econometrics 12(1): 47-88.
"""

from ..event_handlers.lob_event_recorder import LOBEventRecorder
from ..lob import LimitOrderBook


class OFIRecorder(LOBEventRecorder):
    """Records order flow imbalance (OFI) metrics for limit order books.

    Attributes:
        previous_lob: The previous limit order book snapshot
    """

    def __init__(self, writer):
        """Initialize the OFIRecorder.

        Args:
            writer: DataWriter instance for output
        """
        self.previous_lob: LimitOrderBook | None = None
        LOBEventRecorder.__init__(self, writer=writer)

        # Set the schema based on OFI requirements
        schema = self.get_schema()
        self.writer.set_schema(schema)

    def record(self, lob: LimitOrderBook, record_timestamp: bool = None):
        """Record the OFI metric for the current LOB state.

        Args:
            lob: The current limit order book
            record_timestamp: Optional timestamp to record
        """
        if record_timestamp is None:
            record_timestamp = lob.timestamp
        new_lob = lob.copy(max_level=1)
        if self.previous_lob is not None:
            try:
                Pb_new = new_lob.bid_levels[0].price
                qb_new = new_lob.bid_levels[0].volume()
            except IndexError:
                Pb_new = 0
                qb_new = 0
            try:
                Pb_prev = self.previous_lob.bid_levels[0].price
                qb_prev = self.previous_lob.bid_levels[0].volume()
            except IndexError:
                Pb_prev = Pb_new
                qb_prev = 0
            try:
                Ps_prev = self.previous_lob.ask_levels[0].price
                qs_prev = self.previous_lob.ask_levels[0].volume()
            except IndexError:
                Ps_prev = 0
                qs_prev = 0
            try:
                Ps_new = new_lob.ask_levels[0].price
                qs_new = new_lob.ask_levels[0].volume()
            except IndexError:
                Ps_new = Ps_prev
                qs_new = 0
            e_n = 0
            if Pb_new >= Pb_prev:
                e_n += qb_new
            if Pb_new <= Pb_prev:
                e_n -= qb_prev
            if Ps_new <= Ps_prev:
                e_n -= qs_new
            if Ps_new >= Ps_prev:
                e_n += qs_prev
            # Write record directly to the writer
            record = {"Timestamp": str(record_timestamp), "e_n": e_n}
            self.writer.buffer_record(record)
        self.previous_lob = new_lob

    def get_schema(self):
        """Get schema definition for the data writer."""
        return {"fields": {"Timestamp": "string", "e_n": "int64"}}
