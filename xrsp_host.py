import struct

# Requires pyusb
import usb.core
import usb.util

# Draw cameras
import pygame
import numpy as np
import json

from xrsp_parse import *
from xrsp_constants import *

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
        self.topics_mute = [TOPIC_AUI4A_ADV, TOPIC_POSE, TOPIC_HANDS, TOPIC_AUDIO, TOPIC_CAMERA_STREAM]
        #self.topics_mute = [TOPIC_AUI4A_ADV, TOPIC_POSE, TOPIC_AUDIO]

        self.camera_state = CameraStreamState()
        self.pose_state = GenericState()
        self.audio_state = GenericState()
        self.logging_state = GenericState()
        self.ipc_state = GenericState()

        # USB
        self.has_usb = False
        self.dev = None
        self.ep_in = None
        self.ep_out = None
        self.increment = 0
        self.remainder_bytes = b''
        self.working_pkt = None

        self.touchpad_pos = (0,0)
        self.touchpad_z = 0.0

        self.window = pygame.display.set_mode((1280, 1024))
        pygame.display.set_caption('Camera')
        self.update()

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

    def send_to_topic(self, topic, msg, aligned=True):
        if not self.has_usb:
            return

        try:
            pkt_out = struct.pack("<BBHHH", 0x10 if aligned else 0x18, topic, (len(msg) // 4)+1, self.increment, 0)
            pkt_out += bytes(msg)
            to_fill = (0x400 - len(pkt_out)) - 6
            pkt_out += struct.pack("<BBHH", 0x10, 0x0, (to_fill // 4)+1, self.increment)
            #hex_dump(pkt_out)
            pkt_out += b'\x00' * to_fill

            #hex_dump(pkt_out)

            self.increment += 1

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
                    pkt.dump()
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
                    pkt.dump()
                '''
                pkt = TopicPkt(self, b)
                self.remainder_bytes = pkt.remainder_bytes()
                b = b[:len(b)-len(self.remainder_bytes)]
                pkt.dump()
            except Exception as e:
                print (e)

        return b

    def read_xrsp(self):
        if not self.has_usb:
            return

        f = open("dump_pkts.bin", "ab")

        b = b''
        while True:
            try:
                b = bytes(self.ep_in.read(0x200))

                f.write(bytes(b))

                if self.working_pkt is None:
                    self.working_pkt = TopicPkt(self, b)
                elif self.working_pkt.missing_bytes() == 0:
                    self.working_pkt.dump()
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
                    self.working_pkt.dump()
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