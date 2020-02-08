"""ofi_recorder.py: A recorder for the changes in order flow imbalance."""

__author__ = "Vincent Grégoire"
__email__ = "vincent.gregoire@gmail.com"

"""
See Equation (10) of
Cont, R., et al. (2013). "The Price Impact of Order Book Events."
Journal of Financial Econometrics 12(1): 47-88.
"""

# -*- coding: utf-8 -*-
from meatpy.event_handlers.lob_event_recorder import LOBEventRecorder


class OFIRecorder(LOBEventRecorder):
    def __init__(self):
        self.previous_lob = None
        LOBEventRecorder.__init__(self)

    def record(self, lob, record_timestamp=None):
        if record_timestamp is None:
            record_timestamp = lob.timestamp

        new_lob = lob.copy(max_level=1)

        if(self.previous_lob is not None):
            try:
                Pb_new = new_lob.bid_levels[0].price
                qb_new = new_lob.bid_levels[0].volume()
            except IndexError:
                Pb_new = 0  # So that old shares get counted
                qb_new = 0
            try:
                Pb_prev = self.previous_lob.bid_levels[0].price
                qb_prev = self.previous_lob.bid_levels[0].volume()
            except IndexError:
                Pb_prev = Pb_new  # So that new shares get counted
                qb_prev = 0
            try:
                Ps_prev = self.previous_lob.ask_levels[0].price
                qs_prev = self.previous_lob.ask_levels[0].volume()
            except IndexError:
                Ps_prev = 0  # So that new shares get counted
                qs_prev = 0
            try:
                Ps_new = new_lob.ask_levels[0].price
                qs_new = new_lob.ask_levels[0].volume()
            except IndexError:
                Ps_new = Ps_prev   # So that old shares get counted
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

    def write_csv(self, file):
        """Write to a file in CSV format"""
        # Write header row
        file.write('Timestamp,e_n\n')

        # Write content
        for x in self.records:
            file.write(str(x[0]) + ',' + str(x[1]) + '\n')

    def write_csv_header(self, file):
        file.write('Timestamp,e_n\n')

    def append_csv(self, file):
        # Write content
        for x in self.records:
            file.write(str(x[0]) + ',' + str(x[1]) + '\n')
        self.records = []
