
import struct
import time

from capnp_parse import CapnpParser
from xrsp_parse import *
from xrsp_host import *
from xrsp_constants import *
from utils import hex_dump

# XRSP host context
xrsp_host = XrspHost()
xrsp_host.init_usb()

xrsp_host.wait_pairing()

'''
h264_dat = open("h264_dat.bin", "rb").read()
for i in range(TOPIC_SLICE_0, TOPIC_SLICE_5):
    xrsp_host.read_xrsp()
    try:
        h264_dat = h264_dat[0:1] + bytes([i]) + h264_dat[2:]

        xrsp_host.ep_out.write(h264_dat)
    except usb.core.USBTimeoutError as e:
        print ("Failed to send to topic", hex(i), e)
    xrsp_host.read_xrsp()
'''

# Replay IPC packets
'''
for i in range(0, 18):
    f = open("ipc_baked/ipc_baked_" + str(i) + ".bin", "rb")
    dat = f.read()
    f.close()
    xrsp_host.read_xrsp()
    try:
        xrsp_host.ep_out.write(dat)
    except usb.core.USBTimeoutError as e:
        print ("Failed to send baked IPC", e)
    xrsp_host.read_xrsp()
'''

start_ns = xrsp_host.ts_ns()
while True:
    if xrsp_host.ts_ns() - start_ns > 5000000000: # 5s
        break
    xrsp_host.read_xrsp()

#ffmpeg -f image2 -r 72 -i ~/Pictures/toblerone_crop.jpg -c:v libx264 -f rawvideo -pix_fmt yuvj420p -b:v 70000k -x264opts keyint=1 test_toblerone.264
#ffmpeg -f image2 -r 72 -i ~/Pictures/toblerone_crop.jpg -c:v libx264 -f rawvideo -pix_fmt yuvj420p -b:v 70000k -x264opts keyint=1 -profile:v baseline test_toblerone.264
#ffmpeg -f image2 -r 72 -i ~/Pictures/toblerone.jpg -c:v libx264 -f rawvideo -pix_fmt yuvj420p -b:v 70000k -x264opts keyint=1 -profile:v baseline test_toblerone.264

#ffmpeg -f image2 -r 72 -i test_frame/toblerone_1.jpg -c:v libx264 -f rawvideo -pix_fmt yuvj420p -b:v 70000k -x264opts keyint=1 -profile:v baseline test_toblerone_1.264
#ffmpeg -f image2 -r 72 -i test_frame/toblerone_2.jpg -c:v libx264 -f rawvideo -pix_fmt yuvj420p -b:v 70000k -x264opts keyint=1 -profile:v baseline test_toblerone_2.264
#ffmpeg -f image2 -r 72 -i test_frame/toblerone_3.jpg -c:v libx264 -f rawvideo -pix_fmt yuvj420p -b:v 70000k -x264opts keyint=1 -profile:v baseline test_toblerone_3.264
#ffmpeg -f image2 -r 72 -i test_frame/toblerone_4.jpg -c:v libx264 -f rawvideo -pix_fmt yuvj420p -b:v 70000k -x264opts keyint=1 -profile:v baseline test_toblerone_4.264
#ffmpeg -f image2 -r 72 -i test_frame/toblerone_5.jpg -c:v libx264 -f rawvideo -pix_fmt yuvj420p -b:v 70000k -x264opts keyint=1 -profile:v baseline test_toblerone_5.264

# Replay H.264 data
print ("Begin streaming")
frameIdx = 0
while True:
    
    '''
    for i in range(0, 5): #2070 7550
        xrsp_host.read_xrsp()

        f = open("video_extract/video_" + str(i) + "_0.bin", "rb")
        dat0 = f.read()
        f.close()

        f = open("video_extract/video_" + str(i) + "_1.bin", "rb")
        dat1 = f.read()
        f.close()

        if (i % xrsp_host.num_slices) == 0:
            frameIdx += 1

        #xrsp_host.read_xrsp()
        try:
            xrsp_host.send_video(i % xrsp_host.num_slices, frameIdx, dat0, dat1, (i % 5)*(1920 // xrsp_host.num_slices))
        except usb.core.USBTimeoutError as e:
            print ("Failed to send baked video", e)
        print (str(i))
        #xrsp_host.send_to_topic(1, request_echo)
    '''
    

    xrsp_host.read_xrsp()

    for i in range(0, xrsp_host.num_slices):
        #f = open("test_toblerone.264.0", "rb")
        f = open("test_frame/test_toblerone_" + str(i+1) + ".264", "rb")
        dat0 = f.read()[:0x27]
        f.close()
        #dat0 = b''

        #f = open("test_toblerone.264.1", "rb")
        f = open("test_frame/test_toblerone_" + str(i+1) + ".264", "rb")
        dat1 = f.read()[0x29A:]
        f.close()

        #xrsp_host.read_xrsp()
        try:
            xrsp_host.send_video(i, frameIdx, dat0, dat1, (i % 5)*(1920 // xrsp_host.num_slices))
        except usb.core.USBTimeoutError as e:
            print ("Failed to send baked video", e)

    frameIdx += 1
    print (str(frameIdx))
    #xrsp_host.send_to_topic(1, request_echo)

print ("last reads")
while True:
    ret = xrsp_host.read_xrsp()
