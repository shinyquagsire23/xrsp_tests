# xrsp_tests
Attempting to talk to Meta Quest's USB/XRSP interface 

See also: https://github.com/OpenOculus/XrspDocs

## Repo Organization

**Mains:**
 - `xrsp.py`: Main script, talks USB and displays an image.
 - `pkt_parse.py`: Replay packets dumped from `xrsp.py`.
 - `capnp_parse.py`: Display raw capnproto data.
 - `264_extract_wireshark.py`: Wireshark pcap parsing and misc dumping.
 - `float_to_bin.py`: Look at the weird float camera images.

**Helpers**:
 - `xrsp_constants.py`: Constants related to the XRSP protocol.
 - `xrsp_host.py`: XrspHost, the USB device and state. Manages initialization, packet sending, and responses.
 - `xrsp_parse.py`: Objects/parsing for all topics.
 - `utils.py`: Helper functions.

**Data:**
 - `video_extract/`: Displayed H.264 frame.
 - `notes.txt`: Misc docs.
 - `camera_metadata_questpro.json`: JSON sent by CameraStream topic for Quest Pro.
 - `camera_metadata_quest2.json`: JSON sent by CameraStream topic for Quest 2.

# Data Structures
## XrspPacketHeader
| Position | Size | Name                         |
|----------|------|------------------------------|
| 0x00     | u16  | Version, Topic (See below)   |
| 0x02     | u16  | Number of u32 words          |
| 0x04     | u16  | Sequence number              |
| 0x06     | u16  | Padding                      |

## Version/Topic u16
|  Bits | Size | Name                         |
|-------|------|------------------------------|
| 0-2   | 3    | Version?                     |
| 3     | 1    | Packet has alignment padding |
| 4     | 1    | xrspPacketVersionIsInternal  |
| 5-7   | 3    | xrspPacketVersionNumber      |
| 8-13  | 6    | Topic                        |
| 14-15 | 2    | Unk                          |

## XrspBuiltinHeader

Header for hostinfo-adv

| Position | Size | Name                          |
|----------|------|-------------------------------|
| 0x00     | u32  | Header_0                      |
| 0x04     | u32  | Data stream version           |
| 0x08     | u32  | Unk                           |
| 0x0C     | u32  | Payload length (in u64 words) |
| 0x10     | ...  | Payload                       |

## Header_0
|  Bits | Size | Name                                    |
|-------|------|-----------------------------------------|
| 0-3   | 4    | XrspBuiltinMessageType                  |
| 4-13  | 10   | XrspResult(?) xrspTransactionStatusCode |
| 14-31 | 18   | Stream size in words, including header  |

## HostInfo Packet
The initial hostinfo sent is a capnp message containing the device's info, including the serial, name/device type, lens intrinsics, etc.

## Topics
Topics are are 6-bits in length (mask 0x3f). Topics over ID 2 are always encrypted; it is currently unknown as to how they are encrypted. Each topic is routed to and parsed in a separate handler, usually in its own thread.

| ID   | Name               |
|------|--------------------|
| 0x00 | "aui4a-adv"        |
| 0x01 | "hostinfo-adv"     |
| 0x02 | "Command"          |
| 0x03 | "Pose"             |
| 0x04 | "Mesh"             |
| 0x05 | "Video"            |
| 0x06 | "Audio"            |
| 0x07 | "Haptic"           |
| 0x08 | "Hands"            |
| 0x09 | "Skeleton"         |
| 0x0A | "Slice 0"          |
| 0x0B | "Slice 1"          |
| 0x0C | "Slice 2"          |
| 0x0D | "Slice 3"          |
| 0x0E | "Slice 4"          |
| 0x0F | "Slice 5"          |
| 0x10 | "Slice 6"          |
| 0x11 | "Slice 7"          |
| 0x12 | "Slice 8"          |
| 0x13 | "Slice 9"          |
| 0x14 | "Slice 10"         |
| 0x15 | "Slice 11"         |
| 0x16 | "Slice 12"         |
| 0x17 | "Slice 13"         |
| 0x18 | "Slice 14"         |
| 0x19 | "Slice 15"         |
| 0x1A | "AudioControl"     |
| 0x1B | "UserSettingsSync" |
| 0x1C | "InputControl"     |
| 0x1D | "Asw"              |
| 0x1E | "Body"             |
| 0x1F | "RuntimeIPC"       |
| 0x20 | "CameraStream"     |
| 0x21 | "Logging"          |

### Command pkts ids

Search for `Command result err %d`

| Num  | Function                               |
|------|----------------------------------------|
| 0x00 | Termination                            |
| 0x01 | ?                                      |
| 0x02 | ?                                      |
| 0x03 | Calls some funcs in a while loop?      |
| 0x04 | ?                                      |
| 0x05 | Sets some bool true                    |
| 0x06 | Sets some other bool true              |
| 0x07 | Sets some other bool false (same as 6) |
| 0x08 | Starts a timer and calls a func        |
| 0x09 | ?                                      |
| 0x0A | ?                                      |
| 0x0B | Reset guardian                         |
| 0x0C | CHEMX toggle command                   |
| 0x0D | Start camera frame streaming           |
| 0x0E | Stop camera frame streaming            |
| 0x0F | ASW toggle command                     |
| 0x10 | ?                                      |
| 0x11 | Drop frames state command              |

### getInputControl
| Num  | Function                  |
|------|---------------------------|
| 0x00 | ?                         |
| 0x01 | Toggle hands              |
| 0x02 | Toggle 3-pt body tracking |

## Packet Patterns
All packets are wrapped with XrspPacketHeader and Topics, but not all Topics function the same.

 - Some, like hostinfo-adv, wrap capnproto payloads directly in one packet.
 - Some, like AudioControl, Video, and CameraStream have a simple two-state state machine: A raw packet is sent with a u32 type, u32 segment0 length (CameraStream/others have two more u32s for segments 1 and 2). XrspPacketHeader-wrapped packets are then sent until each segment buffer is filled. Once filled, the segment is decoded. This is followed both sending and receiving.
 - Some, like Slice N, have a 3+ stage state machine: A raw packet (u32 type, u32 segment len), a capnproto packet which describes the H.264 CSD NAL size and H.264 IDR NAL size, an optional CSD packet, and an optional IDR packet.
 - Some topics send raw struct data, no capnproto at all (Hands, ...)
