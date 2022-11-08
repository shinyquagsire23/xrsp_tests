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

    xrsp_host = XrspHost()

    full_size = len(contents)
    remainder = contents
    buildup = b''
    idx = 0
    while len(remainder) > 0:
        buildup = remainder[idx:idx+0x200]
        idx += 0x200

        pkt = TopicPkt(xrsp_host, buildup)
        while pkt.missing_bytes() > 0:
            #print ("MISSING", hex(pkt.missing_bytes()))
            _b = remainder[idx:idx+0x200]
            idx += 0x200
            pkt.add_missing_bytes(_b)
        pkt.dump()
        #print("Remains:")
        #hex_dump(pkt.remainder_bytes())
        idx -= len(pkt.remainder_bytes())
        #print ("At:", hex(idx))
        #hex_dump(remainder[:0x200])