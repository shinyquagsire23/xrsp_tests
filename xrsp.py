# Requires pyusb
import usb.core
import usb.util
import struct
import time

from capnp_parse import CapnpParser
from xrsp_parse import *
from utils import hex_dump

# XRSP host context
xrsp_host = XrspHost()

# find our device
dev = usb.core.find(idVendor=0x2833) #, idProduct=0x0183

def test(e):
    print(hex(e.bEndpointAddress))
    return False#usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT

# was it found?
if dev is None:
    raise ValueError('Device not found')

#dev.reset()

# set the active configuration. With no arguments, the first
# configuration will be the active one
dev.set_configuration()

# get an endpoint instance
cfg = dev.get_active_configuration()
intf = None
for i in range(0, 10):
    intf = cfg[(i,0)]
    if "XRSP" in str(intf):
        print (intf)
        break


ep_out = usb.util.find_descriptor(
    intf,
    # match the first OUT endpoint
    custom_match = \
    lambda e: \
        usb.util.endpoint_direction(e.bEndpointAddress) == \
        usb.util.ENDPOINT_OUT)

ep_in = usb.util.find_descriptor(
    intf,
    # match the first OUT endpoint
    custom_match = \
    lambda e: \
        usb.util.endpoint_direction(e.bEndpointAddress) == \
        usb.util.ENDPOINT_IN)

try:
    ep_out.clear_halt()
except:
    a='a'

try:
    ep_in.clear_halt()
except:
    a='a'

reply = bytes(b'')

increment = 0

