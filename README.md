# xrsp_tests
Attempting to talk to Meta Quest's USB/XRSP interface 

See also: https://github.com/OpenOculus/XrspDocs

# XrspPacketHeader
| Position | Size | Name                         |
|----------|------|------------------------------|
| 0x00     | u16  | Version, Topic (See below)   |
| 0x02     | u16  | Number of u32 words          |
| 0x04     | u16  | Sequence number              |
| 0x06     | u16  | Padding                      |

# Version/Topic u16
|  Bits | Size | Name                         |
|-------|------|------------------------------|
| 0-2   | 3    | Version?                     |
| 3     | 1    | Packet has alignment padding |
| 4     | 1    | xrspPacketVersionIsInternal  |
| 5-7   | 3    | xrspPacketVersionNumber      |
| 8-13  | 6    | Topic                        |
| 14-15 | 2    | Unk                          |

# Cap'n Stream header
| Position | Size | Name                          |
|----------|------|-------------------------------|
| 0x00     | u32  | Header_0                      |
| 0x04     | u32  | Data stream version           |
| 0x08     | u32  | Unk                           |
| 0x0C     | u32  | Payload length (in u64 words) |

# Header_0
|  Bits | Size | Name                                    |
|-------|------|-----------------------------------------|
| 0-3   | 4    | XrspBuiltinMessageType                  |
| 4-13  | 14   | XrspResult(?) xrspTransactionStatusCode |
| 14-29 | 16   | Stream size in words, including header  |
| 30-31 | 2    | Unk                                     |

# Payload
The initial hostinfo sent is a capnp message containing the device's info, including the serial, name/device type, lens intrinsics, etc.

# Topics
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
