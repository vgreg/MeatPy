"""Sample code for extracting the symbols from a ITCH 5.0"""

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

# Initialize the parser
parser = ITCH50MessageParser()

# Keep only the Stock Directory Messages
parser.keep_messages_types = 'R'

# Stock Directory Messages are also copied in a separate list by the parser,
# so we can avoid keeping track of stock-specific messages.
parser.skip_stock_messages = True

# Parse the raw compressed ITCH 5.0 file.
# Note: This can take a while. If we were to run this on many files,
# it might make sense to modify the message parser to stop after a given
# number of messages since these stock directory messages are at the
# start of the day.
with gzip.open(input_dir + fn, 'rb') as itch_file:
    parser.parse_file(itch_file)

# We only care about symbols, so let's extract those.
symbols = [x.stock for x in parser.stock_directory]

# Output the list of symbols, one per row.
lines = [x.decode() + '\n' for x in symbols]
with open(output_dir + 'Symbols_' + dt_str + '.txt', 'w') as out_file:
    out_file.writelines(lines)