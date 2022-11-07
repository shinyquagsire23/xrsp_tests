import struct

import sys

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print ("pkt_parse.py file.bin")
        sys.exit(-1)

    f = open(sys.argv[1], "rb")
    contents = f.read()
    f.close()

    f = open(sys.argv[1] + ".u8", "wb")

    for i in range(0, len(contents)//4):
        b = contents[i*4:(i+1)*4]
        val = struct.unpack("<f", b)[0]
        val_u8 = int(val * 255.0 / 6)
        if (val_u8 > 255):
            print (val_u8)
        f.write(bytes([val_u8 & 0xFF]))
        #print (val)
    f.close()