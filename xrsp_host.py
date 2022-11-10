import struct

# Requires pyusb
import usb.core
import usb.util

# Draw cameras
import pygame
import numpy as np
import json

import time

from xrsp_parse import *
from xrsp_constants import *
from protos.Slice_capnp import PayloadSlice

PAIRINGSTATE_WAIT_FIRST = 0
PAIRINGSTATE_WAIT_SECOND = 1
PAIRINGSTATE_PAIRING = 2
PAIRINGSTATE_PAIRED = 3

ECHOSTATE_0 = 0
ECHOSTATE_1 = 1
ECHOSTATE_2 = 2
ECHOSTATE_3 = 3

class CameraStreamState:

    def __init__(self):
        self.has_meta = False
        self.seq_collecting = False
        self.which = 0
        self.seq_seg0_size = 0
        self.seq_seg1_size = 0
        self.seq_seg2_size = 0

        self.seq_seg0 = b''
        self.seq_seg1 = b''
        self.seq_seg2 = b''

        self.pixels = np.zeros((1024,1280))


class GenericState:

    def __init__(self):
        self.state = STATE_SEGMENT_META

        self.reset()

    def reset(self):
        self.type_idx = 0
        self.seg0_size = 0
        self.seg0 = b''
        self.seg1_size = 0
        self.seg1 = b''

        # runtime IPC
        self.timestamp = 0

