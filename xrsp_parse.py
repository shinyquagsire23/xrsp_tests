# pip3 install pycapnp
import struct

import capnp
import Logging_capnp
import CameraStream_capnp

from capnp_parse import CapnpParser
from utils import hex_dump

# pycapnp expects some length header.
def append_size(b):
    return struct.pack("<LL", 0, len(b) // 8) + b

BUILTIN_PAIRING_ACK = 0x0
BUILTIN_INVITE = 0x1
BUILTIN_OK = 0x2
BUILTIN_ACK = 0x3
BUILTIN_ERROR = 0x4
BUILTIN_BYE = 0x5
BUILTIN_ECHO = 0x6
BUILTIN_PAIRING = 0x7
BUILTIN_CODE_GENERATION = 0x9
BUILTIN_CODE_GENERATION_ACK = 0xA
BUILTIN_RESERVED = 0xF

TOPIC_AUI4A_ADV = 0x0
TOPIC_HOSTINFO_ADV = 0x1
TOPIC_COMMAND = 0x2
TOPIC_POSE = 0x3
TOPIC_MESH = 0x4
TOPIC_VIDEO = 0x5
TOPIC_AUDIO = 0x6
TOPIC_HAPTIC = 0x7
TOPIC_HANDS = 0x8
TOPIC_SKELETON = 0x9
TOPIC_SLICE_0 = 0xA
TOPIC_SLICE_1 = 0xB
TOPIC_SLICE_2 = 0xC
TOPIC_SLICE_3 = 0xD
TOPIC_SLICE_4 = 0xE
TOPIC_SLICE_5 = 0xF
TOPIC_SLICE_6 = 0x10
TOPIC_SLICE_7 = 0x11
TOPIC_SLICE_8 = 0x12
TOPIC_SLICE_9 = 0x13
TOPIC_SLICE_10 = 0x14
TOPIC_SLICE_11 = 0x15
TOPIC_SLICE_12 = 0x16
TOPIC_SLICE_13 = 0x17
TOPIC_SLICE_14 = 0x18
TOPIC_SLICE_15 = 0x19
TOPIC_AUDIO_CONTROL = 0x1A
TOPIC_USER_SETTINGS_SYNC = 0x1B
TOPIC_INPUT_CONTROL = 0x1C
TOPIC_ASW = 0x1D
TOPIC_BODY = 0x1E
TOPIC_RUNTIME_IPC = 0x1F
TOPIC_CAMERA_STREAM = 0x20
TOPIC_LOGGING = 0x21
TOPIC_22 = 0x22
TOPIC_23 = 0x23

XrspResultLut = [
    "success",
    "invalid argument",
    "invalid data",
    "invalid state",
    "buffer too small",
    "out of memory",
    "topic does not exist",
    "topic already exists",
    "topic is not writable",
    "topic is not readable",
    "no device",
    "invalid transport description",
    "transport closed",
    "I/O error",
    "timeout occurred",
    "packet lost",
    "incompatible packet version",
    "forced termination",
    "property does not exist",
    "no session active",
    "not implemented",
    "unknown error",
    "network host disconnected",
    "ssl memory allocation failed",
    "ssl set cipher list failed",
    "ssl failed to use the provided cert",
    "ssl failed to use the privided private ",
    "cert and key provided failed validation",
    "ssl failed to set read/write fds",
    "ssl handshake failed",
    "peer failed to provide cert",
    "invalid pairing code",
    "pairing refused",
    "pairing timed out",
    "pairing_invalid_cert"
]

XrspTopic = [
    "aui4a-adv",
    "hostinfo-adv",
    "Command",
    "Pose",
    "Mesh",
    "Video",
    "Audio",
    "Haptic",
    "Hands",
    "Skeleton",
    "Slice 0",
    "Slice 1",
    "Slice 2",
    "Slice 3",
    "Slice 4",
    "Slice 5",
    "Slice 6",
    "Slice 7",
    "Slice 8",
    "Slice 9",
    "Slice 10",
    "Slice 11",
    "Slice 12",
    "Slice 13",
    "Slice 14",
    "Slice 15",
    "AudioControl",
    "UserSettingsSync",
    "InputControl",
    "Asw",
    "Body",
    "RuntimeIPC",
    "CameraStream",
    "Logging",
]

def XrspBuiltinMessageType(idx):
    if idx == BUILTIN_PAIRING_ACK:
        return "PAIRING_ACK"
    elif idx == BUILTIN_INVITE:
        return "INVITE"
    elif idx == BUILTIN_OK:
        return "OK"
    elif idx == BUILTIN_ACK:
        return "ACK"
    elif idx == BUILTIN_ERROR:
        return "ERROR"
    elif idx == BUILTIN_BYE:
        return "BYE"
    elif idx == BUILTIN_ECHO:
        return "ECHO"
    elif idx == BUILTIN_PAIRING:
        return "PAIRING"
    elif idx == BUILTIN_CODE_GENERATION:
        return "CODE_GENERATION"
    elif idx == BUILTIN_CODE_GENERATION_ACK:
        return "CODE_GENERATION_ACK"
    elif idx == BUILTIN_RESERVED:
        return "RESERVED"
    else:
        return "unknown"

class TopicPkt:

    def __init__(self, b):
        if len(b) < 7:
            print ("Bad pkt!")
            return

        topic_raw, num_words, sequence = struct.unpack("<HHH", b[:6])

        self.topic_raw = topic_raw
        self.sequence = sequence
        self.unk_0_2 = (topic_raw) & 0x7
        self.bHasAlignPadding = (topic_raw & 8) == 8
        self.bPacketVersionIsInternal = (topic_raw & 0x10) == 0x10
        self.bPacketVersionNumber = (topic_raw & 0x20) == 0x20
        self.topic_idx = (topic_raw >> 8) & 0x3F
        self.unk_14_15 = (topic_raw >> 14) & 0x3
        self.num_words = num_words
        self.real_size = ((self.num_words - 1) * 4)

        self.do_handoff = False

        self.payload = b[8:]
        self.payload = self.payload[:self.real_size]

        self.payload_remainder = b[8+len(self.payload):]

        self.specificObj = None
        if self.missing_bytes() == 0:
            self.rebuild_specific()

    def rebuild_specific(self):
        self.specificObj = None

        if self.topic_idx == TOPIC_HOSTINFO_ADV:
            self.specificObj = HostInfoPkt(self.payload)
        elif self.topic_idx == TOPIC_POSE:
            self.specificObj = PosePkt(self.payload)
        elif self.topic_idx == TOPIC_AUDIO:
            self.specificObj = AudioPkt(self.payload)
        elif self.topic_idx == TOPIC_CAMERA_STREAM:
            self.specificObj = CameraStreamPkt(self.payload, self.sequence)
        elif self.topic_idx >= TOPIC_SLICE_0 and self.topic_idx <= TOPIC_SLICE_15:
            self.specificObj = SlicePkt(self.payload)
        elif self.topic_idx == TOPIC_LOGGING:
            self.specificObj = LoggingPkt(self.payload)

    def missing_bytes(self):
        amt = ((self.num_words - 1) * 4) - len(self.payload)
        if self.num_words == 0xFFFF and amt == 0:
            self.do_handoff = True
            return 0x200
        if amt >= 0:
            return amt
        return 0

    def add_missing_bytes(self, b):
        if self.do_handoff:
            topic_raw, num_words, sequence = struct.unpack("<HHH", b[:6])
            self.num_words += num_words - 1
            self.real_size = ((self.num_words - 1) * 4)
            b = b[8:]
            self.do_handoff = False

        self.payload += b
        before = len(self.payload)
        self.payload = self.payload[:self.real_size]
        after = len(self.payload)
        self.payload_remainder = b[len(b) - (before-after):]

    def remainder_bytes(self):
        return self.payload_remainder

    def dump(self):
        # Don't print aui4a-adv padding for now
        if self.topic_idx == 0:
            return

        self.rebuild_specific()

        print ("TopicPkt:")
        print ("  unk_0_2: %01x" % self.unk_0_2)
        print ("  bHasAlignPadding: " + str(self.bHasAlignPadding))
        print ("  bPacketVersionIsInternal: " + str(self.bPacketVersionIsInternal))
        print ("  bPacketVersionNumber: " + str(self.bPacketVersionNumber))
        print ("  topic: %s (%01x)" % (XrspTopic[self.topic_idx], self.topic_idx))
        print ("  unk_14_15: %01x" % self.unk_14_15)
        print ("  num_words: %04x" % self.num_words)
        print ("  sequence: %04x" % self.sequence)

        if self.specificObj is not None:
            self.specificObj.dump()
        else:
            hex_dump(self.payload)
        print ("---------")
        print ("")


class HostInfoPkt:

    def __init__(self, b):
        if len(b) < 16:
            print ("Bad pkt!")
            return

        header_0, unk_4, unk_8, len_u64s = struct.unpack("<LLLL", b[:0x10])

        self.header_0 = header_0
        self.unk_4 = unk_4
        self.unk_8 = unk_8
        self.len_u64s = len_u64s
        self.payload = b[0x10:]

        # decode header_0
        self.message_type = header_0 & 0xF
        self.result = (header_0 >> 4) & 0x1FF
        self.stream_size = (header_0 >> 12) & 0xFFFFC
        self.unk_30_31 = (header_0 >> 30)

    def dump(self):
        print ("HostInfoPkt:")
        print ("  header_0: %08x" % self.header_0)

        print ("    message_type:   %s (%01x)" % (XrspBuiltinMessageType(self.message_type), self.message_type))
        print ("    result:         %03x" % self.result)
        print ("    stream_size:    %05x" % self.stream_size)
        print ("    unk_30_31:      %01x" % self.unk_30_31)

        print ("  unk_4:    %08x" % self.unk_4)
        print ("  unk_8:    %08x" % self.unk_8)
        print ("  len_u64s: %08x" % self.len_u64s)

        try:
            parser = CapnpParser(self.payload)
            parser.parse_entry(0)
        except Exception as e:
            a='a'

class LoggingPkt:

    def __init__(self, b):
        if len(b) < 8:
            print ("Bad pkt!")
            return

        self.payload = b[0x0:]

    def dump(self):
        print ("LoggingPkt:", hex(len(self.payload)))
        if len(self.payload) <= 0x8:
            hex_dump(self.payload)
            return

        try:
            with Logging_capnp.PayloadLogging.from_bytes(append_size(self.payload)) as logs:
                print (logs)

            
        except Exception as e:
            print (e)

class PosePkt:

    def __init__(self, b):
        if len(b) < 8:
            print ("Bad pkt!")
            return

        self.payload = b[0x0:]

    def dump(self):
        print ("PosePkt:", hex(len(self.payload)))
        if len(self.payload) <= 0x8:
            hex_dump(self.payload)
            return

        try:
            parser = CapnpParser(self.payload)
            #parser.parse_entry(0)
        except Exception as e:
            print (e)

class AudioPkt:

    def __init__(self, b):
        if len(b) < 8:
            print ("Bad pkt!")
            return

        self.payload = b[0x0:]

    def dump(self):
        print ("AudioPkt:", hex(len(self.payload)))
        if len(self.payload) <= 0x8:
            hex_dump(self.payload)
            return

        try:
            parser = CapnpParser(self.payload)
            #parser.parse_entry(0)
        except Exception as e:
            print (e)

class SlicePkt:

    def __init__(self, b):
        if len(b) < 8:
            print ("Bad pkt!")
            return

        self.payload = b[0xA:]

    def dump(self):
        print ("PosePkt:", hex(len(self.payload)))
        if len(self.payload) <= 0x8:
            hex_dump(self.payload)
            return

        try:
            parser = CapnpParser(self.payload)
            parser.parse_entry(0)
        except Exception as e:
            print (e)

camera_has_meta = False
camera_seq_collecting = False
camera_which = 0
camera_seq_seg0_size = 0
camera_seq_seg1_size = 0
camera_seq_seg2_size = 0

camera_seq_seg0 = b''
camera_seq_seg1 = b''
camera_seq_seg2 = b''

class CameraStreamPkt:

    def __init__(self, b, seq):
        if len(b) < 8:
            print ("Bad pkt!")
            return

        self.seq = seq
        self.payload = b[0x0:]

    def dump(self):
        global camera_seq_collecting, camera_which, camera_seq_seg0_size, camera_seq_seg1_size, camera_seq_seg2_size
        global camera_seq_seg0, camera_seq_seg1, camera_seq_seg2, camera_has_meta

        print ("CameraStreamPkt:", hex(len(self.payload)), hex(self.seq))
        if len(self.payload) == 0x10 and not camera_seq_collecting:
            camera_seq_collecting = True
            camera_which, camera_seq_seg0_size, camera_seq_seg1_size, camera_seq_seg2_size = struct.unpack("<LLLL", self.payload)
            
            print("Decoding camera which: " + hex(camera_which) + " (" + hex(camera_seq_seg0_size) + ", " + hex(camera_seq_seg1_size) + ", " + hex(camera_seq_seg2_size) + ")")

            camera_seq_seg0_size *= 8
            camera_seq_seg1_size *= 8
            camera_seq_seg2_size *= 8

            camera_seq_seg0 = b''
            camera_seq_seg1 = b''
            camera_seq_seg2 = b''
            return

        if camera_seq_collecting and len(camera_seq_seg0) < camera_seq_seg0_size:
            camera_seq_seg0 += self.payload
            print (hex(len(camera_seq_seg0)), hex(len(camera_seq_seg1)), hex(len(camera_seq_seg2)))
        elif camera_seq_collecting and len(camera_seq_seg1) < camera_seq_seg1_size:
            camera_seq_seg1 += self.payload
            print (hex(len(camera_seq_seg0)), hex(len(camera_seq_seg1)), hex(len(camera_seq_seg2)))
        elif camera_seq_collecting and len(camera_seq_seg2) < camera_seq_seg2_size:
            camera_seq_seg2 += self.payload
            print (hex(len(camera_seq_seg0)), hex(len(camera_seq_seg1)), hex(len(camera_seq_seg2)))
        
        seg0_left = camera_seq_seg0_size - len(camera_seq_seg0)
        seg1_left = camera_seq_seg1_size - len(camera_seq_seg1)
        seg2_left = camera_seq_seg2_size - len(camera_seq_seg2)

        if camera_seq_collecting and seg0_left <= 0 and seg1_left <= 0 and seg2_left <= 0:
            print (hex(len(camera_seq_seg0)), hex(len(camera_seq_seg1)), hex(len(camera_seq_seg2)))

            segs = [camera_seq_seg0, camera_seq_seg1, camera_seq_seg2]
            #hex_dump(camera_seq_seg0)
            if camera_which == 1 and camera_seq_seg0_size == 5*8:
                payload = CameraStream_capnp.PayloadCameraStreamMeta.from_segments(segs)
                print (bytes(payload.metadata.data).decode("utf-8"))
                camera_has_meta = True
            elif camera_which == 1 and camera_has_meta or camera_which == 2:
                payload = CameraStream_capnp.PayloadCameraStream.from_segments(segs)

                idx = 0
                for d in payload.unk1.struct1Unk4:
                    dat = bytes(d.data)
                    print (hex(len(dat)))
                    with open("camera_seq_" + str(self.seq) + "_" + str(idx) + ".bin", "wb") as f:
                        f.write(dat)
                        f.close()
                    idx += 1

            camera_seq_collecting = False
            camera_seq_seg0 = b''
            camera_seq_seg1 = b''
            camera_seq_seg2 = b''

            return

        if len(self.payload) <= 0x8:
            #hex_dump(self.payload)
            return

        #with open("camera_seq_" + str(self.seq) + ".bin", "wb") as f:
        #    f.write(self.payload)

        if len(self.payload) > 0x200:
            return

        #test = CameraStream_capnp.PayloadCameraStream.new_message()


        '''
        try:
            parser = CapnpParser(self.payload)
            parser.parse_entry(0)
        except Exception as e:
            print (e)
        '''