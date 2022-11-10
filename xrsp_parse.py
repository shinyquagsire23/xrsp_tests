# pip3 install pycapnp pygame numpy
import struct

# Draw cameras
import pygame
import numpy as np
import json

import capnp
import Logging_capnp
import CameraStream_capnp
import Pose_capnp
import Audio_capnp
import RuntimeIPC_capnp
import Slice_capnp

from capnp_parse import CapnpParser
from utils import hex_dump
from xrsp_constants import *
#from xrsp_host import *

class TopicPkt:

    def __init__(self, host, b):
        if len(b) < 7:
            print ("Bad topic pkt!")
            hex_dump(b)
            return

        self.recv_ns = host.ts_ns()
        self.host = host

        topic_raw, num_words, sequence = struct.unpack("<HHH", b[:6])

        self.unk_0_2 = (topic_raw) & 0x7
        self.bHasAlignPadding = (topic_raw & 8) == 8
        self.bPacketVersionIsInternal = (topic_raw & 0x10) == 0x10
        self.bPacketVersionNumber = (topic_raw & 0x20) == 0x20
        self.topic_idx = (topic_raw >> 8) & 0x3F
        self.unk_14_15 = (topic_raw >> 14) & 0x3
        self.num_words = num_words
        self.sequence = sequence

        self.real_size = ((self.num_words - 1) * 4)
        self.full_size = ((self.num_words - 1) * 4)

        self.payload = b[8:]

        if self.bHasAlignPadding and len(self.payload) >= self.real_size:
            self.real_size -= self.payload[self.real_size-1]

        self.payload = self.payload[:self.real_size]

        self.payload_remainder = b[8+self.full_size:]

        self.specificObj = None

    def rebuild_specific(self):
        if self.specificObj is not None:
            return

        self.specificObj = None

        if self.topic_idx == TOPIC_HOSTINFO_ADV:
            self.specificObj = HostInfoPkt(self.host, self.recv_ns, self.payload)
        elif self.topic_idx == TOPIC_POSE:
            self.specificObj = PosePkt(self.host, self.payload)
        elif self.topic_idx == TOPIC_AUDIO:
            self.specificObj = AudioPkt(self.host, self.payload)
        elif self.topic_idx == TOPIC_HANDS:
            self.specificObj = HandsPkt(self.host, self.payload)
        elif self.topic_idx == TOPIC_SKELETON:
            self.specificObj = SkeletonPkt(self.host, self.payload)
        elif self.topic_idx == TOPIC_CAMERA_STREAM:
            self.specificObj = CameraStreamPkt(self.host, self.payload, self.sequence)
        elif self.topic_idx >= TOPIC_SLICE_0 and self.topic_idx <= TOPIC_SLICE_15:
            self.specificObj = SlicePkt(self.host, self.topic_idx - TOPIC_SLICE_0, self.payload)
        elif self.topic_idx == TOPIC_RUNTIME_IPC:
            self.specificObj = RuntimeIPCPkt(self.host, self.payload)
        elif self.topic_idx == TOPIC_LOGGING:
            self.specificObj = LoggingPkt(self.host, self.payload)

    def missing_bytes(self):
        amt = self.real_size - len(self.payload)

        if amt >= 0:
            return amt
        return 0

    def add_missing_bytes(self, b):
        self.payload += b
        before = len(self.payload)
        self.payload = self.payload[:self.real_size]
        after = len(self.payload)

        if self.bHasAlignPadding and len(self.payload) >= self.real_size:
            self.real_size -= self.payload[self.real_size-1]
            self.payload = self.payload[:self.real_size]

        self.payload_remainder = b[len(b) - (before-after):]

    def remainder_bytes(self):
        #if self.missing_bytes() != 0:
        #    return self.payload + self.payload_remainder

        return self.payload_remainder

    def dump(self):
        # Don't print aui4a-adv padding for now
        
        if self.missing_bytes() == 0:
            self.rebuild_specific()
        else:
            print ("Missing %x bytes..." % self.missing_bytes())
            return

        if self.topic_idx in self.host.topics_mute:
            return

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
            print ("Missing %x bytes..." % self.missing_bytes())
            hex_dump(self.payload)
        print ("---------")
        print ("")