def send_to_topic(topic, msg):
    global increment
    try:
        pkt_out = struct.pack("<BBHHH", 0x10, topic, (len(msg) // 4)+1, increment, 0)
        pkt_out += bytes(msg)
        to_fill = (0x400 - len(pkt_out)) - 6
        pkt_out += struct.pack("<BBHH", 0x10, 0x0, (to_fill // 4)+1, increment)
        #hex_dump(pkt_out)
        pkt_out += b'\x00' * to_fill

        #hex_dump(pkt_out)

        increment += 1

        #pkt = TopicPkt(xrsp_host, pkt_out)
        #pkt.dump()

        #print (hex(len(pkt_out)))

        ep_out.write(pkt_out)
    except usb.core.USBTimeoutError as e:
        print ("Failed to send to topic", hex(topic), e)

# TODO: Figure out why init doesn't work with new read_xrsp
remainder_bytes = b''
def old_read_xrsp():
    global remainder_bytes, xrsp_host
    
    # Parse anything that's whole in the remainder bytes
    try:
        while True:
            if len(remainder_bytes) <= 0:
                break
            pkt = TopicPkt(xrsp_host, remainder_bytes)
            if pkt.missing_bytes() <= 0:
                pkt.dump()
                remainder_bytes = pkt.remainder_bytes()
            else:
                break
    except Exception as e:
        print (e)

    b = remainder_bytes

    try:
        start_idx = len(b)
        b += bytes(ep_in.read(0x200))
        b += bytes(ep_in.read(0x200))
        f = open("dump_pkts.bin", "ab")
        f.write(b[start_idx:])
        f.close()

        if len(b) >= 8:
            pkt = TopicPkt(xrsp_host, b)
            while pkt.missing_bytes() > 0:
                #print ("MISSING", hex(pkt.missing_bytes()))
                _b = bytes(ep_in.read(0x200))
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
            pkt = TopicPkt(xrsp_host, b)
            if pkt.missing_bytes() > 0:
                remainder_bytes = b
            else:
                remainder_bytes = pkt.remainder_bytes()
                b = b[:len(b)-len(remainder_bytes)]
                pkt.dump()
            '''
            pkt = TopicPkt(xrsp_host, b)
            remainder_bytes = pkt.remainder_bytes()
            b = b[:len(b)-len(remainder_bytes)]
            pkt.dump()
        except Exception as e:
            print (e)

    return b

working_pkt = None
remainder_bytes = b''
def read_xrsp():
    global working_pkt, xrsp_host
    
    f = open("dump_pkts.bin", "ab")

    b = b''
    while True:
        try:
            b = bytes(ep_in.read(0x200))

            f.write(bytes(b))

            if working_pkt is None:
                working_pkt = TopicPkt(xrsp_host, b)
            elif working_pkt.missing_bytes() == 0:
                working_pkt.dump()
                remains = working_pkt.remainder_bytes()
                if len(remains) > 0 and len(remains) < 8:
                    working_pkt = None
                    print("Weird remainder!")
                    hex_dump(remains)
                elif len(remains) > 0:
                    working_pkt = TopicPkt(xrsp_host, remains)
                    working_pkt.add_missing_bytes(b)
                else:
                    working_pkt = TopicPkt(xrsp_host, b)
            else:
                working_pkt.add_missing_bytes(b)

            while working_pkt is not None and working_pkt.missing_bytes() == 0:
                working_pkt.dump()
                remains = working_pkt.remainder_bytes()
                if len(remains) > 0 and len(remains) < 8:
                    working_pkt = None
                    print("Weird remainder!")
                    hex_dump(remains)
                elif len(remains) > 0:
                    working_pkt = TopicPkt(xrsp_host, remains)
                else:
                    working_pkt = None
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

# Clear pkt dump
f = open("dump_pkts.bin", "wb")
f.write(b'')
f.close()

try:
    b = ep_in.read(0x200)
    f = open("dump_test_quest.bin", "wb")
    f.write(bytes(b))
    reply += bytes(b)
    b = ep_in.read(0x200)
    f.write(bytes(b))
    reply += bytes(b)
    f.close()
    hex_dump(reply)

    pkt = TopicPkt(xrsp_host, reply)
    pkt.dump()
except usb.core.USBTimeoutError as e:
    print ("Failed first read", e)
except usb.core.USBError as e:
    print ("Failed first read", e)

real_first = [0x82, 0xAC, 0x05, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x09, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x03, 0x00, 0x03, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x05, 0x00, 0x00, 0x00, 0x2B, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x03, 0x00, 0x02, 0x00, 0x04, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
second_send = [0x87, 0x0C, 0x02, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00]
idk_send = [0x89, 0x8C, 0x02, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
echo_send = [0x06, 0x80, 0x02, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x58, 0x2B, 0xDD, 0x3F, 0x73, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
first_5 = [0x00, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x00]
second_5 = [0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x00]

send_usb3 = [0x82, 0xAC, 0x05, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x09, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x03, 0x00, 0x03, 0x00, 0x03, 0x00, 0x01, 0x00, 0x1F, 0x00, 0x00, 0x00, 0x05, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x48, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x09, 0x00, 0x00, 0x00, 0x1B, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x2A, 0x00, 0x00, 0x00, 0x55, 0x53, 0x42, 0x33, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x03, 0x00, 0x02, 0x00, 0x00, 0x00]
send_usb3_2 = [0x89, 0xAC, 0x02, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
send_usb3_3 = [0x87, 0x0C, 0x02, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]

send_1a_1 = struct.pack("<LL", 0, 3)
send_1a_2 = struct.pack("<LLHHLLL", 0, 2, 1, 1, 0, 0, 0)
idk_send_2 = [0x16, 0x80, 0x02, 0x00, 0x01, 0x00, 0x00, 0x00, 0x57, 0xEA, 0x17, 0x80, 0x14, 0x11, 0x00, 0x00, 0xBC, 0x77, 0x22, 0xC1, 0x74, 0x00, 0x00, 0x00, 0xF4, 0xDA, 0x22, 0xC1, 0x74, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
send_2_poses = [0x4F, 0x9D, 0x1B, 0xE9, 0x94, 0xEC, 0x05, 0x00, 0x0C, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
send_2_camerastream = [0x4F, 0x9D, 0x1B, 0xE9, 0x94, 0xEC, 0x05, 0x00, 0x0d, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]


print ("First send")
send_to_topic(1, real_first)

print ("First read")
old_read_xrsp()

print ("idk send")
send_to_topic(1, idk_send)

print ("idk read")
old_read_xrsp()

print ("Second send")
send_to_topic(1, second_send)

print ("Second read")
old_read_xrsp()

print ("Echo send")
send_to_topic(1, echo_send)

print ("First 5 send")
send_to_topic(5, first_5)

print ("Second 5 send")
send_to_topic(5, second_5)

print ("Waiting for user to accept...")

while True:
    print ("5 read")
    ret = old_read_xrsp()
    if len(ret) > 0:
        break

print ("Done?")

print ("USB3 send")
send_to_topic(1, send_usb3)

print ("USB3 read")
old_read_xrsp()

print ("USB3_2 send")
send_to_topic(1, send_usb3_2)

print ("USB3_2 read")
old_read_xrsp()

print ("USB3_3 send")
send_to_topic(1, send_usb3_3)

print ("USB3_3 read")
old_read_xrsp()

print ("Echo send")
send_to_topic(1, echo_send)

print ("1A send 1")
send_to_topic(0x1A, send_1a_1)

print ("1A send 2")
send_to_topic(0x1A, send_1a_2)

print ("1A read")
old_read_xrsp()

print ("1 send")
send_to_topic(1, idk_send_2)

print ("2 send")
#send_to_topic(2, send_2_poses)
send_to_topic(2, send_2_camerastream)

print ("last reads")
while True:
    ret = read_xrsp()
