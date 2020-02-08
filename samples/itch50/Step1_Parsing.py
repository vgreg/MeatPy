"""Sample code for parsing a ITCH 5.0 file"""

__author__ = "Vincent Grégoire"
__email__ = "vincent.gregoire@gmail.com"

import gzip
from datetime import datetime
from meatpy.itch50 import ITCH50MessageParser


input_dir = '../SampleData/'
output_dir = '../SampleData/'

date = datetime(2015, 1, 8)
dt_str = date.strftime('%m%d%y')

fn = 'S' + dt_str + '-v50.txt.gz'

# List of stocks to extract
stocks = [b'AAPL    ', b'ALGN    ']

# Initialize the parser
parser = ITCH50MessageParser()

# Setup parser to minimize memory use
parser.message_buffer = 500  # Per stock buffer size
parser.global_write_trigger = 10000  # Check if buffers exceeded

# We only want our stocks. This is optional, by default MeatPy 
# extracts all stocks.
parser.stocks = stocks

# Set the output dir for stock files
# Using a file prefix is good practice for dating the files.
# It also avoids clashes with reserved filenames on Windows, such
# as 'PRN'.
parser.output_prefix = output_dir + 'ITCH_' + dt_str + '_'

# Parse the raw compressed ITCH 5.0 file.
with gzip.open(input_dir + fn, 'rb') as itch_file:
    parser.parse_file(itch_file, write=True)
