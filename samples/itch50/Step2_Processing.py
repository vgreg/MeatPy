"""Sample code for processing ITCH 5.0 file and extracting measures"""
import gzip
import sys
from datetime import datetime
from meatpy.itch50 import ITCH50MessageParser, ITCH50MarketProcessor, \
ITCH50ExecTradeRecorder, ITCH50OrderEventRecorder
from meatpy.event_handlers import LOBRecorder
from meatpy import ExecutionPriorityException, \
VolumeInconsistencyException, ExecutionPriorityExceptionList

sample_dir = '../sample_data/'

parser = ITCH50MessageParser()

with open(sample_dir + 'BX_ITCH_20190530_ALGN.txt', 'rb') as itch_file:
    parser.parse_file(itch_file)
    
# There should only be one stock in the file.
stocks = [s for s in parser.stock_messages]
stock = stocks[0]

processor = ITCH50MarketProcessor(stock, datetime(2019, 5, 30))
# Create a LOB recorder. By default, it records all LOB events.
# That means we will have an event everytime an order enters or exits the book.
# Create one to record the top of book (level 1), all events
tob_recorder = LOBRecorder()
# We only care about the top of book
tob_recorder.max_depth = 1

# We create another one to record 1-minute snapshots on the book
lob_recorder = LOBRecorder()
# We only want every minute. Nasdaq timestamps are in nanoseconds since 12am.
seconds_range = [x * 1000000000 for x in range(34130, 57730+1, 60)]
seconds_range.sort(reverse=True)
lob_recorder.record_timestamps = seconds_range

# Create the trade recorder
trade_recorder = ITCH50ExecTradeRecorder()
# Create the order event recorder
order_recorder = ITCH50OrderEventRecorder()

# Attach the recorders to the processor 
processor.handlers.append(tob_recorder) 
processor.handlers.append(lob_recorder) 
processor.handlers.append(trade_recorder) 
processor.handlers.append(order_recorder)

# Process the messages
for m in parser.stock_messages[stock]:
    try:
        processor.process_message(m)
    except ExecutionPriorityException as e:
        sys.stderr.write('Warning,' + stock.decode() +
                         ',' + e.args[0] + ',"' + e.args[1] + ' (' +
                         str(e[2]) + ')"\n')
    except VolumeInconsistencyException as e:
        sys.stderr.write('Warning,' + stock.decode() +
                         ',' + e[0] + ',"' + e[1] + '\n')
    except ExecutionPriorityExceptionList as eList:
        for e in eList.args[1]:
            sys.stderr.write('Warning,' + stock.decode() +
                             ',' + e.args[0] + ',"' + e.args[1] + ' (' +
                             str(e.args[2]) + ')"\n')
           
# Output files
with gzip.open(sample_dir + 'tob.csv.gz', 'w') as outfile:
    tob_recorder.write_csv(outfile, collapse_orders=True)
with gzip.open(sample_dir + 'lob.csv.gz', 'w') as outfile:
    lob_recorder.write_csv(outfile, collapse_orders=False)
with gzip.open(sample_dir + 'tr.csv.gz', 'w') as outfile:
    trade_recorder.write_csv(outfile)
with gzip.open(sample_dir + 'or.csv.gz', 'w') as outfile:
    order_recorder.write_csv(outfile)