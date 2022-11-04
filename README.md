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
| 0-2   | 4    | Version?                     |
| 3     | 1    | Packet has alignment padding |
| 4     | 1    | xrspPacketVersionIsInternal  |
| 5-7   | 3    | xrspPacketVersionNumber      |
| 8-13  | 6    | Topic                        |
| 14-15 | 2    | Unk                          |

# Extended header
| Position | Size | Name                          |
|----------|------|-------------------------------|
| 0x00     | u32  | Unk, timestamp?               |
| 0x04     | u32  | Unk                           |
| 0x08     | u32  | Unk                           |
| 0x0C     | u32  | Payload length (in u64 words) |

# Payload
The initial hostinfo sent is a capnp message containing the device's info, including the serial, name/device type, lens intrinsics, etc.

# Topics
Topics are are 6-bits in length (mask 0x3f). Certain topics are also encrypted, it is currently unknown as to how they are encrypted. Each topic is routed to and parsed in a separate thread.

| ID   | Name           | Encrypted |
|------|----------------|-----------|
| 0x00 | "aui4a-adv"    | ?         |
| 0x01 | "hostinfo-adv" | No        |

