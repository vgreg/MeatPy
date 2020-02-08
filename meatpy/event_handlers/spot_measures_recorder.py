"""spot_measures_recorder.py: A recorder for multiple spot (only on current LOB) measures."""

__author__ = "Vincent Grégoire"
__email__ = "vincent.gregoire@gmail.com"

from meatpy.event_handlers.lob_event_recorder import LOBEventRecorder
from meatpy.lob import InexistantValueException
from copy import deepcopy


class SpotMeasuresRecorder(LOBEventRecorder):
    def __init__(self):
        self.measures = []  # List of strings (measure names)
        LOBEventRecorder.__init__(self)

    def record(self, lob, record_timestamp=None):
        if record_timestamp is None:
            new_record = [deepcopy(lob.timestamp)]
        else:
            new_record = [record_timestamp]

        for x in self.measures:
            if x == "Bid-Ask Spread":
                try:
                    spread = lob.bid_ask_spread()
                except InexistantValueException:
                    spread = ''
                new_record.append(spread)
            elif x == "Mid Quote":
                try:
                    mid_quote = lob.mid_quote()
                except InexistantValueException:
                    mid_quote = ''
                new_record.append(mid_quote)
            elif x == "Best Ask":
                try:
                    best_ask = lob.best_ask()
                except InexistantValueException:
                    best_ask = ''
                new_record.append(best_ask)
            elif x == "Best Bid":
                try:
                    best_bid = lob.best_bid()
                except InexistantValueException:
                    best_bid = ''
                new_record.append(best_bid)
            elif x == "Quote Slope":
                try:
                    quote_slope = lob.quote_slope()
                except InexistantValueException:
                    quote_slope = ''
                new_record.append(quote_slope)
            elif x == "Log Quote Slope":
                try:
                    log_quote_slope = lob.log_quote_slope()
                except InexistantValueException:
                    log_quote_slope = ''
                new_record.append(log_quote_slope)
            else:
                raise Exception("SpotMeasuresRecorder:before_lob_update",
                                "Unknown measure: " + x)

        self.records.append(new_record)

    def write_csv(self, file, collapse=False):
        """Write to a file in CSV format"""
        # Write header row
        file.write('Timestamp')
        for x in self.measures:
            file.write(',' + x)
        file.write('\n')

        if collapse:
            last_ts = None
            next_write = None
            # Write content
            for x in self.records:
                if last_ts is None:
                    last_ts = x[0]
                    next_write = x
                elif x[0] == last_ts:
                    next_write = x
                else:
                    if next_write is not None:
                        self.__write_record(file, next_write)
                    last_ts = x[0]
                    next_write = x
            if next_write is not None:
                self.__write_record(file, next_write)
        else:
            # Write content
            for x in self.records:
                self.__write_record(file, x)

    def __write_record(self, file, record):
        first = True
        for y in record:
            if not first:
                file.write(',')
            else:
                first = False
            file.write(str(y))
        file.write('\n')

    def write_csv_header(self, file):
        # Write header row
        file.write('Timestamp')
        for x in self.measures:
            file.write(',' + x)
        file.write('\n')

    def append_csv(self, file):
        # Write content
        for x in self.records:
            first = True
            for y in x:
                if not first:
                    file.write(',')
                else:
                    first = False
                file.write(str(y))
            file.write('\n')
        self.records = []
