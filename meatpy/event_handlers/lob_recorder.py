"""lob_recorder.py: A recorder for limit order book snapshots."""

from .lob_event_recorder import LOBEventRecorder


class LOBRecorder(LOBEventRecorder):
    def __init__(self, max_depth=None):
        self.max_depth = max_depth
        self.collapse_orders = True
        self.show_age = False
        # Indicates if we should collapse the orders by level, only applies
        # to CSV output written during recording
        LOBEventRecorder.__init__(self)

    def record(self, lob, record_timestamp=None):
        new_record = lob.copy(max_level=self.max_depth)
        if record_timestamp is not None:
            new_record.timestamp = record_timestamp
        self.records.append(new_record)

    def write_csv(self, outfile, collapse_orders=False, show_age=False):
        """Write to a file in CSV format

        Collapse order means exporting aggregate level data rather than
        individual orders."""
        # Write header row
        outfile.write(self.get_csv_header(collapse_orders, show_age).encode())

        # Write content
        for x in self.records:
            x.write_csv(outfile, collapse_orders, show_age)

    def write_csv_header(self, outfile):  # Write header row
        outfile.write(self.get_csv_header(self.collapse_orders, self.show_age).encode())

    def append_csv(self, outfile):
        # Write content
        for x in self.records:
            x.write_csv(outfile, self.collapse_orders, self.show_age)
        self.records = []

    def get_csv_header(self, collapse_orders=False, show_age=False):
        if show_age:
            if collapse_orders:
                return "Timestamp,Type,Level,Price,Volume,N Orders,Volume-Weighted Average Age,Average Age,First Age,Last Age\n"
            else:
                return (
                    "Timestamp,Type,Level,Price,Order ID,Volume,Order Timestamp,Age\n"
                )
        else:
            if collapse_orders:
                return "Timestamp,Type,Level,Price,Volume,N Orders\n"
            else:
                return "Timestamp,Type,Level,Price,Order ID,Volume,Order Timestamp\n"
