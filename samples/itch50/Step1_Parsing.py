"""Sample code for parsing a ITCH 5.0 file"""

import gzip
from datetime import datetime
from meatpy.itch50 import ITCH50MessageParser

sample_dir = '../sample_data/'

date = datetime(2019, 5, 30)
dt_str = date.strftime('%Y%m%d')

fn = dt_str + '.BX_ITCH_50.gz'

# List of stocks to extract, in byte arrays.
# Note that all Nasdaq ITCH symbols are 8 bytes long (ticker + whitespace)
stocks = [b'AAPL    ', b'ALGN    ']

# Initialize the parser
parser = ITCH50MessageParser()

# Setup parser to minimize memory use. A smaller buffer uses less memory
# by writes more often to disk, which slows down the process.
parser.message_buffer = 500  # Per stock buffer size (in # of messages)
parser.global_write_trigger = 10000  # Check if buffers exceeded

# We only want our stocks. This is optional, by default MeatPy 
# extracts all stocks.
parser.stocks = stocks

# Set the output dir for stock files
# Using a file prefix is good practice for dating the files.
# It also avoids clashes with reserved filenames on Windows, such
# as 'PRN'.
parser.output_prefix = sample_dir + 'BX_ITCH_' + dt_str + '_'

# Parse the raw compressed ITCH 5.0 file.
with gzip.open(sample_dir + fn, 'rb') as itch_file:
    parser.parse_file(itch_file, write=True)
