# Requires pyusb
import usb.core
import usb.util
import struct
import time

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

def hex_dump(b):
    p = ""
    b = bytes(b)
    for i in range(0, len(b)):
        if i != 0 and i % 16 == 0:
            p += "\n"
        p += ("%02x " % b[i])
    print (p)

def send_to_topic(topic, msg):
    global increment
    try:
        pkt_out = struct.pack("<BBHHH", 0x10, topic, (len(msg) // 4)+1, increment, 0)
        pkt_out += bytes(msg)
        to_fill = (0x400 - len(pkt_out)) - 6
        pkt_out += struct.pack("<BBHH", 0x10, 0x0, (to_fill // 4)+1, increment)
        #hex_dump(pkt_out)
        pkt_out += b'\x00' * to_fill

        increment += 1

        #print (hex(len(pkt_out)))

        ep_out.write(pkt_out)
    except usb.core.USBTimeoutError as e:
        print ("Failed to send to topic", hex(topic), e)

def read_xrsp():
    b = b''
    try:
        b += bytes(ep_in.read(0x200))
        b += bytes(ep_in.read(0x200))
    except usb.core.USBTimeoutError as e:
        print ("Failed read", e)
    except usb.core.USBError as e:
        print ("Failed read", e)
    return b

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
except usb.core.USBTimeoutError as e:
    print ("Failed first read", e)
except usb.core.USBError as e:
    print ("Failed first read", e)

first_send = [0x82, 0xAC, 0x05, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x09, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x03, 0x00, 0x03, 0x00, 0x03, 0x00, 0x01, 0x00, 0x1F, 0x00, 0x00, 0x00, 0x05, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x48, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x09, 0x00, 0x00, 0x00, 0x1B, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x2A, 0x00, 0x00, 0x00, 0x55, 0x53, 0x42, 0x33, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x03, 0x00, 0x02, 0x00, 0x00, 0x00]
second_send = [0x89, 0xAC, 0x02, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
idk_send = [0x89, 0x8C, 0x02, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]

print ("First send")
send_to_topic(1, first_send)

print ("First read")
ret = read_xrsp()
print (hex(len(ret)))
hex_dump (ret)

print ("idk send")
send_to_topic(1, idk_send)

print ("idk read")
ret = read_xrsp()
print (hex(len(ret)))
hex_dump (ret)

print ("Second send")
send_to_topic(1, second_send)

print ("Second read")
ret = read_xrsp()
print (hex(len(ret)))
hex_dump (ret)