class XrspHost:

    def __init__(self):
        self.topics_mute = [TOPIC_AUI4A_ADV, TOPIC_POSE, TOPIC_HANDS, TOPIC_AUDIO] #TOPIC_CAMERA_STREAM
        #self.topics_mute = [TOPIC_AUI4A_ADV, TOPIC_POSE, TOPIC_AUDIO]

        self.camera_state = CameraStreamState()
        self.pose_state = GenericState()
        self.audio_state = GenericState()
        self.logging_state = GenericState()
        self.ipc_state = GenericState()
        self.slice_state = [None] * 15
        for i in range(0, 15):
            self.slice_state[i] = GenericState()

        # USB
        self.has_usb = False
        self.dev = None
        self.ep_in = None
        self.ep_out = None
        self.increment = 0
        self.remainder_bytes = b''
        self.working_pkt = None

        # Pairing
        self.pairing_state = PAIRINGSTATE_WAIT_FIRST
        self.reset_echo()
        self.last_xmt = 0
        self.start_ns = time.time_ns()

        # Video
        self.num_slices = 5

        # Misc
        self.video_inc = 0
        self.touchpad_pos = (0,0)
        self.touchpad_z = 0.0
        self.headsetQuat = [0,0,0,1]
        self.headsetPos = [0,0,0]

        self.window = pygame.display.set_mode((1280, 1024))
        pygame.display.set_caption('Camera')
        self.update()

    def reset_echo(self):
        self.echo_state = ECHOSTATE_0
        self.echo_idx = 1
        self.ns_offset = 0

        self.echo_req_sent_ns = 0 # client ns
        self.echo_req_recv_ns = 0 # server ns
        self.echo_resp_sent_ns = 0 # server ns
        self.echo_resp_recv_ns = 0 # server ns

    def init_usb(self):
        # find our device
        self.dev = usb.core.find(idVendor=0x2833) #, idProduct=0x0183

        # was it found?
        if self.dev is None:
            raise ValueError('Device not found')

        #dev.reset()

        # set the active configuration. With no arguments, the first
        # configuration will be the active one
        self.dev.set_configuration()

        # get an endpoint instance
        cfg = self.dev.get_active_configuration()
        intf = None
        for i in range(0, 10):
            intf = cfg[(i,0)]
            if "XRSP" in str(intf):
                print (intf)
                break


        self.ep_out = usb.util.find_descriptor(
            intf,
            # match the first OUT endpoint
            custom_match = \
            lambda e: \
                usb.util.endpoint_direction(e.bEndpointAddress) == \
                usb.util.ENDPOINT_OUT)

        self.ep_in = usb.util.find_descriptor(
            intf,
            # match the first OUT endpoint
            custom_match = \
            lambda e: \
                usb.util.endpoint_direction(e.bEndpointAddress) == \
                usb.util.ENDPOINT_IN)

        try:
            self.ep_out.clear_halt()
        except:
            a='a'

        try:
            self.ep_in.clear_halt()
        except:
            a='a'

        # Clear pkt dump
        f = open("dump_pkts.bin", "wb")
        f.write(b'')
        f.close()

        self.has_usb = True

    def ts_ns(self):
        return time.time_ns() - self.start_ns

    def init_session(self):
        self.read_xrsp()

        response_ok_payload = bytes([0x00, 0x00, 0x00, 0x00, 0x03, 0x00, 0x03, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x05, 0x00, 0x00, 0x00, 0x2B, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x03, 0x00, 0x02, 0x00, 0x04, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        response_ok = HostInfoPkt.craft_capnp(self, BUILTIN_OK, result=0xC8, unk_4=1, payload=response_ok_payload).to_bytes()
        
        print ("OK send")
        self.send_to_topic(1, response_ok)
        self.old_read_xrsp()

    def send_codegen_1(self):
        request_codegen_payload = bytes([0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        request_codegen = HostInfoPkt.craft_capnp(self, BUILTIN_CODE_GENERATION, result=0xC8, unk_4=1, payload=request_codegen_payload).to_bytes()

        print ("Codegen send")
        self.send_to_topic(1, request_codegen)
        self.old_read_xrsp()

    def send_pairing_1(self):
        request_pairing_payload = bytes([0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00])
        request_pairing = HostInfoPkt.craft_capnp(self, BUILTIN_PAIRING, result=0xC8, unk_4=1, payload=request_pairing_payload).to_bytes()

        print ("Pairing send")
        self.send_to_topic(1, request_pairing)
        self.old_read_xrsp()

    def finish_pairing_1(self):
        request_video_idk = [0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x00]

        print ("Echo send")
        self.send_ping()

        print ("Video idk cmd send")
        self.send_to_topic_capnp_wrapped(TOPIC_VIDEO, 0, request_video_idk)

        print ("Waiting for user to accept...")

    def init_session_2(self):
        self.reset_echo()
        self.read_xrsp()

        response_ok_2_payload = bytes([0x00, 0x00, 0x00, 0x00, 0x03, 0x00, 0x03, 0x00, 0x03, 0x00, 0x01, 0x00, 0x1F, 0x00, 0x00, 0x00, 0x05, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x48, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x09, 0x00, 0x00, 0x00, 0x1B, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x2A, 0x00, 0x00, 0x00, 0x55, 0x53, 0x42, 0x33, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x03, 0x00, 0x02, 0x00, 0x00, 0x00])
        response_ok_2 = HostInfoPkt.craft_capnp(self, message_type=BUILTIN_OK, result=0xC8, unk_4=1, payload=response_ok_2_payload).to_bytes()

        print ("Done?")

        print ("OK send #2")
        self.send_to_topic(TOPIC_HOSTINFO_ADV, response_ok_2)

        print ("OK read #2")
        self.old_read_xrsp()

    def send_codegen_2(self):
        request_codegen_2_payload = bytes([0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        request_codegen_2 = HostInfoPkt.craft_capnp(self, BUILTIN_CODE_GENERATION, result=0xC8, unk_4=1, payload=request_codegen_2_payload).to_bytes()
        
        print ("Codegen send #2")
        self.send_to_topic(TOPIC_HOSTINFO_ADV, request_codegen_2)

        print ("Codegen read #2")
        self.old_read_xrsp()

    def send_pairing_2(self):
        request_pairing_2_payload = bytes([0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        request_pairing_2 = HostInfoPkt.craft_capnp(self, BUILTIN_PAIRING, result=0xC8, unk_4=1, payload=request_pairing_2_payload).to_bytes()

        print ("Pairing send #2")
        self.send_to_topic(TOPIC_HOSTINFO_ADV, request_pairing_2)

        print ("Pairing read #2")
        self.old_read_xrsp()

    def finish_pairing_2(self):
        send_audiocontrol_idk = struct.pack("<LLHHLLL", 0, 2, 1, 1, 0, 0, 0)
        
        send_cmd_chemx_toggle = struct.pack("<QLLLLLL", 0x0005EC94E91B9D4F, COMMAND_TOGGLE_CHEMX, 0, 0, 0, 0, 0)
        send_cmd_asw_toggle = struct.pack("<QLLLLLL", 0x0005EC94E91B9D83, COMMAND_TOGGLE_ASW, 0, 0, 0, 0, 0)
        send_cmd_dropframestate_toggle = struct.pack("<QLLLLLL", 0x0005EC94E91B9D83, COMMAND_DROP_FRAMES_STATE, 0, 0, 0, 0, 0)
        send_cmd_camerastream = struct.pack("<QLLLLLL", 0x0005EC94E91B9D83, COMMAND_ENABLE_CAMERA_STREAM, 0, 0, 0, 0, 0)

        send_cmd_body = struct.pack("<LLHHLLL", 0, 2, 2, 1, 0, 0, 0)
        send_cmd_hands = struct.pack("<LLHHLLL", 0, 2, 1, 1, 0, 0, 0)

        print ("Echo send")
        self.send_ping()

        print ("Audio Control cmd send")
        self.send_to_topic_capnp_wrapped(TOPIC_AUDIO_CONTROL, 0, send_audiocontrol_idk)

        print ("1A read")
        self.old_read_xrsp()

        #print ("1 send")
        #response_echo_pong = HostInfoPkt.craft_echo(self, result=ECHO_PONG, echo_id=1, org=0x000011148017ea57, recv=0x00000074c12277bc, xmt=0x00000074c122daf4, offset=0).to_bytes()
        #self.send_to_topic(TOPIC_HOSTINFO_ADV, response_echo_pong)

        print ("2 sends")
        #self.send_to_topic(TOPIC_COMMAND, send_cmd_chemx_toggle)
        #self.send_to_topic(TOPIC_COMMAND, send_cmd_asw_toggle)
        #self.send_to_topic(TOPIC_COMMAND, send_cmd_dropframestate_toggle)
        #self.send_to_topic(TOPIC_COMMAND, send_cmd_camerastream)

        #self.send_to_topic_capnp_wrapped(TOPIC_INPUT_CONTROL, 0, send_cmd_hands)
        #self.send_to_topic_capnp_wrapped(TOPIC_INPUT_CONTROL, 0, send_cmd_body)


    def send_ping(self):
        #print ("Sending ping...")
        if self.ts_ns() - self.echo_req_sent_ns < 16000000: #16ms
            return

        self.echo_req_sent_ns = self.ts_ns()

        request_echo_ping = HostInfoPkt.craft_echo(self, result=ECHO_PING, echo_id=self.echo_idx, org=0, recv=0, xmt=self.echo_req_sent_ns, offset=self.ns_offset).to_bytes()
        #hex_dump(request_echo_ping)
        self.send_to_topic(TOPIC_HOSTINFO_ADV, request_echo_ping)

        self.echo_idx += 1

    def send_video(self, sliceIdx, frameIdx, csdDat, videoDat, blitYPos):
        msg = PayloadSlice.new_message()

        bits = 0
        if len(csdDat) > 0:
            bits |= 1
        if sliceIdx == self.num_slices-1:
            bits |= 2

        msg.frameIdx = frameIdx
        msg.unk0p1 = 0
        msg.unk1p0 = 0
        msg.poseQuatX = self.headsetQuat[0]
        msg.poseQuatY = self.headsetQuat[1]
        msg.poseQuatZ = self.headsetQuat[2]
        msg.poseQuatW = self.headsetQuat[3]
        msg.poseX = self.headsetPos[0]
        msg.poseY = self.headsetPos[1]
        msg.poseZ = self.headsetPos[2]
        msg.timestamp05 = self.ts_ns()#18278312488115
        msg.sliceNum = sliceIdx
        msg.unk6p1 = bits 
        msg.unk6p2 = 0
        msg.unk6p3 = 0
        msg.blitYPos = blitYPos
        msg.unk7p0 = 24
        
        msg.unk8p1 = 0
        msg.timestamp09 = self.ts_ns()#18787833654115
        msg.unkA = 29502900
        msg.timestamp0B = self.ts_ns()#18278296859411
        msg.timestamp0C = self.ts_ns()#18278292486840
        msg.timestamp0D = self.ts_ns()#18787848654114
        msg.quat1.x = 0
        msg.quat1.y = 0
        msg.quat1.z = 0
        msg.quat1.w = 0
        msg.quat2.x = 0
        msg.quat2.y = 0
        msg.quat2.z = 0
        msg.quat2.w = 0

        msg.csdSize = len(csdDat)
        msg.videoSize = len(videoDat)

        segments = msg.to_segments()

        self.send_to_topic_capnp_wrapped(TOPIC_SLICE_0+sliceIdx, 0, segments[0])
        self.send_to_topic(TOPIC_SLICE_0+sliceIdx, csdDat)
        self.send_to_topic(TOPIC_SLICE_0+sliceIdx, videoDat)

    def send_to_topic(self, topic, msg):
        if not self.has_usb:
            return

        if len(msg) <= 0:
            return

        idx = 0
        to_send = len(msg)
        while True:
            if idx >= to_send:
                break
            self.send_to_topic_raw(topic, msg[idx:idx+0xFFFF])

            idx += 0xFFFF

    def send_to_topic_raw(self, topic, msg):
        if not self.has_usb:
            return

        aligned = True
        real_len = len(msg)
        align_up_bytes = (((4+len(msg)) // 4) * 4) - len(msg)
        if align_up_bytes != 4 and align_up_bytes != 0:
            if align_up_bytes > 1:
                msg += bytes([0xDE] * (align_up_bytes-1))
            msg += bytes([(len(msg)+1) - real_len])
            aligned = False

        try:
            pkt_out = struct.pack("<BBHHH", 0x10 if aligned else 0x18, topic, (len(msg) // 4)+1, self.increment, 0)
            pkt_out += bytes(msg)
            #to_fill = (0x400 - len(pkt_out)) - 6
            to_fill = 0x400 - ((len(pkt_out) + 0x400) & 0x3FF) - 6
            if to_fill > 0:
                pkt_out += struct.pack("<BBHH", 0x10, 0x0, (to_fill // 4)+1, self.increment)
                #hex_dump(pkt_out)
                pkt_out += b'\x00' * to_fill

            #hex_dump(pkt_out)

            self.increment += 1
            self.increment = self.increment & 0xFFFF

            #pkt = TopicPkt(self, pkt_out)
            #pkt.dump()

            #print (hex(len(pkt_out)))

            self.ep_out.write(pkt_out)
        except usb.core.USBTimeoutError as e:
            print ("Failed to send to topic", hex(topic), e)

    def send_to_topic_capnp_wrapped(self, topic, idx, msg):
        prelude = struct.pack("<LL", idx, len(msg) // 8)

        self.send_to_topic(topic, prelude)
        self.send_to_topic(topic, msg)

    # TODO: Figure out why init doesn't work with new read_xrsp
    def old_read_xrsp(self):
        if not self.has_usb:
            return

        # Parse anything that's whole in the remainder bytes
        try:
            while True:
                if len(self.remainder_bytes) <= 0:
                    break
                pkt = TopicPkt(self, self.remainder_bytes)
                if pkt.missing_bytes() <= 0:
                    self.handle_packet(pkt)
                    self.remainder_bytes = pkt.remainder_bytes()
                else:
                    break
        except Exception as e:
            print (e)

        b = self.remainder_bytes

        try:
            start_idx = len(b)
            b += bytes(self.ep_in.read(0x200))
            b += bytes(self.ep_in.read(0x200))
            f = open("dump_pkts.bin", "ab")
            f.write(b[start_idx:])
            f.close()

            if len(b) >= 8:
                pkt = TopicPkt(self, b)
                while pkt.missing_bytes() > 0:
                    #print ("MISSING", hex(pkt.missing_bytes()))
                    _b = bytes(self.ep_in.read(0x200))
                    f = open("dump_pkts.bin", "ab")
                    f.write(_b)
                    f.close()

                    pkt.add_missing_bytes(_b)
                    b += _b
            
        except usb.core.USBTimeoutError as e:
            print ("Failed read", e)
        except usb.core.USBError as e:
            print ("Failed read", e)

        if len(b) >= 8:
            try:
                '''
                pkt = TopicPkt(self, b)
                if pkt.missing_bytes() > 0:
                    self.remainder_bytes = b
                else:
                    self.remainder_bytes = pkt.remainder_bytes()
                    b = b[:len(b)-len(remainder_bytes)]
                    self.handle_packet(pkt)
                '''
                pkt = TopicPkt(self, b)
                self.remainder_bytes = pkt.remainder_bytes()
                b = b[:len(b)-len(self.remainder_bytes)]
                self.handle_packet(pkt)
            except Exception as e:
                print (e)

        return b

    def read_xrsp(self):
        if not self.has_usb:
            return

        if self.ts_ns() - self.echo_req_sent_ns > 1000000000 and self.pairing_state >= PAIRINGSTATE_PAIRING:
            self.send_ping()

        f = open("dump_pkts.bin", "ab")

        b = b''
        while True:
            try:
                b = bytes(self.ep_in.read(0x200))

                f.write(bytes(b))

                if self.working_pkt is None:
                    self.working_pkt = TopicPkt(self, b)
                elif self.working_pkt.missing_bytes() == 0:
                    self.handle_packet(self.working_pkt)
                    remains = self.working_pkt.remainder_bytes()
                    if len(remains) > 0 and len(remains) < 8:
                        self.working_pkt = None
                        print("Weird remainder!")
                        hex_dump(remains)
                    elif len(remains) > 0:
                        self.working_pkt = TopicPkt(self, remains)
                        self.working_pkt.add_missing_bytes(b)
                    else:
                        self.working_pkt = TopicPkt(self, b)
                else:
                    self.working_pkt.add_missing_bytes(b)

                while self.working_pkt is not None and self.working_pkt.missing_bytes() == 0:
                    self.handle_packet(self.working_pkt)
                    remains = self.working_pkt.remainder_bytes()
                    if len(remains) > 0 and len(remains) < 8:
                        self.working_pkt = None
                        print("Weird remainder!")
                        hex_dump(remains)
                    elif len(remains) > 0:
                        self.working_pkt = TopicPkt(self, remains)
                    else:
                        self.working_pkt = None
                break
            except usb.core.USBTimeoutError as e:
                print ("Failed read", e)
                f.close()
                return b
            except usb.core.USBError as e:
                print ("Failed read", e)
                f.close()
                return b

        f.close()
        return b

    def wait_pairing(self):
        while self.pairing_state != PAIRINGSTATE_PAIRED:
            self.read_xrsp()

    def handle_packet(self, pkt):
        pkt.dump()

        if pkt.topic_idx == TOPIC_HOSTINFO_ADV:
            self.handle_hostinfo_adv(pkt)
            return

    def handle_hostinfo_adv(self, pkt):
        hostinfo = pkt.specificObj

        if hostinfo is None:
            return

        if hostinfo.message_type == BUILTIN_ECHO:
            self.handle_echo(hostinfo)
            return

        if self.pairing_state == PAIRINGSTATE_WAIT_FIRST:
            if hostinfo.message_type == BUILTIN_INVITE:
                self.init_session()
            elif hostinfo.message_type == BUILTIN_ACK:
                self.send_codegen_1()
            elif hostinfo.message_type == BUILTIN_CODE_GENERATION_ACK:
                self.send_pairing_1()
            elif hostinfo.message_type == BUILTIN_PAIRING_ACK:
                self.finish_pairing_1()

                self.pairing_state = PAIRINGSTATE_WAIT_SECOND
        elif self.pairing_state == PAIRINGSTATE_WAIT_SECOND or self.pairing_state == PAIRINGSTATE_PAIRING:
            if hostinfo.message_type == BUILTIN_INVITE:
                self.pairing_state = PAIRINGSTATE_PAIRING
                self.init_session_2()
            elif hostinfo.message_type == BUILTIN_ACK:
                self.send_codegen_2()
            elif hostinfo.message_type == BUILTIN_CODE_GENERATION_ACK:
                self.send_pairing_2()
            elif hostinfo.message_type == BUILTIN_PAIRING_ACK:
                self.finish_pairing_2()

                self.pairing_state = PAIRINGSTATE_PAIRED

    def handle_echo(self, echopkt):
        if (echopkt.result & 1) == 1: # PONG

            #print ("Pong!")

            self.echo_req_recv_ns = echopkt.echo_recv # server recv ns
            self.echo_resp_sent_ns = echopkt.echo_xmt # server tx ns
            self.echo_resp_recv_ns = echopkt.recv_ns # client rx ns
            self.echo_req_sent_ns = self.ts_ns()

            self.ns_offset = ((self.echo_req_recv_ns-self.echo_req_sent_ns) + (self.echo_resp_sent_ns-echopkt.recv_ns)) // 2
            self.ns_offset = self.ns_offset & 0xFFFFFFFFFFFFFFFF

            #print("Ping offs:", hex(self.ns_offset))

            if self.pairing_state == PAIRINGSTATE_PAIRED:
                self.send_ping()

        else: # PING
            #print ("Ping!", hex(self.ns_offset))
            self.last_xmt = echopkt.echo_xmt

            outpkt = HostInfoPkt.craft_echo(self, result=ECHO_PONG, echo_id=echopkt.unk_4, org=self.last_xmt, recv=echopkt.recv_ns, xmt=self.ts_ns(), offset=self.ns_offset)
            response_echo_pong = outpkt.to_bytes()
            #hex_dump(response_echo_pong)
            #outpkt.dump()
            self.send_to_topic(TOPIC_HOSTINFO_ADV, response_echo_pong)


    def update(self):
        background_color = (0, 0, 0)
        self.window.fill(background_color)

        
        pixel_array = pygame.PixelArray(self.window)

        for x in range(0, 1280):
            for y in range(0, 1024):
                val = self.camera_state.pixels[y,x]
                pixel_array[x,y] = (val,val,val)
        

        pygame.draw.circle(self.window, (int(self.touchpad_z * 255),255,0), self.touchpad_pos, 20 + (self.touchpad_z * 20))

        #pixel_array.close()
        pygame.display.flip()