class HostInfoPkt:

    def __init__(self, host, recv_ns, b):
        if len(b) < 16:
            print ("Bad hostinfo pkt!")
            hex_dump(b)
            return

        self.recv_ns = recv_ns

        header_0, unk_4 = struct.unpack("<LL", b[:0x8])

        self.header_0 = header_0
        self.unk_4 = unk_4
        

        # decode header_0
        self.message_type = header_0 & 0xF
        self.result = (header_0 >> 4) & 0x1FF
        self.stream_size = (header_0 >> 12) & 0xFFFFC
        self.unk_30_31 = (header_0 >> 30)

        self.unk_8 = 0
        self.len_u64s = 0

        self.echo_org = -1
        self.echo_recv = -1
        self.echo_xmt = -1
        self.echo_offset = -1

        if self.message_type == BUILTIN_ECHO:
            self.payload = b[8:]
            self.echo_org, self.echo_recv, self.echo_xmt, self.echo_offset = struct.unpack("<QQQQ", self.payload)
        else:
            self.unk_8, self.len_u64s = struct.unpack("<LL", b[8:0x10])
            self.payload = b[0x10:]

    def craft_echo(host, result, echo_id, org, recv, xmt, offset):
        org = org & 0xFFFFFFFFFFFFFFFF
        recv = recv & 0xFFFFFFFFFFFFFFFF
        xmt = xmt & 0xFFFFFFFFFFFFFFFF
        offset = offset & 0xFFFFFFFFFFFFFFFF

        return HostInfoPkt.craft(host, BUILTIN_ECHO, result, 0x28, 0, echo_id, struct.pack("<QQQQ", org, recv, xmt, offset))

    def craft_basic(host, message_type, result, unk_4, payload):
        return HostInfoPkt.craft(host, message_type, result, len(payload) + 0x8, 0, unk_4, payload)

    def craft_capnp(host, message_type, result, unk_4, payload):
        return HostInfoPkt.craft(host, message_type, result, len(payload) + 0x10, 0, unk_4, struct.pack("<LL", 0, len(payload) // 8) + payload)

    def craft(host, message_type, result, stream_size, unk_30_31, unk_4, payload):

        header_0 = (message_type & 0xF) | ((result & 0x1FF) << 4) | ((stream_size & 0xFFFFC) << 12) | ((unk_30_31 & 3) << 30)
        b = struct.pack("<LL", header_0, unk_4) + payload

        return HostInfoPkt(host, 0, b)

    def to_bytes(self):
        self.header_0 = (self.message_type & 0xF) | ((self.result & 0x1FF) << 4) | ((self.stream_size & 0xFFFFC) << 12) | ((self.unk_30_31 & 3) << 30)
        b = struct.pack("<LL", self.header_0, self.unk_4)
        if self.message_type == BUILTIN_ECHO:
            b += struct.pack("<QQQQ", self.echo_org, self.echo_recv, self.echo_xmt, self.echo_offset)
        else:
            b += struct.pack("<LL", self.unk_8, self.len_u64s)
            b += self.payload
        return b

    def dump(self):
        print ("HostInfoPkt:")
        print ("  header_0: %08x" % self.header_0)

        print ("    message_type:   %s (%01x)" % (XrspBuiltinMessageType(self.message_type), self.message_type))
        print ("    result:         %03x" % self.result)
        print ("    stream_size:    %05x" % self.stream_size)
        print ("    unk_30_31:      %01x" % self.unk_30_31)

        
        if self.message_type == BUILTIN_ECHO:
            print ("  id:     %08x" % self.unk_4)
            print ("  type:   " + ("PONG" if (self.result & 1) else "PING"))
            print ("  org:    %016x" % self.echo_org)
            print ("  recv:   %016x" % self.echo_recv)
            print ("  xmt:    %016x" % self.echo_xmt)
            print ("  offset: %016x" % self.echo_offset)
            pass
        else:
            print ("  unk_4:    %08x" % self.unk_4)
            print ("  unk_8:    %08x" % self.unk_8)
            print ("  len_u64s: %08x" % self.len_u64s)

        if self.message_type == BUILTIN_ECHO:
            return

        try:
            hex_dump(self.payload)
            parser = CapnpParser(self.payload)
            parser.parse_entry(0)
        except Exception as e:
            a='a'

class RuntimeIPCPkt:

    def __init__(self, host, b):
        if len(b) < 8:
            print ("Bad ipc pkt!")
            hex_dump(b)
            return

        self.host = host
        self.payload = b[0x0:]

        self.printable = ""

        if self.host.ipc_state.state == STATE_SEGMENT_META:
            self.host.ipc_state.reset()
            self.host.ipc_state.type_idx, self.host.ipc_state.seg0_size = struct.unpack("<LL", self.payload[:8])

            self.host.ipc_state.seg0_size *= 8

            self.host.ipc_state.state = STATE_SEGMENT_READ
        elif self.host.ipc_state.state == STATE_SEGMENT_READ:

            if len(self.host.ipc_state.seg0) < self.host.ipc_state.seg0_size:
                self.host.ipc_state.seg0 += self.payload
            
            seg0_left = self.host.ipc_state.seg0_size - len(self.host.ipc_state.seg0)
            
            if seg0_left <= 0:
                print("Seg0:", hex(self.host.ipc_state.seg0_size))

                try:
                    # TODO: store this
                    payload = RuntimeIPC_capnp.PayloadRuntimeIPC.from_segments([self.host.ipc_state.seg0])
                    self.printable = payload

                    self.host.ipc_state.seg1_size = payload.nextSize
                    self.host.ipc_state.type_idx = payload.id
                except Exception as e:
                    print ("Exception in RuntimeIPCPkt:", e)

                self.host.ipc_state.state = STATE_EXT_READ

        elif self.host.ipc_state.state == STATE_EXT_READ:
            if len(self.host.ipc_state.seg1) < self.host.ipc_state.seg1_size:
                self.host.ipc_state.seg1 += self.payload
            
            seg0_left = self.host.ipc_state.seg1_size - len(self.host.ipc_state.seg1)
            
            if seg0_left <= 0:
                print("Ext:")
                hex_dump(self.host.ipc_state.seg1)

                try:
                    parser = CapnpParser(self.host.ipc_state.seg1)
                    parser.parse_entry(0)
                except Exception as e:
                    print (e)

                self.host.ipc_state.state = STATE_SEGMENT_META

    def dump(self):
        print ("RuntimeIPCPkt:")

        try:
            print (self.printable)
        except Exception as e:
            print ("Exception in RuntimeIPCPkt dump:", e)

class LoggingPkt:

    def __init__(self, host, b):
        if len(b) < 8:
            print ("Bad log pkt!")
            hex_dump(b)
            return

        self.host = host
        self.payload = b[0x0:]

        self.printable = ""

        if self.host.logging_state.state == STATE_SEGMENT_META:
            self.host.logging_state.reset()
            self.host.logging_state.type_idx, self.host.logging_state.seg0_size = struct.unpack("<LL", self.payload[:8])

            self.host.logging_state.seg0_size *= 8

            self.host.logging_state.state = STATE_SEGMENT_READ
        elif self.host.logging_state.state == STATE_SEGMENT_READ:

            if len(self.host.logging_state.seg0) < self.host.logging_state.seg0_size:
                self.host.logging_state.seg0 += self.payload
            
            seg0_left = self.host.logging_state.seg0_size - len(self.host.logging_state.seg0)
            
            if seg0_left <= 0:
                try:
                    # TODO: store this
                    self.printable = Logging_capnp.PayloadLogging.from_segments([self.host.logging_state.seg0])
                except Exception as e:
                    print ("Exception in LoggingPkt:", e)
                self.host.logging_state.state = STATE_SEGMENT_META


    def dump(self):
        print ("LoggingPkt:", hex(len(self.payload)))
        if len(self.payload) <= 0x8:
            hex_dump(self.payload)
            return

        '''
        try:
            parser = CapnpParser(self.payload)
            parser.parse_entry(0)
        except Exception as e:
            print (e)
        '''

        try:
            print (self.printable)
        except Exception as e:
            print ("Exception in LoggingPkt dump:", e)

class PosePkt:

    def __init__(self, host, b):
        if len(b) < 8:
            print ("Bad pose pkt!")
            hex_dump(b)
            return

        self.host = host
        self.payload = b[0x0:]

        self.printable = ""

        if self.host.pose_state.state == STATE_SEGMENT_META:
            self.host.pose_state.reset()
            self.host.pose_state.type_idx, self.host.pose_state.seg0_size = struct.unpack("<LL", self.payload[:8])

            self.host.pose_state.seg0_size *= 8

            self.host.pose_state.state = STATE_SEGMENT_READ
        elif self.host.pose_state.state == STATE_SEGMENT_READ:

            if len(self.host.pose_state.seg0) < self.host.pose_state.seg0_size:
                self.host.pose_state.seg0 += self.payload
            
            seg0_left = self.host.pose_state.seg0_size - len(self.host.pose_state.seg0)
            
            if seg0_left <= 0:
                try:
                    # TODO: store this
                    pose_payload = Pose_capnp.PayloadPose.from_segments([self.host.pose_state.seg0])
                    self.printable = pose_payload

                    if len(pose_payload.controllers) >= 1:
                        self.host.touchpad_pos = ((pose_payload.controllers[0].touchpadX * (1280/2)) + (1280/2), (pose_payload.controllers[0].touchpadY * (-1024/2)) + (1024/2))
                        self.host.touchpad_z = pose_payload.controllers[0].touchpadPressure
                        #self.host.update()

                    #print (self.host.touchpad_pos, self.host.touchpad_z)
                except Exception as e:
                    print ("Exception in PosePkt:", e)
                    hex_dump(self.host.pose_state.seg0)
                self.host.pose_state.state = STATE_SEGMENT_META


    def dump(self):
        print ("PosePkt:", hex(len(self.payload)))
        if len(self.payload) <= 0x8:
            hex_dump(self.payload)
            return

        '''
        try:
            parser = CapnpParser(self.payload)
            parser.parse_entry(0)
        except Exception as e:
            print (e)
        '''

        try:
            print (self.printable)
            pass
        except Exception as e:
            print ("Exception in PosePkt dump:", e)

class AudioPkt:

    def __init__(self, host, b):
        if len(b) < 8:
            print ("Bad audio pkt!")
            return

        self.host = host
        self.payload = b[0x0:]

        self.printable = ""

        if self.host.audio_state.state == STATE_SEGMENT_META:
            self.host.audio_state.reset()
            self.host.audio_state.type_idx, self.host.audio_state.seg0_size = struct.unpack("<LL", self.payload[:8])

            self.host.audio_state.seg0_size *= 8

            self.host.audio_state.state = STATE_SEGMENT_READ
        elif self.host.audio_state.state == STATE_SEGMENT_READ:

            if len(self.host.audio_state.seg0) < self.host.audio_state.seg0_size:
                self.host.audio_state.seg0 += self.payload
            
            seg0_left = self.host.audio_state.seg0_size - len(self.host.audio_state.seg0)
            
            if seg0_left <= 0:
                try:
                    # TODO: store this
                    self.printable = Audio_capnp.PayloadAudio.from_segments([self.host.audio_state.seg0])
                    #self.printable = "asdf"
                except Exception as e:
                    print ("Exception in AudioPkt:", e)
                self.host.audio_state.state = STATE_SEGMENT_META


    def dump(self):
        print ("AudioPkt:", hex(len(self.payload)))
        if len(self.payload) <= 0x8:
            hex_dump(self.payload)
            return

        '''
        try:
            parser = CapnpParser(self.payload)
            parser.parse_entry(0)
        except Exception as e:
            print (e)
        '''

        try:
            #print (self.printable)
            pass
        except Exception as e:
            print ("Exception in AudioPkt dump:", e)

class HandPose:

    def __init__(self, b):
        if len(b) != 0x290:
            return
        self.raw = b

        # similar to ovrHandPose

        idx = 0
        def read_u32():
            nonlocal idx, b
            val = struct.unpack("<L", b[idx:idx+4])[0]
            idx += 4
            return val

        def read_f32():
            nonlocal idx, b
            val = struct.unpack("<f", b[idx:idx+4])[0]
            idx += 4
            return val

        def read_f64():
            nonlocal idx, b
            val = struct.unpack("<d", b[idx:idx+8])[0]
            idx += 8
            return val

        def read_vec3():
            val = [read_f32(), read_f32(), read_f32()]
            return val

        def read_quat():
            val = [read_f32(), read_f32(), read_f32(), read_f32()]
            return val

        self.unk_00 = read_u32()
        self.trackingStatus = read_u32() # ovrHandTrackingStatus

        self.rootPos = [0.0] * (4+3) # quat+vec3
        self.unk2 = [0] * 3
        self.boneRots = [[0.0] * 4]*24
        self.requestedTimeStamp = 0.0
        self.sampleTimeStamp = 0.0
        self.fingerConfidence = [0.0] * 5
        self.unk4 = [0.0] * 26
        self.unk5 = [0.0] * 5
        self.unk6 = [0.0] * 7 # elbow?
        self.unk7 = [0.0] * 5

        for i in range(0, 4+3):
            self.rootPos[i] = read_f32()

        
        for i in range(0, 3):
            self.unk2[i] = read_f32()

        for i in range(0, 24):
            self.boneRots[i] = read_quat()

        self.requestedTimeStamp = read_f64()
        self.sampleTimeStamp = read_f64()

        self.handConfidence = read_f32()
        self.handScale = read_f32()

        for i in range(0, 5):
            self.fingerConfidence = read_f32()

        read_u32()
        read_u32()

        for i in range(0, 26):
            self.unk4[i] = read_f32()

        for i in range(0, 5):
            self.unk5[i] = read_f32()

        for i in range(0, 7):
            self.unk6[i] = read_f32()

        for i in range(0, 5):
            self.unk7[i] = read_u32()

    def dump(self):
        print ("  unk_00: " + hex(self.unk_00))
        print ("  trackingStatus: " + hex(self.trackingStatus))
        print ("  rootPos:",self.rootPos)
        print ("  unk2:",self.unk2)
        print ("  boneRots:",self.boneRots)
        print ("  requestedTimeStamp:",self.requestedTimeStamp)
        print ("  sampleTimeStamp:",self.sampleTimeStamp)
        print ("  fingerConfidence:",self.fingerConfidence)
        print ("  unk4:",self.unk4)
        print ("  unk5:",self.unk5)
        print ("  unk6:",self.unk6)
        print ("  unk7:",self.unk7)
        #print ("data:",self.data)
        #hex_dump(self.raw)


class HandsPkt:

    def __init__(self, host, b):
        if len(b) < 8:
            print ("Bad hands pkt!")
            hex_dump(b)
            return

        self.host = host
        self.payload = b[0:]

        if len(self.payload) <= 0x8:
            return

        # TODO check size
        unk_00, unk_04 = struct.unpack("<LL", self.payload[:8])
        hand_l_bin = self.payload[8:8+0x290]
        hand_r_bin = self.payload[8+0x290:8+0x290+0x290]

        self.hand_l = HandPose(hand_l_bin)
        self.hand_r = HandPose(hand_r_bin)

    def dump(self):
        print ("HandsPkt:", hex(len(self.payload)))
        if len(self.payload) <= 0x8:
            hex_dump(self.payload)
            return

        '''
        try:
            parser = CapnpParser(self.payload)
            parser.parse_entry(0)
        except Exception as e:
            print (e)
        '''
        print ("Left hand:")
        self.hand_l.dump()
        print ("Right hand:")
        self.hand_r.dump()

        

class SkeletonPkt:

    def __init__(self, host, b):
        if len(b) < 8:
            print ("Bad skeleton pkt!")
            hex_dump(b)
            return

        self.host = host
        self.payload = b[0:]

    def dump(self):
        print ("SkeletonPkt:", hex(len(self.payload)))
        if len(self.payload) <= 0x8:
            hex_dump(self.payload)
            return

        '''
        try:
            parser = CapnpParser(self.payload)
            parser.parse_entry(0)
        except Exception as e:
            print (e)
        '''

        # TODO check size
        #unk_00, unk_04 = struct.unpack("<LL", self.payload[:8])
        #hex_dump(self.payload)

'''
class SlicePkt:

    def __init__(self, host, b):
        if len(b) < 8:
            print ("Bad slice pkt!")
            hex_dump(b)
            return

        self.host = host
        self.payload = b[0:]

    def dump(self):
        print ("SlicePkt:", hex(len(self.payload)))
        if len(self.payload) <= 0x8:
            hex_dump(self.payload)
            return

        try:
            parser = CapnpParser(self.payload)
            parser.parse_entry(0)
        except Exception as e:
            print ("Exception in SlicePkt dump:", e)
'''

class SlicePkt:

    def __init__(self, host, slice_idx, b):
        if len(b) < 8:
            print ("Bad slice pkt!")
            hex_dump(b)
            return

        self.host = host
        self.payload = b[0x0:]

        self.printable = ""

        if self.host.slice_state[slice_idx].state == STATE_SEGMENT_META:
            print ("meta")
            #hex_dump(self.payload)
            self.host.slice_state[slice_idx].reset()
            self.host.slice_state[slice_idx].type_idx, self.host.slice_state[slice_idx].seg0_size = struct.unpack("<LL", self.payload[:8])

            self.host.slice_state[slice_idx].seg0_size *= 8

            self.host.slice_state[slice_idx].state = STATE_SEGMENT_READ
        elif self.host.slice_state[slice_idx].state == STATE_SEGMENT_READ:
            print ("seg read", hex(self.host.slice_state[slice_idx].seg0_size))
            #hex_dump(self.payload)

            if len(self.host.slice_state[slice_idx].seg0) < self.host.slice_state[slice_idx].seg0_size:
                self.host.slice_state[slice_idx].seg0 += self.payload
            
            seg0_left = self.host.slice_state[slice_idx].seg0_size - len(self.host.slice_state[slice_idx].seg0)
            
            if seg0_left <= 0:
                print("Seg0:", hex(self.host.slice_state[slice_idx].seg0_size))

                try:
                    # TODO: store this
                    payload = Slice_capnp.PayloadSlice.from_segments([self.host.slice_state[slice_idx].seg0])
                    self.printable = payload

                    self.host.slice_state[slice_idx].seg0 = b''
                    self.host.slice_state[slice_idx].seg1 = b''

                    self.host.slice_state[slice_idx].seg0_size = payload.csdSize
                    self.host.slice_state[slice_idx].seg1_size = payload.videoSize
                except Exception as e:
                    print ("Exception in SlicePkt:", e)

                self.host.slice_state[slice_idx].state = STATE_EXT_READ

        elif self.host.slice_state[slice_idx].state == STATE_EXT_READ:
            print ("ext read", hex(len(self.host.slice_state[slice_idx].seg0)), hex(len(self.host.slice_state[slice_idx].seg1)))

            if len(self.host.slice_state[slice_idx].seg0) < self.host.slice_state[slice_idx].seg0_size:
                self.host.slice_state[slice_idx].seg0 += self.payload
            elif len(self.host.slice_state[slice_idx].seg1) < self.host.slice_state[slice_idx].seg1_size:
                self.host.slice_state[slice_idx].seg1 += self.payload
            
            seg0_left = self.host.slice_state[slice_idx].seg0_size - len(self.host.slice_state[slice_idx].seg0)
            seg1_left = self.host.slice_state[slice_idx].seg1_size - len(self.host.slice_state[slice_idx].seg1)
            
            if seg0_left <= 0 and seg1_left <= 0:
                print("Ext 0:", hex(len(self.host.slice_state[slice_idx].seg0)))

                '''
                f = open("video_extract/video_%d_%d.bin" % (self.host.video_inc, 0), "wb")
                f.write(self.host.slice_state[slice_idx].seg0)
                f.close()
                '''

                #hex_dump()
                print("Ext 1:", hex(len(self.host.slice_state[slice_idx].seg1)))
                #hex_dump(self.host.slice_state[slice_idx].seg1)
                '''
                f = open("video_extract/video_%d_%d.bin" % (self.host.video_inc, 1), "wb")
                f.write(self.host.slice_state[slice_idx].seg1)
                f.close()
                '''

                self.host.video_inc += 1

                '''
                try:
                    parser = CapnpParser(self.host.slice_state[slice_idx].seg1)
                    parser.parse_entry(0)
                except Exception as e:
                    print (e)
                '''

                self.host.slice_state[slice_idx].state = STATE_SEGMENT_META

    def dump(self):
        print ("SlicePkt:")

        try:
            print (self.printable)
        except Exception as e:
            print ("Exception in SlicePkt dump:", e)

class CameraStreamPkt:

    def __init__(self, host, b, seq):
        if len(b) < 8:
            print ("Bad camstream pkt!")
            hex_dump(b)
            return

        self.host = host
        self.seq = seq
        self.payload = b[0x0:]

        # TODO: Check seq and don't double-process data
        if len(self.payload) == 0x10 and not self.host.camera_state.seq_collecting:
            self.host.camera_state.seq_collecting = True
            self.host.camera_state.which, self.host.camera_state.seq_seg0_size, self.host.camera_state.seq_seg1_size, self.host.camera_state.seq_seg2_size = struct.unpack("<LLLL", self.payload)
            
            print("Decoding camera which: " + hex(self.host.camera_state.which) + " (" + hex(self.host.camera_state.seq_seg0_size) + ", " + hex(self.host.camera_state.seq_seg1_size) + ", " + hex(self.host.camera_state.seq_seg2_size) + ")")

            self.host.camera_state.seq_seg0_size *= 8
            self.host.camera_state.seq_seg1_size *= 8
            self.host.camera_state.seq_seg2_size *= 8

            self.host.camera_state.seq_seg0 = b''
            self.host.camera_state.seq_seg1 = b''
            self.host.camera_state.seq_seg2 = b''
            return

        if self.host.camera_state.seq_collecting and len(self.host.camera_state.seq_seg0) < self.host.camera_state.seq_seg0_size:
            self.host.camera_state.seq_seg0 += self.payload
        elif self.host.camera_state.seq_collecting and len(self.host.camera_state.seq_seg1) < self.host.camera_state.seq_seg1_size:
            self.host.camera_state.seq_seg1 += self.payload
        elif self.host.camera_state.seq_collecting and len(self.host.camera_state.seq_seg2) < self.host.camera_state.seq_seg2_size:
            self.host.camera_state.seq_seg2 += self.payload
        
        seg0_left = self.host.camera_state.seq_seg0_size - len(self.host.camera_state.seq_seg0)
        seg1_left = self.host.camera_state.seq_seg1_size - len(self.host.camera_state.seq_seg1)
        seg2_left = self.host.camera_state.seq_seg2_size - len(self.host.camera_state.seq_seg2)

        if self.host.camera_state.seq_collecting and seg0_left <= 0 and seg1_left <= 0 and seg2_left <= 0:
            
            '''
            dat = self.host.camera_state.seq_seg0
            with open("camera_" + str(self.host.camera_state.which) + "_seq_" + str(self.seq) + "_seg0.bin", "wb") as f:
                f.write(dat)
                f.close()
            dat = self.host.camera_state.seq_seg1
            with open("camera_" + str(self.host.camera_state.which) + "_seq_" + str(self.seq) + "_seg1.bin", "wb") as f:
                f.write(dat)
                f.close()
            dat = self.host.camera_state.seq_seg2
            with open("camera_" + str(self.host.camera_state.which) + "_seq_" + str(self.seq) + "_seg2.bin", "wb") as f:
                f.write(dat)
                f.close()
            '''

            segs = [self.host.camera_state.seq_seg0, self.host.camera_state.seq_seg1, self.host.camera_state.seq_seg2]
            #hex_dump(self.host.camera_state.seq_seg0)
            #print("Done with", self.host.camera_state.which, hex(self.host.camera_state.seq_seg0_size))
            if self.host.camera_state.which == 1 and self.host.camera_state.seq_seg0_size == 5*8:
                payload = CameraStream_capnp.PayloadCameraStreamMeta.from_segments(segs)
                jsondat = bytes(payload.metadata.data).decode("utf-8")
                with open("camera_metadata.json", "w") as f:
                    f.write(jsondat)
                    f.close()
                self.host.camera_state.has_meta = True
                print("Decoded camera metadata!")
            elif (self.host.camera_state.which == 1 and self.host.camera_state.has_meta) or self.host.camera_state.which == 2:
                payload = CameraStream_capnp.PayloadCameraStream.from_segments(segs)

                idx = 0
                for d in payload.unk1.struct1Unk4:

                    # TODO: store this
                    dat = bytes(d.data)
                    if len(dat) == 0x140000 and idx == 0:
                        self.host.camera_state.pixels = np.frombuffer(dat, dtype=np.uint8).reshape(1024,1280)
                        self.host.update()

                    #with open("camera_seq_" + str(self.seq) + "_" + str(idx) + ".bin", "wb") as f:
                    #    f.write(dat)
                    #    f.close()
                    idx += 1

                '''
                payload = payload.to_dict()
                for i in range(0, len(payload['unk1']['struct1Unk4'])):
                    payload['unk1']['struct1Unk4'][i]['data'] = b''
                print (payload)
                '''

            self.host.camera_state.seq_collecting = False
            self.host.camera_state.seq_seg0 = b''
            self.host.camera_state.seq_seg1 = b''
            self.host.camera_state.seq_seg2 = b''

            return

    def dump(self):

        print ("CameraStreamPkt:", hex(len(self.payload)), hex(self.seq))
        print (hex(len(self.host.camera_state.seq_seg0)), hex(len(self.host.camera_state.seq_seg1)), hex(len(self.host.camera_state.seq_seg2)))

        if len(self.payload) <= 0x8:
            #hex_dump(self.payload)
            return

        #with open("camera_seq_" + str(self.seq) + ".bin", "wb") as f:
        #    f.write(self.payload)

        if len(self.payload) > 0x200:
            return

        #test = CameraStream_capnp.PayloadCameraStream.new_message()


        
        try:
            parser = CapnpParser(self.payload)
            parser.parse_entry(0)
        except Exception as e:
            print ("Exception in CameraStreamPkt dump:", e)
        