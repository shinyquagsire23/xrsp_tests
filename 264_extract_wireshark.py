import sys
import struct

from capnp_parse import CapnpParser
from xrsp_parse import *

from utils import hex_dump

# Didn't work
#(((usb.data_len > 0) && (usb.endpoint_address != 0x81) && (usb.endpoint_address != 0x01))) && (usb.endpoint_address != 0x00) && (usb.endpoint_address != 0x80) && (usb.capdata[0x1] == 0x0A) && (usb.capdata[0xB] == 0x01)

# All the video slices
#(((usb.data_len > 0) && (usb.endpoint_address != 0x81) && (usb.endpoint_address != 0x01))) && (usb.endpoint_address != 0x00) && (usb.endpoint_address != 0x80) && (usb.capdata[0x1] >= 0x0A && usb.capdata[0x1] < 0x1A)

#ffmpeg -framerate 24 -f h264 -i 264_test2.bin -analyzeduration 100M -probesize 100M -vcodec copy slice_idk.mp4

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print ("264_extract_wireshark.py file.bin")
        sys.exit(-1)

    f = open(sys.argv[1], "rb")
    contents = f.read()
    f.close()

    xrsp_host = XrspHost()

    contig = b''
    idx = 0x18

    try:
        while True:
            idx += 0x8
            if idx >= len(contents):
                break
            pkt_size_file = struct.unpack("<L", contents[idx:idx+4])[0]
            idx += 4
            real_pkt_size = struct.unpack("<L", contents[idx:idx+4])[0]
            idx += 4

            idx += 0x1B
            pkt_size_file -= 0x1B
            real_pkt_size -= 0x1B

            contig += contents[idx:idx+real_pkt_size]

            idx += pkt_size_file
            if idx >= len(contents):
                break
    except:
        pass

    f = open("264_test.bin", "wb")
    f.write(contig)
    f.close()

    contents = contig
    contig = b''

    full_size = len(contents)
    remainder = contents
    buildup = b''
    idx = 0
    skip = 0
    while len(remainder) > 0:
        buildup = remainder[idx:idx+0x200]
        idx += 0x200

        pkt = TopicPkt(xrsp_host, buildup)
        while pkt.missing_bytes() > 0:
            if idx >= len(contents):
                break
            #print ("MISSING", hex(pkt.missing_bytes()))
            _b = remainder[idx:idx+0x200]
            idx += 0x200
            pkt.add_missing_bytes(_b)
        if pkt.topic_idx >= TOPIC_SLICE_0 and pkt.topic_idx <= TOPIC_SLICE_15:
            if pkt.num_words == 3:
                skip = 2
            if skip == 0 or pkt.num_words > 0x2b:
                contig += pkt.payload
                skip = 0
            else:
                skip -= 1
            last_numwords = pkt.num_words
            #if pkt.payload[3] == 0x1:
            
        #print("Remains:")
        #hex_dump(pkt.remainder_bytes())
        idx -= len(pkt.remainder_bytes())
        print ("At:", hex(idx))
        #hex_dump(remainder[:0x200])
        if idx >= len(contents):
            break

    f = open("264_test2.bin", "wb")
    f.write(contig)
    f.close()