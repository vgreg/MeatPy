"""Sample code for extracting the symbols from a ITCH 5.0"""

import gzip
from meatpy.itch50 import ITCH50MessageParser

sample_dir = '../sample_data/'

fn = '20190530.BX_ITCH_50.gz'
outfn = 'Symbols_20190530_BX_ITCH.txt'

# Initialize the parser
parser = ITCH50MessageParser()

# Keep only the Stock Directory Messages
parser.keep_messages_types = b'R'

# Stock Directory Messages are also copied in a separate list by the parser,
# so we can avoid keeping track of stock-specific messages, which saves
# memory.
parser.skip_stock_messages = True

# Parse the raw compressed ITCH 5.0 file.
# Note: This can take a while. If we were to run this on many files,
# it might make sense to modify the message parser to stop after a given
# number of messages since the stock directory messages are at the
# start of the day.
with gzip.open(sample_dir + fn, 'rb') as itch_file:
    parser.parse_file(itch_file)

# We only care about symbols, so let's extract those.
symbols = [x.stock for x in parser.stock_directory]

# Output the list of symbols, one per row.
lines = [x.decode() + '\n' for x in symbols]
with open(sample_dir + outfn, 'w') as out_file:
    out_file.writelines(lines)
