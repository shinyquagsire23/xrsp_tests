import sys
import struct

from utils import hex_dump

class CapnpParser:

    def __init__(self, contents):
        self.contents = contents

    def get_bytes(self, idx, len):
        b = self.contents[idx*8:(idx*8)+len]
        return b

    def get_word(self, idx):
        b = self.contents[idx*8:(idx+1)*8]
        return struct.unpack("<Q", b)[0]

    def parse_entry(self, idx, prefix=""):
        ret = 0
        word = self.get_word(idx)
        ret += 1
        #print (prefix + ("0x%016x" % word) + " (" + hex(idx) +"/" + hex(idx*8) + ")")

        a = (word & 3)
        if word == 0:
            print (prefix + "(nullptr)")
            return 8
        elif a == 0: # struct
            dataOffs = (word >> 2) & 0x3FFFFFFF
            dataWords = (word >> 32) & 0xFFFF
            dataPtrs = (word >> 48) & 0xFFFF

            print (prefix + "struct", "offs="+hex(dataOffs), "words="+hex(dataWords), "ptrs="+hex(dataPtrs))

            print (prefix + "  data:")
            for i in range(0, dataWords):
                print(prefix + "    " + "data " + hex(i) + ": " + hex(self.get_word(idx + 1 + dataOffs + i)))

            print (prefix + "  ptrs:")
            for i in range(0, dataPtrs):
                self.parse_entry(idx + 1 + dataOffs + dataWords + i, prefix + "    ")

            ret += dataWords + dataPtrs
        elif a == 1: # list
            dataOffs = (word >> 2) & 0x3FFFFFFF
            dataSizeEnc = (word >> 32) & 0x7
            numElements = (word >> 35)

            sizeLut = [0, 0, 1, 2, 4, 8, 8, 0]

            dataSize = sizeLut[dataSizeEnc]
            totalSize = dataSize * numElements

            if dataSizeEnc == 1:
                totalSize = numElements // 8
                if totalSize <= 8:
                    totalSize = 1

            print (prefix + "list dataOffs=" + hex(dataOffs) + ", dataSizeEnc=" + hex(dataSizeEnc) + ", numElements=" + hex(numElements) + ", dataSize=" + hex(dataSize) + ", totalSize=" + hex(totalSize))
            
            if dataSizeEnc == 7:
                tmp = idx + 1 + dataOffs
                tag = self.get_word(tmp)
                tmp += 1
                ret += 1

                numWords = numElements
                numElements = (tag >> 2) & 0x3FFFFFFF
                dataWords = (tag >> 32) & 0xFFFF
                dataPtrs = (tag >> 48) & 0xFFFF
                print (prefix + "  composite (" + hex(tag) + "), numElements=" + hex(numElements) + ", words=" + hex(dataWords) + ", ptrs=" + hex(dataPtrs) + ":")

                for i in range(0, numElements):
                    print (prefix + "  entry " + hex(i) + ":")
                    print (prefix + "    data:")
                    for i in range(0, dataWords):
                        print(prefix + "      " + "data " + hex(i) + ": " + hex(self.get_word(tmp)))
                        tmp += 1
                        ret += 1

                    print (prefix + "    ptrs:")
                    for i in range(0, dataPtrs):
                        self.parse_entry(tmp, prefix + "      ")
                        tmp += 1
                        ret += 1

            else:
                dataBytes = self.get_bytes(idx + 1 + dataOffs, totalSize)
                print (prefix + "  contents:", dataBytes)
                hex_dump(dataBytes, prefix + "  ")
                print ("")

            ret += (totalSize // 8)

        elif a == 2: # inter-segment ptr
            print (prefix + "inter-seg")
        elif a == 3: # capabilities
            print (prefix + "capability")
        return ret

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print ("capnp_parse.py file.bin")
        sys.exit(-1)

    f = open(sys.argv[1], "rb")
    contents = f.read()
    f.close()

    parser = CapnpParser(contents)

    entries = []
    for i in range(0, len(contents) // 8):
        word = parser.get_word(i)
        if word == 0x0006000500000000:
            entries += [i]

    if len(entries) == 0:
        entries = [0]

    for e in entries:
        parser.parse_entry(e)

'''
wordIdx = 0
while True:
    if wordIdx >= len(contents) // 8:
        break

    wordIdx += parse_entry(wordIdx)
'''
    