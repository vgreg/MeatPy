"""Order Flow Imbalance (OFI) event recorder for limit order books.

This module provides the OFIRecorder class, which records order flow imbalance
metrics as described in Cont et al. (2013) and exports them to CSV files.

See Equation (10) of
Cont, R., et al. (2013). "The Price Impact of Order Book Events."
Journal of Financial Econometrics 12(1): 47-88.
"""

from io import TextIOWrapper

from ..event_handlers.lob_event_recorder import LOBEventRecorder
from ..lob import LimitOrderBook


class OFIRecorder(LOBEventRecorder):
    """Records order flow imbalance (OFI) metrics for limit order books.

    Attributes:
        previous_lob: The previous limit order book snapshot
    """

    def __init__(self):
        """Initialize the OFIRecorder."""
        self.previous_lob: LimitOrderBook | None = None
        LOBEventRecorder.__init__(self)

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
            self.records.append((record_timestamp, e_n))
        self.previous_lob = new_lob

    def write_csv(self, file: TextIOWrapper):
        """Write OFI records to a CSV file.

        Args:
            file: File object to write to
        """
        file.write("Timestamp,e_n\n")
        for x in self.records:
            file.write(f"{x[0]},{x[1]}\n")

    def write_csv_header(self, file: TextIOWrapper):
        """Write the CSV header row to the file.

        Args:
            file: File object to write the header to
        """
        file.write("Timestamp,e_n\n")

    def append_csv(self, file: TextIOWrapper):
        """Append OFI records to a CSV file.

        Args:
            file: File object to append to
        """
        for x in self.records:
            file.write(f"{x[0]},{x[1]}\n")
        self.records = []
