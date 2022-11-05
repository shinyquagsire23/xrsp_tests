import sys
import struct

from capnp_parse import CapnpParser
from xrsp_parse import *

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print ("pkt_parse.py file.bin")
        sys.exit(-1)

    f = open(sys.argv[1], "rb")
    contents = f.read()
    f.close()

    pkt = TopicPkt(contents)
    pkt.dump()