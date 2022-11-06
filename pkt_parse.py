import sys
import struct

from capnp_parse import CapnpParser
from xrsp_parse import *

from utils import hex_dump

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print ("pkt_parse.py file.bin")
        sys.exit(-1)

    f = open(sys.argv[1], "rb")
    contents = f.read()
    f.close()

    full_size = len(contents)
    remainder = contents
    buildup = b''
    while len(remainder) > 0:
        buildup = remainder[:0x200]
        remainder = remainder[0x200:]

        pkt = TopicPkt(buildup)
        while pkt.missing_bytes() > 0:
            #print ("MISSING", hex(pkt.missing_bytes()))
            _b = remainder[:0x200]
            remainder = remainder[0x200:]
            pkt.add_missing_bytes(_b)
        pkt.dump()
        #print("Remains:")
        #hex_dump(pkt.remainder_bytes())
        remainder = pkt.remainder_bytes() + remainder
        #print ("At:", hex(full_size - len(remainder)))
        #hex_dump(remainder[:0x200])